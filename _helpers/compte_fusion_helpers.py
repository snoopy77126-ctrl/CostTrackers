from _helpers._generique_helpers import BaseHelper


class CompteFusionHelpers(BaseHelper):
    def __init__(self, services=None):
        self.services = services or {}
        self.compte_tracker = self.services.get("compte")
        self.compte_list = []

        # 1. Instanciation d'un objet vide via le Tracker
        if not self.compte_tracker:
            raise ValueError("Tracker tiers non trouvé dans services")
        objet_vide = self.compte_tracker.get_new()

        # 2. Récupération dynamique des champs
        self.champs_a_comparer = self._extraire_champs(objet_vide)

    def load_data(self, selected_tiers_data: list):
        """ Interroge le operation_tracker pour recréer les objets métiers complets. """

        for row in selected_tiers_data:
            t_id = row.get("id") or row.get("id_compte") or row.get("iid_key")
            if t_id is not None:
                obj_complet = self.compte_tracker.get_by_id(t_id)
                if obj_complet:
                    self.compte_list.append(obj_complet)

        print(f"[DEBUG] Helper : {len(self.compte_list)} objets métiers chargés.")

        # --- AJOUT ICI ---
        # Une fois les vrais objets chargés, on extrait les champs du premier
        if self.compte_list:
            self.champs_a_comparer = self._extraire_champs(self.compte_list[0])
            print(f"[DEBUG] Champs extraits : {self.champs_a_comparer}")

    def get_columns_config(self):
        """Retourne la configuration des colonnes du Treeview"""
        columns = ["champ", "apres"]
        headings = ["Champ", "Après"]

        for i, t in enumerate(self.compte_list):
            columns.append(f"t_{i}")
            # On affiche le nom ou l'ID dans l'en-tête
            nom = getattr(t, 'nom_du_compte', f"Compte #{getattr(t, 'id_compte', i)}")
            headings.append(f"#{i + 1} ({nom})")

        return columns, headings

    # Correspondance noms SQL (clés de to_sql_dict) -> attributs Python de l'objet
    _SQL_TO_ATTR = {
        "label":           "nom_du_compte",
        "numero":          "identifiant",
        "banque_id":       None,   # FK gérée via l'objet .banque, non éditable ici
        "type_compte_id":  None,   # FK gérée via l'objet .type_compte, non éditable ici
    }
    # Champs SQL à exclure de l'affichage et de la fusion (FK, IDs techniques)
    _CHAMPS_EXCLUS = {"id_compte", "banque_id", "type_compte_id"}

    _BOOL_FIELDS = {"compte_favori", "cache_le_compte", "object_epargne"}
    _FLOAT_FIELDS = {"solde_init", "solde_min", "solde_max", "decouvert_autorise",
                     "taux_interet", "montant", "montant_max", "remboursement_mini"}

    def prepare_rows(self):
        """Prépare les lignes de données et détecte les conflits."""
        rows = []
        for champ_sql in self.champs_a_comparer:
            if champ_sql in self._CHAMPS_EXCLUS:
                continue

            # Nom de l'attribut Python correspondant
            attr = self._SQL_TO_ATTR.get(champ_sql, champ_sql)
            if attr is None:
                continue  # Champ non éditable (FK objet)

            valeurs_tiers = [str(getattr(t, attr, "")) for t in self.compte_list]
            valeurs_uniques = set(v for v in valeurs_tiers if v.strip() != "")

            valeur_apres = ""
            has_conflict = False

            if len(valeurs_uniques) == 1:
                valeur_apres = list(valeurs_uniques)[0]
            elif len(valeurs_uniques) > 1:
                has_conflict = True

            # On stocke le nom SQL dans la colonne "champ" pour pouvoir le récupérer
            # dans _action_ok sans ambiguïté (l'affichage met le label lisible)
            rows.append({
                "champ_sql":  champ_sql,
                "label":      champ_sql.replace("_", " ").capitalize(),
                "valeur_apres": valeur_apres,
                "valeurs_tiers": valeurs_tiers,
                "conflit":    has_conflict,
            })

        return rows

    def executer_fusion(self, resultats_apres: dict):
        """resultats_apres : {champ_sql: valeur_string}"""
        if not self.compte_list:
            return

        champs_maitre = self.compte_list[0]
        id_maitre = champs_maitre.id_compte

        # 1. Mise à jour des attributs Python du maître
        for champ_sql, valeur in resultats_apres.items():
            attr = self._SQL_TO_ATTR.get(champ_sql, champ_sql)
            if attr is None or not hasattr(champs_maitre, attr):
                continue

            # Typage selon la nature du champ
            if champ_sql in self._BOOL_FIELDS:
                if isinstance(valeur, str):
                    valeur = valeur.strip().lower() in ('true', '1', 'yes', 'oui')
                else:
                    valeur = bool(valeur)
            elif champ_sql in self._FLOAT_FIELDS:
                try:
                    valeur = float(valeur or 0.0)
                except (ValueError, TypeError):
                    valeur = 0.0

            setattr(champs_maitre, attr, valeur)
            print(f"[DEBUG] setattr({attr!r}, {valeur!r})")

        success = self.compte_tracker.update(champs_maitre)
        print(f"[DEBUG] compte_tracker.update => {success}")

        # 2. Identification des doublons à supprimer
        ids_doublons = [t.id_compte for t in self.compte_list[1:] if t.id_compte != id_maitre]
        print(f"[DEBUG] ids_doublons à supprimer : {ids_doublons}")

        if not ids_doublons:
            print("[DEBUG] Aucun doublon à supprimer.")
            return

        # 3. Migration des opérations vers le compte maître via le operation_tracker
        #    (obligatoire avant le DELETE pour respecter les FK)
        ops_tracker = self.services.get("operation")
        if ops_tracker:
            nb = ops_tracker.migrer_liaisons_compte(ids_doublons, id_maitre)
            print(f"[DEBUG] Migration opérations : {nb} ligne(s) migrée(s) vers compte_id={id_maitre}")
        else:
            print("[WARN] ops_tracker 'operation' non trouvé dans services")

        # 4. Suppression des comptes doublons en base
        for old_id in ids_doublons:
            deleted = self.compte_tracker.delete(old_id)
            print(f"[DEBUG] Suppression compte id={old_id} => {deleted}")

        print(f"[SUCCESS] Fusion terminée : {len(ids_doublons)} doublon(s) supprimé(s).")

    def _extraire_champs(self, objet_vide) -> list:
        """
        Extrait dynamiquement les champs persistants en utilisant
        le dictionnaire du modèle lui-même.
        """
        # On récupère la liste des clés depuis le dictionnaire du modèle
        if hasattr(objet_vide, 'to_sql_dict'):
            dico = objet_vide.to_sql_dict()
            # On retourne toutes les clés sauf l'ID technique
            return [k for k in dico.keys() if k != 'id_compte']

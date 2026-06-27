from _helpers._generique_helpers import BaseHelper
from models.categories import Categorie, CategorieParent


class CategorieFusionHelpers(BaseHelper):
    def __init__(self, services=None):
        self.services = services or {}
        self.categorie_tracker = self.services.get("categorie")
        self.categorie_list = []

        if not self.categorie_tracker:
            raise ValueError("Tracker catégorie non trouvé dans services")

        objet_vide = self.categorie_tracker.get_new()
        self.champs_a_comparer = self._extraire_champs(objet_vide)

    def load_data(self, selected_categories_data: list):
        """Charge les objets métiers complets depuis le cat_trackers."""
        for row in selected_categories_data:
            cat_id = row.get("id") or row.get("id_categorie") or row.get("iid_key")
            # L'iid_key peut être "a_5" ou "c_12" — on extrait l'entier
            if isinstance(cat_id, str) and "_" in cat_id:
                cat_id = int(cat_id.split("_")[1])
            if cat_id is not None:
                obj = self.categorie_tracker.get_by_id(int(cat_id))
                if obj:
                    self.categorie_list.append(obj)

        print(f"[DEBUG] CategorieFusion : {len(self.categorie_list)} objets chargés.")

        if self.categorie_list:
            self.champs_a_comparer = self._extraire_champs(self.categorie_list[0])
            print(f"[DEBUG] Champs extraits : {self.champs_a_comparer}")

    def get_columns_config(self):
        """Retourne la configuration des colonnes du Treeview."""
        columns  = ["champ", "apres"]
        headings = ["Champ", "Après"]

        for i, cat in enumerate(self.categorie_list):
            columns.append(f"t_{i}")
            nom = getattr(cat, "display_name", f"Catégorie #{getattr(cat, 'id_categorie', i)}")
            headings.append(f"#{i + 1} ({nom})")

        return columns, headings

    # Champs à exclure (IDs techniques et FK)
    _CHAMPS_EXCLUS = {"id_categorie", "parent_id"}

    # Correspondance SQL → attribut Python (pour les cas où ça diffère)
    _SQL_TO_ATTR = {
        "designation": "designation",
    }

    _BOOL_FIELDS  = set()
    _FLOAT_FIELDS = set()

    def prepare_rows(self):
        """Prépare les lignes pour le Treeview avec détection des conflits."""
        rows = []
        for champ_sql in self.champs_a_comparer:
            if champ_sql in self._CHAMPS_EXCLUS:
                continue

            attr = self._SQL_TO_ATTR.get(champ_sql, champ_sql)
            if attr is None:
                continue

            valeurs = [str(getattr(cat, attr, "")) for cat in self.categorie_list]
            valeurs_uniques = set(v for v in valeurs if v.strip())

            valeur_apres = ""
            has_conflict = False

            if len(valeurs_uniques) == 1:
                valeur_apres = list(valeurs_uniques)[0]
            elif len(valeurs_uniques) > 1:
                has_conflict = True

            # Ligne spéciale : parent (catégorie mère)
            if champ_sql == "categorie":
                valeurs = []
                for cat in self.categorie_list:
                    if isinstance(cat, Categorie) and cat.categorie:
                        valeurs.append(cat.categorie.designation)
                    elif isinstance(cat, CategorieParent):
                        valeurs.append("(racine)")
                    else:
                        valeurs.append("")
                valeurs_uniques = set(v for v in valeurs if v.strip())
                has_conflict = len(valeurs_uniques) > 1
                valeur_apres = list(valeurs_uniques)[0] if len(valeurs_uniques) == 1 else ""
                rows.append({
                    "champ_sql":     "categorie",
                    "label":         "Catégorie parente",
                    "valeur_apres":  valeur_apres,
                    "valeurs_tiers": valeurs,
                    "conflit":       has_conflict,
                })
                continue

            rows.append({
                "champ_sql":     champ_sql,
                "label":         champ_sql.replace("_", " ").capitalize(),
                "valeur_apres":  valeur_apres,
                "valeurs_tiers": valeurs,
                "conflit":       has_conflict,
            })

        return rows

    def executer_fusion(self, resultats_apres: dict):
        """Fusionne les catégories : met à jour le maître, migre les opérations,
        supprime les doublons."""
        if not self.categorie_list:
            return

        maitre = self.categorie_list[0]
        id_maitre = maitre.id_categorie

        # 1. Mise à jour des attributs du maître
        for champ_sql, valeur in resultats_apres.items():
            if champ_sql == "categorie":
                continue  # la catégorie parente n'est pas modifiée ici
            attr = self._SQL_TO_ATTR.get(champ_sql, champ_sql)
            if attr is None or not hasattr(maitre, attr):
                continue
            setattr(maitre, attr, valeur)
            print(f"[DEBUG] setattr({attr!r}, {valeur!r})")

        success = self.categorie_tracker.update(maitre)
        print(f"[DEBUG] categorie_tracker.update => {success}")

        # 2. IDs doublons
        ids_doublons = [
            cat.id_categorie for cat in self.categorie_list[1:]
            if cat.id_categorie != id_maitre
        ]
        print(f"[DEBUG] ids_doublons : {ids_doublons}")

        if not ids_doublons:
            print("[DEBUG] Aucun doublon.")
            return

        # 3. Migration des opérations vers la catégorie maître
        ops_tracker = self.services.get("operation")
        cat_tracker = self.services.get("categorie")

        if ops_tracker:
            nb = ops_tracker.migrer_liaisons_categorie(ids_doublons, id_maitre)
            print(f"[DEBUG] Migration opérations : {nb} ligne(s) → categorie_id={id_maitre}")
        else:
            print("[WARN] ops_tracker 'operation' non trouvé dans services")

        if cat_tracker:
            nb = cat_tracker.migrer_liaisons_categorie(ids_doublons, id_maitre)
            print(f"[DEBUG] Migration catégories : {nb} ligne(s) → categorie_id={id_maitre}")
        else:
            print("[WARN] cat_tracker 'categorie' non trouvé dans services")

        # 4. Suppression des doublons
        for old_id in ids_doublons:
            deleted = self.categorie_tracker.delete(old_id)
            print(f"[DEBUG] Suppression categorie id={old_id} => {deleted}")

        print(f"[SUCCESS] Fusion terminée : {len(ids_doublons)} doublon(s) supprimé(s).")

    def _extraire_champs(self, objet) -> list:
        """Extrait les champs persistants depuis to_sql_dict(), ajoute 'categorie'
        pour afficher la catégorie parente."""
        champs = []
        if hasattr(objet, "to_sql_dict"):
            champs = [k for k in objet.to_sql_dict().keys() if k != "id_categorie"]
        # On ajoute l'affichage du parent si c'est une Categorie
        if isinstance(objet, Categorie) and "categorie" not in champs:
            champs.append("categorie")
        return champs

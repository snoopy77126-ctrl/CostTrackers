# operations_import_helpers.py
# -*- coding: utf-8 -*-
import inspect
from pathlib import Path
import hashlib
from datetime import datetime

from ._generique_helpers import BaseHelper
from interfaces_mod.mod_import_mapping_dial import MappingDialog


class _NullObject:
    """Retourné quand compte ou tiers est absent du fichier — évite les None."""
    id_compte = None
    id_tiers = None
    id_categorie = None

class RowProcessor:
    """Gère le traitement d'une ligne brute, le mapping, la résolution et la mémorisation des choix."""

    def __init__(self, compte_tracker, category_tracker, tiers_tracker, operation_tracker):
        self.compte_tracker = compte_tracker
        self.category_tracker = category_tracker
        self.tiers_tracker = tiers_tracker
        self.operation_tracker = operation_tracker

        self.caches = {"accounts": {}, "categories": {}, "tiers": {}}

        # Mémorisation des règles "Appliquer à tout" pendant cet import
        self.batch_rules = {"accounts": None, "categories": None, "tiers": None}

    def process_row(self, parent_window, index, raw_row, mapping, id_import):
        """Transforme une ligne brute en objet OperationImport."""
        mapped = {target: raw_row.get(src_col, "") for target, src_col in mapping.items() if src_col}

        # Extractions
        cat_name, cat_parent = self._extract_category(mapped)
        compte_num = str(mapped.get("compte_num", "") or "").strip()
        compte_label = str(mapped.get("compte_label", "") or "").strip()
        tiers_brut = str(mapped.get("tiers", "") or "").strip()

        # Résolutions avec support Batch
        compte = self._resolve_account(parent_window, compte_label, compte_num)
        if compte is None: return None

        categorie = self._resolve_category(parent_window, cat_name, cat_parent)
        if categorie is None: return None

        tiers = self._resolve_tiers(parent_window, tiers_brut)
        if tiers is None: return None

        # Construction de l'objet
        op = self.operation_tracker.get_new()
        op.id_import = id_import
        op.numero_ligne = index
        op.date_operation = str(mapped.get("date_operation", "") or "")
        op.date_valeur = str(mapped.get("date_valeur", "") or "")
        op.libelle = str(mapped.get("libelle", "") or "")
        op.montant = self._parse_montant(mapped.get("montant", "0"))
        op.type_operation = self._detect_type_operation(op.montant, mapped)
        op.commentaire = str(mapped.get("commentaire", "") or "")
        op.source = "import_bancaire"
        op.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        op.compte_num = compte_num
        op.compte_label = compte_label
        op.tiers = tiers_brut
        op.categorie = cat_name
        op.categorie_parent = cat_parent or ""

        # Identifiant unique
        op.import_key = str(mapped.get("import_key", "") or "") or str(mapped.get("fitid", "") or "")
        if not op.import_key:
            chaine = f"{op.date_operation}_{op.libelle}_{op.montant}_{index}"
            op.import_key = hashlib.md5(chaine.encode()).hexdigest()

        op.compte_id = getattr(compte, "id_compte", None)
        op.tiers_id = getattr(tiers, "id_tiers", None)
        op.categorie_id = getattr(categorie, "id_categorie", None)

        return op

    def _resolve_generic(self, parent_window, type_key, display_val, existing, mapper, creator):
        # 1. Vérifier si une règle batch existe
        rule = self.batch_rules[type_key]
        if rule and rule["action"] != "cancel":
            return mapper(rule["value"]) if rule["action"] == "map" else creator()

        # 2. Ouvrir la boîte de dialogue
        dialog = MappingDialog(parent_window, f"Correspondance {type_key.capitalize()}",
                               type_key.capitalize(), display_val, existing)

        # 3. Mémoriser le choix si demandé (et si action valide)
        if dialog.result.get("apply_to_all") and dialog.result["action"] != "cancel":
            self.batch_rules[type_key] = dialog.result

        # 4. Appliquer selon l'action
        if dialog.result["action"] == "map":
            return mapper(dialog.result["value"])
        elif dialog.result["action"] == "create":
            return creator()

        # Si "cancel" ou fermeture, on retourne None pour arrêter le processus
        return None

    def _resolve_account(self, parent_window, label, num):
        if not label and not num: return _NullObject()
        if (label, num) in self.caches["accounts"]: return self.caches["accounts"][(label, num)]

        compte = self.compte_tracker.get_by_name_and_num(label, num)
        if not compte:
            compte = self._resolve_generic(
                parent_window, "accounts", f"{label} ({num})",
                [f"{c.nom_du_compte} [{getattr(c, 'identifiant', '')}]" for c in self.compte_tracker.get_all()],
                lambda val: self.compte_tracker.get_by_display_string(val),
                lambda: self.compte_tracker.create(name=label, number=num)
            )
        self.caches["accounts"][(label, num)] = compte
        return compte

    def _resolve_category(self, parent_window, name, parent):
        if (name, parent) in self.caches["categories"]: return self.caches["categories"][(name, parent)]

        categorie = self.category_tracker.get_by_name_and_parent(name, parent)
        if not categorie:
            categorie = self._resolve_generic(
                parent_window, "categories", f"{name} [{parent}]",
                [c.display_name for c in self.category_tracker.get_all()],
                lambda val: self.category_tracker.get_by_display_string(val),
                lambda: self.category_tracker.create(name=name, parent_name=parent)
            )
        self.caches["categories"][(name, parent)] = categorie
        return categorie

    def _resolve_tiers(self, parent_window, name):
        if not name: return _NullObject()
        if name in self.caches["tiers"]: return self.caches["tiers"][name]

        tiers = self.tiers_tracker.get_by_name(name)
        if not tiers:
            tiers = self._resolve_generic(
                parent_window, "tiers", name,
                [getattr(t, "display_org_first", str(t)) for t in self.tiers_tracker.get_all()],
                lambda val: self.tiers_tracker.get_by_name(val),
                lambda: self.tiers_tracker.create(name=name)
            )
        self.caches["tiers"][name] = tiers
        return tiers

    # --- Utils ---
    def _parse_montant(self, value) -> float:
        try:
            return float(str(value or "0").replace(",", ".").replace(" ", "").replace("\xa0", "").strip())
        except (ValueError, TypeError):
            return 0.0

    def _detect_type_operation(self, montant: float, mapped: dict) -> str:
        from_mapping = str(mapped.get("type_operation", "") or "").strip().lower()
        if from_mapping: return from_mapping
        trntype = str(mapped.get("trntype", "") or "").strip().upper()
        if trntype == "CREDIT": return "credit"
        if trntype == "DEBIT": return "depense"
        return "credit" if montant > 0 else "depense"

    def _extract_category(self, mapped: dict):
        cat_name = str(mapped.get("categorie", "") or "").strip() or "À catégoriser"
        cat_parent = str(mapped.get("categorie_parent", "") or "").strip() or None
        return cat_name, cat_parent


class OperationsImportHelpers(BaseHelper):
    def __init__(self, services):
        super().__init__(services)
        self.import_service = services.get("bank_import")
        self.operation_tracker = services.get("operation_import")
        self.file_import_trackers = services.get("file_tracker")  # Nécessaire pour le parent
        self.tiers_tracker = services.get("tiers")
        self.compte_tracker = services.get("compte")
        self.category_tracker = services.get("categorie")
        self.db_service = services.get("db")

    def initialise(self):
        self.operation_tracker.clear_cache()

    def get_status_counters(self):
        nb_saisies = nb_imports = 0
        if not self.db_service: return nb_saisies, nb_imports
        try:
            with self.db_service.get_connection() as conn:
                c = conn.cursor()
                # CORRECTION : bonne table "operations_bancaires_lignes"
                c.execute("SELECT COUNT(*) FROM operations_bancaires_lignes WHERE source = 'import_bancaire'")
                nb_imports = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM operations_bancaires_lignes WHERE source = 'saisie'")
                nb_saisies = c.fetchone()[0]
        except Exception:
            pass
        return nb_saisies, nb_imports

    def get_target_columns(self):
        obj = self.operation_tracker.get_new()
        if obj is None: return {}
        champs_a_exclure = {
            "id_import_ligne", "id_import", "numero_ligne", "created_at",
            # "parent_id",  ← SUPPRIMÉ
            "source", "compte_id", "tiers_id", "categorie_id", "compte_obj", "tiers_obj",
            "categorie_obj", "raw_json", "import_key",
        }
        params = inspect.signature(type(obj)).parameters
        return {f: f.replace("_", " ").capitalize() for f in params if f != "self" and f not in champs_a_exclure}

    def _check_doublon(self, date_operation: str, montant: float) -> bool:
        """Retourne True si une opération avec même date+montant existe déjà en BDD."""
        if not self.db_service:
            return False
        try:
            with self.db_service.get_connection() as conn:
                c = conn.cursor()
                c.execute(
                    "SELECT COUNT(*) FROM operations_bancaires_lignes "
                    "WHERE date_operation = ? AND montant = ?",
                    (date_operation, montant)
                )
                return c.fetchone()[0] > 0
        except Exception:
            return False

    # DANS OperationsImportHelpers
    def _process_rows(self, parent_window, raw_rows, mapping, import_id):
        processor = RowProcessor(self.compte_tracker, self.category_tracker,
                                 self.tiers_tracker, self.operation_tracker)
        validated = []
        ignored = 0

        for index, raw_row in enumerate(raw_rows, start=1):
            op = processor.process_row(parent_window, index, raw_row, mapping, import_id)
            if op is None: return None  # Annulation par l'utilisateur

            # VÉRIFICATION DOUBLON (assure la cohérence BDD)
            if self._check_doublon(op.date_operation, op.montant):
                ignored += 1
                continue

            validated.append(op)

        return validated, ignored  # <--- Retourne bien les deux valeurs

    def list_files(self) -> list[dict]:
        """
        Orchestre : récupère les statuts connus via le cat_trackers,
        puis délègue la lecture des fichiers au service.
        """
        # 1. Tracker → statuts connus (seul chemin légal vers la BDD)
        known_checksums = {
            imp.checksum: imp.statut
            for imp in (self.file_import_trackers.get_all() or [])
            if imp.checksum
        }

        # 2. Service → fichiers du dossier (aucun SQL ici)
        return self.import_service.list_input_files(known_checksums)

    def preview_file(self, path):
        return self.import_service.preview_file(path)

    # ------------------------------------------------------------------
    # IMPORT D'UN FICHIER (Méthode refactorisée)
    # ------------------------------------------------------------------

    def _initialize_file_import(self, path: str) -> int | None:
        """Crée ou récupère l'entrée d'import via le cat_trackers (jamais de SQL direct)."""
        p = Path(path)
        raw_rows = self.import_service._read_file(p)
        checksum = self.import_service._checksum(p)

        # Chercher un import existant avec ce checksum
        imports_existants = self.file_import_trackers.get_all()
        import_existant = next((imp for imp in imports_existants if imp.checksum == checksum), None)

        if import_existant:
            if import_existant.statut in ("nouveau", "erreur"):
                return import_existant.id_import  # Reprise après plantage
            else:
                raise ValueError(f"Le fichier '{p.name}' a déjà été importé avec succès.")

        # Nouveau fichier → création via cat_trackers
        nouvel_import = self.file_import_trackers.get_new()
        nouvel_import.fichier = p.name
        nouvel_import.chemin = str(p)
        nouvel_import.format_fichier = p.suffix.lstrip(".").lower()
        nouvel_import.nb_lignes = len(raw_rows)
        nouvel_import.checksum = checksum
        nouvel_import.statut = "nouveau"

        import_enregistre = self.file_import_trackers.add(nouvel_import)

        if import_enregistre and hasattr(import_enregistre, "id_import"):
            return import_enregistre.id_import

        return None

    def _update_file_import(self, import_id: int, nouveau_statut: str):
        """Met à jour le statut du fichier dans la table imports_bancaires."""
        # 1. On récupère l'objet correspondant via le tiers_trackers
        imports_existants = self.file_import_trackers.get_all()
        import_obj = next((imp for imp in imports_existants if imp.id_import == import_id), None)

        # 2. Si on le trouve, on modifie son statut et on sauvegarde
        if import_obj:
            import_obj.statut = nouveau_statut

            # Selon le nom exact de votre méthode dans GenericTracker :
            # ça peut être self.file_import_trackers.update(import_obj)
            # ou self.file_import_trackers.save(import_obj)
            self.file_import_trackers.update(import_obj)

    def import_file(self, parent_window, path: str, mapping: dict) -> dict:
        """Orchestre l'import complet d'un fichier bancaire."""
        p = Path(path)

        # 1. Lecture des lignes brutes via le service
        raw_rows = self.import_service._read_file(p)
        if not raw_rows:
            return {"success": True, "rows": 0, "ignored": 0, "details": {}}

        # 2. Initialisation de l'entrée d'import (via cat_trackers uniquement)
        import_id = self._initialize_file_import(path)
        if not import_id:
            return {"success": False, "message": "Échec init import.", "rows": 0, "ignored": 0}

        # 3. Traitement ligne par ligne
        result_process = self._process_rows(parent_window, raw_rows, mapping, import_id)
        if result_process is None:
            return {"success": False, "message": "Import annulé.", "rows": 0, "ignored": 0}

        validated_ops, ignored = result_process

        # 4. Sauvegarde en BDD via le cat_trackers
        result = self.operation_tracker.save_all(validated_ops)

        # 5. Mise à jour du statut du fichier
        self._update_file_import(import_id, "deja_importe")

        return {"success": True, "rows": len(validated_ops), "ignored": ignored, "details": result}
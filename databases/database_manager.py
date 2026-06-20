# -*- coding: utf-8 -*-
####################################
# Projet : CostTracker
# Fichier : databases/database_manager.py
# Description : Gestionnaire SQLite — schéma piloté par les classes modèles
# Date : 20/06/2026     Etat : Stable
####################################

import sqlite3
from pathlib import Path

from databases.schema_inspector import SchemaInspector, ModelRegistry


class DatabaseManager:
    def __init__(self, config):
        self.config = config

        db_dir  = config.get("DATABASE_DIRECTORY")
        db_name = config.get("DATABASE_NAME")

        if db_dir is None or db_name is None:
            raise ValueError(
                f"Config manquante : DATABASE_DIRECTORY={db_dir}, DATABASE_NAME={db_name}. "
                "Vérifiez votre fichier de configuration ou votre .env !"
            )

        self.db_path = Path(db_dir) / db_name
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialized = False

    # ----------------------------------------------------------------- #
    #  Connexion
    # ----------------------------------------------------------------- #

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def get_connection(self) -> sqlite3.Connection:
        if not self.db_path.exists() or not self._initialized:
            self.init_database()
        return self._connect()

    # ----------------------------------------------------------------- #
    #  Initialisation / migration
    # ----------------------------------------------------------------- #

    def init_database(self):
        """
        Crée ou met à jour toutes les tables à partir des modèles enregistrés
        dans ModelRegistry. Remplace la lecture du JSON de schéma.
        """
        if not ModelRegistry.all_tables():
            # Aucun modèle enregistré → import automatique des modèles connus
            self._auto_import_models()

        with self._connect() as conn:
            SchemaInspector.sync_all(conn, verbose=True)
            self._ensure_indexes(conn)
            self._migrate_legacy_operations(conn)
            conn.commit()

        self._initialized = True

    @staticmethod
    def _auto_import_models():
        """
        Importe les modules modèles pour déclencher les @register_model.
        Adaptez cette liste à l'arborescence de votre projet.
        """
        import importlib
        _KNOWN_MODEL_MODULES = [
            "models.type_compte",
            "models.operations",
            "models.compte",
            "models.tiers",
            "models.categorie",
            # Ajoutez ici tout nouveau module modèle
        ]
        for module_path in _KNOWN_MODEL_MODULES:
            try:
                importlib.import_module(module_path)
            except ModuleNotFoundError:
                pass  # module optionnel non présent dans ce déploiement

    # ----------------------------------------------------------------- #
    #  Index
    # ----------------------------------------------------------------- #

    def _ensure_indexes(self, conn):
        conn.executescript("""
            CREATE INDEX IF NOT EXISTS idx_operations_date
                ON operations_bancaires_lignes(date_operation);
            CREATE INDEX IF NOT EXISTS idx_operations_source
                ON operations_bancaires_lignes(source);
            CREATE INDEX IF NOT EXISTS idx_operations_import
                ON operations_bancaires_lignes(id_import);
            CREATE INDEX IF NOT EXISTS idx_operations_compte
                ON operations_bancaires_lignes(compte_id);
        """)

    # ----------------------------------------------------------------- #
    #  Migration legacy
    # ----------------------------------------------------------------- #

    def _migrate_legacy_operations(self, conn):
        """Migration one-shot depuis l'ancienne table 'operations'."""
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='operations'")
        if cur.fetchone() is None:
            return

        cur.execute("PRAGMA table_info(operations)")
        columns = {row["name"] for row in cur.fetchall()}
        if not {"id_operation", "date_operation", "montant"}.issubset(columns):
            return

        cur.execute("SELECT COUNT(*) FROM operations")
        if cur.fetchone()[0] == 0:
            return

        print("[MIGRATION] Ancienne table 'operations' détectée → migration vers operations_bancaires_lignes")

        select_cols = [
            "id_operation",
            "date_operation",
            "date_value AS date_valeur" if "date_value" in columns else "NULL AS date_valeur",
            "montant",
            "compte_id"    if "compte_id"    in columns else "NULL AS compte_id",
            "tiers_id"     if "tiers_id"     in columns else "NULL AS tiers_id",
            "categorie_id" if "categorie_id" in columns else "NULL AS categorie_id",
        ]
        cur.execute(f"SELECT {', '.join(select_cols)} FROM operations")

        migrated = 0
        for row in cur.fetchall():
            montant    = float(row["montant"] or 0)
            import_key = f"migration_{row['id_operation']}"
            cur.execute(
                """
                INSERT OR IGNORE INTO operations_bancaires_lignes
                    (date_operation, date_valeur, libelle, montant, type_operation,
                     source, compte_id, tiers_id, categorie_id, import_key)
                VALUES (?, ?, ?, ?, ?, 'saisie', ?, ?, ?, ?)
                """,
                (
                    str(row["date_operation"] or ""),
                    str(row["date_valeur"]    or ""),
                    "Opération migrée",
                    montant,
                    "revenu" if montant >= 0 else "depense",
                    row["compte_id"],
                    row["tiers_id"],
                    row["categorie_id"],
                    import_key,
                ),
            )
            migrated += 1

        print(f"[MIGRATION] {migrated} opérations migrées.")

    # ----------------------------------------------------------------- #
    #  Utilitaire : rapport de schéma
    # ----------------------------------------------------------------- #

    def schema_report(self) -> list[dict]:
        """
        Retourne un rapport de diff entre le schéma attendu (modèles)
        et la base de données réelle. Utile pour le debug.
        """
        with self._connect() as conn:
            reports = []
            for table_name, model_cls in ModelRegistry.all_tables().items():
                reports.append(SchemaInspector.diff(conn, model_cls))
        return reports

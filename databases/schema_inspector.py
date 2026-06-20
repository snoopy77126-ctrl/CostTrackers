# -*- coding: utf-8 -*-
####################################
# Projet : CostTracker
# Fichier : databases/schema_inspector.py
# Description : Registre des modèles et inspection dynamique du schéma SQL
# Date : 20/06/2026     Etat : Stable
####################################

from __future__ import annotations
import dataclasses
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models._model_base import ModelBase


# ══════════════════════════════════════════════════════════════════════ #
#  REGISTRE GLOBAL DES MODÈLES
# ══════════════════════════════════════════════════════════════════════ #

class ModelRegistry:
    """
    Registre singleton des classes modèles.
    Chaque modèle s'y enregistre via @register_model ou ModelRegistry.register().

    Permet à DatabaseManager de connaître toutes les tables attendues
    sans importer chaque module manuellement.
    """

    _models: dict[str, type[ModelBase]] = {}  # table_name → classe

    @classmethod
    def register(cls, model_cls: type[ModelBase]) -> type[ModelBase]:
        """Enregistre une classe modèle. Retourne la classe (utilisable en décorateur)."""
        table = model_cls.sql_table()
        if table in cls._models and cls._models[table] is not model_cls:
            raise ValueError(
                f"Conflit de table '{table}' : {cls._models[table].__name__} "
                f"et {model_cls.__name__} pointent vers la même table."
            )
        cls._models[table] = model_cls
        return model_cls

    @classmethod
    def all_tables(cls) -> dict[str, type[ModelBase]]:
        """Retourne {table_name: model_class} pour toutes les classes enregistrées."""
        return dict(cls._models)

    @classmethod
    def get(cls, table_name: str) -> type[ModelBase] | None:
        return cls._models.get(table_name)

    @classmethod
    def clear(cls):
        """Vide le registre (utile pour les tests)."""
        cls._models.clear()


def register_model(cls):
    """Décorateur : @register_model enregistre la classe dans ModelRegistry."""
    return ModelRegistry.register(cls)


# ══════════════════════════════════════════════════════════════════════ #
#  SCHEMA INSPECTOR
# ══════════════════════════════════════════════════════════════════════ #

class SchemaInspector:
    """
    Génère et compare les schémas SQL à partir des classes modèles enregistrées.
    Utilisé par DatabaseManager pour créer/migrer les tables dynamiquement.
    """

    @staticmethod
    def expected_schema(model_cls: type[ModelBase]) -> list[dict]:
        """
        Retourne la liste de colonnes attendues pour une classe modèle.
        Format : [{"name": str, "type": str}, ...]
        Compatible avec DatabaseManager._create_table().
        """
        return model_cls.sql_schema()

    @staticmethod
    def actual_columns(conn, table_name: str) -> set[str]:
        """Retourne les noms de colonnes effectivement présentes dans la table."""
        cur = conn.execute(f"PRAGMA table_info({table_name})")
        return {row["name"] for row in cur.fetchall()}

    @staticmethod
    def table_exists(conn, table_name: str) -> bool:
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        return cur.fetchone() is not None

    @classmethod
    def diff(cls, conn, model_cls: type[ModelBase]) -> dict:
        """
        Compare le schéma attendu (depuis le modèle) avec la table réelle.

        Retourne un dict :
        {
            "table":    str,
            "exists":   bool,
            "missing_columns": [{"name": str, "type": str}],   # à ajouter
            "extra_columns":   [str],                           # présentes en DB mais pas dans le modèle
        }
        """
        table = model_cls.sql_table()
        expected = {col["name"]: col for col in cls.expected_schema(model_cls)}

        if not cls.table_exists(conn, table):
            return {
                "table": table,
                "exists": False,
                "missing_columns": list(expected.values()),
                "extra_columns": [],
            }

        actual = cls.actual_columns(conn, table)
        missing = [col for name, col in expected.items() if name not in actual]
        extra   = [name for name in actual if name not in expected]

        return {
            "table": table,
            "exists": True,
            "missing_columns": missing,
            "extra_columns": extra,
        }

    @classmethod
    def sync_all(cls, conn, verbose: bool = True) -> list[dict]:
        """
        Crée ou met à jour toutes les tables enregistrées dans ModelRegistry.
        Retourne la liste des rapports de diff par table.
        """
        reports = []
        for table_name, model_cls in ModelRegistry.all_tables().items():
            report = cls.diff(conn, model_cls)
            reports.append(report)

            if not report["exists"]:
                cls._create_table(conn, model_cls)
                if verbose:
                    print(f"[SCHEMA] Table créée : {table_name}")
            else:
                for col in report["missing_columns"]:
                    base_type = col["type"].split()[0]
                    conn.execute(
                        f"ALTER TABLE {table_name} ADD COLUMN {col['name']} {base_type}"
                    )
                    if verbose:
                        print(f"[SCHEMA] Colonne ajoutée : {table_name}.{col['name']}")

                if report["extra_columns"] and verbose:
                    print(
                        f"[SCHEMA] Colonnes orphelines dans '{table_name}' "
                        f"(non gérées par le modèle) : {report['extra_columns']}"
                    )

        return reports

    @staticmethod
    def _create_table(conn, model_cls: type[ModelBase]):
        """Crée la table à partir du schéma du modèle."""
        table = model_cls.sql_table()
        cols  = model_cls.sql_schema()
        col_defs = ", ".join(f"{c['name']} {c['type']}" for c in cols)
        conn.execute(f"CREATE TABLE IF NOT EXISTS {table} ({col_defs});")

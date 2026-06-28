# -*- coding: utf-8 -*-
####################################
# Projet : CostTracker
# Fichier : models/_model_base.py
# Description : Classes de base pour tous les modèles — gestion SQL dynamique
# Date : 20/06/2026     Etat : Stable
####################################

import dataclasses
from dataclasses import asdict, fields
from typing import ClassVar, Optional
from typing import get_type_hints


# ══════════════════════════════════════════════════════════════════════ #
#  MARQUEURS DE CHAMPS
# ══════════════════════════════════════════════════════════════════════ #

def transient_field(**kwargs):
    """
    Déclare un champ comme transient (non persisté en base).
    Usage : mon_objet: list = transient_field(default_factory=list)
    """
    metadata = {**kwargs.pop("metadata", {}), "_transient": True}
    return dataclasses.field(**kwargs, metadata=metadata)


def sql_field(sql_type: str = "TEXT", primary_key: bool = False, **kwargs):
    """
    Déclare un champ persisté avec son type SQL explicite.
    Usage : montant: float = sql_field("REAL", default=0.0)
    """
    metadata = {
        **kwargs.pop("metadata", {}),
        "_sql_type": sql_type,
        "_primary_key": primary_key,
    }
    return dataclasses.field(**kwargs, metadata=metadata)


# ══════════════════════════════════════════════════════════════════════ #
#  CORRESPONDANCE PYTHON → SQL
# ══════════════════════════════════════════════════════════════════════ #

_PY_TO_SQL: dict[type, str] = {
    int:   "INTEGER",
    float: "REAL",
    str:   "TEXT",
    bool:  "INTEGER",  # SQLite stocke les booléens en INTEGER
    bytes: "BLOB",
}


def _python_type_to_sql(annotation) -> str:
    """Résout le type SQL depuis une annotation Python (gère Optional[X])."""
    import typing

    origin = getattr(annotation, "__origin__", None)
    if origin is typing.Union:
        # Optional[X] == Union[X, None]
        args = [a for a in annotation.__args__ if a is not type(None)]
        if args:
            return _python_type_to_sql(args[0])

    return _PY_TO_SQL.get(annotation, "TEXT")

def _to_int_bool(val) -> int:
    """Convertit proprement un booléen, un entier ou une string vers 0/1."""
    if isinstance(val, str):
        return 1 if val.strip().lower() in ('true', '1', 'yes', 'oui') else 0
    return int(bool(val))

# ══════════════════════════════════════════════════════════════════════ #
#  MODEL BASE
# ══════════════════════════════════════════════════════════════════════ #

class ModelBase:
    """
    Mixin pour tous les modèles dataclass.

    Fournit :
    - sql_id         : nom de la colonne PK (détecté automatiquement ou via SQL_ID)
    - sql_fields()   : liste ordonnée des champs persistés
    - sql_schema()   : liste de ColumnInfo pour la création/migration de table
    - is_new()       : True si la PK est None
    - to_sql_dict()  : dict des colonnes persistées
    - from_dict()    : constructeur depuis un dict BDD (ignore les clés inconnues)

    SQL_TABLE peut être défini dans la sous-classe pour nommer explicitement
    la table. Par défaut, le nom de la classe en snake_case est utilisé.

    SQL_ID peut être défini pour forcer la PK. Sinon, le premier champ
    Optional[int] dont le nom commence par "id_" est retenu.

    Les champs marqués via transient_field() ou dont le nom figure dans
    _TRANSIENT_FIELDS (ClassVar) sont exclus de la persistance.
    """

    # ---- Surchargeables dans les sous-classes ----------------------- #
    SQL_TABLE:  ClassVar[Optional[str]] = None   # None → snake_case du nom de classe
    SQL_ID:     ClassVar[Optional[str]] = None   # None → auto-détecté
    _TRANSIENT_FIELDS: ClassVar[tuple]  = ()     # noms explicitement exclus

    # ----------------------------------------------------------------- #

    @classmethod
    def _dataclass_fields(cls) -> tuple[dataclasses.Field, ...]:
        """Retourne les champs dataclass de la classe (lève si non-dataclass)."""
        if not dataclasses.is_dataclass(cls):
            raise TypeError(f"{cls.__name__} doit être une dataclass.")
        return dataclasses.fields(cls)

    @classmethod
    def _is_transient(cls, f: dataclasses.Field) -> bool:
        """True si le champ ne doit PAS être persisté."""
        if f.name in cls._TRANSIENT_FIELDS:
            return True
        if f.metadata.get("_transient"):
            return True
        # Les ClassVar ne sont pas des champs dataclass, mais par sécurité :
        if f.name.startswith("_"):
            return True
        return False

    @classmethod
    def sql_fields(cls) -> list[str]:
        """Liste ordonnée des noms de colonnes persistées."""
        return [f.name for f in cls._dataclass_fields() if not cls._is_transient(f)]

    @classmethod
    def sql_id(cls) -> str:
        """Nom de la colonne clé primaire."""
        # 1. Valeur explicite dans la sous-classe
        if cls.SQL_ID:
            return cls.SQL_ID

        # 2. Auto-détection : premier Optional[int] dont le nom commence par "id_"
        hints = get_type_hints(cls)
        for f in cls._dataclass_fields():
            if f.metadata.get("_primary_key"):
                return f.name
            hint = hints.get(f.name)
            if f.name.startswith("id_") and _python_type_to_sql(hint) == "INTEGER":
                return f.name

        raise AttributeError(
            f"{cls.__name__} : impossible de détecter la PK. "
            "Définissez SQL_ID ou utilisez sql_field(primary_key=True)."
        )

    @classmethod
    def sql_table(cls) -> str:
        """Nom de la table SQL."""
        if cls.SQL_TABLE:
            return cls.SQL_TABLE
        # CamelCase → snake_case
        import re
        name = cls.__name__
        return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()

    @classmethod
    def sql_schema(cls) -> list[dict]:
        """
        Retourne la liste des colonnes avec leurs métadonnées SQL.
        Chaque élément : {"name": str, "sql_type": str, "primary_key": bool}
        Compatible avec le format attendu par DatabaseManager._create_table().
        """
        hints = get_type_hints(cls)
        pk = cls.sql_id()
        schema = []

        for f in cls._dataclass_fields():
            if cls._is_transient(f):
                continue

            sql_type = f.metadata.get("_sql_type") or _python_type_to_sql(hints.get(f.name, str))
            is_pk = f.name == pk

            col: dict = {"name": f.name, "type": sql_type}
            if is_pk:
                col["type"] = "INTEGER PRIMARY KEY AUTOINCREMENT"

            schema.append(col)

        return schema

    # ---- Helpers d'instance ----------------------------------------- #

    def is_new(self) -> bool:
        """True si l'objet n'a pas encore de PK (non persisté)."""
        return getattr(self, self.__class__.sql_id(), None) is None

    def to_sql_dict(self) -> dict:
        """Dict des colonnes persistées (valeurs de l'instance)."""
        return {name: getattr(self, name, None) for name in self.__class__.sql_fields()}

    @classmethod
    def from_dict(cls, data: dict):
        """Construit une instance depuis un dict BDD (ignore les clés inconnues)."""
        import inspect
        valid = set(inspect.signature(cls).parameters.keys())
        return cls(**{k: v for k, v in data.items() if k in valid})

    def to_dict(self) -> dict:
        """
        Dictionnaire complet de l'objet (tous les champs dataclass).
        Les champs transients (objets liés, non picklables) sont inclus
        sous forme de None — les surcharges peuvent les exclure.
        """
        try:
            return asdict(self)
        except Exception:
            # Fallback si asdict échoue (champs non-dataclass imbriqués)
            return {f.name: getattr(self, f.name, None) for f in fields(self)}

    @property
    def display_name(self) -> str:
        pk_val = getattr(self, self.__class__.sql_id(), None)
        return f"{self.__class__.__name__} {pk_val or '(nouveau)'}"


# ══════════════════════════════════════════════════════════════════════ #
#  WITH LINKED OBJECTS — mixin pour les objets liés transients
# ══════════════════════════════════════════════════════════════════════ #

class WithLinkedObjects:
    """
    Mixin qui ajoute des slots transients pour porter les objets liés
    (compte, tiers, catégorie) sans les persister.
    """

    _TRANSIENT_FIELDS: ClassVar[tuple] = ("compte_obj", "tiers_obj", "categorie_obj")

    compte_obj:    object = transient_field(default=None)
    tiers_obj:     object = transient_field(default=None)
    categorie_obj: object = transient_field(default=None)

    @property
    def compte_label(self) -> str:
        return getattr(self.compte_obj, "display_name", "") if self.compte_obj else ""

    @property
    def tiers_label(self) -> str:
        return getattr(self.tiers_obj, "display_name", "") if self.tiers_obj else ""

    @property
    def categorie_label(self) -> str:
        return getattr(self.categorie_obj, "display_name", "") if self.categorie_obj else ""

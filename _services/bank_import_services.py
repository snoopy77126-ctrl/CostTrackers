# -*- coding: utf-8 -*-
####################################
# Projet : CostTracker
# Fichier : _services/bank_import_services.py
# Description : Service d'import bancaire multi-format
# Date : 24/06/2026     Etat : Stable
####################################

import hashlib
from pathlib import Path

from _services.bank_import.parsers.csv_parser import CsvParser
from _services.bank_import.parsers.ofx_parser import OfxParser
from _services.bank_import.parsers.xlsx_parser import XlsxParser
from _services.bank_import.parsers.qif_parser import QifParser
from _services.bank_import.parsers.money_csv_parser import MoneyCsvParser


def _is_money_csv(path: Path) -> bool:
    """Détecte un CSV Money à la signature (colonnes OU pas d'en-tête + chiffre en col 0)."""
    import re, csv
    MONEY_PATTERNS = [r"num[eé]ro", r"cat[eé]gories?", r"sous.cat[eé]gorie", r"compte.virement"]
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            with open(path, "r", encoding=enc, errors="replace") as f:
                sample = f.read(512)
            first = sample.splitlines()[0].lower()
            hits = sum(1 for p in MONEY_PATTERNS if re.search(p, first))
            if hits >= 2:
                return True
            # Sans en-tête : première cellule est un entier
            first_cell = first.split(";")[0].strip() if ";" in first else first.split(",")[0].strip()
            if first_cell.isdigit():
                return True
            break
        except Exception:
            pass
    return False


class BankImportService:
    TARGET_COLUMNS = {
        "dateOp":   "Date opération",
        "dateVal":  "Date valeur",
        "label":    "Libellé",
        "amount":   "Montant",
        "categorie":        "Catégorie",
        "categorie_parent": "Catégorie parent",
        "compte_label":     "Compte",
        "commentaire":      "Commentaire",
        "fitid":    "Identifiant unique",
    }

    def __init__(self, db_service, cfg):
        self.db_service = db_service
        self.input_dir  = Path(cfg.get("input_directory"))
        self.input_dir.mkdir(parents=True, exist_ok=True)

        self._parsers = {
            ".ofx":  OfxParser(),
            ".xlsx": XlsxParser(),
            ".qif":  QifParser(),
            # CSV délégué dynamiquement (Money vs générique)
        }
        self._csv_parser       = CsvParser()
        self._money_csv_parser = MoneyCsvParser()

    # ── Lecture ───────────────────────────────────────────────────────

    def _read_file(self, path: Path) -> list[dict]:
        suffix = path.suffix.lower()
        if suffix == ".csv":
            if _is_money_csv(path):
                return self._money_csv_parser.parse(path)
            return self._csv_parser.parse(path)
        parser = self._parsers.get(suffix)
        if not parser:
            raise ValueError(f"Format non géré : {suffix}  (fichier : {path.name})")
        return parser.parse(path)

    # ── Listing des fichiers ──────────────────────────────────────────

    def list_input_files(self, known_checksums: dict = None) -> list[dict]:
        known_checksums = known_checksums or {}
        supported = {".csv", ".ofx", ".xlsx", ".qif"}
        files = []
        if not self.input_dir.exists():
            return files

        for p in sorted(self.input_dir.iterdir()):
            if not p.is_file():
                continue
            if p.suffix.lower() not in supported:
                continue
            try:
                chk  = self._checksum(p)
                rows = self._read_file(p)
                files.append({
                    "filename": p.name,
                    "path":     str(p),
                    "format":   p.suffix[1:].upper(),
                    "rows":     len(rows),
                    "checksum": chk,
                    "status":   known_checksums.get(chk, "a_importer"),
                })
            except Exception:
                continue
        return files

    # ── Prévisualisation ──────────────────────────────────────────────

    def preview_file(self, path) -> dict:
        path = Path(path)
        rows = self._read_file(path)
        columns = list(rows[0].keys()) if rows else []
        return {
            "filename":  path.name,
            "format":    path.suffix[1:].upper(),
            "row_count": len(rows),
            "columns":   columns,
            "rows":      rows[:50],
            "mapping":   {col: "" for col in self.TARGET_COLUMNS},
        }

    # ── Utilitaires ───────────────────────────────────────────────────

    @staticmethod
    def _checksum(path: Path) -> str:
        return hashlib.md5(path.read_bytes()).hexdigest()

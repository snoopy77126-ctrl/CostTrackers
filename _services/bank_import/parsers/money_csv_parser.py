# -*- coding: utf-8 -*-
####################################
# Projet : CostTracker
# Fichier : _services/bank_import/parsers/money_csv_parser.py
# Description : Parseur CSV export Microsoft Money (format spécifique)
# Date : 24/06/2026     Etat : Stable
####################################

import csv
import re
from pathlib import Path
from .base_parser import BaseParser

# Colonnes de l'export Money (avec ou sans ligne d'en-tête)
MONEY_COLS = [
    "numero", "date", "montant", "etat", "tiers",
    "categorie", "sous_categorie", "compte",
    "compte_virement", "mode_paiement", "ref_paiement",
    "reference", "projets", "commentaire",
]

# Signature des en-têtes Money (variantes FR)
MONEY_HEADER_PATTERNS = [
    r"num[eé]ro", r"cat[eé]gories?", r"sous.cat[eé]gorie",
    r"compte.virement", r"mode.paiement",
]


class MoneyCsvParser(BaseParser):
    """
    Parseur pour les exports CSV de Microsoft Money.

    Deux variantes :
    - Avec en-tête  : Numéro;Date;Montant;Etat;Tiers;Catégories;...
    - Sans en-tête  : 0;20240828;-11,00;2;Leclerc;...
    """

    def parse(self, path: Path) -> list[dict]:
        rows = []

        for enc in ("utf-8-sig", "cp1252", "latin-1"):
            try:
                with open(path, "r", encoding=enc, errors="replace") as f:
                    sample = f.read(512)
                    f.seek(0)
                    has_header = self._has_money_header(sample)
                    delimiter  = ";" if ";" in sample else ","

                    reader = csv.reader(f, delimiter=delimiter)
                    raw_rows = list(reader)

                if raw_rows:
                    break
            except Exception:
                raw_rows = []

        if not raw_rows:
            return rows

        if has_header:
            data_rows = raw_rows[1:]
        else:
            data_rows = raw_rows

        for raw in data_rows:
            raw = [c.strip().strip('"') for c in raw]
            if len(raw) < 5 or not any(raw):
                continue

            # Padding si colonnes manquantes
            while len(raw) < len(MONEY_COLS):
                raw.append("")

            entry = dict(zip(MONEY_COLS, raw))
            rows.append(self._normalize(entry))

        return rows

    @staticmethod
    def _has_money_header(sample: str) -> bool:
        first_line = sample.splitlines()[0].lower() if sample else ""
        matched = sum(1 for p in MONEY_HEADER_PATTERNS if re.search(p, first_line))
        return matched >= 2

    @staticmethod
    def _normalize(entry: dict) -> dict:
        raw_date = entry.get("date", "").strip()
        raw_amt  = entry.get("montant", "0").replace(",", ".").replace(" ", "")

        try:
            montant = float(raw_amt)
        except ValueError:
            montant = 0.0

        # Normaliser la date : YYYYMMDD → YYYY-MM-DD  ou  DD/MM/YYYY → YYYY-MM-DD
        date_str = ""
        if len(raw_date) == 8 and raw_date.isdigit():
            date_str = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:8]}"
        elif "/" in raw_date:
            parts = raw_date.split("/")
            if len(parts) == 3:
                d, m, y = parts
                if len(y) == 4:
                    date_str = f"{y}-{m.zfill(2)}-{d.zfill(2)}"
                elif len(d) == 4:
                    date_str = f"{d}-{m.zfill(2)}-{y.zfill(2)}"
        else:
            date_str = raw_date

        cat      = entry.get("categorie", "").strip()
        sous_cat = entry.get("sous_categorie", "").strip()
        compte   = entry.get("compte", "").strip()

        return {
            "dateOp":          date_str,
            "dateVal":         date_str,
            "label":           entry.get("tiers", "").strip(),
            "amount":          str(montant),
            "categorie":       sous_cat or cat,
            "categorie_parent": cat if sous_cat else "",
            "compte_label":    compte,
            "commentaire":     entry.get("commentaire", "").strip(),
            "trntype":         "CREDIT" if montant >= 0 else "DEBIT",
            "fitid":           entry.get("reference", "").strip(),
            "mode_paiement":   entry.get("mode_paiement", "").strip(),
        }

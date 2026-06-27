# -*- coding: utf-8 -*-
####################################
# Projet : CostTracker
# Fichier : _services/bank_import/parsers/csv_parser.py
# Description : Parseur CSV générique avec auto-détection du format
# Date : 24/06/2026     Etat : Stable
####################################

import csv
import re
from pathlib import Path
from .base_parser import BaseParser

# Signatures de formats connus (détection par en-tête)
_BOURSOBANK_COLS  = {"dateop", "dateval", "label", "amount"}
_MONEY_PATTERNS   = [r"num[eé]ro", r"cat[eé]gories?", r"sous.cat[eé]gorie", r"compte.virement"]
_CATEGORIES_COLS  = {"d[eé]signation", "groupe.de.cat[eé]gories?", "type"}


class CsvParser(BaseParser):
    """
    Parseur CSV universel — détecte automatiquement :
    - BoursoBank / Linxo (dateOp;dateVal;label;amount;...)
    - Microsoft Money (Numéro;Date;Montant;Etat;Tiers;...)
    - Autre CSV bancaire (heuristique)

    Retourne des dicts avec clés normalisées compatibles BankImportService.
    """

    def parse(self, path: Path) -> list[dict]:
        for enc in ("utf-8-sig", "cp1252", "latin-1"):
            try:
                with open(path, "r", encoding=enc, errors="replace") as f:
                    sample = f.read(2048)
                    if not sample.strip():
                        return []
                    f.seek(0)
                    delimiter = self._detect_delimiter(sample)
                    reader = csv.DictReader(f, delimiter=delimiter)
                    if reader.fieldnames:
                        reader.fieldnames = [
                            fn.strip().strip('"').strip("'")
                            for fn in reader.fieldnames if fn
                        ]
                    raw_rows = [
                        {k.strip(): (v.strip() if v else "")
                         for k, v in row.items() if k}
                        for row in reader
                        if any(v and v.strip() for v in row.values() if v)
                    ]
                break
            except Exception:
                raw_rows = []

        if not raw_rows:
            return []

        fmt = self._detect_format(raw_rows[0] if raw_rows else {})

        if fmt == "boursobank":
            return [self._normalize_boursobank(r) for r in raw_rows]
        elif fmt == "money":
            from .money_csv_parser import MoneyCsvParser
            return MoneyCsvParser().parse(path)
        else:
            # Format générique : retour brut, laisse le mapping UI faire le travail
            return raw_rows

    # ── Détection ─────────────────────────────────────────────────────

    @staticmethod
    def _detect_delimiter(sample: str) -> str:
        counts = {d: sample.count(d) for d in (";", ",", "\t")}
        return max(counts, key=counts.get)

    @staticmethod
    def _detect_format(row: dict) -> str:
        keys_lower = {k.lower() for k in row}

        # BoursoBank / Linxo : présence de dateop + amount (ou amount)
        if {"dateop", "amount"}.issubset(keys_lower) or \
           {"dateval", "label"}.issubset(keys_lower):
            return "boursobank"

        # Money : numéro + categorie + sous-categorie
        header_str = " ".join(keys_lower)
        money_hits = sum(1 for p in _MONEY_PATTERNS if re.search(p, header_str))
        if money_hits >= 2:
            return "money"

        return "generic"

    # ── Normalisation BoursoBank ───────────────────────────────────────

    @staticmethod
    def _normalize_boursobank(row: dict) -> dict:
        # Cherche les clés sans tenir compte de la casse
        def get(keys):
            for k in keys:
                for rk, rv in row.items():
                    if rk.lower() == k.lower():
                        return rv
            return ""

        raw_amt = get(["amount"]).replace(",", ".").replace("\xa0", "").replace(" ", "")
        try:
            montant = float(raw_amt)
        except ValueError:
            montant = 0.0

        # Date : YYYY-MM-DD (déjà normalisé) ou DD/MM/YYYY
        raw_date = get(["dateOp", "dateop"])
        date_str = raw_date
        if "/" in raw_date:
            parts = raw_date.split("/")
            if len(parts) == 3 and len(parts[2]) == 4:
                date_str = f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"

        # Label : préférer suggestedLabel si dispo, sinon label
        label = get(["suggestedLabel"]) or get(["label"])

        return {
            "dateOp":           date_str,
            "dateVal":          get(["dateVal", "dateval"]) or date_str,
            "label":            label,
            "amount":           str(montant),
            "categorie":        get(["category"]),
            "categorie_parent": get(["categoryParent"]),
            "compte_num":       get(["accountNum"]),
            "compte_label":     get(["accountLabel"]),
            "commentaire":      get(["comment"]),
            "trntype":          "CREDIT" if montant >= 0 else "DEBIT",
            "fitid":            "",
        }

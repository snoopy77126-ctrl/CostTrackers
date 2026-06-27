# -*- coding: utf-8 -*-
####################################
# Projet : CostTracker
# Fichier : _services/bank_import/parsers/qif_parser.py
# Description : Parseur QIF (Quicken Interchange Format) — BoursoBank, Money, etc.
# Date : 24/06/2026     Etat : Stable
####################################

from pathlib import Path
from .base_parser import BaseParser


class QifParser(BaseParser):
    """
    Parseur QIF standard.
    Supporte les champs : D (date), T (montant), P (tiers/payee),
    M (memo), L (catégorie), N (numéro), C (statut).
    Retourne des dicts normalisés compatibles avec BankImportService.
    """

    def parse(self, path: Path) -> list[dict]:
        rows = []

        for enc in ("utf-8-sig", "latin-1", "cp1252"):
            try:
                content = path.read_text(encoding=enc, errors="replace")
                break
            except Exception:
                content = None

        if not content:
            return rows

        current: dict = {}

        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("!"):
                continue

            code = line[0].upper()
            value = line[1:].strip()

            if code == "^":
                # Fin d'enregistrement
                if current:
                    rows.append(self._normalize(current))
                    current = {}
            elif code == "D":
                current["D"] = value
            elif code == "T":
                current["T"] = value
            elif code == "P":
                current["P"] = value
            elif code == "M":
                current["M"] = value
            elif code == "L":
                current["L"] = value
            elif code == "N":
                current["N"] = value
            elif code == "C":
                current["C"] = value

        # Dernier bloc sans ^ final
        if current:
            rows.append(self._normalize(current))

        return rows

    def _normalize(self, entry: dict) -> dict:
        """Convertit un bloc QIF en dict normalisé (clés compatibles BankImportService)."""
        raw_date = entry.get("D", "")
        raw_amt  = entry.get("T", "0").replace(",", ".").replace(" ", "")

        try:
            montant = float(raw_amt)
        except ValueError:
            montant = 0.0

        return {
            "dateOp":  self._parse_date(raw_date),
            "dateVal": self._parse_date(raw_date),
            "label":   entry.get("P", ""),
            "amount":  str(montant),
            "memo":    entry.get("M", ""),
            "categorie": entry.get("L", ""),
            "fitid":   entry.get("N", ""),
            "trntype": "CREDIT" if montant >= 0 else "DEBIT",
        }

    @staticmethod
    def _parse_date(raw: str) -> str:
        """Normalise les dates QIF (DD/MM/YYYY, MM/DD/YYYY, YYYYMMDD…) → YYYY-MM-DD."""
        raw = raw.strip().replace("-", "/")
        for sep in ("/", "."):
            parts = raw.split(sep)
            if len(parts) == 3:
                a, b, c = parts
                # DD/MM/YYYY (français)
                if len(c) == 4:
                    try:
                        return f"{c}-{b.zfill(2)}-{a.zfill(2)}"
                    except Exception:
                        pass
                # YYYY/MM/DD
                if len(a) == 4:
                    try:
                        return f"{a}-{b.zfill(2)}-{c.zfill(2)}"
                    except Exception:
                        pass
        # YYYYMMDD
        if len(raw) == 8 and raw.isdigit():
            return f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"
        return raw

import re
from pathlib import Path
from .base_parser import BaseParser


class OfxParser(BaseParser):
    def parse(self, path: Path) -> list[dict]:
        rows = []
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            try:
                content = path.read_text(encoding="latin-1", errors="ignore")
            except Exception:
                return []

        # Extraction des blocs d'opérations <STMTTRN>
        pattern_trn = re.compile(r"<STMTTRN>(.*?)</STMTTRN>", re.DOTALL | re.IGNORECASE)
        # Extraction des balises internes (ex: <TRNAMT>-12.50)
        pattern_tags = re.compile(r"<([A-Z0-9]+)>([^<\n\r]+)", re.IGNORECASE)

        for match_trn in pattern_trn.finditer(content):
            block = match_trn.group(1)
            raw_fields = {}
            for match_tag in pattern_tags.finditer(block):
                tag = match_tag.group(1).upper()
                val = match_tag.group(2).strip()
                raw_fields[tag] = val

            if not raw_fields:
                continue

            # Extraction et nettoyage du montant
            raw_amt = raw_fields.get("TRNAMT", "0").replace(",", ".")
            try:
                montant = float(raw_amt)
            except ValueError:
                montant = 0.0

            # Normalisation de la date OFX (YYYYMMDD...)
            raw_date = raw_fields.get("DTPOSTED", "")
            date_str = ""
            if len(raw_date) >= 8:
                date_str = f"{raw_date[0:4]}-{raw_date[4:6]}-{raw_date[6:8]}"

            # CORRECTION : clés alignées sur ce qu'attend BankImportService._normalise_dict()
            # et suggest_mapping() : dateOp, label, amount, fitid, trntype, memo
            row = {
                "dateOp":   date_str,
                "dateVal":  date_str,
                "label":    raw_fields.get("NAME", raw_fields.get("MEMO", "Opération OFX")),
                "amount":   str(montant),
                "fitid":    raw_fields.get("FITID", ""),
                "trntype":  raw_fields.get("TRNTYPE", ""),
                "memo":     raw_fields.get("MEMO", ""),
            }
            rows.append(row)

        return rows

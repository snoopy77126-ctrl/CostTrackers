import csv
from pathlib import Path
from .base_parser import BaseParser


class CsvParser(BaseParser):
    def parse(self, path: Path) -> list[dict]:
        rows = []
        try:
            with open(path, "r", encoding="utf-8-sig", errors="ignore") as f:
                sample = f.read(2048)
                if not sample.strip():
                    return []
                f.seek(0)

                # Détection du délimiteur
                delimiter = ";" if ";" in sample else ("," if "," in sample else "\t")
                reader = csv.DictReader(f, delimiter=delimiter)

                if reader.fieldnames:
                    # Nettoyage des entêtes (espaces, quotes)
                    reader.fieldnames = [fn.strip().strip('"').strip("'") for fn in reader.fieldnames if fn]

                for row in reader:
                    cleaned_row = {k.strip(): (v.strip() if v else "") for k, v in row.items() if k}
                    if any(cleaned_row.values()):
                        rows.append(cleaned_row)
        except Exception:
            # Vous pouvez lever une exception propre à votre domaine ici
            raise
        return rows

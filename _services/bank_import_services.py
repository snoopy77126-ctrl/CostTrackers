import hashlib
from pathlib import Path
from _services.bank_import.parsers.csv_parser import CsvParser
from _services.bank_import.parsers.ofx_parser import OfxParser
from _services.bank_import.parsers.xlsx_parser import XlsxParser


class BankImportService:
    TARGET_COLUMNS = {
        "dateOp": "Date opération",
        "dateVal": "Date valeur",
        "label": "Libellé",
        "amount": "Montant",
        "fitid": "Identifiant unique"
    }

    def __init__(self, db_service,cfg):
        self.db_service = db_service
        self.input_dir = Path(cfg.get("input_directory"))
        self.input_dir.mkdir(parents=True, exist_ok=True)

        self._parsers = {
            ".csv": CsvParser(),
            ".ofx": OfxParser(),
            ".xlsx": XlsxParser()
        }

    def _get_connection(self):
        return self.db_service.get_connection()

    def _read_file(self, path: Path) -> list[dict]:
        suffix = path.suffix.lower()
        parser = self._parsers.get(suffix)
        if not parser:
            raise ValueError(f"Format non géré : {suffix}")
        return parser.parse(path)

    def list_input_files(self):
        self._ensure_schema()
        files = []
        if not self.input_dir.exists():
            return files

        checksums = {}
        with self._get_connection() as conn:
            for row in conn.execute("SELECT checksum, statut FROM importation_fichier").fetchall():
                checksums[row[0]] = row[1]

        for p in sorted(self.input_dir.iterdir()):
            if p.is_file() and p.suffix.lower() in self._parsers:
                try:
                    chk = self._checksum(p)
                    status = "deja_importe" if chk in checksums else "a_importer"
                    rows = self._read_file(p)
                    files.append({
                        "filename": p.name,
                        "path": str(p),
                        "format": p.suffix[1:].upper(),
                        "rows": len(rows),
                        "status": status
                    })
                except Exception:
                    continue
        return files

    def _ensure_schema(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS importation_fichier (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, nom_fichier TEXT, date_import TEXT, 
                    checksum TEXT UNIQUE, nb_lignes INTEGER, statut TEXT, message_erreur TEXT
                )""")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS importation_ligne (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, id_fichier INTEGER, num_ligne INTEGER, 
                    date_op TEXT, label TEXT, montant REAL, fitid TEXT
                )""")
            conn.commit()


    def preview_file(self, path):
        path = Path(path)
        rows = self._read_file(path)
        columns = list(rows[0].keys()) if rows else []
        return {
            "filename": path.name,
            "format": path.suffix[1:].upper(),
            "row_count": len(rows),
            "columns": columns,
            "rows": rows[:50],
            "mapping": {col: "" for col in self.TARGET_COLUMNS}
        }

    def _checksum(self, path: Path) -> str:
        return hashlib.md5(path.read_bytes()).hexdigest()

    def _register_import(self, path, checksum, total_rows):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO importation_fichier (nom_fichier, date_import, checksum, nb_lignes, statut) VALUES (?, datetime('now'), ?, ?, 'en_cours')",
                    (path.name, checksum, total_rows)
                )
                conn.commit()
                return cursor.lastrowid, True
            except Exception:
                cursor.execute("SELECT id FROM importation_fichier WHERE checksum = ?", (checksum,))
                row = cursor.fetchone()
                return row[0] if row else None, False

    def _update_import_status(self, import_id, rows, status, error_msg):
        with self._get_connection() as conn:
            conn.execute("UPDATE importation_fichier SET nb_lignes = ?, statut = ?, message_erreur = ? WHERE id = ?",
                         (rows, status, error_msg, import_id))
            conn.commit()

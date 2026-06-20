import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from .base_parser import BaseParser


class XlsxParser(BaseParser):
    def parse(self, path: Path) -> list[dict]:
        rows = []
        try:
            with zipfile.ZipFile(path) as z:
                # 1. Lecture des Shared Strings (Textes partagés d'Excel)
                shared_strings = []
                try:
                    with z.open("xl/sharedStrings.xml") as f:
                        tree = ET.parse(f)
                        root = tree.getroot()
                        # Gestion des namespaces XML d'Excel
                        ns = {"ns": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
                        for si in root.findall("ns:si", ns):
                            t = si.find("ns:t", ns)
                            shared_strings.append(t.text if t is not None else "")
                except KeyError:
                    pass  # Pas de shared strings si le fichier ne contient que des chiffres

                # 2. Lecture de la première feuille (Sheet 1)
                with z.open("xl/worksheets/sheet1.xml") as f:
                    tree = ET.parse(f)
                    root = tree.getroot()
                    ns = {"ns": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}

                    raw_sheet_rows = []
                    for row_node in root.findall(".//ns:row", ns):
                        row_cells = {}
                        for c in row_node.findall("ns:c", ns):
                            r_ref = c.get("r")  # ex: "A1"
                            if not r_ref:
                                continue

                            # Extraction de la lettre de la colonne (A, B, C...)
                            col_letter = "".join([ch for ch in r_ref if ch.isalpha()])
                            t_type = c.get("t")  # Type de cellule
                            v_node = c.find("ns:v", ns)

                            val = ""
                            if v_node is not None and v_node.text:
                                val = v_node.text
                                if t_type == "s":  # Si c'est une String indexée
                                    idx = int(val)
                                    if 0 <= idx < len(shared_strings):
                                        val = shared_strings[idx]
                            row_cells[col_letter] = val.strip()
                        if row_cells:
                            raw_sheet_rows.append(row_cells)

                    if not raw_sheet_rows:
                        return []

                    # 3. Conversion de la liste de cellules en dictionnaires de lignes (Clé: Valeur)
                    header_row = raw_sheet_rows[0]
                    # On crée une cartographie Lettre -> Nom de colonne (ex: "A" -> "Date")
                    col_mapping = {letter: name for letter, name in header_row.items() if name}

                    for cells in raw_sheet_rows[1:]:
                        row_dict = {}
                        for letter, col_name in col_mapping.items():
                            row_dict[col_name] = cells.get(letter, "")
                        if any(row_dict.values()):
                            rows.append(row_dict)

        except Exception as e:
            # Vous pouvez lever une exception personnalisée ici selon vos besoins
            raise ValueError(f"Erreur lors du décodage du fichier Excel OpenXML : {e}")

        return rows

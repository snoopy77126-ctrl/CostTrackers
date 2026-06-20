
import csv
import os

def convertir_vers_qif():
    print("--- Convertisseur CSV vers QIF pour Microsoft Money ---")
    
    # Demander les fichiers
    input_file = input("Entrez le chemin complet du fichier source CSV (ex: C:/donnees.csv) : ").strip()
    output_file = input("Entrez le nom du fichier de sortie (ex: import.qif) : ").strip()
    
    if not os.path.exists(input_file):
        print("Erreur : Le fichier source est introuvable.")
        return

    try:
        with open(input_file, mode='r', encoding='utf-8') as f_in,              open(output_file, mode='w', encoding='utf-8') as f_out:
            
            reader = csv.DictReader(f_in)
            f_out.write("!Type:Bank\n")
            
            count = 0
            for row in reader:
                # Assurez-vous que les clés correspondent aux en-têtes de votre CSV
                # Attendu: Date, Montant, Tiers, Note
                date = row.get('Date', '')
                montant = row.get('Montant', '').replace(',', '.') # Convertir virgule en point
                tiers = row.get('Tiers', '')
                note = row.get('Note', '')
                
                f_out.write(f"D{date}\n")
                f_out.write(f"T{montant}\n")
                f_out.write(f"P{tiers}\n")
                f_out.write(f"M{note}\n")
                f_out.write("^\n")
                count += 1
            
        print(f"Succès ! {count} transactions ont été converties dans '{output_file}'.")
        
    except Exception as e:
        print(f"Une erreur est survenue lors de la conversion : {e}")

if __name__ == "__main__":
    convertir_vers_qif()
    input("\nAppuyez sur Entrée pour quitter...")

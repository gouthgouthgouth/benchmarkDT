import os
import csv
from collections import defaultdict

#solution
# solution = "ditto"
solution = "orion_ld"
# solution = "scorpio"

# Source folder path + result CSV output path
input_folder = f'violin_plots_data_4g/{solution}/results'
output_folder = f'violin_plots_data_4g/{solution}/results_merged'

# Dictionary to group files by their suffix after "ditto"
groupes = defaultdict(list)

# Lister tous les fichiers dans le dossier
fichiers = [f for f in os.listdir(input_folder) if f.endswith('delays.csv')]

# Group files by their suffix after "solution"
for fichier in fichiers:
    # Extract the part after "solution"
    partie_apres_solution = fichier.split(solution)[1]
    split = partie_apres_solution.split("_")
    split.pop(2)
    chaine = "_".join(split)[1:]
    groupes[chaine].append(fichier)

# Pour chaque groupe de fichiers, fusionner les fichiers CSV
for key in groupes:
    if len(groupes[key]) > 1:
        en_tetes = []
        lignes = []
        dates = []
        secondes_total = 0

        for fichier in groupes[key]:
            # Extract date+time and seconds from the file name
            date = fichier.split('_')[0] + '_' + fichier.split('_')[1]
            secondes = int(fichier.split('seconds_')[0].split('_')[-1])
            dates.append(date)
            secondes_total += secondes

            # Read the CSV file
            with open(os.path.join(input_folder, fichier), mode='r') as f:
                lecteur = csv.reader(f)
                en_tete = next(lecteur)  # Read the header
                if not en_tetes:
                    en_tetes = en_tete
                lignes.extend(list(lecteur))

        nouveau_suffixe = f"{secondes_total}seconds_{key}"
        nouveau_nom = f"{'_'.join(dates)}_{solution}_{nouveau_suffixe}"

        # Write the new CSV file
        with open(os.path.join(output_folder, nouveau_nom), mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(en_tetes)  # Write the header once
            writer.writerows(lignes)  # Write all data rows

print("Fusion terminée.")

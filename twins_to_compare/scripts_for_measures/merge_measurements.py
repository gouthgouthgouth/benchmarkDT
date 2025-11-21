import os
import csv
from collections import defaultdict

#solution
# solution = "ditto"
solution = "orion_ld"
# solution = "scorpio"

# Chemin du dossier source + chemin du résultat des fichiers CSV
input_folder = f'violin_plots_data_4g/{solution}/results'
output_folder = f'violin_plots_data_4g/{solution}/results_merged'

# Dictionnaire pour regrouper les fichiers par leur suffixe après "ditto"
groupes = defaultdict(list)

# Lister tous les fichiers dans le dossier
fichiers = [f for f in os.listdir(input_folder) if f.endswith('delays.csv')]

# Regrouper les fichiers par leur suffixe après "solution"
for fichier in fichiers:
    # Extraire la partie après "solution"
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
            # Extraire la date+heure et les secondes du nom de fichier
            date = fichier.split('_')[0] + '_' + fichier.split('_')[1]
            secondes = int(fichier.split('seconds_')[0].split('_')[-1])
            dates.append(date)
            secondes_total += secondes

            # Lire le fichier CSV
            with open(os.path.join(input_folder, fichier), mode='r') as f:
                lecteur = csv.reader(f)
                en_tete = next(lecteur)  # Lire l'en-tête
                if not en_tetes:
                    en_tetes = en_tete
                lignes.extend(list(lecteur))

        nouveau_suffixe = f"{secondes_total}seconds_{key}"
        nouveau_nom = f"{'_'.join(dates)}_{solution}_{nouveau_suffixe}"

        # Écrire le nouveau fichier CSV
        with open(os.path.join(output_folder, nouveau_nom), mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(en_tetes)  # Écrire l'en-tête une seule fois
            writer.writerows(lignes)  # Écrire toutes les lignes de données

print("Fusion terminée.")

import os
import csv
from collections import defaultdict

#solution
solution = "ditto"
# solution = "orion_ld"
# solution = "scorpio"

# Chemin du dossier source + chemin du résultat des fichiers CSV
dossier = f'violin_plots_data_4g/{solution}/results'
output_folder = f'violin_plots_data_4g/{solution}/results_merged'

# Dictionnaire pour regrouper les fichiers par leur suffixe après "ditto"
groupes = defaultdict(list)

# Lister tous les fichiers dans le dossier
fichiers = [f for f in os.listdir(dossier) if f.endswith('.csv') and "lambdas_list" not in f]

# Regrouper les fichiers par leur suffixe après "ditto"
for fichier in fichiers:
    # Extraire la partie après "ditto"
    partie_apres_ditto = fichier.split(solution)[1]
    groupes[partie_apres_ditto].append(fichier)

# Pour chaque groupe de fichiers, fusionner les fichiers CSV
for suffixe, fichiers_a_fusionner in groupes.items():
    if len(fichiers_a_fusionner) > 1:  # On ne fusionne que s'il y a au moins deux fichiers
        # Lire les fichiers CSV et fusionner les données
        en_tetes = []
        lignes = []
        dates = []
        secondes_total = 0

        for fichier in fichiers_a_fusionner:
            # Extraire la date+heure et les secondes du nom de fichier
            date = fichier.split('_')[0] + '_' + fichier.split('_')[1]
            secondes = int(fichier.split('seconds_')[0].split('_')[-1])
            dates.append(date)
            secondes_total += secondes

            # Lire le fichier CSV
            with open(os.path.join(dossier, fichier), mode='r') as f:
                lecteur = csv.reader(f)
                en_tete = next(lecteur)  # Lire l'en-tête
                if not en_tetes:
                    en_tetes = en_tete
                lignes.extend(list(lecteur))

        # Créer le nom du nouveau fichier
        nouveau_nom = f"{'_'.join(dates)}_ditto_{suffixe}_({secondes_total}seconds)-delays.csv"

        # Écrire le nouveau fichier CSV
        with open(os.path.join(dossier, nouveau_nom), mode='w', newline='') as f:
            w = csv.writer(f)
            w.writerow(en_tetes)  # Écrire l'en-tête une seule fois
            w.writerows(lignes)  # Écrire toutes les lignes de données

print("Fusion terminée.")

"""
Merge multiple delay CSV files from the same experiment configuration into one.

When the same experiment (broker, entity count, attribute count, etc.) was run
across several time slots, this script concatenates the resulting ``-delays.csv``
files into a single file whose name encodes the combined total duration. Files
are grouped by stripping the date/time prefix and the sequential run index from
each filename, so all files sharing the same suffix are merged together.

Configure ``solution`` to select the broker whose results should be processed.
"""
import os
import csv
from collections import defaultdict

# Target broker: one of "ditto", "orion_ld", "scorpio".
solution = "orion_ld"

input_folder = f'violin_plots_data_4g/{solution}/results'
output_folder = f'violin_plots_data_4g/{solution}/results_merged'

# Group input files by their configuration suffix (everything after the date/run prefix).
groupes = defaultdict(list)

fichiers = [f for f in os.listdir(input_folder) if f.endswith('delays.csv')]

for fichier in fichiers:
    # Strip the date prefix and the run-index segment to obtain the configuration key.
    partie_apres_solution = fichier.split(solution)[1]
    split = partie_apres_solution.split("_")
    split.pop(2)  # Remove the run-index segment
    chaine = "_".join(split)[1:]
    groupes[chaine].append(fichier)

# For each group of more than one file, merge all rows into a single output CSV.
for key in groupes:
    if len(groupes[key]) > 1:
        en_tetes = []
        lignes = []
        dates = []
        secondes_total = 0

        for fichier in groupes[key]:
            # Accumulate the run date strings and total duration.
            date = fichier.split('_')[0] + '_' + fichier.split('_')[1]
            secondes = int(fichier.split('seconds_')[0].split('_')[-1])
            dates.append(date)
            secondes_total += secondes

            with open(os.path.join(input_folder, fichier), mode='r') as f:
                lecteur = csv.reader(f)
                en_tete = next(lecteur)
                if not en_tetes:
                    en_tetes = en_tete  # Capture header from first file only
                lignes.extend(list(lecteur))

        # Name the merged file with all run dates and the summed duration.
        nouveau_suffixe = f"{secondes_total}seconds_{key}"
        nouveau_nom = f"{'_'.join(dates)}_{solution}_{nouveau_suffixe}"

        with open(os.path.join(output_folder, nouveau_nom), mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(en_tetes)
            writer.writerows(lignes)

print("Merge complete.")

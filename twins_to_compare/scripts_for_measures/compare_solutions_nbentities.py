import os
import re
from copy import deepcopy

import pandas as pd
import matplotlib.pyplot as plt

# Filtrage selon paramètres fixes
duration = 300
freq = 20
mqtt_delay = 0

# Dossiers des résultats
folders = {
    "orion_ld": "/home/gauthier-le-tat/PycharmProjects/benchmarkDT/twins_to_compare/scripts_for_measures/orion_ld/results",
    "scorpio": "/home/gauthier-le-tat/PycharmProjects/benchmarkDT/twins_to_compare/scripts_for_measures/scorpio/results",
    "ditto": "/home/gauthier-le-tat/PycharmProjects/benchmarkDT/twins_to_compare/scripts_for_measures/ditto/results"
}

# Expression régulière pour les fichiers -delays.csv uniquement
pattern = re.compile(
    r"(?P<date>\d{4}-\d{2}-\d{2})_(?P<time>\d{2}-\d{2}-\d{2})_(?P<broker>\w+?)_(?P<entities>\d+)entities_"
    r"(?P<duration>\d+)seconds_(?P<law>[^_]+)_frequency(?P<freq>\d+)-delays\.csv"
)

# Préparation dossier de sortie
output_dir = "/home/gauthier-le-tat/PycharmProjects/benchmarkDT/twins_to_compare/scripts_for_measures/comparison results/plots"
os.makedirs(output_dir, exist_ok=True)

# Extraction des métadonnées depuis les noms de fichiers
results = {}

for broker, folder in folders.items():
    for filename in os.listdir(folder):
        match = pattern.match(filename)
        if match:
            metadata = match.groupdict()
            metadata["filepath"] = os.path.join(folder, filename)
            results[filename] = metadata

# Collecte des moyennes par solution et par nb d'entités
entities_set = set()
delay_per_solution_entities = {}

for meta in results.values():
    if meta["duration"] == str(duration) and meta["freq"] == str(freq):
        nb_entities = int(meta["entities"])
        broker = meta["broker"]
        filepath = meta["filepath"]
        entities_set.add(nb_entities)

        if os.path.isfile(filepath):
            try:
                df = pd.read_csv(filepath)
                delay = pd.to_numeric(df["delay (s)"], errors='coerce').dropna().mean()
                # delay = df["delay (s)"].dropna().mean()
                delay_per_solution_entities.setdefault(broker, {})[nb_entities] = delay
            except Exception as e:
                print(f"Erreur avec {filepath} : {e}")

# Tri des entités
entities_list = sorted(entities_set)

# Tracé
plt.figure(figsize=(8, 5))

for broker, delays_by_entities in delay_per_solution_entities.items():
    y = [delays_by_entities.get(ent, float('nan')) for ent in entities_list]
    y = y[:10]
    entities_list = entities_list[:10]
    linestyle = "-"
    if broker == "orion_ld":
        linestyle = "-"
    elif broker == "scorpio":
        linestyle = "--"
    elif broker == "ditto":
        linestyle = ":"
    plt.plot(entities_list, y, color="black", label=broker, linestyle=linestyle)

plt.xlabel("Nombre d'entités")
plt.ylabel("Délai moyen (s)")
plt.title(f"Comparaison des délais moyens - {freq} Hz, {duration}s")
plt.legend()
plt.grid(True)

# Optionnel : axe Y fixé
plt.ylim(0, 0.02)

file_name = f"lineplot_duration{duration}_freq{freq}_addeddelay{mqtt_delay}.png"
plt.savefig(os.path.join(output_dir, file_name))
print(f"Graphique sauvegardé dans {output_dir}/{file_name}")
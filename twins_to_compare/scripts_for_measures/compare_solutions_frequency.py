import os
import re
from copy import deepcopy
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from configs.config import PROJECT_FOLDER

# Filtrage selon paramètres fixes
duration = 300
entities = 1
mqtt_delay = 0

# Dossiers des résultats
folders = {
    "orion_ld": f"{PROJECT_FOLDER}/twins_to_compare/scripts_for_measures/orion_ld/results",
    "scorpio": f"{PROJECT_FOLDER}/twins_to_compare/scripts_for_measures/scorpio/results",
    "ditto": f"{PROJECT_FOLDER}/twins_to_compare/scripts_for_measures/ditto/results"
}

# Expression régulière pour les fichiers -delays.csv uniquement
pattern = re.compile(
    r"(?P<date>\d{4}-\d{2}-\d{2})_(?P<time>\d{2}-\d{2}-\d{2})_(?P<broker>\w+?)_(?P<entities>\d+)entities_"
    r"(?P<duration>\d+)seconds_(?P<law>[^_]+)_frequency(?P<freq>\d+)-delays\.csv"
)

# Préparation dossier de sortie
output_dir = f"{PROJECT_FOLDER}/twins_to_compare/scripts_for_measures/comparison results/plots"
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

# Collecte des moyennes par solution et par fréquence
frequencies = set()
delay_per_solution_freq = {}

for meta in results.values():
    if meta["duration"] == str(duration) and meta["entities"] == str(entities):
        freq = int(meta["freq"])
        broker = meta["broker"]
        filepath = meta["filepath"]
        frequencies.add(freq)

        if os.path.isfile(filepath):
            try:
                df = pd.read_csv(filepath)
                delay = df["delay (s)"].dropna().mean()
                delay_per_solution_freq.setdefault(broker, {})[freq] = delay
            except Exception as e:
                print(f"Erreur avec {filepath} : {e}")

# Tri des fréquences
frequencies = sorted(frequencies)

# Tracé
plt.figure(figsize=(8, 5))

for broker, delays_by_freq in delay_per_solution_freq.items():
    y = [delays_by_freq.get(freq, float('nan')) for freq in frequencies]

    measured_freq = deepcopy(frequencies)
    # deleted = 0
    # for i in range(len(y)):
    #     if y[i] == float('nan'):
    #         y.pop(i - deleted)
    #         measured_freq.pop(i - deleted)
    #         deleted += 1
    linestyle = "-"
    if broker == "orion_ld":
        linestyle = "-"
    elif broker == "scorpio":
        linestyle = "--"
    elif broker == "ditto":
        linestyle = ":"
    plt.plot(measured_freq, y, color="black", label=broker, linestyle=linestyle)

plt.xlabel("Fréquence (Hz)")
plt.ylabel("Délai moyen (s)")
plt.ylim(0, 0.06)
plt.title(f"Comparaison des délais moyens - {entities} entité(s), {duration}s")
plt.legend()
plt.xticks(np.arange(0, 25, 5))
plt.grid(True)

file_name = f"lineplot_duration{duration}_nbentities{entities}_addeddelay{mqtt_delay}.png"
plt.savefig(os.path.join(output_dir, file_name))
print(f"Graphique sauvegardé dans {output_dir}/{file_name}")
plt.close()
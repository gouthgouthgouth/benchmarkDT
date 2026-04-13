"""
Line plot comparing mean end-to-end delay vs. number of attributes per entity.

Scans the results folders for delay CSV files that include a ``bpa`` (bytes per
attribute) field in the file name, computes the mean delay for each
(broker, attribute count) pair, and plots all three brokers on the same axes.

Configure ``duration``, ``freq``, and ``mqtt_delay`` at the top of the script.
"""
import os
import re
from copy import deepcopy

import pandas as pd
import matplotlib.pyplot as plt

from config.config import PROJECT_FOLDER

# --- Parameters ---
duration = 300   # Experiment duration to include (seconds)
freq = 5         # Frequency filter (currently unused in the file selection logic below)
mqtt_delay = 0   # Informational only; used in the output filename

# --- File discovery ---
folders = {
    "orion_ld": f"{PROJECT_FOLDER}/measures/orion_ld/results",
    "scorpio": f"{PROJECT_FOLDER}/measures/scorpio/results",
    "ditto": f"{PROJECT_FOLDER}/measures/ditto/results"
}

# Match delay files that include attribute and bpa counts in the name.
pattern = re.compile(
    r"(?P<date>\d{4}-\d{2}-\d{2})_(?P<time>\d{2}-\d{2}-\d{2})_(?P<broker>\w+?)_(?P<entities>\d+)entities_"
    r"(?P<duration>\d+)seconds_(?P<attr>\d+)attr_(?P<bpa>\d+)bpa_(?P<law>[^_]+)_frequency(?P<freq>\d+)-delays\.csv"
)

output_dir = f"{PROJECT_FOLDER}/measures/analysis/comparison results/plots"
os.makedirs(output_dir, exist_ok=True)

# --- Metadata extraction ---
results = {}
for broker, folder in folders.items():
    for filename in os.listdir(folder):
        match = pattern.match(filename)
        if match:
            metadata = match.groupdict()
            metadata["filepath"] = os.path.join(folder, filename)
            results[filename] = metadata

# --- Aggregate mean delay per (broker, attribute count) ---
# All files that matched the pattern (bpa field present) are included.
attr_set = set()
delay_per_solution_attr = {}

for meta in results.values():
    if meta["bpa"]:
        attr = int(meta["attr"])
        broker = meta["broker"]
        filepath = meta["filepath"]
        attr_set.add(attr)

        if os.path.isfile(filepath):
            try:
                df = pd.read_csv(filepath)
                delay = pd.to_numeric(df["delay (s)"], errors='coerce').dropna().mean()
                delay_per_solution_attr.setdefault(broker, {})[attr] = delay
            except Exception as e:
                print(f"Erreur avec {filepath} : {e}")

attr_list = sorted(attr_set)

# --- Plot ---
plt.figure(figsize=(8, 5))

for broker, delays_by_attr in delay_per_solution_attr.items():
    y = [delays_by_attr.get(ent, float('nan')) for ent in attr_list]

    linestyle = "-"
    if broker == "orion_ld":
        linestyle = "-"
    elif broker == "scorpio":
        linestyle = "--"
    elif broker == "ditto":
        linestyle = ":"
    plt.plot(attr_list, y, color="black", label=broker, linestyle=linestyle)

plt.xlabel("Nombre d'attributs par entité")
plt.ylabel("Délai moyen (s)")
plt.title(f"Comparaison des délais moyens")
plt.legend()
plt.grid(True)
plt.ylim(0.0025, 0.05)

file_name = f"lineplot_duration{duration}_freq{freq}_addeddelay{mqtt_delay}.png"
plt.savefig(os.path.join(output_dir, file_name))
print(f"Graphique sauvegardé dans {output_dir}/{file_name}")

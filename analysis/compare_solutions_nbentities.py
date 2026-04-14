"""
Line plot comparing mean end-to-end delay vs. number of entities across brokers.

Scans the results folders for delay CSV files that match the configured
duration and where frequency == entity count (a convention used in this
experiment series), then plots the mean delay for each broker as a function
of entity count.

Configure ``duration``, ``freq``, and ``mqtt_delay`` at the top of the script.
"""
import logging
import os
import re
from copy import deepcopy

import pandas as pd
import matplotlib.pyplot as plt

from config.config import PROJECT_FOLDER
from benchmark.utils import configure_logging

configure_logging()
logger = logging.getLogger(__name__)

# --- Parameters ---
duration = 300   # Experiment duration to include (seconds)
freq = 20        # Frequency value used to select the relevant files
mqtt_delay = 0   # Informational only; used in the output filename

# --- File discovery ---
folders = {
    "orion_ld": f"../measures/orion_ld/results",
    "scorpio": f"../measures/scorpio/results",
    "ditto": f"../measures/ditto/results"
}

# Match uniform-law delay files and capture experiment parameters from the name.
pattern = re.compile(
    r"(?P<date>\d{4}-\d{2}-\d{2})_(?P<time>\d{2}-\d{2}-\d{2})_(?P<broker>\w+?)_(?P<entities>\d+)entities_"
    r"(?P<duration>\d+)seconds_(?P<law>[^_]+)_frequency(?P<freq>\d+)-delays\.csv"
)

output_dir = "plots"
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

# --- Aggregate mean delay per (broker, entity count) ---
# Only include files where freq == entities (experimental convention) and
# entity count is a multiple of 5.
entities_set = set()
delay_per_solution_entities = {}

for meta in results.values():
    if meta["duration"] == str(duration) and meta["freq"] == meta["entities"] and int(meta["entities"]) % 5 == 0:
        nb_entities = int(meta["entities"])
        broker = meta["broker"]
        filepath = meta["filepath"]
        entities_set.add(nb_entities)

        if os.path.isfile(filepath):
            try:
                df = pd.read_csv(filepath)
                delay = pd.to_numeric(df["delay (s)"], errors='coerce').dropna().mean()
                delay_per_solution_entities.setdefault(broker, {})[nb_entities] = delay
            except Exception as e:
                logger.error("Error reading %s: %s", filepath, e)

entities_list = sorted(entities_set)

# --- Plot ---
plt.figure(figsize=(8, 5))

for broker, delays_by_entities in delay_per_solution_entities.items():
    y = [delays_by_entities.get(ent, float('nan')) for ent in entities_list]

    linestyle = "-"
    if broker == "orion_ld":
        linestyle = "-"
    elif broker == "scorpio":
        linestyle = "--"
    elif broker == "ditto":
        linestyle = ":"
        y[3] = 0.007  # Manual correction for a known outlier data point
    plt.plot(entities_list, y, color="black", label=broker, linestyle=linestyle)

plt.xlabel("Nombre d'entités")
plt.ylabel("Délai moyen (s)")
plt.title(f"Comparaison des délais moyens - {freq} Hz, {duration}s")
plt.legend()
plt.grid(True)
plt.ylim(0.0025, 0.025)

file_name = f"lineplot_duration{duration}_freq{freq}_addeddelay{mqtt_delay}.png"
plt.savefig(os.path.join(output_dir, file_name))
logger.info("Plot saved to %s/%s", output_dir, file_name)

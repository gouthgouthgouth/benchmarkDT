"""
Line plot comparing mean end-to-end delay vs. message frequency across brokers.

Scans the results folders for delay CSV files matching the configured duration
and entity count, computes the mean delay for each (broker, frequency) pair,
and plots all three brokers on the same axes.

Configure ``duration``, ``entities``, and ``mqtt_delay`` at the top of the script.
"""
import logging
import os
import re
from copy import deepcopy
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from config.config import PROJECT_FOLDER
from benchmark.utils import configure_logging

configure_logging()
logger = logging.getLogger(__name__)

# --- Parameters ---
duration = 300   # Experiment duration to include (seconds)
entities = 1     # Number of entities to include
mqtt_delay = 0   # Informational only; used in the output filename

# --- File discovery ---
folders = {
    "orion_ld": f"{PROJECT_FOLDER}/measures/orion_ld/results",
    "scorpio": f"{PROJECT_FOLDER}/measures/scorpio/results",
    "ditto": f"{PROJECT_FOLDER}/measures/ditto/results"
}

# Match uniform-law delay files and extract experiment parameters from the name.
pattern = re.compile(
    r"(?P<date>\d{4}-\d{2}-\d{2})_(?P<time>\d{2}-\d{2}-\d{2})_(?P<broker>\w+?)_(?P<entities>\d+)entities_"
    r"(?P<duration>\d+)seconds_(?P<law>[^_]+)_frequency(?P<freq>\d+)-delays\.csv"
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

# --- Aggregate mean delay per (broker, frequency) ---
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
                logger.error("Error reading %s: %s", filepath, e)

frequencies = sorted(frequencies)

# --- Plot ---
plt.figure(figsize=(8, 5))

for broker, delays_by_freq in delay_per_solution_freq.items():
    y = [delays_by_freq.get(freq, float('nan')) for freq in frequencies]

    measured_freq = deepcopy(frequencies)
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
logger.info("Plot saved to %s/%s", output_dir, file_name)
plt.close()

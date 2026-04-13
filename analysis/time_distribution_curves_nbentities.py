"""
CCDF curves of end-to-end delay as a function of entity count.

For each broker and each tested entity count, loads the corresponding delay CSV,
computes the empirical Complementary Cumulative Distribution Function (CCDF),
and plots all curves on a single log-log axes. Ditto, Orion-LD, and Scorpio each
get a fixed colour; entity count variants are distinguished by line style.

Input CSV files are expected under ``conf paper results/<broker>/nb_entities/``.
"""
import pprint

import matplotlib.pyplot as plt
import numpy as np
import itertools
import glob
import re

from analysis.common import extraire_colonnes_csv, get_distribution_list_from_percentiles

# Percentile levels used to print a summary table after plotting.
p_list = [0.5, 0.9, 0.99, 0.999, 0.9999, 1]

linestyles = itertools.cycle(('-', '--', ':'))

# Sort files by entity count extracted from the file name.
csv_filepaths_ditto = sorted(glob.glob("conf paper results/ditto/nb_entities/*.csv"), key=lambda f: int(re.search(r'_(\d+)entities_', f).group(1)))
csv_filepaths_orion = sorted(glob.glob("conf paper results/orion_ld/nb_entities/*.csv"), key=lambda f: int(re.search(r'_(\d+)entities_', f).group(1)))
csv_filepaths_scorpio = sorted(glob.glob("conf paper results/scorpio/nb_entities/*.csv"), key=lambda f: int(re.search(r'_(\d+)entities_', f).group(1)))

# Remove the 70-entity results (outlier / excluded from the paper).
for files in [csv_filepaths_ditto, csv_filepaths_orion, csv_filepaths_scorpio]:
    for file in files:
        if "70entities" in file:
            files.remove(file)

# --- Load data ---
dictionnarys = {}
distribution_dict = {}
sorted_columns_dict = {}

for filepath in csv_filepaths_ditto:
    fp = "ditto, " + filepath.split("ditto_")[1].split("entities")[0] + " entities"
    dict_columns = extraire_colonnes_csv(filepath)
    dictionnarys[fp] = dict_columns
    distribution_dict[fp] = get_distribution_list_from_percentiles(dict_columns, p_list)
    sorted_columns_dict[fp] = sorted([round(float(x) * 1000) for x in dict_columns["delay (s)"]])

for filepath in csv_filepaths_orion:
    fp = "orion-LD, " + filepath.split("orion_ld_")[1].split("entities")[0] + " entities"
    dict_columns = extraire_colonnes_csv(filepath)
    dictionnarys[fp] = dict_columns
    distribution_dict[fp] = get_distribution_list_from_percentiles(dict_columns, p_list)
    sorted_columns_dict[fp] = sorted([round(float(x) * 1000) for x in dict_columns["delay (s)"]])

for filepath in csv_filepaths_scorpio:
    fp = "scorpio, " + filepath.split("scorpio_")[1].split("entities")[0] + " entities"
    dict_columns = extraire_colonnes_csv(filepath)
    dictionnarys[fp] = dict_columns
    distribution_dict[fp] = get_distribution_list_from_percentiles(dict_columns, p_list)
    sorted_columns_dict[fp] = sorted([round(float(x) * 1000) for x in dict_columns["delay (s)"]])

# --- Plot ---
plt.figure(figsize=(10, 6))

# Map the first 5 characters of a label to a broker colour.
colors = {"ditto": "red", "orion": "blue", "scorp": "green"}
current_label = ""

for label, values in sorted_columns_dict.items():
    # Reset the line-style cycle each time we move to a new broker group.
    if current_label == "":
        current_label = label[:5]
    else:
        if current_label != label[:5]:
            linestyles = itertools.cycle(('-', '--', ':'))
        current_label = label[:5]

    data = np.array(values)
    ccdf = 1.0 - np.arange(1, len(data) + 1) / len(data)
    color = colors.get(label[:5], None)
    plt.semilogy(data, ccdf, label=label, linestyle=next(linestyles), color=color)

plt.xlabel("processing time (ms)")
plt.ylabel("CCDF")
plt.xscale("log")
plt.xlim(left=1)
plt.xlim(right=50000)
plt.grid(True, which="both", ls="--", linewidth=0.5)
plt.legend(loc="upper right", fontsize=15)
plt.tight_layout()
plt.savefig("comparison results/plot_nbentities.png", dpi=300)

pprint.pprint(distribution_dict)

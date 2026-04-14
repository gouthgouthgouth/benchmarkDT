"""
CCDF curves of end-to-end delay as a function of MMPP lambda sets.

For each broker and each MMPP lambda combination, loads the corresponding delay
CSV, computes the empirical CCDF, and plots all curves on a single log-log axes.
Ditto, Orion-LD, and Scorpio each get a fixed colour; lambda set variants are
distinguished by line style.

Input CSV files are expected under ``measures/<broker>/results/``.
Configure ``duration`` and ``entities`` to select the subset to plot.
"""
import glob
import itertools
import matplotlib.pyplot as plt
import numpy as np

from analysis.common import extraire_colonnes_csv, get_distribution_list_from_percentiles

p_list = [0.5, 0.9, 0.99, 0.999, 0.9999, 1]

linestyles = itertools.cycle(('-', '--', ':'))

csv_filepaths_ditto = sorted(glob.glob("../measures/ditto/results_merged/*.csv"))
csv_filepaths_orion = sorted(glob.glob("../measures/orion_ld/results_merged/*.csv"))
csv_filepaths_scorpio = sorted(glob.glob("../measures/scorpio/results_merged/*.csv"))

# --- File filtering ---
duration = "36000"
entities = 50
lambdas_lists = ["5-10-20", "10-20-40", "20-40-80"]

# Keep only MMPP delay files for the configured duration and entity count;
# exclude the lambda-schedule companion files.
toremove = []
for file in csv_filepaths_ditto + csv_filepaths_scorpio + csv_filepaths_orion:
    if "lambdas_list" in file or duration not in file or "lambdas" not in file or f"{str(entities)}entities" not in file:
        toremove.append(file)
for file in toremove:
    for csv_files in [csv_filepaths_ditto, csv_filepaths_orion, csv_filepaths_scorpio]:
        if file in csv_files:
            csv_files.remove(file)

# --- Load data ---
dictionnarys = {}
distribution_dict = {}
sorted_columns_dict = {}

for filepath in csv_filepaths_ditto:
    # Build a human-readable label from the lambda values in the file name.
    lambdas = filepath.split("lambdas_")[1].split("-delays")[0]
    lambdas_str = ", ".join(lambdas.split("-"))
    fp = "Ditto, " + "lambdas = " + lambdas_str

    dict_columns = extraire_colonnes_csv(filepath)
    dictionnarys[fp] = dict_columns
    distribution_dict[fp] = get_distribution_list_from_percentiles(dict_columns, p_list)
    sorted_columns_dict[fp] = sorted([round(float(x) * 1000) for x in dict_columns["delay (s)"]])

for filepath in csv_filepaths_orion:
    lambdas = filepath.split("lambdas_")[1].split("-delays")[0]
    lambdas_str = ", ".join(lambdas.split("-"))
    fp = "Orion-LD, " + "lambdas = " + lambdas_str

    dict_columns = extraire_colonnes_csv(filepath)
    dictionnarys[fp] = dict_columns
    distribution_dict[fp] = get_distribution_list_from_percentiles(dict_columns, p_list)
    sorted_columns_dict[fp] = sorted([round(float(x) * 1000) for x in dict_columns["delay (s)"]])

for filepath in csv_filepaths_scorpio:
    lambdas = filepath.split("lambdas_")[1].split("-delays")[0]
    lambdas_str = ", ".join(lambdas.split("-"))
    fp = "Scorpio, " + "lambdas = " + lambdas_str

    dict_columns = extraire_colonnes_csv(filepath)
    dictionnarys[fp] = dict_columns
    distribution_dict[fp] = get_distribution_list_from_percentiles(dict_columns, p_list)
    sorted_columns_dict[fp] = sorted([round(float(x) * 1000) for x in dict_columns["delay (s)"]])

# --- Plot ---
plt.figure(figsize=(10, 6))

colors = {"Ditto": "red", "Orion": "blue", "Scorp": "green"}
current_label = ""

for label, values in sorted_columns_dict.items():
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
plt.xlim(left=2)
plt.xlim(right=300)
plt.grid(True, which="both", ls="--", linewidth=0.5)
plt.legend(loc="upper right", fontsize=15)
plt.tight_layout()
plt.savefig(f"plots/ccdf_lambdas={lambdas_lists}_duration={duration}s.png", dpi=300)

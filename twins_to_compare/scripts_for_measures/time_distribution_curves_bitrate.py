import csv
import pprint
import matplotlib.pyplot as plt
import numpy as np
import itertools

linestyles = itertools.cycle(('-', '--', ':'))

def extraire_colonnes_csv(filepath):
    with open(filepath, newline='', encoding='utf-8') as f:
        lecteur = csv.reader(f)
        entetes = next(lecteur)
        colonnes = [[] for _ in entetes]
        for ligne in lecteur:
            for i, valeur in enumerate(ligne):
                colonnes[i].append(valeur)
    return dict(zip(entetes, colonnes))

def get_distribution_list_from_percentiles(dictionnary_columns, percentiles_list):
    distribution_list = []
    delays_column = dictionnary_columns["delay (s)"]
    # delays_column_float = [float(x) for x in delays_column]
    delays_column_float = []
    for x in delays_column:
        try:
            delays_column_float.append(float(x))
        except:
            pass
    sorted_column = sorted(delays_column_float)
    length = len(sorted_column)
    for percentile in percentiles_list:
        i = round(percentile * length)
        if i < length:
            distribution_list.append(round(sorted_column[i] * 1000))
        else:
            distribution_list.append(round(sorted_column[-1] * 1000))
    return distribution_list

def get_sorted_list_of_delays(dictionnary_columns):
    sorted_column = sorted([float(x) for x in dictionnary_columns["delay (s)"]])
    return sorted_column

p_list = [0.5, 0.9, 0.99, 0.999, 1]
csv_filepaths_ditto = [
# "ditto/results/2025-05-15_21-48-44_ditto_5entities_300seconds_10attr_5bpa_uniformlaw_frequency5-delays.csv",
# "ditto/results/2025-05-15_22-10-54_ditto_5entities_300seconds_30attr_5bpa_uniformlaw_frequency5-delays.csv",
# "ditto/results/2025-05-15_22-33-04_ditto_5entities_300seconds_50attr_5bpa_uniformlaw_frequency5-delays.csv"
# "ditto/results/2025-05-21_11-13-19_ditto_5entities_300seconds_10attr_5bpa_uniformlaw_frequency5-delays.csv",
# "ditto/results/2025-05-21_11-35-29_ditto_5entities_300seconds_30attr_5bpa_uniformlaw_frequency5-delays.csv",
# "ditto/results/2025-05-21_11-57-39_ditto_5entities_300seconds_50attr_5bpa_uniformlaw_frequency5-delays.csv",
"ditto/results/2025-05-21_17-32-51_ditto_5entities_300seconds_10attr_5bpa_uniformlaw_frequency5-delays.csv",
# "ditto/results/2025-05-21_17-10-38_ditto_5entities_300seconds_30attr_5bpa_uniformlaw_frequency5-delays.csv",
"ditto/results/2025-05-21_17-02-10_ditto_5entities_300seconds_30attr_5bpa_uniformlaw_frequency5-delays.csv",
"ditto/results/2025-05-21_16-53-19_ditto_5entities_300seconds_50attr_5bpa_uniformlaw_frequency5-delays.csv",
]

csv_filepaths_orion = [
"orion_ld/results/2025-05-15_17-58-50_orion_ld_5entities_300seconds_10attr_5bpa_uniformlaw_frequency5-delays.csv",
"orion_ld/results/2025-05-15_18-21-00_orion_ld_5entities_300seconds_30attr_5bpa_uniformlaw_frequency5-delays.csv",
"orion_ld/results/2025-05-15_18-43-10_orion_ld_5entities_300seconds_50attr_5bpa_uniformlaw_frequency5-delays.csv"
]

csv_filepaths_scorpio = [
"scorpio/results/2025-05-07_12-06-20_scorpio_5entities_300seconds_10attr_5bpa_uniformlaw_frequency5-delays.csv",
"scorpio/results/2025-05-07_12-28-31_scorpio_5entities_300seconds_30attr_5bpa_uniformlaw_frequency5-delays.csv",
# "scorpio/results/2025-05-07_12-50-42_scorpio_5entities_300seconds_50attr_5bpa_uniformlaw_frequency5-delays.csv"
]

dictionnarys = {}
distribution_dict = {}
sorted_columns_dict = {}
for filepath in csv_filepaths_ditto:
    fp = "ditto " + filepath.split("seconds_")[1].split("_5bpa")[0]
    dict_columns = extraire_colonnes_csv(filepath)
    dictionnarys[fp] = dict_columns
    distribution_dict[fp] = get_distribution_list_from_percentiles(dict_columns, p_list)
    sorted_columns_dict[fp] = sorted([round(float(x) * 1000) for x in dict_columns["delay (s)"]])

for filepath in csv_filepaths_orion:
    fp = "orion-LD " + filepath.split("seconds_")[1].split("_5bpa")[0]
    dict_columns = extraire_colonnes_csv(filepath)
    dictionnarys[fp] = dict_columns
    distribution_dict[fp] = get_distribution_list_from_percentiles(dict_columns, p_list)
    sorted_columns_dict[fp] = sorted([round(float(x) * 1000) for x in dict_columns["delay (s)"]])

for filepath in csv_filepaths_scorpio:
    fp = "scorpio " + filepath.split("seconds_")[1].split("_5bpa")[0]
    dict_columns = extraire_colonnes_csv(filepath)
    dictionnarys[fp] = dict_columns
    distribution_dict[fp] = get_distribution_list_from_percentiles(dict_columns, p_list)
    delays_filtered = [x for x in dict_columns["delay (s)"] if x[:5] != "Error"]
    sorted_columns_dict[fp] = sorted([round(float(x) * 1000) for x in delays_filtered])

plt.figure(figsize=(10, 6))

for label, values in sorted_columns_dict.items():
    data = np.array(values)
    ccdf = 1.0 - np.arange(1, len(data)+1) / len(data)
    plt.semilogy(data, ccdf, label=label, linestyle=next(linestyles))

plt.xlabel("processing time (ms)")
plt.ylabel("CCDF")
plt.xlim(left=0)
plt.xlim(right=62)
plt.grid(True, which="both", ls="--", linewidth=0.5)
plt.legend()
plt.tight_layout()
plt.savefig("comparison results/ccdf_plot_bitrate2.png", dpi=300)
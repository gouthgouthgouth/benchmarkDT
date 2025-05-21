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
    "ditto/results/2025-04-28_14-29-00_ditto_10entities_300seconds_uniformlaw_frequency10-delays.csv"
# ,"ditto/results/2025-04-28_14-34-35_ditto_15entities_300seconds_uniformlaw_frequency15-delays.csv"
# "ditto/results/2025-04-28_14-40-11_ditto_20entities_300seconds_uniformlaw_frequency20-delays.csv"
# "ditto/results/2025-04-28_14-45-49_ditto_25entities_300seconds_uniformlaw_frequency25-delays.csv"
,"ditto/results/2025-04-28_15-03-47_ditto_30entities_300seconds_uniformlaw_frequency30-delays.csv"
# ,"ditto/results/2025-04-29_09-27-08_ditto_40entities_300seconds_uniformlaw_frequency40-delays.csv"
# ,"ditto/results/2025-04-29_09-52-39_ditto_45entities_300seconds_uniformlaw_frequency45-delays.csv"
,"ditto/results/2025-04-29_10-20-42_ditto_50entities_300seconds_uniformlaw_frequency50-delays.csv"
# ,"ditto/results/2025-04-29_10-51-16_ditto_55entities_300seconds_uniformlaw_frequency55-delays.csv"
# ,"ditto/results/2025-04-29_11-24-22_ditto_60entities_300seconds_uniformlaw_frequency60-delays.csv"
# ,"ditto/results/2025-04-29_11-59-58_ditto_65entities_300seconds_uniformlaw_frequency65-delays.csv"
# ,"ditto/results/2025-04-29_12-38-06_ditto_70entities_300seconds_uniformlaw_frequency70-delays.csv"
# ,"ditto/results/2025-04-29_13-18-44_ditto_75entities_300seconds_uniformlaw_frequency75-delays.csv"
# ,"ditto/results/2025-04-29_14-01-54_ditto_80entities_300seconds_uniformlaw_frequency80-delays.csv"
# ,"ditto/results/2025-04-29_14-47-35_ditto_85entities_300seconds_uniformlaw_frequency85-delays.csv"
# ,"ditto/results/2025-04-29_15-35-47_ditto_90entities_300seconds_uniformlaw_frequency90-delays.csv"
# ,"ditto/results/2025-04-29_16-26-30_ditto_95entities_300seconds_uniformlaw_frequency95-delays.csv"
                 ]

csv_filepaths_orion = [
    "orion_ld/results/2025-04-30_13-19-31_orion_ld_10entities_300seconds_uniformlaw_frequency10-delays.csv",
    "orion_ld/results/2025-04-30_13-54-16_orion_ld_30entities_300seconds_uniformlaw_frequency30-delays.csv",
    "orion_ld/results/2025-04-30_15-31-19_orion_ld_50entities_300seconds_uniformlaw_frequency50-delays.csv"
]

csv_filepaths_scorpio = [
    "scorpio/results/2025-04-30_10-20-01_scorpio_10entities_300seconds_uniformlaw_frequency10-delays.csv",
    # "scorpio/results/2025-04-30_10-54-48_scorpio_30entities_300seconds_uniformlaw_frequency30-delays.csv",
    # "scorpio/results/2025-04-30_12-31-59_scorpio_50entities_300seconds_uniformlaw_frequency50-delays.csv"
]

dictionnarys = {}
distribution_dict = {}
sorted_columns_dict = {}
for filepath in csv_filepaths_ditto:
    fp = "ditto " + filepath.split("ditto_")[1].split("_300")[0]
    dict_columns = extraire_colonnes_csv(filepath)
    dictionnarys[fp] = dict_columns
    distribution_dict[fp] = get_distribution_list_from_percentiles(dict_columns, p_list)
    sorted_columns_dict[fp] = sorted([round(float(x) * 1000) for x in dict_columns["delay (s)"]])

for filepath in csv_filepaths_orion:
    fp = "orion-LD " + filepath.split("orion_ld")[2].split("_300")[0][1:]
    dict_columns = extraire_colonnes_csv(filepath)
    dictionnarys[fp] = dict_columns
    distribution_dict[fp] = get_distribution_list_from_percentiles(dict_columns, p_list)
    sorted_columns_dict[fp] = sorted([round(float(x) * 1000) for x in dict_columns["delay (s)"]])

for filepath in csv_filepaths_scorpio:
    fp = "scorpio " + filepath.split("scorpio")[2].split("_300")[0][1:]
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
plt.xlim(right=40)
plt.grid(True, which="both", ls="--", linewidth=0.5)
plt.legend()
plt.tight_layout()
plt.savefig("comparison results/ccdf_plot.png", dpi=300)
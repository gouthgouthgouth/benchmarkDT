import csv
import glob
import itertools
import matplotlib.pyplot as plt
import numpy as np

p_list = [0.5, 0.9, 0.99, 0.999, 0.9999, 1]
linestyles = itertools.cycle(('-', '--', ':'))
csv_filepaths_ditto = sorted(glob.glob("violin_plots_data_4g/ditto/results/*.csv"))
csv_filepaths_orion = sorted(glob.glob("violin_plots_data_4g/orion_ld/results/*.csv"))
csv_filepaths_scorpio = sorted(glob.glob("violin_plots_data_4g/scorpio/results/*.csv"))

all_files = csv_filepaths_scorpio + csv_filepaths_orion + csv_filepaths_ditto

duration = "3600"
entities = 50

lambdas_lists = ["5-10-20", "10-20-40", "20-40-80"]


toremove = []
for file in csv_filepaths_ditto + csv_filepaths_scorpio + csv_filepaths_orion:
    if "lambdas_list" in file or duration not in file or "lambdas" not in file or f"{str(entities)}entities" not in file:
        toremove.append(file)
for file in toremove:
    for csv_files in [csv_filepaths_ditto, csv_filepaths_orion, csv_filepaths_scorpio]:
        if file in csv_files:
            csv_files.remove(file)

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

dictionnarys = {}
distribution_dict = {}
sorted_columns_dict = {}
for filepath in csv_filepaths_ditto:

    lambdas = filepath.split("lambdas_")[1].split("-delays")[0]
    lambdas_str = ""
    for i in range(len(lambdas.split("-"))-1):
        lambdas_str += lambdas.split("-")[i] + ", "
    lambdas_str += lambdas.split("-")[-1]
    fp = "Ditto, " + "lambdas = " + lambdas_str

    dict_columns = extraire_colonnes_csv(filepath)
    dictionnarys[fp] = dict_columns
    distribution_dict[fp] = get_distribution_list_from_percentiles(dict_columns, p_list)
    sorted_columns_dict[fp] = sorted([round(float(x) * 1000) for x in dict_columns["delay (s)"]])

for filepath in csv_filepaths_orion:

    lambdas = filepath.split("lambdas_")[1].split("-delays")[0]
    lambdas_str = ""
    for i in range(len(lambdas.split("-"))-1):
        lambdas_str += lambdas.split("-")[i] + ", "
    lambdas_str += lambdas.split("-")[-1]
    fp = "Orion-LD, " + "lambdas = " + lambdas_str

    dict_columns = extraire_colonnes_csv(filepath)
    dictionnarys[fp] = dict_columns
    distribution_dict[fp] = get_distribution_list_from_percentiles(dict_columns, p_list)
    sorted_columns_dict[fp] = sorted([round(float(x) * 1000) for x in dict_columns["delay (s)"]])

for filepath in csv_filepaths_scorpio:

    lambdas = filepath.split("lambdas_")[1].split("-delays")[0]
    lambdas_str = ""
    for i in range(len(lambdas.split("-"))-1):
        lambdas_str += lambdas.split("-")[i] + ", "
    lambdas_str += lambdas.split("-")[-1]

    fp = "Scorpio, " + "lambdas = " + lambdas_str
    dict_columns = extraire_colonnes_csv(filepath)
    dictionnarys[fp] = dict_columns
    distribution_dict[fp] = get_distribution_list_from_percentiles(dict_columns, p_list)
    sorted_columns_dict[fp] = sorted([round(float(x) * 1000) for x in dict_columns["delay (s)"]])
    # delays_filtered = [x for x in dict_columns["delay (s)"] if x[:5] != "Error"]
    # sorted_columns_dict[fp] = sorted([round(float(x) * 1000) for x in delays_filtered])

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
    ccdf = 1.0 - np.arange(1, len(data)+1) / len(data)
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
plt.savefig(f"violin_plots_figs/ccdf/ccdf_lambdas={lambdas_lists}_duration={duration}s.png", dpi=300)

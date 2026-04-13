import math
import pprint

import matplotlib.pyplot as plt
import numpy as np
import itertools
import glob
import re

from analysis.common import extraire_colonnes_csv, get_distribution_list_from_percentiles

linestyles = itertools.cycle(('-', '--', ':'))

p_list = [0.5, 0.9, 0.99, 0.999, 1]
csv_filepaths_ditto = sorted(glob.glob("conf paper results/ditto/bytes_per_attribute/*.csv"), key=lambda f: int(re.search(r'_(\d+)bpa_', f).group(1)))
csv_filepaths_orion = sorted(glob.glob("conf paper results/orion_ld/bytes_per_attribute/*.csv"), key=lambda f: int(re.search(r'_(\d+)bpa_', f).group(1)))
csv_filepaths_scorpio = sorted(glob.glob("conf paper results/scorpio/bytes_per_attribute/*.csv"), key=lambda f: int(re.search(r'_(\d+)bpa_', f).group(1)))

# Uncomment to filter certain results
# for files in [csv_filepaths_ditto, csv_filepaths_orion, csv_filepaths_scorpio]:
#     for file in files:
#         if "70entities" in file:
#             files.remove(file)

def to_power_notation(n):
    if n == 0:
        return "0"
    power = math.log10(n)
    if not power.is_integer():
        return str(n)  # Pas une puissance exacte de 10
    power = int(power)
    superscripts = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")
    return f"10{str(power).translate(superscripts)}"

dictionnarys = {}
distribution_dict = {}
sorted_columns_dict = {}
for filepath in csv_filepaths_ditto:
    bpa = int(filepath.split("attr_")[1].split("bpa")[0])
    fp = "ditto, " + to_power_notation(bpa) + " bytes/attribute"
    dict_columns = extraire_colonnes_csv(filepath)
    dictionnarys[fp] = dict_columns
    distribution_dict[fp] = get_distribution_list_from_percentiles(dict_columns, p_list)
    sorted_columns_dict[fp] = sorted([round(float(x) * 1000) for x in dict_columns["delay (s)"]])

for filepath in csv_filepaths_orion:
    bpa = int(filepath.split("attr_")[1].split("bpa")[0])
    fp = "orion-LD, " + to_power_notation(bpa) + " bytes/attribute"
    dict_columns = extraire_colonnes_csv(filepath)
    dictionnarys[fp] = dict_columns
    distribution_dict[fp] = get_distribution_list_from_percentiles(dict_columns, p_list)
    sorted_columns_dict[fp] = sorted([round(float(x) * 1000) for x in dict_columns["delay (s)"]])

for filepath in csv_filepaths_scorpio:
    bpa = int(filepath.split("attr_")[1].split("bpa")[0])
    fp = "scorpio, " + to_power_notation(bpa) + " bytes/attribute"
    dict_columns = extraire_colonnes_csv(filepath)
    dictionnarys[fp] = dict_columns
    distribution_dict[fp] = get_distribution_list_from_percentiles(dict_columns, p_list)
    sorted_columns_dict[fp] = sorted([round(float(x) * 1000) for x in dict_columns["delay (s)"]])
    # delays_filtered = [x for x in dict_columns["delay (s)"] if x[:5] != "Error"]
    # sorted_columns_dict[fp] = sorted([round(float(x) * 1000) for x in delays_filtered])

plt.figure(figsize=(10, 6))

colors = {"ditto": "red", "orion": "blue", "scorp": "green"}
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
    print(label)
    color = colors.get(label[:5], None)
    plt.semilogy(data, ccdf, label=label, linestyle=next(linestyles), color=color)

plt.xlabel("processing time (ms)")
plt.ylabel("CCDF")
plt.xscale("log")
plt.xlim(left=1)
plt.xlim(right=4000)
plt.grid(True, which="both", ls="--", linewidth=0.5)
plt.legend(loc="upper right", fontsize=15)
plt.tight_layout()
plt.savefig("comparison results/plot_bpa.png", dpi=300)

pprint.pprint(distribution_dict)
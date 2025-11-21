import csv
import glob
import re
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

csv_filepaths_ditto = sorted(glob.glob("violin_plots_data_4g/ditto/results/*.csv"))
csv_filepaths_orion = sorted(glob.glob("violin_plots_data_4g/orion_ld/results/*.csv"))
csv_filepaths_scorpio = sorted(glob.glob("violin_plots_data_4g/scorpio/results/*.csv"))

all_files = csv_filepaths_scorpio + csv_filepaths_orion + csv_filepaths_ditto

duration = "3600"
lambdas = "20-40-80"

toremove = []
for file in all_files:
    if "lambdas_list" in file:
        toremove.append(file)
for file in toremove:
    if file in all_files:
        all_files.remove(file)

files_to_plot = []

for f in all_files:
    if duration in f and lambdas in f:
        files_to_plot.append(f)

def extraire_colonnes_csv(filepath):
    with open(filepath, newline='', encoding='utf-8') as f:
        lecteur = csv.reader(f)
        entetes = next(lecteur)
        colonnes = [[] for _ in entetes]
        for ligne in lecteur:
            for i, valeur in enumerate(ligne):
                colonnes[i].append(valeur)
    return dict(zip(entetes, colonnes))

colonnes = {}
all_values = []
all_labels = []

dfs = {}

for f in files_to_plot:
    delais = extraire_colonnes_csv(f)["delay (s)"]
    for i in range(len(delais)):
        delais[i] = float(delais[i])
    colonnes[f] = extraire_colonnes_csv(f)["delay (s)"]

    colonne_delais_brute = extraire_colonnes_csv(f)["delay (s)"]
    colonne_delais = []
    deleted = 0
    for i in range(len(colonne_delais_brute)):
        if 0 < float(colonne_delais_brute[i]) < 1:
            colonne_delais.append(colonne_delais_brute[i])
        else:
            deleted += 1
    print(deleted)

    df = pd.DataFrame({
        "delai": colonne_delais_brute,
        "source": (["f"] * len(colonne_delais_brute))
    })

    # mask_bad = pd.to_numeric(df["delai"], errors="coerce").isna()
    # print(df.loc[mask_bad].head(20))
    df["delai"] = (
        df["delai"]
        .astype(str)
        .str.strip()
        .str.replace(",", ".")
        .str.replace("'", "")
        .str.replace("\"", "")
    )
    df["delai"] = pd.to_numeric(df["delai"], errors="coerce")
    df["delai"] = df["delai"] * 1000
    dfs[f] = df
    print(df["delai"].dtype)
    print(df["delai"].describe())

# --- Création des violins ---
n = len(dfs)
fig, axes = plt.subplots(1, n, figsize=(6 * n, 6), sharey=True)

if n == 1:
    axes = [axes]

colors = {
    "orion_ld": "#0000ff",  # Bleu
    "ditto": "#ff0000",     # Orange
    "scorpio": "#00ff00"    # Vert
}

for ax, f in zip(axes, dfs):

    if "orion" in f:
        title = "Fiware orion_ld"
        source_name = "orion_ld"
    elif "ditto" in f:
        title = "Eclipse ditto"
        source_name = "ditto"
    elif "scorpio" in f:
        title = "Fiware scorpio"
        source_name = "scorpio"

    sns.violinplot(
        data=dfs[f],
        x="source",
        y="delai",
        hue="source",
        legend=False,
        inner="quartile",
        linewidth=1.2,
        palette=[colors[source_name]],
        ax=ax
    )

    ax.set_title(title)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.set_ylim(0, 50)
    ax.set_xlabel("")
    ax.set_ylabel("Délai (ms)")
    ax.set_xticklabels("")
    # ax.yaxis.set_major_locator(plt.MultipleLocator(0.005))

plt.tight_layout()
plt.savefig(f"violin_plots_figs/duration_{duration}s_lambdas{lambdas}")

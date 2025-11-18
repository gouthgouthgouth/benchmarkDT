import csv
import glob
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

csv_filepaths_ditto = sorted(glob.glob("violin_plots_data/ditto/results/*.csv"))
csv_filepaths_orion = sorted(glob.glob("violin_plots_data/orion_ld/results/*.csv"))
csv_filepaths_scorpio = sorted(glob.glob("violin_plots_data/scorpio/results/*.csv"))
all_files = csv_filepaths_scorpio + csv_filepaths_orion + csv_filepaths_ditto
duration = "18000"
lambdas = "5-10-20"
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
        if 0 < float(colonne_delais_brute[i]) < 10:
            colonne_delais.append(colonne_delais_brute[i])
        else:
            deleted += 1
    df = pd.DataFrame({
        "delai": colonne_delais,
        "source": (["f"] * len(colonne_delais))
    })
    df["delai"] = (
        df["delai"]
        .astype(str)
        .str.strip()
        .str.replace(",", ".")
        .str.replace("'", "")
        .str.replace("\"", "")
    )
    df["delai"] = pd.to_numeric(df["delai"], errors="coerce")
    nombre_nan = df["delai"].isna().sum()
    print(f"Nombre de NaN : {nombre_nan}")
    df["delai"] = df["delai"] * 1000
    dfs[f] = df
    print(df["delai"].describe())

# --- Création des histogrammes ---
n = len(dfs)
fig, axes = plt.subplots(1, n, figsize=(6 * n, 6), sharey=True)
if n == 1:
    axes = [axes]
colors = {
    "orion_ld": "blue",  # Bleu
    "ditto": "red",     # Rouge
    "scorpio": "green"    # Vert
}
for ax, f in zip(axes, dfs):
    if "orion" in f:
        title = "Fiware orion_ld"
        source_name = "orion_ld"
        bins = 20
    elif "ditto" in f:
        title = "Eclipse ditto"
        source_name = "ditto"
        bins = 50
    elif "scorpio" in f:
        title = "Fiware scorpio"
        source_name = "scorpio"
    sns.histplot(
        data=dfs[f],
        x="delai",
        hue="source",
        legend=False,
        kde=False,
        bins=bins,  # Vous pouvez ajuster le nombre de bins selon vos préférences
        palette=[colors[source_name]],
        ax=ax
    )
    ax.set_title(title)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.set_yscale('log')  # Définir l'échelle logarithmique sur l'axe des y
    ax.set_xlabel("Delay (ms)")
    ax.set_ylabel("Frequency")
    # Définir les limites de l'axe x pour s'assurer que toutes les valeurs sont visibles
    # Ajouter une marge de 10% à gauche et à droite
    x_min = max(0, dfs[f]["delai"].min() - 0.1 * dfs[f]["delai"].min())
    x_max = dfs[f]["delai"].max() * 1.1
    # Si la valeur minimale est 0, définir une marge fixe à gauche
    if x_min == 0:
        x_min = -0.1 * dfs[f]["delai"].max()
    ax.set_xlim(x_min, 70)

plt.tight_layout()
plt.savefig(f"histogram_plots_figs/duration_{duration}s_lambdas{lambdas}")
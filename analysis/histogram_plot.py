"""
Histogram plot comparing end-to-end delay distributions across the three brokers.

Reads delay CSV files for a given experiment duration and MMPP lambda set, filters
outliers (delays outside 0–10 s), converts to milliseconds, then renders one
histogram per broker side by side with a shared Y axis (log scale).

Configure ``duration``, ``lambdas``, and ``bin_size`` at the top of the script
before running.
"""
import glob
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import pandas as pd

from analysis.common import extraire_colonnes_csv

# --- Parameters ---
duration = "18000"   # Experiment duration to plot (as it appears in the file name)
lambdas = "10-20-40" # MMPP lambda set to plot
bin_size = 3         # Histogram bin width in ms; set to None for automatic sizing
x_min = None         # Left x-axis limit; None = auto
x_max = None         # Right x-axis limit; None = auto

# --- File discovery ---
csv_filepaths_ditto = sorted(glob.glob("violin_plots_data_4g/ditto/results/*.csv"))
csv_filepaths_orion = sorted(glob.glob("violin_plots_data_4g/orion_ld/results/*.csv"))
csv_filepaths_scorpio = sorted(glob.glob("violin_plots_data_4g/scorpio/results/*.csv"))

# Collect all files, remove the lambda-schedule CSVs (not delay files), then
# keep only the files matching the configured duration and lambda set.
all_files = csv_filepaths_scorpio + csv_filepaths_orion + csv_filepaths_ditto
toremove = [f for f in all_files if "lambdas_list" in f]
for f in toremove:
    if f in all_files:
        all_files.remove(f)
files_to_plot = [f for f in all_files if duration in f and lambdas in f]

# --- Data loading and cleaning ---
colonnes = {}
all_values = []
all_labels = []
dfs = {}

for f in files_to_plot:
    colonne_delais_brute = extraire_colonnes_csv(f)["delay (s)"]

    # Filter out negative delays and extreme outliers (> 10 s).
    deleted = 0
    colonne_delais = []
    for i in range(len(colonne_delais_brute)):
        if 0 < float(colonne_delais_brute[i]) < 10:
            colonne_delais.append(colonne_delais_brute[i])
        else:
            deleted += 1

    df = pd.DataFrame({
        "delai": colonne_delais,
        "source": (["f"] * len(colonne_delais))
    })

    # Normalise the delay column (strip whitespace/quotes, replace commas) before
    # converting to numeric, then scale from seconds to milliseconds.
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

# --- Compute consistent bin edges across all histograms ---
all_delays = []
for f in files_to_plot:
    all_delays.extend(dfs[f]["delai"].dropna().tolist())

if bin_size is not None and all_delays:
    min_delay = min(all_delays)
    max_delay = max(all_delays)
    bins = np.arange(min_delay, max_delay + bin_size, bin_size)
else:
    bins = None

# --- Plot ---
n = len(dfs)
fig, axes = plt.subplots(1, n, figsize=(6 * n, 6), sharey=True)
if n == 1:
    axes = [axes]

colors = {
    "orion_ld": "blue",
    "ditto": "red",
    "scorpio": "green"
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

    # Auto-calculate axis limits if not overridden by the user.
    if x_min is None:
        x_min = max(0, dfs[f]["delai"].min() - 0.1 * dfs[f]["delai"].min())
        if x_min == 0:
            x_min = -0.1 * dfs[f]["delai"].max()
    if x_max is None:
        x_max = max([dfs[file]["delai"].max() * 1.05 for file in dfs])
    if bins is None:
        bins = 3

    sns.histplot(
        data=dfs[f],
        x="delai",
        hue="source",
        legend=False,
        kde=False,
        bins=bins,
        palette=[colors[source_name]],
        ax=ax
    )
    ax.set_title(title)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.set_yscale('log')
    ax.set_xlabel("Delay (ms)")
    ax.set_ylabel("Frequency")
    ax.set_xlim(x_min, x_max)

plt.tight_layout()
plt.savefig(f"histogram_plots_figs/duration_{duration}s_lambdas{lambdas}")

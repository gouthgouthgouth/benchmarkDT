"""
Percentile analysis: compute empirical latency percentiles for each
broker/lambda configuration and export the results as a double-entry
CSV table (rows = configurations, columns = percentile levels).
"""
import csv
import glob
import os
import pprint

from analysis.common import extraire_colonnes_csv, get_distribution_list_from_percentiles

# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
duration = "36000"
entities = 50
lambdas_lists = ["5-10-20", "10-20-40", "20-40-80"]

# Percentile levels to evaluate (values in [0, 1]).
p_list = [0.5, 0.9, 0.99, 0.999, 0.9999, 1.0]

OUTPUT_DIR = "tables"


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def percentile_label(p):
    """Convert a percentile float to a compact column header string.

    Examples: 0.5 → 'p50', 0.999 → 'p99.9', 1.0 → 'p100'.
    """
    pct = p * 100
    return f"p{int(pct)}" if pct == int(pct) else f"p{pct:g}"


def process_broker_files(filepaths, broker_name, p_list):
    """Build a percentile-distribution dict from a broker's CSV result files.

    For each file, the lambda values are extracted from the filename to build
    a human-readable label, then empirical percentile delays are computed.

    Args:
        filepaths (list[str]): Sorted list of CSV result file paths.
        broker_name (str): Display name of the broker (e.g. "Ditto").
        p_list (list[float]): Percentile levels in [0, 1].

    Returns:
        dict[str, list[int]]: Maps each config label to a list of delay
            values in milliseconds, one per percentile in p_list.
    """
    result = {}
    for filepath in filepaths:
        # Extract the lambda sequence from the filename, e.g. "5-10-20".
        lambdas_raw = filepath.split("lambdas_")[1].split("-delays")[0]
        lambdas_str = ", ".join(lambdas_raw.split("-"))
        label = f"{broker_name}, lambdas = {lambdas_str}"

        dict_columns = extraire_colonnes_csv(filepath)
        result[label] = get_distribution_list_from_percentiles(dict_columns, p_list)

    return result


def export_to_csv(distribution_dict, p_list, output_dir, filename="percentile_table.csv"):
    """Export the distribution dictionary as a double-entry CSV table.

    The first column holds the configuration label; subsequent columns hold
    the delay (ms) at each requested percentile level.

    Args:
        distribution_dict (dict[str, list[int]]): Mapping from config label
            to delay values, as returned by process_broker_files.
        p_list (list[float]): Percentile levels — used to generate headers.
        output_dir (str): Directory where the CSV file will be written.
        filename (str): Output filename (default: "percentile_table.csv").
    """
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)

    headers = ["Configuration"] + [percentile_label(p) for p in p_list]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for label, values in distribution_dict.items():
            writer.writerow([label] + values)

    print(f"Table exported to {output_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

# Collect result files for each broker.
csv_filepaths_ditto   = sorted(glob.glob("../measures/ditto/results_merged/*.csv"))
csv_filepaths_orion   = sorted(glob.glob("../measures/orion_ld/results_merged/*.csv"))
csv_filepaths_scorpio = sorted(glob.glob("../measures/scorpio/results_merged/*.csv"))

# Compute empirical percentile distributions for every configuration.
distribution_dict = {}
distribution_dict.update(process_broker_files(csv_filepaths_ditto,   "Ditto",    p_list))
distribution_dict.update(process_broker_files(csv_filepaths_orion,   "Orion-LD", p_list))
distribution_dict.update(process_broker_files(csv_filepaths_scorpio, "Scorpio",  p_list))

pprint.pprint(distribution_dict)

# Export to a double-entry CSV table in the tables/ output directory.
export_to_csv(distribution_dict, p_list, OUTPUT_DIR)

"""
Shared data-loading utilities for the analysis scripts.
"""
import csv


def extraire_colonnes_csv(filepath):
    """Read a CSV file and return its columns as a dictionary of lists.

    Args:
        filepath (str): Path to the CSV file.

    Returns:
        dict[str, list[str]]: Mapping from column header to a list of raw
            string values (one entry per data row).
    """
    with open(filepath, newline='', encoding='utf-8') as f:
        lecteur = csv.reader(f)
        entetes = next(lecteur)
        colonnes = [[] for _ in entetes]
        for ligne in lecteur:
            for i, valeur in enumerate(ligne):
                colonnes[i].append(valeur)
    return dict(zip(entetes, colonnes))


def get_distribution_list_from_percentiles(dictionnary_columns, percentiles_list):
    """Compute delay values (in ms) at given empirical percentile levels.

    Non-numeric entries in the ``"delay (s)"`` column (e.g. error strings) are
    silently skipped. Delay values are converted from seconds to milliseconds
    and rounded to the nearest integer.

    Args:
        dictionnary_columns (dict[str, list[str]]): Column dictionary as returned
            by ``extraire_colonnes_csv``. Must contain a ``"delay (s)"`` key.
        percentiles_list (list[float]): Percentile levels in [0, 1], e.g.
            ``[0.5, 0.9, 0.99, 1]``.

    Returns:
        list[int]: Delay in milliseconds at each requested percentile, in the
            same order as ``percentiles_list``.
    """
    distribution_list = []
    delays_column = dictionnary_columns["delay (s)"]

    # Convert string values to float, ignoring unparseable entries.
    delays_column_float = []
    for x in delays_column:
        try:
            delays_column_float.append(float(x))
        except:
            pass

    sorted_column = sorted(delays_column_float)
    length = len(sorted_column)

    for percentile in percentiles_list:
        # Clamp the index to the last element to avoid an off-by-one at p=1.0.
        i = round(percentile * length)
        if i < length:
            distribution_list.append(round(sorted_column[i] * 1000))
        else:
            distribution_list.append(round(sorted_column[-1] * 1000))

    return distribution_list

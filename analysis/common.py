import csv


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

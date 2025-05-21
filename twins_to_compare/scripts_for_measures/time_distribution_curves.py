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

def get_distribution_from_percentile(column, percentile):
    sorted_column = column.sort()


def get_distribution_list_from_percentiles(dictionnary_columns, percentiles_list):
    distribution_list =
    for percentile in percentiles_list:


csv_filepath = ""

dict_columns = extraire_colonnes_csv(csv_filepath)

distribution_list = get_distribution_from_percentiles()
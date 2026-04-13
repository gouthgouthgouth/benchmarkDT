import string
from itertools import product, islice


def generate_compact_attributes(n):
    alphabet = string.ascii_lowercase
    ids = map(lambda t: ''.join(t), islice(product(alphabet, repeat=1), n)) if n <= 26 else \
        map(lambda t: ''.join(t), islice(product(alphabet, repeat=2), n))

    return [
        {
            "object_id": id_,
            "name": f"attribute_{id_}",
            "type": "String"
        }
        for id_ in ids
    ]

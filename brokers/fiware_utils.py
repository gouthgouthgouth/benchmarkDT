"""
Shared utilities for FIWARE-based broker adapters (Scorpio and Orion-LD).
"""
import string
from itertools import product, islice


def generate_compact_attributes(n):
    """Generate a list of IoT Agent attribute descriptors with compact IDs.

    IDs are drawn from the lowercase alphabet in lexicographic order (a, b, …, z,
    aa, ab, …) so they stay short regardless of the attribute count.

    Args:
        n (int): Number of attributes to generate.

    Returns:
        list[dict]: Each dict has the keys ``object_id``, ``name``, and ``type``
            as expected by the FIWARE IoT Agent device provisioning API.
    """
    alphabet = string.ascii_lowercase
    # Use single letters for up to 26 attributes; fall back to two-letter pairs beyond that.
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

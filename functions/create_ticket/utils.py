from itertools import groupby

def group_by(records, key_one, key_two, key_two_nested):
    """
    Groups a list of json records based on two keys.
    """

    grouped = groupby(
        sorted(records, key=lambda k: (k.get(key_one), k.get(key_two, {}).get(key_two_nested))),
        key=lambda k: (k.get(key_one), k.get(key_two, {}).get(key_two_nested)))

    return grouped

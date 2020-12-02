from itertools import groupby
from google.cloud import datastore


def fetch(kind, key, comparison, value):
    """
    Fetches datastore records given a kind and query parameters.
    """

    client = datastore.Client()
    query = client.query(kind=kind)

    query.add_filter(key, comparison, value)

    results = [dict(entity) for entity in query.fetch()]

    return results


def group_by(records, key_one, key_two, key_two_nested):
    """
    Groups a list of json records based on two keys.
    """

    grouped = groupby(
        sorted(records, key=lambda k: (k.get(key_one), k.get(key_two, {}).get(key_two_nested))),
        key=lambda k: (k.get(key_one), k.get(key_two, {}).get(key_two_nested)))

    return grouped

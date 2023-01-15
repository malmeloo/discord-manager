"""Initializes empty configs, or re-initializes existing ones by wiping them."""


def migrate(conf: dict):
    return {
        '_v': 1,
        'instances': {}
    }

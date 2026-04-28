"""Synthetic config-key consumer."""
import os


def read_config():
    api_key = os.environ["KNOWN_KEY"]
    db = os.environ.get("UNDEF_KEY")
    region = os.getenv("ANOTHER_KNOWN_KEY")
    return api_key, db, region

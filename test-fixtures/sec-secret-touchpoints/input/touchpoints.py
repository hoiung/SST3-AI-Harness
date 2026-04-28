"""Synthetic env-var + credential touchpoints."""
import os
from dotenv import load_dotenv


def env_reads():
    api_key = os.environ["API_KEY"]
    db_url = os.environ.get("DATABASE_URL")
    region = os.getenv("AWS_REGION")
    return api_key, db_url, region


def init_dotenv():
    load_dotenv()


# Synthetic password literal (safe — fixture-only sentinel)
PASSWORD_LITERAL = 'password = "fixture-fake-not-real"'

# Synthetic AWS-key (test pattern starting with AKIA prefix per regex)
AWS_KEY_FAKE = "AKIAFIXTUREFAKEABC12"

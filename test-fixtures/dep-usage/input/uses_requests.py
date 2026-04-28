"""Synthetic dep-usage sample for `requests` package."""
import requests
import requests as req
from requests import Session
from requests.auth import HTTPBasicAuth


def fetch(url):
    r = requests.get(url)
    s = req.Session()
    s2 = Session()
    auth = HTTPBasicAuth("user", "pass")
    return r, s, s2, auth

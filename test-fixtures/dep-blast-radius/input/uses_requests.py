"""Synthetic blast-radius sample — same shape as dep-usage fixture."""
import requests


def caller_a():
    return requests.get("https://example.com")


def caller_b():
    return requests.post("https://example.com", data={})

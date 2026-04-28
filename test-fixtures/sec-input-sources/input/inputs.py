"""Synthetic untrusted-input entry points."""
import sys
from flask import request


def http_handlers():
    body = request.json
    form = request.form
    query = request.args
    return body, form, query


def cli_argv():
    return sys.argv


def stdin_read():
    return sys.stdin.read()


def user_input():
    return input("? ")


def file_open(path):
    return open(path)

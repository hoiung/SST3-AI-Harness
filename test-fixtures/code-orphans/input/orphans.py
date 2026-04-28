"""Synthetic orphan-detection sample."""

__all__ = ["public_used"]


def public_used():
    return 1


def public_orphan():
    return 2


def used_internally():
    return public_used()

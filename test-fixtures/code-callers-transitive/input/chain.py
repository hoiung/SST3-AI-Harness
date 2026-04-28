"""Synthetic 3-deep call chain for callers-transitive BFS."""


def leaf():
    return 42


def mid():
    return leaf()


def top():
    return mid()


def caller_of_top():
    return top()

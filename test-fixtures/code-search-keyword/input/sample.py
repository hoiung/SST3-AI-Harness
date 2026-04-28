def my_unique_marker():
    """A function with a unique name we can grep for in the fixture."""
    return 42


def other_function():
    return my_unique_marker()

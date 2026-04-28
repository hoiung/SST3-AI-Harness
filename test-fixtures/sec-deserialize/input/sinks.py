"""Synthetic unsafe-deserialise + dynamic-eval sites."""
import pickle
import yaml
import marshal


def load_pickle(blob):
    return pickle.loads(blob)


def load_yaml_unsafe(blob):
    return yaml.load(blob)


def load_yaml_safe(blob):
    return yaml.load(blob, Loader=yaml.SafeLoader)


def load_marshal(blob):
    return marshal.loads(blob)


def dyn_eval(s):
    return eval(s)


def dyn_exec(s):
    exec(s)

"""Synthetic shell-out sites for sst3-sec-subprocess fixture."""
import subprocess
import os


def run_lit():
    subprocess.run(["ls", "-la"], check=True)
    subprocess.Popen(["echo", "hi"])


def run_var(cmd_list):
    subprocess.call(cmd_list)
    os.system("echo $HOME")
    os.popen("date").read()

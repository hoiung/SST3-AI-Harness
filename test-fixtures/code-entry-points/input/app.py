"""Synthetic entry-point sample."""
from flask import Flask

app = Flask(__name__)


@app.route("/health")
def health():
    return "ok"


@app.get("/users")
def list_users():
    return []


def main():
    app.run()


if __name__ == "__main__":
    main()

"""Python API service that reads/writes the same jobs_queue SQL table.
Demonstrates the cross-language M6 edge: the table is shared state across
the python-api and a hypothetical rust-worker."""


def enqueue(conn, payload):
    return conn.execute(
        "INSERT INTO jobs_queue (payload, status) VALUES (%s, %s)",
        (payload, "pending"),
    )


def fetch_done(conn):
    return conn.execute(
        "SELECT id, payload FROM jobs_queue WHERE status = 'done' ORDER BY id"
    ).fetchall()

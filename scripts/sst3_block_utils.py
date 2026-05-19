"""SST3 boundary-marker block utilities (Issue #493 Phase 1 / AC 1.3).

Shared core for boundary-marked propagation across both lanes:

* Lane A — CLAUDE.md template (single HTML-comment boundary marker;
  propagate-template.py). Above-marker = SST3-managed; below = project.

* Lane B' — managed pre-commit blocks (paired YAML ``# >>>`` / ``# <<<``
  markers; propagate-block.py). The block BETWEEN the two markers is
  SST3-managed; content above the start marker AND below the end marker
  is consumer-local.

Public API (AC 1.3 export list — do NOT rename):

    find_boundary_lines(content, start_marker, end_marker=None)
        -> tuple[int, int]
    extract_managed_block(content, start_marker, end_marker=None)
        -> str | None
    strip_marker_lines(content, marker_start, marker_end)
        -> str  (Stage 5 DEDUP-1 promotion; replaces the dead
                 extract_outside_block which had zero non-test callers)
    replace_managed_block(content, new_block, start_marker, end_marker)
        -> str
    atomic_write(path, content, encoding="utf-8")
        -> None

Line-anchored marker contract (Issue #493 AC 1.2): markers match only
when the marker substring appears at the start of a (lstrip'ed) line.
A consumer's below-marker comment that quotes "SST3 MANAGED BLOCK" in
prose must NOT trip mis-detection.

Fail-loud contract (Issue #493 AC 1.8 corruption fail-safe): the
helpers themselves never silently paper over corruption — they return
``None`` for "marker(s) missing" so the caller can decide whether to
treat that as first-apply insertion (propagate-block) or a hard error
(check-mirror-drift in --managed-blocks mode).
"""
from __future__ import annotations

import os
from pathlib import Path


def find_boundary_lines(
    content: str,
    start_marker: str,
    end_marker: str | None = None,
) -> tuple[int, int]:
    """Find 0-indexed line numbers of the start and (optionally) end markers.

    Line-anchored: a marker matches only when ``line.lstrip().startswith(marker)``
    is true for that line. Substring matches inside other text do not count.

    Args:
        content: file content as a single string.
        start_marker: required start-marker line prefix.
        end_marker: optional end-marker line prefix. ``None`` means
            single-marker mode (Lane A); paired-marker mode otherwise.

    Returns:
        ``(start_line, end_line)``. ``start_line == -1`` means start marker
        absent. In single-marker mode ``end_line`` is always ``-1`` (it was
        not searched). In paired-marker mode ``end_line == -1`` means the
        end marker is missing — caller decides how to react.

    Raises:
        ValueError: ambiguous duplicate markers, or end marker located
            before the start marker (corrupted ordering).
    """
    lines = content.splitlines()
    start_indices = [
        i for i, line in enumerate(lines)
        if line.lstrip().startswith(start_marker)
    ]
    if len(start_indices) > 1:
        raise ValueError(
            f"multiple start markers found at lines {start_indices} "
            f"(marker={start_marker!r}) — ambiguous, refusing to guess"
        )
    start_line = start_indices[0] if start_indices else -1

    if end_marker is None:
        return start_line, -1

    end_indices = [
        i for i, line in enumerate(lines)
        if line.lstrip().startswith(end_marker)
    ]
    if len(end_indices) > 1:
        raise ValueError(
            f"multiple end markers found at lines {end_indices} "
            f"(marker={end_marker!r}) — ambiguous, refusing to guess"
        )
    end_line = end_indices[0] if end_indices else -1

    if start_line != -1 and end_line != -1 and end_line < start_line:
        raise ValueError(
            f"end marker at line {end_line} appears before start marker "
            f"at line {start_line} — corrupted ordering"
        )

    return start_line, end_line


def extract_managed_block(
    content: str,
    start_marker: str,
    end_marker: str | None = None,
) -> str | None:
    """Extract the SST3-managed portion of ``content``.

    * Single-marker mode (``end_marker is None``): the managed portion is
      everything up to and including the start marker line. Used by Lane A
      callers that own their own boundary-block slicing on top.
    * Paired-marker mode: the managed portion is the lines strictly
      BETWEEN start and end markers (markers themselves excluded — they
      are propagated as part of the template, not consumer-owned).

    Returns:
        The managed block as a string, or ``None`` if the relevant
        marker(s) are missing.
    """
    start, end = find_boundary_lines(content, start_marker, end_marker)
    lines = content.splitlines(keepends=True)
    if end_marker is None:
        if start == -1:
            return None
        return "".join(lines[: start + 1])

    if start == -1 or end == -1:
        return None
    return "".join(lines[start + 1: end])


def strip_marker_lines(
    content: str,
    marker_start: str,
    marker_end: str,
) -> str:
    """Strip lines that contain only the boundary markers (and optional
    whitespace) from ``content``.

    Stage 5 DEDUP-1 promotion (L1-F): both ``propagate-block.py`` and
    ``check-mirror-drift.py`` previously carried near-identical private
    ``_strip_marker_lines`` implementations. Promoting to a public helper
    here means the canonical-block self-documentation pattern (the
    template ships with its own marker lines for human readability; those
    lines are stripped before propagation so the propagator's own markers
    drive insertion) is single-source.

    Returns:
        ``content`` with any line whose left-stripped form starts with
        either ``marker_start`` or ``marker_end`` removed verbatim.
        Other lines pass through unchanged including their trailing
        newlines.
    """
    return "".join(
        line for line in content.splitlines(keepends=True)
        if not (
            line.lstrip().startswith(marker_start)
            or line.lstrip().startswith(marker_end)
        )
    )


def replace_managed_block(
    content: str,
    new_block: str,
    start_marker: str,
    end_marker: str,
) -> str:
    """Replace the paired-marker managed block in ``content`` with ``new_block``.

    The start and end marker lines themselves are preserved; only the
    lines between them are replaced. ``new_block`` is inserted verbatim
    and a trailing newline is appended if missing.

    Single-marker replacement is intentionally NOT supported here —
    Lane A callers (propagate-template.py) drive their own merge logic
    via ``merge_sections``.

    Raises:
        ValueError: either marker missing (caller must handle first-apply
            insertion at a higher level) or ordering corrupted.
    """
    start, end = find_boundary_lines(content, start_marker, end_marker)
    if start == -1 or end == -1:
        raise ValueError(
            f"paired markers not both present (start={start}, end={end}); "
            "refusing to replace — caller must handle first-apply insertion."
        )
    lines = content.splitlines(keepends=True)
    if new_block and not new_block.endswith("\n"):
        new_block = new_block + "\n"
    new_lines = lines[: start + 1] + [new_block] + lines[end:]
    return "".join(new_lines)


def atomic_write(path: Path, content: str, encoding: str = "utf-8") -> None:
    """Write ``content`` to ``path`` via temp-file + ``os.replace``.

    Centralises the ``.tmp`` + atomic-rename pattern used by
    ``propagate-template.py`` (Lane A) and ``propagate-block.py``
    (Lane B'). ``propagate-mirrors.py`` (Lane B vendored-files) carries
    its own variant that additionally preserves the source's executable
    bit via ``os.chmod`` (issue #460 Stage 5 fix); migrating that variant
    to this helper would require a ``source_mode`` parameter — deferred
    as a future-consolidation task (not in #493 scope per JBGE).

    Stage 5 LEAK-1 fix (L1-F): the post-write ``os.replace`` may fail
    (NFS race, permission flip, target-dir gone). Pre-fix the ``.tmp``
    sidecar was leaked on the rename-failure path. Now wrapped in
    try/finally with ``tmp.unlink(missing_ok=True)`` on failure so the
    only persistent state post-call is either (a) the renamed target
    or (b) the original target unchanged.
    """
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    rename_succeeded = False
    try:
        tmp.write_text(content, encoding=encoding)
        os.replace(str(tmp), str(path))
        rename_succeeded = True
    finally:
        if not rename_succeeded and tmp.exists():
            tmp.unlink()

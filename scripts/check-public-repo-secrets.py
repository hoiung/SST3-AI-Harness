#!/usr/bin/env python3
"""
Public Repo Secret Detection Script

Scans codebase for secrets, business identifiers, and private paths
that must never be committed to public repositories.

Exit codes:
  0: No violations found, or not a public repo (PASS)
  1: Violations detected or script error (FAIL)

Usage:
  python check-public-repo-secrets.py <path>
  python check-public-repo-secrets.py <path> --staged-only
  python check-public-repo-secrets.py <path> --allowlist .secret-allowlist
"""

import argparse
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Set

try:
    from sst3_utils import (
        SST3UtilError,
        collect_source_files,
        fix_windows_console,
        get_repo_root,
        log_event,
        should_ignore_path,
    )
    fix_windows_console()
except ImportError:
    # Standalone mode — vendored copy without sst3_utils
    import io
    import json
    from datetime import datetime, timezone

    class SST3UtilError(RuntimeError):
        pass

    def fix_windows_console() -> None:
        if sys.platform == "win32":
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

    fix_windows_console()

    def should_ignore_path(file_path: Path, ignore_patterns, allowed_files=()) -> bool:
        file_str = str(file_path).replace("\\", "/")
        parts = file_path.parts
        for pattern in ignore_patterns:
            pattern_norm = pattern.replace("\\", "/")
            if Path(file_str).match(pattern_norm):
                return True
            clean = pattern_norm.strip("*/").strip("/")
            if clean in parts:
                return True
        return False

    def collect_source_files(
        base_path: Path, extensions, ignore_patterns=(), allowed_files=(),
    ) -> list:
        base = Path(base_path)
        if not base.exists():
            return []
        files = []
        for ext in extensions:
            files.extend(base.rglob(f"*{ext}"))
        if ignore_patterns:
            files = [f for f in files if not should_ignore_path(f, ignore_patterns)]
        return sorted(set(files))

    def get_repo_root() -> Path:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True,
        )
        return Path(result.stdout.strip())

    def log_event(script: str, event: str, level: str = "info", **fields) -> None:
        try:
            log_dir = Path.home() / ".cache" / "sst3"
            log_dir.mkdir(parents=True, exist_ok=True)
            record = json.dumps({
                "ts": datetime.now(timezone.utc).isoformat(),
                "script": script, "event": event, "level": level,
                "fields": fields,
            }, ensure_ascii=True)
            with open(log_dir / "sst3-events.jsonl", "a") as f:
                f.write(record + "\n")
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Finding data structure
# ---------------------------------------------------------------------------

class Finding(NamedTuple):
    line_num: int
    line: str
    category: str
    message: str
    fix: str


# ---------------------------------------------------------------------------
# Pattern definitions — compiled once at module load
# ---------------------------------------------------------------------------

PLATFORM_TOKEN_PATTERNS: List[Dict] = [
    {
        "pattern": re.compile(r"ghp_[A-Za-z0-9]{36}"),
        "message": "GitHub Personal Access Token (classic)",
        "fix": "Move to .env (gitignored) and reference via environment variable",
    },
    {
        "pattern": re.compile(r"github_pat_[A-Za-z0-9_]{82}"),
        "message": "GitHub Fine-Grained Personal Access Token",
        "fix": "Move to .env (gitignored) and reference via environment variable",
    },
    {
        "pattern": re.compile(r"gh[ours]_[A-Za-z0-9]{36}"),
        "message": "GitHub OAuth/App Token",
        "fix": "Move to .env (gitignored) and reference via environment variable",
    },
    {
        "pattern": re.compile(
            r"(?<![A-Z0-9])(?:AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)"
            r"[A-Z0-9]{16}(?![A-Z0-9])"
        ),
        "message": "AWS Access Key ID",
        "fix": "Move to .env (gitignored) and reference via environment variable",
    },
    {
        "pattern": re.compile(r"AIza[0-9A-Za-z\-_]{35}"),
        "message": "GCP API Key",
        "fix": "Move to .env (gitignored) and reference via environment variable",
    },
    {
        "pattern": re.compile(r"sk_live_[0-9A-Za-z]{24,}"),
        "message": "Stripe Live Secret Key",
        "fix": "Move to .env (gitignored) and reference via environment variable",
    },
    {
        "pattern": re.compile(r"sk_test_[0-9A-Za-z]{24,}"),
        "message": "Stripe Test Secret Key",
        "fix": "Move to .env (gitignored) and reference via environment variable",
    },
    {
        "pattern": re.compile(r"whsec_[A-Za-z0-9]{32,}"),
        "message": "Stripe Webhook Secret",
        "fix": "Move to .env (gitignored) and reference via environment variable",
    },
    {
        "pattern": re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
        "message": "JWT Token",
        "fix": "Move to .env (gitignored) and reference via environment variable",
    },
]

PRIVATE_KEY_PATTERNS: List[Dict] = [
    {
        "pattern": re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED )?PRIVATE KEY-----"),
        "message": "Private key header detected",
        "fix": "Never commit private keys. Use environment variable or secrets manager.",
    },
    {
        "pattern": re.compile(r"-----BEGIN PGP PRIVATE KEY BLOCK-----"),
        "message": "PGP private key block detected",
        "fix": "Never commit private keys. Use environment variable or secrets manager.",
    },
]

GENERIC_SECRET_PATTERNS: List[Dict] = [
    {
        "pattern": re.compile(
            r"(?i)(?:password|passwd|secret|token|api_?key|auth_?key|credential|seller_id|account_id)"
            r"\s*[=:]\s*['\"]?[^\s'\"]{4,}"
        ),
        "message": "Generic secret assignment",
        "fix": "Move to .env (gitignored) and reference via environment variable",
    },
    {
        "pattern": re.compile(r"(?i)(?:DB|DATABASE)_(?:PASSWORD|PASS|PWD|SECRET)\s*=\s*.+"),
        "message": "Database password assignment",
        "fix": "Move to .env (gitignored) and reference via environment variable",
    },
    {
        "pattern": re.compile(r"postgres(?:ql)?://[^:]+:[^@]{3,}@[^\s'\"]+"),
        "message": "PostgreSQL connection string with embedded credentials",
        "fix": "Move credentials to .env and construct connection string at runtime",
    },
    {
        "pattern": re.compile(r"mongodb(?:\+srv)?://[^:]+:[^@]{3,}@[^\s'\"]+"),
        "message": "MongoDB connection string with embedded credentials",
        "fix": "Move credentials to .env and construct connection string at runtime",
    },
    {
        "pattern": re.compile(r"redis(?:s)?://[^:]*:[^@]{3,}@[^\s'\"]+"),
        "message": "Redis connection string with embedded credentials",
        "fix": "Move credentials to .env and construct connection string at runtime",
    },
    {
        "pattern": re.compile(r"mysql://[^:]+:[^@]{3,}@[^\s'\"]+"),
        "message": "MySQL connection string with embedded credentials",
        "fix": "Move credentials to .env and construct connection string at runtime",
    },
]

PRIVATE_PATH_PATTERNS: List[Dict] = [
    {
        "pattern": re.compile(r"/mnt/[a-z]/[Uu]sers/"),
        "message": "WSL Windows user path detected",
        "fix": "Use environment variable or relative path",
    },
    {
        "pattern": re.compile(r"(?:C:\\\\Users\\\\|C:/Users/)"),
        "message": "Windows user path detected",
        "fix": "Use environment variable or relative path",
    },
    {
        "pattern": re.compile(r"My Drive/"),
        "message": "Google Drive path detected",
        "fix": "Use environment variable or relative path",
    },
    {
        "pattern": re.compile(r"Google Drive/"),
        "message": "Google Drive path detected",
        "fix": "Use environment variable or relative path",
    },
    {
        "pattern": re.compile(r"OneDrive/"),
        "message": "OneDrive path detected",
        "fix": "Use environment variable or relative path",
    },
]

# Placeholder values that should NOT trigger GENERIC_SECRET findings
PLACEHOLDER_PATTERNS: List[re.Pattern] = [
    re.compile(r"^your[-_]?\w+", re.IGNORECASE),
    re.compile(r"^changeme$", re.IGNORECASE),
    re.compile(r"^change_me$", re.IGNORECASE),
    re.compile(r"^example$", re.IGNORECASE),
    re.compile(r"^sample$", re.IGNORECASE),
    re.compile(r"^test$", re.IGNORECASE),
    re.compile(r"^dummy$", re.IGNORECASE),
    re.compile(r"^fake$", re.IGNORECASE),
    re.compile(r"^mock$", re.IGNORECASE),
    re.compile(r"^placeholder$", re.IGNORECASE),
    re.compile(r"^x{3,}$", re.IGNORECASE),
    re.compile(r"^\*{3,}$"),
    re.compile(r"^todo$", re.IGNORECASE),
    re.compile(r"^fixme$", re.IGNORECASE),
    re.compile(r"^tbd$", re.IGNORECASE),
    re.compile(r"^none$", re.IGNORECASE),
    re.compile(r"^null$", re.IGNORECASE),
    re.compile(r"^undefined$", re.IGNORECASE),
    re.compile(r"^\$\{.+\}$"),
    re.compile(r"^\{\{.+\}\}$"),
    re.compile(r"^<[^>]+>$"),
]

# Files/dirs to always skip
IGNORE_PATTERNS: List[str] = [
    "*/node_modules/*",
    "*/.venv/*",
    "*/venv/*",
    "*/__pycache__/*",
    "*.min.js",
    "*.min.css",
    "*.map",
    "*/dist/*",
    "*/build/*",
    "*/.git/*",
    "*/archive/*",
    "*/.pytest_cache/*",
]

# Filenames that are always exempt
EXEMPT_FILENAMES: Set[str] = {
    ".env.example",
    ".env.template",
}

# Extensions to scan
SCAN_EXTENSIONS: List[str] = [
    ".py", ".js", ".jsx", ".ts", ".tsx",
    ".json", ".yaml", ".yml", ".toml",
    ".md", ".txt", ".html", ".css",
    ".sh", ".bash", ".ps1", ".cfg", ".ini", ".conf",
]


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def is_public_repo(repo_root: Path) -> bool:
    """Check if repo has a .public-repo marker file."""
    return (repo_root / ".public-repo").exists()


def load_file_set(file_path: Optional[Path]) -> Set[str]:
    """Load a text file into a set of non-empty, non-comment lines."""
    result: Set[str] = set()
    if file_path and file_path.exists():
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    result.add(line)
    return result


def is_binary_file(file_path: Path) -> bool:
    """Detect binary files by checking for null bytes in first 8KB."""
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(8192)
            return b"\x00" in chunk
    except OSError:
        return True


def is_placeholder_value(value: str) -> bool:
    """Check if a matched secret value is an obvious placeholder."""
    for pattern in PLACEHOLDER_PATTERNS:
        if pattern.search(value):
            return True
    return False


def has_inline_allow(line: str) -> bool:
    """Check if line has an inline secret-allow comment."""
    return "# secret-allow" in line or "// secret-allow" in line


def is_file_exempt(file_path: Path) -> bool:
    """Check if file is exempt by name."""
    return file_path.name in EXEMPT_FILENAMES


def is_line_allowlisted(
    file_path: Path, line_num: int, allowlist: Set[str]
) -> bool:
    """Check if a specific file or file:line is in the allowlist."""
    file_str = str(file_path).replace("\\", "/")
    for entry in allowlist:
        if ":" in entry:
            allowed_file, allowed_line = entry.rsplit(":", 1)
            if (file_str.endswith(allowed_file) or allowed_file in file_str):
                if allowed_line.isdigit() and int(allowed_line) == line_num:
                    return True
        else:
            if file_str.endswith(entry) or entry in file_str:
                return True
    return False


_GENERIC_VALUE_RE = re.compile(
    r"(?i)(?:password|passwd|secret|token|api_?key|auth_?key|credential|seller_id|account_id"
    r"|(?:DB|DATABASE)_(?:PASSWORD|PASS|PWD|SECRET))"
    r"\s*[=:]\s*['\"]?([^\s'\"]+)"
)


def extract_generic_secret_value(line: str) -> Optional[str]:
    """Extract the value portion from a generic secret assignment for placeholder checking."""
    match = _GENERIC_VALUE_RE.search(line)
    if match:
        return match.group(1)
    return None


def scan_line(
    line: str,
    line_num: int,
    file_path: Path,
    blocklist: Set[str],
    allowlist: Set[str],
) -> List[Finding]:
    """Scan a single line for all secret patterns. Returns findings."""
    findings: List[Finding] = []
    stripped = line.strip()

    if not stripped:
        return findings

    if has_inline_allow(line):
        return findings

    if is_line_allowlisted(file_path, line_num, allowlist):
        return findings

    # PLATFORM_TOKEN — highest confidence, check first
    for pat in PLATFORM_TOKEN_PATTERNS:
        if pat["pattern"].search(line):
            findings.append(Finding(
                line_num=line_num,
                line=stripped,
                category="PLATFORM_TOKEN",
                message=pat["message"],
                fix=pat["fix"],
            ))
            return findings  # One finding per line

    # PRIVATE_KEY
    for pat in PRIVATE_KEY_PATTERNS:
        if pat["pattern"].search(line):
            findings.append(Finding(
                line_num=line_num,
                line=stripped,
                category="PRIVATE_KEY",
                message=pat["message"],
                fix=pat["fix"],
            ))
            return findings

    # GENERIC_SECRET — with placeholder filtering
    for pat in GENERIC_SECRET_PATTERNS:
        if pat["pattern"].search(line):
            value = extract_generic_secret_value(line)
            if value and is_placeholder_value(value):
                continue
            findings.append(Finding(
                line_num=line_num,
                line=stripped,
                category="GENERIC_SECRET",
                message=pat["message"],
                fix=pat["fix"],
            ))
            return findings

    # PRIVATE_PATH
    for pat in PRIVATE_PATH_PATTERNS:
        if pat["pattern"].search(line):
            findings.append(Finding(
                line_num=line_num,
                line=stripped,
                category="PRIVATE_PATH",
                message=pat["message"],
                fix=pat["fix"],
            ))
            return findings

    # BLOCKLIST — case-insensitive substring match
    line_lower = line.lower()
    for term in blocklist:
        if term.lower() in line_lower:
            findings.append(Finding(
                line_num=line_num,
                line=stripped,
                category="BLOCKLIST",
                message=f"Blocked term from .secret-blocklist: {term}",
                fix="Remove business identifier or add to .secret-allowlist if intentional",
            ))
            return findings

    return findings


def scan_file(
    file_path: Path,
    blocklist: Set[str],
    allowlist: Set[str],
) -> List[Finding]:
    """Scan a single file for secrets. Returns all findings."""
    findings: List[Finding] = []

    if is_file_exempt(file_path):
        return findings

    if is_binary_file(file_path):
        return findings

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line_num, line in enumerate(f, start=1):
                line_findings = scan_line(line, line_num, file_path, blocklist, allowlist)
                findings.extend(line_findings)
    except OSError as e:
        print(f"Warning: Could not read {file_path}: {e}", file=sys.stderr)

    return findings


def get_staged_files_filtered() -> List[str]:
    """Get staged files with --diff-filter=ACM to exclude deleted files."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        capture_output=True, text=True, check=True,
    )
    return [f for f in result.stdout.strip().split("\n") if f]


def report_findings(
    all_findings: Dict[Path, List[Finding]],
    scan_root: Path,
) -> int:
    """Print findings report and return total count."""
    total = sum(len(f) for f in all_findings.values())

    print()
    print("=" * 65)
    print("  SECRET DETECTION — BLOCKED (check-public-repo-secrets.py)")
    print("=" * 65)
    print()

    for file_path in sorted(all_findings.keys()):
        findings = all_findings[file_path]
        try:
            rel_path = file_path.relative_to(scan_root)
        except ValueError:
            rel_path = file_path

        for finding in findings:
            display_line = finding.line[:80] + ("..." if len(finding.line) > 80 else "")
            print(f"[{finding.category}] {finding.message}")
            print(f"  File: {rel_path}")
            print(f"  Line {finding.line_num}: {display_line}")
            print(f"  Fix: {finding.fix}")
            print()

    print("-" * 65)
    print(f"  {total} violation(s) found. Commit blocked.")
    print("  To suppress a false positive:")
    print("    - Add file:line to .secret-allowlist")
    print("    - Add inline comment: # secret-allow")
    print("-" * 65)
    print()

    return total


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def scan_text_content(
    text: str,
    source_label: str,
    blocklist: Set[str],
    allowlist: Set[str],
) -> List[Finding]:
    """Scan arbitrary text content (issue body, commit message, etc.) line-by-line."""
    findings: List[Finding] = []
    synthetic_path = Path(source_label)
    for line_num, line in enumerate(text.splitlines(), start=1):
        line_findings = scan_line(line, line_num, synthetic_path, blocklist, allowlist)
        findings.extend(line_findings)
    return findings


def fetch_issue_or_pr_body(repo: str, number: int) -> str:
    """Fetch issue or PR body + comments via gh CLI. Returns concatenated text."""
    result = subprocess.run(
        ["gh", "api", f"repos/{repo}/issues/{number}"],
        capture_output=True, text=True, check=True,
    )
    import json as _json
    issue = _json.loads(result.stdout)
    parts = [f"TITLE: {issue.get('title', '')}", f"BODY:\n{issue.get('body', '')}"]
    # Also fetch all comments
    comments_result = subprocess.run(
        ["gh", "api", f"repos/{repo}/issues/{number}/comments", "--paginate"],
        capture_output=True, text=True, check=True,
    )
    for comment in _json.loads(comments_result.stdout):
        parts.append(f"COMMENT {comment['id']}:\n{comment.get('body', '')}")
    return "\n\n".join(parts)


def fetch_commit_messages_since(since_sha: str) -> List[tuple[str, str]]:
    """Fetch commit messages from `since_sha` to HEAD. Returns list of (sha, message)."""
    result = subprocess.run(
        ["git", "log", f"{since_sha}..HEAD", "--format=%H%x00%B%x1e"],
        capture_output=True, text=True, check=True,
    )
    commits = []
    for entry in result.stdout.split("\x1e"):
        entry = entry.strip()
        if not entry:
            continue
        sha, _, body = entry.partition("\x00")
        if sha:
            commits.append((sha.strip(), body.strip()))
    return commits


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Detect secrets and sensitive data in public repos"
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to scan (file or directory). Ignored in --scan-issue-body / --scan-commit-messages modes.",
    )
    parser.add_argument(
        "--staged-only",
        action="store_true",
        help="Only scan git staged files (for pre-commit use)",
    )
    parser.add_argument(
        "--allowlist",
        help="Path to .secret-allowlist file",
    )
    parser.add_argument(
        "--scan-issue-body",
        action="store_true",
        help="Scan issue/PR body + comments via gh API. Requires --issue-number.",
    )
    parser.add_argument(
        "--issue-number",
        type=int,
        help="GitHub issue or PR number for --scan-issue-body mode.",
    )
    parser.add_argument(
        "--repo",
        help="Repository in owner/repo format (default: current repo). Used by --scan-issue-body.",
    )
    parser.add_argument(
        "--scan-commit-messages",
        action="store_true",
        help="Scan commit messages in the range <--since>..HEAD. Never prints matched content to stdout.",
    )
    parser.add_argument(
        "--since",
        help="Starting commit SHA for --scan-commit-messages mode (exclusive).",
    )
    parser.add_argument(
        "--enforce-on-private",
        action="store_true",
        help=(
            "Enforce blocklist scanning even on private repos (no .public-repo marker). "
            "Default behaviour: exit 0 on private repos (no-op). Used by private-repo "
            "pre-commit hooks that want defence-in-depth blocklist enforcement so "
            "literals do not accumulate locally before an accidental public mirror or "
            "fork. Does NOT enable --scan-commit-messages or --scan-issue-body "
            "amplification protections (those remain public-repo-only by design)."
        ),
    )

    args = parser.parse_args()
    start_time = time.monotonic()

    scan_path = Path(args.path)
    if not (args.scan_issue_body or args.scan_commit_messages) and not scan_path.exists():
        print(f"Error: Path does not exist: {args.path}", file=sys.stderr)
        return 1

    # Resolve repo root
    try:
        repo_root = get_repo_root()
    except (SST3UtilError, FileNotFoundError, subprocess.CalledProcessError):
        if args.staged_only:
            print("Error: --staged-only requires a git repository", file=sys.stderr)
            return 1
        repo_root = scan_path.resolve()

    # Public repo check — exit 0 if not public (no-op by design), unless
    # --enforce-on-private is set for private-repo blocklist defence-in-depth.
    # Note: --scan-commit-messages and --scan-issue-body remain public-only
    # because their threat model (GitHub Actions log amplification) does not
    # apply on private repos.
    if not is_public_repo(repo_root):
        if args.enforce_on_private and not (args.scan_commit_messages or args.scan_issue_body):
            pass  # fall through to blocklist scan
        else:
            return 0

    # Load blocklist and allowlist
    blocklist = load_file_set(repo_root / ".secret-blocklist")

    allowlist_path = Path(args.allowlist) if args.allowlist else repo_root / ".secret-allowlist"
    allowlist = load_file_set(allowlist_path)

    # --scan-issue-body mode: fetch issue body + comments, scan text content.
    # Design rule: NEVER print matched content to stdout (would amplify leak
    # publicly via GitHub Actions logs). Print only line numbers + categories.
    if args.scan_issue_body:
        if not args.issue_number:
            print("Error: --scan-issue-body requires --issue-number", file=sys.stderr)
            return 1
        repo = args.repo
        if not repo:
            try:
                r = subprocess.run(
                    ["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"],
                    capture_output=True, text=True, check=True,
                )
                repo = r.stdout.strip()
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                print(f"Error: Could not resolve repo (use --repo): {e}", file=sys.stderr)
                return 1
        try:
            body_text = fetch_issue_or_pr_body(repo, args.issue_number)
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"Error: Could not fetch issue #{args.issue_number}: {e}", file=sys.stderr)
            return 1
        findings = scan_text_content(body_text, f"{repo}#{args.issue_number}", blocklist, allowlist)
        if findings:
            # Print line numbers + categories ONLY; never echo the matched content.
            print(f"FAIL: {len(findings)} secret-blocklist match(es) in {repo}#{args.issue_number}")
            for f in findings:
                print(f"  line {f.line_num} category={f.category}: {f.message}")
            print("Evidence withheld from this log to prevent public amplification.")
            return 1
        print(f"PASS: No secrets detected in {repo}#{args.issue_number}")
        return 0

    # --scan-commit-messages mode: fetch messages in range, scan each one.
    if args.scan_commit_messages:
        if not args.since:
            print("Error: --scan-commit-messages requires --since <sha>", file=sys.stderr)
            return 1
        try:
            commits = fetch_commit_messages_since(args.since)
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"Error: Could not fetch commits since {args.since}: {e}", file=sys.stderr)
            return 1
        total_findings = 0
        for sha, message in commits:
            findings = scan_text_content(message, sha, blocklist, allowlist)
            if findings:
                total_findings += len(findings)
                print(f"FAIL: {len(findings)} secret-blocklist match(es) in commit {sha[:12]}")
                for f in findings:
                    print(f"  line {f.line_num} category={f.category}: {f.message}")
        if total_findings > 0:
            print("Evidence withheld from this log to prevent public amplification.")
            return 1
        print(f"PASS: No secrets detected in {len(commits)} commit message(s) since {args.since[:12]}")
        return 0

    # Collect files to scan
    if args.staged_only:
        try:
            staged = get_staged_files_filtered()
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"Error: Could not get staged files: {e}", file=sys.stderr)
            return 1
        files_to_scan = [repo_root / f for f in staged if Path(f).suffix in SCAN_EXTENSIONS]
    elif scan_path.is_file():
        files_to_scan = [scan_path]
    else:
        files_to_scan = collect_source_files(
            scan_path,
            extensions=SCAN_EXTENSIONS,
            ignore_patterns=IGNORE_PATTERNS,
        )

    # Scan (ignore-path filtering already done by collect_source_files for dir scans;
    # staged-only and single-file paths need it here)
    all_findings: Dict[Path, List[Finding]] = {}
    needs_ignore_check = args.staged_only or scan_path.is_file()
    for file_path in files_to_scan:
        if needs_ignore_check and should_ignore_path(file_path, IGNORE_PATTERNS):
            continue
        findings = scan_file(file_path, blocklist, allowlist)
        if findings:
            all_findings[file_path] = findings

    duration_ms = int((time.monotonic() - start_time) * 1000)

    # Report
    if all_findings:
        total = report_findings(all_findings, scan_path.resolve())
        log_event(
            "check-public-repo-secrets",
            "violations_found",
            level="error",
            files_scanned=len(files_to_scan),
            violations=total,
            duration_ms=duration_ms,
        )
        return 1

    print("PASS: No secrets detected")
    return 0


if __name__ == "__main__":
    sys.exit(main())

# Intentionally buggy shell script for the code-shell-lint fixture.
# (No shebang — fixture file is sourced by the wrapper for linting only,
# never executed directly. Avoids the executable-shebang pre-commit hook.)
# Tests that sst3-code-shell.sh --lint surfaces shellcheck findings.

x=$1
echo $x  # SC2086 — unquoted variable.

if [ "$x" == "foo" ]; then  # SC2034 may also apply to unused variables
    echo "matched"
fi

result=`ls /tmp`  # SC2006 — backtick command substitution
echo $result

# Ralph Plugin Customizations

Custom modifications to the `ralph-loop` plugin for SST3 workflow.

> **WARNING**: Plugin updates will overwrite these changes.
> Re-apply after any plugin update.

## Plugin Location

```
~/.claude/plugins/cache/claude-plugins-official/ralph-loop/{version}/hooks/
├── stop-hook.sh   # Main bash script
├── stop-hook.cmd  # Windows wrapper (REQUIRED on Windows)
└── hooks.json     # Hook configuration
```

## Usage

Ralph is **disabled by default** to avoid slowdown on main agent.

```bash
# Enable ralph (before ralph session)
rm ~/.claude/ralph-disabled

# Disable ralph (after ralph session, or anytime)
touch ~/.claude/ralph-disabled
```

## Customization 1: Kill Switch

**Purpose**: Disable ralph hook without restarting Claude Code.

**Why**: The hook runs globally (user scope) and spawns bash on every stop. This adds overhead even with fast-exit checks.

**Location**: Top of stop-hook.sh (after comments, before anything else)

```bash
# KILL SWITCH: Touch this file to disable ralph loop without restart
# To disable: touch ~/.claude/ralph-disabled
# To enable:  rm ~/.claude/ralph-disabled
if [[ -f "$HOME/.claude/ralph-disabled" ]]; then
  exit 0
fi
```

## Customization 2: Fast Exit (State File Check First)

**Purpose**: Exit immediately if no ralph loop is active.

**Why**: Avoids expensive stdin read and jq parsing when ralph isn't being used.

**Location**: Right after kill switch, before reading stdin

```bash
# FAST EXIT: Check if ralph-loop is active BEFORE any expensive operations
# This file only exists when /ralph-loop command is running.
# Anchor to project dir, NOT cwd — stop-hook.sh runs from wherever Claude Code
# was launched, and a relative path silently fast-exits when cwd != project root
# (causing ralph to never trigger). Use CLAUDE_PROJECT_DIR if available.
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
RALPH_STATE_FILE="$PROJECT_DIR/.claude/ralph-loop.local.md"
if [[ ! -f "$RALPH_STATE_FILE" ]]; then
  # No active loop - exit immediately without reading stdin
  exit 0
fi
```

## Customization 3: Windows .cmd Wrapper (Windows ONLY - NOT needed for WSL/Linux)

**Purpose**: Enable hook execution on Windows where .sh files don't run directly.

**WSL/Linux**: Skip this customization entirely. The stock `hooks.json` pointing to `.sh` works correctly.

**Windows only**: Claude Code on Windows doesn't execute .sh files through bash - it tries to run them directly, which fails silently with "No stderr output" error.

**Files to create**: `stop-hook.cmd` in the hooks folder

```cmd
@echo off
REM Wrapper to run bash script on Windows
"C:\Program Files\Git\bin\bash.exe" "%~dp0stop-hook.sh"
```

**Update hooks.json** to use .cmd:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/stop-hook.cmd"
          }
        ]
      }
    ]
  }
}
```

**Additional .sh fixes**:
1. Convert line endings to LF: `sed -i 's/\r$//' stop-hook.sh`
2. Add PATH export at top: `export PATH="/usr/bin:/bin:$PATH"`

**Reference**: [GitHub Issue #16560](https://github.com/anthropics/claude-code/issues/16560)

## Customization 4: Standards.md Reminder + Violation Checklist

**Purpose**: Each iteration reminds Claude to check implementation against standards.md and common violations.

**Location**: SYSTEM_MSG construction (~line 159-163 in stock plugin)

**Stock**:
```bash
SYSTEM_MSG="🔄 Ralph iteration $NEXT_ITERATION | To stop: output <promise>$COMPLETION_PROMISE</promise> ..."
```

**Customized**:
```bash
SYSTEM_MSG="🔄 Ralph iteration $NEXT_ITERATION | Check: STANDARDS.md (fallbacks, hardcoding, overengineering, reuse, modularity) | To stop: output <promise>$COMPLETION_PROMISE</promise> ..."
```

**Violation categories**:
- **fallbacks**: Silent failures hiding errors (Fail Fast principle)
- **hardcoding**: Magic numbers/strings not in config (No Hardcoded Settings)
- **overengineering**: Complexity beyond scope (JBGE principle)
- **reuse**: Duplicated existing code instead of using it (Use Existing Before Building)
- **modularity**: Monolithic design instead of reusable components (Single Responsibility, Clear Interfaces)

## Re-applying Customizations

After plugin update:

**All platforms (WSL/Linux/macOS/Windows)**:
1. Open stop-hook.sh at the plugin location
2. Add kill switch check at top (Customization 1)
3. Move state file check before stdin read (Customization 2)
4. Add violations list to SYSTEM_MSG (Customization 4)
5. Create disable file: `touch ~/.claude/ralph-disabled`

**Windows only** (skip on WSL/Linux/macOS):
6. Create stop-hook.cmd wrapper (Customization 3)
7. Update hooks.json to use .cmd
8. Convert line endings to LF

**Final step**:
9. Restart Claude Code

## Version History

| Date | Change |
|------|--------|
| 2026-01-18 | Added WSL note (Customization 3 not needed), expanded Customization 4 with 5 violation categories (fallbacks, hardcoding, overengineering, reuse, modularity) |
| 2026-01-16 | Added Windows .cmd wrapper fix (Customization 3), removed subagent-only restriction (Ralph runs on ALL agents) |
| 2026-01-09 | Added kill switch, fast-exit, updated subagent detection to use transcript path |
| 2026-01-09 | Initial documentation of subagent-only and standards.md customizations |

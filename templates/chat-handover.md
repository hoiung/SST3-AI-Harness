**⚠️ READ IN FULL - DO NOT SKIP SECTIONS ⚠️**
**This template contains critical sections that must be completed in order. Selective completion causes template failures.**

# Session Handover Template

Emergency-only. Use when context hits 80% of the model window (800K for 1M, 160K for Haiku). Do NOT use routinely. Phase checkpoints post to the Issue and keep working — see STANDARDS.md "Keep Going Until Done".

## Critical: Two-Step Process

**NEVER skip Step 1. It's your insurance against context loss.**

### Step 0: Pre-Handover Cleanup (30 seconds)
- [ ] Delete temp files created during session
- [ ] Clean up failed experiment artifacts
- [ ] **Verify no uncommitted debug code** (console.log, print, debug flags)
- [ ] Remove abandoned code from failed/rescoped approaches
- [ ] Check git status for unexpected files

See: `../standards/STANDARDS.md` (File Housekeeping) for guidance.

**Quality First Reminder**: Comprehensive handover prevents context loss. Include more context than seems necessary (clarity over brevity).

---

### Step 1: Post Checkpoint to Issue (FIRST)

Before generating any handover message, post a checkpoint to the current Issue as a comment.

**Why**: If context dies unexpectedly, the Issue checkpoint is the only recovery point. Without it, all progress is lost.

**Post to current Issue**:
```
## Session Checkpoint - [Timestamp]

**Current Stage**: [Stage X: Name]

**Progress Summary**:
- X of Y items complete
- Current task: [what you're doing right now]
- Status: [on track / blocked / needs decision]

**Completed This Session**:
- [x] Task 1 (with brief result)
- [x] Task 2 (with brief result)
- [ ] Task 3 (in progress)

**Next Steps** (in order):
1. [Immediate next action]
2. [Following action]
3. [Then this]

**Key Decisions Made**:
- Decision 1: [what and why]
- Decision 2: [what and why]

**Blockers/Issues**:
- [Any blockers or problems encountered]
- [Or "None" if clear]

**Files Modified**:
- path/to/file1.ext (added X function, modified Y)
- path/to/file2.ext (refactored Z, fixed bug in W)

**Token Usage**: X / {model_window} (Y% used)

**Context for Next Session**:
[Any important context that isn't obvious from the above]
```

### Step 2: Generate Handover (AFTER Step 1)

Only after posting the checkpoint to the Issue, create the handover message for the user.

**For User** (copy/paste to new chat):
```
📋 COPY THIS TO NEW CHAT:

IMPORTANT: Read ../workflow/WORKFLOW.md and {repository-name}/CLAUDE.md (replace {repository-name} with repo root of the github issue you're working on) before starting.

🎯 YOUR ROLE: Follow the 5-stage Solo workflow
- Subagents for research/explore/audit/verify/review (Sonnet/Haiku for reads, Opus for main)
- Main agent collates findings and implements directly
- Read ../workflow/WORKFLOW.md for the 5-stage process
- Post phase completion to Issue after each phase

**IMPORTANT**: You start in PLAN MODE by default. Do NOT execute unless user provides explicit trigger ("work on #X", "implement", "autonomously").

Continue work on Issue #X: [title]
Status: Stage Y - [status description]

Context:
- Issue: https://github.com/[owner]/[repo]/issues/X
- **READ ENTIRE Issue thread** (body + all comments) to get full context
- Latest comment has checkpoint with current progress
- [Any critical context note]

Workflow:
- Follow ../workflow/WORKFLOW.md (5-stage process: Stages 1-5)
- This is [description of work type]
- [Any special notes]

Repository: [Full path or relative from DevProjects/]

Next: ORCHESTRATE [specific first action] (launch appropriate subagent)

---
That's it! The checkpoint in Issue #X has all details.
```

## Format Details

### Checkpoint Post (Step 1)

**Current Stage**:
- Format: "Stage X: Name" (e.g., "Stage 3: Implementation")
- Include substage if relevant (e.g., "Stage 3.2: Unit Tests")

**Progress Summary**:
- Quantify progress (X of Y tasks, N% complete)
- State current task in present continuous (e.g., "implementing login validation")
- Set expectations: on track / blocked / needs decision

**Completed This Session**:
- Use checkboxes for visual clarity
- Include outcome, not just action (e.g., "Added login validation (20 tests pass)")
- Keep it brief but informative

**Next Steps**:
- Numbered list in priority order (3-5 steps minimum)
- Start with immediate next action
- Be specific enough that new session can start immediately

**Key Decisions Made**:
- Document approach choices with rationale (e.g., "Used React Context instead of Redux for simpler state")
- Critical for understanding current implementation

**Blockers/Issues**:
- List anything preventing progress with attempted solutions if any
- If none, explicitly state "None" (don't omit section)

**Files Modified**:
- Full relative paths from repo root with brief description of changes per file

**Token Usage**:
- Exact numbers (e.g., "650,000 / 1,000,000 (65% used)" for Opus/Sonnet, "145,000 / 200,000 (72.5% used)" for Haiku)

### Handover Message (Step 2)

**Resume Line**:
- Format: "Resume Issue #X at Stage Y: [Stage Name]"

**Context**:
- 1-2 sentences maximum to orient without re-reading entire Issue

**Current Status**:
- What's complete and what's remaining (briefly)

**Immediate Next Action**:
- Single, specific, actionable task executable without further research
- Examples: "Implement validatePassword() in src/utils/validation.js", "Run test suite and fix failures"

**Important Notes**:
- Critical context affecting next steps, recent decisions, known issues/workarounds

## When to Create Handover

### Automatic Triggers
- Token usage reaches 80% of context limit (800K for 1M, 160K for Haiku) — the actual stop threshold, not a routine pause point
- System warning about approaching token limit

### Manual Triggers
- Before starting complex or risky operations
- Before long breaks (end of day, etc.)
- User explicitly requests handover
- Before switching to different Issue/task

### Proactive Handovers
Create handovers before critical operations:
- Large refactors
- Database migrations
- Major architectural changes
- Operations with risk of context loss

## Recovery If Context Lost

If session dies before posting checkpoint:

1. **Read Issue History**:
   - Review all comments and updates
   - Identify last known state
   - Look for partial progress indicators

2. **Check Git Log**:
   - `git log -5 --oneline` to see recent commits
   - `git diff` to see uncommitted changes
   - `git status` to see modified files

3. **Review Modified Files**:
   - Use git diff to understand changes
   - Look for TODO comments or work-in-progress markers
   - Check test files for clues about implementation

4. **Reconstruct State**:
   - Post reconstruction to Issue as new checkpoint
   - Note that this is recovery from lost context
   - Continue from best-known state

5. **Prevent Future Loss**:
   - Post checkpoint immediately
   - Consider more frequent checkpoints for complex work

## Best Practices

### Timing
- Post checkpoints early and often
- Don't wait until token limit
- Post before any risky operation
- Post at natural breakpoints (end of stage, etc.)

### Clarity
- Be specific, not vague
- Use exact file paths
- Include concrete next steps
- Document the "why" for decisions

### Completeness
- Don't skip sections
- If section doesn't apply, state "None" or "N/A"
- Include context that future you needs

### Issue Updates
- Checkpoints go in Issue comments, not Issue body
- Keep Issue body for original requirements/acceptance criteria
- Use comments for progress updates

## Examples

### Example 1: Mid-Implementation Handover
```
## Session Checkpoint - 2025-11-07 14:30

**Current Stage**: Stage 3: Implementation

**Progress Summary**:
- 3 of 5 components complete
- Current task: implementing UserProfile component
- Status: on track

**Completed This Session**:
- [x] LoginForm component (validation working, 15 tests pass)
- [x] PasswordReset component (email integration tested)
- [x] ThemeToggle component (localStorage persistence works)
- [ ] UserProfile component (50% complete)

**Next Steps**:
1. Finish UserProfile component (add avatar upload)
2. Write unit tests for UserProfile
3. Add ProfileSettings component
4. Add AccountDeletion component
5. Complete Stage 3 by running full test suite

**Key Decisions Made**:
- Using React Hook Form for all forms (reduces boilerplate, better validation)
- Avatar upload to S3 with presigned URLs (more secure than direct upload)
- Profile data cached in React Query (reduces API calls)

**Blockers/Issues**:
- Avatar upload needs S3 bucket configuration (staging environment)
- Waiting for design team feedback on ProfileSettings layout

**Files Modified**:
- src/components/auth/LoginForm.jsx (complete with validation)
- src/components/auth/PasswordReset.jsx (complete with email)
- src/components/settings/ThemeToggle.jsx (complete with persistence)
- src/components/profile/UserProfile.jsx (partial - needs avatar upload)

**Token Usage**: 650,000 / 1,000,000 (65% used)

**Context for Next Session**:
ThemeToggle uses CSS variables defined in src/styles/themes.css. UserProfile avatar upload should follow same pattern as LoginForm for file validation.
```

**Handover Message**:
```
Resume Issue #87 at Stage 3: Implementation

**Context**: Adding user profile management features including login, password reset, theme toggle, and profile editing.

**Current Status**: 3 of 5 components complete. LoginForm, PasswordReset, and ThemeToggle are done with tests. UserProfile and ProfileSettings remaining.

**Immediate Next Action**: Complete UserProfile component by implementing avatar upload to S3 (follow S3 presigned URL pattern, see PasswordReset for file handling example).

**Important Notes**: Using React Hook Form for all forms. Avatar upload blocked on staging S3 bucket config. Design feedback pending for ProfileSettings.

**Full Checkpoint**: See Issue #87 latest comment for complete session checkpoint
```

## Common Mistakes to Avoid

**DON'T:**
- ❌ Generate user handover FIRST (Step 1 must be Issue checkpoint)
- ❌ Skip Issue checkpoint because "it's obvious"
- ❌ Forget the "🎯 YOUR ROLE: Follow the 5-stage Solo workflow" line
- ❌ Link to wrong Issue number or forget GitHub URL
- ❌ Make handover too long (keep under 20 lines)
- ❌ Forget to specify which subagent to launch
- ❌ Tell next session to "read latest comment only" (must read ENTIRE Issue)

**DO:**
- ✅ ALWAYS post Issue checkpoint FIRST
- ✅ Include Solo workflow role reminder in handover
- ✅ Include full GitHub Issue URL (https://github.com/[owner]/[repo]/issues/X)
- ✅ Keep user handover concise
- ✅ Specify repository path
- ✅ Reference SST3 5-stage Solo workflow
- ✅ Tell next session to "READ ENTIRE Issue thread" for full context

## Handover Checklist

Before creating handover:

- [ ] Step 1: Checkpoint posted to Issue (with all sections)
- [ ] Step 2: Handover message created for user
- [ ] Token usage documented
- [ ] Next steps are specific and actionable
- [ ] Key decisions documented with rationale
- [ ] File changes listed with descriptions
- [ ] Any blockers clearly stated
- [ ] Issue number AND GitHub URL included in handover
- [ ] Solo workflow role reminder included

## Notes

- Checkpoints are insurance: post to Issue (persistent), include more context than seems necessary
- SST3 uses 5 stages (1-5) in the Solo workflow model

---
name: deglaze
description: Pre-commit engagement check — asks the human to explain changes in their own words before committing.
---

# Deglaze — Pre-Commit Engagement Check

Guards against approval fatigue ("glazed eyes") by asking the human to demonstrate understanding of the changes before committing. Tone is **supportive partner**, never scolding.

## Process

### 1. Gather the diff

Run `git diff --cached --stat` to get staged changes. If nothing is staged, fall back to `git diff --stat` for unstaged changes. If there are no staged or unstaged changes either, fall back to the last commit using `git show --stat HEAD` (and `git show HEAD` for the full diff). Also read the full diff internally for evaluation.

**When to show the diff:**
- **Last-commit fallback**: Always show the full diff upfront — the commit may not be fresh in the human's memory.
- **Staged/unstaged changes**: Show only the file list initially. If the human asks to see the diff, show it — reading the diff is still engagement.

### 2. Prompt the human

Show only the **list of changed files** (the `--stat` output) and ask:

If reviewing staged/unstaged changes:
> **Before we commit — in your own words, what changed and why?**

If reviewing the last commit (clean working tree):
> **Looking at your last commit — in your own words, what changed and why?**

**STOP. Wait for the human's response.** Do not proceed until they answer.

### 3. Evaluate their response

Compare the human's explanation against the actual diff content. Look for these signals:

- **Vagueness** — Generic phrases like "fixed the thing," "updated code," or "made some changes" with no specifics about *what* or *why*.
- **Parroting** — Restating a previously proposed commit message verbatim rather than demonstrating their own understanding.
- **Missed scope** — They described part of the change but missed a significant piece (e.g., mentioned the new function but not the error handling that was also added, or missed that a test file changed).

A good explanation doesn't need to be long — just specific enough to show they know what's going into the codebase.

### 4. Give feedback

**If understanding is clear:** Brief, warm acknowledgment. Keep it short — one line is fine.

Examples:
- "Solid — you've got a clear picture of this change."
- "Nailed it. Let's commit."
- "That tracks with what I see in the diff."

**If something seems off:** Gently surface what they might want to look at. Be specific about what was missed, but frame it as a helpful nudge, not a correction.

Examples:
- "You covered the main feature well. I'd also note there were changes to `validators.ts` adding input length checks — worth a quick look?"
- "That captures the 'what' — any thoughts on why this approach vs. alternatives?"
- "Close! You mentioned the new test but the production code in `taskService.ts` also changed."

**This is always non-blocking.** After giving feedback, proceed with the commit flow regardless. The goal is awareness, not gatekeeping.

## Rules

- In the last-commit fallback, always show the full diff upfront. For staged/unstaged changes, start with the file list but show the diff if asked — reading the diff is still engagement.
- Never grade or score the response. This is a conversation, not an exam.
- Keep feedback to 1-2 sentences max. Don't lecture.
- If the human gives a great explanation, don't pad your response with unnecessary praise. A brief acknowledgment respects their time.
- If the human explicitly says they want to skip the check (e.g., "just commit"), respect that and proceed without friction.
- This check is about engagement, not perfection. A concise but accurate explanation is ideal.

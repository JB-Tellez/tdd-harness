---
name: auto-tdd
description: Run strict Test-Driven Development autonomously, without a human at each STOP gate. The agent implements code AND plays a simulated developer at every gate via fresh subagents, so the architectural-review discipline survives even with no human in the loop. Use this skill whenever the user asks to "run TDD solo", "autonomous TDD", "TDD without intervention", "auto-tdd", or `/auto-tdd <feature spec or feature file>`. Also triggers when the user wants Claude to take a feature spec (e.g., Gherkin `.feature` files, acceptance criteria, a list of behaviors) and drive it to completion through red-green-refactor with no mid-cycle approvals — leaving a complete decision log for the human to review at the end.
---

# auto-tdd — autonomous TDD with a simulated developer

This is an autonomous variant of the [`tdd`](../tdd/SKILL.md) skill. Same red-green-refactor discipline, same deglaze + commit conventions — but the agent runs the whole feature unattended.

The trick that makes that work: at every gate where the `tdd` skill says "STOP, wait for the human," this skill spawns a **fresh [`tdd-developer`](../../agents/tdd-developer.md) subagent** that plays the developer. The subagent sees only the artifact (failing test, passing code, diff) and the question — never the agent's reasoning. Its response is captured verbatim and acted on.

The developer *persona* — pragmatic, decisive, notices design forks, didn't write the artifact — lives in the [`tdd-developer`](../../agents/tdd-developer.md) agent definition, so it's a single inspectable file rather than boilerplate repeated in every prompt. The per-gate templates below supply only the *task and artifact* for that gate.

## Why a subagent, not the agent itself

The `tdd` skill's RED gate exists because the *shape* of a failing test silently commits the system to architectural decisions — and those commitments are usually invisible to whoever wrote the test. The skill is explicit: the agent must NOT volunteer the list, because then the human never has to notice.

If the same agent that wrote the test tries to also play the human at this gate, it sees through its own test. The architectural-awareness purpose collapses. A fresh `tdd-developer` subagent restores the asymmetry: it didn't write the test, so it has to notice the commitments the same way a human would. (The agent definition states this asymmetry as its first rule, so the persona enforces it even if a prompt forgets to.)

The same logic applies, more loosely, to GREEN (was the implementation actually minimal?), REFACTOR (the human owns this decision, not the implementer), and especially deglaze (can a separate party explain the change in their own words?).

## When to use

- User says "run TDD solo," "autonomous TDD," "TDD without intervention," `/auto-tdd …`
- User hands you a spec (Gherkin `.feature` files, acceptance criteria, a behavior list) and asks you to drive it to completion
- User wants a complete decision log at the end rather than mid-cycle interruptions

## When NOT to use

- A human is actively pairing with you on TDD — use the regular [`tdd`](../tdd/SKILL.md) skill instead, so the human owns each gate themselves
- One-off code change with no spec to drive against — just do the work

## Process

For each behavior in the spec, run the cycle below. Don't batch — finish one behavior end-to-end before starting the next.

### 0. Setup (once per project)

- Read the spec (feature files, acceptance criteria list, etc.). Enumerate the scenarios.
- Detect the project's test runner, framework, and conventions by examining existing test files. Match them.
- Confirm tests run. Confirm git is initialized (commits depend on it).
- Create `DEV_LOG.md` at the project root with a header explaining the format. See "DEV_LOG format" below.
- Use `TodoWrite` (or equivalent) to track one item per scenario. Mark `in_progress` when you start a cycle, `completed` when its commit lands.

### 1. RED — write one failing test

Same rules as the `tdd` skill: write only one test, only as much as is sufficient to fail. Run the suite to confirm it fails.

**Sanity check before invoking the RED gate:** does the test fail on its *assertion*, or in its *Arrange* phase (setup error, missing method needed just to set up the scenario)? If it fails in Arrange, the test is doing double duty — driving two unbuilt behaviors at once. **Split it.** Write a smaller precursor test that drives only the setup-level behavior; let that cycle complete first; then return to the original test. This is the most common autonomous mistake — surface it before you call the gate.

If the test passes immediately (the behavior already exists), don't just skip it. Ask: does the test pin a contract that no existing test guards? If yes, keep it as a regression guard and commit it explicitly as that. If no, delete it and move to the next behavior.

### 2. RED gate — escalate to a developer subagent

Spawn a fresh `tdd-developer` subagent (the [agent definition](../../agents/tdd-developer.md) carries the persona) with the prompt template in `## Subagent prompts → RED gate` below.

Capture the subagent's response verbatim. Append it to `DEV_LOG.md` under this cycle's "Escalation — RED gate" section.

Act on the response:
- **"Proceed to GREEN"** → continue to step 3.
- **"Change the test first, here's how"** → revise the test per the subagent's direction, re-run, then re-invoke the RED gate with the new test. Log both rounds.
- **"No-go" with no clear direction** → escalate to the human. This is a stop condition.

### 3. GREEN — minimal code to pass

Write the minimum production code to pass the one failing test. Run the suite to confirm all tests pass.

### 4. GREEN gate — escalate

Spawn a fresh `tdd-developer` subagent with the `## Subagent prompts → GREEN gate` template. Log verbatim. Act on the response (approve / push back).

### 5. REFACTOR gate — escalate

**Never skip on your own judgment.** The `tdd` skill is explicit: the decision belongs to the human (or, here, the simulated developer). Spawn a fresh `tdd-developer` subagent with the `## Subagent prompts → REFACTOR gate` template.

**Default policy when the subagent is indifferent:** skip refactoring unless duplication or naming is clearly bad. Don't refactor on speculation.

If the subagent proposes a refactor, apply it, re-run the suite, and confirm nothing broke. If a test unexpectedly fails, undo the refactor and try a smaller step (or skip).

### 6. Deglaze gate — escalate

Per the [`deglaze`](../deglaze/SKILL.md) skill: show the subagent only the **list of changed files** (the `git diff --stat` output), and ask it to explain the change in its own words. **Do not summarize, paraphrase, or hint at what changed** — that defeats the check.

Use the `## Subagent prompts → Deglaze gate` template.

The subagent will produce one of three response shapes:
- **Specific and accurate** → log and proceed to commit.
- **Vague or generic** ("updated some code") → surface it in the log; this is signal that the spec-to-code coupling is weak. Proceed anyway (deglaze is non-blocking by design).
- **Wrong about what changed** (named the wrong API shape, wrong method, missed a file) → this is the highest-value signal in the whole skill. The subagent's mental model of what *should have* happened differs from what *did* happen. Show it the actual code with a follow-up subagent call and let it reconcile. Log both rounds. If the actual code is wrong, go back to GREEN.

### 7. Commit

Propose a concise commit message describing the behavior implemented. Pass it to the deglaze subagent (continuing the conversation if helpful) for approval — the subagent may revise. Log the final message and commit.

Mark the scenario complete in the todo tracker.

### 8. Repeat

Return to step 1 for the next scenario. Continue until all acceptance criteria pass.

## Stop conditions

Stop and escalate to the human if:

1. **All acceptance criteria pass.** Report what shipped and where the log lives.
2. **A subagent says "no-go, change the test first"** with no actionable direction — you need the human to weigh in on design intent.
3. **Hard error after refactor** — tests fail and reverting the refactor doesn't restore green. Don't try to patch around it; surface the state.
4. **Persistent oversized tests** — if every attempt at the next scenario fails in Arrange and the precursor-split doesn't converge in 2–3 tries, the spec might be malformed or the existing API can't support it without bigger design work. Escalate.

## DEV_LOG format

**Why a DEV_LOG when git already records history?** Because the two capture
different things, and the split is deliberate:

- **git owns the *what*** — the verifiable diff of each cycle. Never hand-write
  "what changed" into the DEV_LOG; git records it better (it can't drift from
  the actual code, and it's queryable via `git log`/`git blame`). Duplicating
  it just creates a second record that can lie.
- **DEV_LOG owns the *why*** — the reasoning a commit can't hold: the
  architectural commitments the RED gate surfaced, where the simulated
  developer pushed back, where you fell back to a default, where deglaze
  drifted. A one-line commit subject can't carry this; the DEV_LOG can.

So write the DEV_LOG *per cycle, as you go* (not batched at the end), and keep
it to decisions and escalations — let the diff speak for the code. (For very
long production runs where the DEV_LOG would grow unwieldy, a commit-centric
variant — verbatim gate reviews in commit bodies, DEV_LOG as a thin index — is
a reasonable alternative; the default here keeps everything in the DEV_LOG so a
reviewer can read the run's arc in one file.)

`DEV_LOG.md` at the project root. Append-only. One section per cycle. Header (write once at project setup):

```markdown
# DEV_LOG

Decisions and escalations from an autonomous TDD run (auto-tdd skill).

Format per cycle:
- **Scenario** — the behavior this cycle targets
- **RED** — test path + failure mode
- **Escalations** — each gate's subagent prompt and response, captured verbatim
- **GREEN** — implementation summary
- **REFACTOR** — yes/no + what (if anything)
- **Deglaze** — summary of subagent's explanation; flag drift if any
- **Commit** — final commit message
```

Per-cycle entry (template):

```markdown
## Cycle N — "<scenario title>"

- **Scenario:** <feature file path> — *<scenario name>*
- **RED:** `<test path>::<test name>` — fails with `<error>`

### Escalation — RED gate (architectural review)

**Issue raised to developer:** <the prompt's core question>

**Developer response (verbatim):**

> <the subagent's full response, indented as blockquote>

- **GREEN:** <one-line summary of impl change>. Tests: <N passed>.
- **REFACTOR:** <skipped, or what was done and why>.
- **Deglaze:** <one line — accurate / drifted / corrected after peek>.
- **Commit:** `<final message>`
```

**Critical rule: log every escalation verbatim.** Don't summarize the subagent's response — paste it as a blockquote. The whole point of this skill is that the human can review *what the simulated developer actually said* at the end, not your paraphrase of it.

When the developer's response is long (cycle-4-introducing-a-collection-style review), it's OK to condense in the log body but **only** if the full text is preserved somewhere recoverable (a commit's body, an appendix file). Note explicitly in the log when you've condensed.

## Subagent prompts

These are templates. Fill in the bracketed parts before sending. Each prompt must be self-contained — the subagent has NO access to the agent's chat history or prior reasoning.

### RED gate prompt

```
You are at the **RED gate**. An AI agent has just written a single
failing test for <scenario name> and stopped to ask you to identify the
architectural commitments its shape encodes. The agent must NOT volunteer
this list — noticing them is your job (your standing persona covers the
rest).

Scenario from <feature file path>:
```
<paste the scenario>
```

The failing test (`<test path>`):
```<lang>
<paste the test>
```

Current production code (`<source path>`):
```<lang>
<paste relevant current code, or note "module does not exist yet">
```

The test fails with: `<error message>`

Your task as the developer:
1. Look at the test and name the architectural commitments it encodes —
   what design decisions does the shape of this test silently lock in?
2. For each commitment, say whether you accept it or want to change it.
   If you want to change something, say what.
3. End with a clear go/no-go: "proceed to GREEN" or
   "change the test first, here's how".

Keep it concise — a few bullets is fine. You are a thoughtful but
pragmatic developer; you don't over-engineer, but you do notice real
design forks. Skip commitments already accepted in earlier cycles
unless they've shifted — focus on what's new.
```

### GREEN gate prompt

```
You are at the **GREEN gate**. The agent just made the failing test pass
and wants your approval.

Test (just added):
```<lang>
<paste the test>
```

Implementation (the change):
```<lang>
<paste the diff or new code>
```

Test run: <N passed>.

The TDD rule for GREEN is "minimal code to pass the one failing test —
no logic beyond what the failing test requires."

Your task as the developer:
1. Does the implementation honor the GREEN minimalism rule, or did
   the agent add anything speculative?
2. Anything you'd push back on?
3. End with "approve GREEN, proceed to REFACTOR" or
   "change implementation, here's how".

Keep it concise.
```

### REFACTOR gate prompt

```
You are at the **REFACTOR gate**. The agent has just made a single test
pass and is asking you whether to refactor. The decision belongs to you,
not the agent — it must not declare refactoring unnecessary on its own.

Current state:

`<test path>`:
```<lang>
<paste all current tests in this file>
```

`<source path>`:
```<lang>
<paste the full current source>
```

Test run: <N passed>.

Default policy for this autonomous run: skip refactoring unless
duplication or naming is clearly bad. Don't refactor on speculation.

**Any refactoring you'd like to do?**

If yes: propose specific changes that keep all tests green.
If no: say so explicitly — don't hedge.
```

### Deglaze gate prompt

```
You are at the **deglaze gate** — a pre-commit engagement check. The
point is to demonstrate you actually know what's about to be committed,
without the agent telling you what changed first.

The agent is about to commit the following files (showing the list
only — no summary, no diff):

```
<paste `git diff --stat` output>
```

Context you have: <one sentence — what cycle this is, what scenario,
where prior cycles ended. Do NOT describe the change itself.>

**Before we commit — in your own words, what changed and why?**

Be specific. A few sentences, not a paragraph. Don't be vague
("added some code") and don't parrot a previously proposed commit
message.

If you'd like to see the actual diff to verify, say so — reading the
diff is still engagement.
```

If the subagent's first answer is vague or wrong, follow up with:

```
Continuing the deglaze check. You said: "<the inaccurate part>".
The actual implementation:

```<lang>
<paste the actual code>
```

Quick reorient:
1. Now that you see the actual code, are you good with what shipped,
   or any second thoughts?
2. Approve commit message "<proposed message>", or revise?
```

## Default policies for autonomous runs

When the subagent is indifferent or doesn't give clear direction, fall back to these defaults:

- **REFACTOR:** skip unless duplication or naming is clearly bad
- **Toss-up between options A and B:** pick A (first option / first recommendation)
- **Test fails in Arrange, not Assertion:** split into a precursor cycle
- **Test passes without new code:** keep it only if it pins a contract no existing test guards; otherwise delete

Log every time you fall back to a default (which one, why the subagent didn't decide). This is where the human reviewing the log needs the most visibility.

## What this skill is NOT

- **Not a substitute for review.** The human reviews the entire DEV_LOG and the resulting commits at the end. The skill defers feedback to the end, it doesn't eliminate it.
- **Not a way to skip TDD discipline.** It's the same discipline, with a structural workaround for the missing human.
- **Not a fire-and-forget script.** If the subagent escalates "no-go, here's a deeper problem," stop and surface to the human. Don't try to power through.

## Rules

- Always pause for each gate's subagent call — never skip a gate. The skill collapses if you batch.
- One failing test at a time. Never write more than one test before making it pass.
- Each cycle should be small. Prefer many tiny steps over few large ones.
- Run tests after every change.
- Log every escalation verbatim. Paraphrasing erases the signal.
- The subagent's response is the developer's voice. Act on it as if a human said it — including pushback, refusals, and corrections.

---
name: tdd
description: Implement a feature or fix using strict Test-Driven Development (red-green-refactor).
---

# TDD Workflow

Follow the Three Rules of TDD strictly:

1. You shall not write any production code unless it is to make a failing unit test pass.
2. You shall not write any more of a unit test than is sufficient to fail — and not compiling is failing.
3. You shall not write any more production code than is sufficient to pass the one failing unit test.

## Process

For $ARGUMENTS:

1. **Understand** — Clarify what behavior is being requested. **Look first for a `features/` folder with `*.feature` files as the canonical Gherkin spec source.** If no feature files exist, ask the user to clarify. If ambiguous, ask before writing any code.

2. **RED** — Write a single failing test that describes the next small piece of desired behavior.
   - Write only one test. Do not write multiple tests.
   - Run the test suite to confirm it fails.
   - If it passes, the behavior already exists — skip to the next behavior.
   - **Architectural review — elicit, don't explain.** A failing test is not just a behavioral specification; it is an architectural artifact. Its shape silently commits the system to a set of design decisions — what the unit of behavior is, what its collaborators are, where the seams live, what gets injected vs. constructed, what the public signature looks like, what is owned where. When a human writes the test, these commitments are usually intentional. When an AI writes the test, they are usually invisible — and if the AI lists them upfront, the human never has to notice them, which defeats the architectural-awareness purpose of this step. **Do not volunteer the list of commitments.** Instead, show the failing test and prompt the developer to look at it and name the architectural decisions it encodes. Wait for their response. Only if they ask "what decisions?" or request details, then share specific commitments (e.g., "This test assumes `OrderService` collaborates with a `PricingClient` injected via constructor — is that the seam you want?").
   - **STOP. Show the user the failing test and ask them to identify the architectural commitments it encodes. Wait for their response before proceeding.**

3. **GREEN** — Write the minimal production code to make the failing test pass.
   - Do not add logic beyond what the single failing test requires.
   - Run the test suite to confirm all tests pass.
   - **STOP. Show the user the passing code and wait for their approval before proceeding.**

4. **REFACTOR** — The decision to refactor belongs to the human, not to you. Never declare that refactoring is unnecessary or skip this step on your own judgment — even for small or trivial-looking changes. Always pause and ask the human whether they want to refactor.
   - Ask the human: "Any refactoring you'd like to do?" Do not prejudge the answer.
   - If the human identifies something to refactor (or asks you to propose options), suggest improvements that keep all tests green: remove duplication, improve naming, simplify structure.
   - **STOP. Show the user any proposed refactoring and wait for their approval before applying it.** If the user approves, apply the changes and run the test suite to confirm nothing broke. If the user says no refactoring is needed, skip this step — but only after they have said so.
   - The RED-before-GREEN gate hook permits production edits while the suite is green precisely so this step can run; the discipline that a green edit be a behavior-preserving refactor (not new untested code) is the human's to uphold here. If a refactor turns a test red, undo it — behavior changes belong in their own RED cycle.

5. **COMMIT** — Whenever code changes (test or production), commit with a deglaze check:
   - **Deglaze check first**: Before suggesting a commit, perform the deglaze engagement check (see `.claude/skills/deglaze/SKILL.md`). List only the changed file path(s) and ask the human to explain the change in their own words. **Do NOT summarize, describe, paraphrase, or hint at what the change does — doing so defeats the purpose of the check, which is for the human to recall and articulate the change themselves.** After the human responds, evaluate their response and give brief feedback. This is non-blocking — proceed regardless of the response.
   - Then propose a concise commit message describing the behavior that was just implemented.
   - **STOP. Wait for user approval before committing.** If the user approves, create the commit. If the user declines, skip and continue.

6. **Repeat** — Return to step 2 for the next behavior until the feature is complete.

## Rules

- **Always pause after each step (RED, GREEN, REFACTOR) and wait for user approval before moving to the next step.** Never proceed to the next step without explicit user confirmation. This includes after answering questions or giving recommendations — always wait for the user to explicitly say to proceed before writing any code or moving to the next step. Never combine an answer/recommendation with an action in the same response.
- **After each step, always state the file path(s) that were changed** so the user can easily browse to them in another terminal to review the code.
- One failing test at a time. Never write more than one test before making it pass.
- Each cycle should be small. Prefer many tiny steps over few large ones.
- Detect the project's existing test runner, framework, and conventions by examining existing test files. Match them.
- Run tests after every change — after writing a failing test, after making it pass, and after refactoring.
- If a test unexpectedly fails during refactoring, undo the refactor and try a smaller step.
- Commit at natural boundaries when the user asks (e.g., after a green-refactor cycle completes a meaningful behavior).

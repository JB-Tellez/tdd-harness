# DEV_LOG

Decisions and escalations from an autonomous TDD run (auto-tdd skill) driving vending machine EARS requirements.

Format per cycle:
- **Scenario** — the behavior this cycle targets
- **RED** — test path + failure mode
- **Escalations** — each gate's subagent prompt and response, captured verbatim
- **GREEN** — implementation summary
- **REFACTOR** — yes/no + what (if anything)
- **Deglaze** — summary of subagent's explanation; flag drift if any
- **Commit** — final commit message

---

## Cycle 1 — "Purchase method precursor"

- **Scenario:** specs/vending-machine.md (Requirement 3, State-Driven) — *precursor*
- **RED:** `tests/test_vending_machine_properties.py::TestRequirement3PurchaseMethod::test_purchase_method_exists` — fails with `AttributeError: 'VendingMachine' object has no attribute 'purchase'`

### Escalation — RED gate (architectural review)

**Issue raised to developer:** Identify architectural commitments in the test shape.

**Developer response (verbatim):**

> ## Review
>
> This test locks in four key architectural commitments:
>
> **1. Purchase method signature: `purchase(slot_id: str) -> bool`**
> The test calls `machine.purchase("D4")` and asserts the result is a bool. This commits us to a method that takes a slot identifier and returns a boolean. The bool likely signals success/failure of the transaction.
>
> **2. Purchase is a state-mutating operation on the machine itself**
> The test inserts coins into the machine, then calls purchase on a slot. It's not passing the balance or the price as arguments — it's relying on the machine's internal state (`self.balance` and `self.slots`). This means purchase owns the logic for comparing balance against price and mutating both balance and stock.
>
> **3. At this stage, we're testing existence and return type only — not behavior**
> The test doesn't validate:
> - Whether balance actually changed
> - Whether the item was "dispensed" (no model yet for what that means)
> - Whether change was returned
> - Whether the purchase succeeded or failed
>
> This is a thin test — it's just establishing the method exists and returns a bool. That's fine for RED; the actual transaction logic comes in subsequent tests.
>
> **4. The machine tracks stock count implicitly**
> The test calls `stock_slot()` but doesn't pass a quantity — only slot, name, and price. Currently the production code only stores price in `self.slots[slot]`. For purchase to later validate "while machine has stock," we'll need to change how stocking works to track quantity, not just price. This test doesn't exercise that yet, but Requirement 3's "while machine has stock" precondition will.
>
> **My assessment:**
>
> Commitments 1, 2, and 3 are solid for a RED test — they establish the method signature and return type without over-specifying behavior yet. Commitment 4 is a future tension (stocking doesn't track quantity), but that's not this test's problem; a later test will expose it.
>
> **Proceed to GREEN.** The test is well-shaped for establishing the method contract. Write `purchase()` to take a slot and return a bool (any bool is fine for now).

- **GREEN:** Stubbed `purchase(slot: str) -> bool` returning `True`. Tests: 6 passed.
- **REFACTOR:** Skipped. No duplication or naming issues.
- **Deglaze:** Accurate. Subagent correctly identified precursor test, method stub, and rationale.
- **Commit:** `Add precursor test for purchase method (EARS Req 3)`

---

## Cycle 2 — "Purchase success with sufficient funds"

- **Scenario:** specs/vending-machine.md (Requirement 3, State-Driven) — *happy path*
- **RED:** `tests/test_vending_machine_properties.py::TestRequirement3PurchaseMethod::test_purchase_succeeds_and_clears_balance_when_sufficient_funds` — fails with `AssertionError: assert 1 == 0` (balance not cleared)

### Escalation — RED gate (architectural review)

**Issue raised to developer:** Identify architectural commitments in the test shape.

**Developer response (verbatim):**

> **Architectural Commitments:**
>
> 1. **`purchase()` returns `True` on success (not just a bool, but specifically `True`)** — The test asserts `result is True`, not just `isinstance(result, bool)`. This locks in that success is distinct from failure, and that we're using a boolean return type rather than an exception or different sentinel. Accepted.
>
> 2. **`purchase()` has a side effect: it mutates the machine's balance to 0** — The test observes `machine.balance == 0` after a successful purchase. This locks in that balance clearing is the purchase method's responsibility, not delegated elsewhere. The spec says "return the exact change" but doesn't say *how* — this test chooses to represent it as balance clearing. Accepted, and it's sensible; change is implicit in a balance of zero.
>
> 3. **`purchase()` is conditional: it only executes the assertion when `total >= price`** — The test wraps the purchase call in `if total >= price:`. This is a guard, not a test of the method's behavior. The method itself doesn't validate; the test just doesn't call it when preconditions fail. This is fine and doesn't constrain the implementation — the method can (and should) validate internally.
>
> 4. **One happy path only** — The test covers only the "sufficient funds" scenario. It doesn't test insufficient funds (Req 4.1), zero stock (Req 4.2), or the return value when those fail. This is intentional for this cycle. Accepted.
>
> **Verdict: proceed to GREEN.** The test is well-shaped. It's tightly scoped to the happy path of Requirement 3, and its commitments are reasonable: return True on success, clear the balance to represent exact change. The implementation now needs to check if balance >= price, clear the balance, and return True.

- **GREEN:** Implemented `purchase()` to validate slot exists, check balance >= price, clear balance on success. Tests: 7 passed.
- **REFACTOR:** Skipped. Code is minimal, no duplication. Note: test uses `if` guard instead of `hypothesis.assume()`, which is weak test design, but implementation is minimal given the test as written.
- **Deglaze:** Accurate. Subagent correctly identified the purchase validation logic and balance clearing behavior.
- **Commit:** `Implement purchase logic for sufficient funds (EARS Req 3)`

---

## Status

Cycle 2 complete. Moving to Cycle 3: rejection when insufficient funds (EARS Req 4.1).

Requirements 1, 2.1, 2.1.5, 2.2, 4.3 are complete and passing.
Requirement 3 happy path complete. Still need: insufficient funds rejection (4.1) and zero stock rejection (4.2).

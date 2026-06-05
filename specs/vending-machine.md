# Vending Machine Requirements Specification

This document defines the functional requirements for the core transaction engine using the **EARS (Easy Approach to Requirements Syntax)** framework.

## 1. Ubiquitous Requirements (Universal System Rules)

* The vending machine **shall** display the price of an item when it is selected by a user.
* The vending machine **shall** maintain and display the current session balance at all times.
* Valid coin denominations **shall** be: $0.01 (penny), $0.05 (nickel), $0.10 (dime), $0.25 (quarter).
* The vending machine **shall** support coin storage with the following initial capacity per denomination: 100 quarters, 100 dimes, 100 nickels, 100 pennies.

## 2. Event-Driven Requirements (Trigger Responses)

* **When** a user inserts a valid coin, the vending machine **shall** increment the current session balance by the coin's value and add the coin to machine storage.
* **When** the user presses the cancel button, the vending machine **shall** dispense all coins from the session balance as exact change and reset the balance to zero.
* **When** a user selects an item during an active session, the vending machine **shall** update the displayed price without affecting the current session balance.

## 3. State-Driven Requirements (Contextual Behavior)

* **While** the machine has stock greater than zero for a selected item, **when** a user inserts an amount of money equal to or greater than the item's price and presses purchase, the vending machine **shall** dispense the item, decrement the stock, and dispense change as exact coins.
* **While** dispensing change, the machine **shall** prioritize larger denominations first (quarters before dimes, dimes before nickels, nickels before pennies) to minimize coins returned.
* **While** the machine cannot make exact change due to insufficient coins of required denominations, the vending machine **shall** reject the purchase, retain the session balance, and dispense nothing.

## 4. Unwanted Behavior Requirements (Error & Safety Boundaries)

* **If** a user attempts to purchase an item when the session balance is less than the item's price, **then** the vending machine **shall** reject the purchase, retain the session balance, and dispense nothing.
* **If** a user attempts to purchase an item when the machine has zero stock of that item, **then** the vending machine **shall** reject the purchase, retain the session balance, and dispense nothing.
* **If** a user inserts an invalid or unrecognized coin, **then** the vending machine **shall** immediately reject and eject the coin, leaving the session balance and machine storage unchanged.
* **If** a dispense or coin-return mechanism fails during an active transaction, **then** the vending machine **shall** halt the transaction, preserve the session balance, log the fault, and display an error message to the user.
* **If** the coin storage reaches capacity for any denomination, **then** the vending machine **shall** reject further coin insertions of that denomination until coins are removed during maintenance.
* **If** a user attempts to purchase when no item is selected, **then** the vending machine **shall** reject the purchase and display a prompt to select an item.

## 5. Notes on Change-Making Logic

* Change is always calculated as `session_balance - item_price` and must be returned in exact coins (no paper bills).
* If the machine cannot construct exact change with available coins, the purchase is rejected and the user retains their balance to try a different item.
* The greedy algorithm (largest denominations first) is used to minimize the number of coins returned, improving user experience.

## 6. Notes on Session Lifecycle

* A session begins when a user first inserts a coin.
* A session ends when either: (a) the user completes a purchase, or (b) the user presses cancel.
* Multiple items can be selected during a single session without resetting the balance.
* The balance persists across item selections until the session ends.

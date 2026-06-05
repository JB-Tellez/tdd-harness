# Vending Machine Requirements Specification

This document defines the functional requirements for the core transaction engine using the **EARS (Easy Approach to Requirements Syntax)** framework.

## 1. Ubiquitous Requirements (Universal System Rules)
* The vending machine **shall** display the price of an item when it is selected by a user.

## 2. Event-Driven Requirements (Trigger Responses)
* **When** a user inserts a valid coin, the vending machine **shall** increment the current session balance by the coin's value.
* **When** the user presses the cancel button, the vending machine **shall** return all coins currently held in the session balance and reset the balance to zero.

## 3. State-Driven Requirements (Contextual Behavior)
* **While** the machine has stock of a selected item, **when** a user inserts an amount of money equal to or greater than the item's price and presses purchase, the vending machine **shall** dispense the item and return the exact change.

## 4. Unwanted Behavior Requirements (Error & Safety Boundaries)
* **If** a user attempts to purchase an item when the session balance is less than the item's price, **then** the vending machine **shall** reject the purchase, retain the session balance, and dispense nothing.
* **If** a user attempts to purchase an item when the machine has zero stock, **then** the vending machine **shall** reject the purchase, retain the session balance, and dispense nothing.
* **If** a user inserts an invalid or unrecognized coin, **then** the vending machine **shall** immediately reject and eject the coin, leaving the session balance unchanged.

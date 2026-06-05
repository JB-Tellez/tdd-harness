"""
Property-based tests for vending machine requirements (EARS spec).
"""

import pytest
from hypothesis import given, strategies as st


class TestRequirement1DisplayPrice:
    """
    EARS Requirement 1 (Ubiquitous):
    The vending machine shall display the price of an item when it is selected by a user.
    """

    @given(price=st.integers(min_value=1, max_value=500))
    def test_displays_price_when_slot_selected(self, price):
        """When a slot is selected, the price of the item in that slot is displayed."""
        from vending_machine import VendingMachine

        machine = VendingMachine()
        machine.stock_slot("D4", "Soda", price)

        displayed_price = machine.price("D4")
        assert displayed_price == price


class TestRequirement2_1InsertCoin:
    """
    EARS Requirement 2.1 (Event-Driven):
    When a user inserts a valid coin, the vending machine shall increment
    the current session balance by the coin's value.
    """

    @given(coin=st.sampled_from([1, 5, 10, 25, 50, 100]))
    def test_valid_coin_increments_balance(self, coin):
        """Inserting a valid coin increases balance by coin value."""
        from vending_machine import VendingMachine

        machine = VendingMachine()
        initial_balance = machine.balance

        success = machine.insert_coin(coin)

        assert success is True
        assert machine.balance == initial_balance + coin


class TestRequirement2_1_5MultipleCoins:
    """
    EARS Requirement 2.1.5 (Implicit from 2.1):
    Multiple valid coins inserted sequentially shall accumulate in the balance.
    """

    @given(coins=st.lists(st.sampled_from([1, 5, 10, 25, 50, 100]), min_size=1, max_size=20))
    def test_multiple_coins_accumulate(self, coins):
        """Inserting multiple valid coins accumulates their values."""
        from vending_machine import VendingMachine

        machine = VendingMachine()

        for coin in coins:
            success = machine.insert_coin(coin)
            assert success is True

        assert machine.balance == sum(coins)


class TestRequirement2_2Cancel:
    """
    EARS Requirement 2.2 (Event-Driven):
    When the user presses the cancel button, the vending machine shall return
    all coins currently held in the session balance and reset the balance to zero.
    """

    @given(coins=st.lists(st.sampled_from([1, 5, 10, 25, 50, 100]), min_size=0, max_size=20))
    def test_cancel_returns_all_coins_and_resets_balance(self, coins):
        """Pressing cancel returns all accumulated coins and resets balance to zero."""
        from vending_machine import VendingMachine

        machine = VendingMachine()

        for coin in coins:
            machine.insert_coin(coin)

        refunded = machine.cancel()

        assert refunded == sum(coins)
        assert machine.balance == 0


class TestRequirement4_1InsufficientFunds:
    """
    EARS Requirement 4.1 (Unwanted Behavior):
    If a user attempts to purchase an item when the session balance is less
    than the item's price, then the vending machine shall reject the purchase,
    retain the session balance, and dispense nothing.
    """

    @given(
        coins=st.lists(st.sampled_from([1, 5, 10, 25, 50, 100]), min_size=1, max_size=5),
        price=st.integers(min_value=100, max_value=500)
    )
    def test_purchase_rejected_when_insufficient_funds(self, coins, price):
        """When balance < price, purchase returns False and balance unchanged."""
        from vending_machine import VendingMachine

        machine = VendingMachine()
        machine.stock_slot("D4", "Soda", price)

        total = sum(coins)
        for coin in coins:
            machine.insert_coin(coin)

        if total < price:
            initial_balance = machine.balance
            result = machine.purchase("D4")

            assert result is False
            assert machine.balance == initial_balance


class TestRequirement4_3InvalidCoin:
    """
    EARS Requirement 4.3 (Unwanted Behavior):
    If a user inserts an invalid or unrecognized coin, then the vending machine
    shall immediately reject and eject the coin, leaving the session balance unchanged.
    """

    @given(invalid_coin=st.integers().filter(lambda x: x not in {1, 5, 10, 25, 50, 100}))
    def test_invalid_coin_rejected_balance_unchanged(self, invalid_coin):
        """Inserting an invalid coin is rejected; balance remains unchanged."""
        from vending_machine import VendingMachine

        machine = VendingMachine()
        initial_balance = machine.balance

        success = machine.insert_coin(invalid_coin)

        assert success is False
        assert machine.balance == initial_balance


class TestRequirement3PurchaseMethod:
    """
    EARS Requirement 3 (State-Driven):
    While the machine has stock of a selected item, when a user inserts an amount
    of money equal to or greater than the item's price and presses purchase,
    the vending machine shall dispense the item and return the exact change.

    Precursor cycle: test that purchase() method exists and returns a bool.
    """

    @given(price=st.integers(min_value=1, max_value=500))
    def test_purchase_method_exists(self, price):
        """The purchase method exists and can be called."""
        from vending_machine import VendingMachine

        machine = VendingMachine()
        machine.stock_slot("D4", "Soda", price)
        machine.insert_coin(25)
        machine.insert_coin(25)

        result = machine.purchase("D4")

        assert isinstance(result, bool)

    @given(
        coins=st.lists(st.sampled_from([1, 5, 10, 25, 50, 100]), min_size=1, max_size=10),
        price=st.integers(min_value=1, max_value=500)
    )
    def test_purchase_succeeds_and_clears_balance_when_sufficient_funds(self, coins, price):
        """When balance >= price, purchase returns True and clears the balance (change returned)."""
        from vending_machine import VendingMachine

        machine = VendingMachine()
        machine.stock_slot("D4", "Soda", price)

        total = sum(coins)
        for coin in coins:
            machine.insert_coin(coin)

        if total >= price:
            result = machine.purchase("D4")

            assert result is True
            assert machine.balance == 0

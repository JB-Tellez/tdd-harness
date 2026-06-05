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

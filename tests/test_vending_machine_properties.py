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

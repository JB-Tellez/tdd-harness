from typing import Optional


class VendingMachine:
    def __init__(self):
        self.slots: dict[str, dict[str, int | str]] = {}
        self.balance = 0

    def stock_slot(self, slot: str, name: str, price: int, quantity: int = 1) -> None:
        self.slots[slot] = {"name": name, "price": price, "quantity": quantity}

    def price(self, slot: str) -> Optional[int]:
        slot_data = self.slots.get(slot)
        return slot_data["price"] if slot_data else None

    def name(self, slot: str) -> Optional[str]:
        slot_data = self.slots.get(slot)
        return slot_data["name"] if slot_data else None

    def insert_coin(self, coin_cents: int) -> bool:
        if coin_cents not in {1, 5, 10, 25, 50, 100}:
            return False
        self.balance += coin_cents
        return True

    def cancel(self) -> int:
        refund = self.balance
        self.balance = 0
        return refund

    def purchase(self, slot: str) -> bool:
        slot_data = self.slots.get(slot)
        if slot_data is None:
            return False
        price = slot_data["price"]
        quantity = slot_data["quantity"]
        if quantity == 0 or self.balance < price:
            return False
        self.balance = 0
        return True

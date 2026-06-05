from typing import Optional


class VendingMachine:
    def __init__(self):
        self.slots: dict[str, int] = {}
        self.quantities: dict[str, int] = {}
        self.balance = 0

    def stock_slot(self, slot: str, name: str, price: int, quantity: int = 1) -> None:
        self.slots[slot] = price
        self.quantities[slot] = quantity

    def price(self, slot: str) -> Optional[int]:
        return self.slots.get(slot)

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
        price = self.slots.get(slot)
        quantity = self.quantities.get(slot, 1)
        if price is None or quantity == 0 or self.balance < price:
            return False
        self.balance = 0
        return True

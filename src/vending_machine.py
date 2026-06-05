from typing import Optional


class VendingMachine:
    def __init__(self):
        self.slots: dict[str, int] = {}
        self.balance = 0

    def stock_slot(self, slot: str, name: str, price: int) -> None:
        self.slots[slot] = price

    def price(self, slot: str) -> Optional[int]:
        return self.slots.get(slot)

    def insert_coin(self, coin_cents: int) -> bool:
        if coin_cents not in {1, 5, 10, 25, 50, 100}:
            return False
        self.balance += coin_cents
        return True

from typing import Optional


class VendingMachine:
    def __init__(self):
        self.slots: dict[str, int] = {}

    def stock_slot(self, slot: str, name: str, price: int) -> None:
        self.slots[slot] = price

    def price(self, slot: str) -> Optional[int]:
        return self.slots.get(slot)

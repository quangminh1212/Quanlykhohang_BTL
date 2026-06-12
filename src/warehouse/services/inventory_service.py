"""Dịch vụ nghiệp vụ nhập/xuất kho.

Tương ứng ``CirculationService`` trong thiết kế: điều phối nghiệp vụ nhập/xuất
kho, ủy quyền việc truy cập dữ liệu và xử lý transaction cho
``TransactionRepository``.
"""

from __future__ import annotations

from ..models.transaction import Transaction, TransactionType
from ..repositories.transaction_repository import (
    TransactionRepository,
    InsufficientStockError,
    ProductNotFoundError,
)

# Re-export để tầng UI bắt ngoại lệ thuận tiện.
__all__ = [
    "InventoryService",
    "InsufficientStockError",
    "ProductNotFoundError",
]


class InventoryService:
    """Nghiệp vụ luân chuyển hàng hóa: nhập kho, xuất kho, tra cứu lịch sử."""

    def __init__(self, transaction_repository: TransactionRepository) -> None:
        self._tx = transaction_repository

    # --- Nhập kho ---
    def import_stock(
        self,
        *,
        product_id: int,
        quantity: int,
        unit_price: float,
        partner: str,
        username: str,
        note: str = "",
    ) -> Transaction:
        return self._tx.import_stock(
            product_id=product_id,
            quantity=quantity,
            unit_price=unit_price,
            partner=partner,
            username=username,
            note=note,
        )

    # --- Xuất kho ---
    def export_stock(
        self,
        *,
        product_id: int,
        quantity: int,
        unit_price: float,
        partner: str,
        username: str,
        note: str = "",
    ) -> Transaction:
        return self._tx.export_stock(
            product_id=product_id,
            quantity=quantity,
            unit_price=unit_price,
            partner=partner,
            username=username,
            note=note,
        )

    # --- Lịch sử ---
    def find_all(self, tx_type: str | None = None) -> list[Transaction]:
        return self._tx.find_all(tx_type)

    def find_by_product(self, product_id: int) -> list[Transaction]:
        return self._tx.find_by_product(product_id)

    def find_between(self, start: str, end: str) -> list[Transaction]:
        return self._tx.find_between(start, end)

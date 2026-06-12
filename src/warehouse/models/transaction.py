"""Mô hình giao dịch nhập/xuất kho."""

from __future__ import annotations

from dataclasses import dataclass


class TransactionType:
    """Loại giao dịch kho."""

    IMPORT = "IMPORT"  # Nhập kho
    EXPORT = "EXPORT"  # Xuất kho

    LABELS = {
        IMPORT: "Nhập kho",
        EXPORT: "Xuất kho",
    }

    @classmethod
    def label(cls, t: str) -> str:
        return cls.LABELS.get(t, t)


@dataclass
class Transaction:
    """Đối tượng phiếu nhập/xuất kho."""

    id: int | None = None
    code: str = ""
    type: str = TransactionType.IMPORT
    product_id: int | None = None
    product_name: str = ""
    quantity: int = 0
    unit_price: float = 0.0
    total: float = 0.0
    partner: str = ""
    user_username: str = ""
    transaction_date: str = ""
    note: str = ""

    @property
    def type_label(self) -> str:
        return TransactionType.label(self.type)

    @staticmethod
    def from_row(row) -> "Transaction":
        return Transaction(
            id=row["id"],
            code=row["code"],
            type=row["type"],
            product_id=row["product_id"],
            product_name=row["product_name"],
            quantity=row["quantity"],
            unit_price=row["unit_price"],
            total=row["total"],
            partner=row["partner"],
            user_username=row["user_username"],
            transaction_date=str(row["transaction_date"]),
            note=row["note"],
        )

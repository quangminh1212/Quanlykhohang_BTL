"""Mô hình hàng hóa trong kho."""

from __future__ import annotations

from dataclasses import dataclass


class ProductStatus:
    """Trạng thái hàng hóa."""

    ACTIVE = "ACTIVE"            # Đang kinh doanh
    DISCONTINUED = "DISCONTINUED"  # Ngừng kinh doanh

    LABELS = {
        ACTIVE: "Đang kinh doanh",
        DISCONTINUED: "Ngừng kinh doanh",
    }

    @classmethod
    def label(cls, status: str) -> str:
        return cls.LABELS.get(status, status)


@dataclass
class Product:
    """Đối tượng hàng hóa."""

    id: int | None = None
    sku: str = ""
    name: str = ""
    category: str = ""
    unit: str = "cái"
    quantity: int = 0
    min_quantity: int = 0
    unit_price: float = 0.0
    location: str = ""
    supplier_id: int | None = None
    status: str = ProductStatus.ACTIVE
    supplier_name: str = ""  # Trường suy diễn (join) phục vụ hiển thị

    @property
    def is_low_stock(self) -> bool:
        """Hàng hóa đang dưới ngưỡng tồn kho tối thiểu."""
        return self.quantity <= self.min_quantity

    @property
    def stock_value(self) -> float:
        """Giá trị tồn kho của mặt hàng."""
        return self.quantity * self.unit_price

    @property
    def status_label(self) -> str:
        return ProductStatus.label(self.status)

    @staticmethod
    def from_row(row) -> "Product":
        keys = row.keys()
        return Product(
            id=row["id"],
            sku=row["sku"],
            name=row["name"],
            category=row["category"],
            unit=row["unit"],
            quantity=row["quantity"],
            min_quantity=row["min_quantity"],
            unit_price=row["unit_price"],
            location=row["location"],
            supplier_id=row["supplier_id"],
            status=row["status"],
            supplier_name=row["supplier_name"] if "supplier_name" in keys else "",
        )

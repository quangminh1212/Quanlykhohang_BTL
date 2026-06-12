"""Mô hình nhà cung cấp."""

from __future__ import annotations

from dataclasses import dataclass


class SupplierStatus:
    """Trạng thái nhà cung cấp."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"

    LABELS = {
        ACTIVE: "Đang hợp tác",
        INACTIVE: "Ngừng hợp tác",
    }

    @classmethod
    def label(cls, status: str) -> str:
        return cls.LABELS.get(status, status)


@dataclass
class Supplier:
    """Đối tượng nhà cung cấp."""

    id: int | None = None
    code: str = ""
    name: str = ""
    contact_person: str = ""
    phone: str = ""
    email: str = ""
    address: str = ""
    status: str = SupplierStatus.ACTIVE

    @property
    def status_label(self) -> str:
        return SupplierStatus.label(self.status)

    @staticmethod
    def from_row(row) -> "Supplier":
        return Supplier(
            id=row["id"],
            code=row["code"],
            name=row["name"],
            contact_person=row["contact_person"],
            phone=row["phone"],
            email=row["email"],
            address=row["address"],
            status=row["status"],
        )

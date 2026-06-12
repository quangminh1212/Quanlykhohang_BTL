"""Mô hình người dùng hệ thống."""

from __future__ import annotations

from dataclasses import dataclass


class Role:
    """Hằng số vai trò người dùng."""

    MANAGER = "MANAGER"  # Quản lý kho (toàn quyền)
    STAFF = "STAFF"      # Nhân viên kho (nghiệp vụ nhập/xuất, tra cứu)

    ALL = (MANAGER, STAFF)

    LABELS = {
        MANAGER: "Quản lý kho",
        STAFF: "Nhân viên kho",
    }

    @classmethod
    def label(cls, role: str) -> str:
        return cls.LABELS.get(role, role)


@dataclass
class User:
    """Đối tượng người dùng (nhân viên kho / quản lý kho)."""

    id: int | None = None
    username: str = ""
    password_hash: str = ""
    role: str = Role.STAFF
    full_name: str = ""
    email: str = ""
    department: str = ""
    position: str = ""
    phone: str = ""
    bio: str = ""

    @property
    def is_manager(self) -> bool:
        return self.role == Role.MANAGER

    @property
    def role_label(self) -> str:
        return Role.label(self.role)

    @staticmethod
    def from_row(row) -> "User":
        """Khởi tạo ``User`` từ một dòng kết quả truy vấn (sqlite3.Row)."""
        return User(
            id=row["id"],
            username=row["username"],
            password_hash=row["password_hash"],
            role=row["role"],
            full_name=row["full_name"],
            email=row["email"],
            department=row["department"],
            position=row["position"],
            phone=row["phone"],
            bio=row["bio"] or "",
        )

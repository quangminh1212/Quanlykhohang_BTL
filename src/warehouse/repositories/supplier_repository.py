"""Repository truy cập bảng ``suppliers``."""

from __future__ import annotations

from ..database.database import Database
from ..models.supplier import Supplier


class SupplierRepository:
    """Thực hiện các truy vấn SQL trên bảng ``suppliers``."""

    def __init__(self, database: Database) -> None:
        self._db = database

    def find_all(self) -> list[Supplier]:
        with self._db.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM suppliers ORDER BY name"
            ).fetchall()
            return [Supplier.from_row(r) for r in rows]

    def find_by_id(self, supplier_id: int) -> Supplier | None:
        with self._db.connection() as conn:
            row = conn.execute(
                "SELECT * FROM suppliers WHERE id = ?", (supplier_id,)
            ).fetchone()
            return Supplier.from_row(row) if row else None

    def search(self, keyword: str) -> list[Supplier]:
        like = f"%{keyword.strip()}%"
        with self._db.connection() as conn:
            rows = conn.execute(
                """
                SELECT * FROM suppliers
                 WHERE name LIKE ? OR code LIKE ? OR contact_person LIKE ?
                 ORDER BY name
                """,
                (like, like, like),
            ).fetchall()
            return [Supplier.from_row(r) for r in rows]

    def code_exists(self, code: str, exclude_id: int | None = None) -> bool:
        with self._db.connection() as conn:
            if exclude_id is None:
                row = conn.execute(
                    "SELECT 1 FROM suppliers WHERE code = ?", (code,)
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT 1 FROM suppliers WHERE code = ? AND id <> ?",
                    (code, exclude_id),
                ).fetchone()
            return row is not None

    def insert(self, supplier: Supplier) -> int:
        with self._db.connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO suppliers
                    (code, name, contact_person, phone, email, address, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    supplier.code,
                    supplier.name,
                    supplier.contact_person,
                    supplier.phone,
                    supplier.email,
                    supplier.address,
                    supplier.status,
                ),
            )
            conn.commit()
            return int(cur.lastrowid)

    def update(self, supplier: Supplier) -> None:
        with self._db.connection() as conn:
            conn.execute(
                """
                UPDATE suppliers
                   SET code = ?, name = ?, contact_person = ?, phone = ?,
                       email = ?, address = ?, status = ?
                 WHERE id = ?
                """,
                (
                    supplier.code,
                    supplier.name,
                    supplier.contact_person,
                    supplier.phone,
                    supplier.email,
                    supplier.address,
                    supplier.status,
                    supplier.id,
                ),
            )
            conn.commit()

    def delete_by_id(self, supplier_id: int) -> None:
        with self._db.connection() as conn:
            conn.execute("DELETE FROM suppliers WHERE id = ?", (supplier_id,))
            conn.commit()

    def count(self) -> int:
        with self._db.connection() as conn:
            return int(
                conn.execute("SELECT COUNT(*) AS c FROM suppliers").fetchone()["c"]
            )

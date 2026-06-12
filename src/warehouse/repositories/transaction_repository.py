"""Repository truy cập bảng ``transactions`` và xử lý nhập/xuất kho.

Đây là repository quan trọng nhất vì tác động đồng thời tới hai bảng
(``transactions`` và ``products``). Hai thao tác ``import_stock`` và
``export_stock`` đều được bao trong một giao dịch CSDL (transaction) để bảo
đảm tính toàn vẹn: hoặc cập nhật tồn kho và ghi phiếu thành công cùng lúc,
hoặc hoàn tác (rollback) toàn bộ khi có lỗi.
"""

from __future__ import annotations

from datetime import datetime

from ..database.database import Database
from ..models.transaction import Transaction, TransactionType


class InsufficientStockError(Exception):
    """Ngoại lệ khi xuất kho vượt quá số lượng tồn."""


class ProductNotFoundError(Exception):
    """Ngoại lệ khi không tìm thấy hàng hóa tương ứng."""


class TransactionRepository:
    """Thực hiện truy vấn lịch sử giao dịch và nghiệp vụ nhập/xuất kho."""

    def __init__(self, database: Database) -> None:
        self._db = database

    # ------------------------------------------------------------------
    # Truy vấn lịch sử
    # ------------------------------------------------------------------
    def find_all(self, tx_type: str | None = None) -> list[Transaction]:
        sql = "SELECT * FROM transactions"
        params: tuple = ()
        if tx_type:
            sql += " WHERE type = ?"
            params = (tx_type,)
        sql += " ORDER BY transaction_date DESC, id DESC"
        with self._db.connection() as conn:
            rows = conn.execute(sql, params).fetchall()
            return [Transaction.from_row(r) for r in rows]

    def find_by_product(self, product_id: int) -> list[Transaction]:
        with self._db.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM transactions WHERE product_id = ? "
                "ORDER BY transaction_date DESC, id DESC",
                (product_id,),
            ).fetchall()
            return [Transaction.from_row(r) for r in rows]

    def find_between(self, start: str, end: str) -> list[Transaction]:
        """Lấy giao dịch trong khoảng ngày [start, end] (định dạng YYYY-MM-DD)."""
        with self._db.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM transactions "
                "WHERE date(transaction_date) BETWEEN date(?) AND date(?) "
                "ORDER BY transaction_date DESC, id DESC",
                (start, end),
            ).fetchall()
            return [Transaction.from_row(r) for r in rows]

    # ------------------------------------------------------------------
    # Nghiệp vụ nhập kho
    # ------------------------------------------------------------------
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
        """Nhập kho: tăng tồn kho và ghi phiếu nhập trong cùng một transaction."""
        if quantity <= 0:
            raise ValueError("Số lượng nhập phải lớn hơn 0.")
        if unit_price < 0:
            raise ValueError("Đơn giá không hợp lệ.")

        with self._db.transaction() as conn:
            product = conn.execute(
                "SELECT id, name, quantity FROM products WHERE id = ?",
                (product_id,),
            ).fetchone()
            if product is None:
                raise ProductNotFoundError(
                    f"Không tìm thấy hàng hóa có mã {product_id}."
                )

            conn.execute(
                "UPDATE products SET quantity = quantity + ? WHERE id = ?",
                (quantity, product_id),
            )

            code = self._next_code(conn, TransactionType.IMPORT)
            total = round(quantity * unit_price, 2)
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cur = conn.execute(
                """
                INSERT INTO transactions
                    (code, type, product_id, product_name, quantity, unit_price,
                     total, partner, user_username, transaction_date, note)
                VALUES (?, 'IMPORT', ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    code,
                    product_id,
                    product["name"],
                    quantity,
                    unit_price,
                    total,
                    partner,
                    username,
                    now,
                    note,
                ),
            )
            return Transaction(
                id=int(cur.lastrowid),
                code=code,
                type=TransactionType.IMPORT,
                product_id=product_id,
                product_name=product["name"],
                quantity=quantity,
                unit_price=unit_price,
                total=total,
                partner=partner,
                user_username=username,
                transaction_date=now,
                note=note,
            )

    # ------------------------------------------------------------------
    # Nghiệp vụ xuất kho
    # ------------------------------------------------------------------
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
        """Xuất kho: kiểm tra tồn kho, giảm tồn và ghi phiếu xuất trong cùng transaction."""
        if quantity <= 0:
            raise ValueError("Số lượng xuất phải lớn hơn 0.")
        if unit_price < 0:
            raise ValueError("Đơn giá không hợp lệ.")

        with self._db.transaction() as conn:
            product = conn.execute(
                "SELECT id, name, quantity FROM products WHERE id = ?",
                (product_id,),
            ).fetchone()
            if product is None:
                raise ProductNotFoundError(
                    f"Không tìm thấy hàng hóa có mã {product_id}."
                )

            if product["quantity"] < quantity:
                raise InsufficientStockError(
                    f"Tồn kho không đủ. Hiện còn {product['quantity']}, "
                    f"yêu cầu xuất {quantity}."
                )

            conn.execute(
                "UPDATE products SET quantity = quantity - ? WHERE id = ?",
                (quantity, product_id),
            )

            code = self._next_code(conn, TransactionType.EXPORT)
            total = round(quantity * unit_price, 2)
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cur = conn.execute(
                """
                INSERT INTO transactions
                    (code, type, product_id, product_name, quantity, unit_price,
                     total, partner, user_username, transaction_date, note)
                VALUES (?, 'EXPORT', ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    code,
                    product_id,
                    product["name"],
                    quantity,
                    unit_price,
                    total,
                    partner,
                    username,
                    now,
                    note,
                ),
            )
            return Transaction(
                id=int(cur.lastrowid),
                code=code,
                type=TransactionType.EXPORT,
                product_id=product_id,
                product_name=product["name"],
                quantity=quantity,
                unit_price=unit_price,
                total=total,
                partner=partner,
                user_username=username,
                transaction_date=now,
                note=note,
            )

    # ------------------------------------------------------------------
    # Tiện ích nội bộ và thống kê
    # ------------------------------------------------------------------
    @staticmethod
    def _next_code(conn, tx_type: str) -> str:
        """Sinh mã phiếu dạng PN-YYYYMMDD-#### (nhập) hoặc PX-... (xuất)."""
        prefix = "PN" if tx_type == TransactionType.IMPORT else "PX"
        today = datetime.now().strftime("%Y%m%d")
        like = f"{prefix}-{today}-%"
        row = conn.execute(
            "SELECT COUNT(*) AS c FROM transactions WHERE code LIKE ?", (like,)
        ).fetchone()
        seq = int(row["c"]) + 1
        return f"{prefix}-{today}-{seq:04d}"

    def count(self, tx_type: str | None = None) -> int:
        sql = "SELECT COUNT(*) AS c FROM transactions"
        params: tuple = ()
        if tx_type:
            sql += " WHERE type = ?"
            params = (tx_type,)
        with self._db.connection() as conn:
            return int(conn.execute(sql, params).fetchone()["c"])

    def sum_total(self, tx_type: str, start: str | None = None, end: str | None = None) -> float:
        sql = "SELECT COALESCE(SUM(total), 0) AS v FROM transactions WHERE type = ?"
        params: list[object] = [tx_type]
        if start and end:
            sql += " AND date(transaction_date) BETWEEN date(?) AND date(?)"
            params.extend([start, end])
        with self._db.connection() as conn:
            return float(conn.execute(sql, tuple(params)).fetchone()["v"])

    def top_products(self, tx_type: str, limit: int = 5) -> list[tuple[str, int]]:
        """Trả về danh sách (tên hàng, tổng số lượng) theo loại giao dịch."""
        with self._db.connection() as conn:
            rows = conn.execute(
                """
                SELECT product_name, SUM(quantity) AS q
                  FROM transactions
                 WHERE type = ?
                 GROUP BY product_id, product_name
                 ORDER BY q DESC
                 LIMIT ?
                """,
                (tx_type, limit),
            ).fetchall()
            return [(r["product_name"], int(r["q"])) for r in rows]

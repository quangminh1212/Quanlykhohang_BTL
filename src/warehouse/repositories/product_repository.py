"""Repository truy cập bảng ``products``."""

from __future__ import annotations

from ..database.database import Database
from ..models.product import Product

# Câu lệnh SELECT chuẩn có join sang suppliers để lấy tên nhà cung cấp.
_BASE_SELECT = """
SELECT p.*, COALESCE(s.name, '') AS supplier_name
  FROM products p
  LEFT JOIN suppliers s ON p.supplier_id = s.id
"""


class ProductRepository:
    """Thực hiện các truy vấn SQL trên bảng ``products``."""

    def __init__(self, database: Database) -> None:
        self._db = database

    def find_all(self) -> list[Product]:
        with self._db.connection() as conn:
            rows = conn.execute(_BASE_SELECT + " ORDER BY p.name").fetchall()
            return [Product.from_row(r) for r in rows]

    def find_by_id(self, product_id: int) -> Product | None:
        with self._db.connection() as conn:
            row = conn.execute(
                _BASE_SELECT + " WHERE p.id = ?", (product_id,)
            ).fetchone()
            return Product.from_row(row) if row else None

    def search(self, keyword: str = "", category: str = "") -> list[Product]:
        clauses: list[str] = []
        params: list[object] = []
        if keyword.strip():
            like = f"%{keyword.strip()}%"
            clauses.append("(p.name LIKE ? OR p.sku LIKE ?)")
            params.extend([like, like])
        if category.strip():
            clauses.append("p.category = ?")
            params.append(category.strip())
        sql = _BASE_SELECT
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY p.name"
        with self._db.connection() as conn:
            rows = conn.execute(sql, tuple(params)).fetchall()
            return [Product.from_row(r) for r in rows]

    def find_low_stock(self) -> list[Product]:
        with self._db.connection() as conn:
            rows = conn.execute(
                _BASE_SELECT + " WHERE p.quantity <= p.min_quantity ORDER BY p.quantity"
            ).fetchall()
            return [Product.from_row(r) for r in rows]

    def sku_exists(self, sku: str, exclude_id: int | None = None) -> bool:
        with self._db.connection() as conn:
            if exclude_id is None:
                row = conn.execute(
                    "SELECT 1 FROM products WHERE sku = ?", (sku,)
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT 1 FROM products WHERE sku = ? AND id <> ?",
                    (sku, exclude_id),
                ).fetchone()
            return row is not None

    def insert(self, product: Product) -> int:
        with self._db.connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO products
                    (sku, name, category, unit, quantity, min_quantity,
                     unit_price, location, supplier_id, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    product.sku,
                    product.name,
                    product.category,
                    product.unit,
                    product.quantity,
                    product.min_quantity,
                    product.unit_price,
                    product.location,
                    product.supplier_id,
                    product.status,
                ),
            )
            conn.commit()
            return int(cur.lastrowid)

    def update(self, product: Product) -> None:
        with self._db.connection() as conn:
            conn.execute(
                """
                UPDATE products
                   SET sku = ?, name = ?, category = ?, unit = ?,
                       min_quantity = ?, unit_price = ?, location = ?,
                       supplier_id = ?, status = ?
                 WHERE id = ?
                """,
                (
                    product.sku,
                    product.name,
                    product.category,
                    product.unit,
                    product.min_quantity,
                    product.unit_price,
                    product.location,
                    product.supplier_id,
                    product.status,
                    product.id,
                ),
            )
            conn.commit()

    def delete_by_id(self, product_id: int) -> None:
        with self._db.connection() as conn:
            conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
            conn.commit()

    def distinct_categories(self) -> list[str]:
        with self._db.connection() as conn:
            rows = conn.execute(
                "SELECT DISTINCT category FROM products WHERE category <> '' ORDER BY category"
            ).fetchall()
            return [r["category"] for r in rows]

    # --- Thống kê ---
    def count(self) -> int:
        with self._db.connection() as conn:
            return int(
                conn.execute("SELECT COUNT(*) AS c FROM products").fetchone()["c"]
            )

    def total_stock_value(self) -> float:
        with self._db.connection() as conn:
            row = conn.execute(
                "SELECT COALESCE(SUM(quantity * unit_price), 0) AS v FROM products"
            ).fetchone()
            return float(row["v"])

    def total_quantity(self) -> int:
        with self._db.connection() as conn:
            row = conn.execute(
                "SELECT COALESCE(SUM(quantity), 0) AS q FROM products"
            ).fetchone()
            return int(row["q"])

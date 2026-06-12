"""Dịch vụ thống kê và báo cáo.

Tổng hợp số liệu vận hành kho: tổng quan tồn kho, giá trị tồn, cảnh báo tồn
thấp, thống kê nhập/xuất theo thời gian và kết xuất báo cáo ra tệp CSV.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field

from ..models.transaction import TransactionType
from ..repositories.product_repository import ProductRepository
from ..repositories.supplier_repository import SupplierRepository
from ..repositories.transaction_repository import TransactionRepository


@dataclass
class DashboardSummary:
    """Số liệu tổng quan hiển thị trên màn hình Dashboard."""

    total_products: int = 0
    total_quantity: int = 0
    total_stock_value: float = 0.0
    total_suppliers: int = 0
    low_stock_count: int = 0
    import_count: int = 0
    export_count: int = 0
    low_stock_items: list = field(default_factory=list)


@dataclass
class PeriodReport:
    """Báo cáo nhập/xuất trong một khoảng thời gian."""

    start: str = ""
    end: str = ""
    import_count: int = 0
    export_count: int = 0
    import_value: float = 0.0
    export_value: float = 0.0
    transactions: list = field(default_factory=list)


class ReportService:
    """Nghiệp vụ thống kê và báo cáo."""

    def __init__(
        self,
        product_repository: ProductRepository,
        supplier_repository: SupplierRepository,
        transaction_repository: TransactionRepository,
    ) -> None:
        self._products = product_repository
        self._suppliers = supplier_repository
        self._tx = transaction_repository

    def dashboard_summary(self) -> DashboardSummary:
        low = self._products.find_low_stock()
        return DashboardSummary(
            total_products=self._products.count(),
            total_quantity=self._products.total_quantity(),
            total_stock_value=self._products.total_stock_value(),
            total_suppliers=self._suppliers.count(),
            low_stock_count=len(low),
            import_count=self._tx.count(TransactionType.IMPORT),
            export_count=self._tx.count(TransactionType.EXPORT),
            low_stock_items=low,
        )

    def period_report(self, start: str, end: str) -> PeriodReport:
        txs = self._tx.find_between(start, end)
        import_count = sum(1 for t in txs if t.type == TransactionType.IMPORT)
        export_count = sum(1 for t in txs if t.type == TransactionType.EXPORT)
        import_value = sum(t.total for t in txs if t.type == TransactionType.IMPORT)
        export_value = sum(t.total for t in txs if t.type == TransactionType.EXPORT)
        return PeriodReport(
            start=start,
            end=end,
            import_count=import_count,
            export_count=export_count,
            import_value=round(import_value, 2),
            export_value=round(export_value, 2),
            transactions=txs,
        )

    def top_imported(self, limit: int = 5) -> list[tuple[str, int]]:
        return self._tx.top_products(TransactionType.IMPORT, limit)

    def top_exported(self, limit: int = 5) -> list[tuple[str, int]]:
        return self._tx.top_products(TransactionType.EXPORT, limit)

    # ------------------------------------------------------------------
    # Kết xuất báo cáo
    # ------------------------------------------------------------------
    def export_transactions_csv(self, path: str, start: str, end: str) -> int:
        """Xuất danh sách giao dịch trong khoảng thời gian ra tệp CSV.

        Trả về số dòng giao dịch đã ghi.
        """
        txs = self._tx.find_between(start, end)
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "Mã phiếu",
                    "Loại",
                    "Hàng hóa",
                    "Số lượng",
                    "Đơn giá",
                    "Thành tiền",
                    "Đối tác",
                    "Người thực hiện",
                    "Thời gian",
                    "Ghi chú",
                ]
            )
            for t in txs:
                writer.writerow(
                    [
                        t.code,
                        t.type_label,
                        t.product_name,
                        t.quantity,
                        t.unit_price,
                        t.total,
                        t.partner,
                        t.user_username,
                        t.transaction_date,
                        t.note,
                    ]
                )
        return len(txs)

    def export_inventory_csv(self, path: str) -> int:
        """Xuất danh sách tồn kho hiện tại ra tệp CSV."""
        products = self._products.find_all()
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "SKU",
                    "Tên hàng hóa",
                    "Danh mục",
                    "Đơn vị",
                    "Tồn kho",
                    "Tồn tối thiểu",
                    "Đơn giá",
                    "Giá trị tồn",
                    "Vị trí",
                    "Nhà cung cấp",
                    "Trạng thái",
                ]
            )
            for p in products:
                writer.writerow(
                    [
                        p.sku,
                        p.name,
                        p.category,
                        p.unit,
                        p.quantity,
                        p.min_quantity,
                        p.unit_price,
                        p.stock_value,
                        p.location,
                        p.supplier_name,
                        p.status_label,
                    ]
                )
        return len(products)

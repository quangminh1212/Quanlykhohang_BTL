"""Khởi tạo và gắn kết các thành phần của hệ thống (Composition Root).

Lớp ``AppContext`` đóng vai trò khởi tạo tầng dữ liệu (``initializeDataLayer``
trong thiết kế tham khảo): tạo ``Database`` từ ``DbConfig``, bảo đảm schema,
nạp dữ liệu mẫu lần đầu và khởi tạo toàn bộ repository, service.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from .config.db_config import DbConfig
from .database.database import Database
from .models.product import Product
from .models.supplier import Supplier
from .models.user import Role
from .repositories.product_repository import ProductRepository
from .repositories.supplier_repository import SupplierRepository
from .repositories.transaction_repository import TransactionRepository
from .repositories.user_repository import UserRepository
from .services.account_service import AccountService
from .services.catalog_service import CatalogService
from .services.inventory_service import InventoryService
from .services.report_service import ReportService
from .utils import security


class AppContext:
    """Bộ chứa các dịch vụ và repository của ứng dụng."""

    def __init__(self, config: DbConfig | None = None) -> None:
        self.config = config or DbConfig.load()
        self.database = Database(self.config)
        self.database.ensure_schema()

        # Tầng truy cập dữ liệu
        self.user_repository = UserRepository(self.database)
        self.product_repository = ProductRepository(self.database)
        self.supplier_repository = SupplierRepository(self.database)
        self.transaction_repository = TransactionRepository(self.database)

        # Tầng nghiệp vụ
        self.account_service = AccountService(self.user_repository)
        self.catalog_service = CatalogService(
            self.product_repository, self.supplier_repository
        )
        self.inventory_service = InventoryService(self.transaction_repository)
        self.report_service = ReportService(
            self.product_repository,
            self.supplier_repository,
            self.transaction_repository,
        )

    def close(self) -> None:
        self.database.close()

    # ------------------------------------------------------------------
    # Dữ liệu mẫu
    # ------------------------------------------------------------------
    def seed_sample_data(self) -> None:
        """Nạp dữ liệu mẫu nếu CSDL còn trống.

        Tạo:
        - 2 tài khoản: ``manager``/``123456`` (Quản lý) và ``staff``/``123456``.
        - Một số nhà cung cấp và hàng hóa mẫu.
        - Vài giao dịch nhập/xuất mẫu để minh họa báo cáo.
        """
        if self.user_repository.count() > 0:
            return  # Đã có dữ liệu, không nạp lại.

        # --- Tài khoản ---
        self.user_repository.insert(
            _user("manager", "123456", Role.MANAGER, "Nguyễn Văn Quản",
                  "manager@khohang.vn", "Ban Giám đốc", "Quản lý kho", "0901000001")
        )
        self.user_repository.insert(
            _user("staff", "123456", Role.STAFF, "Trần Thị Nhân",
                  "staff@khohang.vn", "Kho vận", "Nhân viên kho", "0901000002")
        )

        # --- Nhà cung cấp ---
        suppliers = [
            Supplier(code="NCC001", name="Công ty TNHH Thiết bị Điện tử Minh Anh",
                     contact_person="Lê Minh Anh", phone="0281234567",
                     email="sales@minhanh.vn", address="12 Lê Lợi, Q.1, TP.HCM"),
            Supplier(code="NCC002", name="Công ty CP Văn phòng phẩm Hồng Hà",
                     contact_person="Phạm Thu Hà", phone="0247654321",
                     email="kinhdoanh@hongha.vn", address="25 Lý Thường Kiệt, Hà Nội"),
            Supplier(code="NCC003", name="Nhà phân phối Gia dụng Sao Mai",
                     contact_person="Đỗ Văn Sao", phone="0236998877",
                     email="contact@saomai.vn", address="88 Hùng Vương, Đà Nẵng"),
        ]
        supplier_ids = [self.supplier_repository.insert(s) for s in suppliers]

        # --- Hàng hóa ---
        products = [
            Product(sku="SP001", name="Chuột không dây Logitech M331", category="Điện tử",
                    unit="cái", quantity=40, min_quantity=10, unit_price=320000,
                    location="A1-K1", supplier_id=supplier_ids[0]),
            Product(sku="SP002", name="Bàn phím cơ Keychron K2", category="Điện tử",
                    unit="cái", quantity=15, min_quantity=5, unit_price=1850000,
                    location="A1-K2", supplier_id=supplier_ids[0]),
            Product(sku="SP003", name="Giấy in A4 Double A 70gsm", category="Văn phòng phẩm",
                    unit="ram", quantity=8, min_quantity=20, unit_price=68000,
                    location="B2-K1", supplier_id=supplier_ids[1]),
            Product(sku="SP004", name="Bút bi Thiên Long TL-027", category="Văn phòng phẩm",
                    unit="hộp", quantity=120, min_quantity=30, unit_price=45000,
                    location="B2-K2", supplier_id=supplier_ids[1]),
            Product(sku="SP005", name="Bình giữ nhiệt Lock&Lock 500ml", category="Gia dụng",
                    unit="cái", quantity=25, min_quantity=10, unit_price=240000,
                    location="C3-K1", supplier_id=supplier_ids[2]),
            Product(sku="SP006", name="Ổ cắm điện đa năng Điện Quang", category="Gia dụng",
                    unit="cái", quantity=3, min_quantity=8, unit_price=135000,
                    location="C3-K2", supplier_id=supplier_ids[2]),
        ]
        product_ids = [self.product_repository.insert(p) for p in products]

        # --- Một vài giao dịch mẫu (ghi trực tiếp để có ngày trong quá khứ) ---
        self._seed_transactions(products, product_ids, suppliers)

    def _seed_transactions(self, products, product_ids, suppliers) -> None:
        """Tạo vài phiếu nhập/xuất mẫu trong những ngày gần đây."""
        with self.database.connection() as conn:
            base = datetime.now()
            samples = [
                ("IMPORT", 0, 20, products[0].unit_price, suppliers[0].name, "manager", 5),
                ("IMPORT", 2, 50, products[2].unit_price, suppliers[1].name, "staff", 4),
                ("EXPORT", 0, 8, 350000, "Phòng Kinh doanh", "staff", 3),
                ("EXPORT", 3, 25, 50000, "Chi nhánh Hà Nội", "staff", 2),
                ("IMPORT", 4, 10, products[4].unit_price, suppliers[2].name, "manager", 1),
            ]
            counters: dict[str, int] = {}
            for tx_type, idx, qty, price, partner, user, days_ago in samples:
                day = base - timedelta(days=days_ago)
                prefix = "PN" if tx_type == "IMPORT" else "PX"
                date_str = day.strftime("%Y%m%d")
                key = f"{prefix}-{date_str}"
                counters[key] = counters.get(key, 0) + 1
                code = f"{key}-{counters[key]:04d}"
                total = round(qty * price, 2)
                conn.execute(
                    """
                    INSERT INTO transactions
                        (code, type, product_id, product_name, quantity, unit_price,
                         total, partner, user_username, transaction_date, note)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '')
                    """,
                    (
                        code, tx_type, product_ids[idx], products[idx].name, qty,
                        price, total, partner, user,
                        day.strftime("%Y-%m-%d %H:%M:%S"),
                    ),
                )
            conn.commit()


def _user(username, password, role, full_name, email, department, position, phone):
    from .models.user import User
    return User(
        username=username,
        password_hash=security.hash_password(password),
        role=role,
        full_name=full_name,
        email=email,
        department=department,
        position=position,
        phone=phone,
    )

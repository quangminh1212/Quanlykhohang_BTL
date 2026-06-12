"""Kiểm thử các nghiệp vụ chính của hệ thống quản lý kho.

Bộ kiểm thử dùng CSDL SQLite tạm thời (mỗi test một tệp riêng) nên không ảnh
hưởng tới dữ liệu thật. Chạy bằng: ``pytest`` hoặc ``python -m unittest``.
"""

import os
import tempfile
import unittest

from warehouse.config.db_config import DbConfig
from warehouse.app_context import AppContext
from warehouse.models.product import Product
from warehouse.models.supplier import Supplier
from warehouse.models.user import Role
from warehouse.services.auth_service import AuthError
from warehouse.services.catalog_service import CatalogError
from warehouse.repositories.transaction_repository import InsufficientStockError
from warehouse.utils import security


class BaseTest(unittest.TestCase):
    def setUp(self) -> None:
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        os.remove(self.db_path)  # để Database tự tạo mới
        self.ctx = AppContext(DbConfig(db_path=self.db_path))

    def tearDown(self) -> None:
        self.ctx.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)


class SecurityTest(unittest.TestCase):
    def test_hash_and_verify(self):
        h = security.hash_password("matkhau123")
        self.assertTrue(security.verify_password("matkhau123", h))
        self.assertFalse(security.verify_password("sai", h))

    def test_hash_is_salted(self):
        self.assertNotEqual(
            security.hash_password("abc"), security.hash_password("abc")
        )


class AuthTest(BaseTest):
    def test_register_and_login(self):
        self.ctx.account_service.register(
            username="nv01", password="123456", role=Role.STAFF, full_name="Test")
        user = self.ctx.account_service.login("nv01", "123456")
        self.assertEqual(user.username, "nv01")
        self.assertEqual(user.role, Role.STAFF)

    def test_duplicate_username(self):
        self.ctx.account_service.register(username="dup", password="123456")
        with self.assertRaises(AuthError):
            self.ctx.account_service.register(username="dup", password="123456")

    def test_login_wrong_password(self):
        self.ctx.account_service.register(username="u", password="123456")
        with self.assertRaises(AuthError):
            self.ctx.account_service.login("u", "sai")

    def test_change_password(self):
        self.ctx.account_service.register(username="u", password="123456")
        self.ctx.account_service.change_password("u", "123456", "newpass")
        self.assertTrue(self.ctx.account_service.login("u", "newpass"))
        with self.assertRaises(AuthError):
            self.ctx.account_service.change_password("u", "wrong", "x123")


class CatalogTest(BaseTest):
    def _add_product(self, sku="SKU1", qty=10):
        p = Product(sku=sku, name="Sản phẩm", category="Test", quantity=qty,
                    min_quantity=5, unit_price=1000)
        return self.ctx.catalog_service.add_product(p)

    def test_add_product(self):
        p = self._add_product()
        self.assertIsNotNone(p.id)
        self.assertEqual(len(self.ctx.catalog_service.find_all_products()), 1)

    def test_duplicate_sku(self):
        self._add_product(sku="X")
        with self.assertRaises(CatalogError):
            self._add_product(sku="X")

    def test_invalid_product(self):
        with self.assertRaises(CatalogError):
            self.ctx.catalog_service.add_product(Product(sku="", name=""))

    def test_low_stock(self):
        self._add_product(sku="LOW", qty=3)  # min=5 -> low stock
        low = self.ctx.catalog_service.low_stock_products()
        self.assertTrue(any(p.sku == "LOW" for p in low))

    def test_supplier_crud(self):
        s = self.ctx.catalog_service.add_supplier(
            Supplier(code="NCC9", name="NCC Test"))
        self.assertIsNotNone(s.id)
        s.name = "NCC Đổi tên"
        self.ctx.catalog_service.update_supplier(s)
        found = self.ctx.catalog_service.find_supplier(s.id)
        self.assertEqual(found.name, "NCC Đổi tên")


class InventoryTest(BaseTest):
    def setUp(self):
        super().setUp()
        # Tạo người dùng để thỏa ràng buộc khóa ngoại transactions.user_username
        self.ctx.account_service.register(
            username="manager", password="123456", role=Role.MANAGER)
        self.ctx.account_service.register(
            username="staff", password="123456", role=Role.STAFF)
        self.product = self.ctx.catalog_service.add_product(
            Product(sku="P1", name="Mặt hàng", quantity=10, min_quantity=2,
                    unit_price=5000))

    def test_import_increases_stock(self):
        self.ctx.inventory_service.import_stock(
            product_id=self.product.id, quantity=5, unit_price=5000,
            partner="NCC", username="manager")
        p = self.ctx.catalog_service.find_product(self.product.id)
        self.assertEqual(p.quantity, 15)

    def test_export_decreases_stock(self):
        self.ctx.inventory_service.export_stock(
            product_id=self.product.id, quantity=4, unit_price=6000,
            partner="KH", username="staff")
        p = self.ctx.catalog_service.find_product(self.product.id)
        self.assertEqual(p.quantity, 6)

    def test_export_insufficient_stock_rolls_back(self):
        with self.assertRaises(InsufficientStockError):
            self.ctx.inventory_service.export_stock(
                product_id=self.product.id, quantity=999, unit_price=6000,
                partner="KH", username="staff")
        # Tồn kho không đổi do transaction đã rollback
        p = self.ctx.catalog_service.find_product(self.product.id)
        self.assertEqual(p.quantity, 10)
        # Không có phiếu xuất nào được tạo
        self.assertEqual(len(self.ctx.inventory_service.find_all("EXPORT")), 0)

    def test_transaction_code_generated(self):
        tx = self.ctx.inventory_service.import_stock(
            product_id=self.product.id, quantity=1, unit_price=1000,
            partner="NCC", username="manager")
        self.assertTrue(tx.code.startswith("PN-"))

    def test_total_computed(self):
        tx = self.ctx.inventory_service.import_stock(
            product_id=self.product.id, quantity=3, unit_price=2000,
            partner="NCC", username="manager")
        self.assertEqual(tx.total, 6000)


class ReportTest(BaseTest):
    def test_dashboard_summary(self):
        self.ctx.catalog_service.add_product(
            Product(sku="A", name="A", quantity=10, min_quantity=2, unit_price=100))
        summary = self.ctx.report_service.dashboard_summary()
        self.assertEqual(summary.total_products, 1)
        self.assertEqual(summary.total_quantity, 10)
        self.assertEqual(summary.total_stock_value, 1000)


if __name__ == "__main__":
    unittest.main(verbosity=2)

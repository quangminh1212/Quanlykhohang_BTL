"""Dịch vụ quản lý danh mục hàng hóa và nhà cung cấp.

Tương ứng ``CatalogService`` trong thiết kế: chứa logic nghiệp vụ quản lý danh
mục, kiểm tra hợp lệ dữ liệu trước khi ủy quyền cho repository thao tác SQL.
"""

from __future__ import annotations

from ..models.product import Product, ProductStatus
from ..models.supplier import Supplier, SupplierStatus
from ..repositories.product_repository import ProductRepository
from ..repositories.supplier_repository import SupplierRepository


class CatalogError(Exception):
    """Ngoại lệ nghiệp vụ quản lý danh mục."""


class CatalogService:
    """Nghiệp vụ quản lý hàng hóa và nhà cung cấp."""

    def __init__(
        self,
        product_repository: ProductRepository,
        supplier_repository: SupplierRepository,
    ) -> None:
        self._products = product_repository
        self._suppliers = supplier_repository

    # ------------------------------------------------------------------
    # Hàng hóa
    # ------------------------------------------------------------------
    def find_all_products(self) -> list[Product]:
        return self._products.find_all()

    def search_products(self, keyword: str = "", category: str = "") -> list[Product]:
        return self._products.search(keyword, category)

    def find_product(self, product_id: int) -> Product | None:
        return self._products.find_by_id(product_id)

    def low_stock_products(self) -> list[Product]:
        return self._products.find_low_stock()

    def categories(self) -> list[str]:
        return self._products.distinct_categories()

    def add_product(self, product: Product) -> Product:
        self._validate_product(product)
        if self._products.sku_exists(product.sku):
            raise CatalogError(f"Mã SKU '{product.sku}' đã tồn tại.")
        product.id = self._products.insert(product)
        return product

    def update_product(self, product: Product) -> None:
        if product.id is None:
            raise CatalogError("Thiếu định danh hàng hóa cần cập nhật.")
        self._validate_product(product)
        if self._products.sku_exists(product.sku, exclude_id=product.id):
            raise CatalogError(f"Mã SKU '{product.sku}' đã được dùng cho hàng hóa khác.")
        self._products.update(product)

    def delete_product(self, product_id: int) -> None:
        self._products.delete_by_id(product_id)

    @staticmethod
    def _validate_product(product: Product) -> None:
        if not product.sku.strip():
            raise CatalogError("Mã SKU không được để trống.")
        if not product.name.strip():
            raise CatalogError("Tên hàng hóa không được để trống.")
        if product.min_quantity < 0:
            raise CatalogError("Ngưỡng tồn tối thiểu không hợp lệ.")
        if product.unit_price < 0:
            raise CatalogError("Đơn giá không hợp lệ.")
        if product.status not in (ProductStatus.ACTIVE, ProductStatus.DISCONTINUED):
            raise CatalogError("Trạng thái hàng hóa không hợp lệ.")

    # ------------------------------------------------------------------
    # Nhà cung cấp
    # ------------------------------------------------------------------
    def find_all_suppliers(self) -> list[Supplier]:
        return self._suppliers.find_all()

    def search_suppliers(self, keyword: str) -> list[Supplier]:
        return self._suppliers.search(keyword)

    def find_supplier(self, supplier_id: int) -> Supplier | None:
        return self._suppliers.find_by_id(supplier_id)

    def add_supplier(self, supplier: Supplier) -> Supplier:
        self._validate_supplier(supplier)
        if self._suppliers.code_exists(supplier.code):
            raise CatalogError(f"Mã nhà cung cấp '{supplier.code}' đã tồn tại.")
        supplier.id = self._suppliers.insert(supplier)
        return supplier

    def update_supplier(self, supplier: Supplier) -> None:
        if supplier.id is None:
            raise CatalogError("Thiếu định danh nhà cung cấp cần cập nhật.")
        self._validate_supplier(supplier)
        if self._suppliers.code_exists(supplier.code, exclude_id=supplier.id):
            raise CatalogError(f"Mã nhà cung cấp '{supplier.code}' đã được dùng.")
        self._suppliers.update(supplier)

    def delete_supplier(self, supplier_id: int) -> None:
        self._suppliers.delete_by_id(supplier_id)

    @staticmethod
    def _validate_supplier(supplier: Supplier) -> None:
        if not supplier.code.strip():
            raise CatalogError("Mã nhà cung cấp không được để trống.")
        if not supplier.name.strip():
            raise CatalogError("Tên nhà cung cấp không được để trống.")
        if supplier.status not in (SupplierStatus.ACTIVE, SupplierStatus.INACTIVE):
            raise CatalogError("Trạng thái nhà cung cấp không hợp lệ.")

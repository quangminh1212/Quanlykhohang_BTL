"""Ứng dụng giao diện Quản lý Kho hàng (Tkinter).

Lớp ``WarehouseApp`` tương ứng ``LibraryApplication`` trong thiết kế tham khảo:
là lớp khởi động và điều phối UI trung tâm. Nó dựng cửa sổ, điều hướng giữa các
màn hình (đăng nhập, màn hình chính) và gọi các service nghiệp vụ tương ứng.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date, datetime

from ..app_context import AppContext
from ..models.product import Product, ProductStatus
from ..models.supplier import Supplier, SupplierStatus
from ..models.user import User, Role
from ..services.auth_service import AuthError
from ..services.catalog_service import CatalogError
from ..repositories.transaction_repository import (
    InsufficientStockError,
    ProductNotFoundError,
)

# Bảng màu giao diện
COLOR_PRIMARY = "#1f6feb"
COLOR_PRIMARY_DARK = "#13438f"
COLOR_BG = "#f4f6fb"
COLOR_SIDEBAR = "#10243e"
COLOR_SIDEBAR_ACTIVE = "#1f6feb"
COLOR_CARD = "#ffffff"
COLOR_TEXT = "#1b2733"
COLOR_MUTED = "#6b7785"
COLOR_DANGER = "#d1242f"
COLOR_SUCCESS = "#1a7f37"


def format_money(value: float) -> str:
    """Định dạng tiền tệ kiểu Việt Nam: 1.234.567 đ."""
    try:
        return f"{value:,.0f} đ".replace(",", ".")
    except (ValueError, TypeError):
        return f"{value} đ"


class WarehouseApp:
    """Lớp khởi động và điều phối giao diện ứng dụng."""

    def __init__(self) -> None:
        # Khởi tạo tầng dữ liệu và nghiệp vụ
        self.ctx = AppContext()
        self.ctx.seed_sample_data()

        self.current_user: User | None = None

        self.root = tk.Tk()
        self.root.title("Hệ thống Quản lý Kho hàng")
        self.root.geometry("1180x720")
        self.root.minsize(1024, 640)
        self.root.configure(bg=COLOR_BG)

        self._init_styles()
        self._show_login()

    # ------------------------------------------------------------------
    # Vòng đời ứng dụng
    # ------------------------------------------------------------------
    def run(self) -> None:
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()

    def _on_close(self) -> None:
        self.ctx.close()
        self.root.destroy()

    def _init_styles(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background=COLOR_BG)
        style.configure("Card.TFrame", background=COLOR_CARD)
        style.configure("TLabel", background=COLOR_BG, foreground=COLOR_TEXT,
                        font=("Segoe UI", 10))
        style.configure("Card.TLabel", background=COLOR_CARD, foreground=COLOR_TEXT,
                        font=("Segoe UI", 10))
        style.configure("Title.TLabel", background=COLOR_BG, foreground=COLOR_TEXT,
                        font=("Segoe UI", 18, "bold"))
        style.configure("CardTitle.TLabel", background=COLOR_CARD,
                        foreground=COLOR_MUTED, font=("Segoe UI", 10))
        style.configure("CardValue.TLabel", background=COLOR_CARD,
                        foreground=COLOR_PRIMARY, font=("Segoe UI", 22, "bold"))
        style.configure("TButton", font=("Segoe UI", 10), padding=6)
        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"))
        style.configure("Treeview", font=("Segoe UI", 10), rowheight=28,
                        fieldbackground=COLOR_CARD, background=COLOR_CARD)
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        style.map("Treeview", background=[("selected", COLOR_PRIMARY)])

    def _clear_root(self) -> None:
        for widget in self.root.winfo_children():
            widget.destroy()

    # ------------------------------------------------------------------
    # Màn hình đăng nhập
    # ------------------------------------------------------------------
    def _show_login(self) -> None:
        self._clear_root()
        self.current_user = None

        container = tk.Frame(self.root, bg=COLOR_BG)
        container.pack(fill="both", expand=True)

        # Cột trái: nền thương hiệu
        left = tk.Frame(container, bg=COLOR_SIDEBAR, width=520)
        left.pack(side="left", fill="both", expand=True)
        left.pack_propagate(False)
        tk.Label(left, text="📦", font=("Segoe UI", 72), bg=COLOR_SIDEBAR,
                 fg="white").pack(pady=(140, 10))
        tk.Label(left, text="QUẢN LÝ KHO HÀNG", font=("Segoe UI", 24, "bold"),
                 bg=COLOR_SIDEBAR, fg="white").pack()
        tk.Label(left, text="Giải pháp số hóa quản trị kho hiện đại",
                 font=("Segoe UI", 12), bg=COLOR_SIDEBAR, fg="#9fb3c8").pack(pady=8)

        # Cột phải: biểu mẫu đăng nhập
        right = tk.Frame(container, bg=COLOR_BG)
        right.pack(side="left", fill="both", expand=True)
        form = tk.Frame(right, bg=COLOR_BG)
        form.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(form, text="Đăng nhập hệ thống", font=("Segoe UI", 20, "bold"),
                 bg=COLOR_BG, fg=COLOR_TEXT).grid(row=0, column=0, columnspan=2,
                                                  pady=(0, 24), sticky="w")

        tk.Label(form, text="Tên đăng nhập", bg=COLOR_BG, fg=COLOR_MUTED,
                 font=("Segoe UI", 10)).grid(row=1, column=0, columnspan=2, sticky="w")
        username_var = tk.StringVar()
        username_entry = tk.Entry(form, textvariable=username_var, width=34,
                                  font=("Segoe UI", 12), relief="solid", bd=1)
        username_entry.grid(row=2, column=0, columnspan=2, ipady=6, pady=(2, 14), sticky="we")

        tk.Label(form, text="Mật khẩu", bg=COLOR_BG, fg=COLOR_MUTED,
                 font=("Segoe UI", 10)).grid(row=3, column=0, columnspan=2, sticky="w")
        password_var = tk.StringVar()
        password_entry = tk.Entry(form, textvariable=password_var, show="•", width=34,
                                  font=("Segoe UI", 12), relief="solid", bd=1)
        password_entry.grid(row=4, column=0, columnspan=2, ipady=6, pady=(2, 18), sticky="we")

        def do_login(_event=None) -> None:
            try:
                user = self.ctx.account_service.login(
                    username_var.get(), password_var.get()
                )
            except AuthError as exc:
                messagebox.showerror("Đăng nhập thất bại", str(exc))
                return
            self.current_user = user
            self._show_main_shell()

        login_btn = tk.Button(form, text="Đăng nhập", command=do_login,
                              bg=COLOR_PRIMARY, fg="white", font=("Segoe UI", 12, "bold"),
                              relief="flat", cursor="hand2", activebackground=COLOR_PRIMARY_DARK,
                              activeforeground="white")
        login_btn.grid(row=5, column=0, columnspan=2, ipady=8, sticky="we")

        hint = tk.Label(
            form,
            text="Tài khoản mẫu:\n• Quản lý: manager / 123456\n• Nhân viên: staff / 123456",
            bg=COLOR_BG, fg=COLOR_MUTED, font=("Segoe UI", 9), justify="left")
        hint.grid(row=6, column=0, columnspan=2, pady=(20, 0), sticky="w")

        username_entry.focus_set()
        self.root.bind("<Return>", do_login)

    # ------------------------------------------------------------------
    # Màn hình chính (main shell)
    # ------------------------------------------------------------------
    def _show_main_shell(self) -> None:
        self._clear_root()
        self.root.unbind("<Return>")

        shell = tk.Frame(self.root, bg=COLOR_BG)
        shell.pack(fill="both", expand=True)

        # Sidebar
        self.sidebar = tk.Frame(shell, bg=COLOR_SIDEBAR, width=240)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        tk.Label(self.sidebar, text="📦 KHO HÀNG", font=("Segoe UI", 15, "bold"),
                 bg=COLOR_SIDEBAR, fg="white").pack(pady=(24, 4), padx=20, anchor="w")
        tk.Label(self.sidebar, text=f"{self.current_user.full_name}",
                 font=("Segoe UI", 10, "bold"), bg=COLOR_SIDEBAR, fg="#cdd9e5").pack(
            padx=20, anchor="w")
        tk.Label(self.sidebar, text=f"({self.current_user.role_label})",
                 font=("Segoe UI", 9), bg=COLOR_SIDEBAR, fg="#7d8da1").pack(
            padx=20, anchor="w", pady=(0, 16))

        # Khu vực nội dung
        self.content = tk.Frame(shell, bg=COLOR_BG)
        self.content.pack(side="left", fill="both", expand=True)

        # Định nghĩa menu: (khóa, nhãn, hàm dựng, chỉ dành cho quản lý)
        menu_items = [
            ("dashboard", "🏠  Tổng quan", self._view_dashboard, False),
            ("products", "📦  Hàng hóa", self._view_products, False),
            ("suppliers", "🏢  Nhà cung cấp", self._view_suppliers, False),
            ("import", "⬇️  Nhập kho", self._view_import, False),
            ("export", "⬆️  Xuất kho", self._view_export, False),
            ("history", "🧾  Lịch sử giao dịch", self._view_history, False),
            ("reports", "📊  Báo cáo & Thống kê", self._view_reports, True),
            ("profile", "👤  Hồ sơ cá nhân", self._view_profile, False),
        ]

        self._menu_buttons: dict[str, tk.Button] = {}
        for key, label, builder, manager_only in menu_items:
            if manager_only and not self.current_user.is_manager:
                continue
            btn = tk.Button(
                self.sidebar, text=label, anchor="w", relief="flat",
                bg=COLOR_SIDEBAR, fg="#cdd9e5", font=("Segoe UI", 11),
                activebackground=COLOR_SIDEBAR_ACTIVE, activeforeground="white",
                cursor="hand2", padx=20, pady=10,
                command=lambda k=key, b=builder: self._navigate(k, b),
            )
            btn.pack(fill="x")
            self._menu_buttons[key] = btn

        # Nút đăng xuất ở đáy
        tk.Button(self.sidebar, text="🚪  Đăng xuất", anchor="w", relief="flat",
                  bg=COLOR_SIDEBAR, fg="#f0a8a8", font=("Segoe UI", 11),
                  activebackground=COLOR_DANGER, activeforeground="white",
                  cursor="hand2", padx=20, pady=10,
                  command=self._logout).pack(side="bottom", fill="x", pady=(0, 16))

        self._navigate("dashboard", self._view_dashboard)

    def _navigate(self, key: str, builder) -> None:
        """Chuyển đổi giữa các màn hình chức năng."""
        for k, btn in self._menu_buttons.items():
            if k == key:
                btn.configure(bg=COLOR_SIDEBAR_ACTIVE, fg="white")
            else:
                btn.configure(bg=COLOR_SIDEBAR, fg="#cdd9e5")
        for widget in self.content.winfo_children():
            widget.destroy()
        builder()

    def _logout(self) -> None:
        if messagebox.askyesno("Đăng xuất", "Bạn có chắc muốn đăng xuất?"):
            self._show_login()

    # ------------------------------------------------------------------
    # Tiện ích dựng giao diện
    # ------------------------------------------------------------------
    def _page_header(self, parent, title: str) -> tk.Frame:
        header = tk.Frame(parent, bg=COLOR_BG)
        header.pack(fill="x", padx=28, pady=(24, 12))
        tk.Label(header, text=title, font=("Segoe UI", 18, "bold"),
                 bg=COLOR_BG, fg=COLOR_TEXT).pack(side="left")
        return header

    # ------------------------------------------------------------------
    # Màn hình: Tổng quan (Dashboard)
    # ------------------------------------------------------------------
    def _view_dashboard(self) -> None:
        self._page_header(self.content, "Tổng quan kho hàng")
        summary = self.ctx.report_service.dashboard_summary()

        cards_frame = tk.Frame(self.content, bg=COLOR_BG)
        cards_frame.pack(fill="x", padx=28)

        cards = [
            ("Tổng mặt hàng", str(summary.total_products), COLOR_PRIMARY),
            ("Tổng tồn kho", f"{summary.total_quantity:,}".replace(",", "."), COLOR_SUCCESS),
            ("Giá trị tồn kho", format_money(summary.total_stock_value), "#8250df"),
            ("Nhà cung cấp", str(summary.total_suppliers), "#bf8700"),
            ("Cảnh báo tồn thấp", str(summary.low_stock_count),
             COLOR_DANGER if summary.low_stock_count else COLOR_MUTED),
        ]
        for i, (title, value, color) in enumerate(cards):
            card = tk.Frame(cards_frame, bg=COLOR_CARD, bd=0, highlightthickness=1,
                            highlightbackground="#e1e6ef")
            card.grid(row=0, column=i, padx=6, pady=6, sticky="nsew", ipadx=10, ipady=14)
            cards_frame.grid_columnconfigure(i, weight=1)
            tk.Label(card, text=title, bg=COLOR_CARD, fg=COLOR_MUTED,
                     font=("Segoe UI", 10)).pack(anchor="w", padx=14, pady=(4, 0))
            tk.Label(card, text=value, bg=COLOR_CARD, fg=color,
                     font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=14, pady=(2, 6))

        # Khu vực hai cột: cảnh báo tồn thấp & giao dịch gần đây
        body = tk.Frame(self.content, bg=COLOR_BG)
        body.pack(fill="both", expand=True, padx=28, pady=16)

        # Cảnh báo tồn kho thấp
        low_card = tk.Frame(body, bg=COLOR_CARD, highlightthickness=1,
                            highlightbackground="#e1e6ef")
        low_card.pack(side="left", fill="both", expand=True, padx=(0, 8))
        tk.Label(low_card, text="⚠️  Hàng hóa cần nhập thêm", bg=COLOR_CARD,
                 fg=COLOR_TEXT, font=("Segoe UI", 12, "bold")).pack(anchor="w",
                                                                    padx=14, pady=12)
        low_tree = ttk.Treeview(low_card, columns=("sku", "name", "qty", "min"),
                                show="headings", height=8)
        for col, text, w in [("sku", "SKU", 80), ("name", "Tên hàng", 220),
                             ("qty", "Tồn", 60), ("min", "Tối thiểu", 80)]:
            low_tree.heading(col, text=text)
            low_tree.column(col, width=w, anchor="w")
        for p in summary.low_stock_items:
            low_tree.insert("", "end", values=(p.sku, p.name, p.quantity, p.min_quantity))
        if not summary.low_stock_items:
            low_tree.insert("", "end", values=("", "Không có cảnh báo", "", ""))
        low_tree.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        # Giao dịch gần đây
        recent_card = tk.Frame(body, bg=COLOR_CARD, highlightthickness=1,
                               highlightbackground="#e1e6ef")
        recent_card.pack(side="left", fill="both", expand=True, padx=(8, 0))
        tk.Label(recent_card, text="🧾  Giao dịch gần đây", bg=COLOR_CARD,
                 fg=COLOR_TEXT, font=("Segoe UI", 12, "bold")).pack(anchor="w",
                                                                    padx=14, pady=12)
        recent_tree = ttk.Treeview(recent_card, columns=("type", "name", "qty", "date"),
                                   show="headings", height=8)
        for col, text, w in [("type", "Loại", 80), ("name", "Hàng hóa", 200),
                             ("qty", "SL", 50), ("date", "Thời gian", 130)]:
            recent_tree.heading(col, text=text)
            recent_tree.column(col, width=w, anchor="w")
        for t in self.ctx.inventory_service.find_all()[:10]:
            recent_tree.insert("", "end", values=(t.type_label, t.product_name,
                                                   t.quantity, t.transaction_date[:16]))
        recent_tree.pack(fill="both", expand=True, padx=14, pady=(0, 14))

    # ------------------------------------------------------------------
    # Màn hình: Quản lý hàng hóa
    # ------------------------------------------------------------------
    def _view_products(self) -> None:
        header = self._page_header(self.content, "Quản lý hàng hóa")
        tk.Button(header, text="➕ Thêm hàng hóa", bg=COLOR_PRIMARY, fg="white",
                  relief="flat", cursor="hand2", font=("Segoe UI", 10, "bold"),
                  padx=14, pady=6, command=self._open_product_form).pack(side="right")

        # Thanh tìm kiếm
        toolbar = tk.Frame(self.content, bg=COLOR_BG)
        toolbar.pack(fill="x", padx=28)
        search_var = tk.StringVar()
        cat_var = tk.StringVar(value="Tất cả")
        tk.Label(toolbar, text="Tìm kiếm:", bg=COLOR_BG, fg=COLOR_MUTED).pack(side="left")
        search_entry = tk.Entry(toolbar, textvariable=search_var, width=30,
                                font=("Segoe UI", 10), relief="solid", bd=1)
        search_entry.pack(side="left", padx=8, ipady=3)
        tk.Label(toolbar, text="Danh mục:", bg=COLOR_BG, fg=COLOR_MUTED).pack(side="left")
        categories = ["Tất cả"] + self.ctx.catalog_service.categories()
        cat_combo = ttk.Combobox(toolbar, textvariable=cat_var, values=categories,
                                 state="readonly", width=18)
        cat_combo.pack(side="left", padx=8)

        # Bảng hàng hóa
        table_frame = tk.Frame(self.content, bg=COLOR_BG)
        table_frame.pack(fill="both", expand=True, padx=28, pady=14)
        columns = ("sku", "name", "category", "unit", "qty", "min", "price", "value",
                   "location", "supplier", "status")
        headers = [("sku", "SKU", 70), ("name", "Tên hàng hóa", 200),
                   ("category", "Danh mục", 110), ("unit", "ĐVT", 50),
                   ("qty", "Tồn", 55), ("min", "Tối thiểu", 70),
                   ("price", "Đơn giá", 100), ("value", "Giá trị tồn", 110),
                   ("location", "Vị trí", 70), ("supplier", "Nhà cung cấp", 160),
                   ("status", "Trạng thái", 110)]
        tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        for col, text, w in headers:
            tree.heading(col, text=text)
            tree.column(col, width=w, anchor="w")
        tree.tag_configure("low", foreground=COLOR_DANGER)
        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self._product_tree = tree

        def reload() -> None:
            for item in tree.get_children():
                tree.delete(item)
            keyword = search_var.get()
            category = "" if cat_var.get() == "Tất cả" else cat_var.get()
            for p in self.ctx.catalog_service.search_products(keyword, category):
                tag = "low" if p.is_low_stock else ""
                tree.insert("", "end", iid=str(p.id), tags=(tag,), values=(
                    p.sku, p.name, p.category, p.unit, p.quantity, p.min_quantity,
                    format_money(p.unit_price), format_money(p.stock_value),
                    p.location, p.supplier_name, p.status_label))

        self._reload_products = reload
        search_var.trace_add("write", lambda *_: reload())
        cat_combo.bind("<<ComboboxSelected>>", lambda *_: reload())

        # Nút thao tác
        actions = tk.Frame(self.content, bg=COLOR_BG)
        actions.pack(fill="x", padx=28, pady=(0, 18))
        tk.Button(actions, text="✏️ Sửa", relief="flat", bg="#e7eefc",
                  fg=COLOR_PRIMARY_DARK, cursor="hand2", padx=14, pady=6,
                  command=lambda: self._edit_selected_product(tree)).pack(side="left")
        if self.current_user.is_manager:
            tk.Button(actions, text="🗑️ Xóa", relief="flat", bg="#fbe9ea",
                      fg=COLOR_DANGER, cursor="hand2", padx=14, pady=6,
                      command=lambda: self._delete_selected_product(tree)).pack(
                side="left", padx=8)
        tree.bind("<Double-1>", lambda _e: self._edit_selected_product(tree))
        reload()

    def _edit_selected_product(self, tree) -> None:
        selection = tree.selection()
        if not selection:
            messagebox.showinfo("Thông báo", "Vui lòng chọn một hàng hóa.")
            return
        product = self.ctx.catalog_service.find_product(int(selection[0]))
        if product:
            self._open_product_form(product)

    def _delete_selected_product(self, tree) -> None:
        selection = tree.selection()
        if not selection:
            messagebox.showinfo("Thông báo", "Vui lòng chọn một hàng hóa.")
            return
        if messagebox.askyesno("Xác nhận", "Xóa hàng hóa đã chọn?"):
            try:
                self.ctx.catalog_service.delete_product(int(selection[0]))
                self._reload_products()
            except Exception as exc:  # noqa: BLE001
                messagebox.showerror("Lỗi", f"Không thể xóa: {exc}")

    def _open_product_form(self, product: Product | None = None) -> None:
        """Mở hộp thoại thêm/sửa hàng hóa."""
        is_edit = product is not None
        dialog = tk.Toplevel(self.root)
        dialog.title("Sửa hàng hóa" if is_edit else "Thêm hàng hóa")
        dialog.configure(bg=COLOR_CARD)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        suppliers = self.ctx.catalog_service.find_all_suppliers()
        supplier_labels = ["(Không chọn)"] + [f"{s.code} - {s.name}" for s in suppliers]

        fields: dict[str, tk.Variable] = {
            "sku": tk.StringVar(value=product.sku if is_edit else ""),
            "name": tk.StringVar(value=product.name if is_edit else ""),
            "category": tk.StringVar(value=product.category if is_edit else ""),
            "unit": tk.StringVar(value=product.unit if is_edit else "cái"),
            "min_quantity": tk.StringVar(value=str(product.min_quantity) if is_edit else "0"),
            "unit_price": tk.StringVar(value=str(int(product.unit_price)) if is_edit else "0"),
            "location": tk.StringVar(value=product.location if is_edit else ""),
        }
        supplier_var = tk.StringVar(value="(Không chọn)")
        status_var = tk.StringVar(value=ProductStatus.label(
            product.status if is_edit else ProductStatus.ACTIVE))
        qty_var = tk.StringVar(value=str(product.quantity) if is_edit else "0")
        if is_edit and product.supplier_id:
            for i, s in enumerate(suppliers):
                if s.id == product.supplier_id:
                    supplier_var.set(supplier_labels[i + 1])

        rows = [
            ("Mã SKU *", fields["sku"]),
            ("Tên hàng hóa *", fields["name"]),
            ("Danh mục", fields["category"]),
            ("Đơn vị tính", fields["unit"]),
            ("Tồn tối thiểu", fields["min_quantity"]),
            ("Đơn giá (đ)", fields["unit_price"]),
            ("Vị trí lưu trữ", fields["location"]),
        ]
        for i, (label, var) in enumerate(rows):
            tk.Label(dialog, text=label, bg=COLOR_CARD, fg=COLOR_TEXT,
                     font=("Segoe UI", 10)).grid(row=i, column=0, sticky="w",
                                                 padx=18, pady=6)
            tk.Entry(dialog, textvariable=var, width=34, font=("Segoe UI", 11),
                     relief="solid", bd=1).grid(row=i, column=1, padx=18, pady=6, ipady=3)

        base = len(rows)
        # Số lượng tồn (chỉ hiển thị khi thêm mới; khi sửa thì khóa, đổi qua nhập/xuất)
        tk.Label(dialog, text="Tồn kho ban đầu", bg=COLOR_CARD, fg=COLOR_TEXT,
                 font=("Segoe UI", 10)).grid(row=base, column=0, sticky="w", padx=18, pady=6)
        qty_entry = tk.Entry(dialog, textvariable=qty_var, width=34, font=("Segoe UI", 11),
                             relief="solid", bd=1)
        qty_entry.grid(row=base, column=1, padx=18, pady=6, ipady=3)
        if is_edit:
            qty_entry.configure(state="disabled")

        tk.Label(dialog, text="Nhà cung cấp", bg=COLOR_CARD, fg=COLOR_TEXT,
                 font=("Segoe UI", 10)).grid(row=base + 1, column=0, sticky="w",
                                             padx=18, pady=6)
        ttk.Combobox(dialog, textvariable=supplier_var, values=supplier_labels,
                     state="readonly", width=32).grid(row=base + 1, column=1, padx=18, pady=6)

        tk.Label(dialog, text="Trạng thái", bg=COLOR_CARD, fg=COLOR_TEXT,
                 font=("Segoe UI", 10)).grid(row=base + 2, column=0, sticky="w",
                                             padx=18, pady=6)
        ttk.Combobox(dialog, textvariable=status_var,
                     values=[ProductStatus.label(ProductStatus.ACTIVE),
                             ProductStatus.label(ProductStatus.DISCONTINUED)],
                     state="readonly", width=32).grid(row=base + 2, column=1, padx=18, pady=6)

        def save() -> None:
            try:
                sup_idx = supplier_labels.index(supplier_var.get())
                supplier_id = suppliers[sup_idx - 1].id if sup_idx > 0 else None
                status = (ProductStatus.ACTIVE
                          if status_var.get() == ProductStatus.label(ProductStatus.ACTIVE)
                          else ProductStatus.DISCONTINUED)
                data = Product(
                    id=product.id if is_edit else None,
                    sku=fields["sku"].get().strip(),
                    name=fields["name"].get().strip(),
                    category=fields["category"].get().strip(),
                    unit=fields["unit"].get().strip() or "cái",
                    quantity=product.quantity if is_edit else int(qty_var.get() or 0),
                    min_quantity=int(fields["min_quantity"].get() or 0),
                    unit_price=float(fields["unit_price"].get() or 0),
                    location=fields["location"].get().strip(),
                    supplier_id=supplier_id,
                    status=status,
                )
            except ValueError:
                messagebox.showerror("Lỗi", "Số lượng/đơn giá phải là số.", parent=dialog)
                return
            try:
                if is_edit:
                    self.ctx.catalog_service.update_product(data)
                else:
                    self.ctx.catalog_service.add_product(data)
            except CatalogError as exc:
                messagebox.showerror("Lỗi", str(exc), parent=dialog)
                return
            dialog.destroy()
            self._reload_products()

        btn_frame = tk.Frame(dialog, bg=COLOR_CARD)
        btn_frame.grid(row=base + 3, column=0, columnspan=2, pady=16)
        tk.Button(btn_frame, text="Lưu", bg=COLOR_PRIMARY, fg="white", relief="flat",
                  cursor="hand2", font=("Segoe UI", 11, "bold"), padx=24, pady=6,
                  command=save).pack(side="left", padx=6)
        tk.Button(btn_frame, text="Hủy", bg="#e6e9ef", fg=COLOR_TEXT, relief="flat",
                  cursor="hand2", padx=24, pady=6,
                  command=dialog.destroy).pack(side="left", padx=6)

    # ------------------------------------------------------------------
    # Màn hình: Nhà cung cấp
    # ------------------------------------------------------------------
    def _view_suppliers(self) -> None:
        header = self._page_header(self.content, "Quản lý nhà cung cấp")
        tk.Button(header, text="➕ Thêm nhà cung cấp", bg=COLOR_PRIMARY, fg="white",
                  relief="flat", cursor="hand2", font=("Segoe UI", 10, "bold"),
                  padx=14, pady=6, command=self._open_supplier_form).pack(side="right")

        table_frame = tk.Frame(self.content, bg=COLOR_BG)
        table_frame.pack(fill="both", expand=True, padx=28, pady=14)
        columns = ("code", "name", "contact", "phone", "email", "address", "status")
        headers = [("code", "Mã", 80), ("name", "Tên nhà cung cấp", 240),
                   ("contact", "Người liên hệ", 140), ("phone", "Điện thoại", 110),
                   ("email", "Email", 180), ("address", "Địa chỉ", 220),
                   ("status", "Trạng thái", 110)]
        tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        for col, text, w in headers:
            tree.heading(col, text=text)
            tree.column(col, width=w, anchor="w")
        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        def reload() -> None:
            for item in tree.get_children():
                tree.delete(item)
            for s in self.ctx.catalog_service.find_all_suppliers():
                tree.insert("", "end", iid=str(s.id), values=(
                    s.code, s.name, s.contact_person, s.phone, s.email,
                    s.address, s.status_label))

        self._reload_suppliers = reload

        actions = tk.Frame(self.content, bg=COLOR_BG)
        actions.pack(fill="x", padx=28, pady=(0, 18))
        tk.Button(actions, text="✏️ Sửa", relief="flat", bg="#e7eefc",
                  fg=COLOR_PRIMARY_DARK, cursor="hand2", padx=14, pady=6,
                  command=lambda: self._edit_selected_supplier(tree)).pack(side="left")
        if self.current_user.is_manager:
            tk.Button(actions, text="🗑️ Xóa", relief="flat", bg="#fbe9ea",
                      fg=COLOR_DANGER, cursor="hand2", padx=14, pady=6,
                      command=lambda: self._delete_selected_supplier(tree)).pack(
                side="left", padx=8)
        tree.bind("<Double-1>", lambda _e: self._edit_selected_supplier(tree))
        reload()

    def _edit_selected_supplier(self, tree) -> None:
        selection = tree.selection()
        if not selection:
            messagebox.showinfo("Thông báo", "Vui lòng chọn một nhà cung cấp.")
            return
        supplier = self.ctx.catalog_service.find_supplier(int(selection[0]))
        if supplier:
            self._open_supplier_form(supplier)

    def _delete_selected_supplier(self, tree) -> None:
        selection = tree.selection()
        if not selection:
            messagebox.showinfo("Thông báo", "Vui lòng chọn một nhà cung cấp.")
            return
        if messagebox.askyesno("Xác nhận", "Xóa nhà cung cấp đã chọn?"):
            try:
                self.ctx.catalog_service.delete_supplier(int(selection[0]))
                self._reload_suppliers()
            except Exception as exc:  # noqa: BLE001
                messagebox.showerror("Lỗi", f"Không thể xóa: {exc}")

    def _open_supplier_form(self, supplier: Supplier | None = None) -> None:
        is_edit = supplier is not None
        dialog = tk.Toplevel(self.root)
        dialog.title("Sửa nhà cung cấp" if is_edit else "Thêm nhà cung cấp")
        dialog.configure(bg=COLOR_CARD)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        fields = {
            "code": tk.StringVar(value=supplier.code if is_edit else ""),
            "name": tk.StringVar(value=supplier.name if is_edit else ""),
            "contact_person": tk.StringVar(value=supplier.contact_person if is_edit else ""),
            "phone": tk.StringVar(value=supplier.phone if is_edit else ""),
            "email": tk.StringVar(value=supplier.email if is_edit else ""),
            "address": tk.StringVar(value=supplier.address if is_edit else ""),
        }
        status_var = tk.StringVar(value=SupplierStatus.label(
            supplier.status if is_edit else SupplierStatus.ACTIVE))

        rows = [
            ("Mã nhà cung cấp *", fields["code"]),
            ("Tên nhà cung cấp *", fields["name"]),
            ("Người liên hệ", fields["contact_person"]),
            ("Điện thoại", fields["phone"]),
            ("Email", fields["email"]),
            ("Địa chỉ", fields["address"]),
        ]
        for i, (label, var) in enumerate(rows):
            tk.Label(dialog, text=label, bg=COLOR_CARD, fg=COLOR_TEXT,
                     font=("Segoe UI", 10)).grid(row=i, column=0, sticky="w",
                                                 padx=18, pady=6)
            tk.Entry(dialog, textvariable=var, width=36, font=("Segoe UI", 11),
                     relief="solid", bd=1).grid(row=i, column=1, padx=18, pady=6, ipady=3)

        tk.Label(dialog, text="Trạng thái", bg=COLOR_CARD, fg=COLOR_TEXT,
                 font=("Segoe UI", 10)).grid(row=len(rows), column=0, sticky="w",
                                             padx=18, pady=6)
        ttk.Combobox(dialog, textvariable=status_var,
                     values=[SupplierStatus.label(SupplierStatus.ACTIVE),
                             SupplierStatus.label(SupplierStatus.INACTIVE)],
                     state="readonly", width=34).grid(row=len(rows), column=1, padx=18, pady=6)

        def save() -> None:
            status = (SupplierStatus.ACTIVE
                      if status_var.get() == SupplierStatus.label(SupplierStatus.ACTIVE)
                      else SupplierStatus.INACTIVE)
            data = Supplier(
                id=supplier.id if is_edit else None,
                code=fields["code"].get().strip(),
                name=fields["name"].get().strip(),
                contact_person=fields["contact_person"].get().strip(),
                phone=fields["phone"].get().strip(),
                email=fields["email"].get().strip(),
                address=fields["address"].get().strip(),
                status=status,
            )
            try:
                if is_edit:
                    self.ctx.catalog_service.update_supplier(data)
                else:
                    self.ctx.catalog_service.add_supplier(data)
            except CatalogError as exc:
                messagebox.showerror("Lỗi", str(exc), parent=dialog)
                return
            dialog.destroy()
            self._reload_suppliers()

        btn_frame = tk.Frame(dialog, bg=COLOR_CARD)
        btn_frame.grid(row=len(rows) + 1, column=0, columnspan=2, pady=16)
        tk.Button(btn_frame, text="Lưu", bg=COLOR_PRIMARY, fg="white", relief="flat",
                  cursor="hand2", font=("Segoe UI", 11, "bold"), padx=24, pady=6,
                  command=save).pack(side="left", padx=6)
        tk.Button(btn_frame, text="Hủy", bg="#e6e9ef", fg=COLOR_TEXT, relief="flat",
                  cursor="hand2", padx=24, pady=6,
                  command=dialog.destroy).pack(side="left", padx=6)

    # ------------------------------------------------------------------
    # Màn hình: Nhập kho / Xuất kho (dùng chung khung)
    # ------------------------------------------------------------------
    def _view_import(self) -> None:
        self._build_stock_form(is_import=True)

    def _view_export(self) -> None:
        self._build_stock_form(is_import=False)

    def _build_stock_form(self, *, is_import: bool) -> None:
        title = "Phiếu nhập kho" if is_import else "Phiếu xuất kho"
        self._page_header(self.content, title)

        wrapper = tk.Frame(self.content, bg=COLOR_BG)
        wrapper.pack(fill="both", expand=True, padx=28, pady=8)

        card = tk.Frame(wrapper, bg=COLOR_CARD, highlightthickness=1,
                        highlightbackground="#e1e6ef")
        card.pack(side="left", fill="both", expand=True, padx=(0, 8))

        products = self.ctx.catalog_service.find_all_products()
        product_labels = [f"{p.sku} - {p.name} (tồn: {p.quantity})" for p in products]

        product_var = tk.StringVar()
        qty_var = tk.StringVar(value="1")
        price_var = tk.StringVar(value="0")
        partner_var = tk.StringVar()
        note_var = tk.StringVar()

        def on_product_selected(_e=None) -> None:
            label = product_var.get()
            if label in product_labels:
                p = products[product_labels.index(label)]
                price_var.set(str(int(p.unit_price)))

        rows_def = [
            ("Hàng hóa *", "combo", product_var, product_labels),
            ("Số lượng *", "entry", qty_var, None),
            ("Đơn giá (đ) *", "entry", price_var, None),
            ("Nhà cung cấp" if is_import else "Bên nhận", "entry", partner_var, None),
            ("Ghi chú", "entry", note_var, None),
        ]
        for i, (label, kind, var, values) in enumerate(rows_def):
            tk.Label(card, text=label, bg=COLOR_CARD, fg=COLOR_TEXT,
                     font=("Segoe UI", 10)).grid(row=i, column=0, sticky="w",
                                                 padx=20, pady=10)
            if kind == "combo":
                combo = ttk.Combobox(card, textvariable=var, values=values,
                                     state="readonly", width=44)
                combo.grid(row=i, column=1, padx=20, pady=10)
                combo.bind("<<ComboboxSelected>>", on_product_selected)
            else:
                tk.Entry(card, textvariable=var, width=46, font=("Segoe UI", 11),
                         relief="solid", bd=1).grid(row=i, column=1, padx=20,
                                                    pady=10, ipady=3)

        def submit() -> None:
            label = product_var.get()
            if label not in product_labels:
                messagebox.showwarning("Thiếu thông tin", "Vui lòng chọn hàng hóa.")
                return
            product = products[product_labels.index(label)]
            try:
                qty = int(qty_var.get())
                price = float(price_var.get() or 0)
            except ValueError:
                messagebox.showerror("Lỗi", "Số lượng và đơn giá phải là số.")
                return
            try:
                if is_import:
                    tx = self.ctx.inventory_service.import_stock(
                        product_id=product.id, quantity=qty, unit_price=price,
                        partner=partner_var.get().strip(),
                        username=self.current_user.username,
                        note=note_var.get().strip())
                else:
                    tx = self.ctx.inventory_service.export_stock(
                        product_id=product.id, quantity=qty, unit_price=price,
                        partner=partner_var.get().strip(),
                        username=self.current_user.username,
                        note=note_var.get().strip())
            except (InsufficientStockError, ProductNotFoundError, ValueError) as exc:
                messagebox.showerror("Không thể thực hiện", str(exc))
                return
            messagebox.showinfo(
                "Thành công",
                f"Đã tạo phiếu {tx.code}.\n{tx.type_label}: {tx.quantity} "
                f"{product.unit} {product.name}.\nThành tiền: {format_money(tx.total)}")
            # Làm mới màn hình để cập nhật tồn kho hiển thị
            self._navigate("import" if is_import else "export",
                           self._view_import if is_import else self._view_export)

        btn_color = COLOR_SUCCESS if is_import else "#bf6a02"
        btn_frame = tk.Frame(card, bg=COLOR_CARD)
        btn_frame.grid(row=len(rows_def), column=0, columnspan=2, pady=18)
        tk.Button(btn_frame, text=("⬇️ Xác nhận nhập kho" if is_import
                                   else "⬆️ Xác nhận xuất kho"),
                  bg=btn_color, fg="white", relief="flat", cursor="hand2",
                  font=("Segoe UI", 11, "bold"), padx=24, pady=8,
                  command=submit).pack()

        # Cột phải: hướng dẫn / tồn kho hiện tại
        side = tk.Frame(wrapper, bg=COLOR_CARD, highlightthickness=1,
                        highlightbackground="#e1e6ef", width=320)
        side.pack(side="left", fill="both", expand=True, padx=(8, 0))
        tk.Label(side, text="Tồn kho hiện tại", bg=COLOR_CARD, fg=COLOR_TEXT,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=14, pady=12)
        mini = ttk.Treeview(side, columns=("name", "qty"), show="headings", height=14)
        mini.heading("name", text="Hàng hóa")
        mini.heading("qty", text="Tồn")
        mini.column("name", width=210, anchor="w")
        mini.column("qty", width=60, anchor="center")
        for p in products:
            mini.insert("", "end", values=(p.name, p.quantity))
        mini.pack(fill="both", expand=True, padx=14, pady=(0, 14))

    # ------------------------------------------------------------------
    # Màn hình: Lịch sử giao dịch
    # ------------------------------------------------------------------
    def _view_history(self) -> None:
        self._page_header(self.content, "Lịch sử nhập / xuất kho")

        toolbar = tk.Frame(self.content, bg=COLOR_BG)
        toolbar.pack(fill="x", padx=28)
        filter_var = tk.StringVar(value="Tất cả")
        tk.Label(toolbar, text="Lọc theo loại:", bg=COLOR_BG, fg=COLOR_MUTED).pack(side="left")
        combo = ttk.Combobox(toolbar, textvariable=filter_var,
                             values=["Tất cả", "Nhập kho", "Xuất kho"],
                             state="readonly", width=16)
        combo.pack(side="left", padx=8)

        table_frame = tk.Frame(self.content, bg=COLOR_BG)
        table_frame.pack(fill="both", expand=True, padx=28, pady=14)
        columns = ("code", "type", "name", "qty", "price", "total", "partner",
                   "user", "date")
        headers = [("code", "Mã phiếu", 130), ("type", "Loại", 80),
                   ("name", "Hàng hóa", 200), ("qty", "SL", 50),
                   ("price", "Đơn giá", 100), ("total", "Thành tiền", 120),
                   ("partner", "Đối tác", 160), ("user", "Người thực hiện", 110),
                   ("date", "Thời gian", 140)]
        tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        for col, text, w in headers:
            tree.heading(col, text=text)
            tree.column(col, width=w, anchor="w")
        tree.tag_configure("import", foreground=COLOR_SUCCESS)
        tree.tag_configure("export", foreground="#bf6a02")
        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        def reload() -> None:
            for item in tree.get_children():
                tree.delete(item)
            sel = filter_var.get()
            tx_type = None
            if sel == "Nhập kho":
                tx_type = "IMPORT"
            elif sel == "Xuất kho":
                tx_type = "EXPORT"
            for t in self.ctx.inventory_service.find_all(tx_type):
                tag = "import" if t.type == "IMPORT" else "export"
                tree.insert("", "end", tags=(tag,), values=(
                    t.code, t.type_label, t.product_name, t.quantity,
                    format_money(t.unit_price), format_money(t.total),
                    t.partner, t.user_username, t.transaction_date[:16]))

        combo.bind("<<ComboboxSelected>>", lambda *_: reload())
        reload()

    # ------------------------------------------------------------------
    # Màn hình: Báo cáo & Thống kê
    # ------------------------------------------------------------------
    def _view_reports(self) -> None:
        self._page_header(self.content, "Báo cáo & Thống kê")

        toolbar = tk.Frame(self.content, bg=COLOR_BG)
        toolbar.pack(fill="x", padx=28)
        today = date.today()
        first_day = today.replace(day=1)
        start_var = tk.StringVar(value=first_day.isoformat())
        end_var = tk.StringVar(value=today.isoformat())

        tk.Label(toolbar, text="Từ ngày:", bg=COLOR_BG, fg=COLOR_MUTED).pack(side="left")
        tk.Entry(toolbar, textvariable=start_var, width=14, relief="solid", bd=1).pack(
            side="left", padx=6, ipady=3)
        tk.Label(toolbar, text="Đến ngày:", bg=COLOR_BG, fg=COLOR_MUTED).pack(side="left")
        tk.Entry(toolbar, textvariable=end_var, width=14, relief="solid", bd=1).pack(
            side="left", padx=6, ipady=3)
        tk.Label(toolbar, text="(định dạng YYYY-MM-DD)", bg=COLOR_BG,
                 fg=COLOR_MUTED, font=("Segoe UI", 8)).pack(side="left", padx=6)

        result_frame = tk.Frame(self.content, bg=COLOR_BG)
        result_frame.pack(fill="both", expand=True, padx=28, pady=14)

        def render() -> None:
            for widget in result_frame.winfo_children():
                widget.destroy()
            try:
                datetime.strptime(start_var.get(), "%Y-%m-%d")
                datetime.strptime(end_var.get(), "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Lỗi", "Ngày không hợp lệ (YYYY-MM-DD).")
                return
            report = self.ctx.report_service.period_report(start_var.get(), end_var.get())

            cards = [
                ("Số phiếu nhập", str(report.import_count), COLOR_SUCCESS),
                ("Số phiếu xuất", str(report.export_count), "#bf6a02"),
                ("Tổng giá trị nhập", format_money(report.import_value), COLOR_PRIMARY),
                ("Tổng giá trị xuất", format_money(report.export_value), "#8250df"),
            ]
            cards_frame = tk.Frame(result_frame, bg=COLOR_BG)
            cards_frame.pack(fill="x")
            for i, (t, v, c) in enumerate(cards):
                card = tk.Frame(cards_frame, bg=COLOR_CARD, highlightthickness=1,
                                highlightbackground="#e1e6ef")
                card.grid(row=0, column=i, padx=6, sticky="nsew", ipadx=8, ipady=12)
                cards_frame.grid_columnconfigure(i, weight=1)
                tk.Label(card, text=t, bg=COLOR_CARD, fg=COLOR_MUTED,
                         font=("Segoe UI", 10)).pack(anchor="w", padx=14, pady=(4, 0))
                tk.Label(card, text=v, bg=COLOR_CARD, fg=c,
                         font=("Segoe UI", 15, "bold")).pack(anchor="w", padx=14, pady=(2, 6))

            # Top hàng hóa
            top_frame = tk.Frame(result_frame, bg=COLOR_BG)
            top_frame.pack(fill="both", expand=True, pady=14)
            for side_title, data, side in [
                ("Top hàng hóa nhập nhiều", self.ctx.report_service.top_imported(), "left"),
                ("Top hàng hóa xuất nhiều", self.ctx.report_service.top_exported(), "right"),
            ]:
                box = tk.Frame(top_frame, bg=COLOR_CARD, highlightthickness=1,
                               highlightbackground="#e1e6ef")
                box.pack(side=side, fill="both", expand=True,
                         padx=(0, 8) if side == "left" else (8, 0))
                tk.Label(box, text=side_title, bg=COLOR_CARD, fg=COLOR_TEXT,
                         font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=14, pady=10)
                t = ttk.Treeview(box, columns=("name", "qty"), show="headings", height=6)
                t.heading("name", text="Hàng hóa")
                t.heading("qty", text="Số lượng")
                t.column("name", width=240, anchor="w")
                t.column("qty", width=90, anchor="center")
                for name, qty in data:
                    t.insert("", "end", values=(name, qty))
                if not data:
                    t.insert("", "end", values=("(Chưa có dữ liệu)", ""))
                t.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        def export_csv() -> None:
            path = filedialog.asksaveasfilename(
                defaultextension=".csv", filetypes=[("CSV", "*.csv")],
                initialfile=f"baocao_giaodich_{start_var.get()}_{end_var.get()}.csv")
            if not path:
                return
            try:
                count = self.ctx.report_service.export_transactions_csv(
                    path, start_var.get(), end_var.get())
                messagebox.showinfo("Thành công", f"Đã xuất {count} giao dịch ra:\n{path}")
            except Exception as exc:  # noqa: BLE001
                messagebox.showerror("Lỗi", f"Không thể xuất báo cáo: {exc}")

        def export_inventory() -> None:
            path = filedialog.asksaveasfilename(
                defaultextension=".csv", filetypes=[("CSV", "*.csv")],
                initialfile="baocao_tonkho.csv")
            if not path:
                return
            try:
                count = self.ctx.report_service.export_inventory_csv(path)
                messagebox.showinfo("Thành công", f"Đã xuất {count} mặt hàng ra:\n{path}")
            except Exception as exc:  # noqa: BLE001
                messagebox.showerror("Lỗi", f"Không thể xuất báo cáo: {exc}")

        tk.Button(toolbar, text="🔍 Xem thống kê", bg=COLOR_PRIMARY, fg="white",
                  relief="flat", cursor="hand2", font=("Segoe UI", 10, "bold"),
                  padx=14, pady=4, command=render).pack(side="left", padx=8)
        tk.Button(toolbar, text="📄 Xuất CSV giao dịch", bg="#e7eefc",
                  fg=COLOR_PRIMARY_DARK, relief="flat", cursor="hand2",
                  padx=12, pady=4, command=export_csv).pack(side="right")
        tk.Button(toolbar, text="📦 Xuất CSV tồn kho", bg="#e7eefc",
                  fg=COLOR_PRIMARY_DARK, relief="flat", cursor="hand2",
                  padx=12, pady=4, command=export_inventory).pack(side="right", padx=8)
        render()

    # ------------------------------------------------------------------
    # Màn hình: Hồ sơ cá nhân
    # ------------------------------------------------------------------
    def _view_profile(self) -> None:
        self._page_header(self.content, "Hồ sơ cá nhân")
        user = self.current_user

        wrapper = tk.Frame(self.content, bg=COLOR_BG)
        wrapper.pack(fill="both", expand=True, padx=28, pady=8)

        card = tk.Frame(wrapper, bg=COLOR_CARD, highlightthickness=1,
                        highlightbackground="#e1e6ef")
        card.pack(side="left", fill="both", expand=True, padx=(0, 8))
        tk.Label(card, text="Thông tin tài khoản", bg=COLOR_CARD, fg=COLOR_TEXT,
                 font=("Segoe UI", 12, "bold")).grid(row=0, column=0, columnspan=2,
                                                     sticky="w", padx=20, pady=12)

        full_name = tk.StringVar(value=user.full_name)
        email = tk.StringVar(value=user.email)
        department = tk.StringVar(value=user.department)
        position = tk.StringVar(value=user.position)
        phone = tk.StringVar(value=user.phone)

        info_rows = [
            ("Tên đăng nhập", tk.StringVar(value=user.username), False),
            ("Vai trò", tk.StringVar(value=user.role_label), False),
            ("Họ và tên", full_name, True),
            ("Email", email, True),
            ("Phòng ban", department, True),
            ("Chức vụ", position, True),
            ("Điện thoại", phone, True),
        ]
        for i, (label, var, editable) in enumerate(info_rows, start=1):
            tk.Label(card, text=label, bg=COLOR_CARD, fg=COLOR_MUTED,
                     font=("Segoe UI", 10)).grid(row=i, column=0, sticky="w",
                                                 padx=20, pady=8)
            entry = tk.Entry(card, textvariable=var, width=36, font=("Segoe UI", 11),
                             relief="solid", bd=1)
            entry.grid(row=i, column=1, padx=20, pady=8, ipady=3)
            if not editable:
                entry.configure(state="readonly")

        def save_profile() -> None:
            user.full_name = full_name.get().strip()
            user.email = email.get().strip()
            user.department = department.get().strip()
            user.position = position.get().strip()
            user.phone = phone.get().strip()
            try:
                self.ctx.account_service.update_profile(user)
                messagebox.showinfo("Thành công", "Đã cập nhật hồ sơ.")
            except Exception as exc:  # noqa: BLE001
                messagebox.showerror("Lỗi", str(exc))

        tk.Button(card, text="💾 Lưu hồ sơ", bg=COLOR_PRIMARY, fg="white",
                  relief="flat", cursor="hand2", font=("Segoe UI", 11, "bold"),
                  padx=20, pady=6, command=save_profile).grid(
            row=len(info_rows) + 1, column=0, columnspan=2, pady=16)

        # Cột phải: đổi mật khẩu
        side = tk.Frame(wrapper, bg=COLOR_CARD, highlightthickness=1,
                        highlightbackground="#e1e6ef", width=340)
        side.pack(side="left", fill="both", expand=True, padx=(8, 0))
        tk.Label(side, text="Đổi mật khẩu", bg=COLOR_CARD, fg=COLOR_TEXT,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=20, pady=12)

        old_pw = tk.StringVar()
        new_pw = tk.StringVar()
        confirm_pw = tk.StringVar()
        for label, var in [("Mật khẩu hiện tại", old_pw), ("Mật khẩu mới", new_pw),
                           ("Nhập lại mật khẩu mới", confirm_pw)]:
            tk.Label(side, text=label, bg=COLOR_CARD, fg=COLOR_MUTED,
                     font=("Segoe UI", 10)).pack(anchor="w", padx=20, pady=(6, 0))
            tk.Entry(side, textvariable=var, show="•", width=30,
                     font=("Segoe UI", 11), relief="solid", bd=1).pack(
                anchor="w", padx=20, pady=(2, 6), ipady=3)

        def change_password() -> None:
            if new_pw.get() != confirm_pw.get():
                messagebox.showerror("Lỗi", "Mật khẩu mới nhập lại không khớp.")
                return
            try:
                self.ctx.account_service.change_password(
                    user.username, old_pw.get(), new_pw.get())
                messagebox.showinfo("Thành công", "Đã đổi mật khẩu.")
                old_pw.set(""); new_pw.set(""); confirm_pw.set("")
            except AuthError as exc:
                messagebox.showerror("Lỗi", str(exc))

        tk.Button(side, text="🔑 Đổi mật khẩu", bg=COLOR_PRIMARY, fg="white",
                  relief="flat", cursor="hand2", font=("Segoe UI", 11, "bold"),
                  padx=20, pady=6, command=change_password).pack(anchor="w", padx=20, pady=16)


def main() -> None:
    """Điểm khởi chạy ứng dụng giao diện."""
    app = WarehouseApp()
    app.run()


if __name__ == "__main__":
    main()

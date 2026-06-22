"""
ui/gui.py
Giao diện đồ họa (GUI) cho Hệ thống Quản lý Hóa đơn, sử dụng Tkinter.

Module cung cấp giao diện người dùng đầy đủ gồm 4 tab:
    • Tab Sản phẩm  : Thêm, sửa, xóa, xem danh sách sản phẩm
    • Tab Khách hàng: Thêm, sửa, xóa, xem danh sách khách hàng
    • Tab Hóa đơn   : Tạo hóa đơn mới, xem chi tiết, xóa
    • Tab Thống kê  : Doanh thu (ngày/tháng/sản phẩm), bán chạy, khách VIP

Các kỹ thuật đã sử dụng:
    - entries = []
    - field_labels + field_values = 2 list song song
    - col_names + col_widths = 2 list song song
    - current_items = [[pid, qty], ...]
    - categories = [[category, [products]], ...]
    """

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import io
import sys
from utils.algorithms import sort_by_key, group_sum_pair, unique_values
from utils.data_structures import ArrayList

from core.product_manager import ProductManager
from core.customer_manager import CustomerManager
from core.invoice_manager import InvoiceManager
from core.statistics_manager import StatisticsManager


class InvoiceAppGUI:
    """
    Lớp giao diện đồ họa chính cho ứng dụng quản lý hóa đơn.

    Lớp này tạo và quản lý giao diện người dùng với 4 tab chức năng,
    kết nối trực tiếp với các Manager ở tầng core.

    Thay thế kỹ thuật quan trọng:
        • entries = []         — Danh sách ô nhập liệu, truy cập bằng index
        • current_items = [[pid, qty], ...]
        • categories = [[cat, [products]], ...]

    Thuộc tính:
        root (tk.Tk)                : Cửa sổ gốc Tkinter
        product_manager             : Quản lý sản phẩm
        customer_manager            : Quản lý khách hàng
        invoice_manager             : Quản lý hóa đơn
        statistics_manager          : Quản lý thống kê
    """

    def __init__(self, root):
        """
        Khởi tạo giao diện ứng dụng quản lý hóa đơn.

        Tham số:
            root: Cửa sổ gốc Tkinter

        Ném ra:
            Exception: Nếu không thể khởi tạo các trình quản lý
        """
        self.root = root
        self.root.title("Hệ thống Quản lý Hóa đơn")
        self.root.geometry("900x700")

        try:
            # Khởi tạo các trình quản lý
            self.product_manager = ProductManager()
            self.customer_manager = CustomerManager()
            self.invoice_manager = InvoiceManager(self.product_manager)
            self.statistics_manager = StatisticsManager(self.invoice_manager, self.product_manager)
        except Exception as e:
            messagebox.showerror("Lỗi khởi tạo", f"Không thể khởi tạo trình quản lý: {str(e)}")
            self.root.destroy()
            return

        # Tạo Notebook (giao diện tab)
        self.notebook = ttk.Notebook(root)
        self.product_tab = ttk.Frame(self.notebook)
        self.customer_tab = ttk.Frame(self.notebook)
        self.invoice_tab = ttk.Frame(self.notebook)
        self.statistics_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.product_tab, text='Quản lý Sản phẩm')
        self.notebook.add(self.customer_tab, text='Quản lý Khách hàng')
        self.notebook.add(self.invoice_tab, text='Quản lý Hóa đơn')
        self.notebook.add(self.statistics_tab, text='Thống kê')
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)

        # Điền nội dung cho mỗi tab
        self._create_product_tab()
        self._create_customer_tab()
        self._create_invoice_tab()
        self._create_statistics_tab()

    # TAB SẢN PHẨM
    def _create_product_tab(self):
        """
        Tạo tab Quản lý Sản phẩm.

        Tab bao gồm:
        - Treeview hiển thị danh sách sản phẩm (5 cột)
        - Bộ nút chức năng: Tải lại, Thêm, Cập nhật, Xóa

        Kỹ thuật:
            Chiều rộng cột Treeview dùng 2 list song song
        """
        # Frame chứa danh sách sản phẩm
        list_frame = ttk.LabelFrame(self.product_tab, text="Danh sách sản phẩm")
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Treeview để hiển thị sản phẩm — dùng tuple không phải dict
        columns = ("ID", "Tên", "Đơn giá", "Đơn vị tính", "Danh mục")
        self.product_tree = ttk.Treeview(list_frame, columns=columns, show="headings")

        # Chiều rộng cột — dùng 2 tuple song song thay vì dict
        col_names  = ("ID",  "Tên", "Đơn giá", "Đơn vị tính", "Danh mục")
        col_widths = (80,    200,   100,        100,            120)
        for i in range(len(col_names)):
            self.product_tree.heading(col_names[i], text=col_names[i])
            self.product_tree.column(col_names[i], width=col_widths[i])

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.product_tree.yview)
        self.product_tree.configure(yscrollcommand=scrollbar.set)
        self.product_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Frame chứa các nút
        button_frame = ttk.Frame(self.product_tab)
        button_frame.pack(fill="x", padx=10, pady=5)

        ttk.Button(button_frame, text="Tải lại",  command=self.load_products).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Thêm",     command=self.add_product_dialog).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Cập nhật", command=self.update_product_dialog).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Xóa",      command=self.delete_product).pack(side="left", padx=5)

        # Tải dữ liệu ban đầu
        self.load_products()

    def load_products(self):
        """Tải lại danh sách sản phẩm từ manager và cập nhật Treeview."""
        try:
            success, message = self.product_manager.load_products()
            if not success:
                messagebox.showerror("Lỗi", f"Không thể tải danh sách sản phẩm: {message}")
                return

            # Xóa dữ liệu cũ
            for item in self.product_tree.get_children():
                self.product_tree.delete(item)

            # Hiển thị dữ liệu mới
            for product in self.product_manager.products:
                self.product_tree.insert("", "end", values=(
                    product.product_id,
                    product.name,
                    f"{product.unit_price:,.0f}",
                    product.calculation_unit,
                    product.category
                ))
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tải danh sách sản phẩm: {str(e)}")

    def add_product_dialog(self):
        """
        Hiển thị hộp thoại nhập thông tin để thêm sản phẩm mới.

        Thiết kế UI:
            entries = []  — List các ô nhập liệu, truy cập bằng index:
                entries[0] → Mã sản phẩm
                entries[1] → Tên sản phẩm
                entries[2] → Đơn giá
                entries[3] → Đơn vị tính
                entries[4] → Danh mục
        Trả về:
            None

        Ném ra:
            ValueError: Nếu đơn giá không hợp lệ
            Exception: Nếu không thể thêm sản phẩm
        """
        dialog = tk.Toplevel(self.root)
        dialog.title("Thêm sản phẩm mới")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()

        input_frame = ttk.Frame(dialog, padding=10)
        input_frame.pack(fill="both", expand=True)

        # Nhãn/mặc định dùng 2 tuple song song; ô nhập lưu trong ArrayList
        field_labels  = ("Mã sản phẩm", "Tên sản phẩm", "Đơn giá", "Đơn vị tính", "Danh mục")
        field_defaults = ("",            "",              "",         "cái",          "Chung")
        entries = ArrayList()

        for i in range(len(field_labels)):
            ttk.Label(input_frame, text=f"{field_labels[i]}:", font=("Cambria", 12)).grid(
                row=i, column=0, sticky="w", pady=5)
            entry = tk.Entry(input_frame, width=30, font=("Cambria", 12))
            entry.grid(row=i, column=1, pady=5)
            entry.insert(0, field_defaults[i])
            entries.append(entry)

        def on_add():
            try:
                price_str = entries[2].get().strip()   # index 2 = Đơn giá
                price = float(price_str) if price_str else 0.0

                success, message = self.product_manager.add_product(
                    product_id=entries[0].get().strip(),        # index 0 = Mã
                    name=entries[1].get().strip(),              # index 1 = Tên
                    unit_price=price,
                    calculation_unit=entries[3].get().strip(),  # index 3 = Đơn vị
                    category=entries[4].get().strip()           # index 4 = Danh mục
                )
                if success:
                    messagebox.showinfo("Thành công", message)
                    self.load_products()
                    dialog.destroy()
                else:
                    messagebox.showerror("Lỗi", message)
            except ValueError:
                messagebox.showerror("Lỗi", "Đơn giá phải là một con số.")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể thêm sản phẩm: {str(e)}")

        button_frame = ttk.Frame(dialog, padding=10)
        button_frame.pack(fill="x")
        ttk.Button(button_frame, text="Thêm", command=on_add).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Hủy",  command=dialog.destroy).pack(side="right", padx=5)

    def update_product_dialog(self):
        """
        Hiển thị hộp thoại chỉnh sửa thông tin sản phẩm đã chọn.

        Thiết kế UI:
            entries = []  — List các ô nhập liệu, điền sẵn giá trị hiện tại:
                entries[0] → Tên sản phẩm
                entries[1] → Đơn giá
                entries[2] → Đơn vị tính
                entries[3] → Danh mục

        Trả về:
            None

        Ném ra:
            ValueError: Nếu đơn giá không hợp lệ
            Exception: Nếu không thể cập nhật sản phẩm
        """
        selected = self.product_tree.selection()
        if not selected:
            messagebox.showinfo("Thông báo", "Vui lòng chọn một sản phẩm để cập nhật.")
            return

        product_id = self.product_tree.item(selected[0], "values")[0]
        product = self.product_manager.find_product(product_id)
        if not product:
            messagebox.showerror("Lỗi", f"Không tìm thấy sản phẩm với mã {product_id}.")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title(f"Cập nhật sản phẩm - {product_id}")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()

        input_frame = ttk.Frame(dialog, padding=10)
        input_frame.pack(fill="both", expand=True)

        # 2 tuple song song: tên nhãn và giá trị hiện tại
        field_labels  = ("Tên sản phẩm", "Đơn giá", "Đơn vị tính", "Danh mục")
        field_values  = (product.name, str(product.unit_price),
                         product.calculation_unit, product.category)
        entries = ArrayList()

        for i in range(len(field_labels)):
            ttk.Label(input_frame, text=f"{field_labels[i]}:", font=("Cambria", 12)).grid(
                row=i, column=0, sticky="w", pady=5)
            entry = tk.Entry(input_frame, width=30, font=("Cambria", 12))
            entry.grid(row=i, column=1, pady=5)
            entry.insert(0, field_values[i])
            entries.append(entry)

        def on_update():
            try:
                price_str = entries[1].get().strip()    # index 1 = Đơn giá
                price = float(price_str) if price_str else product.unit_price

                success, message = self.product_manager.update_product(
                    product_id=product_id,
                    name=entries[0].get().strip(),            # index 0 = Tên
                    unit_price=price,
                    calculation_unit=entries[2].get().strip(),# index 2 = Đơn vị
                    category=entries[3].get().strip()         # index 3 = Danh mục
                )
                if success:
                    messagebox.showinfo("Thành công", message)
                    self.load_products()
                    dialog.destroy()
                else:
                    messagebox.showerror("Lỗi", message)
            except ValueError:
                messagebox.showerror("Lỗi", "Đơn giá phải là một con số.")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể cập nhật sản phẩm: {str(e)}")

        button_frame = ttk.Frame(dialog, padding=10)
        button_frame.pack(fill="x")
        ttk.Button(button_frame, text="Cập nhật", command=on_update).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Hủy",      command=dialog.destroy).pack(side="right", padx=5)

    def delete_product(self):
        """
        Xóa sản phẩm đã chọn sau khi xác nhận với người dùng.

        Trả về:
            None

        Ném ra:
            Exception: Nếu không thể xóa sản phẩm
        """
        selected = self.product_tree.selection()
        if not selected:
            messagebox.showinfo("Thông báo", "Vui lòng chọn một sản phẩm để xóa.")
            return

        product_id = self.product_tree.item(selected[0], "values")[0]

        if messagebox.askyesno("Xác nhận",
                               f"Bạn có chắc chắn muốn xóa sản phẩm '{product_id}'? "
                               f"Hành động này không thể hoàn tác."):
            try:
                success, message = self.product_manager.delete_product(product_id)
                if success:
                    messagebox.showinfo("Thành công", message)
                    self.load_products()
                else:
                    messagebox.showerror("Lỗi", message)
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể xóa sản phẩm: {str(e)}")
    # TAB KHÁCH HÀNG

    def _create_customer_tab(self):
        """Tạo tab Quản lý Khách hàng."""
        list_frame = ttk.LabelFrame(self.customer_tab, text="Danh sách khách hàng")
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        columns = ("ID", "Tên", "Điện thoại", "Địa chỉ")
        self.customer_tree = ttk.Treeview(list_frame, columns=columns, show="headings")

        # 2 tuple song song
        col_names  = ("ID", "Tên", "Điện thoại", "Địa chỉ")
        col_widths = (80,   180,   110,           160)
        for i in range(len(col_names)):
            self.customer_tree.heading(col_names[i], text=col_names[i])
            self.customer_tree.column(col_names[i], width=col_widths[i])

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.customer_tree.yview)
        self.customer_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.customer_tree.pack(fill="both", expand=True)

        button_frame = ttk.Frame(self.customer_tab)
        button_frame.pack(fill="x", padx=10, pady=5)
        ttk.Button(button_frame, text="Tải lại",  command=self.load_customers).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Thêm",     command=self.add_customer_dialog).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Cập nhật", command=self.update_customer_dialog).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Xóa",      command=self.delete_customer).pack(side="left", padx=5)

        self.load_customers()

    def load_customers(self):
        """Tải danh sách khách hàng lên Treeview."""
        for item in self.customer_tree.get_children():
            self.customer_tree.delete(item)
        self.customer_manager.load_customers()
        for c in self.customer_manager.customers:
            self.customer_tree.insert("", "end", iid=c.customer_id, values=(
                c.customer_id, c.name, c.phone, c.address
            ))

    def _get_selected_customer(self):
        """Lấy khách hàng đang chọn trong Treeview."""
        sel = self.customer_tree.selection()
        if not sel:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn một khách hàng.")
            return None
        return self.customer_manager.find_customer(sel[0])

    def add_customer_dialog(self):
        """Pop-up thêm khách hàng mới."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Thêm khách hàng")
        dialog.geometry("380x300")
        dialog.resizable(False, False)
        dialog.grab_set()

        frame = ttk.Frame(dialog, padding=15)
        frame.pack(fill="both", expand=True)

        # 2 tuple song song; ô nhập lưu trong ArrayList
        field_labels = ("Mã KH *:", "Họ tên *:", "Điện thoại:", "Địa chỉ:")
        field_keys   = ("id",       "name",       "phone",       "address")
        entries = ArrayList()

        for i in range(len(field_labels)):
            ttk.Label(frame, text=field_labels[i]).grid(
                row=i, column=0, sticky="w", pady=4, padx=(0, 10))
            e = ttk.Entry(frame, width=28)
            e.grid(row=i, column=1, sticky="ew", pady=4)
            entries.append(e)

        def on_add():
            success, msg = self.customer_manager.add_customer(
                entries[0].get(),   # id
                entries[1].get(),   # name
                entries[2].get(),   # phone
                entries[3].get()    # address
            )
            if success:
                messagebox.showinfo("Thành công", msg, parent=dialog)
                self.load_customers()
                dialog.destroy()
            else:
                messagebox.showerror("Lỗi", msg, parent=dialog)

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=8)
        ttk.Button(btn_frame, text="Thêm", command=on_add).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="Hủy",  command=dialog.destroy).pack(side="left", padx=6)

    def update_customer_dialog(self):
        """Pop-up cập nhật khách hàng."""
        c = self._get_selected_customer()
        if not c:
            return
        dialog = tk.Toplevel(self.root)
        dialog.title("Cập nhật khách hàng")
        dialog.geometry("380x300")
        dialog.resizable(False, False)
        dialog.grab_set()

        frame = ttk.Frame(dialog, padding=15)
        frame.pack(fill="both", expand=True)

        # 2 tuple song song: nhãn + giá trị hiện tại
        field_labels = ("Mã KH:", "Họ tên *:", "Điện thoại:", "Địa chỉ:")
        field_vals   = (c.customer_id, c.name, c.phone, c.address)
        entries = ArrayList()

        for i in range(len(field_labels)):
            ttk.Label(frame, text=field_labels[i]).grid(
                row=i, column=0, sticky="w", pady=4, padx=(0, 10))
            e = ttk.Entry(frame, width=28)
            e.insert(0, field_vals[i])
            if i == 0:  # Mã KH không cho sửa
                e.config(state="disabled")
            e.grid(row=i, column=1, sticky="ew", pady=4)
            entries.append(e)

        def on_update():
            success, msg = self.customer_manager.update_customer(
                c.customer_id,
                entries[1].get(),   # name
                entries[2].get(),   # phone
                entries[3].get()    # address
            )
            if success:
                messagebox.showinfo("Thành công", msg, parent=dialog)
                self.load_customers()
                dialog.destroy()
            else:
                messagebox.showerror("Lỗi", msg, parent=dialog)

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=8)
        ttk.Button(btn_frame, text="Cập nhật", command=on_update).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="Hủy",      command=dialog.destroy).pack(side="left", padx=6)

    def delete_customer(self):
        """Xóa khách hàng đã chọn."""
        c = self._get_selected_customer()
        if not c:
            return
        if messagebox.askyesno("Xác nhận", f"Xóa khách hàng '{c.name}'?"):
            success, msg = self.customer_manager.delete_customer(c.customer_id)
            if success:
                messagebox.showinfo("Thành công", msg)
                self.load_customers()
            else:
                messagebox.showerror("Lỗi", msg)
    # TAB HÓA ĐƠN

    def _create_invoice_tab(self):
        """
        Tạo tab quản lý hóa đơn với danh sách và các chức năng quản lý.

        Tab này bao gồm:
        - Treeview hiển thị danh sách hóa đơn
        - Các nút xem chi tiết, tạo mới, xóa hóa đơn
        - Chức năng tải lại dữ liệu
        """
        list_frame = ttk.LabelFrame(self.invoice_tab, text="Danh sách hóa đơn")
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        columns = ("ID", "Khách hàng", "Ngày", "Tổng tiền", "Số mặt hàng")
        self.invoice_tree = ttk.Treeview(list_frame, columns=columns, show="headings")

        for col in columns:
            self.invoice_tree.heading(col, text=col)
            self.invoice_tree.column(col, width=120)
        self.invoice_tree.column("ID", width=50, anchor='center')

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.invoice_tree.yview)
        self.invoice_tree.configure(yscrollcommand=scrollbar.set)
        self.invoice_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        button_frame = ttk.Frame(self.invoice_tab)
        button_frame.pack(fill="x", padx=10, pady=5)

        ttk.Button(button_frame, text="Tải lại",      command=self.load_invoices).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Xem chi tiết", command=self.view_invoice_details).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Tạo hóa đơn",  command=self.create_new_invoice).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Xóa hóa đơn",  command=self.delete_invoice).pack(side="left", padx=5)

        self.load_invoices()

    def load_invoices(self):
        """Tải lại danh sách hóa đơn từ manager và cập nhật Treeview."""
        try:
            success, message = self.invoice_manager.load_invoices()
            if not success:
                messagebox.showerror("Lỗi", f"Không thể tải danh sách hóa đơn: {message}")
                return

            for item in self.invoice_tree.get_children():
                self.invoice_tree.delete(item)

            for invoice in self.invoice_manager.invoices:
                self.invoice_tree.insert("", "end", values=(
                    invoice.invoice_id,
                    invoice.customer_name,
                    invoice.date,
                    f"{invoice.total_amount:,.0f}",
                    invoice.total_items
                ))
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tải danh sách hóa đơn: {str(e)}")

    def view_invoice_details(self):
        """
        Hiển thị chi tiết hóa đơn đã chọn trong cửa sổ mới.

        Trả về:
            None

        Ném ra:
            Exception: Nếu không tìm thấy hóa đơn
        """
        selected = self.invoice_tree.selection()
        if not selected:
            messagebox.showinfo("Thông báo", "Vui lòng chọn một hóa đơn để xem chi tiết.")
            return

        invoice_id = self.invoice_tree.item(selected[0], "values")[0]
        invoice = self.invoice_manager.find_invoice(str(invoice_id))
        if not invoice:
            messagebox.showerror("Lỗi", f"Không tìm thấy hóa đơn #{invoice_id}.")
            return

        detail_window = tk.Toplevel(self.root)
        detail_window.title(f"Chi tiết hóa đơn #{invoice_id}")
        detail_window.geometry("800x600")
        detail_window.transient(self.root)

        info_frame = ttk.LabelFrame(detail_window, text="Thông tin hóa đơn")
        info_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(info_frame, text=f"Mã hóa đơn: {invoice.invoice_id}", font=("Cambria", 11)).grid(
            row=0, column=0, sticky="w", padx=10, pady=5)
        ttk.Label(info_frame, text=f"Ngày: {invoice.date}", font=("Cambria", 11)).grid(
            row=0, column=1, sticky="w", padx=10, pady=5)
        ttk.Label(info_frame, text=f"Khách hàng: {invoice.customer_name}", font=("Cambria", 11)).grid(
            row=1, column=0, columnspan=2, sticky="w", padx=10, pady=5)

        items_frame = ttk.LabelFrame(detail_window, text="Danh sách mặt hàng")
        items_frame.pack(fill="both", expand=True, padx=10, pady=5)

        columns = ("STT", "Mã SP", "Tên", "Số lượng", "Đơn giá", "Thành tiền")
        items_tree = ttk.Treeview(items_frame, columns=columns, show="headings")

        for col in columns:
            items_tree.heading(col, text=col)

        items_tree.column("STT", width=40, anchor='center')
        items_tree.column("Mã SP", width=100)
        items_tree.column("Tên", width=250)

        for idx in range(len(invoice.items)):
            item = invoice.items[idx]
            product = self.product_manager.find_product(item.product_id)
            product_name = product.name if product else "[Sản phẩm không tồn tại]"
            items_tree.insert("", "end", values=(
                idx + 1, item.product_id, product_name, item.quantity,
                f"{item.unit_price:,.0f}", f"{item.total_price:,.0f}"
            ))

        items_tree.pack(fill='both', expand=True)

        summary_frame = ttk.Frame(detail_window)
        summary_frame.pack(fill="x", padx=10, pady=10)
        ttk.Label(summary_frame,
                  text=f"Tổng tiền: {invoice.total_amount:,.0f} VND",
                  font=("Cambria", 12, "bold")).pack(side="right")

        ttk.Button(detail_window, text="Đóng", command=detail_window.destroy).pack(pady=10)

    def delete_invoice(self):
        """Xóa hóa đơn đã chọn sau khi xác nhận."""
        selected = self.invoice_tree.selection()
        if not selected:
            messagebox.showinfo("Thông báo", "Vui lòng chọn một hóa đơn để xóa.")
            return

        invoice_id = str(self.invoice_tree.item(selected[0], "values")[0])
        invoice = self.invoice_manager.find_invoice(invoice_id)
        if not invoice:
            messagebox.showerror("Lỗi", f"Không tìm thấy hóa đơn #{invoice_id}.")
            return

        confirm_message = (
            f"Bạn có chắc chắn muốn xóa hóa đơn này?\n\n"
            f"Mã hóa đơn: #{invoice.invoice_id}\n"
            f"Khách hàng: {invoice.customer_name}\n"
            f"Ngày: {invoice.date}\n"
            f"Tổng tiền: {invoice.total_amount:,.0f} VND\n"
            f"Số mặt hàng: {invoice.total_items}\n\n"
            f"Hành động này không thể hoàn tác!"
        )

        if messagebox.askyesno("Xác nhận xóa hóa đơn", confirm_message, icon='warning'):
            try:
                success, message = self.invoice_manager.delete_invoice(invoice_id)
                if success:
                    messagebox.showinfo("Thành công", message)
                    self.load_invoices()
                else:
                    messagebox.showerror("Lỗi", message)
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể xóa hóa đơn: {str(e)}")

    def create_new_invoice(self):
        """
        Hiển thị hộp thoại tạo hóa đơn mới.

        Cửa sổ popup gồm:
        - Combobox chọn khách hàng
        - Ô nhập chiết khấu (%) và thuế VAT (%)
        - Treeview danh sách mặt hàng đã thêm
        - Nút thêm/xóa mặt hàng, nhãn tổng tiền tạm tính

        Thiết kế kỹ thuật:
            current_items = [[product_id, quantity], ...]
                — List-of-list
                — Tìm kiếm bằng Linear Search
            Khi "Tạo hóa đơn": truyền current_items thẳng vào
            invoice_manager.create_invoice() theo format List[List].

        Trả về:
            None

        Ném ra:
            ValueError: Nếu số lượng không hợp lệ
            Exception: Nếu không thể tạo hóa đơn
        """
        if not self.product_manager.products:
            messagebox.showinfo("Thông báo", "Không có sản phẩm nào. Vui lòng thêm sản phẩm trước.")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Tạo hóa đơn mới")
        dialog.geometry("700x600")
        dialog.transient(self.root)
        dialog.grab_set()

        # Phần thông tin khách hàng
        info_frame = ttk.LabelFrame(dialog, text="Thông tin hóa đơn")
        info_frame.pack(fill="x", padx=10, pady=5, side='top')

        ttk.Label(info_frame, text="Khách hàng:", font=("Cambria", 12)).grid(
            row=0, column=0, sticky="w", pady=5, padx=5)
        customer_var = tk.StringVar()
        customer_combo = ttk.Combobox(info_frame, textvariable=customer_var, width=38,
                                      state="readonly", font=("Cambria", 12))
        customer_combo["values"] = tuple(c.display_name() for c in self.customer_manager.customers)
        customer_combo.grid(row=0, column=1, pady=5, padx=5)

        # Ô nhập chiết khấu (%)
        ttk.Label(info_frame, text="Chiết khấu (%):", font=("Cambria", 12)).grid(
            row=1, column=0, sticky="w", pady=5, padx=5)
        discount_entry = tk.Entry(info_frame, width=10, font=("Cambria", 12))
        discount_entry.insert(0, "0")
        discount_entry.grid(row=1, column=1, sticky="w", pady=5, padx=5)

        # Ô nhập VAT (%)
        ttk.Label(info_frame, text="Thuế VAT (%):", font=("Cambria", 12)).grid(
            row=2, column=0, sticky="w", pady=5, padx=5)
        vat_entry = tk.Entry(info_frame, width=10, font=("Cambria", 12))
        vat_entry.insert(0, "10")
        vat_entry.grid(row=2, column=1, sticky="w", pady=5, padx=5)

        # Phần mặt hàng
        items_container_frame = ttk.Frame(dialog)
        items_container_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Frame chứa danh sách các mặt hàng đã thêm
        items_frame = ttk.LabelFrame(items_container_frame, text="Mặt hàng đã thêm")
        items_frame.pack(fill="both", expand=True, side="top", pady=(0, 5))

        # current_items dùng ArrayList chứa ArrayList: [[product_id, quantity], ...]
        current_items = ArrayList()

        columns = ("Mã SP", "Tên", "Số lượng", "Đơn giá", "Thành tiền")
        items_tree = ttk.Treeview(items_frame, columns=columns, show="headings")
        for col in columns:
            items_tree.heading(col, text=col)
        items_tree.pack(side="left", fill="both", expand=True)

        # Phần thêm/xóa mặt hàng
        add_item_frame = ttk.LabelFrame(items_container_frame, text="Thao tác")
        add_item_frame.pack(fill="x", side="bottom", pady=(5, 0))

        ttk.Label(add_item_frame, text="Sản phẩm:", font=("Cambria", 12)).grid(
            row=0, column=0, padx=5, pady=5, sticky='w')
        product_var = tk.StringVar()
        product_combo = ttk.Combobox(add_item_frame, textvariable=product_var, width=35,
                                     state="readonly", font=("Cambria", 12))
        product_combo['values'] = tuple(f"{p.product_id} - {p.name}" for p in self.product_manager.products)
        product_combo.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(add_item_frame, text="Số lượng:", font=("Cambria", 12)).grid(
            row=0, column=2, padx=5, pady=5, sticky='w')
        quantity_entry = tk.Entry(add_item_frame, width=10, font=("Cambria", 12))
        quantity_entry.grid(row=0, column=3, padx=5, pady=5)
        quantity_entry.insert(0, "1")

        total_label = ttk.Label(dialog, text="Tổng tiền: 0 VND", font=("Cambria", 12, "bold"))

        def update_items_list():
            """Cập nhật Treeview từ current_items (list of list)."""
            for i in items_tree.get_children():
                items_tree.delete(i)
            total_amount = 0.0
            # current_items[i] = [product_id, quantity]
            for item in current_items:
                pid = item[0]
                qty = item[1]
                product = self.product_manager.find_product(pid)
                if product:
                    total_price = qty * product.unit_price
                    total_amount = total_amount + total_price
                    items_tree.insert("", "end", values=(
                        product.product_id, product.name, qty,
                        f"{product.unit_price:,.0f}", f"{total_price:,.0f}"
                    ))
            total_label.config(text=f"Tổng tiền: {total_amount:,.0f} VND")

        def add_item():
            """Thêm mặt hàng vào current_items (list of list)."""
            if not product_var.get():
                return
            try:
                quantity = int(quantity_entry.get())
                if quantity <= 0:
                    return
                product_id = product_var.get().partition(" - ")[0]

                # Tìm xem đã có sản phẩm này chưa (Linear Search)
                found_index = -1
                for i in range(len(current_items)):
                    if current_items[i][0] == product_id:
                        found_index = i
                        break

                if found_index != -1:
                    # Đã có → cộng thêm số lượng
                    current_items[found_index][1] = current_items[found_index][1] + quantity
                else:
                    # Chưa có → thêm mới [product_id, quantity]
                    current_items.append(ArrayList((product_id, quantity)))
                update_items_list()
            except ValueError:
                messagebox.showerror("Lỗi", "Số lượng phải là số nguyên.")

        def remove_item():
            """Xóa mặt hàng khỏi current_items."""
            selected = items_tree.selection()
            if not selected:
                return
            product_id = items_tree.item(selected[0], "values")[0]
            # Lọc bỏ phần tử có product_id khớp
            new_items = ArrayList()
            for item in current_items:
                if item[0] != product_id:
                    new_items.append(item)
            # Cập nhật current_items tại chỗ
            current_items.clear()
            for item in new_items:
                current_items.append(item)
            update_items_list()

        # Nút thêm và xóa
        button_container = ttk.Frame(add_item_frame)
        button_container.grid(row=0, column=4, padx=10, pady=5)
        ttk.Button(button_container, text="Thêm", command=add_item).pack(side="left", padx=2)
        ttk.Button(button_container, text="Xóa",  command=remove_item).pack(side="left", padx=2)

        add_item_frame.grid_columnconfigure(1, weight=1)
        total_label.pack(pady=10, side='top')

        # Nút tạo hóa đơn
        def on_create():
            selected = customer_var.get()
            if not selected:
                messagebox.showinfo("Thông báo", "Vui lòng chọn khách hàng.")
                return
            customer_id = selected.partition(" - ")[0]
            customer = self.customer_manager.find_customer(customer_id)
            customer_name = customer.name if customer else selected
            if not current_items:
                messagebox.showinfo("Thông báo", "Hóa đơn phải có ít nhất một mặt hàng.")
                return

            try:
                try:
                    vat_rate      = float(vat_entry.get()) / 100
                    discount_rate = float(discount_entry.get()) / 100
                except ValueError:
                    messagebox.showerror("Lỗi", "Thuế VAT và chiết khấu phải là số.")
                    return
                if not (0 <= vat_rate <= 1) or not (0 <= discount_rate <= 1):
                    messagebox.showerror("Lỗi", "VAT và chiết khấu phải từ 0% đến 100%.")
                    return

                # Truyền current_items (list of list [[pid, qty],...]) vào create_invoice
                new_invoice, message = self.invoice_manager.create_invoice(
                    customer_name=customer_name,
                    items_data=current_items,
                    vat_rate=vat_rate,
                    discount_rate=discount_rate
                )
                if new_invoice:
                    messagebox.showinfo("Thành công", message)
                    self.load_invoices()
                    dialog.destroy()
                else:
                    messagebox.showerror("Lỗi", message)
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể tạo hóa đơn: {str(e)}")

        button_frame = ttk.Frame(dialog)
        button_frame.pack(side="bottom", fill="x", padx=10, pady=10)
        ttk.Button(button_frame, text="Tạo hóa đơn", command=on_create).pack(side="left")
        ttk.Button(button_frame, text="Hủy",          command=dialog.destroy).pack(side="right")

    # TAB THỐNG KÊ
    def _create_statistics_tab(self):
        """
        Tạo tab thống kê với các loại báo cáo khác nhau.

        Tab này bao gồm:
        - Sub-tab doanh thu (theo sản phẩm, theo thời gian)
        - Sub-tab sản phẩm (bán chạy nhất, phân loại)
        - Sub-tab khách hàng (khách hàng thân thiết)
        """
        stats_notebook = ttk.Notebook(self.statistics_tab)
        stats_notebook.pack(fill="both", expand=True, padx=10, pady=5)

        revenue_tab  = ttk.Frame(stats_notebook)
        product_tab  = ttk.Frame(stats_notebook)
        customer_tab = ttk.Frame(stats_notebook)

        stats_notebook.add(revenue_tab,  text="Doanh thu")
        stats_notebook.add(product_tab,  text="Sản phẩm")
        stats_notebook.add(customer_tab, text="Khách hàng")

        # Tab Doanh thu
        revenue_frame = ttk.LabelFrame(revenue_tab, text="Thống kê doanh thu")
        revenue_frame.pack(fill="both", expand=True, padx=10, pady=5)

        revenue_buttons = ttk.Frame(revenue_frame)
        revenue_buttons.pack(fill="x", padx=5, pady=5)

        ttk.Button(revenue_buttons, text="Doanh thu theo sản phẩm",
                   command=self.show_revenue_by_product).pack(side="left", padx=5)
        ttk.Button(revenue_buttons, text="Doanh thu theo ngày",
                   command=self.show_revenue_by_time).pack(side="left", padx=5)
        ttk.Button(revenue_buttons, text="Doanh thu theo tháng",
                   command=self.show_revenue_by_month).pack(side="left", padx=5)

        self.revenue_result = tk.Text(revenue_frame, height=20, width=80, font=("Cambria", 12))
        self.revenue_result.pack(fill="both", expand=True, padx=5, pady=5)
        self.revenue_result.insert("1.0", "Chọn loại thống kê doanh thu để xem kết quả")
        self.revenue_result.config(state="disabled")

        # Tab Sản phẩm
        product_frame = ttk.LabelFrame(product_tab, text="Thống kê sản phẩm")
        product_frame.pack(fill="both", expand=True, padx=10, pady=5)

        product_buttons = ttk.Frame(product_frame)
        product_buttons.pack(fill="x", padx=5, pady=5)

        ttk.Button(product_buttons, text="Top 10 bán chạy nhất (tháng)",
                   command=self.show_top_bestsellers).pack(side="left", padx=5)
        ttk.Button(product_buttons, text="Top 10 bán chạy nhất (tất cả)",
                   command=self.show_top_products).pack(side="left", padx=5)
        ttk.Button(product_buttons, text="Phân loại sản phẩm",
                   command=self.show_product_categories).pack(side="left", padx=5)

        self.product_result = tk.Text(product_frame, height=20, width=80, font=("Cambria", 12))
        self.product_result.pack(fill="both", expand=True, padx=5, pady=5)
        self.product_result.insert("1.0", "Chọn loại thống kê sản phẩm để xem kết quả")
        self.product_result.config(state="disabled")

        # Tab Khách hàng
        customer_frame = ttk.LabelFrame(customer_tab, text="Thống kê khách hàng")
        customer_frame.pack(fill="both", expand=True, padx=10, pady=5)

        customer_buttons = ttk.Frame(customer_frame)
        customer_buttons.pack(fill="x", padx=5, pady=5)

        ttk.Button(customer_buttons, text="Khách hàng thân thiết",
                   command=self.show_top_customers).pack(side="left", padx=5)

        self.customer_result = tk.Text(customer_frame, height=20, width=80, font=("Cambria", 12))
        self.customer_result.pack(fill="both", expand=True, padx=5, pady=5)
        self.customer_result.insert("1.0", "Chọn loại thống kê khách hàng để xem kết quả")
        self.customer_result.config(state="disabled")

    def _capture_stats_output(self, func):
        """
        Tham số:
            func: Callable — hàm thống kê cần gọi (không có tham số).

        Trả về:
            str — nội dung đã in ra.
        """
        old_stdout = sys.stdout
        buf = io.StringIO()
        sys.stdout = buf
        try:
            func()
        finally:
            sys.stdout = old_stdout
        return buf.getvalue()

    def _show_in_text(self, text_widget, content: str):
        """Hiển thị nội dung vào Text widget."""
        text_widget.config(state="normal")
        text_widget.delete("1.0", tk.END)
        text_widget.insert("1.0", content)
        text_widget.config(state="disabled")

    def show_revenue_by_product(self):
        """
        Hiển thị thống kê doanh thu theo từng sản phẩm.

        Trả về:
            None

        Ném ra:
            Exception: Nếu không thể tạo báo cáo thống kê
        """
        try:
            if not self.invoice_manager.invoices:
                messagebox.showinfo("Thông báo", "Không có dữ liệu hóa đơn để thống kê!")
                return
            output = self._capture_stats_output(self.statistics_manager.revenue_by_product)
            self._show_in_text(self.revenue_result, output)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể hiển thị thống kê: {str(e)}")

    def show_revenue_by_time(self):
        """
        Hiển thị thống kê doanh thu theo thời gian.

        Trả về:
            None

        Ném ra:
            Exception: Nếu không thể tạo báo cáo thống kê
        """
        try:
            if not self.invoice_manager.invoices:
                messagebox.showinfo("Thông báo", "Không có dữ liệu hóa đơn để thống kê!")
                return
            output = self._capture_stats_output(self.statistics_manager.revenue_by_date)
            self._show_in_text(self.revenue_result, output)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể hiển thị thống kê: {str(e)}")

    def show_revenue_by_month(self):
        """Hiển thị thống kê doanh thu theo tháng."""
        try:
            if not self.invoice_manager.invoices:
                messagebox.showinfo("Thông báo", "Không có dữ liệu hóa đơn!")
                return
            output = self._capture_stats_output(self.statistics_manager.revenue_by_month)
            self._show_in_text(self.revenue_result, output)
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def show_top_bestsellers(self):
        """Hiển thị Top 10 mặt hàng bán chạy nhất theo tháng người dùng chọn."""
        try:
            if not self.invoice_manager.invoices:
                messagebox.showinfo("Thông báo", "Không có dữ liệu hóa đơn!")
                return
            # Lấy danh sách các tháng có hóa đơn
            month_keys = unique_values(self.invoice_manager.invoices,
                                       key_func=lambda inv: inv.date[:7])
            months = sort_by_key(month_keys, key=lambda m: m, reverse=True)
            month = simpledialog.askstring(
                "Chọn tháng",
                "Nhập tháng (YYYY-MM), ví dụ: " + (months[0] if months else "") +
                "\nĐể trống = tất cả thời gian:",
                initialvalue=months[0] if months else ""
            )
            if month is None:
                return   # Người dùng bấm Cancel
            month = month.strip() if month.strip() else None

            output = self._capture_stats_output(
                lambda: self.statistics_manager.top_bestsellers(month=month, top_n=10)
            )
            self._show_in_text(self.product_result, output)
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def show_top_products(self):
        """
        Hiển thị thống kê các sản phẩm bán chạy nhất.

        Tính toán số lượng bán ra của từng sản phẩm dựa trên dữ liệu
        hóa đơn, sắp xếp theo thứ tự giảm dần và hiển thị báo cáo.

        Trả về:
            None

        Ném ra:
            Exception: Nếu không thể tạo báo cáo thống kê
        """
        try:
            if not self.invoice_manager.invoices:
                messagebox.showinfo("Thông báo", "Không có dữ liệu hóa đơn để thống kê!")
                return

            # Gom tất cả items
            all_items = ArrayList()
            for invoice in self.invoice_manager.invoices:
                for item in invoice.items:
                    all_items.append(item)

            # group_sum_pair trả về [[pid, qty, qty2], ...]
            product_stats = group_sum_pair(
                all_items,
                key_func=lambda it: it.product_id,
                qty_func=lambda it: it.quantity,
                rev_func=lambda it: it.quantity   # Cùng qty cho cả 2 giá trị
            )
            # product_stats[i] = [product_id, total_qty, total_qty2]

            if not product_stats:
                messagebox.showinfo("Thông báo", "Không có dữ liệu sản phẩm bán ra!")
                return

            # Sắp xếp theo số lượng (cột 1) giảm dần
            sorted_products = sort_by_key(
                product_stats,
                key=lambda x: x[1],
                reverse=True
            )

            # Tính tổng số lượng (duyệt list)
            total_quantity = 0
            for row in product_stats:
                total_quantity = total_quantity + row[1]

            # Tạo báo cáo
            report = io.StringIO()
            report.write("\n" + "="*80 + "\n")
            report.write("TOP SẢN PHẨM BÁN CHẠY NHẤT (THEO SỐ LƯỢNG)\n")
            report.write("="*80 + "\n")
            report.write(f"{'MÃ SP':<10} {'TÊN SẢN PHẨM':<30} {'SỐ LƯỢNG':<10} "
                         f"{'ĐƠN GIÁ':<15} {'DOANH THU':<15}\n")
            report.write("-"*80 + "\n")

            for row in sorted_products:
                product_id = row[0]
                quantity   = int(row[1])
                product = self.product_manager.find_product(product_id)
                if product:
                    unit_price = product.unit_price
                    revenue    = quantity * unit_price
                    report.write(f"{product_id:<10} {product.name:<30} {quantity:>10} "
                                 f"{unit_price:>15,.2f} {revenue:>15,.2f}\n")
                else:
                    report.write(f"{product_id:<10} {'[Sản phẩm không tồn tại]':<30} "
                                 f"{quantity:>10} {'N/A':>15} {'N/A':>15}\n")

            report.write("-"*80 + "\n")
            report.write(f"{'TỔNG CỘNG:':<40} {total_quantity:>10}\n")
            report.write("="*80 + "\n")

            self._show_in_text(self.product_result, report.getvalue())
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể hiển thị thống kê sản phẩm: {str(e)}")

    def show_product_categories(self):
        """
        Hiển thị thống kê sản phẩm theo danh mục.

        Thuật toán nhóm:
            categories = [[category_name, [product, ...]], ...]
            — List-of-pairs
            — Tìm kiếm danh mục đã tồn tại bằng Linear Search.

        Sắp xếp:
            - Danh mục: theo thứ tự bảng chữ cái (Merge Sort)
            - Sản phẩm trong danh mục: theo tên (Merge Sort)

        Trả về:
            None

        Ném ra:
            Exception: Nếu không thể tạo báo cáo thống kê
        """
        try:
            if not self.product_manager.products:
                messagebox.showinfo("Thông báo", "Không có sản phẩm nào!")
                return

            # Nhóm sản phẩm theo danh mục
            # categories = [[category_name, [product, product, ...]], ...]
            categories = ArrayList()

            for product in self.product_manager.products:
                category = product.category if product.category else "Chưa phân loại"

                # Linear Search tìm danh mục đã có
                found_index = -1
                for i in range(len(categories)):
                    if categories[i][0] == category:
                        found_index = i
                        break

                if found_index != -1:
                    categories[found_index][1].append(product)
                else:
                    group = ArrayList()
                    group.append(product)
                    categories.append(ArrayList((category, group)))

            # Tạo báo cáo
            report = io.StringIO()
            report.write("=" * 80 + "\n")
            report.write("THỐNG KÊ SẢN PHẨM THEO DANH MỤC\n")
            report.write("=" * 80 + "\n")

            total_products = len(self.product_manager.products)

            # Sắp xếp danh mục theo thứ tự bảng chữ cái
            sorted_categories = sort_by_key(categories, key=lambda c: c[0])

            for cat_pair in sorted_categories:
                category = cat_pair[0]
                products = cat_pair[1]
                percentage = (len(products) / total_products * 100) if total_products > 0 else 0

                report.write(f"\nDANH MỤC: {category} ({len(products)} sản phẩm - {percentage:.2f}%)\n")
                report.write("-" * 80 + "\n")
                report.write(f"{'MÃ SP':<10} {'TÊN SẢN PHẨM':<30} {'ĐƠN VỊ':<10} {'ĐƠN GIÁ':>15}\n")
                report.write("-" * 80 + "\n")

                for product in sort_by_key(products, key=lambda p: p.name):
                    report.write(f"{product.product_id:<10} {product.name:<30} "
                                 f"{product.calculation_unit:<10} {product.unit_price:>15,.2f}\n")

            report.write("\n" + "=" * 80 + "\n")
            report.write(f"TỔNG SỐ: {total_products} sản phẩm trong {len(categories)} danh mục\n")
            report.write("=" * 80 + "\n")

            self._show_in_text(self.product_result, report.getvalue())
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể hiển thị thống kê danh mục: {str(e)}")

    def show_top_customers(self):
        """
        Hiển thị thống kê khách hàng thân thiết.

        Trả về:
            None

        Ném ra:
            Exception: Nếu không thể tạo báo cáo thống kê
        """
        try:
            if not self.invoice_manager.invoices:
                messagebox.showinfo("Thông báo", "Không có dữ liệu hóa đơn để thống kê!")
                return

            while True:
                limit = simpledialog.askinteger(
                    "Số lượng khách hàng",
                    "Nhập số lượng khách hàng tiềm năng muốn xem:",
                    initialvalue=5
                )
                if limit is None:
                    return
                if limit <= 0:
                    messagebox.showerror("Lỗi", "Số lượng khách hàng phải lớn hơn 0.")
                    continue
                if limit > 20:
                    messagebox.showerror("Lỗi", "Số lượng khách hàng không được vượt quá 20.")
                    continue
                break

            output = self._capture_stats_output(
                lambda: self.statistics_manager.top_customers(limit=limit)
            )
            self._show_in_text(self.customer_result, output)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể hiển thị thống kê khách hàng: {str(e)}")


def start_gui():
    """
    Hàm khởi động giao diện đồ họa chính của ứng dụng.

    Tạo cửa sổ Tkinter root và khởi tạo lớp InvoiceAppGUI,
    sau đó bắt đầu vòng lặp sự kiện chính. Xử lý các lỗi
    nghiêm trọng bằng cách hiển thị hộp thoại lỗi.

    Trả về:
        None

    Ném ra:
        Exception: Nếu không thể khởi tạo giao diện
        tk.TclError: Nếu có lỗi với Tkinter
    """
    try:
        root = tk.Tk()
        app = InvoiceAppGUI(root)
        root.mainloop()
    except Exception as e:
        try:
            error_root = tk.Tk()
            error_root.title("Lỗi nghiêm trọng")
            error_root.geometry("400x200")
            error_label = ttk.Label(error_root,
                                    text=f"Đã xảy ra lỗi không thể phục hồi:\n{str(e)}",
                                    wraplength=380)
            error_label.pack(padx=20, pady=20)
            ttk.Button(error_root, text="Đóng", command=error_root.destroy).pack(pady=10)
            error_root.mainloop()
        except tk.TclError:
            pass

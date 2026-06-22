"""
core/statistics_manager.py
Tầng thống kê và báo cáo cho Hệ thống Quản lý Hóa đơn.

Module cung cấp hai loại phương thức:

  1. Phương thức in ra console (dùng cho CLI):
       revenue_by_date()     — Doanh thu theo từng ngày
       revenue_by_product()  — Doanh thu theo từng sản phẩm
       revenue_by_month()    — Doanh thu theo từng tháng
       top_customers(limit)  — Xếp hạng khách hàng thân thiết
       top_bestsellers(month, top_n) — Sản phẩm bán chạy nhất

  2. Phương thức trả về dữ liệu cho GUI (bắt đầu bằng 'get_'):
       get_revenue_by_date()    → list-of-pairs [[date, revenue], ...]
       get_revenue_by_product() → list ba cột  [[pid, revenue, qty], ...]
       get_top_customers(limit) → list-of-pairs [[name, spending], ...]

Thuật toán sử dụng (từ utils/algorithms.py):
    group_sum()      — Gom nhóm, trả về list-of-pairs
    group_sum_pair() — Gom nhóm 2 giá trị, trả về list 3 cột
    sort_by_key()    — Merge Sort tự cài đặt
    unique_values()  — Giá trị duy nhất
    get_value()      — Tra cứu trong list-of-pairs
"""

from .invoice_manager import InvoiceManager
from .product_manager import ProductManager
from utils.algorithms import sort_by_key, group_sum, group_sum_pair, unique_values, get_value
from utils.data_structures import ArrayList


class StatisticsManager:
    """
    Quản lý các thao tác thống kê và báo cáo trong Hệ thống Quản lý Hóa đơn.

    Lớp này cung cấp hai loại phương thức:

    Phương thức in console:
        revenue_by_date()    — Doanh thu theo từng ngày (Merge Sort giảm dần)
        revenue_by_product() — Doanh thu theo từng sản phẩm (group_sum_pair)
        revenue_by_month()   — Doanh thu theo tháng (group theo date[:7])
        top_customers(n)     — Top N khách hàng chi tiêu nhiều nhất
        top_bestsellers(...) — Top N sản phẩm bán chạy theo kỳ

    Phương thức trả về dữ liệu:
        get_revenue_by_date()    → list[list]: [[date_str, revenue], ...]
        get_revenue_by_product() → list[list]: [[pid, revenue, qty], ...]
        get_top_customers(n)     → list[list]: [[customer_name, spending], ...]

    Thuộc tính:
        invoice_manager (InvoiceManager): Trình quản lý hóa đơn
        product_manager (ProductManager): Trình quản lý sản phẩm
    """

    def __init__(self, invoice_manager: InvoiceManager, product_manager: ProductManager):
        """
        Khởi tạo trình quản lý thống kê.

        Tham số:
            invoice_manager (InvoiceManager): Trình quản lý hóa đơn.
                Dùng để đọc danh sách invoice và items khi tạo báo cáo.
            product_manager (ProductManager): Trình quản lý sản phẩm.
                Dùng để tra cứu tên sản phẩm khi hiển thị báo cáo.
        """
        self.invoice_manager = invoice_manager
        self.product_manager = product_manager

    def revenue_by_date(self) -> None:
        """
        In báo cáo doanh thu theo từng ngày ra console.

        Thuật toán:
            1. Duyệt toàn bộ hóa đơn, gom nhóm doanh thu theo ngày
               bằng group_sum() → list-of-pairs [[date, revenue], ...].
            2. Sắp xếp theo ngày giảm dần bằng Merge Sort tự cài đặt.
            3. Tính tổng doanh thu bằng vòng lặp dọng thẳng (không dùng sum()).
            4. Hiển thị bảng kết quả kèm tỉ lệ %.
        """
        if not self.invoice_manager.invoices:
            print("Không có dữ liệu hóa đơn để thống kê!")
            return

        # Nhóm doanh thu theo ngày
        date_revenue = group_sum(
            self.invoice_manager.invoices,
            key_func=lambda inv: inv.date,
            value_func=lambda inv: inv.total_amount
        )

        if not date_revenue:
            print("Không có dữ liệu doanh thu để hiển thị!")
            return

        # Sắp xếp theo ngày (mới nhất trước) bằng Merge Sort
        sorted_dates = sort_by_key(date_revenue, key=lambda x: x[0], reverse=True)

        # Tính tổng doanh thu (duyệt qua list-of-pairs)
        total_revenue = 0.0
        for pair in date_revenue:
            total_revenue = total_revenue + pair[1]

        # Hiển thị báo cáo
        print("\n" + "="*60)
        print("THỐNG KÊ DOANH THU THEO NGÀY")
        print("="*60)
        print(f"{'NGÀY':<15} {'DOANH THU':<20} {'TỈ LỆ':<10}")
        print("-"*60)

        for pair in sorted_dates:
            date    = pair[0]
            revenue = pair[1]
            percentage = (revenue / total_revenue) * 100 if total_revenue > 0 else 0
            print(f"{date:<15} {revenue:>20,.2f} {percentage:>9.2f}%")

        print("-"*60)
        print(f"{'TỔNG CỘNG:':<15} {total_revenue:>20,.2f}")
        print("="*60)

    def revenue_by_product(self) -> None:
        """
        In báo cáo doanh thu chi tiết theo từng sản phẩm ra console.

        Thuật toán:
            1. Gộp tất cả InvoiceItem từ mọi hóa đơn thành một list.
            2. Dùng group_sum_pair() gom nhóm theo product_id,
               cộng đồng thời doanh thu và số lượng.
               Kết quả: [[product_id, tổng_doanh_thu, tổng_số_lượng], ...]
            3. Sắp xếp giảm dần theo doanh thu (cột 1) bằng Merge Sort.
            4. Tra cứu tên sản phẩm từ ProductManager để hiển thị.
        """
        if not self.invoice_manager.invoices:
            print("Không có dữ liệu hóa đơn để thống kê!")
            return

        # Gom tất cả items từ tất cả hóa đơn
        all_items = ArrayList()
        for invoice in self.invoice_manager.invoices:
            for item in invoice.items:
                all_items.append(item)

        if not all_items:
            print("Không có dữ liệu doanh thu theo sản phẩm để hiển thị!")
            return

        # group_sum_pair trả về list ba cột: [[product_id, total_price, quantity], ...]
        # qty_func = total_price (doanh thu), rev_func = quantity (số lượng)
        product_stats = group_sum_pair(
            all_items,
            key_func=lambda it: it.product_id,
            qty_func=lambda it: it.total_price,
            rev_func=lambda it: it.quantity
        )
        # product_stats[i] = [product_id, tổng_doanh_thu, tổng_số_lượng]

        # Sắp xếp theo doanh thu (cao nhất trước)
        sorted_products = sort_by_key(
            product_stats,
            key=lambda x: x[1],    # Cột 1 = tổng doanh thu
            reverse=True
        )

        # Tính tổng doanh thu
        total_revenue = 0.0
        for row in product_stats:
            total_revenue = total_revenue + row[1]

        # Hiển thị báo cáo
        print("\n" + "="*80)
        print("THỐNG KÊ DOANH THU THEO SẢN PHẨM")
        print("="*80)
        print(f"{'MÃ SP':<10} {'TÊN SẢN PHẨM':<30} {'SỐ LƯỢNG':<10} {'DOANH THU':<15} {'TỈ LỆ':<10}")
        print("-"*80)

        for row in sorted_products:
            product_id = row[0]
            revenue    = row[1]
            quantity   = int(row[2])
            product = self.product_manager.find_product(product_id)
            product_name = product.name if product else "[Sản phẩm không tồn tại]"
            percentage = (revenue / total_revenue) * 100 if total_revenue > 0 else 0
            print(f"{product_id:<10} {product_name:<30} {quantity:>10} {revenue:>15,.2f} {percentage:>9.2f}%")

        print("-"*80)
        print(f"{'TỔNG CỘNG:':<50} {total_revenue:>15,.2f}")
        print("="*80)

    def top_customers(self, limit: int = 5) -> None:
        """
        Hiển thị báo cáo khách hàng thân thiết (chi tiêu nhiều nhất).

        Tham số:
            limit (int): Số lượng khách hàng hàng đầu cần hiển thị.
                        Mặc định là 5.
        """
        if not self.invoice_manager.invoices:
            print("Không có dữ liệu hóa đơn để thống kê!")
            return

        # Nhóm chi tiêu theo khách hàng
        customer_spending = group_sum(
            self.invoice_manager.invoices,
            key_func=lambda inv: inv.customer_name,
            value_func=lambda inv: inv.total_amount
        )

        if not customer_spending:
            print("Không có dữ liệu khách hàng để hiển thị!")
            return

        # Sắp xếp theo chi tiêu (cao nhất trước), lấy top limit
        sorted_customers = sort_by_key(
            customer_spending,
            key=lambda x: x[1],
            reverse=True
        )
        # Giới hạn kết quả
        if len(sorted_customers) > limit:
            sorted_customers = sorted_customers[:limit]

        # Tính tổng chi tiêu
        total_spending = 0.0
        for pair in customer_spending:
            total_spending = total_spending + pair[1]

        # Hiển thị báo cáo
        print("\n" + "="*60)
        print(f"TOP {limit} KHÁCH HÀNG TIỀM NĂNG")
        print("="*60)
        print(f"{'KHÁCH HÀNG':<30} {'TỔNG CHI TIÊU':<20} {'TỈ LỆ':<10}")
        print("-"*60)

        for pair in sorted_customers:
            customer_name = pair[0]
            spending      = pair[1]
            percentage = (spending / total_spending) * 100 if total_spending > 0 else 0
            print(f"{customer_name:<30} {spending:>20,.2f} {percentage:>9.2f}%")

        print("-"*60)
        print(f"{'TỔNG CỘNG:':<30} {total_spending:>20,.2f}")
        print("="*60)

    def revenue_by_month(self) -> None:
        """
        Hiển thị báo cáo doanh thu theo từng tháng.
        Nhóm hóa đơn theo YYYY-MM, tính tổng và hiển thị mới nhất trước.
        """
        if not self.invoice_manager.invoices:
            print("Không có dữ liệu hóa đơn để thống kê!")
            return

        # Nhóm doanh thu theo tháng (YYYY-MM)
        month_revenue = group_sum(
            self.invoice_manager.invoices,
            key_func=lambda inv: inv.date[:7],
            value_func=lambda inv: inv.total_amount
        )

        # Sắp xếp theo tháng (mới nhất trước)
        sorted_months = sort_by_key(month_revenue, key=lambda x: x[0], reverse=True)

        # Tính tổng doanh thu
        total_revenue = 0.0
        for pair in month_revenue:
            total_revenue = total_revenue + pair[1]

        sep = "=" * 60
        print("\n" + sep)
        print("THONG KE DOANH THU THEO THANG")
        print(sep)
        print("{:<15} {:>20} {:>10}".format("THANG", "DOANH THU", "TI LE"))
        print("-" * 60)
        for pair in sorted_months:
            month   = pair[0]
            revenue = pair[1]
            pct = (revenue / total_revenue * 100) if total_revenue > 0 else 0
            print("{:<15} {:>20,.0f} {:>9.1f}%".format(month, revenue, pct))
        print("-" * 60)
        print("{:<15} {:>20,.0f}".format("TONG CONG:", total_revenue))
        print(sep)

    def top_bestsellers(self, month: str = None, top_n: int = 10) -> None:
        """
        Hiển thị Top N mặt hàng bán chạy nhất trong kỳ.

        Tham số:
            month : Lọc theo tháng định dạng YYYY-MM (None = tất cả).
            top_n : Số lượng sản phẩm hiển thị, mặc định 10.

        Thuật toán:
            1. Lọc hóa đơn theo tháng nếu có.
            2. Cộng dồn số lượng bán ra và doanh thu theo từng sản phẩm.
            3. Sắp xếp giảm dần theo số lượng, lấy top_n đầu.
        """
        if not self.invoice_manager.invoices:
            print("Không có dữ liệu hóa đơn để thống kê!")
            return

        invoices = self.invoice_manager.invoices
        if month:
            filtered = ArrayList()
            for inv in invoices:
                if inv.date[:7] == month:
                    filtered.append(inv)
            invoices = filtered
        if not invoices:
            print("Không có hóa đơn nào trong tháng " + str(month))
            return

        all_items = ArrayList()
        for invoice in invoices:
            for item in invoice.items:
                all_items.append(item)

        # group_sum_pair trả về [[product_id, qty, revenue], ...]
        product_stats = group_sum_pair(
            all_items,
            key_func=lambda it: it.product_id,
            qty_func=lambda it: it.quantity,
            rev_func=lambda it: it.total_price
        )

        # Sắp xếp theo số lượng (cột 1) giảm dần, lấy top_n
        sorted_products = sort_by_key(
            product_stats, key=lambda x: x[1], reverse=True
        )
        if len(sorted_products) > top_n:
            sorted_products = sorted_products[:top_n]

        period = ("thang " + month) if month else "tat ca thoi gian"
        sep = "=" * 75
        print("\n" + sep)
        print("TOP {} MAT HANG BAN CHAY NHAT ({})".format(top_n, period.upper()))
        print(sep)
        print("{:<4} {:<8} {:<28} {:>10} {:>12}".format(
            "#", "MA SP", "TEN SAN PHAM", "SO LUONG", "DOANH THU"))
        print("-" * 75)
        for rank in range(len(sorted_products)):
            row      = sorted_products[rank]
            pid      = row[0]
            qty      = int(row[1])
            rev      = row[2]
            product  = self.product_manager.find_product(pid)
            name     = product.name if product else "[Da xoa]"
            print("{:<4} {:<8} {:<28} {:>10} {:>12,.0f}".format(
                rank + 1, pid, name, qty, rev))
        print(sep)

    # PHƯƠNG THỨC TRẢ VỀ DỮ LIỆU
    def get_revenue_by_date(self):
        """
        Trả về dữ liệu doanh thu theo ngày dạng list-of-pairs.

        Trả về:
            list[list]: [[date_str, revenue], ...] đã sắp xếp theo ngày mới nhất.
        """
        if not self.invoice_manager.invoices:
            return ArrayList()
        date_revenue = group_sum(
            self.invoice_manager.invoices,
            key_func=lambda inv: inv.date,
            value_func=lambda inv: inv.total_amount
        )
        return sort_by_key(date_revenue, key=lambda x: x[0], reverse=True)

    def get_revenue_by_product(self):
        """
        Trả về dữ liệu doanh thu theo sản phẩm dạng list ba cột.
        Trả về:
            list[list]: [[product_id, revenue, quantity], ...] đã sắp xếp giảm dần.
        """
        if not self.invoice_manager.invoices:
            return ArrayList()
        all_items = ArrayList()
        for invoice in self.invoice_manager.invoices:
            for item in invoice.items:
                all_items.append(item)
        if not all_items:
            return ArrayList()
        product_stats = group_sum_pair(
            all_items,
            key_func=lambda it: it.product_id,
            qty_func=lambda it: it.total_price,
            rev_func=lambda it: it.quantity
        )
        return sort_by_key(product_stats, key=lambda x: x[1], reverse=True)

    def get_top_customers(self, limit: int = 5):
        """
        Trả về dữ liệu khách hàng tiềm năng dạng list-of-pairs.

        Trả về:
            list[list]: [[customer_name, total_spending], ...] đã sắp xếp.
        """
        if not self.invoice_manager.invoices:
            return ArrayList()
        customer_spending = group_sum(
            self.invoice_manager.invoices,
            key_func=lambda inv: inv.customer_name,
            value_func=lambda inv: inv.total_amount
        )
        sorted_list = sort_by_key(customer_spending, key=lambda x: x[1], reverse=True)
        if len(sorted_list) > limit:
            return sorted_list[:limit]
        return sorted_list

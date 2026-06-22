"""
core/invoice_manager.py
Tầng xử lý nghiệp vụ: Quản lý hóa đơn.

Lớp InvoiceManager xử lý toàn bộ logic liên quan đến hóa đơn:
    • Tải hóa đơn + chi tiết từ 2 file CSV theo mô hình Master-Detail
    • Tạo hóa đơn mới: ghi cả 2 file, snapshot giá tại thời điểm lập
    • Xóa hóa đơn: xóa cả dữ liệu master lẫn detail
    • Tìm kiếm hóa đơn bằng thuật toán Linear Search

Mô hình lưu trữ Master-Detail:
    Master: data/invoices.csv     — thông tin chính của hóa đơn
    Detail: data/invoice_items.csv — từng dòng mặt hàng trong hóa đơn

Cột CSV invoices và chỉ số tương ứng:
    Cột:  invoice_id | customer_name | date | vat_rate | discount_rate
    Index:     0      |      1        |  2   |    3     |      4

Cột CSV invoice_items và chỉ số tương ứng:
    Cột:  invoice_id | product_id | quantity | unit_price
    Index:     0      |     1      |    2     |     3

Format đầu vào items_data (List[List], KHÔNG dùng Dict):
    Mỗi phần tử: [product_id, quantity]  ví dụ: ['P001', 3]

Lógic tính tiền:
    subtotal     = Σ (quantity × unit_price)
    discount_amt = subtotal × discount_rate
    after_disc   = subtotal - discount_amt
    vat_amount   = after_disc × vat_rate
    total_amount = after_disc + vat_amount
"""

from datetime import datetime
from typing import Optional

from models import Invoice, InvoiceItem
from utils.data_structures import ArrayList
from utils.file_storage import (
    read_csv, append_row, write_csv,
    delete_rows_by_key, get_max_id,
    initialize_csv_files
)
from utils.validation import validate_required_field, validate_date_format, validate_quantity
from utils.formatting import format_date
from .product_manager import ProductManager

# Hằng số nghiệp vụ
DEFAULT_VAT_RATE      = 0.10   # Thuế VAT 10%
DEFAULT_DISCOUNT_RATE = 0.0    # Không chiết khấu mặc định

# Chỉ số (index) của từng cột trong file data/invoices.csv
_INV_COL_ID        = 0    # invoice_id
_INV_COL_CNAME     = 1    # customer_name
_INV_COL_DATE      = 2    # date
_INV_COL_VAT       = 3    # vat_rate
_INV_COL_DISCOUNT  = 4    # discount_rate

# Chỉ số (index) của từng cột trong file data/invoice_items.csv
_ITEM_COL_INV_ID   = 0    # invoice_id (khóa ngoại tham chiếu invoices)
_ITEM_COL_PROD_ID  = 1    # product_id
_ITEM_COL_QTY      = 2    # quantity
_ITEM_COL_PRICE    = 3    # unit_price (snapshot giá lúc lập hóa đơn)


def _row_to_invoice_item(row) -> InvoiceItem:
    """Chuyển dòng CSV invoice_items thành đối tượng InvoiceItem."""
    product_id = row[_ITEM_COL_PROD_ID].strip()
    try:
        quantity = int(row[_ITEM_COL_QTY].strip())
    except (ValueError, IndexError):
        quantity = 0
    try:
        unit_price = float(row[_ITEM_COL_PRICE].strip())
    except (ValueError, IndexError):
        unit_price = 0.0
    return InvoiceItem(product_id=product_id, quantity=quantity, unit_price=unit_price)


def _row_to_invoice(inv_row, items: ArrayList) -> Invoice:
    """Chuyển dòng CSV invoices + danh sách items thành đối tượng Invoice."""
    invoice_id    = inv_row[_INV_COL_ID].strip()
    customer_name = inv_row[_INV_COL_CNAME].strip()
    date          = inv_row[_INV_COL_DATE].strip()
    try:
        vat_rate = float(inv_row[_INV_COL_VAT].strip())
    except (ValueError, IndexError):
        vat_rate = DEFAULT_VAT_RATE
    try:
        discount_rate = float(inv_row[_INV_COL_DISCOUNT].strip())
    except (ValueError, IndexError):
        discount_rate = DEFAULT_DISCOUNT_RATE
    return Invoice(
        invoice_id=invoice_id,
        customer_name=customer_name,
        date=date,
        items=items,
        vat_rate=vat_rate,
        discount_rate=discount_rate,
    )


class InvoiceManager:
    """
    Quản lý toàn bộ thao tác với hóa đơn.

    Thuộc tính:
        product_manager (ProductManager): Dùng để tra cứu thông tin sản phẩm.
        invoices (List[Invoice])        : Danh sách hóa đơn trong bộ nhớ.
    """

    def __init__(self, product_manager: ProductManager):
        """
        Khởi tạo InvoiceManager.

        Tham số:
            product_manager: Đối tượng ProductManager đã được khởi tạo,
                             dùng để tìm sản phẩm khi tạo/hiển thị hóa đơn.
        """
        self.product_manager = product_manager
        self.invoices = ArrayList()
        initialize_csv_files()    # Đảm bảo file CSV đã tồn tại
        self.load_invoices()      # Nạp toàn bộ hóa đơn vào bộ nhớ

    # TẢI DỮ LIỆU (MASTER-DETAIL)
    def load_invoices(self) -> tuple:
        """
        Tải toàn bộ hóa đơn và chi tiết từ 2 file CSV vào self.invoices.

        Quy trình Master-Detail:
        1. Đọc tất cả dòng từ invoices.csv        → danh sách Master
        2. Đọc tất cả dòng từ invoice_items.csv   → danh sách Detail
        3. Với mỗi hóa đơn, dùng Linear Search lọc Detail theo invoice_id
        4. Ghép Detail vào Invoice tương ứng

        Trả về:
            (True, thông báo) hoặc (False, lỗi).
        """
        self.invoices = ArrayList()
        try:
            # Bước 1: Đọc tất cả hóa đơn (Master)
            inv_rows = read_csv("invoices")
            # Bước 2: Đọc tất cả chi tiết hóa đơn (Detail)
            item_rows = read_csv("invoice_items")

            for inv_row in inv_rows:
                if len(inv_row) < 3:
                    continue
                invoice_id = inv_row[_INV_COL_ID].strip()

                # Bước 3: Lọc chi tiết theo invoice_id bằng Linear Search
                items = ArrayList()
                for item_row in item_rows:
                    if (len(item_row) > _ITEM_COL_INV_ID and
                            item_row[_ITEM_COL_INV_ID].strip() == invoice_id):
                        items.append(_row_to_invoice_item(item_row))

                # Bước 4: Ghép Master + Detail
                invoice = _row_to_invoice(inv_row, items)
                self.invoices.append(invoice)

            return True, f"Đã tải {len(self.invoices)} hóa đơn."
        except Exception as e:
            return False, f"Lỗi khi tải hóa đơn: {e}"

    # TẠO HÓA ĐƠN MỚI
    def create_invoice(self, customer_name: str,
                       items_data,
                       date: Optional[str] = None,
                       vat_rate: float = DEFAULT_VAT_RATE,
                       discount_rate: float = DEFAULT_DISCOUNT_RATE
                       ) -> tuple:
        """
        Tạo hóa đơn mới với tính toán VAT và chiết khấu.

        Tham số:
            customer_name  : Tên khách hàng.
            items_data     : Danh sách các mặt hàng — mỗi phần tử là
                             [product_id, quantity] (list 2 phần tử).
            date           : Ngày lập hóa đơn (YYYY-MM-DD), mặc định hôm nay.
            vat_rate       : Thuế suất VAT, mặc định 0.10 (10%).
            discount_rate  : Tỷ lệ chiết khấu, mặc định 0.0 (0%).

        Trả về:
            (Invoice, thông báo thành công) hoặc (None, thông báo lỗi).

        """
        # Bước 1: Xác thực đầu vào
        valid, error = validate_required_field(customer_name, "Tên khách hàng")
        if not valid:
            return None, error
        if not items_data:
            return None, "Hóa đơn phải có ít nhất một mặt hàng."

        invoice_date = date if date else datetime.now().strftime('%Y-%m-%d')
        valid, error = validate_date_format(invoice_date, "Ngày hóa đơn")
        if not valid:
            return None, error

        if not (0.0 <= vat_rate <= 1.0):
            return None, "Thuế VAT phải nằm trong khoảng 0% đến 100%."
        if not (0.0 <= discount_rate <= 1.0):
            return None, "Chiết khấu phải nằm trong khoảng 0% đến 100%."

        # Giữ nguyên tên khách hàng (chỉ cắt khoảng trắng thừa) để đồng bộ
        # với tên đã lưu trong bảng khách hàng, tránh sai lệch khi thống kê.
        customer_name = customer_name.strip()

        # Xác thực từng dòng mặt hàng
        # items_data[i] = [product_id, quantity]
        for item in items_data:
            pid = item[0]
            qty = item[1]
            valid, error = validate_quantity(qty)
            if not valid:
                return None, error
            if not self.product_manager.find_product(pid):
                return None, f"Sản phẩm '{pid}' không tồn tại."

        # Bước 2: Tạo invoice_id mới (max hiện tại + 1)
        new_invoice_id = get_max_id("invoices", _INV_COL_ID) + 1
        new_invoice_id_str = str(new_invoice_id)

        # Bước 3: Ghi hóa đơn vào invoices.csv
        inv_row = ArrayList((
            new_invoice_id_str,
            customer_name,
            invoice_date,
            str(vat_rate),
            str(discount_rate),
        ))
        ok = append_row("invoices", inv_row)
        if not ok:
            return None, "Không thể ghi vào file invoices.csv."

        # Bước 4: Ghi từng dòng mặt hàng vào invoice_items.csv
        for item in items_data:
            pid = item[0]
            qty = item[1]
            product = self.product_manager.find_product(pid)
            # Snapshot giá tại thời điểm lập hóa đơn
            item_row = ArrayList((
                new_invoice_id_str,
                pid,
                str(qty),
                str(product.unit_price),
            ))
            ok = append_row("invoice_items", item_row)
            if not ok:
                return None, f"Không thể ghi mặt hàng '{pid}' vào invoice_items.csv."

        # Bước 5: Reload và trả về hóa đơn vừa tạo
        self.load_invoices()
        new_invoice = self.find_invoice(new_invoice_id_str)
        if new_invoice:
            return new_invoice, (
                f"Đã tạo hóa đơn #{new_invoice.invoice_id} "
                f"cho khách hàng '{customer_name}' thành công!\n"
                f"Tiền hàng: {new_invoice.subtotal:,.0f} VNĐ | "
                f"Chiết khấu: {new_invoice.discount_amount:,.0f} VNĐ | "
                f"VAT ({vat_rate*100:.0f}%): {new_invoice.vat_amount:,.0f} VNĐ | "
                f"Tổng phải trả: {new_invoice.total_amount:,.0f} VNĐ"
            )
        return None, "Không thể tạo hóa đơn."

    # TÌM HÓA ĐƠN — LINEAR SEARCH
    def find_invoice(self, invoice_id: str) -> Optional[Invoice]:
        """
        Tìm hóa đơn theo ID bằng Linear Search.

        Duyệt tuần tự qua self.invoices từ đầu đến cuối.
        Độ phức tạp: O(n).

        Tham số:
            invoice_id: Mã hóa đơn cần tìm.

        Trả về:
            Invoice nếu tìm thấy, None nếu không.
        """
        for invoice in self.invoices:       # Duyệt từng phần tử
            if invoice.invoice_id == invoice_id:
                return invoice              # Tìm thấy → trả về ngay
        return None                         # Không tìm thấy

    # XÓA HÓA ĐƠN
    def delete_invoice(self, invoice_id: str) -> tuple:
        """
        Xóa hóa đơn và toàn bộ chi tiết liên quan.

        Quy trình:
        1. Kiểm tra hóa đơn tồn tại (Linear Search).
        2. Xóa tất cả dòng trong invoice_items.csv có invoice_id tương ứng.
        3. Xóa dòng trong invoices.csv.
        4. Reload.

        Tham số:
            invoice_id: Mã hóa đơn cần xóa.

        Trả về:
            (True, thông báo) hoặc (False, lỗi).
        """
        # Bước 1: Kiểm tra tồn tại
        invoice = self.find_invoice(invoice_id)
        if not invoice:
            return False, f"Không tìm thấy hóa đơn '{invoice_id}'!"

        try:
            # Bước 2: Xóa tất cả chi tiết (invoice_items)
            delete_rows_by_key("invoice_items", _ITEM_COL_INV_ID, invoice_id)

            # Bước 3: Xóa hóa đơn (invoices)
            rows = read_csv("invoices")
            new_rows = ArrayList()
            found = False
            for row in rows:
                if len(row) > _INV_COL_ID and row[_INV_COL_ID].strip() == invoice_id:
                    found = True
                else:
                    new_rows.append(row)
            if not found:
                return False, f"Không tìm thấy hóa đơn '{invoice_id}' trong file CSV!"
            ok = write_csv("invoices", new_rows)
            if not ok:
                return False, "Không thể ghi vào file invoices.csv."

            # Bước 4: Reload
            self.load_invoices()
            return True, f"Đã xóa hóa đơn #{invoice_id} của '{invoice.customer_name}' thành công!"

        except Exception as e:
            return False, f"Lỗi khi xóa hóa đơn: {e}"
    # HIỂN THỊ (CLI)
    def view_invoice_detail(self, invoice_id: str) -> None:
        """Hiển thị chi tiết hóa đơn kèm VAT và chiết khấu (dùng cho CLI)."""
        invoice = self.find_invoice(invoice_id)
        if not invoice:
            print(f"Không tìm thấy hóa đơn #{invoice_id}.")
            return

        print("\n" + "="*70)
        print(f"  CHI TIẾT HÓA ĐƠN #{invoice.invoice_id}")
        print(f"  Khách hàng : {invoice.customer_name}")
        print(f"  Ngày       : {format_date(invoice.date)}")
        print("="*70)
        print(f"{'MÃ SP':<10} {'TÊN SẢN PHẨM':<28} {'SL':>4} {'ĐƠN GIÁ':>12} {'THÀNH TIỀN':>12}")
        print("-"*70)
        for item in invoice.items:
            product = self.product_manager.find_product(item.product_id)
            name = product.name if product else "[Đã xóa]"
            print(f"{item.product_id:<10} {name:<28} {item.quantity:>4} "
                  f"{item.unit_price:>12,.0f} {item.total_price:>12,.0f}")
        print("-"*70)
        print(f"{'Tiền hàng:':<55} {invoice.subtotal:>12,.0f}")
        if invoice.discount_rate > 0:
            print(f"{'Chiết khấu (' + str(int(invoice.discount_rate*100)) + '%):':<55} "
                  f"-{invoice.discount_amount:>11,.0f}")
        print(f"{'VAT (' + str(int(invoice.vat_rate*100)) + '%):':<55} "
              f"{invoice.vat_amount:>12,.0f}")
        print("="*70)
        print(f"{'TỔNG TIỀN KHÁCH PHẢI TRẢ:':<55} {invoice.total_amount:>12,.0f}")
        print("="*70)

    def list_invoices(self) -> None:
        """Hiển thị danh sách hóa đơn (dùng cho CLI)."""
        if not self.invoices:
            print("Danh sách hóa đơn trống!")
            return
        print("\n" + "="*70)
        print(f"{'MÃ HĐ':<8} {'KHÁCH HÀNG':<25} {'NGÀY':<12} {'SL':>5} {'TỔNG TIỀN':>12}")
        print("-"*70)
        for inv in self.invoices:
            print(f"#{inv.invoice_id:<7} {inv.customer_name:<25} {format_date(inv.date):<12} "
                  f"{inv.total_items:>5} {inv.total_amount:>12,.0f}")
        print("="*70)
        print(f"Tổng số: {len(self.invoices)} hóa đơn")
        print("="*70)

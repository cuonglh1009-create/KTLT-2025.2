"""
models/invoice.py
Mô hình dữ liệu Hóa đơn — Master-Detail record.

Cấu trúc Master-Detail:
    Master : Invoice      — thông tin chung của hóa đơn (khách hàng, ngày, VAT, chiết khấu)
    Detail : InvoiceItem  — từng dòng mặt hàng trong hóa đơn (sản phẩm, SL, đơn giá)

Logic tính tiền:
    subtotal     = Σ (quantity × unit_price) của tất cả InvoiceItem
    discount_amt = subtotal × discount_rate          (chiết khấu theo %)
    after_disc   = subtotal - discount_amt
    vat_amount   = after_disc × vat_rate             (thuế VAT theo %)
    total_amount = after_disc + vat_amount           (số tiền khách phải trả)
"""

from dataclasses import dataclass, field
import datetime

from utils.data_structures import ArrayList

# Hằng số mặc định
DEFAULT_VAT_RATE      = 0.10   # Thuế VAT mặc định: 10%
DEFAULT_DISCOUNT_RATE = 0.0    # Chiết khấu mặc định: 0%


@dataclass
class InvoiceItem:
    """
    Mô hình dữ liệu một dòng mặt hàng trong hóa đơn (Detail record).

    Thuộc tính:
        product_id (str)  : Mã sản phẩm (khóa ngoại tham chiếu bảng products).
        quantity   (int)  : Số lượng mua.
        unit_price (float): Đơn giá tại thời điểm lập hóa đơn
                            (lưu riêng để không bị ảnh hưởng khi giá SP thay đổi sau này).
    """
    product_id: str
    quantity:   int
    unit_price: float

    @property
    def total_price(self) -> float:
        """
        Tính thành tiền của dòng mặt hàng này.

        Công thức: total_price = quantity × unit_price

        Trả về:
            float: Thành tiền chưa bao gồm VAT và chiết khấu.
        """
        return self.quantity * self.unit_price


@dataclass
class Invoice:
    """
    Mô hình dữ liệu Hóa đơn (Master record).

    Thuộc tính:
        invoice_id     (str)             : Mã hóa đơn (tự tăng từ DB).
        customer_name  (str)             : Tên khách hàng.
        items          (List[InvoiceItem]): Danh sách các dòng mặt hàng (Detail).
        date           (str)             : Ngày lập hóa đơn (định dạng YYYY-MM-DD).
        vat_rate       (float)           : Thuế suất VAT (mặc định 10% = 0.10).
        discount_rate  (float)           : Tỷ lệ chiết khấu (mặc định 0%).
    """
    invoice_id:    str
    customer_name: str
    items:         ArrayList = field(default_factory=ArrayList)
    date:          str   = field(default_factory=lambda: datetime.datetime.now().strftime('%Y-%m-%d'))
    vat_rate:      float = DEFAULT_VAT_RATE
    discount_rate: float = DEFAULT_DISCOUNT_RATE

    # CÁC PROPERTY TÍNH TIỀN TỰ ĐỘNG

    @property
    def subtotal(self) -> float:
        """
        Tổng tiền hàng trước chiết khấu và VAT.

        Công thức: subtotal = Σ item.total_price  (duyệt qua tất cả InvoiceItem)
        """
        total = 0.0
        for item in self.items:
            total = total + item.total_price
        return total

    @property
    def discount_amount(self) -> float:
        """
        Số tiền chiết khấu.

        Công thức: discount_amount = subtotal × discount_rate
        Ví dụ: subtotal=1.000.000, discount_rate=0.05 → discount_amount=50.000
        """
        return self.subtotal * self.discount_rate

    @property
    def after_discount(self) -> float:
        """
        Tổng tiền sau khi áp dụng chiết khấu (trước VAT).

        Công thức: after_discount = subtotal - discount_amount
        """
        return self.subtotal - self.discount_amount

    @property
    def vat_amount(self) -> float:
        """
        Số tiền thuế VAT.

        Công thức: vat_amount = after_discount × vat_rate
        Ví dụ: after_discount=950.000, vat_rate=0.10 → vat_amount=95.000
        """
        return self.after_discount * self.vat_rate

    @property
    def total_amount(self) -> float:
        """
        Tổng số tiền khách phải trả (sau chiết khấu và sau VAT).

        Công thức: total_amount = after_discount + vat_amount
        Đây là con số cuối cùng hiển thị trên hóa đơn.
        """
        return self.after_discount + self.vat_amount

    @property
    def total_items(self) -> int:
        """
        Tổng số lượng mặt hàng trong hóa đơn.

        Công thức: total_items = Σ item.quantity
        """
        total = 0
        for item in self.items:
            total = total + item.quantity
        return total

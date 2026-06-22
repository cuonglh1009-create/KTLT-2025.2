"""
Gói models chứa các mô hình dữ liệu cho Hệ thống Quản lý Hóa đơn.

Gói này export các dataclass chính:
- Product: Mô hình sản phẩm
- Invoice: Mô hình hóa đơn
- InvoiceItem: Mô hình mục hàng trong hóa đơn
"""

from .product import Product
from .invoice import Invoice, InvoiceItem

__all__ = ['Product', 'Invoice', 'InvoiceItem'] 
from models.customer import Customer

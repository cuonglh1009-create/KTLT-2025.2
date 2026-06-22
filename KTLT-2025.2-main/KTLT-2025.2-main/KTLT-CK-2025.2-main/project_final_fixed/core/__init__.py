"""
Gói core chứa business logic chính cho Hệ thống Quản lý Hóa đơn.

Gói này chứa các manager classes:
- ProductManager: Quản lý sản phẩm
- InvoiceManager: Quản lý hóa đơn
- StatisticsManager: Quản lý thống kê và báo cáo
"""

from .product_manager import ProductManager
from .invoice_manager import InvoiceManager
from .statistics_manager import StatisticsManager

__all__ = [
    'ProductManager',
    'InvoiceManager',
    'StatisticsManager'
] 
from core.customer_manager import CustomerManager

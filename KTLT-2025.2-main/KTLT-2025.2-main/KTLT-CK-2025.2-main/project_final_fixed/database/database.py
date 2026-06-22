"""
database/database.py
Khởi tạo và quản lý cơ sở dữ liệu dạng text (CSV).

Cấu trúc lưu trữ (CSV phân cách bằng '|'):
    data/products.csv      — Danh mục sản phẩm
    data/customers.csv     — Danh sách khách hàng
    data/invoices.csv      — Hóa đơn (Master)
    data/invoice_items.csv — Chi tiết hóa đơn (Detail)
"""

import os
import sys

# Đảm bảo import được utils khi chạy trực tiếp hoặc qua package
try:
    from utils.file_storage import initialize_csv_files, read_csv, write_csv, DATA_DIR
except ImportError:
    try:
        from ..utils.file_storage import initialize_csv_files, read_csv, write_csv, DATA_DIR
    except ImportError:
        parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        from utils.file_storage import initialize_csv_files, read_csv, write_csv, DATA_DIR

# Định nghĩa các biến đường dẫn để duy trì tương thích ngược
DATABASE_NAME = "data"
DATABASE_PATH = DATA_DIR


def initialize_database():
    """
    Khởi tạo toàn bộ cấu trúc cơ sở dữ liệu bằng các file text CSV.
    Nạp dữ liệu mẫu (sản phẩm, khách hàng) khi chạy lần đầu nếu dữ liệu trống.

    Trả về:
        (True, thông báo) nếu thành công.
        (False, lỗi)      nếu có lỗi.
    """
    try:
        # 1. Đảm bảo các file CSV đã được khởi tạo
        success, message = initialize_csv_files()
        if not success:
            return False, f"Không thể khởi tạo file CSV: {message}"

        # 2. Nạp dữ liệu mẫu cho khách hàng nếu trống
        customers = read_csv("customers")
        if not customers:
            sample_customers = (
                ("KH001", "Lê Hùng Cường", "0901234567", "Bắc Ninh"),
                ("KH002", "Hoàng Văn Quân", "0912345678", "Hà Nội"),
                ("KH003", "Nguyễn Tuấn Nam", "0923456789", "Hải Phòng"),
                ("KH004", "Phạm Thị Dung", "0934567890", "Vĩnh Phúc"),
                ("KH005", "Hoàng Văn Em", "0945678901", "Hải Phòng"),
            )
            if not write_csv("customers", sample_customers):
                return False, "Không thể ghi dữ liệu mẫu khách hàng."

        # 3. Nạp dữ liệu mẫu cho sản phẩm nếu trống
        products = read_csv("products")
        if not products:
            sample_products = (
                ("P001", "Máy tính xách tay", "1200", "chiếc", "Thiết bị điện tử"),
                ("P002", "Bàn phím cơ", "26", "cái", "Phụ kiện"),
                ("P003", "Bộ giá đỡ máy tính", "45", "bộ", "Phụ kiện"),
                ("P004", "Bàn làm việc", "151", "cái", "Nội thất"),
                ("P005", "Hạt hướng dương", "15", "gói", "Thực phẩm"),
                ("P006", "Vở ghi", "4", "quyển", "Văn phòng phẩm"),
            )
            if not write_csv("products", sample_products):
                return False, "Không thể ghi dữ liệu mẫu sản phẩm."

        return True, f"Cơ sở dữ liệu dạng text/CSV đã được khởi tạo thành công tại: {DATABASE_PATH}"

    except Exception as e:
        return False, f"Lỗi khi khởi tạo cơ sở dữ liệu: {e}"


if __name__ == '__main__':
    print("Đang tiến hành khởi tạo database dạng text...")
    success, message = initialize_database()
    print(message)


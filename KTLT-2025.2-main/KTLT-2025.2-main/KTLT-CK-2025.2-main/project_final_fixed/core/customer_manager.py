"""
core/customer_manager.py
Tầng xử lý nghiệp vụ: Quản lý khách hàng.

Lớp CustomerManager chịu trách nhiệm toàn bộ logic liên quan đến khách hàng:
    • Tải, thêm, sửa, xóa khách hàng từ file data/customers.csv
    • Kiểm tra trùng mã khách hàng bằng thuật toán Linear Search
    • Tìm kiếm khách hàng bằng thuật toán Linear Search

Lưu trữ:
    File CSV: data/customers.csv (phân cách '|')

Cột CSV và chỉ số tương ứng:
    Cột:  customer_id | name | phone | address
    Index:      0      |  1   |   2   |    3
"""

from typing import Optional
from models import Customer
from utils.data_structures import ArrayList
from utils.validation import validate_required_field, validate_string_length
from utils.file_storage import (
    read_csv, append_row, write_csv, initialize_csv_files
)

# Chỉ số (index) của từng cột trong file data/customers.csv
# Duy trì hằng số giúp code rõ ý nghĩa khi truy cập row[index]
_COL_ID      = 0    # customer_id
_COL_NAME    = 1    # name
_COL_PHONE   = 2    # phone
_COL_ADDRESS = 3    # address


def _row_to_customer(row) -> Customer:
    """Chuyển một dòng CSV (list[str]) thành đối tượng Customer."""
    cid     = row[_COL_ID].strip()
    name    = row[_COL_NAME].strip()
    phone   = row[_COL_PHONE].strip()   if len(row) > _COL_PHONE   else ""
    address = row[_COL_ADDRESS].strip() if len(row) > _COL_ADDRESS else ""
    return Customer(customer_id=cid, name=name, phone=phone, address=address)


def _customer_to_row(customer: Customer):
    """Chuyển đối tượng Customer thành dòng CSV (ArrayList[str])."""
    return ArrayList((
        customer.customer_id,
        customer.name,
        customer.phone,
        customer.address,
    ))


class CustomerManager:
    """
    Quản lý toàn bộ thao tác CRUD với khách hàng.

    Thuộc tính:
        customers (List[Customer]): Danh sách khách hàng trong bộ nhớ,
                                    được tải từ file CSV.
    """

    def __init__(self):
        """
        Khởi tạo CustomerManager.
        - Đảm bảo file CSV tồn tại.
        - Tải toàn bộ khách hàng vào self.customers.
        """
        self.customers = ArrayList()
        initialize_csv_files()    # Tạo file CSV nếu chưa có
        self.load_customers()     # Nạp dữ liệu vào bộ nhớ

    # TẢI DỮ LIỆU

    def load_customers(self) -> tuple:
        """
        Tải toàn bộ khách hàng từ file CSV vào self.customers.

        Trả về:
            (True, thông báo) nếu thành công.
            (False, lỗi)      nếu thất bại.
        """
        self.customers = ArrayList()
        try:
            rows = read_csv("customers")
            for row in rows:
                if len(row) >= 2:   # Ít nhất phải có ID và tên
                    self.customers.append(_row_to_customer(row))
            return True, f"Đã tải {len(self.customers)} khách hàng."
        except Exception as e:
            return False, f"Lỗi khi tải khách hàng: {e}"

    # THUẬT TOÁN CÀI ĐẶT: TÌM KIẾM TUYẾN TÍNH (LINEAR SEARCH)
    # Mục đích: Kiểm tra trùng mã ID và tìm kiếm khách hàng.

    def linear_search(self, customer_id: str) -> int:
        """
        Thuật toán Tìm kiếm tuyến tính (Linear Search).

        Duyệt tuần tự từ đầu đến cuối danh sách self.customers,
        so sánh từng phần tử với customer_id cần tìm.

        Tham số:
            customer_id (str): Mã khách hàng cần tìm (đã upper).

        Trả về:
            int: Chỉ số (index) nếu tìm thấy.
                 -1 nếu không tìm thấy.
        """
        for i in range(len(self.customers)):            # Duyệt từ đầu đến cuối
            if self.customers[i].customer_id == customer_id:
                return i                                # Tìm thấy → trả về vị trí
        return -1                                       # Không tìm thấy → trả về -1

    def find_customer(self, customer_id: str) -> Optional[Customer]:
        """
        Tìm khách hàng theo mã ID, sử dụng Linear Search.

        Tham số:
            customer_id (str): Mã khách hàng cần tìm.

        Trả về:
            Customer nếu tìm thấy, None nếu không.
        """
        index = self.linear_search(customer_id.upper())   # Chuẩn hóa và tìm kiếm
        return self.customers[index] if index != -1 else None

    # THÊM KHÁCH HÀNG
    def add_customer(self, customer_id: str, name: str,
                     phone: str = "", address: str = "") -> tuple:
        """
        Thêm khách hàng mới vào hệ thống.

        Quy trình:
        1. Xác thực mã và tên khách hàng.
        2. Dùng Linear Search kiểm tra mã đã tồn tại chưa.
        3. Ghi dòng mới vào file CSV.
        4. Reload danh sách.

        Tham số:
            customer_id : Mã khách hàng (sẽ được chuyển thành chữ hoa).
            name        : Họ tên khách hàng (2–50 ký tự).
            phone       : Số điện thoại (tùy chọn).
            address     : Địa chỉ (tùy chọn).

        Trả về:
            (True, thông báo) hoặc (False, lỗi).
        """
        # Bước 1: Xác thực dữ liệu
        valid, error = validate_required_field(customer_id, "Mã khách hàng")
        if not valid:
            return False, error
        valid, error = validate_required_field(name, "Tên khách hàng")
        if not valid:
            return False, error
        valid, error = validate_string_length(name, "Tên khách hàng", 2, 50)
        if not valid:
            return False, error

        cid = customer_id.strip().upper()   # Chuẩn hóa mã khách hàng

        # Bước 2: Kiểm tra trùng mã bằng Linear Search
        if self.find_customer(cid):
            return False, f"Mã khách hàng '{cid}' đã tồn tại!"

        # Bước 3: Ghi vào file CSV
        new_row = ArrayList((cid, name.strip(), phone.strip(), address.strip()))
        ok = append_row("customers", new_row)
        if not ok:
            return False, "Không thể ghi vào file customers.csv."

        # Bước 4: Reload
        self.load_customers()
        return True, f"Đã thêm khách hàng '{name}' thành công!"

    # CẬP NHẬT KHÁCH HÀNG
    def update_customer(self, customer_id: str, name: str = None,
                        phone: str = None, address: str = None) -> tuple:
        """
        Cập nhật thông tin khách hàng (không đổi mã ID).

        Quy trình:
        1. Kiểm tra khách hàng tồn tại (Linear Search).
        2. Xác thực tên nếu được cập nhật.
        3. Đọc toàn bộ CSV, sửa dòng cần thiết, ghi lại.

        Trả về:
            (True, thông báo) hoặc (False, lỗi).
        """
        cid = customer_id.strip().upper()

        # Bước 1: Kiểm tra tồn tại
        existing = self.find_customer(cid)
        if not existing:
            return False, f"Không tìm thấy khách hàng '{cid}'!"

        # Bước 2: Xác thực name nếu được cập nhật
        if name is not None:
            valid, error = validate_string_length(name, "Tên khách hàng", 2, 50)
            if not valid:
                return False, error

        # Bước 3: Xây dựng dòng mới (giữ nguyên các trường không thay đổi)
        new_name    = name.strip()    if name    is not None else existing.name
        new_phone   = phone.strip()   if phone   is not None else existing.phone
        new_address = address.strip() if address is not None else existing.address

        new_row = ArrayList((cid, new_name, new_phone, new_address))

        # Đọc tất cả dòng CSV, thay dòng có cùng customer_id
        rows = read_csv("customers")
        found = False
        for i in range(len(rows)):
            if len(rows[i]) > _COL_ID and rows[i][_COL_ID].strip() == cid:
                rows[i] = new_row
                found = True
                break
        if not found:
            return False, f"Không tìm thấy khách hàng '{cid}' trong file CSV!"

        ok = write_csv("customers", rows)
        if not ok:
            return False, "Không thể ghi vào file customers.csv."

        self.load_customers()
        return True, f"Đã cập nhật khách hàng '{cid}' thành công!"
    # XÓA KHÁCH HÀNG
    def delete_customer(self, customer_id: str) -> tuple:
        """
        Xóa khách hàng khỏi hệ thống.

        Quy trình:
        1. Kiểm tra khách hàng tồn tại (Linear Search).
        2. Đọc CSV, loại bỏ dòng cần xóa, ghi lại.

        Trả về:
            (True, thông báo) hoặc (False, lỗi).
        """
        cid = customer_id.strip().upper()

        # Bước 1: Kiểm tra tồn tại
        if not self.find_customer(cid):
            return False, f"Không tìm thấy khách hàng '{cid}'!"

        # Bước 2: Đọc tất cả và lọc bỏ dòng cần xóa
        rows = read_csv("customers")
        new_rows = ArrayList()
        found = False
        for row in rows:
            if len(row) > _COL_ID and row[_COL_ID].strip() == cid:
                found = True
            else:
                new_rows.append(row)

        if not found:
            return False, f"Không tìm thấy khách hàng '{cid}' trong file CSV!"

        ok = write_csv("customers", new_rows)
        if not ok:
            return False, "Không thể ghi vào file customers.csv."

        self.load_customers()
        return True, f"Đã xóa khách hàng '{cid}' thành công!"

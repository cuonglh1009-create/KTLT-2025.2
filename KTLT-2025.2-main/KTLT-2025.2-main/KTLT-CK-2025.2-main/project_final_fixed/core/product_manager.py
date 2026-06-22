"""
core/product_manager.py
Tầng xử lý nghiệp vụ: Quản lý sản phẩm.

Lớp ProductManager chịu trách nhiệm toàn bộ logic liên quan đến sản phẩm:
    • Tải, thêm, sửa, xóa sản phẩm từ file data/products.csv
    • Kiểm tra trùng mã sản phẩm bằng thuật toán Linear Search
    • Tìm kiếm sản phẩm theo mã ID bằng thuật toán Linear Search

Lưu trữ:
    File CSV: data/products.csv (phân cách '|')

Cột CSV và chỉ số tương ứng:
    Cột:  product_id | name | unit_price | calculation_unit | category
    Index:     0      |  1   |     2      |        3         |    4
"""

from typing import Optional

from models import Product
from utils.data_structures import ArrayList
from utils.validation import (
    validate_required_field,
    validate_positive_number,
    validate_product_id,
    validate_string_length,
)
from utils.formatting import format_product_id
from utils.file_storage import (
    read_csv, append_row, write_csv, initialize_csv_files
)

# Chỉ số (index) của từng cột trong file data/products.csv
# Duy trì hằng số giúp code rõ ý nghĩa khi truy cập row[index]
_COL_ID    = 0    # product_id
_COL_NAME  = 1    # name
_COL_PRICE = 2    # unit_price
_COL_UNIT  = 3    # calculation_unit
_COL_CAT   = 4    # category


def _row_to_product(row) -> Product:
    """Chuyển một dòng CSV (list[str]) thành đối tượng Product."""
    pid   = row[_COL_ID].strip()
    name  = row[_COL_NAME].strip()
    try:
        price = float(row[_COL_PRICE].strip())
    except (ValueError, IndexError):
        price = 0.0
    unit  = row[_COL_UNIT].strip() if len(row) > _COL_UNIT else "đơn vị"
    cat   = row[_COL_CAT].strip()  if len(row) > _COL_CAT  else "Chung"
    return Product(product_id=pid, name=name, unit_price=price,
                   calculation_unit=unit, category=cat)


def _product_to_row(product: Product):
    """Chuyển đối tượng Product thành dòng CSV (ArrayList[str])."""
    return ArrayList((
        product.product_id,
        product.name,
        str(product.unit_price),
        product.calculation_unit,
        product.category,
    ))


class ProductManager:
    """
    Quản lý toàn bộ thao tác CRUD với sản phẩm.

    Thuộc tính:
        products (List[Product]): Danh sách sản phẩm đang giữ trong bộ nhớ,
                                  được tải từ file CSV mỗi khi có thay đổi.
    """

    def __init__(self):
        """
        Khởi tạo ProductManager.
        - Gọi initialize_csv_files() để đảm bảo file CSV đã tồn tại.
        - Tải toàn bộ sản phẩm vào self.products.
        """
        self.products = ArrayList()
        initialize_csv_files()    # Tạo file CSV nếu chưa có
        self.load_products()      # Nạp dữ liệu vào bộ nhớ
    # TẢI DỮ LIỆU

    def load_products(self) -> tuple:
        """
        Tải toàn bộ sản phẩm từ file CSV vào self.products.

        Trả về:
            (True, thông báo) nếu thành công.
            (False, lỗi)      nếu thất bại.
        """
        self.products = ArrayList()
        try:
            rows = read_csv("products")
            for row in rows:
                if len(row) >= 3:   # Ít nhất ID, tên, giá
                    self.products.append(_row_to_product(row))
            return True, f"Đã tải {len(self.products)} sản phẩm."
        except Exception as e:
            return False, f"Lỗi khi tải sản phẩm: {e}"

    # THUẬT TOÁN CÀI ĐẶT: TÌM KIẾM TUYẾN TÍNH (LINEAR SEARCH)
    # Mục đích: Kiểm tra trùng mã ID và tìm sản phẩm trong danh sách.
    def linear_search(self, product_id: str) -> int:
        """
        Thuật toán Tìm kiếm tuyến tính (Linear Search).

        Duyệt tuần tự qua danh sách self.products từ đầu đến cuối,
        so sánh từng phần tử với product_id cần tìm.

        Tham số:
            product_id (str): Mã sản phẩm cần tìm (đã chuẩn hóa).

        Trả về:
            int: Chỉ số (index) của sản phẩm nếu tìm thấy.
                 -1 nếu không tìm thấy.
        """
        for i in range(len(self.products)):              # Duyệt từ đầu đến cuối
            if self.products[i].product_id == product_id:
                return i                                 # Tìm thấy → trả về vị trí
        return -1                                        # Duyệt hết mà không thấy → -1

    def find_product(self, product_id: str) -> Optional[Product]:
        """
        Tìm sản phẩm theo mã ID, sử dụng Linear Search.

        Tham số:
            product_id (str): Mã sản phẩm cần tìm.

        Trả về:
            Product nếu tìm thấy, None nếu không.
        """
        product_id = format_product_id(product_id)   # Chuẩn hóa: strip + upper
        index = self.linear_search(product_id)         # Gọi Linear Search
        if index != -1:
            return self.products[index]               # Trả về sản phẩm tại vị trí index
        return None

    # THÊM SẢN PHẨM
    def add_product(self, product_id: str, name: str, unit_price: float,
                    calculation_unit: str = "đơn vị", category: str = "Chung") -> tuple:
        """
        Thêm sản phẩm mới vào hệ thống.

        Quy trình:
        1. Xác thực dữ liệu đầu vào (mã, tên, đơn giá).
        2. Dùng Linear Search kiểm tra mã đã tồn tại chưa.
        3. Ghi dòng mới vào file CSV.
        4. Reload danh sách.

        Tham số:
            product_id       : Mã sản phẩm (chỉ chữ hoa và số, 3–10 ký tự).
            name             : Tên sản phẩm (2–50 ký tự).
            unit_price       : Đơn giá (phải > 0).
            calculation_unit : Đơn vị tính (mặc định: "đơn vị").
            category         : Danh mục (mặc định: "Chung").

        Trả về:
            (True, thông báo thành công) hoặc (False, thông báo lỗi).
        """
        # Bước 1: Xác thực dữ liệu đầu vào
        valid, error = validate_product_id(product_id)
        if not valid:
            return False, error
        valid, error = validate_required_field(name, "Tên sản phẩm")
        if not valid:
            return False, error
        valid, error = validate_string_length(name, "Tên sản phẩm", 2, 50)
        if not valid:
            return False, error
        valid, error = validate_positive_number(unit_price, "Đơn giá")
        if not valid:
            return False, error

        # Bước 2: Kiểm tra trùng mã bằng Linear Search
        if self.find_product(product_id):
            return False, f"Sản phẩm với Mã '{product_id}' đã tồn tại!"

        product_id = format_product_id(product_id)   # Chuẩn hóa mã

        # Bước 3: Ghi vào file CSV
        new_row = ArrayList((product_id, name, str(unit_price), calculation_unit, category))
        ok = append_row("products", new_row)
        if not ok:
            return False, "Không thể ghi vào file products.csv."

        # Bước 4: Reload danh sách trong bộ nhớ
        self.load_products()
        return True, f"Đã thêm sản phẩm '{name}' thành công!"
    # CẬP NHẬT SẢN PHẨM
    def update_product(self, product_id: str, name: Optional[str] = None,
                       unit_price: Optional[float] = None,
                       calculation_unit: Optional[str] = None,
                       category: Optional[str] = None) -> tuple:
        """
        Cập nhật thông tin sản phẩm (không đổi mã ID).

        Quy trình:
        1. Dùng Linear Search kiểm tra sản phẩm có tồn tại không.
        2. Xác thực các trường được cập nhật.
        3. Đọc CSV, sửa dòng, ghi lại.

        Trả về:
            (True, thông báo thành công) hoặc (False, thông báo lỗi).
        """
        product_id = format_product_id(product_id)

        # Bước 1: Kiểm tra sản phẩm tồn tại
        existing = self.find_product(product_id)
        if not existing:
            return False, f"Không tìm thấy sản phẩm với Mã '{product_id}'!"

        # Bước 2: Xác thực các trường cần cập nhật
        if name is not None:
            valid, error = validate_string_length(name, "Tên sản phẩm", 2, 50)
            if not valid:
                return False, error
        if unit_price is not None:
            valid, error = validate_positive_number(unit_price, "Đơn giá")
            if not valid:
                return False, error

        # Bước 3: Xây dựng dòng mới
        new_name  = name             if name             is not None else existing.name
        new_price = unit_price       if unit_price        is not None else existing.unit_price
        new_unit  = calculation_unit if calculation_unit  is not None else existing.calculation_unit
        new_cat   = category         if category          is not None else existing.category

        new_row = ArrayList((product_id, new_name, str(new_price), new_unit, new_cat))

        # Đọc tất cả dòng CSV, thay dòng có cùng product_id
        rows = read_csv("products")
        found = False
        for i in range(len(rows)):
            if len(rows[i]) > _COL_ID and rows[i][_COL_ID].strip() == product_id:
                rows[i] = new_row
                found = True
                break
        if not found:
            return False, f"Không tìm thấy sản phẩm '{product_id}' trong file CSV!"

        ok = write_csv("products", rows)
        if not ok:
            return False, "Không thể ghi vào file products.csv."

        self.load_products()
        return True, f"Đã cập nhật sản phẩm '{product_id}' thành công!"

    # XÓA SẢN PHẨM
    def delete_product(self, product_id: str) -> tuple:
        """
        Xóa sản phẩm khỏi hệ thống.

        Quy trình:
        1. Kiểm tra sản phẩm tồn tại (Linear Search).
        2. Đọc CSV, loại bỏ dòng cần xóa, ghi lại.

        Trả về:
            (True, thông báo) hoặc (False, lỗi).
        """
        product_id = format_product_id(product_id)

        # Bước 1: Kiểm tra tồn tại
        if not self.find_product(product_id):
            return False, f"Không tìm thấy sản phẩm với Mã '{product_id}'!"

        # Bước 2: Đọc và lọc bỏ dòng cần xóa
        rows = read_csv("products")
        new_rows = ArrayList()
        found = False
        for row in rows:
            if len(row) > _COL_ID and row[_COL_ID].strip() == product_id:
                found = True
            else:
                new_rows.append(row)

        if not found:
            return False, f"Không tìm thấy sản phẩm '{product_id}' trong file CSV!"

        ok = write_csv("products", new_rows)
        if not ok:
            return False, "Không thể ghi vào file products.csv."

        self.load_products()
        return True, f"Đã xóa sản phẩm '{product_id}' thành công!"

    # HIỂN THỊ
    def list_products(self) -> None:
        """Hiển thị danh sách sản phẩm dạng bảng ra console."""
        if not self.products:
            print("Danh sách sản phẩm trống!")
            return
        print("\n" + "="*80)
        print(f"{'MÃ SP':<10} {'TÊN SẢN PHẨM':<30} {'ĐƠN VỊ':<10} {'DANH MỤC':<15} {'ĐƠN GIÁ':>10}")
        print("-"*80)
        for product in self.products:
            print(f"{product.product_id:<10} {product.name:<30} {product.calculation_unit:<10} "
                  f"{product.category:<15} {product.unit_price:>10,.2f}")
        print("="*80)
        print(f"Tổng số: {len(self.products)} sản phẩm")
        print("="*80)

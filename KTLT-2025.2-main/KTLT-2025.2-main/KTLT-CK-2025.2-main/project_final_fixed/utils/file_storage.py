"""
utils/file_storage.py
Tầng lưu trữ dữ liệu bằng file CSV thuần (text mode).
Mỗi bảng dữ liệu tương ứng một file CSV trong thư mục data/:
    data/customers.csv
    data/products.csv
    data/invoices.csv
    data/invoice_items.csv

Định dạng file:
- Dòng đầu tiên: header (tên cột, phân cách bằng ký tự '|')
- Các dòng tiếp theo: dữ liệu, mỗi trường cách nhau bằng '|'
- Dùng '|' thay vì ',' để tránh xung đột với dữ liệu tiếng Việt
- Toàn bộ giá trị lưu dưới dạng str; tầng gọi tự chuyển kiểu khi cần

Các hàm chính:
    initialize_csv_files()  — Tạo file CSV với header nếu chưa có (khởi động)
    read_csv(table)         — Đọc toàn bộ dữ liệu → list[list[str]]
    write_csv(table, rows)  — Ghi đè toàn bộ dữ liệu
    append_row(table, row)  — Thêm một dòng mới
    update_row(...)         — Cập nhật dòng theo khóa
    delete_row(...)         — Xóa một dòng theo khóa
    delete_rows_by_key(...) — Xóa nhiều dòng cùng khóa
    find_row(...)           — Tìm dòng đầu tiên khớp khóa
    find_rows(...)          — Tìm tất cả dòng khớp khóa
    get_max_id(...)         — Lấy ID lớn nhất 
"""

import os

from utils.data_structures import ArrayList, split_fields

# Thư mục chứa các file CSV
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

# Ký tự phân cách trường (dùng | để tránh xung đột với dấu phẩy trong tên)
SEP = "|"

# Schema cột của từng bảng — dùng 2 tuple song song (tuple bất biến, không phải
# cấu trúc dữ liệu động nên dùng cho hằng cấu hình; dữ liệu động dùng ArrayList)
# _TABLE_NAMES[i] khớp với _TABLE_HEADERS[i]
_TABLE_NAMES = ("customers", "products", "invoices", "invoice_items")
_TABLE_HEADERS = (
    ("customer_id", "name", "phone", "address"),                             # customers
    ("product_id", "name", "unit_price", "calculation_unit", "category"),    # products
    ("invoice_id", "customer_name", "date", "vat_rate", "discount_rate"),    # invoices
    ("invoice_id", "product_id", "quantity", "unit_price"),                  # invoice_items
)


def _get_table_index(table: str) -> int:
    """Trả về chỉ số bảng trong _TABLE_NAMES, hoặc -1 nếu không có."""
    for i in range(len(_TABLE_NAMES)):
        if _TABLE_NAMES[i] == table:
            return i
    return -1


def get_headers(table: str):
    """Trả về ArrayList tên cột của bảng. Trả về ArrayList rỗng nếu không có."""
    idx = _get_table_index(table)
    if idx == -1:
        return ArrayList()
    return ArrayList(_TABLE_HEADERS[idx])  # Bản sao để tránh sửa ngoài


def _get_file_path(table: str) -> str:
    """Trả về đường dẫn file CSV tương ứng với tên bảng."""
    return os.path.join(DATA_DIR, table + ".csv")


def _ensure_data_dir():
    """Tạo thư mục data/ nếu chưa tồn tại."""
    os.makedirs(DATA_DIR, exist_ok=True)


def _escape(value: str) -> str:
    """Loại bỏ ký tự SEP trong giá trị để tránh lỗi parse."""
    return str(value).replace(SEP, " ")


def _unescape(value: str) -> str:
    """Giải mã giá trị từ CSV (hiện tại chỉ strip)."""
    return value.strip()


# ĐỌC FILE CSV

def read_csv(table: str):
    """
    Đọc toàn bộ dữ liệu từ file CSV.

    Trả về:
        ArrayList[ArrayList[str]]: Mỗi phần tử là một dòng dữ liệu (bỏ header).
                                   ArrayList rỗng nếu file chưa có/chỉ có header.
    """
    path = _get_file_path(table)
    if not os.path.exists(path):
        return ArrayList()
    try:
        rows = ArrayList()
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        lines = split_fields(content, "\n")    # tự tách dòng thay readlines()
        # Bỏ qua dòng header (dòng đầu tiên, chỉ số 0)
        for i in range(1, len(lines)):
            line = lines[i].strip()
            if line == "":
                continue
            fields = split_fields(line, SEP)   # tự tách trường thay str.split
            rows.append(fields)
        return rows
    except IOError:
        return ArrayList()


def write_csv(table: str, rows) -> bool:
    """
    Ghi toàn bộ dữ liệu vào file CSV (ghi đè).

    Tham số:
        table : Tên bảng.
        rows  : list[list[str]] — mỗi phần tử là một dòng dữ liệu.

    Trả về:
        True nếu thành công, False nếu lỗi.
    """
    _ensure_data_dir()
    headers = get_headers(table)
    if not headers:
        return False
    path = _get_file_path(table)
    try:
        with open(path, "w", encoding="utf-8") as f:
            # Ghi header
            f.write(SEP.join(headers) + "\n")
            # Ghi từng dòng dữ liệu
            for row in rows:
                escaped = ArrayList()
                for val in row:
                    escaped.append(_escape(val))
                f.write(SEP.join(escaped) + "\n")
        return True
    except IOError:
        return False


# CÁC THAO TÁC CRUD TRÊN FILE

def append_row(table: str, row) -> bool:
    """
    Thêm một dòng mới vào cuối file CSV.

    Tham số:
        table : Tên bảng.
        row   : list[str] — giá trị các trường theo đúng thứ tự header.

    Trả về:
        True nếu thành công.
    """
    rows = read_csv(table)
    rows.append(row)
    return write_csv(table, rows)


def update_row(table: str, key_col_index: int, key_value: str, new_row) -> bool:
    """
    Cập nhật dòng có giá trị tại cột key_col_index bằng key_value.

    Tham số:
        table         : Tên bảng.
        key_col_index : Chỉ số cột khóa (0-based).
        key_value     : Giá trị khóa cần tìm.
        new_row       : list[str] — dòng mới thay thế.

    Trả về:
        True nếu tìm thấy và cập nhật thành công.
    """
    rows = read_csv(table)
    updated = False
    for i in range(len(rows)):
        if len(rows[i]) > key_col_index and rows[i][key_col_index].strip() == str(key_value).strip():
            rows[i] = new_row
            updated = True
            break
    if updated:
        return write_csv(table, rows)
    return False


def delete_row(table: str, key_col_index: int, key_value: str) -> bool:
    """
    Xóa dòng có giá trị tại cột key_col_index bằng key_value.

    Tham số:
        table         : Tên bảng.
        key_col_index : Chỉ số cột khóa (0-based).
        key_value     : Giá trị khóa cần xóa.

    Trả về:
        True nếu xóa được, False nếu không tìm thấy.
    """
    rows = read_csv(table)
    new_rows = ArrayList()
    found = False
    for row in rows:
        if len(row) > key_col_index and row[key_col_index].strip() == str(key_value).strip():
            found = True
        else:
            new_rows.append(row)
    if found:
        return write_csv(table, new_rows)
    return False


def delete_rows_by_key(table: str, key_col_index: int, key_value: str) -> bool:
    """
    Xóa TẤT CẢ dòng có giá trị tại cột key_col_index bằng key_value
    (dùng để xóa tất cả invoice_items của một invoice_id).

    Trả về:
        True nếu xóa ít nhất một dòng.
    """
    rows = read_csv(table)
    new_rows = ArrayList()
    found = False
    for row in rows:
        if len(row) > key_col_index and row[key_col_index].strip() == str(key_value).strip():
            found = True
        else:
            new_rows.append(row)
    if found:
        return write_csv(table, new_rows)
    return False


def find_row(table: str, key_col_index: int, key_value: str):
    """
    Tìm dòng đầu tiên có giá trị tại cột key_col_index bằng key_value.

    Trả về:
        list[str] nếu tìm thấy, None nếu không.
    """
    rows = read_csv(table)
    for row in rows:
        if len(row) > key_col_index and row[key_col_index].strip() == str(key_value).strip():
            return row
    return None


def find_rows(table: str, key_col_index: int, key_value: str):
    """
    Tìm TẤT CẢ dòng có giá trị tại cột key_col_index bằng key_value.

    Trả về:
        list[list[str]] — có thể rỗng.
    """
    rows = read_csv(table)
    result = ArrayList()
    for row in rows:
        if len(row) > key_col_index and row[key_col_index].strip() == str(key_value).strip():
            result.append(row)
    return result


def get_max_id(table: str, id_col_index: int) -> int:
    """
    Lấy giá trị số nguyên lớn nhất trong cột id_col_index.
    Dùng để tự tạo ID tự tăng thay cho AUTOINCREMENT của SQLite.

    Trả về:
        int — giá trị max (0 nếu bảng trống).
    """
    rows = read_csv(table)
    max_id = 0
    for row in rows:
        if len(row) > id_col_index:
            try:
                val = int(row[id_col_index].strip())
                if val > max_id:
                    max_id = val
            except ValueError:
                pass
    return max_id


def initialize_csv_files():
    """
    Đảm bảo tất cả file CSV tồn tại với header đúng.
    Nếu file chưa có → tạo file chỉ chứa header.
    Gọi khi khởi động ứng dụng (thay cho initialize_database()).

    Trả về:
        (True, thông báo) nếu thành công.
        (False, lỗi) nếu có lỗi.
    """
    _ensure_data_dir()
    try:
        for i in range(len(_TABLE_NAMES)):
            table = _TABLE_NAMES[i]
            headers = _TABLE_HEADERS[i]
            path = _get_file_path(table)
            if not os.path.exists(path):
                with open(path, "w", encoding="utf-8") as f:
                    f.write(SEP.join(headers) + "\n")
        return True, "Đã khởi tạo các file CSV thành công."
    except IOError as e:
        return False, f"Lỗi khi khởi tạo file CSV: {e}"

"""
Điểm vào chính cho Hệ thống Quản lý Hóa đơn.

Module này chứa hàm main() phục vụ như điểm khởi đầu chính
của ứng dụng quản lý hóa đơn. Khi được chạy trực tiếp,
nó sẽ khởi động giao diện đồ họa của ứng dụng.
"""
import sys

# Ép luồng xuất chuẩn về UTF-8 để in được tiếng Việt trên console Windows
# (mặc định Windows dùng cp1252, gây UnicodeEncodeError với ký tự như 'Đ').
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

from ui.gui import start_gui

def main():
    """
    Điểm vào chính cho Hệ thống Quản lý Hóa đơn.
    
    Khởi tạo và bắt đầu giao diện người dùng đồ họa cho ứng dụng
    quản lý hóa đơn. Hàm này phục vụ như điểm vào chính khi
    ứng dụng được chạy trực tiếp.
    
    Trả về:
        None
    
    Ném ra:
        SystemExit: Nếu GUI không thể được khởi tạo
    """
    try:
        start_gui()
    except Exception as e:
        print(f"Lỗi khi khởi động ứng dụng: {e}")
        raise SystemExit(1)

if __name__ == "__main__":
    main() 
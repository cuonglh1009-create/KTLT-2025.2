1.Yêu cầu chạy code
Python: phiên bản 3.7 trở lên (kiểm tra bằng lệnh python --version)
Tkinter: thường đã có sẵn khi cài Python trên Windows. Trên Linux/Ubuntu nếu thiếu, cài bằng lệnh:
  sudo apt-get install python3-tk

2. Cách chạy chương trình
Bước 1 — Mở terminal (Command Prompt trên Windows, hoặc Terminal trên macOS/Linux)
Bước 2 — Di chuyển vào đúng thư mục chứa main.py:
cd đường-dẫn-tới/project_final_fixed
Bước 3 — Chạy lệnh:
python main.py
hoặc nếu máy dùng python3:
python3 main.py

3.  Cấu trúc thư mục cần biết
project_final_fixed/
├── main.py              ← Đây là file để CHẠY chương trình
├── core/                ← Logic xử lý 
├── models/               ← Định nghĩa dữ liệu 
├── utils/                ← Công cụ hỗ trợ 
├── database/             ← Khởi tạo dữ liệu mẫu 
├── ui/                   ← Giao diện 
└── data/                 ← Nơi lưu dữ liệu

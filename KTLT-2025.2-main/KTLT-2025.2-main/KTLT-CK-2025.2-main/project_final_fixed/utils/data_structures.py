"""
utils/data_structures.py
Cấu trúc dữ liệu TỰ CÀI ĐẶT cho toàn bộ hệ thống.

Đề bài yêu cầu KHÔNG dùng các cấu trúc dữ liệu có sẵn (list, hash, ...)
mà phải tự cài đặt. Module này cung cấp lớp ArrayList — một MẢNG ĐỘNG
(dynamic array) được xây dựng từ vùng nhớ thô.

Nguyên lý:
    - Dùng ctypes.py_object để cấp phát một KHỐI BỘ NHỚ THÔ có kích thước
      cố định (tương đương malloc trong C). ctypes ở đây chỉ đóng vai trò
      "xin bộ nhớ", KHÔNG cung cấp sẵn thao tác thêm/xóa/sắp xếp/tìm kiếm.
    - Toàn bộ logic của mảng động (lưu phần tử, tự nhân đôi dung lượng khi
      đầy, lập chỉ mục, cắt lát, duyệt) đều do lớp ArrayList tự cài đặt.

ArrayList hỗ trợ các thao tác giống list để thay thế list ở mọi nơi:
    append(value)           — thêm phần tử vào cuối, O(1) khấu hao
    arr[i]                  — truy cập theo chỉ số (hỗ trợ chỉ số âm)
    arr[i] = value          — gán theo chỉ số
    arr[a:b]                — cắt lát, trả về ArrayList mới
    len(arr), bool(arr)     — số phần tử / kiểm tra rỗng
    for x in arr            — duyệt tuần tự
    value in arr            — kiểm tra tồn tại (Linear Search)
    clear()                 — xóa toàn bộ phần tử

Ngoài ra:
    split_fields(text, sep) — tự tách chuỗi thành ArrayList (thay str.split)
"""

import ctypes


class ArrayList:
    """
    Mảng động tự cài đặt trên vùng nhớ thô (thay cho list có sẵn).

    Thuộc tính nội bộ:
        _size     : Số phần tử đang lưu.
        _capacity : Dung lượng khối nhớ hiện tại (số ô đã cấp phát).
        _store    : Khối nhớ thô chứa tham chiếu tới các phần tử.
    """

    def __init__(self, iterable=None):
        """
        Khởi tạo mảng rỗng, có thể nạp sẵn từ một iterable bất kỳ.

        Tham số:
            iterable: Nguồn phần tử ban đầu (None = mảng rỗng).
        """
        self._size = 0
        self._capacity = 4
        self._store = self._new_block(self._capacity)
        if iterable is not None:
            for value in iterable:
                self.append(value)

    @staticmethod
    def _new_block(capacity):
        """Cấp phát một khối nhớ thô chứa `capacity` ô (như malloc trong C)."""
        return (capacity * ctypes.py_object)()

    def _resize(self, new_capacity):
        """Cấp khối nhớ lớn hơn rồi sao chép phần tử cũ sang (tự cài đặt)."""
        new_block = self._new_block(new_capacity)
        for i in range(self._size):
            new_block[i] = self._store[i]
        self._store = new_block
        self._capacity = new_capacity

    def _normalize_index(self, index):
        """Chuẩn hóa chỉ số (cho phép âm) và kiểm tra biên."""
        if index < 0:
            index = index + self._size
        if index < 0 or index >= self._size:
            raise IndexError("ArrayList: chỉ số nằm ngoài phạm vi")
        return index

    def append(self, value):
        """Thêm phần tử vào cuối; tự nhân đôi dung lượng khi khối nhớ đầy."""
        if self._size == self._capacity:
            self._resize(2 * self._capacity)
        self._store[self._size] = value
        self._size = self._size + 1

    def clear(self):
        """Xóa toàn bộ phần tử và cấp lại khối nhớ ban đầu."""
        self._size = 0
        self._capacity = 4
        self._store = self._new_block(self._capacity)

    def __len__(self):
        return self._size

    def __bool__(self):
        return self._size > 0

    def __getitem__(self, index):
        """Truy cập theo chỉ số hoặc cắt lát (slice trả về ArrayList mới)."""
        if isinstance(index, slice):
            result = ArrayList()
            start, stop, step = index.indices(self._size)
            i = start
            if step > 0:
                while i < stop:
                    result.append(self._store[i])
                    i = i + step
            else:
                while i > stop:
                    result.append(self._store[i])
                    i = i + step
            return result
        index = self._normalize_index(index)
        return self._store[index]

    def __setitem__(self, index, value):
        index = self._normalize_index(index)
        self._store[index] = value

    def __iter__(self):
        for i in range(self._size):
            yield self._store[i]

    def __contains__(self, value):
        """Kiểm tra tồn tại bằng Linear Search tự cài đặt."""
        for i in range(self._size):
            if self._store[i] == value:
                return True
        return False

    def __repr__(self):
        parts = ""
        for i in range(self._size):
            if i > 0:
                parts = parts + ", "
            parts = parts + repr(self._store[i])
        return "ArrayList([" + parts + "])"


def split_fields(text, separator):
    """
    Tự tách chuỗi `text` theo `separator` thành một ArrayList các trường,
    thay cho phương thức str.split() có sẵn (vốn trả về list).

    Tham số:
        text      : Chuỗi cần tách.
        separator : Chuỗi phân cách (một hoặc nhiều ký tự).

    Trả về:
        ArrayList các đoạn con (giữ cả đoạn rỗng giữa hai dấu phân cách).
    """
    result = ArrayList()
    current = ""
    sep_len = len(separator)
    i = 0
    n = len(text)
    while i < n:
        if sep_len > 0 and text[i:i + sep_len] == separator:
            result.append(current)
            current = ""
            i = i + sep_len
        else:
            current = current + text[i]
            i = i + 1
    result.append(current)
    return result

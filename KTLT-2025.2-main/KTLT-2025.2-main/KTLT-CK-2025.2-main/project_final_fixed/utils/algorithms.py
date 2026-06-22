"""
utils/algorithms.py
Các thuật toán tự cài đặt dùng cho toàn bộ hệ thống.

Module này cung cấp:
    sort_by_key(data, key, reverse)
        — Sắp xếp danh sách bằng Merge Sort tự cài đặt.
          Thay thế hàm sorted() có sẵn của Python.

    group_sum(items, key_func, value_func) → list[list]
        — Gom nhóm và cộng tổng một giá trị.


    group_sum_pair(items, key_func, qty_func, rev_func) → list[list]
        — Gom nhóm và cộng tổng đồng thời hai giá trị.

    unique_values(items, key_func) → list[str]
        — Lấy danh sách giá trị không trùng lặp.


"""

from typing import Callable, Any

from utils.data_structures import ArrayList



# THUẬT TOÁN CÀI ĐẶT: SẮP XẾP TRỘN (MERGE SORT)

def sort_by_key(data, key: Callable[[Any], Any] = None,
                reverse: bool = False) -> ArrayList:
    """
    Sắp xếp danh sách bằng thuật toán Merge Sort tự cài đặt.

    Tham số:
        data    : Danh sách cần sắp xếp.
        key     : Hàm trích xuất giá trị dùng để so sánh
                  (None = so sánh trực tiếp phần tử).
        reverse : True = sắp xếp giảm dần, False = tăng dần.

    Trả về:
        Danh sách mới đã được sắp xếp (không thay đổi danh sách gốc).

    Độ phức tạp: O(n log n)
    """
    items = ArrayList(data)
    if len(items) <= 1:
        return items

    if key is None:
        key = lambda x: x

    def merge_sort(arr: ArrayList) -> ArrayList:
        if len(arr) <= 1:
            return arr
        mid = len(arr) // 2
        left = merge_sort(arr[:mid])
        right = merge_sort(arr[mid:])
        return merge(left, right)

    def merge(left: ArrayList, right: ArrayList) -> ArrayList:
        result = ArrayList()
        i = 0
        j = 0
        while i < len(left) and j < len(right):
            left_key = key(left[i])
            right_key = key(right[j])
            if reverse:
                take_left = left_key >= right_key
            else:
                take_left = left_key <= right_key
            if take_left:
                result.append(left[i])
                i = i + 1
            else:
                result.append(right[j])
                j = j + 1
        while i < len(left):
            result.append(left[i])
            i = i + 1
        while j < len(right):
            result.append(right[j])
            j = j + 1
        return result

    return merge_sort(items)



# Thao tác tìm kiếm theo khóa dùng thuật toán Linear Search 

def _find_pair_index(pairs: ArrayList, key) -> int:
    """
    Tìm chỉ số của cặp [key, value] trong list-of-pairs theo khóa.

    Tham số:
        pairs : List các cặp [[k1, v1], [k2, v2], ...]
        key   : Khóa cần tìm.

    Trả về:
        int — chỉ số nếu tìm thấy, -1 nếu không.

    """
    for i in range(len(pairs)):
        if pairs[i][0] == key:
            return i
    return -1


def get_value(pairs: ArrayList, key, default=None):
    """
    Tra cứu giá trị trong list-of-pairs theo khóa.

    Tham số:
        pairs   : List các cặp [[k, v], ...].
        key     : Khóa cần tra cứu.
        default : Giá trị trả về nếu không tìm thấy.

    Trả về:
        Giá trị nếu tìm thấy, default nếu không.
    """
    idx = _find_pair_index(pairs, key)
    if idx != -1:
        return pairs[idx][1]
    return default


def group_sum(items, key_func: Callable[[Any], str],
              value_func: Callable[[Any], float]) -> ArrayList:
    """
    Gom nhóm các phần tử theo khóa và cộng tổng giá trị tương ứng.
    Sử dụng list-of-pairs [[key, sum], ...] 

    Tham số:
        items      : Danh sách phần tử cần gom nhóm.
        key_func   : Hàm lấy khóa nhóm từ một phần tử.
        value_func : Hàm lấy giá trị (số) cần cộng dồn từ một phần tử.

    Trả về:
        List[List]: [[khóa, tổng_giá_trị], ...]

    """
    result = ArrayList()    # List-of-pairs: [[key, accumulated_value], ...]
    for item in items:
        k = key_func(item)
        v = value_func(item)
        idx = _find_pair_index(result, k)
        if idx != -1:
            result[idx][1] = result[idx][1] + v
        else:
            result.append(ArrayList((k, v)))
    return result


def group_sum_pair(items, key_func: Callable[[Any], str],
                   qty_func: Callable[[Any], float],
                   rev_func: Callable[[Any], float]):
    """
    Gom nhóm theo khóa và cộng dồn ĐỒNG THỜI hai giá trị.
    Sử dụng list ba cột [[key, qty, rev], ...] 

    Tham số:
        items    : Danh sách phần tử cần gom nhóm.
        key_func : Hàm lấy khóa nhóm từ một phần tử.
        qty_func : Hàm lấy giá trị thứ nhất (ví dụ: số lượng).
        rev_func : Hàm lấy giá trị thứ hai (ví dụ: doanh thu).

    Trả về:
        List[List]: [[key, tổng_qty, tổng_rev], ...] — tự quản lý.

    """
    result = ArrayList()    # List ba cột: [[key, qty_sum, rev_sum], ...]
    for item in items:
        k = key_func(item)
        q = qty_func(item)
        r = rev_func(item)
        idx = _find_pair_index(result, k)
        if idx != -1:
            result[idx][1] = result[idx][1] + q
            result[idx][2] = result[idx][2] + r
        else:
            result.append(ArrayList((k, q, r)))
    return result


def unique_values(items, key_func: Callable[[Any], str]) -> ArrayList:
    """
    Lấy danh sách các giá trị khóa duy nhất (không trùng lặp).

    Tham số:
        items    : Danh sách phần tử.
        key_func : Hàm lấy khóa từ một phần tử.

    Trả về:
        Danh sách các khóa duy nhất, giữ thứ tự xuất hiện đầu tiên.

    """
    seen = ArrayList()
    result = ArrayList()
    for item in items:
        k = key_func(item)
        # Linear Search để kiểm tra đã thấy k chưa
        found = False
        for j in range(len(seen)):
            if seen[j] == k:
                found = True
                break
        if not found:
            seen.append(k)
            result.append(k)
    return result

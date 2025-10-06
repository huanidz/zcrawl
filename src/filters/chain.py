"""
Module chứa lớp FilterChain để quản lý nhiều Filter.
"""

from typing import Any, List, Union

from loguru import logger

from .base import Filter


class FilterChain(Filter):
    """
    Lớp FilterChain để quản lý và thực thi nhiều Filter theo chuỗi.
    Hỗ trợ các toán tử logic: AND, OR, NOT.
    """

    def __init__(self, filters: List[Filter], operator: str = "and"):
        """
        Khởi tạo FilterChain.

        Args:
            filters (List[Filter]): Danh sách các filter để thực thi
            operator (str): Toán tử logic ("and", "or", "not")
        """
        self.filters = filters
        self.operator = operator.lower()

        if self.operator not in ["and", "or", "not"]:
            raise ValueError(
                f"Operator không hợp lệ: {operator}. Phải là 'and', 'or', hoặc 'not'"
            )

        if self.operator == "not" and len(self.filters) != 1:
            raise ValueError("Operator 'not' chỉ được sử dụng với một filter duy nhất")

    def run(self, input_value: Any) -> bool:
        """
        Thực hiện chuỗi filter trên giá trị đầu vào.

        Args:
            input_value (Any): Giá trị cần kiểm tra

        Returns:
            bool: True nếu giá trị hợp lệ theo chuỗi filter, False nếu không hợp lệ
        """
        if not self.filters:
            return True

        if self.operator == "and":
            # Tất cả filters phải trả về True
            for filter_obj in self.filters:
                if not filter_obj.run(input_value):
                    return False
            return True

        elif self.operator == "or":
            # Ít nhất một filter phải trả về True
            for filter_obj in self.filters:
                if filter_obj.run(input_value):
                    return True
            return False

        elif self.operator == "not":
            # Đảo ngược kết quả của filter duy nhất
            return not self.filters[0].run(input_value)

        return False

    def add_filter(self, filter_obj: Filter) -> None:
        """
        Thêm một filter vào chuỗi.

        Args:
            filter_obj (Filter): Filter cần thêm
        """
        self.filters.append(filter_obj)

    def remove_filter(self, filter_obj: Filter) -> bool:
        """
        Xóa một filter khỏi chuỗi.

        Args:
            filter_obj (Filter): Filter cần xóa

        Returns:
            bool: True nếu xóa thành công, False nếu không tìm thấy
        """
        try:
            self.filters.remove(filter_obj)
            return True
        except ValueError:
            return False

    def __and__(self, other: Filter) -> "FilterChain":
        """
        Toán tử AND để kết hợp với filter khác.

        Args:
            other (Filter): Filter khác để kết hợp

        Returns:
            FilterChain: Chuỗi filter mới với logic AND
        """
        if self.operator == "and":
            # Nếu chuỗi hiện tại đã là AND, chỉ cần thêm filter
            new_filters = self.filters.copy()
            if isinstance(other, FilterChain) and other.operator == "and":
                new_filters.extend(other.filters)
            else:
                new_filters.append(other)
            return FilterChain(filters=new_filters, operator="and")
        else:
            # Nếu chuỗi hiện tại không phải là AND, tạo chuỗi mới
            return FilterChain(filters=[self, other], operator="and")

    def __or__(self, other: Filter) -> "FilterChain":
        """
        Toán tử OR để kết hợp với filter khác.

        Args:
            other (Filter): Filter khác để kết hợp

        Returns:
            FilterChain: Chuỗi filter mới với logic OR
        """
        if self.operator == "or":
            # Nếu chuỗi hiện tại đã là OR, chỉ cần thêm filter
            new_filters = self.filters.copy()
            if isinstance(other, FilterChain) and other.operator == "or":
                new_filters.extend(other.filters)
            else:
                new_filters.append(other)
            return FilterChain(filters=new_filters, operator="or")
        else:
            # Nếu chuỗi hiện tại không phải là OR, tạo chuỗi mới
            return FilterChain(filters=[self, other], operator="or")

    def __invert__(self) -> "FilterChain":
        """
        Toán tử NOT để đảo ngược kết quả filter.

        Returns:
            FilterChain: Chuỗi filter mới với logic NOT
        """
        return FilterChain(filters=[self], operator="not")

    def __str__(self) -> str:
        """
        Biểu diễn chuỗi filter dưới dạng string.

        Returns:
            str: Biểu diễn chuỗi filter
        """
        if not self.filters:
            return "EmptyFilterChain"

        filter_strs = [str(f) for f in self.filters]

        if self.operator == "not":
            return f"NOT ({filter_strs[0]})"
        elif self.operator == "and":
            return f"({') AND ('.join(filter_strs)})"
        else:  # or
            return f"({') OR ('.join(filter_strs)})"

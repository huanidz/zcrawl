"""
Module chứa lớp Filter cơ bản.
"""

from abc import ABC, abstractmethod
from typing import Any

from loguru import logger


class Filter(ABC):
    """
    Lớp cơ bản cho tất cả các filter.
    Cung cấp interface chung cho việc kiểm tra giá trị đầu vào.
    """

    @abstractmethod
    def run(self, input_value: Any) -> bool:
        """
        Thực hiện filtering trên giá trị đầu vào.

        Args:
            input_value (Any): Giá trị cần kiểm tra

        Returns:
            bool: True nếu giá trị hợp lệ, False nếu không hợp lệ
        """
        pass

    def __and__(self, other: "Filter") -> "FilterChain":
        """
        Toán tử AND để kết hợp với filter khác.

        Args:
            other (Filter): Filter khác để kết hợp

        Returns:
            FilterChain: Chuỗi filter mới với logic AND
        """
        from .chain import FilterChain

        return FilterChain(filters=[self, other], operator="and")

    def __or__(self, other: "Filter") -> "FilterChain":
        """
        Toán tử OR để kết hợp với filter khác.

        Args:
            other (Filter): Filter khác để kết hợp

        Returns:
            FilterChain: Chuỗi filter mới với logic OR
        """
        from .chain import FilterChain

        return FilterChain(filters=[self, other], operator="or")

    def __invert__(self) -> "FilterChain":
        """
        Toán tử NOT để đảo ngược kết quả filter.

        Returns:
            FilterChain: Chuỗi filter mới với logic NOT
        """
        from .chain import FilterChain

        return FilterChain(filters=[self], operator="not")

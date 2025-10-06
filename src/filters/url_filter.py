"""
Module chứa lớp URLFilter để lọc các URL.
"""

import re
from typing import Any, List, Optional, Set, Union
from urllib.parse import urlparse

from loguru import logger

from .base import Filter


class URLFilter(Filter):
    """
    Filter để kiểm tra tính hợp lệ của URL dựa trên các tiêu chí khác nhau.
    """

    def __init__(
        self,
        allowed_domains: Optional[List[str]] = None,
        blocked_domains: Optional[List[str]] = None,
        allowed_schemes: Optional[List[str]] = None,
        blocked_extensions: Optional[List[str]] = None,
        regex_pattern: Optional[str] = None,
        max_length: Optional[int] = None,
        min_length: Optional[int] = None,
    ):
        """
        Khởi tạo URLFilter.

        Args:
            allowed_domains (Optional[List[str]]): Danh sách các domain được phép
            blocked_domains (Optional[List[str]]): Danh sách các domain bị chặn
            allowed_schemes (Optional[List[str]]): Danh sách các scheme được phép (http, https, etc.)
            blocked_extensions (Optional[List[str]]): Danh sách các phần mở rộng bị chặn (.pdf, .jpg, etc.)
            regex_pattern (Optional[str]): Pattern regex để kiểm tra URL
            max_length (Optional[int]): Độ dài tối đa của URL
            min_length (Optional[int]): Độ dài tối thiểu của URL
        """
        self.allowed_domains = set(allowed_domains or [])
        self.blocked_domains = set(blocked_domains or [])
        self.allowed_schemes = set(allowed_schemes or ["http", "https"])
        self.blocked_extensions = set(blocked_extensions or [])
        self.regex_pattern = re.compile(regex_pattern) if regex_pattern else None
        self.max_length = max_length
        self.min_length = min_length

    def run(self, input_value: Any) -> bool:
        """
        Kiểm tra xem URL có hợp lệ không.

        Args:
            input_value (Any): URL cần kiểm tra

        Returns:
            bool: True nếu URL hợp lệ, False nếu không hợp lệ
        """
        if not isinstance(input_value, str):
            logger.debug(f"URL không phải là string: {input_value}")
            return False

        url = input_value.strip()

        # Kiểm tra độ dài
        if self.min_length is not None and len(url) < self.min_length:
            logger.debug(f"URL quá ngắn: {url}")
            return False

        if self.max_length is not None and len(url) > self.max_length:
            logger.debug(f"URL quá dài: {url}")
            return False

        # Parse URL
        try:
            parsed = urlparse(url)
        except Exception as e:
            logger.debug(f"Lỗi khi parse URL {url}: {e}")
            return False

        # Kiểm tra scheme
        if (
            parsed.scheme
            and self.allowed_schemes
            and parsed.scheme not in self.allowed_schemes
        ):
            logger.debug(f"Scheme không được phép: {parsed.scheme} trong URL: {url}")
            return False

        # Kiểm tra domain
        domain = parsed.netloc.lower()
        if domain:
            # Kiểm tra domain bị chặn
            if self.blocked_domains and any(
                blocked in domain for blocked in self.blocked_domains
            ):
                logger.debug(f"Domain bị chặn: {domain} trong URL: {url}")
                return False

            # Kiểm tra domain được phép
            if self.allowed_domains and not any(
                allowed in domain for allowed in self.allowed_domains
            ):
                logger.debug(f"Domain không được phép: {domain} trong URL: {url}")
                return False

        # Kiểm tra phần mở rộng
        path = parsed.path.lower()
        if path and self.blocked_extensions:
            for ext in self.blocked_extensions:
                if path.endswith(ext.lower()):
                    logger.debug(f"Phần mở rộng bị chặn: {ext} trong URL: {url}")
                    return False

        # Kiểm tra regex pattern
        if self.regex_pattern and not self.regex_pattern.match(url):
            logger.debug(f"URL không khớp với pattern regex: {url}")
            return False

        return True

    def __str__(self) -> str:
        """
        Biểu diễn filter dưới dạng string.

        Returns:
            str: Biểu diễn filter
        """
        criteria = []
        if self.allowed_domains:
            criteria.append(f"allowed_domains={list(self.allowed_domains)}")
        if self.blocked_domains:
            criteria.append(f"blocked_domains={list(self.blocked_domains)}")
        if self.allowed_schemes:
            criteria.append(f"allowed_schemes={list(self.allowed_schemes)}")
        if self.blocked_extensions:
            criteria.append(f"blocked_extensions={list(self.blocked_extensions)}")
        if self.regex_pattern:
            criteria.append(f"regex_pattern={self.regex_pattern.pattern}")
        if self.max_length is not None:
            criteria.append(f"max_length={self.max_length}")
        if self.min_length is not None:
            criteria.append(f"min_length={self.min_length}")

        return f"URLFilter({', '.join(criteria)})"


class DomainFilter(Filter):
    """
    Filter để kiểm tra domain của URL.
    """

    def __init__(
        self,
        allowed_domains: Optional[List[str]] = None,
        blocked_domains: Optional[List[str]] = None,
    ):
        """
        Khởi tạo DomainFilter.

        Args:
            allowed_domains (Optional[List[str]]): Danh sách các domain được phép
            blocked_domains (Optional[List[str]]): Danh sách các domain bị chặn
        """
        self.allowed_domains = set(allowed_domains or [])
        self.blocked_domains = set(blocked_domains or [])

    def run(self, input_value: Any) -> bool:
        """
        Kiểm tra xem domain của URL có hợp lệ không.

        Args:
            input_value (Any): URL cần kiểm tra

        Returns:
            bool: True nếu domain hợp lệ, False nếu không hợp lệ
        """
        if not isinstance(input_value, str):
            return False

        try:
            parsed = urlparse(input_value)
            domain = parsed.netloc.lower()
        except Exception:
            return False

        if not domain:
            return False

        # Kiểm tra domain bị chặn
        if self.blocked_domains and any(
            blocked in domain for blocked in self.blocked_domains
        ):
            return False

        # Kiểm tra domain được phép
        if self.allowed_domains and not any(
            allowed in domain for allowed in self.allowed_domains
        ):
            return False

        return True

    def __str__(self) -> str:
        """
        Biểu diễn filter dưới dạng string.

        Returns:
            str: Biểu diễn filter
        """
        criteria = []
        if self.allowed_domains:
            criteria.append(f"allowed_domains={list(self.allowed_domains)}")
        if self.blocked_domains:
            criteria.append(f"blocked_domains={list(self.blocked_domains)}")

        return f"DomainFilter({', '.join(criteria)})"

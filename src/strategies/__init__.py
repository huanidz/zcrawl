"""
Package chứa các strategy cho crawler.
"""

from .BaseStrategy import BaseStrategy
from .BFSCrawlingStrategy import BFSCrawlingStrategy
from .DFSCrawlingStrategy import DFSCrawlingStrategy

__all__ = ["BaseStrategy", "DFSCrawlingStrategy", "BFSCrawlingStrategy"]

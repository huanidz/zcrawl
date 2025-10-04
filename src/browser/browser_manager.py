"""
Module chứa orchestrator chính cho browser instances.
Quản lý vòng đời của nhiều browser instances (khởi động, đóng, khởi động lại).
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set

from .browser_config import BrowserConfig, ConfigType, get_browser_config
from .browser_instance import BrowserInstance

logger = logging.getLogger(__name__)


class BrowserManager:
    """
    Class orchestrator chính cho browser instances.
    Quản lý vòng đời của nhiều browser instances.
    """

    def __init__(self):
        """
        Khởi tạo BrowserManager.
        """
        self._instances: Dict[str, BrowserInstance] = {}
        self._instance_configs: Dict[str, BrowserConfig] = {}
        self._instance_created_at: Dict[str, datetime] = {}
        self._instance_last_used: Dict[str, datetime] = {}
        self._max_idle_time: timedelta = timedelta(minutes=30)
        self._max_lifetime: timedelta = timedelta(hours=2)
        self._cleanup_task: Optional[asyncio.Task] = None
        self._is_running = False

    async def start(self) -> None:
        """
        Khởi động browser manager và bắt đầu task cleanup.
        """
        if self._is_running:
            return

        self._is_running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("BrowserManager đã được khởi động")

    async def stop(self) -> None:
        """
        Dừng browser manager và tất cả instances.
        """
        if not self._is_running:
            return

        self._is_running = False

        # Hủy task cleanup
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None

        # Dừng tất cả instances
        await self.stop_all_instances()
        logger.info("BrowserManager đã được dừng")

    async def create_instance(
        self,
        name: str,
        config: Optional[BrowserConfig] = None,
        auto_start: bool = True,
    ) -> BrowserInstance:
        """
        Tạo mới browser instance.

        Args:
            name (str): Tên của instance
            config (Optional[BrowserConfig]): Cấu hình cho browser
            auto_start (bool): Tự động khởi động instance sau khi tạo

        Returns:
            BrowserInstance: Browser instance mới

        Raises:
            ValueError: Nếu instance với tên đã tồn tại
        """
        if name in self._instances:
            raise ValueError(f"Browser instance '{name}' đã tồn tại")

        if config is None:
            config = get_browser_config(ConfigType.DEFAULT)

        instance = BrowserInstance(config)

        if auto_start:
            await instance.start()

        now = datetime.now()
        self._instances[name] = instance
        self._instance_configs[name] = config
        self._instance_created_at[name] = now
        self._instance_last_used[name] = now

        logger.info(f"Đã tạo browser instance '{name}'")
        return instance

    async def get_instance(self, name: str) -> BrowserInstance:
        """
        Lấy browser instance theo tên và cập nhật thời gian sử dụng.

        Args:
            name (str): Tên của instance

        Returns:
            BrowserInstance: Browser instance

        Raises:
            KeyError: Nếu instance không tồn tại
        """
        if name not in self._instances:
            raise KeyError(f"Browser instance '{name}' không tồn tại")

        # Cập nhật thời gian sử dụng cuối cùng
        self._instance_last_used[name] = datetime.now()
        return self._instances[name]

    def has_instance(self, name: str) -> bool:
        """
        Kiểm tra instance có tồn tại không.

        Args:
            name (str): Tên của instance

        Returns:
            bool: True nếu instance tồn tại
        """
        return name in self._instances

    async def remove_instance(self, name: str) -> None:
        """
        Xóa browser instance.

        Args:
            name (str): Tên của instance
        """
        if name in self._instances:
            await self._instances[name].stop()
            del self._instances[name]
            del self._instance_configs[name]
            del self._instance_created_at[name]
            del self._instance_last_used[name]
            logger.info(f"Đã xóa browser instance '{name}'")

    async def restart_instance(self, name: str) -> BrowserInstance:
        """
        Khởi động lại browser instance.

        Args:
            name (str): Tên của instance

        Returns:
            BrowserInstance: Browser instance sau khi restart

        Raises:
            KeyError: Nếu instance không tồn tại
        """
        if name not in self._instances:
            raise KeyError(f"Browser instance '{name}' không tồn tại")

        logger.info(f"Đang khởi động lại browser instance '{name}'")

        # Dừng instance
        await self._instances[name].stop()

        # Khởi động lại
        await self._instances[name].start()

        # Cập nhật thời gian
        now = datetime.now()
        self._instance_created_at[name] = now
        self._instance_last_used[name] = now

        logger.info(f"Đã khởi động lại browser instance '{name}'")
        return self._instances[name]

    async def stop_all_instances(self) -> None:
        """
        Dừng tất cả browser instances.
        """
        logger.info("Đang dừng tất cả browser instances")

        # Dừng tất cả instances song song
        tasks = [instance.stop() for instance in self._instances.values()]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        # Xóa tất cả thông tin
        self._instances.clear()
        self._instance_configs.clear()
        self._instance_created_at.clear()
        self._instance_last_used.clear()

        logger.info("Đã dừng tất cả browser instances")

    def list_instances(self) -> List[str]:
        """
        Lấy danh sách tên các instances.

        Returns:
            List[str]: Danh sách tên instances
        """
        return list(self._instances.keys())

    def get_instance_info(self, name: str) -> Optional[Dict]:
        """
        Lấy thông tin chi tiết về instance.

        Args:
            name (str): Tên của instance

        Returns:
            Optional[Dict]: Thông tin instance hoặc None nếu không tồn tại
        """
        if name not in self._instances:
            return None

        instance = self._instances[name]
        created_at = self._instance_created_at[name]
        last_used = self._instance_last_used[name]

        return {
            "name": name,
            "is_started": instance.is_started(),
            "created_at": created_at.isoformat(),
            "last_used_at": last_used.isoformat(),
            "uptime": (datetime.now() - created_at).total_seconds(),
            "idle_time": (datetime.now() - last_used).total_seconds(),
            "headless": self._instance_configs[name].headless,
            "viewport": {
                "width": self._instance_configs[name].viewport_width,
                "height": self._instance_configs[name].viewport_height,
            },
        }

    def get_all_instances_info(self) -> Dict[str, Dict]:
        """
        Lấy thông tin tất cả instances.

        Returns:
            Dict[str, Dict]: Dictionary chứa thông tin tất cả instances
        """
        return {name: self.get_instance_info(name) for name in self._instances.keys()}

    def set_max_idle_time(self, minutes: int) -> None:
        """
        Thiết lập thời gian idle tối đa trước khi tự động dừng.

        Args:
            minutes (int): Thời gian tối đa theo phút
        """
        self._max_idle_time = timedelta(minutes=minutes)
        logger.info(f"Thiết lập max idle time: {minutes} phút")

    def set_max_lifetime(self, hours: int) -> None:
        """
        Thiết lập thời gian sống tối đa của instance.

        Args:
            hours (int): Thời gian tối đa theo giờ
        """
        self._max_lifetime = timedelta(hours=hours)
        logger.info(f"Thiết lập max lifetime: {hours} giờ")

    async def _cleanup_loop(self) -> None:
        """
        Loop cleanup để dừng các instances không được sử dụng.
        """
        while self._is_running:
            try:
                await self._cleanup_idle_instances()
                await asyncio.sleep(60)  # Check mỗi phút
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Lỗi trong cleanup loop: {e}")
                await asyncio.sleep(60)

    async def _cleanup_idle_instances(self) -> None:
        """
        Dừng các instances đã idle quá lâu hoặc hết lifetime.
        """
        now = datetime.now()
        instances_to_remove: Set[str] = set()

        for name in self._instances:
            created_at = self._instance_created_at[name]
            last_used = self._instance_last_used[name]

            # Kiểm tra lifetime
            if now - created_at > self._max_lifetime:
                logger.warning(f"Instance '{name}' đã hết lifetime, sẽ bị dừng")
                instances_to_remove.add(name)
                continue

            # Kiểm tra idle time
            if now - last_used > self._max_idle_time:
                logger.info(f"Instance '{name}' đã idle quá lâu, sẽ bị dừng")
                instances_to_remove.add(name)

        # Xóa các instances cần cleanup
        for name in instances_to_remove:
            await self.remove_instance(name)

    async def __aenter__(self):
        """
        Async context manager entry.
        """
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Async context manager exit.
        """
        await self.stop()

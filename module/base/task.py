import time

from module.logger import logger


class ModuleBase:
    """Primitive chung cho mọi task: appear / appear_then_click / wait_until_*.

    Quy ước: các hàm appear* đọc self.device.image (screenshot đã chụp);
    các hàm wait_until_* tự chụp mới liên tục.
    """

    def __init__(self, config, device):
        self.config = config
        self.device = device
        self._last_click: dict[str, float] = {}

    def appear(self, button, threshold: float = None) -> bool:
        return button.match(self.device.image, threshold=threshold)

    def appear_then_click(self, button, interval: float = 3) -> bool:
        """Click nếu button xuất hiện, nhưng cùng 1 button tối đa 1 lần mỗi `interval` giây
        (chống double-click khi UI chưa kịp phản hồi)."""
        if not self.appear(button):
            return False
        if time.time() - self._last_click.get(button.name, 0) < interval:
            return False
        self.device.click(button)
        self._last_click[button.name] = time.time()
        return True

    def wait_until_appear(self, button, timeout: float = 20, interval: float = 0.5) -> bool:
        end = time.time() + timeout
        while time.time() < end:
            self.device.screenshot()
            if self.appear(button):
                return True
            time.sleep(interval)
        logger.warning(f'wait_until_appear({button.name}) timeout sau {timeout}s')
        return False

    def wait_until_disappear(self, button, timeout: float = 20, interval: float = 0.5) -> bool:
        end = time.time() + timeout
        while time.time() < end:
            self.device.screenshot()
            if not self.appear(button):
                return True
            time.sleep(interval)
        logger.warning(f'wait_until_disappear({button.name}) timeout sau {timeout}s')
        return False

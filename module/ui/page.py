import time
from collections import deque

from module.base.task import ModuleBase
from module.exception import GameStuckError
from module.logger import logger


class Page:
    """Node trong page graph. check = Button nhận diện 'đang ở page này'."""

    registry: dict[str, 'Page'] = {}

    def __init__(self, name: str, check):
        self.name = name
        self.check = check
        self.links: dict[str, object] = {}  # tên page đích -> Button để đi tới đó
        Page.registry[name] = self

    def link(self, button, destination: 'Page') -> None:
        self.links[destination.name] = button

    def __repr__(self):
        return f'Page({self.name})'


class UI(ModuleBase):
    """Điều hướng theo page graph: xác định page hiện tại, tìm đường BFS, đi tới page đích."""

    # Danh sách Button đóng popup toàn cục (nạp trong module/ui/pages.py, bổ sung dần ở Phase 2)
    popup_closers: list = []

    def handle_popup(self) -> bool:
        for b in self.popup_closers:
            if self.appear_then_click(b, interval=1):
                logger.info(f'Đóng popup: {b.name}')
                return True
        return False

    def ui_current_page(self, timeout: float = 15):
        """Nhận diện page hiện tại; vừa thử vừa đóng popup. Hết timeout -> GameStuckError."""
        end = time.time() + timeout
        while time.time() < end:
            self.device.screenshot()
            for page in Page.registry.values():
                if self.appear(page.check):
                    return page
            self.handle_popup()
            time.sleep(0.5)
        raise GameStuckError('Không nhận diện được page nào — màn hình lạ hoặc thiếu asset.')

    def ui_ensure(self, destination: Page, timeout: float = 60) -> None:
        """Điều hướng tới `destination` bằng BFS trên page graph."""
        end = time.time() + timeout
        while time.time() < end:
            current = self.ui_current_page()
            if current is destination:
                logger.info(f'Đã ở {destination}')
                return
            path = self._find_path(current, destination)
            if path is None:
                raise GameStuckError(f'Không có đường từ {current} tới {destination} trong page graph.')
            next_button = current.links[path[1]]
            self.appear_then_click(next_button, interval=2)
            time.sleep(1)
        raise GameStuckError(f'ui_ensure({destination}) timeout sau {timeout}s')

    @staticmethod
    def _find_path(src: Page, dst: Page) -> list | None:
        queue = deque([[src.name]])
        seen = {src.name}
        while queue:
            path = queue.popleft()
            if path[-1] == dst.name:
                return path
            for nxt in Page.registry[path[-1]].links:
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append(path + [nxt])
        return None

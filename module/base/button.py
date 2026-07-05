from pathlib import Path

import cv2
import numpy as np

from module.config import ROOT
from module.exception import AssetMissingError
from module.logger import logger

_SERVER = 'en'


def set_server(server: str) -> None:
    global _SERVER
    _SERVER = server


class Button:
    """Template button: file ảnh dưới assets/<server>/, vùng tìm kiếm `area` (None = toàn màn hình).

    Convention: tên biến UPPER_SNAKE_CASE khớp 100% tên file (xem skill crop-button-asset).
    """

    def __init__(self, file: str, area: tuple = None, threshold: float = 0.85, name: str = None):
        self.file = file
        self.area = area  # (x1, y1, x2, y2) vùng tìm kiếm trên screenshot
        self.threshold = threshold
        self.name = name or Path(file).stem
        self._template = None
        self._size_warned = False
        self.last_match: tuple | None = None  # (x, y) tâm vùng khớp gần nhất

    @property
    def path(self) -> Path:
        p = Path(self.file)
        return p if p.is_absolute() else ROOT / 'assets' / _SERVER / self.file

    @property
    def template(self) -> np.ndarray:
        if self._template is None:
            if not self.path.exists():
                raise AssetMissingError(
                    f'Thiếu asset {self.path} — crop bằng: python dev_tools/crop.py <screenshot> '
                    f'--area x1,y1,x2,y2 --page <page> --name {self.name}')
            self._template = cv2.imread(str(self.path), cv2.IMREAD_COLOR)
        return self._template

    def match(self, image: np.ndarray, threshold: float = None) -> bool:
        """Tìm template trong `image` (giới hạn theo self.area nếu có). Lưu last_match khi khớp."""
        threshold = threshold or self.threshold
        x1, y1 = 0, 0
        crop = image
        if self.area is not None:
            x1, y1, x2, y2 = self.area
            crop = image[y1:y2, x1:x2]
        th, tw = self.template.shape[:2]
        ch, cw = crop.shape[:2]
        if th > ch or tw > cw:
            # Template lớn hơn vùng tìm -> matchTemplate sẽ ném assertion. Không thể khớp -> bỏ qua.
            if not self._size_warned:
                logger.warning(f'{self.name}: template {tw}x{th} lớn hơn vùng tìm {cw}x{ch} — '
                               f'bỏ qua match (kiểm tra area/asset)')
                self._size_warned = True
            return False
        res = cv2.matchTemplate(crop, self.template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        if max_val < threshold:
            return False
        th, tw = self.template.shape[:2]
        self.last_match = (x1 + max_loc[0] + tw // 2, y1 + max_loc[1] + th // 2)
        return True

    def click_point(self) -> tuple:
        if self.last_match is not None:
            return self.last_match
        if self.area is not None:
            x1, y1, x2, y2 = self.area
            return (x1 + x2) // 2, (y1 + y2) // 2
        raise ValueError(f'{self.name}: chưa match lần nào và không có area để suy ra điểm click')

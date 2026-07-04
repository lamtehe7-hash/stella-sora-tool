import re
import subprocess

import adbutils

from module.exception import EmulatorNotRunningError
from module.logger import logger


class Adb:
    """Wrapper mỏng quanh adbutils: 1 serial, 1 adb server chạy từ đúng binary cấu hình."""

    def __init__(self, serial: str, adb_path: str = 'adb'):
        self.serial = serial
        self.adb_path = adb_path
        self._client = adbutils.AdbClient(host='127.0.0.1', port=5037)
        self._device = None

    def connect(self) -> None:
        # Chạy start-server bằng đúng binary cấu hình để tránh 2 bản adb khác version kill nhau
        subprocess.run([self.adb_path, 'start-server'], capture_output=True)
        try:
            self._client.connect(self.serial, timeout=5)
        except adbutils.AdbError as e:
            raise EmulatorNotRunningError(
                f'Không connect được {self.serial} — giả lập đã mở chưa? ({e})')
        serials = [d.serial for d in self._client.device_list()]
        if self.serial not in serials:
            raise EmulatorNotRunningError(
                f'{self.serial} không có trong adb devices: {serials}')
        self._device = self._client.device(self.serial)
        logger.info(f'Đã kết nối {self.serial}')

    @property
    def device(self) -> adbutils.AdbDevice:
        if self._device is None:
            self.connect()
        return self._device

    def shell(self, cmd: str, encoding='utf-8'):
        return self.device.shell(cmd, encoding=encoding)

    def screenshot_png(self) -> bytes:
        return self.shell('screencap -p', encoding=None)

    def tap(self, x: int, y: int) -> None:
        self.shell(f'input tap {int(x)} {int(y)}')

    def swipe(self, x1, y1, x2, y2, duration_ms: int = 300) -> None:
        self.shell(f'input swipe {int(x1)} {int(y1)} {int(x2)} {int(y2)} {int(duration_ms)}')

    def app_current(self) -> str:
        """Package đang focus, '' nếu không xác định được."""
        out = self.shell('dumpsys window')
        m = re.search(r'mCurrentFocus=Window\{[^ ]+ [^ ]+ ([^/ ]+)/', out)
        return m.group(1) if m else ''

    def app_start(self, package: str) -> None:
        self.shell(f'monkey -p {package} -c android.intent.category.LAUNCHER 1')

    def app_stop(self, package: str) -> None:
        self.shell(f'am force-stop {package}')

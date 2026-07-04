import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict

from pydantic import BaseModel, Field

# Bản exe (PyInstaller): assets/ config/ log/ nằm CẠNH file exe, không nằm trong bundle tạm
if getattr(sys, 'frozen', False):
    ROOT = Path(sys.executable).resolve().parent
else:
    ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = ROOT / 'config' / 'stella.json'
EPOCH = datetime(2020, 1, 1)


def utcnow() -> datetime:
    """Mốc thời gian nội bộ: UTC naive, thống nhất toàn tool (kể cả next_run trong config)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class EmulatorConfig(BaseModel):
    serial: str = '127.0.0.1:16384'
    adb_path: str = r'E:\MuMuPlayerGlobal\nx_device\12.0\shell\adb.exe'
    package: str = 'com.YoStarEN.StellaSora'


class TaskSettings(BaseModel):
    enable: bool = True
    next_run: datetime = EPOCH


class Config(BaseModel):
    emulator: EmulatorConfig = Field(default_factory=EmulatorConfig)
    server: str = 'en'
    # Giờ reset daily theo UTC. 11:00 UTC = 04:00 UTC-7 theo chuẩn Yostar EN.
    # TODO(Phase 2): xác minh giờ reset thật của Stella Sora EN trong game.
    daily_reset_utc: str = '11:00'
    # Cleanup có đóng hẳn game không (mặc định để game ở màn hình chính)
    close_game_on_cleanup: bool = False
    tasks: Dict[str, TaskSettings] = Field(default_factory=dict)

    @classmethod
    def load(cls) -> 'Config':
        if CONFIG_FILE.exists():
            return cls.model_validate_json(CONFIG_FILE.read_text(encoding='utf-8'))
        cfg = cls()
        cfg.save()
        return cfg

    def save(self) -> None:
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(self.model_dump_json(indent=2), encoding='utf-8')

    def task(self, name: str) -> TaskSettings:
        return self.tasks.setdefault(name, TaskSettings())

    def next_server_reset(self) -> datetime:
        h, m = (int(x) for x in self.daily_reset_utc.split(':'))
        now = utcnow()
        reset = now.replace(hour=h, minute=m, second=0, microsecond=0)
        if reset <= now:
            reset += timedelta(days=1)
        return reset

    def task_delay(self, name: str, minutes: float = None, server_reset: bool = False) -> None:
        """Hẹn next_run cho task: tới reset daily kế tiếp, hoặc sau N phút."""
        t = self.task(name)
        if server_reset:
            t.next_run = self.next_server_reset()
        elif minutes is not None:
            t.next_run = utcnow() + timedelta(minutes=minutes)
        else:
            raise ValueError('task_delay cần minutes hoặc server_reset=True')
        self.save()

    def get_next_task(self, order: list) -> str | None:
        """Task đến hạn có ưu tiên cao nhất theo thứ tự `order`, hoặc None."""
        now = utcnow()
        for name in order:
            t = self.task(name)
            if t.enable and t.next_run <= now:
                return name
        return None

    def next_wake(self, order: list) -> datetime | None:
        """Thời điểm next_run sớm nhất trong các task đang bật."""
        runs = [self.task(n).next_run for n in order if self.task(n).enable]
        return min(runs) if runs else None

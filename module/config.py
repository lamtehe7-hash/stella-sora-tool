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
# Task tắt sẵn khi mở lần đầu (chưa có trong config). Người chơi bật/tắt sau đó được LƯU vào
# config như mọi task khác (mặc định OFF chỉ áp dụng lần tạo mới):
#   Ascension  — tốn vé + chạy lâu, để người chơi chủ động bật.
#   BountyTrial — tiêu Vigor, người chơi tự quyết có tiêu vào Trial hay không.
#   EventDaily  — sự kiện theo đợt, cần crop banner + set stage mỗi đợt trước khi bật.
DEFAULT_OFF_TASKS = {'Ascension', 'BountyTrial', 'EventDaily'}


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


class AscensionConfig(BaseModel):
    """Tuỳ chọn người chơi cho task Ascension (Monolith Quick Battle).

    Mặc định = đúng hành vi cũ (chạy 1 run/ngày, chiến lược shop v3, chọn thẻ theo mức tăng level).
    """
    # --- Vé / số lần chạy ---
    # Mỗi run Quick Battle tốn 1 vé Monolith. runs_per_session = số run tối đa mỗi lần task chạy;
    # tool tự dừng sớm khi nút Quick Battle không còn sáng (hết vé / difficulty chưa clear).
    runs_per_session: int = 1
    # --- Chọn map Monolith ---
    # '' = giữ map game nhớ (không đụng); hoặc 'currents'|'dust'|'storm'|'misstep' — 4 Monolith
    # cố định (Currents and Shadows / Dust and Flames / Storm and Thunder / Misstep On One).
    map: str = ''
    # --- Chọn Squad/Team ---
    # 0 = giữ nguyên squad game nhớ (không đụng vào); 1..N = tự vuốt tới squad này trước khi vào run.
    squad: int = 0
    # --- Preset Potential ---
    # Khi squad CHƯA gắn preset (hiện "Preset not set" góc phải-trên màn Squad):
    #   warn  = cảnh báo rồi chạy tiếp (sẽ không có thẻ 👍 ưu tiên)
    #   skip  = bỏ qua Ascension hôm nay, hẹn lại sau reset
    #   abort = coi như lỗi, dừng task để người chơi vào set preset (MẶC ĐỊNH)
    preset_behavior: str = 'abort'
    # --- Chọn thẻ khi nhiều thẻ 👍 ---
    #   level_gain = mức tăng level lớn nhất (SR core ưu tiên tuyệt đối) — mặc định
    #   super_rare = ưu tiên thẻ Super Rare, còn lại lấy trái nhất
    #   leftmost   = luôn lấy thẻ 👍 trái nhất
    card_priority: str = 'level_gain'
    # --- Chiến lược Shop ---
    buy_melody_when_needed_only: bool = True   # Melody chỉ mua khi dialog có panel Relevant Harmony Skills
    enhance_milestone: int = 180               # giữa run enhance tới hết bậc này rồi giữ coin cho shop sau
    enhance_reserve: int = 360                 # coin luôn chừa khi mua sắm (đủ Free+60+120+180)
    refresh_shelf_last_room: bool = True       # phòng cuối refresh kệ shop (100 coin, ≤2 lượt)
    refresh_cards_no_recommend: bool = True    # màn chọn thẻ không có 👍 -> refresh bộ thẻ 1 lần (40 coin)
    # --- Tinh chỉnh run ---
    brief_mode: bool = True                    # bật Brief (rút gọn mô tả thẻ, chạy nhanh hơn)
    save_record: bool = True                   # cuối run lưu Record (giữ setup cho Quick Battle sau)
    run_timeout: int = 2400                    # thời gian tối đa 1 run (giây)


class BountyConfig(BaseModel):
    """Tuỳ chọn task Bounty Trial (tiêu Vigor bằng Trial Quick Battle sweep).

    Mặc định = đúng hành vi cũ (task Stamina): Basic Trial, giữ nguyên difficulty game đang
    chọn, Quick Battle tự sweep tối đa theo Vigor.
    """
    # Loại Trial ("map"): 4 Trial trong Bounty hub —
    #   basic  = Basic Trial  (Basic Material)
    #   tierup = Tier-up Trial (Trekker Promotion)
    #   skill  = Skill Trial  (Skill Upgrade)
    #   emblem = Emblem Trial (Emblem Material)
    trial: str = 'basic'
    # Độ khó: 0 = giữ nguyên difficulty game đang chọn (không đụng); 1..6 = tự chọn difficulty đó.
    # Quick Battle luôn auto-clear (sweep) tối đa số lần theo Vigor hiện có.
    difficulty: int = 0


class EventConfig(BaseModel):
    """Tuỳ chọn task EventDaily (Quick Battle sweep ở Battle Stage của sự kiện đang diễn ra).

    Mặc định: chạy stage cao nhất, sweep tối đa theo Vigor. Vào event qua BANNER sự kiện ở home
    (asset event/EVENT_BANNER.png) — mỗi đợt sự kiện đổi banner + đổi stage nên cần re-crop banner
    và chỉnh lại stage; xem hướng dẫn ở docs/game-map.md mục Event.
    """
    # Stage sẽ Quick Battle. '' = stage CAO NHẤT (phải-nhất trong danh sách, thường tối ưu thưởng).
    # 'W-N' (vd '1-12') = tự cuộn danh sách + OCR badge để chọn đúng stage đó.
    stage: str = ''
    # Số trận Quick Battle. 0 = tối đa theo Vigor hiện có (nút ">>"); N>0 = đúng N trận.
    battles: int = 0


class Config(BaseModel):
    emulator: EmulatorConfig = Field(default_factory=EmulatorConfig)
    server: str = 'en'
    # Ngôn ngữ giao diện desktop: 'vi' | 'en' (đổi ở trang Home). Không ảnh hưởng server game.
    language: str = 'vi'
    # Giờ reset daily theo UTC. 11:00 UTC = 04:00 UTC-7 theo chuẩn Yostar EN.
    # TODO(Phase 2): xác minh giờ reset thật của Stella Sora EN trong game.
    daily_reset_utc: str = '11:00'
    # Cleanup có đóng hẳn game không (mặc định để game ở màn hình chính)
    close_game_on_cleanup: bool = False
    ascension: AscensionConfig = Field(default_factory=AscensionConfig)
    bounty: BountyConfig = Field(default_factory=BountyConfig)
    event: EventConfig = Field(default_factory=EventConfig)
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
        # Task trong DEFAULT_OFF_TASKS tắt sẵn khi TẠO MỚI (người chơi tự bật;
        # đổi rồi thì lưu lại như bình thường). Config đã có sẵn thì giữ nguyên trạng thái đã lưu.
        if name not in self.tasks:
            self.tasks[name] = TaskSettings(enable=name not in DEFAULT_OFF_TASKS)
        return self.tasks[name]

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

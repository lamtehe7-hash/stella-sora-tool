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
#   EventFirstClear — như EventDaily: sự kiện theo đợt + tốn Vigor đánh thật từng stage.
DEFAULT_OFF_TASKS = {'Ascension', 'BountyTrial', 'EventDaily', 'EventFirstClear'}


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
    # ⚠️ KHÔNG dùng 'misstep' để farm: đây là tháp tập sự ngắn (~7 tầng), stub/coin thấp
    # (xem docs/ascension-strategy.md §1).
    map: str = ''
    # --- Chọn Difficulty (khảo sát go/05_difficulty2.png) ---
    # Phần thưởng tăng ĐƠN ĐIỆU theo difficulty (Diff2≈210, Diff7≈430 stub/clear; +coin; +trần điểm
    # Record) — giữ bậc game nhớ có thể bỏ lỡ nhiều thưởng.
    #   0 = TỰ nâng lên bậc đã-clear CAO NHẤT (quét lên từ bậc hiện tại tới khi Quick Battle hết sáng;
    #       chỉ đi LÊN, không bao giờ chọn bậc chưa clear) — MẶC ĐỊNH.
    #   2..8 = ép đúng bậc đó (chỉ đổi nếu Quick Battle bậc đó sáng; không thì cảnh báo + giữ nguyên).
    difficulty: int = 0
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
    # --- Mục tiêu tối ưu (POWER vs SCORE) ---
    #   power = Record tái sử dụng mạnh: mua potential + enhance, Melody chỉ khi Harmony Skill cần.
    #           MẶC ĐỊNH — khớp meta CN 塔8 (potential > note cho sát thương). Đã kiểm chứng.
    #   score = farm Journey Ticket Stub bằng điểm Record (mua nhiều Note + thẻ mới, tối thiểu enhance).
    #           ⚠️ THỬ NGHIỆM, chưa code + chỉ đáng nếu stub phụ thuộc rank Record khi LƯU (cần test
    #           live — xem docs/ascension-strategy.md §8). Đặt 'score' hiện chạy như 'power' + cảnh báo.
    objective: str = 'power'
    # --- Chiến lược Shop ---
    buy_melody_when_needed_only: bool = True   # Melody chỉ mua khi dialog có panel Relevant Harmony Skills
    enhance_milestone: int = 180               # giữa run enhance tới hết bậc này rồi giữ coin cho shop sau
    enhance_reserve: int = 360                 # coin chừa khi mua sắm GIỮA RUN (đủ Free+60+120+180)
    # PHÒNG CUỐI chừa ít hơn (chỉ 2 bậc enhance rẻ nhất 60+120=180) để CẢ 2 refresh charge được dùng
    # (refresh surface SALE; 1 SALE potential 45-72 rẻ/level hơn enhance bậc 180). Xem docs §3.
    enhance_reserve_last_room: int = 180
    # Refresh kệ shop: chỉ ở PHÒNG CUỐI (EV tối ưu — coin mất trắng khi rời nên opportunity cost ~0;
    # phòng đầu/giữa opportunity cost cao). 100 coin/lượt, tối đa 2 lượt/RUN (research-gated Lab2=1/Lab3=2).
    refresh_shelf_last_room: bool = True
    refresh_cards_no_recommend: bool = True    # màn chọn thẻ không có 👍 -> refresh bộ thẻ 1 lần (40 coin)
    # Event/Choice Domain: ưu tiên option cho phần thưởng ITEM free (Potential/Note — tag KHÔNG có
    # icon coin) thay vì mù bấm option dưới cùng. Không đọc được -> vẫn về option dưới cùng (an toàn).
    # BỎ TICK để quay lại hành vi cũ (luôn bấm dưới cùng).
    smart_event_choice: bool = True
    # --- Tinh chỉnh run ---
    # Bỏ qua Ascension khi Weekly Limit đã đầy (N/3000) — run lúc đó = 0 stub, chỉ phí vé.
    # BỎ TICK nếu vẫn muốn chạy để build sức mạnh Record (POWER) dù đã capped.
    skip_when_capped: bool = True
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


class EventFirstClearConfig(BaseModel):
    """Tuỳ chọn task EventFirstClear (tự đánh Deploy + Auto-Battle các stage còn sao XÁM để lấy
    quà First Clear).

    3 checkbox tương ứng 3 tab độ khó góc dưới-trái màn Battle Stage. Độ khó đang KHOÁ sẽ tự bỏ
    qua. Mỗi lần chạy chỉ đánh các stage CHƯA first-clear (sao xám) rồi hẹn lại sau reset.
    """
    normal: bool = True        # tab Normal
    hard: bool = True          # tab Hard (chỉ chạy khi đã mở khoá)
    challenge: bool = True     # tab thứ 3 (Challenge — tên tuỳ event; chỉ chạy khi mở khoá)
    max_stages: int = 12       # trần số stage đánh mỗi lần chạy (chống lặp vô hạn)
    run_timeout: int = 180     # thời gian tối đa 1 trận (giây) — Auto-Battle tự bật khi phát hiện OFF


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
    event_first_clear: EventFirstClearConfig = Field(default_factory=EventFirstClearConfig)
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

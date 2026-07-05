"""App desktop kiểu Alas: web UI (assets/gui) bọc trong cửa sổ WebView2 qua pywebview.

Chạy dev:  python app.py            (thêm --debug để mở devtools)
Bản exe:   app.exe (build bằng pyinstaller app.spec) — assets/ config/ log/ nằm cạnh exe.
Giao diện web thuần vẫn dùng được: python gui.py
"""
import sys
import threading
from datetime import timezone

import webview

from module.config import ROOT, Config, utcnow
from module.logger import gui_log, logger
from module.scheduler import ORDER, Scheduler, run_single

_scheduler: Scheduler | None = None
_single: threading.Thread | None = None


def _busy() -> bool:
    return (_scheduler is not None and _scheduler.is_alive()) or \
           (_single is not None and _single.is_alive())


def _fmt_next_run(dt) -> str:
    if dt <= utcnow():
        return 'sẵn sàng'
    return dt.replace(tzinfo=timezone.utc).astimezone().strftime('%d/%m %H:%M')


# Toast trả về JS — song ngữ theo cfg.language (UI chrome khác dịch phía JS trong app.js).
MSG = {
    'busy_running':      ('Đang chạy rồi', 'Already running'),
    'sched_started':     ('Đã bắt đầu scheduler', 'Scheduler started'),
    'sched_not_running': ('Scheduler không chạy', 'Scheduler is not running'),
    'sched_stopping':    ('Sẽ dừng sau khi task hiện tại xong', 'Will stop after the current task'),
    'task_on':           ('{n}: BẬT', '{n}: ON'),
    'task_off':          ('{n}: TẮT', '{n}: OFF'),
    'run_due':           ('{n}: đến hạn ngay — scheduler sẽ chạy trong vòng lặp',
                          '{n}: queued now — the scheduler will pick it up'),
    'busy_other':        ('Đang bận chạy task khác', 'Busy running another task'),
    'run_started':       ('Đang chạy {n}...', 'Running {n}...'),
    'cfg_saved':         ('Đã lưu cấu hình', 'Configuration saved'),
    'asc_saved':         ('Đã lưu cài đặt Ascension', 'Ascension settings saved'),
    'bounty_saved':      ('Đã lưu cài đặt Bounty Trial', 'Bounty Trial settings saved'),
    'event_saved':       ('Đã lưu cài đặt Event', 'Event settings saved'),
}
PRESET_BEHAVIORS = ('warn', 'skip', 'abort')
CARD_PRIORITIES = ('level_gain', 'super_rare', 'leftmost')
MAP_KEYS = ('', 'currents', 'dust', 'storm', 'misstep')
TRIAL_KEYS = ('basic', 'tierup', 'skill', 'emblem')


def _m(cfg, key: str, **kw) -> str:
    vi, en = MSG[key]
    return (en if getattr(cfg, 'language', 'vi') == 'en' else vi).format(**kw)


class Api:
    """Cầu nối JS ↔ Python (pywebview js_api). Mỗi method được gọi từ assets/gui/app.js."""

    def poll(self, last_seq: int = 0) -> dict:
        cfg = Config.load()
        now = utcnow()
        tasks = []
        for name in ORDER:
            t = cfg.task(name)
            tasks.append({
                'name': name,
                'enable': t.enable,
                'ready': t.next_run <= now,
                'next_run': _fmt_next_run(t.next_run),
            })

        alive = _scheduler is not None and _scheduler.is_alive()
        if _scheduler is None:
            state, current, error = 'off', '', ''
        else:
            state, current, error = _scheduler.state, _scheduler.current_task, _scheduler.error

        snapshot = list(gui_log)
        lines = [line for seq, line in snapshot if seq > last_seq]
        seq = snapshot[-1][0] if snapshot else last_seq
        return {'state': state, 'current': current, 'error': error, 'alive': alive,
                'tasks': tasks, 'lines': lines, 'seq': seq}

    def start(self) -> str:
        global _scheduler
        cfg = Config.load()
        if _busy():
            return _m(cfg, 'busy_running')
        _scheduler = Scheduler()
        _scheduler.start()
        logger.info('GUI: bắt đầu scheduler')
        return _m(cfg, 'sched_started')

    def stop(self) -> str:
        cfg = Config.load()
        if _scheduler is None or not _scheduler.is_alive():
            return _m(cfg, 'sched_not_running')
        _scheduler.stop()
        return _m(cfg, 'sched_stopping')

    def toggle(self, name: str) -> str:
        cfg = Config.load()
        t = cfg.task(name)
        t.enable = not t.enable
        cfg.save()
        logger.info(f'GUI: {name} -> {"BẬT" if t.enable else "TẮT"}')
        return _m(cfg, 'task_on' if t.enable else 'task_off', n=name)

    def run_now(self, name: str) -> str:
        global _single
        cfg = Config.load()
        cfg.task(name).next_run = utcnow()
        cfg.save()
        if _scheduler is not None and _scheduler.is_alive():
            return _m(cfg, 'run_due', n=name)
        if _busy():
            return _m(cfg, 'busy_other')

        def _run():
            try:
                run_single(name)
            except Exception as e:
                logger.error(f'{name} lỗi: {e}')

        _single = threading.Thread(target=_run, name=f'sst-single-{name}', daemon=True)
        _single.start()
        return _m(cfg, 'run_started', n=name)

    def get_config(self) -> dict:
        cfg = Config.load()
        return {
            'serial': cfg.emulator.serial,
            'adb_path': cfg.emulator.adb_path,
            'daily_reset_utc': cfg.daily_reset_utc,
            'close_game_on_cleanup': cfg.close_game_on_cleanup,
        }

    def save_config(self, data: dict) -> str:
        cfg = Config.load()
        cfg.emulator.serial = data['serial']
        cfg.emulator.adb_path = data['adb_path']
        cfg.daily_reset_utc = data['daily_reset_utc']
        cfg.close_game_on_cleanup = bool(data['close_game_on_cleanup'])
        cfg.save()
        logger.info('GUI: đã lưu cấu hình')
        return _m(cfg, 'cfg_saved')

    # --- Ngôn ngữ giao diện (toggle ở Home) ---

    def get_lang(self) -> str:
        return Config.load().language

    def set_lang(self, lang: str) -> str:
        cfg = Config.load()
        cfg.language = 'en' if lang == 'en' else 'vi'
        cfg.save()
        logger.info(f'GUI: ngôn ngữ -> {cfg.language}')
        return cfg.language

    # --- Cài đặt task Ascension ---

    def get_ascension(self) -> dict:
        return Config.load().ascension.model_dump()

    def save_ascension(self, data: dict) -> str:
        cfg = Config.load()
        a = cfg.ascension
        a.runs_per_session = max(1, min(50, int(data['runs_per_session'])))
        if data.get('map') in MAP_KEYS:
            a.map = data['map']
        a.squad = max(0, min(20, int(data['squad'])))
        if data.get('preset_behavior') in PRESET_BEHAVIORS:
            a.preset_behavior = data['preset_behavior']
        if data.get('card_priority') in CARD_PRIORITIES:
            a.card_priority = data['card_priority']
        a.buy_melody_when_needed_only = bool(data['buy_melody_when_needed_only'])
        a.enhance_milestone = max(0, int(data['enhance_milestone']))
        a.enhance_reserve = max(0, int(data['enhance_reserve']))
        a.refresh_shelf_last_room = bool(data['refresh_shelf_last_room'])
        a.refresh_cards_no_recommend = bool(data['refresh_cards_no_recommend'])
        a.brief_mode = bool(data['brief_mode'])
        a.save_record = bool(data['save_record'])
        a.run_timeout = max(300, min(7200, int(data['run_timeout'])))
        cfg.save()
        logger.info('GUI: đã lưu cài đặt Ascension')
        return _m(cfg, 'asc_saved')

    # --- Cài đặt task Bounty Trial ---

    def get_bounty(self) -> dict:
        return Config.load().bounty.model_dump()

    def save_bounty(self, data: dict) -> str:
        cfg = Config.load()
        b = cfg.bounty
        if data.get('trial') in TRIAL_KEYS:
            b.trial = data['trial']
        b.difficulty = max(0, min(6, int(data['difficulty'])))
        cfg.save()
        logger.info('GUI: đã lưu cài đặt Bounty Trial')
        return _m(cfg, 'bounty_saved')

    # --- Cài đặt task EventDaily ---

    def get_event(self) -> dict:
        return Config.load().event.model_dump()

    def save_event(self, data: dict) -> str:
        cfg = Config.load()
        e = cfg.event
        e.stage = str(data.get('stage', '')).strip()
        e.battles = max(0, min(999, int(data['battles'])))
        cfg.save()
        logger.info('GUI: đã lưu cài đặt Event')
        return _m(cfg, 'event_saved')


WIN_W, WIN_H = 1380, 900


def _fit_and_show(window) -> None:
    """Thu cửa sổ cho vừa màn hình (chừa taskbar) rồi căn giữa và hiện ra.
    Màn hình nhỏ hơn kích thước mặc định là nguyên nhân cửa sổ mở ra bị che mép dưới."""
    try:
        s = webview.screens[0]
        sw, sh = s.width, s.height
        w = min(WIN_W, sw - 40)
        h = min(WIN_H, sh - 80)          # chừa taskbar + viền tiêu đề
        if (w, h) != (WIN_W, WIN_H):
            window.resize(w, h)
        window.move(max(0, (sw - w) // 2), max(0, (sh - h) // 2 - 10))
        logger.info(f'SST desktop: cửa sổ {w}x{h} trên màn hình {sw}x{sh}')
    except Exception as e:
        logger.warning(f'Không căn/thu cửa sổ: {e}')
    finally:
        window.show()


def main() -> None:
    index = ROOT / 'assets' / 'gui' / 'index.html'
    if not index.exists():
        print(f'Không tìm thấy giao diện: {index} — assets/ phải nằm cạnh app.exe')
        sys.exit(1)
    window = webview.create_window(
        'Stella Sora Tool', str(index), js_api=Api(),
        width=WIN_W, height=WIN_H, min_size=(1024, 640), hidden=True,
    )
    logger.info('SST desktop: mở cửa sổ')
    webview.start(_fit_and_show, window, debug='--debug' in sys.argv)


if __name__ == '__main__':
    main()

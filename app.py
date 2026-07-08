"""App desktop kiểu Alas: web UI (assets/gui) bọc trong cửa sổ WebView2 qua pywebview.

Chạy dev:  python app.py            (thêm --debug để mở devtools)
Bản exe:   app.exe (build bằng pyinstaller app.spec) — assets/ config/ log/ nằm cạnh exe.
Giao diện web thuần vẫn dùng được: python gui.py
"""
import sys
import threading
from datetime import timezone

import webview

from module.ascension_analysis import (
    analyze_session, cleanup_images, image_dirs, images_size_bytes, render_report_md,
)
from module.config import ROOT, Config, MailTarget, utcnow
from module.exception import TaskInterrupted
from module.logger import gui_log, logger
from module.scheduler import ORDER, Scheduler, run_single
from module.stop_signal import request_stop

CAPTURE_ROOT = ROOT / 'data' / 'ascension_capture'

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
    'sched_stopping':    ('Đang dừng — ngắt task hiện tại...', 'Stopping — interrupting the current task...'),
    'single_stopping':   ('Đang ngắt task...', 'Interrupting the task...'),
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
    'efc_saved':         ('Đã lưu cài đặt Event First Clear', 'Event First Clear settings saved'),
    'heartlink_saved':   ('Đã lưu cài đặt Heartlink', 'Heartlink settings saved'),
    'asc_no_session':    ('Chưa có/chọn phiên capture', 'No capture session selected'),
    'asc_exported':      ('Đã xuất báo cáo → {p}', 'Report exported → {p}'),
    'asc_export_cancelled': ('Đã huỷ xuất báo cáo', 'Export cancelled'),
    'asc_cleaned':       ('Đã dọn {n} thư mục ảnh, giải phóng {mb}', 'Cleaned {n} image folders, freed {mb}'),
}
PRESET_BEHAVIORS = ('warn', 'skip', 'abort')
CARD_PRIORITIES = ('level_gain', 'super_rare', 'leftmost')
MAP_KEYS = ('', 'currents', 'dust', 'storm', 'misstep')
OBJECTIVES = ('power', 'score')
DISSOLVE_BANDS = ('silver', 'green', 'blue', 'golden')
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
        if _scheduler is not None and _scheduler.is_alive():
            _scheduler.stop()  # set luôn cờ dừng-ngay → ngắt task hiện tại
            return _m(cfg, 'sched_stopping')
        if _single is not None and _single.is_alive():
            request_stop()  # 'Chạy ngay' cũng ngắt được
            return _m(cfg, 'single_stopping')
        return _m(cfg, 'sched_not_running')

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
            except TaskInterrupted:
                logger.info(f'{name} bị ngắt theo yêu cầu Dừng của người dùng.')
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
        _diff = int(data.get('difficulty', a.difficulty))
        a.difficulty = _diff if _diff == 0 or 2 <= _diff <= 8 else a.difficulty
        a.skip_when_capped = bool(data.get('skip_when_capped', a.skip_when_capped))
        if data.get('map') in MAP_KEYS:
            a.map = data['map']
        a.squad = max(0, min(20, int(data['squad'])))
        if data.get('preset_behavior') in PRESET_BEHAVIORS:
            a.preset_behavior = data['preset_behavior']
        if data.get('card_priority') in CARD_PRIORITIES:
            a.card_priority = data['card_priority']
        a.smart_event_choice = bool(data.get('smart_event_choice', a.smart_event_choice))
        if data.get('objective') in OBJECTIVES:
            a.objective = data['objective']
        a.buy_melody_when_needed_only = bool(data['buy_melody_when_needed_only'])
        a.enhance_milestone = max(0, int(data['enhance_milestone']))
        a.enhance_reserve = max(0, int(data['enhance_reserve']))
        a.enhance_reserve_last_room = max(0, int(data.get('enhance_reserve_last_room',
                                                          a.enhance_reserve_last_room)))
        a.refresh_shelf_last_room = bool(data['refresh_shelf_last_room'])
        a.refresh_cards_no_recommend = bool(data['refresh_cards_no_recommend'])
        a.brief_mode = bool(data['brief_mode'])
        a.save_record = bool(data['save_record'])
        a.dissolve_record = bool(data.get('dissolve_record', a.dissolve_record))
        if data.get('dissolve_max_band') in DISSOLVE_BANDS:
            a.dissolve_max_band = data['dissolve_max_band']
        a.run_timeout = max(300, min(7200, int(data['run_timeout'])))
        cfg.save()
        logger.info('GUI: đã lưu cài đặt Ascension')
        return _m(cfg, 'asc_saved')

    # --- Phân tích phiên capture Ascension (thuần Python, KHÔNG cần AI) ---

    def list_capture_sessions(self) -> list:
        """Danh sách phiên capture (mới nhất trước) cho dropdown giao diện."""
        if not CAPTURE_ROOT.exists():
            return []
        out = []
        for d in sorted((p for p in CAPTURE_ROOT.glob('2*') if p.is_dir()), reverse=True):
            imgs = image_dirs(d)
            out.append({'name': d.name, 'has_images': bool(imgs), 'n_image_dirs': len(imgs)})
        return out

    def analyze_capture(self, session: str) -> dict:
        """Phân tích 1 phiên → metrics (player/technical/per_run) + dung lượng ảnh (MB) để hiển thị."""
        d = CAPTURE_ROOT / session
        if not session or not d.exists():
            return {'error': _m(Config.load(), 'asc_no_session')}
        data = analyze_session(d)
        data['images_mb'] = round(images_size_bytes(d) / 1024 / 1024, 1)
        logger.info(f'GUI: phân tích phiên capture {session}')
        return data

    def export_capture_report(self, session: str) -> str:
        """Xuất báo cáo Markdown cho người dùng lưu. Ưu tiên hộp thoại Save; fallback ghi vào
        thư mục phiên (sống sót khi dọn ảnh)."""
        cfg = Config.load()
        d = CAPTURE_ROOT / session
        if not session or not d.exists():
            return _m(cfg, 'asc_no_session')
        md = render_report_md(analyze_session(d))
        dest = None
        try:
            wins = webview.windows
            if wins:
                picked = wins[0].create_file_dialog(
                    webview.SAVE_DIALOG, save_filename=f'ascension_{session}.md',
                    file_types=('Markdown (*.md)', 'All files (*.*)'))
                if picked:
                    dest = picked if isinstance(picked, str) else picked[0]
                else:                          # người dùng bấm Cancel → KHÔNG ghi gì (review 2026-07-08)
                    return _m(cfg, 'asc_export_cancelled')
        except Exception:
            dest = None
        if dest is None:                       # không có window / dialog lỗi: fallback ghi vào thư mục phiên
            dest = str(d / f'ascension_{session}.md')
        from pathlib import Path
        Path(dest).write_text(md, encoding='utf-8')
        logger.info(f'GUI: xuất báo cáo phiên {session} → {dest}')
        return _m(cfg, 'asc_exported', p=dest)

    def cleanup_capture_images(self, session: str) -> str:
        """Xoá thư mục ảnh run_* của phiên để giải phóng ổ (GIỮ log + báo cáo)."""
        cfg = Config.load()
        d = CAPTURE_ROOT / session
        if not session or not d.exists():
            return _m(cfg, 'asc_no_session')
        res = cleanup_images(d)
        mb = f"{res['freed_bytes'] / 1024 / 1024:.1f} MB"
        logger.info(f'GUI: dọn ảnh phiên {session} — {res["removed_dirs"]} thư mục, {mb}')
        return _m(cfg, 'asc_cleaned', n=res['removed_dirs'], mb=mb)

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

    # --- Cài đặt task EventFirstClear ---

    def get_event_first_clear(self) -> dict:
        return Config.load().event_first_clear.model_dump()

    def save_event_first_clear(self, data: dict) -> str:
        cfg = Config.load()
        e = cfg.event_first_clear
        e.normal = bool(data['normal'])
        e.hard = bool(data['hard'])
        e.challenge = bool(data['challenge'])
        e.max_stages = max(1, min(50, int(data['max_stages'])))
        e.run_timeout = max(60, min(600, int(data['run_timeout'])))
        cfg.save()
        logger.info('GUI: đã lưu cài đặt Event First Clear')
        return _m(cfg, 'efc_saved')

    # --- Cài đặt task Heartlink ---

    def get_heartlink(self) -> dict:
        return Config.load().heartlink.model_dump()

    def save_heartlink(self, data: dict) -> str:
        cfg = Config.load()
        h = cfg.heartlink
        h.do_invite = bool(data.get('do_invite', True))
        h.invite_count = max(1, min(5, int(data['invite_count'])))
        h.send_gift = bool(data['send_gift'])
        h.invite_targets = [s.strip() for s in str(data.get('invite_targets', '')).split(',') if s.strip()]
        h.do_mail = bool(data.get('do_mail', True))
        h.mail_count = max(1, min(10, int(data.get('mail_count', 10))))
        # Custom Mail: (name,qty), tổng ≤ mail_count & ≤10
        targets, budget = [], h.mail_count
        for row in data.get('mail_targets', []):
            name = str(row.get('name', '')).strip()
            qty = max(0, int(row.get('qty', 0)))
            if name and qty > 0 and budget > 0:
                qty = min(qty, budget)
                targets.append(MailTarget(name=name, qty=qty))
                budget -= qty
        h.mail_targets = targets
        cfg.save()
        logger.info('GUI: đã lưu cài đặt Heartlink')
        return _m(cfg, 'heartlink_saved')


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

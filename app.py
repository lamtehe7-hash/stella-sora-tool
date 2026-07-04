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
        if _busy():
            return 'Đang chạy rồi'
        _scheduler = Scheduler()
        _scheduler.start()
        logger.info('GUI: bắt đầu scheduler')
        return 'Đã bắt đầu scheduler'

    def stop(self) -> str:
        if _scheduler is None or not _scheduler.is_alive():
            return 'Scheduler không chạy'
        _scheduler.stop()
        return 'Sẽ dừng sau khi task hiện tại xong'

    def toggle(self, name: str) -> str:
        cfg = Config.load()
        t = cfg.task(name)
        t.enable = not t.enable
        cfg.save()
        logger.info(f'GUI: {name} -> {"BẬT" if t.enable else "TẮT"}')
        return f'{name}: {"BẬT" if t.enable else "TẮT"}'

    def run_now(self, name: str) -> str:
        global _single
        cfg = Config.load()
        cfg.task(name).next_run = utcnow()
        cfg.save()
        if _scheduler is not None and _scheduler.is_alive():
            return f'{name}: đến hạn ngay — scheduler sẽ chạy trong vòng lặp'
        if _busy():
            return 'Đang bận chạy task khác'

        def _run():
            try:
                run_single(name)
            except Exception as e:
                logger.error(f'{name} lỗi: {e}')

        _single = threading.Thread(target=_run, name=f'sst-single-{name}', daemon=True)
        _single.start()
        return f'Đang chạy {name}...'

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
        return 'Đã lưu cấu hình'


def main() -> None:
    index = ROOT / 'assets' / 'gui' / 'index.html'
    if not index.exists():
        print(f'Không tìm thấy giao diện: {index} — assets/ phải nằm cạnh app.exe')
        sys.exit(1)
    webview.create_window(
        'Stella Sora Tool', str(index), js_api=Api(),
        width=1380, height=900, min_size=(1024, 640),
    )
    logger.info('SST desktop: mở cửa sổ')
    webview.start(debug='--debug' in sys.argv)


if __name__ == '__main__':
    main()

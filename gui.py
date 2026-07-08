"""Giao diện web kiểu ALAS (pywebio): bật/tắt task, start/stop scheduler, log trực tiếp.

Chạy dev:  python gui.py            (mở http://localhost:22270, tự bật trình duyệt)
Bản exe:   SST.exe (build bằng dev_tools/build_exe.ps1) — assets/ config/ log/ nằm cạnh exe.
"""
import threading
import time
from datetime import timezone

from pywebio import config as pw_config
from pywebio.input import checkbox, input as pw_input, input_group
from pywebio.output import (put_buttons, put_markdown, put_scope, put_scrollable,
                            put_table, put_text, toast, use_scope)
from pywebio.platform.tornado import start_server

from module.config import Config, utcnow
from module.exception import TaskInterrupted
from module.logger import gui_log, logger
from module.scheduler import ORDER, Scheduler, run_single
from module.stop_signal import request_stop

PORT = 22270

_scheduler: Scheduler | None = None
_single: threading.Thread | None = None


def _busy() -> bool:
    return (_scheduler is not None and _scheduler.is_alive()) or \
           (_single is not None and _single.is_alive())


# --- callbacks -------------------------------------------------------------

def on_start(_=None) -> None:
    global _scheduler
    if _busy():
        toast('Đang chạy rồi', color='warn')
        return
    _scheduler = Scheduler()
    _scheduler.start()
    logger.info('GUI: bắt đầu scheduler')


def on_stop(_=None) -> None:
    if _scheduler is not None and _scheduler.is_alive():
        _scheduler.stop()  # set luôn cờ dừng-ngay → ngắt task hiện tại
        toast('Đang dừng — ngắt task hiện tại...')
        return
    if _single is not None and _single.is_alive():
        request_stop()  # 'Chạy ngay' cũng ngắt được
        toast('Đang ngắt task...')
        return
    toast('Scheduler không chạy', color='warn')


def on_run_now(name: str) -> None:
    global _single
    cfg = Config.load()
    cfg.task(name).next_run = utcnow()
    cfg.save()
    if _scheduler is not None and _scheduler.is_alive():
        toast(f'{name}: đến hạn ngay — scheduler sẽ chạy trong vòng lặp')
        return
    if _busy():
        toast('Đang bận chạy task khác', color='warn')
        return

    def _run():
        try:
            run_single(name)
        except TaskInterrupted:
            logger.info(f'{name} bị ngắt theo yêu cầu Dừng của người dùng.')
        except Exception as e:
            logger.error(f'{name} lỗi: {e}')

    _single = threading.Thread(target=_run, name=f'sst-single-{name}', daemon=True)
    _single.start()


def on_toggle(name: str) -> None:
    cfg = Config.load()
    t = cfg.task(name)
    t.enable = not t.enable
    cfg.save()
    logger.info(f'GUI: {name} -> {"BẬT" if t.enable else "TẮT"}')


def on_config(_=None) -> None:
    cfg = Config.load()
    data = input_group('Cấu hình', [
        pw_input('Serial giả lập', name='serial', value=cfg.emulator.serial),
        pw_input('Đường dẫn adb.exe', name='adb_path', value=cfg.emulator.adb_path),
        pw_input('Giờ reset daily (UTC, HH:MM)', name='reset', value=cfg.daily_reset_utc),
        checkbox('Cleanup', name='cleanup',
                 options=[{'label': 'Đóng game khi Cleanup', 'value': 'close',
                           'selected': cfg.close_game_on_cleanup}]),
    ])
    if data is None:
        return
    cfg.emulator.serial = data['serial'].strip()
    cfg.emulator.adb_path = data['adb_path'].strip()
    cfg.daily_reset_utc = data['reset'].strip()
    cfg.close_game_on_cleanup = 'close' in data['cleanup']
    cfg.save()
    toast('Đã lưu cấu hình')
    logger.info('GUI: đã lưu cấu hình')


# --- render ----------------------------------------------------------------

def _status_line() -> str:
    if _scheduler is None:
        return '⚪ Chưa chạy — bấm **Bắt đầu**'
    s = _scheduler
    return {
        'running': f'🟢 Đang chạy task **{s.current_task}**',
        'waiting': '🟡 Chờ task đến hạn',
        'stopped': '⚪ Đã dừng',
        'error': f'🔴 Lỗi: {s.error}',
        'human': f'🔴 {s.error}',
        'idle': '🟡 Đang khởi động...',
    }.get(s.state, s.state)


def _fmt_next_run(dt) -> str:
    if dt <= utcnow():
        return 'sẵn sàng'
    return dt.replace(tzinfo=timezone.utc).astimezone().strftime('%d/%m %H:%M')


def _tasks_snapshot(cfg: Config) -> list:
    running = _scheduler.current_task if _scheduler and _scheduler.is_alive() else ''
    rows = []
    for name in ORDER:
        t = cfg.task(name)
        rows.append((name, t.enable, _fmt_next_run(t.next_run), name == running))
    return rows


def _render_tasks(snapshot: list) -> None:
    header = ['Task', 'Bật', 'Chạy kế tiếp', '']
    rows = []
    for name, enable, next_run, running in snapshot:
        state = '▶️ đang chạy' if running else ('✅' if enable else '⛔ tắt')
        rows.append([
            name, state, next_run,
            put_buttons([
                {'label': 'Tắt' if enable else 'Bật', 'value': 'toggle', 'color': 'secondary'},
                {'label': 'Chạy ngay', 'value': 'run', 'color': 'primary'},
            ], onclick=lambda v, n=name: on_toggle(n) if v == 'toggle' else on_run_now(n),
                small=True),
        ])
    with use_scope('tasks', clear=True):
        put_table(rows, header=header)


@pw_config(title='Stella Sora Tool', theme='dark')
def main() -> None:
    put_markdown('# 🌠 Stella Sora Tool')
    put_buttons([
        {'label': '▶ Bắt đầu', 'value': 'start', 'color': 'success'},
        {'label': '■ Dừng', 'value': 'stop', 'color': 'danger'},
        {'label': '⚙ Cấu hình', 'value': 'config', 'color': 'secondary'},
    ], onclick=[on_start, on_stop, on_config])
    put_scope('status')
    put_markdown('## Task')
    put_scope('tasks')
    put_markdown('## Log')
    put_scrollable(put_scope('log'), height=320, keep_bottom=True)

    last_status, last_snapshot, last_seq = None, None, 0
    while True:
        status = _status_line()
        if status != last_status:
            with use_scope('status', clear=True):
                put_markdown(status)
            last_status = status

        snapshot = _tasks_snapshot(Config.load())
        if snapshot != last_snapshot:
            _render_tasks(snapshot)
            last_snapshot = snapshot

        new_lines = [line for seq, line in list(gui_log) if seq > last_seq]
        if new_lines:
            last_seq = list(gui_log)[-1][0]
            with use_scope('log'):
                for line in new_lines:
                    put_text(line)
        time.sleep(1)


if __name__ == '__main__':
    logger.info(f'GUI: http://localhost:{PORT}')
    start_server(main, port=PORT, auto_open_webbrowser=True)

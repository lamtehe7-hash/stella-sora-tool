"""Chạy task Ascension N run và CHỤP LẠI mọi screenshot + log + coins-timeline
để làm data nghiên cứu tối ưu (session sau). KHÔNG sửa logic task — chỉ monkey-patch
`Device.screenshot` (lưu mỗi frame) và gắn thêm 1 file-log-handler.

Dùng (từ gốc repo):
    venv\\Scripts\\python.exe dev_tools\\ascension_capture.py
    venv\\Scripts\\python.exe dev_tools\\ascension_capture.py --runs 70 --map storm --difficulty 8 --squad 1
    ... --jpg            # lưu JPG q92 thay vì PNG (nhẹ ổ ~5-8x, vẫn đủ soi)
    ... --no-login       # bỏ bước Login (nếu game chắc chắn đã ở Home)

Output (đã .gitignore) — data/ascension_capture/<session_ts>/:
    session.log        # TOÀN BỘ log task: mọi quyết định (difficulty / card pick + lý do / shop / leave)
    frames.jsonl       # 1 dòng/screenshot: {run, step, ts_ms, coins, file} + marker {event:"run_start"}
    config_used.json   # config ascension thực tế đã áp (để tái lập)
    run_00_setup/      # frame điều hướng trước run 1 (login + map/difficulty/squad/disc lần đầu)
    run_01/ ... run_NN/  # mỗi run Quick Battle 1 thư mục ảnh

⚠️ Config chỉ set trong RAM — KHÔNG ghi đè config/stella.json của bạn.
⚠️ skip_when_capped=False (chạy đủ N run kể cả tuần đã capped 3000 — mục tiêu là DATA, không phải stub).
⚠️ preset_behavior='warn' (không abort giữa 70 run vì 1 lần đọc nhầm preset).
"""
import argparse
import json
import sys
import time
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import logging

from module.config import Config
from module.device.device import Device
from module.logger import logger
from module.ui.pages import (ASCENSION_CHECK, ASCENSION_ENTER, ASCENSION_TITLE, GO_CHECK,
                             GO_ENTER, page_asc_diff, page_ascension)
from tasks.ascension import (ASC_GIVE_UP, ASCENSION_QUICK_BATTLE, SAVE_RECORD, Ascension,
                             read_coins)
from tasks.login import Login

# --- state cho các hook (module-level vì monkey-patch dùng closure) ---
_session_dir: Path
_run_dir: Path
_jsonl = None
_run_idx = 0
_step = 0
_ext = 'png'
_jpg_params = [cv2.IMWRITE_JPEG_QUALITY, 92]


def _new_run() -> None:
    """Bắt đầu 1 thư mục run mới (gọi ở đầu mỗi _enter_run)."""
    global _run_idx, _step, _run_dir
    _run_idx += 1
    _step = 0
    _run_dir = _session_dir / f'run_{_run_idx:02d}'
    _run_dir.mkdir(parents=True, exist_ok=True)
    if _jsonl is not None:
        _jsonl.write(json.dumps({'event': 'run_start', 'run': _run_idx,
                                 'ts_ms': int(time.time() * 1000)}) + '\n')
        _jsonl.flush()
    logger.info(f'[capture] === RUN {_run_idx} -> {_run_dir.name}/ ===')


def _save_frame(img) -> None:
    """Lưu 1 screenshot + 1 dòng metadata (coins đọc được nếu màn có pill Starcoin)."""
    global _step
    _step += 1
    ts = int(time.time() * 1000)
    fn = _run_dir / f'{_step:04d}_{ts}.{_ext}'
    try:
        if _ext == 'jpg':
            cv2.imwrite(str(fn), img, _jpg_params)
        else:
            cv2.imwrite(str(fn), img)
    except Exception as e:  # I/O hỏng không được làm chết task
        logger.debug(f'[capture] lưu ảnh lỗi: {e}')
        return
    coins = None
    try:
        coins = read_coins(img)
    except Exception:
        pass
    if _jsonl is not None:
        _jsonl.write(json.dumps({'run': _run_idx, 'step': _step, 'ts_ms': ts,
                                 'coins': coins,
                                 'file': str(fn.relative_to(_session_dir))}) + '\n')
        _jsonl.flush()


def _install_hooks() -> None:
    orig_ss = Device.screenshot

    def patched_ss(self):
        img = orig_ss(self)
        _save_frame(img)
        return img

    Device.screenshot = patched_ss

    orig_enter = Ascension._enter_run

    def patched_enter(self):
        _new_run()
        return orig_enter(self)

    Ascension._enter_run = patched_enter


def main() -> None:
    global _session_dir, _run_dir, _jsonl, _ext

    ap = argparse.ArgumentParser(description='Chạy Ascension N run + capture data.')
    ap.add_argument('--runs', type=int, default=70)
    ap.add_argument('--map', default='storm',
                    choices=['storm', 'currents', 'dust', 'misstep', ''])
    ap.add_argument('--difficulty', type=int, default=8)
    ap.add_argument('--squad', type=int, default=1)
    ap.add_argument('--jpg', action='store_true', help='Lưu JPG q92 thay PNG (nhẹ ổ)')
    ap.add_argument('--no-login', action='store_true', help='Bỏ bước Login đầu')
    ap.add_argument('--resume', action='store_true',
                    help='Game đang KẸT giữa 1 run: chạy _run_loop dọn nốt run đó trước')
    ap.add_argument('--from-diff', action='store_true',
                    help='Bắt đầu vòng run từ page_asc_diff (né nav Home->ascension; giữ map+diff game nhớ)')
    args = ap.parse_args()

    _ext = 'jpg' if args.jpg else 'png'

    _session_dir = ROOT / 'data' / 'ascension_capture' / time.strftime('%Y%m%d_%H%M%S')
    _session_dir.mkdir(parents=True, exist_ok=True)
    _run_dir = _session_dir / 'run_00_setup'
    _run_dir.mkdir(parents=True, exist_ok=True)
    _jsonl = open(_session_dir / 'frames.jsonl', 'w', encoding='utf-8')

    # Toàn bộ log task -> session.log (chứa mọi quyết định của tool)
    fh = logging.FileHandler(_session_dir / 'session.log', encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-5s | %(message)s'))
    logger.addHandler(fh)

    config = Config.load()
    a = config.ascension
    a.runs_per_session = args.runs
    a.map = args.map
    a.difficulty = args.difficulty
    a.squad = args.squad
    a.skip_when_capped = False      # chạy đủ N run kể cả đã capped — mục tiêu là DATA
    a.preset_behavior = 'warn'      # không abort giữa chừng
    a.save_record = True            # nhánh Save Record đã verify -> run kết thúc sạch

    (_session_dir / 'config_used.json').write_text(
        a.model_dump_json(indent=2) if hasattr(a, 'model_dump_json') else json.dumps(vars(a), indent=2),
        encoding='utf-8')

    _install_hooks()

    logger.info(f'[capture] Session -> {_session_dir}')
    logger.info(f'[capture] map={args.map} diff={args.difficulty} squad={args.squad} '
                f'runs={args.runs} ext={_ext}')

    device = Device(config)
    device.connect()

    task = Ascension(config, device)
    task.cfg = config.ascension   # run() vốn tự set self.cfg; chế độ from-diff/resume set thủ công

    t0 = time.time()
    try:
        if args.resume:
            logger.info('[capture] RESUME — bỏ run pause hỏng để bắt đầu 70 run sạch...')
            # Chuỗi màn có thể gặp: Home -> Go -> card Ascension -> dialog "Return to Ascension?"
            # (Give Up đỏ) -> dialog "Sure to give up?" (Confirm teal) -> page_ascension sạch.
            # Vòng lặp xử lý mọi trạng thái để robust (game có thể đang ở bất kỳ bước nào).
            # Chuỗi: [Home->Go->card] -> "Return to Ascension?" (Give Up đỏ) -> "Sure to give up?"
            # (Confirm teal) -> màn Record (Save Record). Vòng lặp đóng dialog tới khi chạm màn Record
            # / asc_diff / page_ascension; sau đó giao _run_loop lo Save Record -> về asc_diff.
            for _ in range(8):
                task.device.screenshot()
                if (task.appear(SAVE_RECORD) or task.appear(ASCENSION_TITLE)
                        or task.appear(ASCENSION_CHECK)):
                    logger.info('[capture] Đã tới màn Record / trang Ascension — giao _run_loop')
                    break
                if task.appear(ASC_GIVE_UP):
                    logger.info('[capture] Dialog "Return to Ascension?" -> Give Up')
                    task.device.click(ASC_GIVE_UP)
                    time.sleep(2.5)
                    continue
                if task.appear(GO_ENTER):
                    logger.info('[capture] Ở Home -> vào Go -> card Ascension')
                    task.appear_then_click(GO_ENTER, interval=2)
                    time.sleep(1.5)
                    if task.wait_until_appear(GO_CHECK, timeout=8):
                        task.appear_then_click(GO_CHECK, interval=2)
                        time.sleep(2.5)
                    continue
                # dialog Notice khác (vd "Sure to give up on the current Monolith progress?") -> Confirm
                logger.info('[capture] Dialog Notice -> Confirm teal (780,508)')
                task.device.click_xy(780, 508, name='ASC_NOTICE_CONFIRM')
                time.sleep(2.5)
            # Màn Record (hoặc đoạn kết thúc run) -> _run_loop tự Save Record -> về asc_diff
            _new_run()
            try:
                task._run_loop()
            except Exception:
                logger.exception('[capture] resume _run_loop lỗi (bỏ qua, đi tiếp)')

        if args.from_diff:
            logger.info('[capture] from-diff: vòng run bắt đầu từ page_asc_diff '
                        '(giữ map+difficulty game nhớ, né nav Home->ascension)')
            done = 0
            for i in range(args.runs):
                task.ui_ensure(page_asc_diff)
                if i == 0:
                    task._select_difficulty()
                task.device.screenshot()
                if not task.appear(ASCENSION_QUICK_BATTLE):
                    logger.info(f'[capture] Quick Battle không sáng (hết vé?) sau {done} run — dừng')
                    break
                if task._enter_run() is None:
                    logger.warning('[capture] _enter_run trả None (preset chưa set?) — dừng')
                    break
                logger.info(f'[capture] === vào run mới {done + 1}/{args.runs} ===')
                task._run_loop()
                done += 1
            logger.info(f'[capture] from-diff hoàn tất {done}/{args.runs} run')
        else:
            if not args.no_login:
                logger.info('[capture] Login (đưa game về Home)...')
                Login(config, device).run()
            task.run()
    except KeyboardInterrupt:
        logger.warning('[capture] Ctrl+C — dừng, data đã lưu tới thời điểm này.')
    except Exception:
        logger.exception('[capture] Task lỗi — data đã lưu tới thời điểm này.')
    finally:
        dt = time.time() - t0
        summary = {'runs_captured': _run_idx, 'frames_total_approx': _step,
                   'elapsed_sec': round(dt), 'session_dir': str(_session_dir)}
        (_session_dir / 'summary.json').write_text(json.dumps(summary, indent=2),
                                                    encoding='utf-8')
        if _jsonl is not None:
            _jsonl.close()
        logger.info(f'[capture] XONG: {_run_idx} run, ~{_step} frame ở run cuối, {round(dt)}s. '
                    f'-> {_session_dir}')


if __name__ == '__main__':
    main()

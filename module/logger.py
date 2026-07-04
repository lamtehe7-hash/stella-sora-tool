import logging
import sys
import time
import traceback
from collections import deque
from logging.handlers import RotatingFileHandler
from pathlib import Path

from module.config import ROOT  # ROOT chung, đã xử lý chế độ exe (frozen)

LOG_DIR = ROOT / 'log'

# Đuôi log cho GUI: (seq tăng dần, dòng đã format) — seq để session web chỉ append phần mới
gui_log: deque = deque(maxlen=500)
_seq = 0


class _GuiLogHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        global _seq
        _seq += 1
        gui_log.append((_seq, self.format(record)))


def _build_logger() -> logging.Logger:
    LOG_DIR.mkdir(exist_ok=True)
    # Console Windows mặc định cp1252 không in được tiếng Việt — ép utf-8 (bẫy ALAS đã xử lý)
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    lg = logging.getLogger('sst')
    lg.setLevel(logging.DEBUG)
    fmt = logging.Formatter('%(asctime)s | %(levelname)-5s | %(message)s', '%H:%M:%S')

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(fmt)
    lg.addHandler(console)

    file = RotatingFileHandler(LOG_DIR / 'sst.log', maxBytes=5 * 1024 * 1024,
                               backupCount=3, encoding='utf-8')
    file.setLevel(logging.DEBUG)
    file.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-5s | %(message)s'))
    lg.addHandler(file)

    gui = _GuiLogHandler()
    gui.setLevel(logging.INFO)
    gui.setFormatter(fmt)
    lg.addHandler(gui)
    return lg


logger = _build_logger()


def save_error_log(device=None) -> Path:
    """Dump traceback + screenshot mới nhất vào log/error/<timestamp>/ để debug offline."""
    folder = LOG_DIR / 'error' / time.strftime('%Y%m%d_%H%M%S')
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'traceback.txt').write_text(traceback.format_exc(), encoding='utf-8')
    if device is not None and getattr(device, 'image', None) is not None:
        import cv2
        cv2.imwrite(str(folder / 'screenshot.png'), device.image)
    logger.info(f'Đã lưu error log vào {folder}')
    return folder

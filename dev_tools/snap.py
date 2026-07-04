"""Chụp 1 screenshot từ giả lập ra file (mặc định screenshots/raw/snap.png).

    python dev_tools/snap.py [đường_dẫn_ra.png]
"""
import sys
from pathlib import Path

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from module.config import Config, ROOT  # noqa: E402
from module.device.device import Device  # noqa: E402

out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'screenshots' / 'raw' / 'snap.png'
out.parent.mkdir(parents=True, exist_ok=True)
device = Device(Config.load())
device.connect()
cv2.imwrite(str(out), device.screenshot())
print(out)

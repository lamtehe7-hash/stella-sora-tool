"""Điều hướng tới 1 page rồi chụp screenshot ra file — phục vụ khảo sát.

    python dev_tools/goto_snap.py <page> [đường_dẫn_ra.png]
"""
import sys
from pathlib import Path

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from module.base.button import set_server  # noqa: E402
from module.config import Config, ROOT  # noqa: E402
from module.device.device import Device  # noqa: E402
from module.ui.page import Page, UI  # noqa: E402
import module.ui.pages  # noqa: E402,F401 — nạp page graph

name = sys.argv[1]
out = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / 'screenshots' / 'raw' / f'{name}_survey.png'
out.parent.mkdir(parents=True, exist_ok=True)

config = Config.load()
set_server(config.server)
device = Device(config)
device.connect()
ui = UI(config, device)
ui.ui_ensure(Page.registry[name])
cv2.imwrite(str(out), device.screenshot())
print(out)

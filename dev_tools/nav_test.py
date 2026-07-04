"""Test điều hướng page graph: từ vị trí hiện tại đi tới page đích rồi quay về home.

    python dev_tools/nav_test.py missions
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from module.base.button import set_server   # noqa: E402
from module.config import Config            # noqa: E402
from module.device.device import Device     # noqa: E402
from module.logger import logger            # noqa: E402
from module.ui.page import Page, UI         # noqa: E402
from module.ui import pages                 # noqa: E402,F401 — đăng ký page graph

config = Config.load()
set_server(config.server)
device = Device(config)
device.connect()

ui = UI(config, device)
dest = Page.registry[sys.argv[1]]
ui.ui_ensure(dest)
ui.ui_ensure(pages.page_home)
logger.info(f'NAV TEST OK: home -> {dest.name} -> home')

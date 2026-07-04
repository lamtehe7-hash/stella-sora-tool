"""Smoke test chuỗi vision end-to-end trên giả lập thật, KHÔNG click gì vào game:

1. Kết nối ADB theo config
2. Đo tốc độ screenshot (mục tiêu < 0.5s/ảnh)
3. Self-match: crop 1 vùng từ chính screenshot làm template tạm -> Button.match
   phải tìm lại đúng vị trí đó (sai số <= 3px)
"""
import sys
import time
from pathlib import Path

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from module.base.button import Button, set_server  # noqa: E402
from module.config import Config                   # noqa: E402
from module.device.device import Device            # noqa: E402
from module.logger import logger                   # noqa: E402


def main() -> None:
    config = Config.load()
    set_server(config.server)
    device = Device(config)
    device.connect()
    logger.info(f'App đang focus: {device.app_current() or "(không rõ)"}')

    times = []
    for _ in range(3):
        t0 = time.time()
        device.screenshot()
        times.append(time.time() - t0)
    avg = sum(times) / len(times)
    logger.info(f'Screenshot: {[f"{t:.2f}s" for t in times]}, trung bình {avg:.2f}s '
                f'-> {"ĐẠT" if avg < 0.5 else "CHẬM (mục tiêu <0.5s, cân nhắc nemu_ipc)"}')

    # Self-match: vùng 120x70 quanh tâm màn hình
    x1, y1, x2, y2 = 580, 325, 700, 395
    tmp = Path(__file__).parent / '_smoke_template.png'
    cv2.imwrite(str(tmp), device.image[y1:y2, x1:x2])
    try:
        btn = Button(str(tmp), threshold=0.85, name='SMOKE_SELF_MATCH')
        found = btn.match(device.image)
        expect = ((x1 + x2) // 2, (y1 + y2) // 2)
        ok = found and abs(btn.last_match[0] - expect[0]) <= 3 and abs(btn.last_match[1] - expect[1]) <= 3
        logger.info(f'Self-match: found={found}, vị trí={btn.last_match}, kỳ vọng={expect} '
                    f'-> {"ĐẠT" if ok else "TRƯỢT"}')
        sys.exit(0 if ok and avg < 2 else 1)
    finally:
        tmp.unlink(missing_ok=True)


if __name__ == '__main__':
    main()

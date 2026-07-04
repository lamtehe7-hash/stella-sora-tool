"""Crop asset template từ screenshot + sinh code Button (xem skill crop-button-asset).

Ví dụ:
    python dev_tools/crop.py screenshots/raw/home.png --area 1180,20,1260,80 --page home --name HOME_CHECK

- Ảnh crop lưu vào assets/<server>/<page>/<NAME>.png
- In ra code Button để dán vào module/task (vùng tìm kiếm = area nới thêm --pad px, mặc định 20)
"""
import argparse
import sys
from pathlib import Path

import cv2

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from module.config import ROOT, Config  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('screenshot', help='đường dẫn ảnh screenshot 1280x720')
    p.add_argument('--area', required=True, help='vùng crop x1,y1,x2,y2')
    p.add_argument('--page', required=True, help='tên page (thư mục asset)')
    p.add_argument('--name', required=True, help='tên button UPPER_SNAKE_CASE')
    p.add_argument('--pad', type=int, default=20, help='nới vùng tìm kiếm quanh area (px)')
    args = p.parse_args()

    x1, y1, x2, y2 = (int(v) for v in args.area.split(','))
    img = cv2.imread(args.screenshot)
    if img is None:
        sys.exit(f'Không đọc được ảnh: {args.screenshot}')
    if img.shape[:2] != (720, 1280):
        sys.exit(f'Ảnh {img.shape[1]}x{img.shape[0]} — yêu cầu đúng 1280x720.')

    server = Config.load().server
    out = ROOT / 'assets' / server / args.page / f'{args.name}.png'
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), img[y1:y2, x1:x2])

    sx1, sy1 = max(0, x1 - args.pad), max(0, y1 - args.pad)
    sx2, sy2 = min(1280, x2 + args.pad), min(720, y2 + args.pad)
    print(f'Đã lưu {out}')
    print('Code dán vào module/task tương ứng:')
    print(f"{args.name} = Button('{args.page}/{args.name}.png', area=({sx1}, {sy1}, {sx2}, {sy2}))")


if __name__ == '__main__':
    main()

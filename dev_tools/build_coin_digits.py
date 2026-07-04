"""Sinh bộ template chữ số Starcoin (assets/en/ascension/coin_digits/) từ ảnh khảo sát shop.

Nguồn glyph (cùng 1 typeface của game, 3 cỡ/màu):
- Pill số dư coin (trắng trên nền navy, h~11): shop_ui_*, shopevt_*, card_017
- Giá trên kệ shop (navy đậm h~19): shop_ui_00 (160/100/200/200, 72/45/90/90)
- Số đếm note ở top bar Monolith Bag (trắng viền đen, h~11): shop_ui_08_exit

Template lưu dạng mask 12x16 (0/255), tên d<digit>_<i>.png. Chạy lại được để tái tạo:
    python dev_tools/build_coin_digits.py
"""
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / 'screenshots' / 'raw' / 'shop_survey'
OUT = ROOT / 'assets' / 'en' / 'ascension' / 'coin_digits'


def glyphs(mask, min_h=9, max_h=24, min_w=2):
    """Cụm cột liền kề trong mask. Trả [(x1, x2, crop)] đã lọc theo kích thước."""
    cols = mask.sum(0)
    out, x, w = [], 0, len(cols)
    while x < w:
        if cols[x]:
            x2 = x
            while x2 < w and cols[x2]:
                x2 += 1
            ys = np.where(mask[:, x:x2].sum(1) > 0)[0]
            h = ys.max() - ys.min() + 1
            if min_h <= h <= max_h and x2 - x >= min_w:
                out.append((x, x2, mask[ys.min():ys.max() + 1, x:x2]))
            x = x2
        x += 1
    return out


def norm(g):
    return cv2.resize(g.astype(np.uint8) * 255, (12, 16), interpolation=cv2.INTER_AREA)


def white_mask(roi):
    return (roi.min(axis=2) >= 190).astype(np.uint8)


def navy_mask(roi):
    b = roi[:, :, 0].astype(int)
    g = roi[:, :, 1].astype(int)
    r = roi[:, :, 2].astype(int)
    return ((b > 90) & (b < 200) & (r < 110) & (b - r > 45) & (g < 150)).astype(np.uint8)


def outline_white_mask(roi):
    mx = roi.max(axis=2).astype(int)
    mn = roi.min(axis=2).astype(int)
    return ((mn >= 200) & (mx - mn <= 30)).astype(np.uint8)


store: dict[str, list] = {}


def add(txt, gs, src):
    if len(gs) != len(txt):
        print(f'  BO QUA {src}: expect "{txt}" nhung tach duoc {len(gs)} glyph')
        return
    for ch, g in zip(txt, gs):
        store.setdefault(ch, []).append((norm(g[2]), src))


# --- 1. Pill số dư (bỏ dấu phẩy nhờ min_h) ---
for f, txt in {
    'shop_ui_00.png': '1010', 'shop_ui_11.png': '865', 'shopevt_002.png': '865',
    'shopevt_004.png': '805', 'card_017.png': '1845', 'shop_ui_03_after.png': '910',
}.items():
    img = cv2.imread(str(RAW / f))
    add(txt, glyphs(white_mask(img[16:52, 1183:1252]), min_h=9, max_h=14), f'pill:{f}')

# --- 2. Giá kệ shop_ui_00 ---
shop00 = cv2.imread(str(RAW / 'shop_ui_00.png'))
for (row, cx), txt in {
    (0, 700): '160', (0, 849): '100', (0, 999): '200', (0, 1148): '200',
    (1, 700): '72', (1, 849): '45', (1, 999): '90', (1, 1148): '90',
}.items():
    y1 = (250, 448)[row]
    roi = shop00[y1:y1 + 32, cx - 45:cx + 62]
    add(txt, glyphs(navy_mask(roi), min_h=15, max_h=24, min_w=4), f'price:r{row}c{cx}')

# --- 3. Số đếm note top bar Monolith Bag ---
bag = cv2.imread(str(RAW / 'shop_ui_08_exit.png'))
for cx, txt in zip((718, 776, 834, 891, 1007, 1065),
                   ('8', '21', '3', '0', '10', '23')):
    add(txt, glyphs(outline_white_mask(bag[54:78, cx - 24:cx + 24]), min_h=9, max_h=14),
        f'bag:x{cx}')

# --- Dedup (score >0.95 với mẫu đã giữ thì bỏ) rồi ghi file ---
OUT.mkdir(parents=True, exist_ok=True)
for old in OUT.glob('d*.png'):
    old.unlink()
total = 0
for ch in sorted(store):
    kept = []
    for m, src in store[ch]:
        if any(1 - np.abs(m.astype(np.int16) - k.astype(np.int16)).mean() / 255 > 0.95
               for k in kept):
            continue
        kept.append(m)
        cv2.imwrite(str(OUT / f'd{ch}_{len(kept) - 1}.png'), m)
        print(f'd{ch}_{len(kept) - 1}.png  <- {src}')
        total += 1
print(f'\nXong: {total} template cho {len(store)} chữ số -> {OUT}')

# --- Tự kiểm: phân loại lại từng mẫu gốc bằng bộ template vừa ghi ---
tpls: dict[int, list] = {}
for p in OUT.glob('d*.png'):
    tpls.setdefault(int(p.stem[1]), []).append(
        cv2.imread(str(p), cv2.IMREAD_GRAYSCALE).astype(np.int16))
bad = 0
for ch, lst in sorted(store.items()):
    for m, src in lst:
        a = m.astype(np.int16)
        best_v, best_s = None, -1.0
        for v, ts in tpls.items():
            for t in ts:
                s = 1 - np.abs(a - t).mean() / 255
                if s > best_s:
                    best_v, best_s = v, s
        if best_v != int(ch):
            bad += 1
            print(f'SELF-TEST SAI: mẫu {ch} ({src}) -> {best_v} ({best_s:.3f})')
print('SELF-TEST:', 'DAT' if bad == 0 else f'{bad} SAI')
sys.exit(1 if bad else 0)

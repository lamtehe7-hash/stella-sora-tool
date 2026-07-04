"""Validate bộ nhận diện shop v3 (tasks/ascension) trên ảnh khảo sát — không cần thiết bị.

- read_coins: pill số dư trên nhiều loại màn (shop UI, options, chọn thẻ).
- slot_offer: giá + cờ SALE từng slot, Sold Out phải trả None.
- SHOP_RELEVANT: dialog Melody cần thiết có panel, dialog Drink/màn khác không.
- CARD_REFRESH: có ở màn nhận thẻ, KHÔNG có ở màn chọn thẻ Enhance/options.
Chạy: python dev_tools/validate_shop_parser.py
"""
import sys
from pathlib import Path

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tasks.ascension import (CARD_REFRESH, SHOP_ENHANCE, SHOP_RELEVANT,  # noqa: E402
                             dialog_price, enhance_cost, read_coins, slot_offer)

RAW = Path(__file__).resolve().parent.parent / 'screenshots' / 'raw' / 'shop_survey'
fails = 0


def check(label, got, expect):
    global fails
    ok = got == expect
    fails += 0 if ok else 1
    print(f"{'PASS' if ok else 'FAIL'} {label}: {got}" + ('' if ok else f' != {expect}'))


def img(name):
    return cv2.imread(str(RAW / name))


# --- read_coins ---
for f, expect in {
    'shop_ui_00.png': 1010, 'shop_ui_11.png': 865, 'shopevt_002.png': 865,
    'shopevt_004.png': 805, 'card_017.png': 1845, 'shop_ui_03_after.png': 910,
    'card_001.png': 865, 'shop_ui_02_bought.png': 910, 'enh_00_options.png': None,
}.items():
    got = read_coins(img(f))
    if expect is None:
        print(f'INFO {f}: read_coins={got} (chưa có đáp án, soi tay)')
    else:
        check(f'read_coins {f}', got, expect)

# --- slot_offer ---
check('offers shop_ui_00',
      [slot_offer(img('shop_ui_00.png'), i) for i in range(8)],
      [(160, True), (100, True), (200, False), (200, False),
       (72, True), (45, True), (90, False), (90, False)])
check('offers shop_ui_11 (slot1+5 Sold Out)',
      [slot_offer(img('shop_ui_11.png'), i) for i in range(8)],
      [(160, True), None, (200, False), (200, False),
       (72, True), None, (90, False), (90, False)])

# --- SHOP_RELEVANT / CARD_REFRESH ---
for f, expect in {'shop_ui_06_melody_dlg.png': True, 'shop_ui_01_item2.png': False,
                  'shop_ui_00.png': False}.items():
    check(f'SHOP_RELEVANT {f}', SHOP_RELEVANT.match(img(f)), expect)
for f, expect in {'card_017.png': True, 'shop_ui_03_after.png': True,
                  'card_001.png': False, 'shopevt_002.png': False}.items():
    check(f'CARD_REFRESH {f}', CARD_REFRESH.match(img(f)), expect)

# --- enhance_cost: giá đọc từ dòng option (0 = Free) ---
for f, expect in {'enh_00_options.png': 0, 'shopevt_002.png': 60,
                  'shopevt_004.png': 120}.items():
    im = img(f)
    assert SHOP_ENHANCE.match(im), f
    check(f'enhance_cost {f}', enhance_cost(im, *SHOP_ENHANCE.last_match), expect)

# --- dialog_price: giá chuẩn trong dialog Purchase ---
for f, expect in {'shop_ui_06_melody_dlg.png': 45, 'shop_ui_01_item2.png': 100}.items():
    check(f'dialog_price {f}', dialog_price(img(f)), expect)

# --- Quét thêm: read_coins trên mọi ảnh khảo sát (soi bằng mắt, không chấm điểm) ---
print('=== read_coins quét toàn bộ shop_survey ===')
for p in sorted(RAW.glob('*.png')):
    im = cv2.imread(str(p))
    if im is not None and im.shape[:2] == (720, 1280):
        print(f'{p.name}: {read_coins(im)}')

print('FAILS =', fails)
sys.exit(1 if fails else 0)

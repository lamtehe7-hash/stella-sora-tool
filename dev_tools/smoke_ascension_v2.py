"""Smoke test nâng cấp Ascension v2: parser level + quyết định chọn thẻ + template shop.

Chạy: python dev_tools/smoke_ascension_v2.py  (exit 0 = PASS hết)
"""
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, r'e:\Claude\Stella Sora Tool')
from tasks.ascension import (ASCENSION_RECOMMEND, SHOP_DIALOG, SHOP_ENHANCE,  # noqa: E402
                             SHOP_NOTES, SHOP_PURCHASE, SHOP_SHELF, card_lv, pick_card,
                             read_selected_difficulty, weekly_is_capped,
                             event_options, event_tag_has_coin)

RAW = Path(r'e:\Claude\Stella Sora Tool\screenshots\raw')
fails = []


def recommend_xs(img):
    x1, y1, x2, y2 = ASCENSION_RECOMMEND.area
    tpl = ASCENSION_RECOMMEND.template
    r = cv2.matchTemplate(img[y1:y2, x1:x2], tpl, cv2.TM_CCOEFF_NORMED)
    _, xs = np.where(r >= ASCENSION_RECOMMEND.threshold)
    centers = sorted(int(x) + x1 + tpl.shape[1] // 2 for x in set(xs.tolist()))
    out = []
    for c in centers:
        if not out or c - out[-1] > 60:
            out.append(c)
    return out


def check(name, cond, extra=''):
    print(f"{'PASS' if cond else 'FAIL'} {name} {extra}")
    if not cond:
        fails.append(name)


# --- 1. Ground truth parser level ---
for f, expect in {
    'shop_survey/shop_ui_02_bought.png': [(0, 2), (3, 4), (2, 3)],
    'shop_survey/shop_ui_04_focused.png': [(0, 2), (3, 4), (2, 3)],
    'shop_survey/enh_01_cards.png': [(3, 4), (2, 4), (2, 3)],
    'shop_survey/card_012.png': [(0, 1), (0, 3), (4, 5)],
    'shop_survey/card_029.png': [(1, 3), (3, 4), (3, 4)],   # định dạng "Lv. 1+2 ▶ 3+2"
    'shop_survey/card_062.png': [(4, 6), (2, 3), (4, 5)],
    'asc_06_brief_on.png': [None, None, None],
}.items():
    img = cv2.imread(str(RAW / f))
    got = [card_lv(img, ci) for ci in range(3)]
    check(f'card_lv {f}', got == expect, f'{got}')

# --- 2. Quyết định chọn thẻ khi nhiều 👍 ---
for f, expect_ci in {
    'shop_survey/card_044.png': 1,   # 👍 thẻ2 (3->4, +1) vs thẻ3 (5->6, +1) -> hoà, trái nhất
    'shop_survey/card_029.png': 0,   # 👍 thẻ1 (1->3, +2) vs thẻ2 (3->4, +1) -> thẻ1
    'shop_survey/card_002.png': 1,   # 👍 thẻ2+thẻ3 đều Super Rare (không level) -> hoà, trái nhất
    'shop_survey/card_017.png': 1,   # 👍 thẻ2 (mới Lv2, +2) vs thẻ3 (5->6, +1) -> thẻ2
}.items():
    img = cv2.imread(str(RAW / f))
    recs = recommend_xs(img)
    ci, why = pick_card(img, recs)
    check(f'pick_card {f}', ci == expect_ci, f'recs={recs} -> {why}')

# --- 3. Template shop: dương tính + âm tính ---
POS = {
    SHOP_PURCHASE: ['shop_survey/enh_00_options.png', 'run2/event_099.png', 'run2/event_024.png'],
    SHOP_ENHANCE: ['shop_survey/enh_00_options.png', 'run2/event_099.png', 'run2/event_024.png'],
    SHOP_SHELF: ['shop_survey/shop_ui_00.png', 'shop_survey/shop_ui_11.png'],
    SHOP_DIALOG: ['shop_survey/shop_ui_01_item2.png', 'shop_survey/shop_ui_06_melody_dlg.png'],
    SHOP_NOTES: ['shop_survey/shop_ui_07_melody_bought.png', 'shop_survey/shop_ui_09.png'],
}
NEG = {
    SHOP_PURCHASE: ['run2/event_008.png', 'run2/event_042.png', 'shop_survey/card_044.png'],
    SHOP_ENHANCE: ['run2/event_008.png', 'run2/event_050.png'],
    SHOP_SHELF: ['shop_survey/shop_ui_02_bought.png', 'shop_survey/enh_01_cards.png',
                 'run2/event_024.png'],
    SHOP_DIALOG: ['shop_survey/shop_ui_00.png', 'shop_survey/card_044.png'],
    SHOP_NOTES: ['shop_survey/shop_ui_00.png', 'run2/event_024.png'],
}
for btn, files in POS.items():
    for f in files:
        img = cv2.imread(str(RAW / f))
        check(f'{btn.name} + {f}', btn.match(img), f'{btn.last_match}')
for btn, files in NEG.items():
    for f in files:
        img = cv2.imread(str(RAW / f))
        check(f'{btn.name} - {f}', not btn.match(img))

# --- 4. Đọc Difficulty đang chọn (page_asc_diff) + reject màn khác ---
for f, expect in {
    'go/05_difficulty2.png': 2,      # Diff2 đang chọn (pill navy), phần còn lại trắng
    'go/18_bernina.png': None,       # màn event -> không nhận nhầm
    'go/event_13.png': None,         # màn shop options
    'go/02_ascension.png': None,     # trang chọn Monolith
    'shop_survey/shop_ui_00.png': None,
}.items():
    img = cv2.imread(str(RAW / f))
    got = read_selected_difficulty(img)
    check(f'read_selected_difficulty {f}', got == expect, f'{got}')

# --- 5. Weekly Limit capped (page_ascension) ---
for f, expect in {
    'weekly_capped_3000.png': True,   # 3000/3000 -> capped
    'go/02_ascension.png': False,     # meter cũ N<3000 (2 vế lệch số chữ số) -> chưa capped, không nhận nhầm
}.items():
    img = cv2.imread(str(RAW / f))
    got = weekly_is_capped(img)
    check(f'weekly_is_capped {f}', got == expect, f'{got}')

# --- 6. Event: chọn option thưởng item-free (tag không coin) thay vì mù bấm dưới cùng ---
def _pick_event(img):
    opts = event_options(img)
    if not opts:
        return None
    for cx, cy in opts:
        if not event_tag_has_coin(img, cy):
            return cy
    return opts[-1][1]


for f, expect_y in {
    'event_potential_vs_coin.png': 355,   # top = Rare Potential (không coin) -> chọn, KHÔNG lấy 30 coin
    'go/event_01.png': 355,               # top = Potential (vs Note) -> chọn top
    'event_gamble_3opt.png': 520,         # 3 gamble coin -> fallback option dưới cùng
}.items():
    img = cv2.imread(str(RAW / f))
    got = _pick_event(img)
    check(f'event pick {f}', got == expect_y, f'y={got}')

print(f'=== {"PASS hết" if not fails else f"{len(fails)} FAIL: {fails}"} ===')
sys.exit(1 if fails else 0)

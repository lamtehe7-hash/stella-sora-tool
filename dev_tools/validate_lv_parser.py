"""Validate parser đọc level thẻ (tasks/ascension.card_lv) trên ảnh khảo sát.

- Phần 1: các ảnh đã biết đáp án (ground truth).
- Phần 2: quét mọi card_*.png trong shop_survey/ — in kết quả để soi + dump glyph lạ
  (chữ số chưa có template) vào log/lv_glyphs/.
"""
import sys
from pathlib import Path

import cv2

sys.path.insert(0, r'e:\Claude\Stella Sora Tool')
from tasks.ascension import card_lv  # noqa: E402

RAW = Path(r'e:\Claude\Stella Sora Tool\screenshots\raw')

TRUTH = {
    'shop_survey/shop_ui_02_bought.png': [(0, 2), (3, 4), (2, 3)],
    'shop_survey/shop_ui_04_focused.png': [(0, 2), (3, 4), (2, 3)],
    'shop_survey/enh_01_cards.png': [(3, 4), (2, 4), (2, 3)],
    'asc_06_brief_on.png': [None, None, None],
}

fails = 0
for f, expect in TRUTH.items():
    img = cv2.imread(str(RAW / f))
    got = [card_lv(img, ci) for ci in range(3)]
    ok = got == expect
    fails += 0 if ok else 1
    print(f"{'PASS' if ok else 'FAIL'} {f}: {got}" + ('' if ok else f' != {expect}'))

print('=== quét card_*.png ===')
for p in sorted((RAW / 'shop_survey').glob('card_*.png')):
    img = cv2.imread(str(p))
    print(p.name, [card_lv(img, ci) for ci in range(3)])

sys.exit(1 if fails else 0)

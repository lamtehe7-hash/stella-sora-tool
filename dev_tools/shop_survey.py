"""Driver khảo sát Shop/Enhance trong Monolith (chuẩn bị nâng cấp task Ascension).

Chạy: python dev_tools/shop_survey.py [stop|enhance]
- stop (mặc định): auto chạy run; gặp shop đầu tiên -> bấm "Purchase at the shop",
  chụp UI shop rồi THOÁT (exit 42) để khảo sát tay bằng snap.py/tap.
- enhance: gặp shop -> bấm "Enhance (...)" lặp tới khi hết coin (màn không đổi)
  rồi đi tiếp (option cuối / Leave Monolith ở phòng chót). Chạy hết run.

Luôn lưu: mọi màn chọn thẻ (card_*.png — để crop mẫu chữ Lv), event shop, màn lạ.
"""
import sys
import time
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, r'e:\Claude\Stella Sora Tool')
from module.config import Config  # noqa: E402
from module.device.device import Device  # noqa: E402

MODE = sys.argv[1] if len(sys.argv) > 1 else 'stop'
ASSETS = Path(r'e:\Claude\Stella Sora Tool\assets\en')
OUT = Path(r'e:\Claude\Stella Sora Tool\screenshots\raw\shop_survey')
OUT.mkdir(parents=True, exist_ok=True)

NAMES = {
    'ASCENSION_TITLE': 'ascension/ASCENSION_TITLE.png',
    'ASCENSION_QUICK_BATTLE': 'ascension/ASCENSION_QUICK_BATTLE.png',
    'SQUAD_TITLE': 'ascension/SQUAD_TITLE.png',
    'SQUAD_NEXT': 'ascension/SQUAD_NEXT.png',
    'DISC_TITLE': 'ascension/DISC_TITLE.png',
    'DISC_START_BATTLE': 'ascension/DISC_START_BATTLE.png',
    'ASCENSION_RECOMMEND': 'ascension/ASCENSION_RECOMMEND.png',
    'ASCENSION_SELECT': 'ascension/ASCENSION_SELECT.png',
    'ASCENSION_EVENT_CHOICE': 'ascension/ASCENSION_EVENT_CHOICE.png',
    'ASCENSION_CONTINUE': 'ascension/ASCENSION_CONTINUE.png',
    'DIALOG_PIN': 'ascension/DIALOG_PIN.png',
    'SHOP_PURCHASE': 'ascension/SHOP_PURCHASE.png',
    'SHOP_ENHANCE': 'ascension/SHOP_ENHANCE.png',
    'LEAVE_MONOLITH': 'ascension/LEAVE_MONOLITH.png',
    'SAVE_RECORD': 'ascension/SAVE_RECORD.png',
    'DIALOG_CONFIRM': 'common/DIALOG_CONFIRM.png',
    'NETWORK_RETRY': 'common/NETWORK_RETRY.png',
}
TPL = {n: cv2.imread(str(ASSETS / p)) for n, p in NAMES.items()}

CARD_X = (295, 640, 985)
CARD_Y = 380


def find(img, name, threshold=0.85):
    r = cv2.matchTemplate(img, TPL[name], cv2.TM_CCOEFF_NORMED)
    _, score, _, loc = cv2.minMaxLoc(r)
    if score < threshold:
        return None
    h, w = TPL[name].shape[:2]
    return loc[0] + w // 2, loc[1] + h // 2, score, r


def find_all_x(img, name, threshold=0.8):
    r = cv2.matchTemplate(img, TPL[name], cv2.TM_CCOEFF_NORMED)
    ys, xs = np.where(r >= threshold)
    w = TPL[name].shape[1]
    centers = sorted(int(x) + w // 2 for x in set(xs))
    out = []
    for c in centers:
        if not out or c - out[-1] > 60:
            out.append(c)
    return out


def card_index(x):
    return 0 if x < 550 else (1 if x < 900 else 2)


device = Device(Config.load())
device.connect()

# --- Vào run nếu đang ở trang difficulty ---
img = device.screenshot()
if find(img, 'ASCENSION_TITLE') and find(img, 'ASCENSION_QUICK_BATTLE'):
    m = find(img, 'ASCENSION_QUICK_BATTLE')
    device.click_xy(m[0], m[1], name='QB')
    print('Vào run: Quick Battle')
    time.sleep(3)
    for gate, btn in (('SQUAD_TITLE', 'SQUAD_NEXT'), ('DISC_TITLE', 'DISC_START_BATTLE')):
        for _ in range(10):
            img = device.screenshot()
            if find(img, gate):
                b = find(img, btn)
                if b:
                    device.click_xy(b[0], b[1], name=btn[:8])
                    time.sleep(2)
                    break
            time.sleep(1)

unknown = 0
step = 0
enh_clicks = 0        # số lần bấm Enhance liên tiếp ở shop hiện tại
prev_shop_img = None  # so sánh màn shop event để phát hiện hết coin
end = time.time() + 900
while time.time() < end:
    img = device.screenshot()
    step += 1

    if find(img, 'ASCENSION_TITLE'):
        print(f'DONE: về trang difficulty sau {step} bước')
        cv2.imwrite(str(OUT / '99_done.png'), img)
        sys.exit(0)

    m = find(img, 'NETWORK_RETRY')
    if m:
        print(f'[{step}] Network Error -> Retry')
        device.click_xy(m[0], m[1], name=f'NET_{step}')
        time.sleep(10)
        continue

    m = find(img, 'SAVE_RECORD')
    if m:
        print(f'[{step}] Save Record')
        cv2.imwrite(str(OUT / f'record_{step:03d}.png'), img)
        device.click_xy(m[0], m[1], name=f'SAVE_{step}')
        time.sleep(2)
        continue

    m = find(img, 'DIALOG_CONFIRM')
    if m and 455 < m[1] < 560:
        print(f'[{step}] Dialog Confirm @ {m[:2]}')
        device.click_xy(m[0], m[1], name=f'CFM_{step}')
        time.sleep(2.5)
        continue

    # --- Màn chọn thẻ: LƯU trước rồi chọn 👍 trái nhất ---
    recs = find_all_x(img, 'ASCENSION_RECOMMEND', 0.8)
    sel = find(img, 'ASCENSION_SELECT')
    if recs or sel:
        cv2.imwrite(str(OUT / f'card_{step:03d}.png'), img)
        unknown = 0
        target = CARD_X[card_index(recs[0])] if recs else sel[0]
        if sel and abs(sel[0] - target) < 80:
            print(f'[{step}] Select thẻ x={target} (recs={recs}) -> card_{step:03d}.png')
            device.click_xy(sel[0], sel[1], name=f'SEL_{step}')
        else:
            print(f'[{step}] Focus thẻ x={target} (recs={recs})')
            device.click_xy(target, CARD_Y, name=f'CARD_{step}')
        time.sleep(2.5)
        continue

    # --- Shop event: Purchase / Enhance / đi tiếp ---
    pur = find(img, 'SHOP_PURCHASE', 0.75)
    if pur:
        unknown = 0
        cv2.imwrite(str(OUT / f'shopevt_{step:03d}.png'), img)
        if MODE == 'stop':
            print(f'[{step}] SHOP! Bấm Purchase rồi dừng để khảo sát tay')
            device.click_xy(640, pur[1], name=f'PUR_{step}')
            time.sleep(3)
            cv2.imwrite(str(OUT / 'shop_ui_00.png'), device.screenshot())
            print('Đã lưu shop_ui_00.png — exit 42')
            sys.exit(42)
        enh = find(img, 'SHOP_ENHANCE', 0.75)
        if enh:
            # hết coin? màn shop event lặp lại y hệt sau khi bấm Enhance
            same = (prev_shop_img is not None
                    and np.abs(img.astype(np.int16) - prev_shop_img).mean() < 1.0)
            if same and enh_clicks >= 1:
                lv = find(img, 'LEAVE_MONOLITH')
                if lv:
                    print(f'[{step}] Enhance hết coin -> Leave Monolith')
                    device.click_xy(lv[0], lv[1], name=f'LEAVE_{step}')
                else:
                    r = find(img, 'ASCENSION_EVENT_CHOICE')[3]
                    ys, xs = np.where(r >= 0.85)
                    y = int(ys.max()) + TPL['ASCENSION_EVENT_CHOICE'].shape[0] // 2
                    print(f'[{step}] Enhance hết coin -> option cuối (đi tiếp) y={y}')
                    device.click_xy(640, y, name=f'SKIP_{step}')
                enh_clicks = 0
                prev_shop_img = None
                time.sleep(3)
                continue
            print(f'[{step}] Bấm Enhance (lần {enh_clicks + 1})')
            prev_shop_img = img.astype(np.int16)
            enh_clicks += 1
            device.click_xy(640, enh[1], name=f'ENH_{step}')
            time.sleep(2.5)
            continue

    m = find(img, 'ASCENSION_EVENT_CHOICE')
    if m:
        unknown = 0
        r = m[3]
        ys, xs = np.where(r >= 0.85)
        y = int(ys.max()) + TPL['ASCENSION_EVENT_CHOICE'].shape[0] // 2
        x = int(xs[ys.argmax()]) + 240
        print(f'[{step}] Event (option cuối) @ ({x},{y})')
        cv2.imwrite(str(OUT / f'event_{step:03d}.png'), img)
        device.click_xy(x, y, name=f'EVT_{step}')
        enh_clicks = 0
        prev_shop_img = None
        time.sleep(3)
        continue

    m = find(img, 'ASCENSION_CONTINUE')
    if m:
        unknown = 0
        print(f'[{step}] Continue')
        device.click_xy(640, 653, name=f'CONT_{step}')
        time.sleep(2)
        continue

    m = find(img, 'DIALOG_PIN')
    if m:
        unknown = 0
        device.click_xy(740, 585, name=f'DLG_{step}')
        time.sleep(1.5)
        continue

    unknown += 1
    if unknown % 3 == 1:
        p = OUT / f'unknown_{step:03d}.png'
        cv2.imwrite(str(p), img)
        print(f'[{step}] Màn lạ -> {p.name}')
    if unknown >= 3:
        device.click_xy(740, 585, name=f'UNK_{step}')
        unknown = 0
    time.sleep(2)

print('TIMEOUT — xem snap trong shop_survey/')

"""Driver v2: tự chạy hết run Monolith (Quick Battle + Brief), chọn thẻ theo 👍 Recommended.

Quy tắc mỗi vòng:
1. ASCENSION_TITLE (title trang difficulty) -> run kết thúc, DONE
2. NETWORK_RETRY -> bấm Retry, đợi 10s
3. Có 👍 ASCENSION_RECOMMEND -> chọn thẻ 👍 trái nhất (tap thẻ để focus nếu cần, rồi Select)
   Không 👍 nhưng có nút Select -> bấm Select (giữ thẻ game đang focus)
4. ASCENSION_EVENT_CHOICE -> chọn option dưới cùng
5. ASCENSION_CONTINUE -> tap (640, 653)
6. Màn lạ: lưu snap; 3 lần liên tiếp -> tap (740, 585) vượt hội thoại
"""
import sys
import time
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, r'e:\Claude\Stella Sora Tool')
from module.config import Config  # noqa: E402
from module.device.device import Device  # noqa: E402

ASSETS = Path(r'e:\Claude\Stella Sora Tool\assets\en\ascension')
OUT = Path(r'e:\Claude\Stella Sora Tool\screenshots\raw\run2')
OUT.mkdir(parents=True, exist_ok=True)

NAMES = ('ASCENSION_TITLE', 'ASCENSION_RECOMMEND', 'ASCENSION_SELECT',
         'ASCENSION_EVENT_CHOICE', 'ASCENSION_CONTINUE')
TPL = {n: cv2.imread(str(ASSETS / f'{n}.png')) for n in NAMES}
TPL['NETWORK_RETRY'] = cv2.imread(r'e:\Claude\Stella Sora Tool\assets\en\common\NETWORK_RETRY.png')

CARD_X = (295, 640, 985)  # tâm 3 thẻ
CARD_Y = 380


def find(img, name, threshold=0.85):
    r = cv2.matchTemplate(img, TPL[name], cv2.TM_CCOEFF_NORMED)
    _, score, _, loc = cv2.minMaxLoc(r)
    if score < threshold:
        return None
    h, w = TPL[name].shape[:2]
    return loc[0] + w // 2, loc[1] + h // 2, score, r


def find_all_x(img, name, threshold=0.85):
    """Trả về list x-tâm các match (gộp cụm cách nhau >60px)."""
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

unknown = 0
end = time.time() + 720
step = 0
while time.time() < end:
    img = device.screenshot()
    step += 1

    if any(find(img, n) for n in NAMES) or find(img, 'NETWORK_RETRY'):
        unknown = 0

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

    recs = find_all_x(img, 'ASCENSION_RECOMMEND', 0.8)
    sel = find(img, 'ASCENSION_SELECT')
    if recs or sel:
        target = CARD_X[card_index(recs[0])] if recs else sel[0]
        tag = 'REC' if recs else 'FOCUS'
        if sel and abs(sel[0] - target) < 80:
            print(f'[{step}] Select thẻ {tag} @ x={target} (recs={recs})')
            device.click_xy(sel[0], sel[1], name=f'SEL_{step}')
        else:
            print(f'[{step}] Focus thẻ {tag} @ x={target} (recs={recs})')
            device.click_xy(target, CARD_Y, name=f'CARD_{step}')
        time.sleep(2.5)
        continue

    m = find(img, 'ASCENSION_EVENT_CHOICE')
    if m:
        r = m[3]
        ys, xs = np.where(r >= 0.85)
        y = int(ys.max()) + TPL['ASCENSION_EVENT_CHOICE'].shape[0] // 2
        x = int(xs[ys.argmax()]) + 240
        print(f'[{step}] Event choice (option cuối) @ ({x},{y})')
        cv2.imwrite(str(OUT / f'event_{step:03d}.png'), img)
        device.click_xy(x, y, name=f'EVT_{step}')
        time.sleep(3)
        continue

    m = find(img, 'ASCENSION_CONTINUE')
    if m:
        print(f'[{step}] Continue')
        device.click_xy(640, 653, name=f'CONT_{step}')
        time.sleep(2)
        continue

    unknown += 1
    if unknown % 3 == 1:
        p = OUT / f'unknown_{step:03d}.png'
        cv2.imwrite(str(p), img)
        print(f'[{step}] Màn lạ -> {p.name}')
    if unknown >= 3:
        print(f'[{step}] Tap vượt hội thoại')
        device.click_xy(740, 585, name=f'DLG_{step}')
        unknown = 0
    time.sleep(2)

print('TIMEOUT 12 phút — xem snap cuối trong run2/')

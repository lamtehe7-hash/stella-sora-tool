import time
from pathlib import Path

import cv2
import numpy as np

from module.base.button import Button
from module.config import ROOT
from module.exception import TaskError
from module.logger import logger
from module.ui.page import UI
from module.ui.pages import ASCENSION_TITLE, page_asc_diff, page_ascension

# --- Trang difficulty (khảo sát 2026-07-04 đêm) ---
# Quick Battle: tốn vé Monolith (badge x1 cạnh nút), CHỈ sáng khi difficulty đang chọn đã clear.
# Game nhớ stage + difficulty + disc của lần chơi trước — tool giữ nguyên, không tự chọn.
ASCENSION_QUICK_BATTLE = Button('ascension/ASCENSION_QUICK_BATTLE.png', area=(795, 615, 985, 690))
# --- Chọn Difficulty (page_asc_diff): danh sách Difficulty 2..8 xếp dọc trái; pill ĐANG CHỌN màu
# navy đậm (meanV~91), các pill khác trắng (meanV~224) — khảo sát go/05_difficulty2.png 2026-07-05.
# Toạ độ tâm pill cố định (spacing ~72px). Quick Battle chỉ sáng khi bậc đó ĐÃ CLEAR + còn vé ->
# dùng chính ASCENSION_QUICK_BATTLE làm tín hiệu "bậc này farm được". Không cần template ảnh riêng. ---
DIFF_X = 160
DIFF_Y = {2: 137, 3: 209, 4: 281, 5: 353, 6: 425, 7: 497, 8: 569}
DIFF_PILL_DARK_V = 150  # pill đang chọn < mốc này (navy ~91); pill trắng ~224
# --- Trang chọn Monolith (page_ascension): 4 map xếp dọc bên trái, map đang chọn có KHUNG GÓC
# XANH LÁ ở dải trái (khảo sát 2026-07-05). Chọn map = tap nhãn; verify bằng khung xanh. Game nhớ
# map lần trước — chỉ đụng khi config ascension.map != ''. ---
MAP_CURRENTS = Button('ascension/MAP_CURRENTS.png', area=(285, 70, 610, 590), threshold=0.85)
MAP_DUST = Button('ascension/MAP_DUST.png', area=(285, 70, 610, 590), threshold=0.85)
MAP_STORM = Button('ascension/MAP_STORM.png', area=(285, 70, 610, 590), threshold=0.85)
MAP_MISSTEP = Button('ascension/MAP_MISSTEP.png', area=(285, 70, 610, 590), threshold=0.85)
MAP_LABELS = {'currents': MAP_CURRENTS, 'dust': MAP_DUST, 'storm': MAP_STORM, 'misstep': MAP_MISSTEP}
# --- Màn chọn squad: preset Potential tự áp theo thành viên squad ("Currently applied.") ---
SQUAD_TITLE = Button('ascension/SQUAD_TITLE.png', area=(105, 8, 255, 80))
SQUAD_NEXT = Button('ascension/SQUAD_NEXT.png', area=(1070, 635, 1255, 700))
SQUAD_PRESET_SET = Button('ascension/SQUAD_PRESET_SET.png', area=(1080, 72, 1260, 120))
# Cảnh báo "Preset not set." (navy, chữ trắng, KHÔNG icon kính lúp) — hiện khi squad chưa gắn
# Potential Preset. Khác pill "Preset set." nên bắt riêng để quyết định skip/abort/warn.
SQUAD_PRESET_NOT_SET = Button('ascension/SQUAD_PRESET_NOT_SET.png', area=(1080, 78, 1265, 118),
                              threshold=0.85)
# Mũi tên đổi squad (khảo sát 2026-07-05): trái = squad -1, phải = squad +1, CẢ HAI wrap vòng
# (squad 1 <-vuốt trái- squad N). Hàng dot dưới tiêu đề cho biết squad hiện tại + tổng số squad.
SQUAD_LEFT_XY = (60, 357)
SQUAD_RIGHT_XY = (1220, 357)
# --- Màn Disc Combo (giữ setup lần trước) ---
DISC_TITLE = Button('ascension/DISC_TITLE.png', area=(105, 8, 295, 80))
DISC_START_BATTLE = Button('ascension/DISC_START_BATTLE.png', area=(1065, 630, 1255, 700))
# --- Trong run ---
# Ribbon 👍 trên thẻ thuộc preset; 2 biến thể chữ ("Recommended" / "Rcmd: Lv. N") nhưng
# template là icon 👍 tròn nên khớp cả hai (0.90+).
ASCENSION_RECOMMEND = Button('ascension/ASCENSION_RECOMMEND.png', area=(280, 120, 1200, 240),
                             threshold=0.8)
ASCENSION_SELECT = Button('ascension/ASCENSION_SELECT.png', area=(150, 560, 1150, 650),
                          threshold=0.75)  # nút có animation nhấp nháy, score tụt tới ~0.78
ASCENSION_EVENT_CHOICE = Button('ascension/ASCENSION_EVENT_CHOICE.png')  # icon chat trong option
# Tag thưởng ở đáy-phải mỗi option: có icon coin (đĩa vàng) = liên quan coin (nhận/tốn coin);
# KHÔNG có icon coin = phần thưởng ITEM free (Potential/Note) -> ưu tiên POWER. Ngưỡng pixel vàng.
EVENT_TAG_COIN_MIN = 20
ASCENSION_CONTINUE = Button('ascension/ASCENSION_CONTINUE.png')
# Icon 📍 teal góc phải hộp thoại NPC — nhận diện hội thoại để tap vượt ngay
DIALOG_PIN = Button('ascension/DIALOG_PIN.png', area=(990, 625, 1055, 678))
# Toggle Brief (rút gọn mô tả thẻ, chạy nhanh hơn) — chỉ hiện ở màn chọn thẻ
BRIEF_OFF = Button('ascension/BRIEF_OFF.png', area=(995, 18, 1150, 68))
NETWORK_RETRY_RUN = Button('common/NETWORK_RETRY.png', area=(657, 463, 910, 553),
                           name='NETWORK_RETRY_RUN')
# --- Phòng Shop (Trade Domain 1-6/2-9/3-8 + phòng cuối "big sale", khảo sát 2026-07-05) ---
# Options phòng shop: "Purchase at the shop" / "Enhance (Free|60|... 🪙)" / "Nah, let's go up"
# (phòng cuối: Purchase / Enhance / nút đỏ Leave Monolith). Enhance lần đầu MỖI phòng miễn phí,
# sau đó +60/lần: Free -> 60 -> 120 -> 180 -> ... Starcoin mất trắng khi rời Monolith.
SHOP_PURCHASE = Button('ascension/SHOP_PURCHASE.png', area=(370, 240, 920, 570), threshold=0.75)
SHOP_ENHANCE = Button('ascension/SHOP_ENHANCE.png', area=(370, 240, 920, 570), threshold=0.75)
# Trong shop UI: 2 kệ x 4 slot (trên: Potential Drink = +1 thẻ/level, dưới: Melody x5 note);
# slot mua xong thành Sold Out (tag tối, giá hết màu navy); refresh kệ 100 coin.
# ⚠️ Số lượt refresh là NGÂN SÁCH CẢ RUN (gated node Research 倉庫の鍵: Lab2=1, Lab3=2 lượt),
# KHÔNG phải 2/phòng. EV tối ưu = dồn hết vào phòng CUỐI (coin mất trắng khi rời -> opportunity
# cost ~0); phòng đầu/giữa opportunity cost cao nên không refresh. Xem docs/ascension-strategy.md §3.
SHOP_SHELF = Button('ascension/SHOP_SHELF.png', area=(560, 230, 680, 330))     # tag penguin kệ trên
SHOP_DIALOG = Button('ascension/SHOP_DIALOG.png', area=(280, 150, 520, 230))   # header dialog Purchase
SHOP_NOTES = Button('ascension/SHOP_NOTES.png', area=(430, 20, 860, 80))       # "Musical Notes Acquired!"
# Tag SALE! đỏ trên slot đang giảm giá (match trong ROI từng slot)
SHOP_SALE = Button('ascension/SHOP_SALE.png', threshold=0.75)
# Panel "Relevant Harmony Skills" góc trên-trái khi mở dialog mua Melody: chỉ hiện nếu note đó
# được Harmony Skill của disc hiện tại dùng -> đây chính là "mặt hàng cần thiết" (Melody không
# hiện panel = không skill nào cần -> bỏ qua). Dialog Drink không bao giờ có panel này.
SHOP_RELEVANT = Button('ascension/SHOP_RELEVANT.png', area=(10, 14, 320, 62))
# Nút refresh bộ thẻ ở màn chọn thẻ (góc phải-dưới, 40 coin/lần) — chỉ có ở màn nhận thẻ mới,
# màn chọn thẻ của Enhance không có. Cùng icon với refresh kệ shop nhưng khác ngữ cảnh.
CARD_REFRESH = Button('ascension/CARD_REFRESH.png', area=(1190, 600, 1252, 662))
# Chữ "(Free" trong option "Enhance (Free 🪙)" — match trong dải chữ cạnh SHOP_ENHANCE.
# Threshold 0.88: bản thân Free khớp ~1.0, "(120" chỉ 0.74 (đo 2026-07-05).
ENHANCE_FREE = Button('ascension/ENHANCE_FREE.png', threshold=0.88)
# --- Phòng cuối + kết thúc run ---
LEAVE_MONOLITH = Button('ascension/LEAVE_MONOLITH.png', area=(360, 250, 920, 560))
# Màn Record sau khi rời: Save Record (teal, góc phải-dưới) -> dialog "Record Saved" Confirm
SAVE_RECORD = Button('ascension/SAVE_RECORD.png', area=(1030, 625, 1245, 690))
# Khi save_record=OFF: thử rời màn Record không lưu bằng nút back góc trái-trên (chưa khảo sát kỹ;
# nếu 2 lần không thoát được thì fallback lưu Record để run không kẹt).
SAVE_RECORD_SKIP_XY = (66, 37)
# Nút Confirm teal của dialog trong run: bắt cả biến thể giữa (640,508) lẫn phải (780,508)
ASC_DIALOG_CONFIRM = Button('common/DIALOG_CONFIRM.png', area=(500, 455, 920, 560),
                            name='ASC_DIALOG_CONFIRM')
# Dialog "There is an Ascension in progress — Return to Ascension?" (hiện khi vào Ascension lúc có
# run PAUSE, khảo sát 2026-07-07). "Give Up" (đỏ, ~500,508) = bỏ run dở; "Confirm" (teal, ~780,508)
# = tiếp tục run. Dùng ASC_GIVE_UP để nhận diện dialog + bỏ run kẹt, bắt đầu run mới sạch.
ASC_GIVE_UP = Button('ascension/ASC_GIVE_UP.png', area=(378, 470, 620, 545), threshold=0.85,
                     name='ASC_GIVE_UP')

CARD_X = (295, 640, 985)  # tâm 3 thẻ ở màn chọn thẻ
CARD_Y = 270  # tap vùng art phía trên thẻ — ripple của tap không che thanh Lv (y~402+)
RUN_TIMEOUT = 2400  # run brief ~5 phút + 4 phòng shop mua/enhance theo chiến lược

# Toạ độ shop UI (khảo sát shop_ui_*.png 2026-07-05)
SHOP_SLOTS = ((700, 250), (849, 250), (999, 250), (1148, 250),   # kệ trên: Potential Drink
              (700, 420), (849, 420), (999, 420), (1148, 420))   # kệ dưới: Melody x5
SHOP_BUY_XY = (640, 520)       # nút Purchase trong dialog
SHOP_CLOSE_XY = (935, 191)     # X đóng dialog Purchase
SHOP_BACK_XY = (66, 37)        # nút back thoát shop UI (CHỈ trên màn shop!)
# --- Rank band từ MÀU KHUNG badge Record (màn Save Record) — KHÔNG OCR số (font nâu khó + cần đủ 0-9).
# Khung theo rank (nguồn cộng đồng): silver 1-5 / green 6-10 / blue 11-20 / golden 21-30 / chroma 31-40.
# Phân loại theo MEDIAN HUE của pixel khung bão hoà. Verify live 2026-07-07: golden hue~17-22,
# chroma hue~133-137 (tách rõ). silver/green/blue chưa có mẫu trên acc Diff8 (record luôn rank ≥29) —
# ngưỡng hue đặt theo lý thuyết, cần verify khi gặp record band thấp. RECORD_BADGE_ROI = hexagon màn Save.
RECORD_BADGE_ROI = (66, 44, 156, 136)
BAND_ORDER = {'silver': 1, 'green': 2, 'blue': 3, 'golden': 4, 'chroma': 5}
BAND_NAME = {1: 'silver', 2: 'green', 3: 'blue', 4: 'golden', 5: 'chroma'}
SHOP_REFRESH_XY = (1220, 633)  # refresh kệ (100 coin) — chỉ dùng ở phòng cuối
SHOP_DISMISS_XY = (640, 690)   # tap đóng màn "Notes Acquired" (né (66,37) = mở Monolith Bag)

# --- Chiến lược shop v3 (Img_test + shop_survey 2026-07-05): SALE trước, Melody chỉ mua khi
# "cần thiết" (dialog có panel Relevant Harmony Skills), chừa coin đủ enhance tới mốc 180. ---
SHOP_ROW_Y = (250, 448)              # y1 dải giá của kệ trên / kệ dưới
SHOP_COL_X = (700, 849, 999, 1148)   # tâm x 4 slot
COIN_ROI = (1183, 16, 1252, 52)      # pill số dư Starcoin góc phải-trên (mọi màn trong run)
ENHANCE_STEP = 60                    # thang giá enhance mỗi phòng: (Free ->) 60 -> 120 -> 180...
#                                      Bậc Free chỉ có 1 LẦN CẢ RUN (phòng shop đầu tiên);
#                                      các phòng sau vào thẳng 60 (đo 2 run thật 2026-07-05)
#                                      -> giá luôn đọc từ dòng option, bộ đếm chỉ là fallback
ENHANCE_MILESTONE = 180              # giữa run enhance tới hết bậc này rồi dừng, giữ coin
ENHANCE_RESERVE = 360                # coin phải chừa khi mua sắm = 60 + 120 + 180
CARD_REFRESH_COST = 40               # refresh bộ thẻ ở màn chọn thẻ
SHOP_REFRESH_COST = 100              # refresh kệ shop; tối đa 2 lượt/RUN (research-gated Lab2=1/Lab3=2),
#                                      dồn hết vào phòng cuối (EV cao nhất — xem docs §3)
SHOP_MIN_PRICE = 45                  # giá rẻ nhất từng thấy — mốc "vẫn còn mua được gì đó"

# --- Đọc level trên thẻ (màn chọn/nâng thẻ) ---
# Thanh Lv dưới tên thẻ: "Lv. N" (thẻ mới nhận thẳng cấp N) hoặc "Lv. A ▶ B" (nâng A->B,
# B có thể nhảy >1 cấp). Chữ cấp hiện tại màu NAVY, cấp sau nâng màu XANH LÁ.
# Thẻ không có thanh Lv = Super Rare (không có hệ level) — là thẻ core của build.
LV_NAVY = (128, 92, 72)     # BGR
LV_GREEN = (33, 155, 110)   # BGR
LV_BAR_BG = (229, 226, 218)  # BGR nền xám nhạt của thanh Lv (phân biệt với nền thẻ trắng)
CARD_COLS = ((175, 419), (519, 763), (863, 1107))  # dải x thanh Lv của 3 thẻ
LV_ROI_Y = (393, 467)       # phủ cả thẻ thường (bar ~y437) lẫn thẻ đang focus (bar ~y402)

_DIGIT_TPLS: dict | None = None


def _digit_templates() -> dict:
    """Mask nhị phân chữ số 1..6 (assets/en/ascension/digits/d?.png), chuẩn hoá 12x16."""
    global _DIGIT_TPLS
    if _DIGIT_TPLS is None:
        _DIGIT_TPLS = {}
        d = ROOT / 'assets' / 'en' / 'ascension' / 'digits'
        for p in sorted(d.glob('d*.png')):
            m = cv2.imread(str(p), cv2.IMREAD_GRAYSCALE)
            if m is not None:
                _DIGIT_TPLS[int(p.stem[1])] = cv2.resize(m, (12, 16),
                                                         interpolation=cv2.INTER_AREA)
    return _DIGIT_TPLS


def _color_mask(img, ref, tol=45):
    return (np.linalg.norm(img.astype(np.int16) - np.array(ref, dtype=np.int16), axis=2)
            < tol).astype(np.uint8)


# --- OCR số Starcoin (số dư + giá shop) -------------------------------------
# Template 12x16 sinh bởi dev_tools/build_coin_digits.py từ ảnh khảo sát (3 biến thể cùng
# typeface: pill trắng h~11, giá navy h~19, số đếm note h~11). Nhiều mẫu / chữ số.
_COIN_TPLS: list | None = None


def _coin_templates() -> list:
    global _COIN_TPLS
    if _COIN_TPLS is None:
        _COIN_TPLS = []
        d = ROOT / 'assets' / 'en' / 'ascension' / 'coin_digits'
        for p in sorted(d.glob('d*.png')):
            m = cv2.imread(str(p), cv2.IMREAD_GRAYSCALE)
            if m is not None:
                _COIN_TPLS.append((int(p.stem[1]),
                                   cv2.resize(m, (12, 16),
                                              interpolation=cv2.INTER_AREA).astype(np.int16)))
    return _COIN_TPLS


def _digit_runs(mask, min_h, max_h, min_w) -> list:
    """Cụm cột liền kề (KHÔNG khoan dung khe — chữ số coin tách rời nhau), lọc kích thước.
    Dấu phẩy nghìn (h~4) và rác nhỏ tự rớt nhờ min_h."""
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


def _read_number(mask, min_h, max_h, min_w=2):
    """Ghép số từ mask nhị phân, trái -> phải. None nếu không có chữ số hoặc có glyph
    không nhận diện chắc chắn (<0.75) — glyph lạ dump vào log/coin_glyphs/ để bổ sung."""
    runs = _digit_runs(mask, min_h, max_h, min_w)
    if not runs:
        return None
    digits = ''
    for _, _, crop in runs:
        a = cv2.resize(crop * 255, (12, 16), interpolation=cv2.INTER_AREA).astype(np.int16)
        best_v, best_s = None, 0.0
        for v, t in _coin_templates():
            s = 1 - np.abs(a - t).mean() / 255
            if s > best_s:
                best_v, best_s = v, s
        if best_s < 0.75:
            try:
                d = ROOT / 'log' / 'coin_glyphs'
                d.mkdir(parents=True, exist_ok=True)
                cv2.imwrite(str(d / f'{int(time.time() * 1000)}.png'), crop * 255)
            except Exception:
                pass
            return None
        digits += str(best_v)
    return int(digits)


def read_record_band(img):
    """Band khung badge rank (1=silver..5=chroma) ở màn Save Record, phân loại theo MÀU KHUNG
    (median hue của pixel bão hoà) — KHÔNG OCR số. None nếu hue không rơi dải nào (layout lạ)."""
    x1, y1, x2, y2 = RECORD_BADGE_ROI
    roi = img[y1:y2, x1:x2]
    if roi.size == 0:
        return None
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    h, s, v = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]
    colored = (s > 60) & (v > 120)
    if colored.sum() < 0.12 * roi.shape[0] * roi.shape[1]:
        return 1                       # rất ít pixel bão hoà -> khung xám/kim loại = silver
    hue = float(np.median(h[colored]))
    if 8 <= hue <= 32:
        return 4                       # golden (vàng)
    if 33 <= hue <= 92:
        return 2                       # green
    if 93 <= hue <= 118:
        return 3                       # blue
    if 119 <= hue <= 165:
        return 5                       # chroma (xanh-tím óng)
    return None


def read_coins(img):
    """Số dư Starcoin từ pill góc phải-trên (chữ trắng nền navy). None = không đọc được."""
    x1, y1, x2, y2 = COIN_ROI
    roi = img[y1:y2, x1:x2]
    return _read_number((roi.min(axis=2) >= 190).astype(np.uint8), min_h=9, max_h=14)


def _price_mask(roi):
    """Mask chữ số giá navy đậm trên tag trắng — loại giá gốc gạch ngang (xám nhạt),
    tên item (nằm dưới ROI) và vạch trang trí (lọc theo chiều cao ở _digit_runs)."""
    b = roi[:, :, 0].astype(np.int16)
    g = roi[:, :, 1].astype(np.int16)
    r = roi[:, :, 2].astype(np.int16)
    return ((b > 90) & (b < 200) & (r < 110) & (b - r > 45) & (g < 150)).astype(np.uint8)


def slot_offer(img, idx: int):
    """Đọc slot shop thứ idx (0-7): (giá, đang_sale) hoặc None nếu Sold Out/không đọc được
    (tag Sold Out chuyển nền tối, giá mất màu navy -> mask trống)."""
    row, col = divmod(idx, 4)
    y1, cx = SHOP_ROW_Y[row], SHOP_COL_X[col]
    price = _read_number(_price_mask(img[y1:y1 + 32, cx - 45:cx + 62]),
                         min_h=15, max_h=24, min_w=4)
    if price is None or price < 10:
        return None
    badge = img[max(0, y1 - 44):y1 + 10, cx - 70:cx - 2]
    r = cv2.matchTemplate(badge, SHOP_SALE.template, cv2.TM_CCOEFF_NORMED)
    return price, float(r.max()) >= SHOP_SALE.threshold


def enhance_cost(img, mx: int, my: int):
    """Giá enhance đọc từ dòng option "Enhance (Free|60|... 🪙)" quanh tâm chữ Enhance
    (mx, my). 0 = Free; None = không đọc được. Chữ số h=13, ngoặc h=16, chữ thường h≤11
    (đo shopevt_*) — lọc h 11-15 chỉ giữ chữ số; icon coin vàng bị mask navy loại sẵn."""
    band = img[max(0, my - 18):my + 18, mx + 40:mx + 230]
    r = cv2.matchTemplate(band, ENHANCE_FREE.template, cv2.TM_CCOEFF_NORMED)
    if float(r.max()) >= ENHANCE_FREE.threshold:
        return 0
    return _read_number(_price_mask(band), min_h=11, max_h=15, min_w=4)


def dialog_price(img):
    """Giá trong dialog Purchase (hàng "Price 🪙 [giá gạch] giá") — nguồn giá CHUẨN,
    dùng đối chiếu với giá đọc từ kệ (kệ thi thoảng đọc sai). None = không đọc được."""
    return _read_number(_price_mask(img[436:468, 690:820]), min_h=14, max_h=24, min_w=4)


def _row_bands(mask, min_gap=5) -> list:
    """Các dải dòng có pixel, tách nhau bởi >= min_gap dòng trống. Trả [(y1, y2)] bao gồm 2 đầu."""
    rows = mask.sum(1)
    bands, y, h = [], 0, len(rows)
    while y < h:
        if rows[y]:
            y2, gap = y, 0
            while y2 + 1 < h and gap < min_gap:
                y2 += 1
                gap = gap + 1 if rows[y2] == 0 else 0
            y2 -= gap
            bands.append((y, y2))
            y = y2 + gap + 1
        else:
            y += 1
    return bands


def _blobs(mask) -> list:
    """Cụm cột liền (cho phép khe <=2px) trong mask 1 dòng chữ. Trả [(x1, x2, crop)]."""
    cols = mask.sum(0)
    out, x, w = [], 0, len(cols)
    while x < w:
        if cols[x]:
            x2 = x
            while x2 < w and (cols[x2] or (x2 + 2 < w and cols[x2 + 1:x2 + 3].sum())):
                x2 += 1
            ys = np.where(mask[:, x:x2].sum(1) > 0)[0]
            out.append((x, x2, mask[ys.min():ys.max() + 1, x:x2]))
            x = x2
        x += 1
    return out


def _classify_digit(crop):
    """Nhận diện chữ số từ mask glyph. Không chắc (<0.72) -> None + dump glyph để bổ sung."""
    tpls = _digit_templates()
    if not tpls:
        return None
    a = cv2.resize(crop * 255, (12, 16), interpolation=cv2.INTER_AREA).astype(np.int16)
    best_v, best_s = None, 0.0
    for v, t in tpls.items():
        s = 1 - np.abs(a - t.astype(np.int16)).mean() / 255
        if s > best_s:
            best_v, best_s = v, s
    if best_s < 0.72:
        try:
            d = ROOT / 'log' / 'lv_glyphs'
            d.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(d / f'{int(time.time() * 1000)}.png'), crop * 255)
        except Exception:
            pass
        return None
    return best_v


def _find_lv_trio(navy_mask):
    """Tìm digit cấp hiện tại trong mask navy CỦA THANH BAR (đã lọc nền xám nên navy chỉ có
    thể là "Lv. N[+k]"). Tuỳ anti-alias, "Lv." render thành 1-3 blob: dính ["Lv." w18-23],
    tách ["Lv" w13-17]["." nhỏ], hoặc mảnh ["L"]["v"]["."]. Digit = blob dạng chữ số đầu tiên
    sau mốc kết thúc cụm "Lv.". Trả (y1, y2, digit_crop) hoặc None."""
    for y1, y2 in _row_bands(navy_mask):
        if not 8 <= y2 - y1 + 1 <= 18:
            continue
        bl = _blobs(navy_mask[y1:y2 + 1])
        start = None
        for i, b in enumerate(bl):
            w, h = b[1] - b[0], b[2].shape[0]
            if w >= 18:               # "Lv." dính liền
                start = i + 1
                break
            if w <= 4 and h <= 4:     # dấu '.' rời (nằm thấp)
                start = i + 1
                break
        if start is None:
            if len(bl) >= 2 and 13 <= bl[0][1] - bl[0][0] <= 17:
                start = 1             # ["Lv" w13-17] không thấy dấu chấm
            else:
                continue
        for b in bl[start:]:
            w, h = b[1] - b[0], b[2].shape[0]
            if 3 <= w <= 11 and 9 <= h <= 16:
                return y1, y2, b[2]
    return None


def _bar_bands(roi) -> list:
    """Các dải dòng thuộc thanh Lv (nền xám nhạt chiếm >50% chiều ngang, cao >= 12 dòng).
    Tiêu đề/mô tả thẻ nằm trên nền trắng nên bị loại — tránh trio giả từ chữ cái."""
    frac = _color_mask(roi, LV_BAR_BG, tol=14).mean(axis=1)
    bands, y, h = [], 0, len(frac)
    while y < h:
        if frac[y] > 0.5:
            y2 = y
            while y2 < h and frac[y2] > 0.5:
                y2 += 1
            if y2 - y >= 12:
                bands.append((y, y2))
            y = y2
        y += 1
    return bands


def card_lv(img, ci: int):
    """Đọc thanh level của thẻ thứ ci (0-2). None = không có thanh (Super Rare);
    (0, N) = thẻ mới nhận thẳng cấp N; (A, B) = nâng cấp A -> B."""
    x1, x2 = CARD_COLS[ci]
    roi = img[LV_ROI_Y[0]:LV_ROI_Y[1], x1:x2]
    for by1, by2 in _bar_bands(roi):
        bar = roi[max(0, by1 - 2):by2 + 2]
        trio = _find_lv_trio(_color_mask(bar, LV_NAVY))
        if trio is None:
            continue
        y1, y2, digit_crop = trio
        cur = _classify_digit(digit_crop)
        green = _color_mask(bar[max(0, y1 - 2):y2 + 3], LV_GREEN)
        # thứ tự green: [▶][digit][chevron]; chevron w>=15 bị loại, blob 1px = nhiễu
        gb = [b for b in _blobs(green) if 2 <= b[1] - b[0] < 15]
        tgt = _classify_digit(gb[1][2]) if len(gb) >= 2 else None
        if tgt is None:
            return (0, cur if cur is not None else 1)  # thẻ mới cấp N (parse fail -> coi như 1)
        return (cur if cur is not None else max(1, tgt - 1), tgt)
    return None


def read_squad(img):
    """(squad hiện tại, tổng squad) từ hàng dot dưới tiêu đề "Squad N" trên màn chọn Squad.
    Dot sáng (trắng) = squad đang chọn; các dot cách đều ~8px. None nếu không đọc được.
    Khảo sát 2026-07-05: map dot sáng đúng squad 2/3/5 trên tài khoản 6 squad."""
    band = img[62:74, 595:690]
    b, g, r = [band[:, :, i].astype(int) for i in range(3)]
    gray = band.mean(2)
    # 'dot' = navy tối (dot chưa chọn) hoặc trắng trung tính (dot đang chọn) — khác nền trời xanh
    dot = (gray < 120) | ((gray > 200) & ((b - r) < 50))
    xs = np.where(dot.sum(0) >= 4)[0]
    if len(xs) == 0:
        return None
    groups = []
    for x in xs:
        if groups and x - groups[-1][-1] <= 1:
            groups[-1].append(int(x))
        else:
            groups.append([int(x)])
    cens = [int(np.mean(gp)) + 595 for gp in groups]
    # Giữ chuỗi dot cách đều (6..11px) dài nhất — loại blob rác lẻ (vd vạch trang trí ~x601)
    best_run, run = [], [cens[0]]
    for c in cens[1:]:
        if 6 <= c - run[-1] <= 11:
            run.append(c)
        else:
            best_run = run if len(run) > len(best_run) else best_run
            run = [c]
    best_run = run if len(run) > len(best_run) else best_run
    if len(best_run) < 2:
        return None
    lit_idx, best = None, 205
    for i, c in enumerate(best_run):
        v = gray[:, max(0, c - 595 - 4):c - 595 + 5].max()
        if v > best:
            best, lit_idx = v, i
    if lit_idx is None:
        return None
    return lit_idx + 1, len(best_run)


def selected_map_center(img):
    """y tâm card map đang chọn (page_ascension) = trung điểm 2 cụm khung góc XANH LÁ (trên+dưới)
    ở dải trái x6-46. None nếu không thấy khung xanh. (Card cách nhau ~130px, khung cao ~135px nên
    phải ghép cặp trên+dưới thay vì bắt trong 1 cửa sổ — tránh dính khung card kề)."""
    strip = img[70:600, 6:46]
    b, g, r = [strip[:, :, k].astype(int) for k in range(3)]
    green = (g > 150) & (g - r > 50) & (g - b > 40)
    ys = np.where(green.sum(1) > 2)[0]
    if len(ys) < 4:
        return None
    clusters, cur = [], [ys[0]]
    for y in ys[1:]:
        if y - cur[-1] <= 15:
            cur.append(y)
        else:
            clusters.append(cur)
            cur = [y]
    clusters.append(cur)
    return int((np.mean(clusters[0]) + np.mean(clusters[-1])) / 2) + 70


def _map_is_selected(img, y_center: int) -> bool:
    """True nếu card map ở y_center (page_ascension) đang được chọn (khung xanh bao quanh)."""
    c = selected_map_center(img)
    return c is not None and abs(c - y_center) < 40


# --- Weekly Limit "N/3000" trên page_ascension (đáy, cạnh nhãn "Weekly Limit"). Khảo sát
# 2026-07-05: số navy trên nền sáng, font khác coin -> KHÔNG OCR giá trị mà so KHỐI SỐ trái (N)
# với khối phải (max): capped <=> hai khối giống hệt (số runs LẺ + từng cặp glyph khớp). ---
WEEKLY_ROI = (496, 636, 618, 662)


def weekly_is_capped(img):
    """True nếu Weekly Limit đã đầy (N == max, vd 3000/3000) trên page_ascension. False nếu chưa;
    None nếu không đọc được (sai trang / layout lạ). So khối số trái-phải, không cần đọc giá trị."""
    x1, y1, x2, y2 = WEEKLY_ROI
    runs = _digit_runs(_price_mask(img[y1:y2, x1:x2]), min_h=10, max_h=22, min_w=3)
    runs = [r for r in runs if 3 <= r[1] - r[0] <= 14]   # bỏ blob rác rộng (nhãn/viền)
    n = len(runs)
    if n < 3:
        return None
    if n % 2 == 0:
        return False                      # số chữ số 2 vế khác nhau -> N != max -> chưa capped
    k = n // 2                            # dấu '/' ở giữa khi 2 vế cùng số chữ số
    for (_, _, cl), (_, _, cr) in zip(runs[:k], runs[k + 1:]):
        a = cv2.resize((cl * 255).astype(np.uint8), (10, 16)).astype(np.int16)
        b = cv2.resize((cr * 255).astype(np.uint8), (10, 16)).astype(np.int16)
        if 1 - np.abs(a - b).mean() / 255 < 0.82:
            return False
    return True


def event_options(img) -> list:
    """Các option của event NPC = icon chat ASCENSION_EVENT_CHOICE, gộp theo hàng, TRÊN -> DƯỚI.
    Trả [(x_click, y_center)] — x_click lệch phải khỏi icon để bấm giữa dòng option."""
    tpl = ASCENSION_EVENT_CHOICE.template
    r = cv2.matchTemplate(img, tpl, cv2.TM_CCOEFF_NORMED)
    ys, xs = np.where(r >= ASCENSION_EVENT_CHOICE.threshold)
    rows = []
    for y, x in sorted(zip(ys.tolist(), xs.tolist())):
        cy = y + tpl.shape[0] // 2
        if not rows or cy - rows[-1][1] > 40:
            rows.append((x + 240, cy))
    return rows


def event_tag_has_coin(img, cy: int) -> bool:
    """True nếu tag thưởng của option (icon chat tâm y=cy) có icon coin (đĩa vàng) — tức phần thưởng
    liên quan coin (nhận/tốn coin). False = tag không coin = phần thưởng item free (Potential/Note)."""
    tag = img[cy + 18:cy + 54, 840:1252]
    if tag.size == 0:
        return True
    b, g, r = [tag[:, :, i].astype(int) for i in range(3)]
    yellow = int(((r > 150) & (g > 110) & (b < 110) & (r - b > 60)).sum())
    return yellow >= EVENT_TAG_COIN_MIN


def read_selected_difficulty(img):
    """Bậc Difficulty đang chọn trên page_asc_diff = pill navy đậm (các pill khác trắng).
    None nếu layout không khớp (không ở đúng trang) — yêu cầu ĐÚNG 1 pill tối + phần còn lại
    sáng như pill trắng, để không nhận nhầm trên màn khác."""
    vals = {d: float(img[y - 14:y + 14, DIFF_X - 45:DIFF_X + 55].mean()) for d, y in DIFF_Y.items()}
    d_sel = min(vals, key=vals.get)
    others = sorted(v for d, v in vals.items() if d != d_sel)
    if vals[d_sel] < DIFF_PILL_DARK_V and others[len(others) // 2] > 190:
        return d_sel
    return None


def _gain(lv, priority: str = 'level_gain') -> int:
    """Lợi tức chọn thẻ theo tiêu chí người chơi:
    - level_gain: Super Rare (không level, core build) = 99 (ưu tiên tuyệt đối); thẻ mới "Lv. N" = N;
      nâng "A ▶ B" = B - A.
    - super_rare: chỉ SR = 99, còn lại 0 (hoà -> trái nhất).
    - leftmost: mọi thẻ = 0 (luôn lấy trái nhất)."""
    if priority == 'leftmost':
        return 0
    if lv is None:
        return 99
    return max(lv[1] - lv[0], 0) if priority == 'level_gain' else 0


def _card_index(x: int) -> int:
    return 0 if x < 550 else (1 if x < 900 else 2)


def pick_card(img, recs: list, priority: str = 'level_gain') -> tuple:
    """Chọn thẻ trong các thẻ 👍 theo `priority` (level_gain/super_rare/leftmost); hoà -> thẻ
    trái nhất. Trả (chỉ số thẻ 0-2, mô tả lý do)."""
    if len(recs) == 1:
        return _card_index(recs[0]), '👍 duy nhất'
    best_g, best_ci, detail = -1, 0, []
    for x in recs:
        ci = _card_index(x)
        g = _gain(card_lv(img, ci), priority)
        detail.append(f'thẻ{ci + 1}:+{g if g < 99 else "SR"}')
        if g > best_g:
            best_g, best_ci = g, ci
    return best_ci, f"👍 x{len(recs)} [{', '.join(detail)}] -> thẻ{best_ci + 1}"


class Ascension(UI):
    """Chạy 1 run Monolith/ngày bằng Quick Battle, chọn thẻ theo Potential Preset của người chơi.

    Chiến lược đầy đủ + cơ chế đã verify đa nguồn: xem docs/ascension-strategy.md.

    Cách game vận hành (khảo sát + wiki + guide cộng đồng):
    - Difficulty: phần thưởng tăng đơn điệu theo bậc (Diff7≈430 stub/clear). cfg.difficulty=0 ->
      tự nâng lên bậc đã-clear cao nhất (Quick Battle sáng = bậc farm được); 2..8 -> ép bậc đó.
    - Preset Potential tự áp theo squad trùng thành viên; thẻ thuộc preset hiện ribbon 👍 ở màn
      chọn thẻ. Nhiều thẻ 👍 -> chọn thẻ có MỨC TĂNG LEVEL lớn nhất (đọc thanh "Lv. A ▶ B"/"Lv. N");
      thẻ 👍 không có thanh level = Super Rare core -> ưu tiên tuyệt đối. Hoà -> thẻ trái nhất.
    - Phòng Shop (1-6, 2-9, 3-8, phòng cuối): mua theo chiến lược — ưu tiên hàng SALE, Drink
      mua tự do, Melody CHỈ mua khi "cần thiết" (dialog mua hiện panel Relevant Harmony Skills
      = note được skill của disc dùng); luôn chừa 360 coin để Enhance đủ Free+60+120+180 (quy tắc
      ROI: chỉ enhance khi 1 lượt ≤200 coin). Enhance mỗi phòng dừng ở mốc 180 để dành coin cho
      shop sau; PHÒNG CUỐI (coin mất trắng khi rời) ưu tiên giá trị lâu dài: mua -> enhance tới mốc
      180 -> VÉT kệ note/thẻ + refresh (100 coin, ≤2 lượt) -> chỉ khi còn dư mới enhance nốt tới hết.
    - Màn chọn thẻ không có thẻ 👍 nào -> refresh bộ thẻ 1 lần (40 coin, nếu màn đó có nút);
      vẫn không có 👍 thì lấy thẻ đang focus như cũ.
    - Người chơi cần chơi tay 1 lần trước: clear difficulty muốn farm, lưu preset trùng squad,
      chọn disc — game nhớ toàn bộ cho các lần Quick Battle sau.
    """

    def run(self) -> None:
        self.cfg = self.config.ascension
        if self.cfg.objective == 'score':
            logger.warning("Ascension: objective='score' chưa được implement — chạy như 'power' "
                           '(xem docs/ascension-strategy.md §4, §8)')
        # Ghé page_ascension (trên đường tới asc_diff) để đọc Weekly Limit + (tuỳ config) chọn map.
        self.ui_ensure(page_ascension)
        if self.cfg.skip_when_capped:
            if weekly_is_capped(self.device.screenshot()):
                logger.info('Ascension: Weekly Limit đã đầy (N/3000) — run bây giờ = 0 stub, bỏ qua '
                            'để khỏi phí vé. Bỏ tick skip_when_capped nếu muốn chạy để build POWER.')
                self.config.task_delay('Ascension', server_reset=True)
                return
        if self.cfg.map:
            self._select_map(self.cfg.map)   # loop bên dưới sẽ đi tiếp ascension -> asc_diff
        runs = max(1, self.cfg.runs_per_session)
        done = 0
        for i in range(runs):
            self.ui_ensure(page_asc_diff)
            if i == 0:
                self._select_difficulty()   # chọn 1 lần/session (game nhớ cho các run sau)
            self.device.screenshot()
            if not self.appear(ASCENSION_QUICK_BATTLE):
                if done == 0:
                    logger.warning('Ascension: nút Quick Battle không sáng (difficulty chưa clear '
                                   'hoặc hết vé?) — cần chơi tay 1 lần, bỏ qua hôm nay')
                else:
                    logger.info(f'Ascension: hết vé Quick Battle sau {done} run — dừng')
                break
            entered = self._enter_run()
            if entered is None:      # preset_behavior=skip -> bỏ qua Ascension hôm nay
                self.config.task_delay('Ascension', server_reset=True)
                return
            logger.info(f'Ascension: đã vào run {done + 1}/{runs} — bắt đầu vòng roguelike')
            self._run_loop()
            done += 1

        logger.info(f'Ascension: hoàn tất {done}/{runs} run')
        self.config.task_delay('Ascension', server_reset=True)

    def _select_map(self, key: str) -> bool:
        """Chọn map Monolith `key` trên page_ascension (tap nhãn map; verify khung xanh chọn).
        Trả True nếu map đích đang được chọn. Không thấy nhãn/không xác nhận -> giữ map hiện tại."""
        tpl = MAP_LABELS.get(key)
        if tpl is None:
            logger.warning(f'Ascension: map "{key}" không hợp lệ — giữ map game nhớ')
            return False
        for attempt in range(4):
            img = self.device.screenshot()
            if not self.appear(tpl):
                logger.warning(f'Ascension: không thấy map "{key}" trong danh sách — giữ map hiện tại')
                return False
            x, y = tpl.last_match
            if _map_is_selected(img, y):
                logger.info(f'Ascension: đã chọn map "{key}"')
                return True
            logger.info(f'Ascension: chọn map "{key}" (tap {x},{y})')
            self.device.click_xy(x, y, name=f'ASC_MAP_{attempt % 3}')
            time.sleep(1.3)
        logger.warning(f'Ascension: chọn map "{key}" — không xác nhận được khung chọn, vẫn đi tiếp')
        return False

    def _tap_difficulty(self, d: int) -> None:
        self.device.click_xy(DIFF_X, DIFF_Y[d], name=f'ASC_DIFF_{d}')
        time.sleep(1.2)

    def _select_difficulty(self) -> None:
        """Chọn Difficulty trên page_asc_diff theo cfg.difficulty.
        - N in 2..8: ép bậc N (chỉ hữu ích nếu Quick Battle bậc đó sáng).
        - 0 (auto): TỪ bậc đang chọn quét LÊN, dừng ở bậc đã-clear cao nhất (Quick Battle còn sáng).
          Chỉ đi lên nên không bao giờ tự hạ xuống bậc thấp hơn / bậc chưa clear."""
        img = self.device.screenshot()
        cur = read_selected_difficulty(img)
        target = self.cfg.difficulty
        if target in DIFF_Y:                      # ép bậc cụ thể
            if cur != target:
                self._tap_difficulty(target)
            self.device.screenshot()
            if self.appear(ASCENSION_QUICK_BATTLE):
                logger.info(f'Ascension: đã chọn Difficulty {target}')
            else:
                logger.warning(f'Ascension: Difficulty {target} Quick Battle KHÔNG sáng '
                               '(chưa clear / hết vé) — vẫn giữ lựa chọn này')
            return
        if cur is None:
            logger.info('Ascension: không đọc được Difficulty đang chọn — giữ nguyên bậc game nhớ')
            return
        # auto: quét lên tìm bậc đã-clear cao nhất (Quick Battle còn sáng)
        best = cur
        probe = cur + 1
        while probe <= 8:
            self._tap_difficulty(probe)
            self.device.screenshot()
            if self.appear(ASCENSION_QUICK_BATTLE):
                best = probe
                probe += 1
            else:
                break                             # bậc này chưa clear -> dừng, best là bậc cao nhất
        if read_selected_difficulty(self.device.image) != best:
            self._tap_difficulty(best)            # đang đứng ở bậc chưa clear -> quay về best
            self.device.screenshot()
        # Guard: xác nhận best thực sự sáng Quick Battle; nếu không (đọc nhầm do timing) quay về
        # bậc game nhớ (đã biết farm được) để không skip cả ngày vì kẹt ở bậc chưa clear.
        if best != cur and not self.appear(ASCENSION_QUICK_BATTLE):
            logger.warning(f'Ascension: Difficulty {best} không xác nhận Quick Battle sáng — '
                           f'quay về Difficulty {cur}')
            self._tap_difficulty(cur)
            best = cur
        if best != cur:
            logger.info(f'Ascension: tự nâng Difficulty {cur} -> {best} (bậc đã-clear cao nhất)')
        else:
            logger.info(f'Ascension: giữ Difficulty {cur} (không có bậc cao hơn đã clear)')

    def _enter_run(self):
        """Quick Battle -> màn Squad (chọn squad nếu cấu hình + kiểm tra Preset) -> Disc -> Start.
        Trả True nếu đã vào run; None nếu preset_behavior=skip; raise TaskError nếu abort/lỗi nav."""
        self.device.click(ASCENSION_QUICK_BATTLE)
        if not self.wait_until_appear(SQUAD_TITLE, timeout=10):
            raise TaskError('Ascension: màn chọn Squad không mở sau Quick Battle')

        if self.cfg.squad > 0:
            self._goto_squad(self.cfg.squad)

        self.device.screenshot()
        if self.appear(SQUAD_PRESET_NOT_SET):
            b = self.cfg.preset_behavior
            if b == 'abort':
                raise TaskError('Ascension: squad CHƯA gắn Potential Preset (preset_behavior=abort) '
                                '— dừng để người chơi vào set preset')
            if b == 'skip':
                logger.warning('Ascension: squad CHƯA gắn Potential Preset — bỏ qua Ascension hôm nay '
                               '(preset_behavior=skip)')
                return None
            logger.warning('Ascension: squad CHƯA gắn Potential Preset — vẫn chạy (preset_behavior=warn), '
                           'sẽ không có thẻ 👍 để ưu tiên')

        self.device.click(SQUAD_NEXT)
        if not self.wait_until_appear(DISC_TITLE, timeout=10):
            raise TaskError('Ascension: màn Disc Combo không mở')
        self.device.click(DISC_START_BATTLE)
        return True

    def _goto_squad(self, target: int) -> bool:
        """Vuốt tới Squad `target` (1..N) trên màn Squad. Đọc dot xác định squad hiện tại rồi
        đi hướng ngắn nhất (mũi tên wrap vòng). Trả True nếu tới đúng squad."""
        for step in range(16):
            st = read_squad(self.device.screenshot())
            if st is None:
                logger.warning('Ascension: không đọc được số Squad — giữ squad hiện tại')
                return False
            cur, total = st
            if target > total:
                logger.warning(f'Ascension: Squad {target} vượt tổng {total} — giữ Squad {cur}')
                return False
            if cur == target:
                logger.info(f'Ascension: đã ở Squad {target}/{total}')
                return True
            suffix = step % 3
            if (target - cur) % total <= (cur - target) % total:
                self.device.click_xy(*SQUAD_RIGHT_XY, name=f'SQ_RIGHT_{suffix}')
            else:
                self.device.click_xy(*SQUAD_LEFT_XY, name=f'SQ_LEFT_{suffix}')
            time.sleep(0.9)
        logger.warning(f'Ascension: không tới được Squad {target} sau 16 bước')
        return False

    # --- vòng roguelike -----------------------------------------------------

    def _run_loop(self) -> None:
        end = time.time() + self.cfg.run_timeout
        unknown = 0
        step = 0
        save_tries = 0          # số lần thử rời màn Record không lưu (save_record=OFF)
        last_evt = None         # (x, y) option event vừa bấm
        evt_repeat = 0          # số lần bấm liên tiếp cùng 1 option mà màn không đổi
        shop_done = False       # đã mua ở phòng shop GIỮA RUN hiện tại chưa
        shop_last_done = False  # đã mua ở PHÒNG CUỐI chưa (nhận diện qua nút Leave Monolith;
        #                         cờ riêng vì giữa shop 3-8 và phòng cuối có thể không có
        #                         event/continue nào để reset shop_done)
        shop_exit_tries = 0     # số lần bấm "go up" mà chưa rời được phòng shop (chống deadlock)
        while time.time() < end:
            img = self.device.screenshot()
            step += 1
            suffix = step % 3  # xoay tên click để không vấp GameTooManyClickError khi spam hợp lệ

            known = (self.appear(ASCENSION_TITLE) or self.appear(NETWORK_RETRY_RUN)
                     or self.appear(ASCENSION_SELECT) or self.appear(ASCENSION_EVENT_CHOICE)
                     or self.appear(ASCENSION_CONTINUE) or self.appear(DIALOG_PIN)
                     or self.appear(SAVE_RECORD) or self.appear(ASC_DIALOG_CONFIRM)
                     or self.appear(SHOP_SHELF) or self.appear(SHOP_NOTES)
                     or self.appear(SHOP_DIALOG) or bool(self._recommend_xs(img)))
            if known:
                unknown = 0

            # Hết run: game trả về trang difficulty
            if self.appear(ASCENSION_TITLE):
                logger.info(f'Ascension: run kết thúc sau {step} bước')
                return

            if self.appear(NETWORK_RETRY_RUN):
                self.device.click(NETWORK_RETRY_RUN)
                logger.info('Ascension: Network Error — Retry, đợi 10s')
                time.sleep(10)
                continue

            # Màn Record cuối run: (tuỳ chọn) đọc BAND khung rank để quyết định HUỶ record yếu vs lưu.
            # save_record=OFF -> thử rời không lưu; sau 2 lần không thoát thì fallback lưu (né kẹt run).
            if self.appear(SAVE_RECORD):
                if getattr(self.cfg, 'dissolve_record', False):
                    band = read_record_band(img)
                    thr = BAND_ORDER.get(getattr(self.cfg, 'dissolve_max_band', 'silver'), 1)
                    to_discard = band is not None and band <= thr
                    logger.info(f"Ascension: Record khung={BAND_NAME.get(band, '?')}(band {band}) | "
                                f"ngưỡng rã ≤ {getattr(self.cfg, 'dissolve_max_band', 'silver')} -> "
                                f"{'ĐỦ ĐK HUỶ' if to_discard else 'GIỮ'}")
                    if to_discard:
                        # ⚠️ Luồng HUỶ (bấm thùng rác ~448,655 + dialog confirm) CHƯA khảo sát/verify live.
                        # FAIL-SAFE: LƯU tạm để KHÔNG mất data. Bật huỷ thật sau khi crop RECORD_DISCARD
                        # + map dialog confirm + test giám sát (xem docs/game-map.md ▸ records).
                        logger.warning('Ascension: record đủ điều kiện HUỶ nhưng luồng huỷ chưa verify '
                                       'live -> LƯU tạm (fail-safe, không mất data).')
                if self.cfg.save_record or save_tries >= 2:
                    logger.info('Ascension: Save Record')
                    self.device.click_xy(*SAVE_RECORD.last_match, name=f'ASC_SAVE_{suffix}')
                else:
                    save_tries += 1
                    logger.info('Ascension: save_record tắt — thử rời màn Record không lưu')
                    self.device.click_xy(*SAVE_RECORD_SKIP_XY, name=f'ASC_NOSAVE_{suffix}')
                time.sleep(2)
                continue

            # Dialog Confirm trong run: "Leave anyway?" (phải) / "Record Saved" (giữa)
            if self.appear(ASC_DIALOG_CONFIRM):
                self.device.click_xy(*ASC_DIALOG_CONFIRM.last_match, name=f'ASC_CFM_{suffix}')
                time.sleep(2.5)
                continue

            # Safety net: bấm mãi 1 option mà màn không đổi ở phòng cuối -> rời Monolith
            if evt_repeat >= 2 and self.appear(LEAVE_MONOLITH):
                logger.info('Ascension: hết coin nâng thẻ — Leave Monolith')
                self.device.click_xy(*LEAVE_MONOLITH.last_match, name=f'ASC_LEAVE_{suffix}')
                last_evt, evt_repeat, shop_done = None, 0, False
                time.sleep(2.5)
                continue

            # Màn chọn thẻ: bật Brief nếu đang tắt (chạy nhanh hơn), rồi chọn thẻ
            if self._handle_card_pick(img, suffix):
                last_evt, evt_repeat = None, 0
                time.sleep(2.5)
                continue

            # Phòng Shop (Trade Domain / phòng cuối): mua chiến lược + enhance trọn gói 1 lần
            at_shop_opts = self.appear(SHOP_PURCHASE)
            if not at_shop_opts:
                shop_exit_tries = 0          # không ở màn options shop -> reset guard deadlock
            if at_shop_opts:
                last_room = self.appear(LEAVE_MONOLITH)
                if not (shop_last_done if last_room else shop_done):
                    self._do_shop_room(last_room=last_room)
                    if last_room:
                        shop_last_done = True
                    else:
                        shop_done = True
                    last_evt, evt_repeat, shop_exit_tries = None, 0, 0
                    time.sleep(2)
                    continue
                # Đã xong phòng này -> rời đi
                if self.appear(LEAVE_MONOLITH):
                    logger.info('Ascension: shop + enhance xong — Leave Monolith')
                    self.device.click_xy(*LEAVE_MONOLITH.last_match, name=f'ASC_LEAVE_{suffix}')
                    shop_exit_tries = 0
                else:
                    # RỜI phòng shop = bấm ĐÚNG option cuối "Nah, let's go up right away" (lên tầng).
                    # KHÔNG dùng _handle_event_choice: smart_event_choice chọn nhầm option item-free
                    # "Purchase at the shop" -> mở lại shelf -> deadlock shelf<->options (bug 2026-07-07).
                    self._leave_shop_room(img, suffix)
                    shop_exit_tries += 1
                    if shop_exit_tries >= 10:
                        raise TaskError('Ascension: kẹt phòng shop, không rời được sau 10 lần '
                                        '"go up" — dừng tránh treo run (kiểm tra lại option shop)')
                last_evt, evt_repeat = None, 0
                time.sleep(3)
                continue

            # Hồi phục nếu lạc trong shop UI / popup shop (vd _do_shop bị ngắt giữa chừng)
            if self.appear(SHOP_NOTES):
                self.device.click_xy(*SHOP_DISMISS_XY, name=f'ASC_NOTE_{suffix}')
                time.sleep(1.5)
                continue
            if self.appear(SHOP_DIALOG):
                self.device.click_xy(*SHOP_CLOSE_XY, name=f'ASC_SHOPX_{suffix}')
                time.sleep(1.5)
                continue
            if self.appear(SHOP_SHELF):
                logger.info('Ascension: đang ở shop UI ngoài luồng — thoát ra')
                self.device.click_xy(*SHOP_BACK_XY, name=f'ASC_SHOPBK_{suffix}')
                time.sleep(2.5)
                continue

            clicked = self._handle_event_choice(img, suffix)
            if clicked:
                evt_repeat = evt_repeat + 1 if clicked == last_evt else 0
                last_evt = clicked
                shop_done = False  # đã qua event khác -> phòng shop kế là phòng mới
                time.sleep(3)
                continue

            if self.appear(ASCENSION_CONTINUE):
                self.device.click_xy(640, 653, name=f'ASC_CONT_{suffix}')
                last_evt, evt_repeat, shop_done = None, 0, False
                time.sleep(2)
                continue

            if self.appear(DIALOG_PIN):
                self.device.click_xy(740, 585, name=f'ASC_DLG_{suffix}')
                shop_done = False
                time.sleep(1.5)
                continue

            # Màn lạ: chờ 3 nhịp rồi tap vùng hộp thoại — vô hại trên cutscene/overlay lạ;
            # trên màn "Select anywhere to continue" (ASCENDED/Affinity) tap này cũng đi tiếp
            unknown += 1
            if unknown >= 3:
                self.device.click_xy(740, 585, name=f'ASC_UNK_{suffix}')
                unknown = 0
            time.sleep(2)

        raise TaskError(f'Ascension: run không kết thúc sau {self.cfg.run_timeout}s')

    # --- chọn thẻ -----------------------------------------------------------

    def _handle_card_pick(self, img, suffix: int) -> bool:
        """Chọn thẻ ở màn chọn/nâng thẻ. Nhiều thẻ 👍 -> thẻ có mức tăng level lớn nhất
        (Super Rare không level = ưu tiên tuyệt đối; hoà -> trái nhất). Không 👍 -> refresh
        bộ thẻ 1 lần (40 coin, nếu màn có nút) rồi đánh giá lại; vẫn không -> thẻ focus."""
        recs = self._recommend_xs(img)
        has_select = self.appear(ASCENSION_SELECT)
        if not recs and not has_select:
            return False

        if self.cfg.brief_mode and self.appear(BRIEF_OFF):
            self.device.click(BRIEF_OFF)
            logger.info('Ascension: bật Brief mode')
            time.sleep(1)
            return True

        if recs:
            ci, why = pick_card(img, recs, self.cfg.card_priority)
            target = CARD_X[ci]
        else:
            # Không thẻ 👍: thử đổi bộ thẻ 1 lần (màn Enhance không có nút refresh -> tự bỏ qua)
            if (self.cfg.refresh_cards_no_recommend
                    and has_select and not getattr(self, '_card_refreshed', False)
                    and self.appear(CARD_REFRESH)):
                coins = read_coins(img)
                if coins is None or coins >= CARD_REFRESH_COST:
                    self._card_refreshed = True
                    logger.info(f'Ascension: không thẻ 👍 — refresh bộ thẻ '
                                f'({CARD_REFRESH_COST} coin, số dư {coins})')
                    self.device.click(CARD_REFRESH)
                    time.sleep(2.5)
                    return True
            target = ASCENSION_SELECT.last_match[0]
            why = 'game focus sẵn'

        # Guard chống dao động: nếu tap focus >=3 lần liên tiếp mà vẫn chưa Select được
        # (vd thanh Lv của 1 thẻ đọc chập chờn làm quyết định lật qua lại) -> chọn luôn
        # thẻ đang focus thay vì tap tiếp.
        taps = getattr(self, '_focus_taps', 0)
        if has_select and (abs(ASCENSION_SELECT.last_match[0] - target) < 80 or taps >= 3):
            if taps >= 3 and abs(ASCENSION_SELECT.last_match[0] - target) >= 80:
                logger.warning(f'Ascension: dao động chọn thẻ ({taps} lần tap) — '
                               f'chọn thẻ đang focus x={ASCENSION_SELECT.last_match[0]}')
            else:
                logger.info(f'Ascension: Select thẻ x={target} ({why})')
            self._focus_taps = 0
            self._card_refreshed = False  # lượt chọn kết thúc -> lượt sau được refresh lại
            self.device.click_xy(*ASCENSION_SELECT.last_match, name=f'ASC_SEL_{suffix}')
        else:
            # Thẻ đích chưa focus: tap thẻ để nút Select nhảy sang dưới thẻ đó
            self._focus_taps = taps + 1
            self.device.click_xy(target, CARD_Y, name=f'ASC_CARD_{suffix}')
        return True

    # --- shop (Trade Domain) --------------------------------------------------

    def _do_shop_room(self, last_room: bool) -> None:
        """Phòng shop trọn gói. Giữa run: mua (chừa 360 coin) -> Enhance tới mốc 180 (giữ coin cho
        shop sau). PHÒNG CUỐI (coin mất trắng khi rời): ưu tiên GIÁ TRỊ LÂU DÀI hơn enhance bậc cao
        ROI kém — mua chừa 360 -> enhance tới mốc 180 -> VÉT sạch kệ (note/thẻ, refresh) -> chỉ khi
        còn dư mới enhance nốt tới hết (note 15đ Record lời hơn enhance bậc 540/740). Xem
        docs/ascension-strategy.md §5."""
        self._shop_refreshes = 0
        self._do_shop(last_room=last_room)
        self._do_enhance(last_room=last_room, until_broke=False)   # dừng ở mốc 180 (cả phòng cuối)
        if not last_room:
            return
        img = self.device.screenshot()
        coins = read_coins(img)
        if coins is not None and coins >= SHOP_MIN_PRICE and self.appear(SHOP_PURCHASE):
            logger.info(f'Ascension: phòng cuối còn {coins} coin — vét note/thẻ + refresh kệ trước')
            self._do_shop(last_room=True, burn=True)
        # Còn dư sau khi vét sạch kệ -> enhance nốt (coin sẽ mất khi rời Monolith)
        self._do_enhance(last_room=True, until_broke=True)

    def _do_shop(self, last_room: bool, burn: bool = False) -> None:
        """Từ màn options shop: mở shop UI, mua theo thứ tự SALE trước rồi giá rẻ trước.
        Drink (kệ trên) mua tự do; Melody (kệ dưới) chỉ mua khi dialog có panel Relevant
        Harmony Skills (= note cần thiết). Luôn chừa ENHANCE_RESERVE coin (trừ lượt burn
        vét phòng cuối — mua tất khi còn tiền). Phòng cuối refresh kệ ≤2 lượt. Xong thoát."""
        img = self.device.screenshot()
        if not self.appear(SHOP_PURCHASE):
            logger.warning('Ascension: mất màn options shop — bỏ qua mua sắm')
            return
        mode = 'vét coin' if burn else ('phòng cuối' if last_room else 'giữa run')
        logger.info(f'Ascension: phòng Shop — mua sắm ({mode})')
        self.device.click_xy(640, SHOP_PURCHASE.last_match[1], name='ASC_SHOP_OPEN')
        time.sleep(3)
        # Reserve = coin chừa lại khi mua/refresh (đảm bảo đủ enhance sau đó).
        # - burn (vét cuối): 0.
        # - giữa run: enhance_reserve (360 = Free+60+120+180) — vì phòng sau còn cần enhance.
        # - PHÒNG CUỐI: chỉ chừa cho 2 bậc enhance RẺ nhất (60+120=180) thay vì 360, để CẢ 2 refresh
        #   charge đều được dùng (surface SALE) + mua thêm SALE. Bậc enhance 180 (biên, ROI kém hơn 1
        #   SALE potential 45-72) nhường chỗ cho refresh+SALE. Xem docs/ascension-strategy.md §3.
        reserve = 0 if burn else (self.cfg.enhance_reserve_last_room if last_room
                                  else self.cfg.enhance_reserve)
        while True:
            if not self._shop_settle():
                logger.warning('Ascension: lạc khỏi shop UI — dừng mua')
                return
            img = self.device.screenshot()
            coins = read_coins(img)
            if coins is None:
                coins = self._read_coins_stable()
                img = self.device.image
            offers = {i: slot_offer(img, i) for i in range(8)}
            avail = [(i, p, sale) for i, off in offers.items() if off for p, sale in [off]]
            logger.info(f'Ascension: coin={coins} | kệ: '
                        + ', '.join(f"slot{i}={'SALE ' if s else ''}{p}" for i, p, s in avail))
            if coins is None and not burn:
                logger.warning('Ascension: không đọc được số dư coin — bỏ qua mua sắm '
                               'để chắc chắn đủ tiền enhance (glyph lạ đã dump log/coin_glyphs)')
                break
            # SALE trước (rẻ trước trong nhóm), rồi hàng thường rẻ trước
            avail.sort(key=lambda o: (not o[2], o[1]))
            for i, price, sale in avail:
                if coins is not None and coins - price < reserve:
                    continue  # slot sau có thể rẻ hơn -> không break
                _, coins = self._buy_slot(i, price, sale, coins, reserve, burn)
            # Refresh kệ: chỉ phòng cuối (nếu bật), còn lượt, và dư tiền mua tiếp sau khi refresh
            coins = read_coins(self.device.screenshot())
            if (not last_room or not self.cfg.refresh_shelf_last_room
                    or self._shop_refreshes >= 2 or coins is None
                    or coins - SHOP_REFRESH_COST - reserve < SHOP_MIN_PRICE):
                break
            if not self._shop_settle():
                return
            logger.info(f'Ascension: refresh kệ lượt {self._shop_refreshes + 1} '
                        f'({SHOP_REFRESH_COST} coin, số dư {coins})')
            self.device.click_xy(*SHOP_REFRESH_XY, name=f'ASC_SHOPREF_{self._shop_refreshes}')
            self._shop_refreshes += 1
            time.sleep(2.5)
        if self._shop_settle():
            self.device.click_xy(*SHOP_BACK_XY, name='ASC_SHOP_EXIT')
            time.sleep(2.5)

    def _buy_slot(self, i: int, price: int, sale: bool, coins, reserve: int, burn: bool):
        """Mở dialog slot i và mua nếu hợp lệ. Trả (đã_mua, số_dư_mới). Melody không có panel
        Relevant Harmony Skills = không cần thiết -> đóng dialog (trừ lượt burn). Giá lấy lại
        từ dialog (chuẩn hơn kệ — run 2026-07-05 kệ đọc sai vài slot) để chốt ngân sách."""
        if not self._shop_settle():
            return False, coins
        self.device.click_xy(*SHOP_SLOTS[i], name=f'ASC_SLOT_{i}')
        time.sleep(1.8)
        img = self.device.screenshot()
        if not self.appear(SHOP_DIALOG):
            return False, coins  # Sold Out / màn khác chen ngang
        if i >= 4 and not burn and self.cfg.buy_melody_when_needed_only \
                and not self.appear(SHOP_RELEVANT):
            logger.info(f'Ascension: slot{i} Melody không Harmony Skill nào cần — bỏ qua')
            self._audit_dump(f'skip_slot{i}')
            self.device.click_xy(*SHOP_CLOSE_XY, name=f'ASC_SHOPX_{i}')
            time.sleep(1.5)
            return False, coins
        dlg = dialog_price(img)
        if dlg is not None and dlg != price:
            logger.info(f'Ascension: slot{i} giá dialog {dlg} != giá kệ {price} — tin dialog')
            self._audit_dump(f'price_slot{i}')
            price = dlg
        if coins is not None and coins - price < reserve:
            logger.info(f'Ascension: slot{i} giá {price} vượt ngân sách '
                        f'(số dư {coins}, chừa {reserve}) — bỏ qua')
            self.device.click_xy(*SHOP_CLOSE_XY, name=f'ASC_SHOPX_{i}')
            time.sleep(1.5)
            return False, coins
        self.device.click_xy(*SHOP_BUY_XY, name=f'ASC_BUY_{i}')
        time.sleep(2)
        self.device.screenshot()
        if self.appear(SHOP_DIALOG):
            # Không mua được (thiếu coin dù đã tính?) — đóng dialog đi tiếp
            logger.warning(f'Ascension: slot{i} mua hụt (giá {price}, số dư ước {coins})')
            self.device.click_xy(*SHOP_CLOSE_XY, name=f'ASC_SHOPX_{i}')
            time.sleep(1.5)
            return False, coins
        self._shop_settle()  # Drink -> chọn 1-trong-3 thẻ; Melody -> popup Notes
        new = read_coins(self.device.screenshot())
        expect = coins - price if coins is not None else None
        if new is None:
            new = expect
        elif expect is not None and new not in (expect, expect - CARD_REFRESH_COST):
            # Lệch đúng 40 = refresh thẻ trong màn chọn của Drink (đã tự log) -> không cảnh báo
            logger.warning(f'Ascension: slot{i} số dư đọc {new} != kỳ vọng {expect} '
                           f'({coins} - {price}) — tin số đọc được')
            self._audit_dump(f'recon_slot{i}')
        logger.info(f"Ascension: đã mua slot{i} ({'SALE ' if sale else ''}{price}) — còn {new}")
        return True, new

    def _read_coins_stable(self, tries: int = 3, delay: float = 1.3):
        """read_coins với retry — pill hay None thoáng qua khi số coin đang animation
        (glyph bị cắt giữa chừng, thấy trong run 03:43 2026-07-05)."""
        for _ in range(tries):
            v = read_coins(self.device.screenshot())
            if v is not None:
                return v
            time.sleep(delay)
        return None

    def _audit_dump(self, tag: str) -> None:
        """Lưu screenshot hiện tại vào log/asc_audit/ làm bằng chứng đối chiếu OCR/quyết định."""
        try:
            d = ROOT / 'log' / 'asc_audit'
            d.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(d / f'{int(time.time())}_{tag}.png'), self.device.image)
        except Exception:
            pass

    def _do_enhance(self, last_room: bool, until_broke: bool = False) -> None:
        """Enhance theo GIÁ ĐỌC TỪ DÒNG OPTION "Enhance (Free|60|... 🪙)" (phòng thường
        Free -> 60 -> 120 -> 180...; PHÒNG CUỐI không có bậc Free — run 2026-07-05). Mỗi lần
        enhance mở màn chọn 1-trong-3 thẻ (xử lý qua _settle_to_options).
        - until_broke=False (mặc định): dừng sau mốc enhance_milestone (180). Quy tắc ROI cộng đồng:
          chỉ enhance khi 1 lượt ≤200 coin (dưới 200 lời hơn mua potential 200) = Free+60+120+180.
        - until_broke=True (chỉ phòng cuối, SAU khi đã vét kệ): bấm tới khi hết tiền — coin dư sẽ
          mất trắng khi rời Monolith nên đổ nốt vào enhance.
        Guard: số dư không đổi 2 nhịp liên tiếp khi bậc trả phí -> dừng."""
        step, prev_coins, same, expect, last_cost = 0, None, 0, None, None
        while True:
            img = self.device.screenshot()
            if not self.appear(SHOP_PURCHASE):
                if not self._settle_to_options():
                    return
                img = self.device.screenshot()
            if not self.appear(SHOP_ENHANCE):
                logger.info('Ascension: không còn option Enhance — dừng')
                return
            cost = enhance_cost(img, *SHOP_ENHANCE.last_match)
            if cost is None:  # màn animation -> chụp lại vài nhịp
                for _ in range(2):
                    time.sleep(1.2)
                    cost = enhance_cost(self.device.screenshot(), *SHOP_ENHANCE.last_match)
                    if cost is not None:
                        break
            if cost is None:
                # Mù giá: bậc kế = giá bậc trước + 60 (fallback này phản ánh đúng thang tăng
                # nên vẫn vượt mốc -> dừng sạch giữa run; đầu run coi như 60)
                cost = (last_cost + ENHANCE_STEP) if last_cost is not None else ENHANCE_STEP
                logger.warning(f'Ascension: không đọc được giá enhance — ước tính {cost}')
            if not until_broke and cost > self.cfg.enhance_milestone:
                logger.info(f'Ascension: enhance đã tới mốc {self.cfg.enhance_milestone} '
                            f'— dừng ({"giữ coin cho shop sau" if not last_room else "ưu tiên vét kệ"})')
                return
            coins = read_coins(img)
            if coins is None and cost > 0:
                coins = self._read_coins_stable()  # pill hay None lúc số đang animation
            if expect is not None and coins is not None and coins != expect:
                logger.warning(f'Ascension: số dư {coins} != kỳ vọng sau enhance {expect}')
                self._audit_dump(f'enh_recon_{step}')
            if cost > 0:
                if coins is None:
                    logger.warning('Ascension: không đọc được số dư — dừng enhance trả phí')
                    return
                if coins < cost:
                    logger.info(f'Ascension: số dư {coins} < giá enhance {cost} — dừng')
                    return
            if coins is not None and coins == prev_coins and cost > 0:
                same += 1
                if same >= 2:
                    logger.warning('Ascension: enhance không trừ coin 2 nhịp — dừng')
                    return
            else:
                same = 0
            prev_coins = coins
            last_cost = cost
            expect = coins - cost if coins is not None else None
            logger.info(f"Ascension: Enhance bậc {step + 1} "
                        f"({'Free' if cost == 0 else cost} coin, số dư {coins})")
            self.device.click_xy(640, SHOP_ENHANCE.last_match[1], name=f'ASC_ENH_{step % 3}')
            step += 1
            time.sleep(2.5)
            if not self._settle_to_options():
                return

    def _settle_to_options(self, timeout: int = 45) -> bool:
        """Xử lý các màn phụ (chọn thẻ enhance/drink, popup Notes, dialog) cho tới khi thấy
        lại màn options shop (SHOP_PURCHASE). False nếu quá timeout."""
        end = time.time() + timeout
        n = 0
        while time.time() < end:
            img = self.device.screenshot()
            n += 1
            if self.appear(SHOP_PURCHASE):
                return True
            if self.appear(SHOP_NOTES):
                self.device.click_xy(*SHOP_DISMISS_XY, name=f'ASC_NOTE_{n % 3}')
                time.sleep(1.5)
                continue
            if self.appear(ASC_DIALOG_CONFIRM):
                self.device.click_xy(*ASC_DIALOG_CONFIRM.last_match, name=f'ASC_CFM_{n % 3}')
                time.sleep(2)
                continue
            if self._handle_card_pick(img, n % 3):
                time.sleep(2.5)
                continue
            time.sleep(1.5)
        logger.warning('Ascension: không về được màn options shop sau enhance')
        return False

    def _shop_settle(self, timeout: int = 30) -> bool:
        """Xử lý các màn phụ sau khi mua (chọn 1-trong-3 thẻ của Drink, popup Notes của Melody)
        cho tới khi thấy lại shop UI. False nếu quá timeout vẫn không về shop."""
        end = time.time() + timeout
        n = 0
        while time.time() < end:
            img = self.device.screenshot()
            n += 1
            if self.appear(SHOP_SHELF):
                return True
            if self.appear(SHOP_NOTES):
                self.device.click_xy(*SHOP_DISMISS_XY, name=f'ASC_NOTE_{n % 3}')
                time.sleep(1.5)
                continue
            if self._handle_card_pick(img, n % 3):
                time.sleep(2.5)
                continue
            # Màn 1-trong-3 của Drink có thể không 👍 và không focus sẵn (không có Select):
            # tap thẻ giữa để focus rồi vòng sau Select. Tap này vô hại trên các màn khác.
            if n % 4 == 3:
                self.device.click_xy(CARD_X[1], CARD_Y, name=f'ASC_SETTLE_{n % 3}')
            time.sleep(1.5)
        return False

    # --- event / nhận diện chung ----------------------------------------------

    def _handle_event_choice(self, img, suffix: int) -> tuple | None:
        """Sự kiện NPC nhiều lựa chọn. smart_event_choice=True: ưu tiên option cho phần thưởng ITEM
        free (Potential/Note — tag KHÔNG có icon coin) thay vì mù bấm dưới cùng (phát hiện live-test:
        tool cũ lấy 30 coin thay vì Rare Potential). Không có option item-free / tắt config -> bấm
        option DƯỚI CÙNG (an toàn, thường là rời/từ chối). Trả (x, y) đã bấm."""
        opts = event_options(img)
        if not opts:
            return None
        target, why = None, ''
        if getattr(self.cfg, 'smart_event_choice', True) and len(opts) >= 2:
            for cx, cy in opts:                       # trên -> dưới: item-free đầu tiên
                if not event_tag_has_coin(img, cy):
                    target, why = (cx, cy), 'thưởng item free (tag không coin)'
                    break
        if target is None:
            target, why = opts[-1], 'option dưới cùng (mặc định an toàn)'
        self.device.click_xy(*target, name=f'ASC_EVT_{suffix}')
        logger.info(f'Ascension: event {len(opts)} option -> y={target[1]} ({why})')
        return target

    def _leave_shop_room(self, img, suffix: int) -> None:
        """Rời phòng shop đã mua xong: bấm option CUỐI "Nah, let's go up right away" (lên tầng).
        Dùng thay _handle_event_choice — smart_event_choice chọn nhầm "Purchase at the shop"
        (item-free tag) làm mở lại shelf -> deadlock shelf<->options (bug 2026-07-07)."""
        opts = event_options(img)
        if opts:
            x, y = opts[-1]                  # option dưới cùng = "Nah, let's go up right away"
        else:
            x, y = 625, 517                  # fallback: toạ độ option dưới cùng màn shop options
        self.device.click_xy(x, y, name=f'ASC_GOUP_{suffix}')
        logger.info(f'Ascension: rời phòng shop — "Nah, let\'s go up" (y={y})')

    def _recommend_xs(self, img) -> list:
        """Toạ độ x các ribbon 👍 Recommended (gộp cụm >60px), trái -> phải."""
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

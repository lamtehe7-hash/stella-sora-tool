"""Page graph + asset điều hướng — khảo sát Phase 2 (2026-07-04), server EN.

Ghi chú khảo sát quan trọng:
- Phím Back Android (keyevent 4) KHÔNG có tác dụng trong game — phải bấm nút trong game.
- Trang con chuẩn (mail/missions/commission/shop/grant/friend) có nút ngôi nhà GOTO_HOME (~377,42).
- Heartlink là UI "điện thoại" fullscreen, KHÔNG có nút nhà — thoát bằng nút nguồn (HEARTLINK_EXIT).
- Panel Menu (hamburger) chứa Daily Check-in; đóng bằng MENU_CLOSE (X).
"""
from module.base.button import Button
from module.ui.page import Page, UI

# --- Check "đang ở page nào" ---
HOME_CHECK = Button('home/HOME_CHECK.png', area=(1150, 0, 1280, 90))
MISSIONS_CHECK = Button('missions/MISSIONS_CHECK.png', area=(132, 8, 268, 80))
COMMISSION_CHECK = Button('commission/COMMISSION_CHECK.png', area=(132, 8, 305, 80))
SHOP_CHECK = Button('shop/SHOP_CHECK.png', area=(132, 8, 232, 80))
GRANT_CHECK = Button('grant/GRANT_CHECK.png', area=(132, 8, 360, 80))
MAIL_CHECK = Button('mail/MAIL_CHECK.png', area=(132, 8, 226, 80))
FRIEND_CHECK = Button('friend/FRIEND_CHECK.png', area=(132, 8, 245, 80))
HEARTLINK_CHECK = Button('heartlink/HEARTLINK_CHECK.png', area=(88, 612, 220, 696))
MENU_CHECK = Button('menu/MENU_CHECK.png', area=(806, 10, 912, 82))

# --- Nút điều hướng ---
# threshold 0.80: tab nền nút nhà đổi sắc nhẹ theo trang (Basic Trial/Ascension match 0.828,
# trang không có nút ≤0.454 — đo 2026-07-04)
GOTO_HOME = Button('common/GOTO_HOME.png', area=(332, 2, 420, 82), threshold=0.80)
MAIL_ENTER = Button('home/MAIL_ENTER.png', area=(1121, 5, 1201, 78))
FRIEND_ENTER = Button('home/FRIEND_ENTER.png', area=(1046, 4, 1126, 80))
MISSIONS_ENTER = Button('home/MISSIONS_ENTER.png', area=(905, 88, 1012, 172), threshold=0.80)
HEARTLINK_ENTER = Button('home/HEARTLINK_ENTER.png', area=(992, 90, 1090, 168))
COMMISSION_ENTER = Button('home/COMMISSION_ENTER.png', area=(1168, 90, 1268, 168))
# SHOP_ENTER/MISSIONS_ENTER: crop TIGHT chỉ phần icon opaque (2026-07-05) — nền home đổi art theo
# nhân vật nổi bật làm template cũ (dính nền) vỡ match (Shop 0.796, Missions 0.606). Icon-only +
# threshold 0.80 -> bất biến nền (validate vs asset nền cũ: Shop 0.989, Missions 0.886).
SHOP_ENTER = Button('home/SHOP_ENTER.png', area=(95, 115, 190, 205), threshold=0.80)
GRANT_ENTER = Button('home/GRANT_ENTER.png', area=(178, 115, 272, 200))
MENU_ENTER = Button('home/HOME_CHECK.png', area=(1150, 0, 1280, 90), name='MENU_ENTER')
HEARTLINK_EXIT = Button('heartlink/HEARTLINK_EXIT.png', area=(1180, 10, 1260, 90))
MENU_CLOSE = Button('menu/MENU_CLOSE.png', area=(1186, 8, 1260, 82))

# --- Go hub / Bounty / Ascension (khảo sát 2026-07-04 tối) ---
# Go hub + Bounty hub là UI "điện thoại": KHÔNG có chrome chuẩn, thoát bằng nút nhà riêng (142,42).
# Trang Basic Trial + Ascension lại có chrome chuẩn (GOTO_HOME 377,42).
GO_ENTER = Button('home/GO_ENTER.png', area=(1065, 575, 1250, 710))
GO_CHECK = Button('go/GO_CHECK.png', area=(680, 420, 880, 515))  # label "Ascension" trên card
GO_HUB_HOME = Button('go/GO_HUB_HOME.png', area=(98, 0, 188, 86))
BOUNTY_ENTER = Button('go/BOUNTY_ENTER.png', area=(905, 145, 1095, 220))
BOUNTY_CHECK = Button('bounty/BOUNTY_CHECK.png', area=(350, 140, 550, 260))
BOUNTY_GO_BASIC = Button('bounty/BOUNTY_GO_BASIC.png', area=(818, 550, 1080, 648))
BASIC_TRIAL_CHECK = Button('bounty/BASIC_TRIAL_CHECK.png', area=(112, 0, 290, 100))
# Ascension tách 2 page (khảo sát 2026-07-04 đêm):
# - page 'ascension' = trang chọn stage Monolith: UI điện thoại (home riêng 142,42 như Go hub),
#   check = badge "Weekly Limit" dưới màn hình.
# - page 'asc_diff'  = trang chọn difficulty: chrome chuẩn, title "Ascension", GOTO_HOME 377,42.
ASCENSION_CHECK = Button('ascension/ASCENSION_CHECK.png', area=(295, 620, 500, 680))
ASCENSION_ENTER = Button('ascension/ASCENSION_ENTER.png', area=(830, 555, 1075, 640))
ASCENSION_TITLE = Button('ascension/ASCENSION_TITLE.png', area=(105, 8, 290, 80))

# Dialog "Network Error" (title + nút Retry bên phải) — hiện ngẫu nhiên khi rớt mạng,
# có thể cần bấm Retry vài lần liên tiếp mới qua (quan sát 2026-07-04)
NETWORK_RETRY = Button('common/NETWORK_RETRY.png', area=(657, 463, 910, 553))

# --- Nút chức năng trong trang (dùng bởi tasks/) ---
DAILY_CHECKIN = Button('menu/DAILY_CHECKIN.png', area=(798, 372, 970, 462))

# --- Page graph ---
page_home = Page('home', HOME_CHECK)
page_mail = Page('mail', MAIL_CHECK)
page_missions = Page('missions', MISSIONS_CHECK)
page_commission = Page('commission', COMMISSION_CHECK)
page_shop = Page('shop', SHOP_CHECK)
page_grant = Page('grant', GRANT_CHECK)
page_friend = Page('friend', FRIEND_CHECK)
page_heartlink = Page('heartlink', HEARTLINK_CHECK)
page_menu = Page('menu', MENU_CHECK)
page_go = Page('go', GO_CHECK)
page_bounty = Page('bounty', BOUNTY_CHECK)
page_basic_trial = Page('basic_trial', BASIC_TRIAL_CHECK)
page_ascension = Page('ascension', ASCENSION_CHECK)
page_asc_diff = Page('asc_diff', ASCENSION_TITLE)

page_home.link(MAIL_ENTER, page_mail)
page_home.link(MISSIONS_ENTER, page_missions)
page_home.link(COMMISSION_ENTER, page_commission)
page_home.link(SHOP_ENTER, page_shop)
page_home.link(GRANT_ENTER, page_grant)
page_home.link(FRIEND_ENTER, page_friend)
page_home.link(HEARTLINK_ENTER, page_heartlink)
page_home.link(MENU_ENTER, page_menu)

page_home.link(GO_ENTER, page_go)
page_go.link(GO_HUB_HOME, page_home)
page_go.link(BOUNTY_ENTER, page_bounty)
page_go.link(GO_CHECK, page_ascension)  # card Ascension — click chính label
page_bounty.link(GO_HUB_HOME, page_home)
page_bounty.link(BOUNTY_GO_BASIC, page_basic_trial)
page_ascension.link(GO_HUB_HOME, page_home)
page_ascension.link(ASCENSION_ENTER, page_asc_diff)

for _p in (page_mail, page_missions, page_commission, page_shop, page_grant, page_friend,
           page_basic_trial, page_asc_diff):
    _p.link(GOTO_HOME, page_home)
page_heartlink.link(HEARTLINK_EXIT, page_home)
page_menu.link(MENU_CLOSE, page_home)

# Popup closers toàn cục. Network Error cần bấm Retry lặp lại được (interval trong handle_popup lo).
UI.popup_closers = [NETWORK_RETRY]

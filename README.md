# Stella Sora Tool (SST)

Tool tự động hoá daily cho **Stella Sora (EN)** trên giả lập Android, kiến trúc lấy cảm hứng từ
[AzurLaneAutoScript (ALAS)](https://github.com/LmeSzinc/AzurLaneAutoScript): điều khiển qua ADB,
nhận diện màn hình bằng template matching (OpenCV), scheduler tự hẹn giờ từng task.

**Task hiện có:** Login, Mail, DailyReward, Dispatch, Shop, Stamina, Ascension, Cleanup.

## Cài đặt

```powershell
python -m venv venv
venv\Scripts\pip install -r requirements.txt
```

Yêu cầu: giả lập Android chạy game ở **1280x720** (đã test MuMu Player Global), adb.exe kèm giả lập.

## Chạy

| Lệnh | Chế độ |
|---|---|
| `python app.py` | App desktop kiểu Alas (cửa sổ WebView2, khuyến nghị) |
| `python gui.py` | Web UI tại http://localhost:22270 |
| `python sst.py` | CLI — vòng lặp scheduler 24/7 |
| `python sst.py <Task>` | CLI — chạy 1 task rồi thoát |

Lần chạy đầu tự tạo `config/stella.json` — sửa **serial** và **đường dẫn adb.exe** theo giả lập
của máy (mở app → Cấu hình).

## Build exe

```powershell
powershell -ExecutionPolicy Bypass -File dev_tools\build_exe.ps1        # dist\app\app.exe (desktop)
powershell -ExecutionPolicy Bypass -File dev_tools\build_exe.ps1 -Web   # dist\SST\SST.exe (web)
```

`assets/` phải nằm **cạnh exe** (script build tự copy). `config/` và `log/` tự tạo cạnh exe khi chạy.

## Lưu ý

- Dự án dùng cá nhân, phục vụ học tập — tự chịu rủi ro với tài khoản game.
- `PLAN.md` ghi roadmap chi tiết; `docs/game-map.md` là bản đồ màn hình/điều hướng trong game.

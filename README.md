# Stella Sora Tool (SST)

**Tiếng Việt** | [English](README_EN.md)

Tool tự động hoá công việc hằng ngày (daily) cho **Stella Sora (bản EN)** trên giả lập Android.
Kiến trúc lấy cảm hứng từ [AzurLaneAutoScript (ALAS)](https://github.com/LmeSzinc/AzurLaneAutoScript):
điều khiển qua ADB, nhận diện màn hình bằng template matching (OpenCV), scheduler tự hẹn giờ từng task.

> ⚠️ Đây là **dự án cá nhân, phi thương mại**, phục vụ học tập. Vui lòng đọc kỹ phần
> [Tuyên bố & Điều khoản sử dụng](#️-tuyên-bố--điều-khoản-sử-dụng) trước khi dùng.

---

## 🚀 Chỉ muốn chạy tool? (không cần cài Python)

Dành cho người dùng cuối — **không cần cài đặt gì ngoài giả lập**:

1. Vào trang **[Releases](https://github.com/lamtehe7-hash/stella-sora-tool/releases)** → tải file
   `StellaSoraTool-vX.Y.Z-win64.zip` **mới nhất**.
2. **Giải nén cả thư mục** ra ổ đĩa — giữ nguyên `app.exe`, `_internal/` và `assets/` cạnh nhau
   (đừng tách rời).
3. Mở giả lập Android (khuyến nghị **MuMu Player**), bật **ADB**, đăng nhập **Stella Sora (EN)** về
   màn hình Home.
4. Chạy **`app.exe`**. Lần đầu: vào **Cấu hình** nhập **Serial ADB** (vd `127.0.0.1:16384`) và
   **đường dẫn adb.exe**.
5. Bật các task muốn chạy → bấm **Start**.

> `config/` và `log/` sẽ tự tạo cạnh `app.exe` khi chạy lần đầu. Không cần cài Python.

> ⚠️ **Screenshot adb PHẢI ra đúng `1280 × 720`** (rộng × cao — game chạy ngang/landscape). Đây chính là
> con số mà panel **"Android Device"** của MuMu hiển thị (`1280 × 720 | 240 DPI`). Tool nhận diện bằng ảnh
> mẫu ở đúng kích thước này và **không tự co giãn**; đặt sang độ phân giải khác (1080×1920, 1600×900,
> custom…) sẽ khiến tool báo lỗi và dừng.
> Ngược lại, **kéo to/thu nhỏ hay zoom CỬA SỔ** MuMu trên desktop thì **vô hại** (adb chụp framebuffer
> Android, độc lập với cửa sổ hiển thị) — cứ zoom thoải mái để nhìn.

📖 Chi tiết từng task & tuỳ chọn cấu hình: **[CHANGELOG_VN.md](CHANGELOG_VN.md)**.

---

## 📋 Các task hiện có

`Login` · `Mail` · `Dispatch` (Commission) · `Shop` · `BountyTrial` · `Ascension` · `EventDaily` ·
`Grant` · `DailyReward` · `Cleanup`

Xem mô tả đầy đủ trong [CHANGELOG_VN.md](CHANGELOG_VN.md).

---

## ❓ Vì sao chỉ hỗ trợ giả lập Android, không hỗ trợ bản PC?

Bản PC (client Windows) của Stella Sora **chống tự-động-hoá**: game lọc bỏ mọi thao tác click "nhân
tạo" (injected), nên tool **điều khiển được màn hình nhưng không bấm được nút**. Đã khảo sát & dựng
thử backend PC (chụp màn hình bằng WGC chạy rất tốt) nhưng phải dừng vì rào cản này. SST vì thế chỉ
chạy trên **giả lập Android qua ADB** — nơi input được bơm ở **tầng hệ điều hành**, ngoài tầm chặn
của game (giống ALAS / StarRailCopilot / MaaStellaSora).

📄 Chi tiết kỹ thuật + cách xem lại code đã khảo sát: **[docs/pc-backend-rejected.md](docs/pc-backend-rejected.md)**.

---

## 🛠️ Chạy từ mã nguồn (cho lập trình viên)

### Cài đặt

```powershell
python -m venv venv
venv\Scripts\pip install -r requirements.txt
```

Yêu cầu: giả lập Android chạy game ở **1280x720** (đã test MuMu Player Global), `adb.exe` kèm giả lập.

### Chạy

| Lệnh | Chế độ |
|---|---|
| `python app.py` | App desktop kiểu Alas (cửa sổ WebView2, khuyến nghị) |
| `python gui.py` | Web UI tại http://localhost:22270 |
| `python sst.py` | CLI — vòng lặp scheduler 24/7 |
| `python sst.py <Task>` | CLI — chạy 1 task rồi thoát |

Lần chạy đầu tự tạo `config/stella.json` — sửa **serial** và **đường dẫn adb.exe** theo giả lập của máy.

### Build exe

```powershell
venv\Scripts\pyinstaller.exe --noconfirm app.spec
```

Kết quả: `dist\app\app.exe` + `_internal\` + `assets\`. `assets/` phải nằm **cạnh exe**;
`config/` và `log/` tự tạo cạnh exe khi chạy.

### Phát hành release (maintainer)

Tạo GitHub Release bằng **1 lệnh** (cần [GitHub CLI](https://cli.github.com) đã đăng nhập: `gh auth login`):

```powershell
# 1) Thêm mục "## vX.Y.Z" vào CHANGELOG_EN.md (script lấy notes từ đây)
# 2) Chạy:
.\dev_tools\release.ps1 -Version 0.1.1 -PreRelease
```

Script tự động: build exe → đóng gói `StellaSoraTool-vX.Y.Z-win64.zip` → trích notes từ CHANGELOG →
tạo tag + release + upload zip. Thêm `-DryRun` để chạy thử (không đụng GitHub), `-SkipBuild` để dùng
lại bản build sẵn.

---

## ⚖️ Tuyên bố & Điều khoản sử dụng

Đọc kỹ trước khi tải hoặc sử dụng. **Bằng việc tải/sử dụng tool, bạn đồng ý với toàn bộ điều khoản dưới đây.**

- **Dự án cá nhân, phi thương mại.** Được phát triển với mục đích học tập, nghiên cứu về tự động hoá.
  Không phải sản phẩm thương mại.
- **Không liên kết với nhà phát hành.** Dự án **không** được tài trợ, xác nhận hay liên kết với YoStar
  hoặc nhà phát hành Stella Sora dưới bất kỳ hình thức nào. "Stella Sora" cùng mọi thương hiệu, logo,
  tài sản liên quan thuộc quyền sở hữu của chủ sở hữu tương ứng.
- **Miễn phí — NGHIÊM CẤM thương mại hoá & sử dụng phạm pháp.** Cụ thể cấm:
  - Bán, cho thuê, thu phí phân phối hoặc đóng gói lại tool này để kiếm lời.
  - Dùng tool để vận hành dịch vụ cày thuê, buôn bán tài khoản/tài nguyên game trái phép.
  - Dùng vào bất kỳ mục đích **vi phạm pháp luật** nào (gian lận, lừa đảo, rửa tiền, phá hoại...).
- **Rủi ro tài khoản.** Tự động hoá có thể vi phạm Điều khoản dịch vụ (ToS/EULA) của game và dẫn tới
  **khoá tài khoản**. Bạn **tự chịu hoàn toàn rủi ro** khi sử dụng.
- **Miễn trừ trách nhiệm.** Phần mềm cung cấp "nguyên trạng" (AS IS), không kèm bất kỳ bảo hành nào.
  Tác giả **không chịu trách nhiệm** cho mọi thiệt hại, mất mát tài khoản/tài sản ảo, hay hậu quả pháp
  lý phát sinh từ việc sử dụng hoặc lạm dụng tool.
- **Quyền riêng tư.** Tool **không** thu thập hay gửi thông tin tài khoản đi bất kỳ đâu; mọi cấu hình
  (serial/adb) do bạn tự nhập và chỉ lưu **cục bộ** trên máy.
- **Gỡ bỏ theo yêu cầu.** Nếu nhà phát hành/chủ sở hữu quyền hợp pháp yêu cầu, dự án sẽ ngừng phân phối.

---

## 📄 Giấy phép

Phát hành theo **[PolyForm Noncommercial License 1.0.0](LICENSE)** — được phép dùng, sửa và chia sẻ
cho mục đích **phi thương mại**; **mọi hình thức sử dụng thương mại đều bị cấm**.

## 📚 Tài liệu

- [CHANGELOG_VN.md](CHANGELOG_VN.md) / [CHANGELOG_EN.md](CHANGELOG_EN.md) — chi tiết bản phát hành.
- `docs/game-map.md` — bản đồ màn hình / điều hướng trong game.

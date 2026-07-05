#!/usr/bin/env bash
# Stop hook: tự build lại dist/app/app.exe SAU MỖI TASK, nhưng chỉ khi source thật sự đổi.
#   - có file .py (app.py/gui.py/sst.py/module/tasks) mới hơn marker -> pyinstaller build + copy assets
#   - chỉ assets đổi -> copy lại assets (nhanh, không build)
#   - không đổi -> no-op
# An toàn: KHÔNG build khi app.exe đang chạy (khóa dist/app -> hỏng bản đang dùng); và chỉ coi là
# thành công khi exe THỰC SỰ có mặt sau build (pyinstaller đôi khi exit 0 mà không ra exe do file bị khóa).
# Marker dist/app/.last_sync = mốc lần build/đồng bộ gần nhất. In JSON {systemMessage} cho Claude Code.
cd "e:/Claude/Stella Sora Tool" || exit 0
marker="dist/app/.last_sync"
exe="dist/app/app.exe"

sync_assets() { rm -rf dist/app/assets && cp -r assets dist/app/assets; }

need_build=0
need_assets=0
if [ ! -f "$exe" ] || [ ! -f "$marker" ]; then
  need_build=1
else
  if [ -n "$(find app.py gui.py sst.py module tasks -name '*.py' -newer "$marker" 2>/dev/null | head -1)" ]; then
    need_build=1
  fi
  if [ -n "$(find assets -type f -newer "$marker" 2>/dev/null | head -1)" ]; then
    need_assets=1
  fi
fi

if [ "$need_build" = 1 ]; then
  # Không build khi app.exe còn chạy (con msedgewebview2 khóa dist/app) — nhắc đóng, thử lại lần sau.
  running=$(powershell -NoProfile -Command "@(Get-Process app -ErrorAction SilentlyContinue).Count" 2>/dev/null | tr -d '[:space:]')
  if [ -n "$running" ] && [ "$running" != "0" ]; then
    echo '{"systemMessage":"⏭️ app.exe đang chạy — bỏ auto-build. Đóng app rồi task sau sẽ build lại."}'
    exit 0
  fi
  if venv/Scripts/pyinstaller.exe --noconfirm app.spec >/dev/null 2>&1 && [ -f "$exe" ]; then
    sync_assets
    touch "$marker"
    echo '{"systemMessage":"🔨 app.exe đã build lại (source .py đổi)"}'
  else
    # KHÔNG touch marker -> lần Stop sau tự thử lại
    echo '{"systemMessage":"⚠️ auto-build LỖI (không ra exe — app.exe còn khóa dist/app?). Chạy tay: venv/Scripts/pyinstaller.exe --noconfirm app.spec"}'
  fi
elif [ "$need_assets" = 1 ]; then
  sync_assets
  touch "$marker"
  echo '{"systemMessage":"📁 assets đã đồng bộ vào dist/app"}'
fi
exit 0

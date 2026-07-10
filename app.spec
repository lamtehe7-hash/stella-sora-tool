# -*- mode: python ; coding: utf-8 -*-
# Build app desktop (pywebview): venv\Scripts\pyinstaller.exe --noconfirm app.spec
# Kết quả: dist\app\app.exe — nhớ copy assets/ nằm cạnh exe (dev_tools/build_exe.ps1 làm sẵn).
from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = []
# pywebio: cho giao diện WEB dự phòng (app.py::_run_web_ui) khi desktop/clr lỗi trên máy user
for pkg in ('webview', 'clr_loader', 'pythonnet', 'adbutils', 'pywebio'):
    tmp_ret = collect_all(pkg)
    datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
hiddenimports += ['gui']  # module trang pywebio (app.py import lazy trong _run_web_ui)


a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='app',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='app',
)

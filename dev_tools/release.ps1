<#
.SYNOPSIS
  Tạo GitHub Release bằng 1 lệnh: build exe -> đóng gói zip portable -> trích notes từ
  CHANGELOG -> tạo tag + release + upload zip (qua GitHub CLI).

.EXAMPLE
  .\dev_tools\release.ps1 -Version 0.1.1 -PreRelease
  .\dev_tools\release.ps1 -Version 1.0.0
  .\dev_tools\release.ps1 -Version 0.1.1 -DryRun        # chỉ build+zip+xem notes, KHÔNG đụng GitHub

.NOTES
  - Cần GitHub CLI (gh) đã đăng nhập: chạy `gh auth login` một lần, hoặc đặt biến $env:GH_TOKEN.
  - Notes lấy từ mục "## v<Version>" trong CHANGELOG_EN.md — nhớ cập nhật CHANGELOG trước khi release.
  - KHÔNG build khi app.exe đang chạy (dist\app bị khóa).
#>
[CmdletBinding()]
param(
  [Parameter(Mandatory)][string]$Version,   # vd "0.1.1" (không kèm 'v')
  [switch]$PreRelease,
  [switch]$SkipBuild,
  [switch]$Draft,
  [switch]$DryRun,
  [string]$NotesFile                          # tùy chọn: tự cấp file notes thay vì trích CHANGELOG
)
$ErrorActionPreference = 'Stop'

$repo = Split-Path $PSScriptRoot -Parent      # thư mục gốc dự án (cha của dev_tools)
$tag  = "v$($Version.TrimStart('v'))"
$zipName = "StellaSoraTool-$tag-win64.zip"
$relDir  = Join-Path $repo 'releases'
$zipPath = Join-Path $relDir $zipName
Set-Location $repo

function Info($m) { Write-Host "  $m" -ForegroundColor Cyan }
function Ok($m)   { Write-Host "✅ $m" -ForegroundColor Green }

# --- 0. Tìm gh ---
$gh = (Get-Command gh -ErrorAction SilentlyContinue).Source
if (-not $gh) { $gh = "$env:LOCALAPPDATA\Programs\gh\bin\gh.exe" }
if (-not $DryRun -and -not (Test-Path $gh)) {
  throw "Không tìm thấy GitHub CLI (gh). Cài rồi thử lại, hoặc chạy với -DryRun."
}

# --- 1. Build exe ---
if (-not $SkipBuild) {
  if (@(Get-Process app -ErrorAction SilentlyContinue).Count -gt 0) {
    throw "app.exe đang chạy — đóng app rồi chạy lại (dist\app bị khóa)."
  }
  Info "Build exe (pyinstaller app.spec)..."
  & "$repo\venv\Scripts\pyinstaller.exe" --noconfirm app.spec | Out-Null
  if (-not (Test-Path "$repo\dist\app\app.exe")) { throw "Build không ra exe." }
  Remove-Item "$repo\dist\app\assets" -Recurse -Force -ErrorAction SilentlyContinue
  Copy-Item "$repo\assets" "$repo\dist\app\assets" -Recurse
  Ok "Build xong + đồng bộ assets."
} else { Info "Bỏ qua build (-SkipBuild) — dùng dist\app hiện có." }
if (-not (Test-Path "$repo\dist\app\app.exe")) { throw "Chưa có dist\app\app.exe — bỏ -SkipBuild để build." }

# --- 2. Đóng gói zip portable (bsdtar -> forward slash chuẩn, thư mục gốc StellaSoraTool) ---
New-Item -ItemType Directory -Force $relDir | Out-Null
$stage = Join-Path $relDir 'StellaSoraTool'
if (Test-Path $stage) { Remove-Item $stage -Recurse -Force }
Copy-Item "$repo\dist\app" $stage -Recurse
@"
Stella Sora Tool — bản portable $tag (Windows 64-bit)

CÁCH DÙNG:
  1. Giải nén CẢ thư mục này — giữ app.exe, _internal và assets cạnh nhau.
     ⚠️ Giải nén vào đường dẫn KHÔNG DẤU (vd C:\StellaSoraTool), TRÁNH thư mục tên tiếng Việt có dấu.
  2. Mở giả lập Android, bật ADB, đăng nhập Stella Sora (EN) về màn hình Home.
  3. Chạy app.exe. Lần đầu: vào Cấu hình nhập Serial ADB (vd 127.0.0.1:16384) + đường dẫn adb.
  4. Bật task muốn chạy rồi bấm Start.

config/ và log/ tự tạo cạnh app.exe khi chạy lần đầu. Không cần cài Python.

NẾU app.exe BÁO LỖI "Failed to resolve Python.Runtime..." (giao diện desktop lỗi):
  → Bấm YES ở hộp thoại để MỞ BẰNG GIAO DIỆN WEB (trình duyệt) — không cần .NET, chạy mọi máy.
    (hoặc chạy thẳng:  app.exe --web)
  → Muốn dùng bản desktop thì thử: (1) giải nén vào đường dẫn KHÔNG dấu; (2) chuột phải file .zip →
    Properties → Unblock → giải nén lại; (3) máy Windows cũ thì cài .NET Framework 4.8 + WebView2:
      .NET 4.8:   https://dotnet.microsoft.com/download/dotnet-framework/net48
      WebView2:   https://developer.microsoft.com/microsoft-edge/webview2/
"@ | Set-Content "$stage\README.txt" -Encoding utf8
if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
Push-Location $relDir
tar -a -c -f $zipName 'StellaSoraTool'
Pop-Location
Remove-Item $stage -Recurse -Force
$sizeMB = [math]::Round((Get-Item $zipPath).Length / 1MB, 1)
Ok "Đóng gói $zipName ($sizeMB MB)."

# --- 3. Notes: trích mục CHANGELOG hoặc dùng file tự cấp ---
function Get-Section($file, $tag) {
  if (-not (Test-Path $file)) { return $null }
  $lines = Get-Content -LiteralPath $file -Encoding utf8
  $start = -1; $end = $lines.Count
  $re = '^##\s+' + [regex]::Escape($tag) + '(\b|\s|$)'
  for ($i = 0; $i -lt $lines.Count; $i++) {
    if ($start -lt 0) { if ($lines[$i] -match $re) { $start = $i } }
    elseif ($lines[$i] -match '^##\s+v') { $end = $i; break }
  }
  if ($start -lt 0) { return $null }
  return ($lines[$start..($end - 1)] -join "`n").Trim()
}

# slug owner/repo từ origin để tạo link CHANGELOG đầy đủ
$slug = ''
try { if ((git -C $repo remote get-url origin) -match 'github\.com[:/](.+?)(?:\.git)?$') { $slug = $matches[1] } } catch {}

if ($NotesFile) {
  if (-not (Test-Path $NotesFile)) { throw "Không thấy NotesFile: $NotesFile" }
  $notesPath = $NotesFile
} else {
  $body = Get-Section "$repo\CHANGELOG_EN.md" $tag
  if (-not $body) {
    throw "CHANGELOG_EN.md chưa có mục '## $tag'. Thêm mục changelog cho $tag rồi chạy lại (hoặc dùng -NotesFile)."
  }
  if ($slug) {
    $body += "`n`n---`n📖 Full changelog: " +
             "[EN](https://github.com/$slug/blob/main/CHANGELOG_EN.md) · " +
             "[VN](https://github.com/$slug/blob/main/CHANGELOG_VN.md)"
  }
  $notesPath = Join-Path $relDir "_notes_$tag.md"
  $body | Set-Content $notesPath -Encoding utf8
}
Ok "Notes: $notesPath"

# --- 4. Tạo release + upload ---
$ghArgs = @('release', 'create', $tag, $zipPath,
            '--title', "Stella Sora Tool $tag",
            '--notes-file', $notesPath, '--target', 'main')
if ($PreRelease) { $ghArgs += '--prerelease' }
if ($Draft)      { $ghArgs += '--draft' }

if ($DryRun) {
  Write-Host "`n--- DRY RUN (không gọi GitHub) ---" -ForegroundColor Yellow
  Write-Host "Lệnh: gh $($ghArgs -join ' ')"
  Write-Host "`n----- NOTES PREVIEW -----`n" -ForegroundColor Yellow
  Get-Content $notesPath | Write-Host
  return
}

# kiểm tra đăng nhập
& $gh auth status 2>$null
if ($LASTEXITCODE -ne 0 -and -not $env:GH_TOKEN) {
  throw "gh chua dang nhap. Chay: gh auth login (mot lan), hoac dat bien moi truong GH_TOKEN."
}
Info "Tạo release $tag trên GitHub..."
& $gh @ghArgs
if ($LASTEXITCODE -ne 0) { throw "gh release create thất bại (exit $LASTEXITCODE)." }
Ok "Đã phát hành $tag."
& $gh release view $tag --web 2>$null

/* Logic UI: poll trạng thái từ Python (pywebview js_api) mỗi giây và render kiểu Alas. */
'use strict';

const $ = (id) => document.getElementById(id);

let lastSeq = 0;
let autoScroll = true;
let logCount = 0;
const LOG_MAX = 800;
let currentPage = 'overview';
let currentTask = null;   // tên task đang mở ở page-task
let lastState = null;     // snapshot poll gần nhất

// ===== Theme =====
function setTheme(t) {
  document.documentElement.dataset.theme = t;
  localStorage.setItem('sst-theme', t);
}
setTheme(localStorage.getItem('sst-theme') || 'light');
document.querySelectorAll('[data-theme]').forEach((b) => {
  if (b.tagName === 'BUTTON') b.addEventListener('click', () => setTheme(b.dataset.theme));
});

// ===== Toast =====
let toastTimer = null;
function toast(msg) {
  const el = $('toast');
  el.textContent = msg;
  el.classList.remove('hidden');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.add('hidden'), 2500);
}

// ===== Điều hướng =====
const PAGE_TITLES = { home: 'Home', overview: 'Overview', settings: 'Cấu hình', task: '' };

function showPage(page, taskName) {
  currentPage = page;
  currentTask = page === 'task' ? taskName : null;
  ['overview', 'task', 'home', 'settings'].forEach((p) => {
    $('page-' + p).classList.toggle('hidden', p !== page);
  });
  $('page-title').textContent = page === 'task' ? taskName : PAGE_TITLES[page];

  document.querySelectorAll('.rail-item').forEach((b) => {
    b.classList.toggle('active', b.dataset.page === page ||
      (b.dataset.page === 'overview' && page === 'task'));
  });
  document.querySelectorAll('#sidebar .menu-item').forEach((m) => {
    m.classList.toggle('active',
      (m.dataset.page === page && page !== 'task') ||
      (page === 'task' && m.dataset.task === taskName));
  });

  if (page === 'task' && lastState) renderTaskDetail();
  if (page === 'settings') loadConfig();
}

document.querySelectorAll('.rail-item').forEach((b) =>
  b.addEventListener('click', () => showPage(b.dataset.page)));
document.querySelector('#sidebar .menu-item[data-page="overview"]')
  .addEventListener('click', () => showPage('overview'));

// ===== Render Overview =====
function taskRow(t, extra) {
  return `<div class="task-row">
    <div><div class="task-name">${t.name}</div>${extra || ''}</div>
    <button class="btn btn-sm" data-setting="${t.name}">Setting</button>
  </div>`;
}

function renderLists(s) {
  const running = s.tasks.filter((t) => t.name === s.current && s.state === 'running');
  const pending = s.tasks.filter((t) => t.enable && t.ready && t.name !== s.current);
  const waiting = s.tasks.filter((t) => t.enable && !t.ready && t.name !== s.current);
  const off = s.tasks.filter((t) => !t.enable);

  $('list-running').innerHTML = running.length
    ? running.map((t) => taskRow(t)).join('')
    : '<div class="empty">Không có task</div>';
  $('list-pending').innerHTML = pending.length
    ? pending.map((t) => taskRow(t, '<div class="task-time">sẵn sàng</div>')).join('')
    : '<div class="empty">Không có task</div>';
  $('list-waiting').innerHTML = waiting.length
    ? waiting.map((t) => taskRow(t, `<div class="task-time">${t.next_run}</div>`)).join('')
    : '<div class="empty">Không có task</div>';

  document.querySelectorAll('[data-setting]').forEach((b) =>
    b.addEventListener('click', () => showPage('task', b.dataset.setting)));

  // Sidebar: danh sách task + trạng thái nhỏ
  $('menu-tasks').innerHTML = s.tasks.map((t) => {
    const mini = t.name === s.current && s.state === 'running' ? '▶'
      : (t.enable ? (t.ready ? 'sẵn sàng' : t.next_run) : 'tắt');
    return `<div class="menu-item ${t.enable ? '' : 'task-off'}" data-task="${t.name}">
      ${t.name}<span class="mini">${mini}</span></div>`;
  }).join('');
  document.querySelectorAll('#menu-tasks .menu-item').forEach((m) => {
    m.addEventListener('click', () => showPage('task', m.dataset.task));
    m.classList.toggle('active', currentPage === 'task' && m.dataset.task === currentTask);
  });
}

const STATUS = {
  off:      ['dot-idle',    'Chưa chạy'],
  idle:     ['dot-waiting', 'Đang khởi động...'],
  running:  ['dot-running', ''],
  waiting:  ['dot-waiting', 'Chờ task đến hạn'],
  stopped:  ['dot-idle',    'Đã dừng'],
  error:    ['dot-error',   ''],
  human:    ['dot-error',   'Cần người can thiệp'],
};

function renderHeader(s) {
  const [dot, text] = STATUS[s.state] || ['dot-idle', s.state];
  $('status-dot').className = 'dot ' + dot;
  $('status-text').textContent =
    s.state === 'running' ? 'Đang chạy: ' + s.current :
    s.state === 'error' ? 'Lỗi: ' + s.error : text;

  const btn = $('btn-scheduler');
  if (s.alive) {
    btn.textContent = '■ Dừng';
    btn.className = 'btn btn-danger';
  } else {
    btn.textContent = 'Bắt đầu';
    btn.className = 'btn btn-primary';
  }
}

function renderTaskDetail() {
  const t = lastState.tasks.find((x) => x.name === currentTask);
  if (!t) return;
  $('task-title').textContent = t.name;
  $('task-enable').checked = t.enable;
  $('task-next').textContent =
    lastState.state === 'running' && lastState.current === t.name ? '▶ đang chạy'
      : (t.enable ? (t.ready ? 'sẵn sàng' : t.next_run) : 'đã tắt');
}

function appendLog(lines) {
  if (!lines.length) return;
  const body = $('log-body');
  body.textContent += (body.textContent ? '\n' : '') + lines.join('\n');
  logCount += lines.length;
  if (logCount > LOG_MAX) {
    const arr = body.textContent.split('\n').slice(-LOG_MAX);
    body.textContent = arr.join('\n');
    logCount = arr.length;
  }
  if (autoScroll) body.scrollTop = body.scrollHeight;
}

// ===== Poll =====
async function poll() {
  if (!window.pywebview) return;
  try {
    const s = await pywebview.api.poll(lastSeq);
    lastState = s;
    lastSeq = s.seq;
    renderHeader(s);
    if (currentPage === 'overview') renderLists(s);
    if (currentPage === 'task') renderTaskDetail();
    appendLog(s.lines);
  } catch (e) { /* Python đang bận — bỏ qua nhịp này */ }
}

// ===== Nút bấm =====
$('btn-scheduler').addEventListener('click', async () => {
  const r = lastState && lastState.alive
    ? await pywebview.api.stop()
    : await pywebview.api.start();
  if (r) toast(r);
});

$('btn-autoscroll').addEventListener('click', () => {
  autoScroll = !autoScroll;
  const b = $('btn-autoscroll');
  b.textContent = 'Auto Scroll ' + (autoScroll ? 'ON' : 'OFF');
  b.className = 'btn ' + (autoScroll ? 'btn-primary' : 'off');
  if (autoScroll) $('log-body').scrollTop = $('log-body').scrollHeight;
});

$('task-enable').addEventListener('change', async () => {
  if (currentTask) {
    const r = await pywebview.api.toggle(currentTask);
    if (r) toast(r);
    poll();
  }
});

$('btn-run-now').addEventListener('click', async () => {
  if (currentTask) {
    const r = await pywebview.api.run_now(currentTask);
    if (r) toast(r);
  }
});

// ===== Cấu hình =====
async function loadConfig() {
  if (!window.pywebview) return;
  const c = await pywebview.api.get_config();
  $('cfg-serial').value = c.serial;
  $('cfg-adb').value = c.adb_path;
  $('cfg-reset').value = c.daily_reset_utc;
  $('cfg-close').checked = c.close_game_on_cleanup;
}

$('btn-save-cfg').addEventListener('click', async () => {
  const r = await pywebview.api.save_config({
    serial: $('cfg-serial').value.trim(),
    adb_path: $('cfg-adb').value.trim(),
    daily_reset_utc: $('cfg-reset').value.trim(),
    close_game_on_cleanup: $('cfg-close').checked,
  });
  toast(r || 'Đã lưu cấu hình');
  const note = $('cfg-saved');
  note.classList.remove('hidden');
  setTimeout(() => note.classList.add('hidden'), 2000);
});

// ===== Khởi động =====
function boot() {
  showPage('overview');
  poll();
  setInterval(poll, 1000);
}
if (window.pywebview) boot();
else window.addEventListener('pywebviewready', boot);

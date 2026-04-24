/**
 * VocaTask CRM — Frontend: task list, detail, status management.
 */

// ── State ──────────────────────────────────────────────────────────────────
const state = {
    view: 'list',          // 'list' | 'detail'
    currentUser: localStorage.getItem('crm_user') || '',
    statusFilter: '',
    viewMode: 'all',       // 'all' | 'mine'
    refreshTimer: null,
    currentTaskId: null,
    sortBy: 'time',        // 'time' | 'priority'
    sortDir: 'desc',       // 'desc' | 'asc'
};

// ── API ────────────────────────────────────────────────────────────────────
const CrmApi = {
    async getTasks(status, assignee) {
        const params = new URLSearchParams();
        if (status) params.set('status', status);
        if (assignee) params.set('assignee', assignee);
        const res = await fetch('/api/crm/tasks?' + params);
        return res.json();
    },
    async getTask(id) {
        const res = await fetch(`/api/crm/tasks/${id}`);
        return res.json();
    },
    async updateStatus(id, status) {
        const res = await fetch(`/api/crm/tasks/${id}/status`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status, updated_by: state.currentUser }),
        });
        return res.json();
    },
    async deleteTask(id) {
        const res = await fetch(`/api/crm/tasks/${id}`, { method: 'DELETE' });
        return res.json();
    },
    async addNote(id, noteText) {
        const res = await fetch(`/api/crm/tasks/${id}/notes`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ note_text: noteText, note_by: state.currentUser }),
        });
        return res.json();
    },
    async getStats() {
        const res = await fetch('/api/crm/stats');
        return res.json();
    },
};

// ── Helpers ────────────────────────────────────────────────────────────────
function esc(str) {
    return String(str || '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

// SQLite CURRENT_TIMESTAMP is UTC without 'Z'; append it so JS parses correctly.
function parseTs(ts) {
    if (!ts) return null;
    const s = String(ts).replace(' ', 'T');
    return new Date(s.endsWith('Z') || s.includes('+') ? s : s + 'Z');
}

function relativeTime(ts) {
    const d = parseTs(ts);
    if (!d) return '';
    const diff = Date.now() - d;
    if (diff < 60000) return '刚刚';
    if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`;
    return d.toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' });
}

function formatTime(ts) {
    const d = parseTs(ts);
    if (!d) return '';
    return d.toLocaleString('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

const PRIORITY_TEXT = { high: '高', medium: '中', low: '低' };
const STATUS_TEXT = { open: '待处理', in_progress: '处理中', completed: '已完成', cancelled: '已取消' };

// ── Stats ──────────────────────────────────────────────────────────────────
async function refreshStats() {
    const data = await CrmApi.getStats().catch(() => null);
    if (!data?.success) return;
    const s = data.stats;
    document.getElementById('stat-open').textContent = s.open;
    document.getElementById('stat-progress').textContent = s.in_progress;
    document.getElementById('stat-done').textContent = s.completed;
    document.getElementById('stat-total').textContent = s.total;
}

// ── Sort ───────────────────────────────────────────────────────────────────
const PRIORITY_RANK = { high: 0, medium: 1, low: 2 };

function sortTasks(tasks) {
    return [...tasks].sort((a, b) => {
        let cmp = 0;
        if (state.sortBy === 'priority') {
            cmp = (PRIORITY_RANK[a.priority] ?? 1) - (PRIORITY_RANK[b.priority] ?? 1);
        } else {
            cmp = (parseTs(a.created_at) || 0) - (parseTs(b.created_at) || 0);
        }
        return state.sortDir === 'desc' ? -cmp : cmp;
    });
}

function toggleSort(col) {
    if (state.sortBy === col) {
        state.sortDir = state.sortDir === 'desc' ? 'asc' : 'desc';
    } else {
        state.sortBy = col;
        state.sortDir = col === 'time' ? 'desc' : 'asc';
    }
    loadTasks();
}

function renderTableHeader() {
    const timeIcon = state.sortBy === 'time'     ? (state.sortDir === 'desc' ? '↓' : '↑') : '↕';
    const priIcon  = state.sortBy === 'priority' ? (state.sortDir === 'asc'  ? '↑' : '↓') : '↕';
    return `<div class="task-table-header">
        <div class="th-priority${state.sortBy === 'priority' ? ' sort-active' : ''}" onclick="toggleSort('priority')">优先级 ${priIcon}</div>
        <div class="th-content">任务描述</div>
        <div class="th-time${state.sortBy === 'time' ? ' sort-active' : ''}" onclick="toggleSort('time')">时间 ${timeIcon}</div>
        <div class="th-actions">操作</div>
    </div>`;
}

// ── Task List ──────────────────────────────────────────────────────────────
async function loadTasks() {
    const assignee = state.viewMode === 'mine' ? state.currentUser : null;
    const data = await CrmApi.getTasks(state.statusFilter, assignee).catch(() => null);
    if (!data?.success) return;
    renderTaskList(data.tasks);
    document.getElementById('refresh-hint').textContent = '刚刚更新';
    refreshStats();
}

function groupTasksByTime(tasks) {
    const now = new Date();
    const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const yesterdayStart = new Date(todayStart - 86400000);
    const weekStart = new Date(todayStart - 6 * 86400000);
    const groups = [
        { key: 'today',     label: '今天', defaultOpen: true,  tasks: [] },
        { key: 'yesterday', label: '昨天', defaultOpen: false, tasks: [] },
        { key: 'week',      label: '本周', defaultOpen: false, tasks: [] },
        { key: 'earlier',   label: '更早', defaultOpen: false, tasks: [] },
    ];
    for (const t of tasks) {
        const d = parseTs(t.created_at);
        if      (d >= todayStart)     groups[0].tasks.push(t);
        else if (d >= yesterdayStart) groups[1].tasks.push(t);
        else if (d >= weekStart)      groups[2].tasks.push(t);
        else                          groups[3].tasks.push(t);
    }
    return groups.filter(g => g.tasks.length > 0);
}

function renderProgressSteps(status) {
    const steps = ['open', 'in_progress', 'completed'];
    const labels = ['已创建', '处理中', '已完成'];
    const idx = steps.indexOf(status === 'cancelled' ? 'open' : (status || 'open'));
    return `<div class="task-progress">` +
        steps.map((s, i) => {
            const done = i <= idx;
            const cur  = i === idx;
            return (i > 0 ? `<div class="prog-line${i <= idx ? ' done' : ''}"></div>` : '') +
                `<div class="prog-step${done ? ' done' : ''}${cur ? ' current' : ''}">
                    <div class="prog-dot"></div>
                    <div class="prog-label">${labels[i]}</div>
                </div>`;
        }).join('') +
    `</div>`;
}

function renderTaskCard(t) {
    const p = t.priority || 'medium';
    const s = t.status || 'open';
    const hasAnalyzed = t.task_description && t.task_description !== t.transcribed_text;
    const title = esc(t.task_description || t.transcribed_text || '(无内容)');
    const meta  = [t.assignee, t.department].filter(Boolean).map(esc).join(' · ');
    const canAccept = s === 'open' && state.currentUser;

    // 原话副标题（仅当 Claude 分析结果与原话不同时显示）
    const raw = t.transcribed_text || '';
    const rawShort = raw.length > 60 ? raw.slice(0, 60) + '…' : raw;
    const originalHtml = hasAnalyzed
        ? `<div class="task-card-original">原话：${esc(rawShort)}</div>`
        : '';

    // 图片缩略图
    const fileId = t.first_image_path
        ? t.first_image_path.replace(/\\/g, '/').split('/').pop().replace(/\.[^.]+$/, '')
        : null;
    const thumbHtml = fileId
        ? `<img class="task-card-thumb" src="/api/images/${fileId}" alt="附件">`
        : '';

    return `<div class="task-card priority-${p}" onclick="openTask(${t.id})">
        <div class="task-priority-col">
            <span class="priority-badge ${p}">${PRIORITY_TEXT[p] || p}</span>
        </div>
        <div class="task-card-main">
            <div class="task-card-title">${title}</div>
            ${originalHtml}
            <div class="task-card-meta">
                <span class="assignee">${meta}</span>
                ${t.note_count > 0 ? `<span>💬 ${t.note_count}</span>` : ''}
                ${thumbHtml}
            </div>
            ${renderProgressSteps(s)}
        </div>
        <div class="task-card-time">${relativeTime(t.created_at)}</div>
        <div class="task-card-actions" onclick="event.stopPropagation()">
            ${canAccept ? `<button class="btn-accept" onclick="quickAccept(${t.id})">接受任务</button>` : ''}
            <button class="btn-delete-card" onclick="deleteTask(${t.id})" title="删除任务">×</button>
            <span style="font-size:12px;color:#bbb">#${t.id}</span>
        </div>
    </div>`;
}

function renderTaskList(tasks) {
    const el = document.getElementById('task-list');
    if (!tasks.length) {
        el.innerHTML = renderTableHeader() + '<div class="empty-state">暂无任务</div>';
        return;
    }
    const sorted = sortTasks(tasks);
    const groups = groupTasksByTime(sorted);
    // Preserve open/closed state across refreshes
    const openKeys = new Set(
        [...el.querySelectorAll('details[open]')].map(d => d.dataset.key)
    );
    // On first render openKeys is empty — use defaultOpen
    const isFirst = openKeys.size === 0;

    el.innerHTML = renderTableHeader() + groups.map(g => {
        const isOpen = isFirst ? g.defaultOpen : openKeys.has(g.key);
        const pending = g.tasks.filter(t => (t.status || 'open') === 'open').length;
        const badge = pending > 0 ? `<span class="group-badge">${pending} 待处理</span>` : '';
        return `<details class="time-group" data-key="${g.key}"${isOpen ? ' open' : ''}>
            <summary class="group-header">
                <span class="group-arrow">›</span>
                <span class="group-label">${g.label}</span>
                <span class="group-count">${g.tasks.length} 条</span>
                ${badge}
            </summary>
            <div class="group-body">
                ${g.tasks.map(renderTaskCard).join('')}
            </div>
        </details>`;
    }).join('');
}

async function quickAccept(taskId) {
    if (!state.currentUser) { alert('请先在右上角选择当前用户'); return; }
    await CrmApi.updateStatus(taskId, 'in_progress');
    loadTasks();
}

// ── Task Detail ────────────────────────────────────────────────────────────
async function openTask(taskId) {
    state.currentTaskId = taskId;
    const data = await CrmApi.getTask(taskId).catch(() => null);
    if (!data?.success) return;
    renderTaskDetail(data.task);
    showView('detail');
}

function renderTaskDetail(t) {
    const p = t.priority || 'medium';
    const s = t.status || 'open';
    const title = esc(t.task_description || t.transcribed_text || '(无内容)');

    // Attachments
    let attachHtml = '';
    if (t.attachments?.length) {
        const imgs = t.attachments.map(a => {
            const fileId = a.image_path.replace(/\\/g, '/').split('/').pop().replace(/\.[^.]+$/, '');
            const desc = esc(a.description || '');
            return `<div style="display:inline-block">
                <img class="attachment-thumb" src="/api/images/${fileId}" alt="附件" title="${desc}">
                ${desc ? `<div style="font-size:11px;color:#888;max-width:80px;text-align:center;word-break:break-all">${desc}</div>` : ''}
            </div>`;
        }).join('');
        attachHtml = `<div class="detail-section">
            <div class="detail-section-title">附件图片</div>
            <div class="attachments-grid">${imgs}</div>
        </div>`;
    }

    // Notes
    const notesHtml = (t.notes || []).map(n => `
        <div class="note-item">
            <div class="note-meta">${esc(n.note_by)} · ${formatTime(n.created_at)}</div>
            <div class="note-text">${esc(n.note_text)}</div>
        </div>`).join('');

    // Action buttons
    let actionHtml = '<div class="status-control">';
    if (s === 'open') {
        actionHtml += `<button class="btn-status accept" onclick="changeStatus('in_progress')">▶ 开始处理</button>`;
    }
    if (s === 'in_progress') {
        actionHtml += `<button class="btn-status complete" onclick="changeStatus('completed')">✓ 标记完成</button>`;
        actionHtml += `<button class="btn-status reopen" onclick="changeStatus('open')">← 退回待处理</button>`;
    }
    if (s === 'completed') {
        actionHtml += `<button class="btn-status reopen" onclick="changeStatus('in_progress')">← 重新开始</button>`;
    }
    actionHtml += `<button class="btn-status delete-btn" onclick="deleteTask(${t.id})">🗑 删除任务</button>`;
    actionHtml += '</div>';

    document.getElementById('task-detail-content').innerHTML = `
        <div class="detail-card">
            <div class="detail-header">
                <span class="detail-id">#${t.id}</span>
                <span class="detail-title">${title}</span>
                <span class="priority-badge ${p}">${PRIORITY_TEXT[p] || p}</span>
                <span class="status-badge ${s}">${STATUS_TEXT[s] || s}</span>
            </div>

            <div class="detail-section">
                <div class="detail-section-title">语音转录</div>
                <div class="detail-text">${esc(t.transcribed_text || '(无内容)')}</div>
            </div>

            <div class="detail-section">
                <div class="detail-section-title">分配信息</div>
                <div class="detail-rows">
                    <div class="detail-row"><span class="lbl">分配给</span><span class="val">${esc(t.assignee || '-')}</span></div>
                    <div class="detail-row"><span class="lbl">部门</span><span class="val">${esc(t.department || '-')}</span></div>
                    <div class="detail-row"><span class="lbl">分配理由</span><span class="val">${esc(t.reason || '-')}</span></div>
                    <div class="detail-row"><span class="lbl">路由方式</span><span class="val">${esc(t.method || '-')}</span></div>
                    <div class="detail-row"><span class="lbl">创建时间</span><span class="val">${formatTime(t.created_at)}</span></div>
                    ${t.accepted_by ? `<div class="detail-row"><span class="lbl">接受人</span><span class="val">${esc(t.accepted_by)} · ${formatTime(t.accepted_at)}</span></div>` : ''}
                    ${t.completed_at ? `<div class="detail-row"><span class="lbl">完成时间</span><span class="val">${formatTime(t.completed_at)}</span></div>` : ''}
                </div>
            </div>

            ${attachHtml}

            <div class="detail-section">
                <div class="detail-section-title">状态操作</div>
                ${state.currentUser ? actionHtml : '<p style="color:#aaa;font-size:13px">请先在右上角选择当前用户</p>'}
            </div>

            <div class="detail-section">
                <div class="detail-section-title">处理备注</div>
                <div class="notes-list" id="notes-list">${notesHtml || '<p style="color:#ccc;font-size:13px">暂无备注</p>'}</div>
                ${state.currentUser ? `
                <div class="note-form">
                    <textarea class="note-input" id="note-input" placeholder="添加备注..." rows="2"></textarea>
                    <button class="btn-note" onclick="submitNote()">提交</button>
                </div>` : ''}
            </div>
        </div>`;
}

async function changeStatus(newStatus) {
    if (!state.currentUser) { alert('请先选择当前用户'); return; }
    const data = await CrmApi.updateStatus(state.currentTaskId, newStatus);
    if (data.success) openTask(state.currentTaskId);
}

async function deleteTask(taskId) {
    if (!confirm('确定删除该任务？此操作不可恢复。')) return;
    await CrmApi.deleteTask(taskId);
    showView('list');
    loadTasks();
}

async function submitNote() {
    const input = document.getElementById('note-input');
    const text = input.value.trim();
    if (!text) return;
    const btn = document.querySelector('.btn-note');
    btn.disabled = true;
    const data = await CrmApi.addNote(state.currentTaskId, text).catch(() => null);
    if (data?.success) {
        input.value = '';
        openTask(state.currentTaskId);
    }
    btn.disabled = false;
}

// ── View switching ─────────────────────────────────────────────────────────
function showView(v) {
    state.view = v;
    document.getElementById('view-list').classList.toggle('active', v === 'list');
    document.getElementById('view-detail').classList.toggle('active', v === 'detail');
}

// ── Init ───────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    // Restore user
    const sel = document.getElementById('user-select');
    if (state.currentUser) sel.value = state.currentUser;
    sel.addEventListener('change', () => {
        state.currentUser = sel.value;
        localStorage.setItem('crm_user', sel.value);
        loadTasks();
    });

    // Nav tabs
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            state.viewMode = tab.dataset.view;
            showView('list');
            loadTasks();
        });
    });

    // Stat cards — click to filter
    document.querySelectorAll('.stat-card').forEach(card => {
        card.addEventListener('click', () => {
            document.querySelectorAll('.stat-card').forEach(c => c.classList.remove('active'));
            card.classList.add('active');
            state.statusFilter = card.dataset.filter || '';
            document.getElementById('filter-status').value = state.statusFilter;
            loadTasks();
        });
    });

    // Status filter dropdown
    document.getElementById('filter-status').addEventListener('change', (e) => {
        state.statusFilter = e.target.value;
        loadTasks();
    });

    // Refresh button
    document.getElementById('btn-refresh').addEventListener('click', loadTasks);

    // Back button
    document.getElementById('btn-back').addEventListener('click', () => {
        showView('list');
        loadTasks();
    });

    // Initial load
    loadTasks();

    // Auto-refresh every 5 seconds (only when on list view)
    setInterval(() => {
        if (state.view === 'list') loadTasks();
    }, 5000);
});

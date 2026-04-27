/**
 * Help App — Frontend: Audio recording, API calls, UI rendering.
 */

// ========== Tab Switching ==========
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
        tab.classList.add('active');
        document.getElementById(`panel-${tab.dataset.tab}`).classList.add('active');
    });
});

// ========== Audio Recorder ==========
class AudioRecorder {
    constructor(opts = {}) {
        this.onStop = opts.onStop || (() => {});
        this.onError = opts.onError || (() => {});
        this.onTick = opts.onTick || (() => {});
        this.stream = null;
        this.mediaRecorder = null;
        this.chunks = [];
        this.startTime = null;
        this._timerInterval = null;
    }

    async start() {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            this.onError('录音需要 HTTPS 环境。请在手机浏览器中通过 HTTPS 访问，或使用 localhost。');
            return false;
        }
        try {
            this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        } catch (err) {
            if (err.name === 'NotAllowedError') {
                this.onError('请允许浏览器访问麦克风');
            } else if (err.name === 'NotFoundError') {
                this.onError('未检测到麦克风设备');
            } else {
                this.onError(`麦克风错误: ${err.message}`);
            }
            return false;
        }

        const mimeType = this._pickMimeType();
        this.mediaRecorder = new MediaRecorder(this.stream, mimeType ? { mimeType } : {});
        this.chunks = [];

        this.mediaRecorder.ondataavailable = e => {
            if (e.data.size > 0) this.chunks.push(e.data);
        };

        this.mediaRecorder.onstop = () => {
            clearInterval(this._timerInterval);
            this.stream.getTracks().forEach(t => t.stop());

            const ext = mimeType ? mimeType.split('/')[1].split(';')[0] : 'webm';
            const blob = new Blob(this.chunks, { type: mimeType || 'audio/webm' });
            this.onStop(blob, ext);
        };

        this.mediaRecorder.onerror = e => {
            this.onError(`录音错误: ${e.error?.message || '未知错误'}`);
        };

        this.mediaRecorder.start(1000);
        this.startTime = Date.now();
        this._timerInterval = setInterval(() => {
            this.onTick(this._elapsed());
        }, 200);

        return true;
    }

    stop() {
        if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
            this.mediaRecorder.stop();
        }
    }

    isRecording() {
        return this.mediaRecorder && this.mediaRecorder.state === 'recording';
    }

    _elapsed() {
        if (!this.startTime) return '00:00';
        const s = Math.floor((Date.now() - this.startTime) / 1000);
        return `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`;
    }

    _pickMimeType() {
        const types = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus', 'audio/ogg'];
        for (const t of types) {
            if (MediaRecorder.isTypeSupported(t)) return t;
        }
        return '';
    }
}

// ========== Image Handler ==========
class ImageHandler {
    constructor(previewContainerId, maxImages = 5) {
        this.previewEl = document.getElementById(previewContainerId);
        this.maxImages = maxImages;
        this.files = [];
        this._setupListeners();
    }

    _setupListeners() {
        const container = this.previewEl.parentElement;
        const fileInput = container.querySelector('input[type="file"]');
        fileInput.addEventListener('change', (e) => this._handleFiles(e.target.files));
    }

    _handleFiles(fileList) {
        for (const file of fileList) {
            if (this.files.length >= this.maxImages) {
                alert(`最多只能添加 ${this.maxImages} 张图片`);
                break;
            }
            if (!file.type.startsWith('image/')) continue;
            this.files.push(file);
            this._addPreview(file);
        }
    }

    _addPreview(file) {
        const reader = new FileReader();
        const wrapper = document.createElement('div');
        wrapper.className = 'preview-item';

        reader.onload = (e) => {
            wrapper.innerHTML = `
                <img src="${e.target.result}" alt="预览">
                <button class="preview-remove">&times;</button>
            `;
            wrapper.querySelector('.preview-remove').addEventListener('click', () => {
                const idx = this.files.indexOf(file);
                if (idx > -1) this.files.splice(idx, 1);
                wrapper.remove();
            });
        };
        reader.readAsDataURL(file);
        this.previewEl.appendChild(wrapper);
    }

    clear() {
        this.files = [];
        this.previewEl.innerHTML = '';
    }

    get hasImages() {
        return this.files.length > 0;
    }
}

// ========== API Client ==========
class HelpApi {
    static _log(api, data) {
        const time = new Date().toLocaleTimeString();
        console.log(`[${time}] ${api}`, data);
    }

    static async uploadAudio(blob, ext) {
        const fd = new FormData();
        fd.append('audio', blob, `recording.${ext}`);
        const res = await fetch('/api/upload-audio', { method: 'POST', body: fd });
        const data = await res.json();
        this._log('upload-audio', data);
        return data;
    }

    static async transcribe(blob, ext) {
        const fd = new FormData();
        fd.append('audio', blob, `recording.${ext}`);
        const res = await fetch('/api/transcribe', { method: 'POST', body: fd });
        const data = await res.json();
        this._log('transcribe', data);
        return data;
    }

    static async transcribeAndRoute(blob, ext, imageFiles = []) {
        const fd = new FormData();
        fd.append('audio', blob, `recording.${ext}`);
        for (const file of imageFiles) {
            fd.append('images', file);
        }
        const res = await fetch('/api/transcribe-and-route', { method: 'POST', body: fd });
        const data = await res.json();
        this._log('transcribe-and-route', data);
        return data;
    }

    static async routeText(text) {
        const res = await fetch('/api/route', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text }),
        });
        const data = await res.json();
        this._log('route', data);
        return data;
    }

    static async queueAudio(blob, ext) {
        const fd = new FormData();
        fd.append('audio', blob, `recording.${ext}`);
        const res = await fetch('/api/queue', { method: 'POST', body: fd });
        const data = await res.json();
        this._log('queue', data);
        return data;
    }

    static async getJobStatus(jobId) {
        const res = await fetch(`/api/queue/status/${jobId}`);
        const data = await res.json();
        this._log('queue-status', data);
        return data;
    }

    static async getHistory() {
        const res = await fetch('/api/history');
        return res.json();
    }
}

// ========== Helpers ==========
function esc(str) {
    return String(str || '').replace(/[&<>"']/g, c =>
        ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

// ========== Quick Task — Chat UI ==========
(function initQuickTask() {
    const btn      = document.getElementById('quick-record-btn');
    const timerSpan = document.getElementById('quick-timer');
    const chatEl   = document.getElementById('chat-messages');
    const imageHandler = new ImageHandler('quick-preview');

    let recorder = null;

    function getPreviewSrcs() {
        return [...document.querySelectorAll('#quick-preview .preview-item img')]
            .map(img => img.src);
    }

    function appendMsg(role, innerHtml) {
        const id = 'msg-' + Date.now() + '-' + (Math.random() * 1e4 | 0);
        const wrap = document.createElement('div');
        wrap.className = 'chat-msg ' + role;
        wrap.id = id;
        wrap.innerHTML = role === 'ai'
            ? `<div class="msg-avatar">VT</div><div class="msg-bubble">${innerHtml}</div>`
            : `<div class="msg-bubble">${innerHtml}</div>`;
        const welcome = chatEl.querySelector('.chat-welcome');
        if (welcome) welcome.remove();
        chatEl.appendChild(wrap);
        chatEl.scrollTop = chatEl.scrollHeight;
        return id;
    }

    function updateMsg(id, innerHtml) {
        const el = document.getElementById(id);
        if (el) {
            el.querySelector('.msg-bubble').innerHTML = innerHtml;
            chatEl.scrollTop = chatEl.scrollHeight;
        }
    }

    function buildUserBubble(text, imgSrcs) {
        const imgs = imgSrcs.length
            ? `<div class="msg-images">${imgSrcs.map(s => `<img class="msg-img" src="${s}">`).join('')}</div>`
            : '';
        return imgs + esc(text);
    }

    function buildRoutingBubble(data) {
        const r = data.routing || {};
        const p = r.priority || 'medium';
        const pText = {high:'高', medium:'中', low:'低'}[p] || p;
        const desc = r.task_description || data.transcription?.text?.slice(0, 50) || '-';
        if (!r.assignee && !r.department) return '已收到您的任务，正在处理中。';
        return `<div class="route-intro">好的，任务已分配：</div>
            <div class="route-row"><span class="lbl">任务</span><span class="val">${esc(desc)}</span></div>
            <div class="route-row"><span class="lbl">分配给</span><span class="val">${esc(r.assignee || '-')} · ${esc(r.department || '-')}</span></div>
            <div class="route-row"><span class="lbl">优先级</span><span class="val"><span class="priority-badge ${p}">${pText}</span></span></div>
            ${r.reason ? `<div class="route-row"><span class="lbl">理由</span><span class="val">${esc(r.reason)}</span></div>` : ''}`;
    }

    btn.addEventListener('click', async () => {
        if (recorder && recorder.isRecording()) {
            recorder.stop();
            return;
        }

        recorder = new AudioRecorder({
            onTick: t => { timerSpan.textContent = t; },
            onError: msg => {
                btn.classList.remove('recording');
                timerSpan.textContent = '点击录音';
                appendMsg('ai', `<span style="color:#e74c3c">${esc(msg)}</span>`);
            },
            onStop: async (blob, ext) => {
                btn.classList.remove('recording');
                timerSpan.textContent = '点击录音';

                const imgSrcs = getPreviewSrcs();
                const imgFiles = [...imageHandler.files];
                imageHandler.clear();

                // Show user bubble with images + placeholder, then AI loading
                const userId = appendMsg('user', buildUserBubble('转录中…', imgSrcs));
                const loadId = appendMsg('ai', '<div class="loading-dots"><span></span><span></span><span></span></div>');

                try {
                    const data = await HelpApi.transcribeAndRoute(blob, ext, imgFiles);
                    if (data.success) {
                        updateMsg(userId, buildUserBubble(data.transcription?.text || '(无内容)', imgSrcs));
                        updateMsg(loadId, buildRoutingBubble(data));
                    } else {
                        updateMsg(userId, buildUserBubble('处理失败', imgSrcs));
                        updateMsg(loadId, `<span style="color:#e74c3c">${esc(data.error || '处理失败')}</span>`);
                    }
                } catch (err) {
                    updateMsg(userId, buildUserBubble('网络错误', imgSrcs));
                    updateMsg(loadId, `<span style="color:#e74c3c">网络错误: ${esc(err.message)}</span>`);
                }
            },
        });

        const ok = await recorder.start();
        if (ok) {
            btn.classList.add('recording');
            timerSpan.textContent = '00:00';
        }
    });
})();

// ========== Long Transcription (Workflow B) ==========
(function initLongTranscription() {
    const recordBtn = document.getElementById('long-record-btn');
    const stopBtn = document.getElementById('long-stop-btn');
    const timer = document.getElementById('long-timer');
    const hint = document.getElementById('long-hint');
    const statusArea = document.getElementById('long-status');
    const resultArea = document.getElementById('long-result');

    let recorder = null;
    let pollTimer = null;

    recordBtn.addEventListener('click', async () => {
        recorder = new AudioRecorder({
            onTick: t => { timer.textContent = t; },
            onError: msg => {
                hint.textContent = msg;
                recordBtn.style.display = '';
                stopBtn.style.display = 'none';
                timer.classList.remove('recording');
            },
            onStop: async (blob, ext) => {
                recordBtn.style.display = '';
                stopBtn.style.display = 'none';
                timer.classList.remove('recording');
                hint.textContent = '上传中...';

                try {
                    const data = await HelpApi.queueAudio(blob, ext);
                    if (data.success) {
                        startPolling(data.job_id, statusArea, resultArea);
                    } else {
                        statusArea.style.display = 'block';
                        statusArea.innerHTML = `<div class="error-msg">${data.error || '上传失败'}</div>`;
                    }
                } catch (err) {
                    statusArea.style.display = 'block';
                    statusArea.innerHTML = `<div class="error-msg">网络错误: ${err.message}</div>`;
                }
                hint.textContent = '适用于会议、巡检等长时录音';
            },
        });

        const ok = await recorder.start();
        if (ok) {
            recordBtn.style.display = 'none';
            stopBtn.style.display = '';
            timer.classList.add('recording');
            timer.textContent = '00:00';
            hint.textContent = '录音中...点击停止按钮结束';
        }
    });

    stopBtn.addEventListener('click', () => {
        if (recorder) recorder.stop();
    });

    function startPolling(jobId, statusEl, resultEl) {
        if (pollTimer) clearInterval(pollTimer);
        statusEl.style.display = 'block';
        resultEl.style.display = 'none';

        const poll = async () => {
            try {
                const data = await HelpApi.getJobStatus(jobId);
                if (!data.success) return;
                const s = data.status;
                statusEl.innerHTML = `<span class="status-badge ${s}">${{queued:'排队中',processing:'处理中',completed:'已完成',failed:'失败'}[s] || s}</span>`;

                if (data.progress) {
                    statusEl.innerHTML += `<p style="margin-top:8px;font-size:13px;color:#666">${data.progress}</p>`;
                }

                if (s === 'completed') {
                    clearInterval(pollTimer);
                    resultEl.style.display = 'block';
                    resultEl.innerHTML = `<h3>转录结果</h3><div class="transcription-text">${data.result || '(无内容)'}</div>`;
                } else if (s === 'failed') {
                    clearInterval(pollTimer);
                    resultEl.style.display = 'block';
                    resultEl.innerHTML = `<div class="error-msg">${data.error || '处理失败'}</div>`;
                }
            } catch (err) {
                // keep polling on network hiccup
            }
        };

        poll();
        pollTimer = setInterval(poll, 3000);
    }
})();


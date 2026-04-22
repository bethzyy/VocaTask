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

    static async transcribeAndRoute(blob, ext) {
        const fd = new FormData();
        fd.append('audio', blob, `recording.${ext}`);
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

// ========== Quick Task (Workflow A) ==========
(function initQuickTask() {
    const btn = document.getElementById('quick-record-btn');
    const timer = document.getElementById('quick-timer');
    const hint = document.getElementById('quick-hint');
    const resultArea = document.getElementById('quick-result');

    let recorder = null;

    btn.addEventListener('click', async () => {
        if (recorder && recorder.isRecording()) {
            recorder.stop();
            return;
        }

        recorder = new AudioRecorder({
            onTick: t => { timer.textContent = t; },
            onError: msg => {
                hint.textContent = msg;
                btn.classList.remove('recording');
                timer.classList.remove('recording');
            },
            onStop: async (blob, ext) => {
                btn.classList.remove('recording');
                timer.classList.remove('recording');
                hint.textContent = '处理中...';
                resultArea.style.display = 'block';
                resultArea.innerHTML = '<div class="loading"><span class="spinner"></span>正在转录并路由...</div>';

                try {
                    const data = await HelpApi.transcribeAndRoute(blob, ext);
                    renderQuickResult(data, resultArea);
                } catch (err) {
                    resultArea.innerHTML = `<div class="error-msg">网络错误: ${err.message}</div>`;
                }
                hint.textContent = '点击按钮开始录音';
            },
        });

        const ok = await recorder.start();
        if (ok) {
            btn.classList.add('recording');
            timer.classList.add('recording');
            timer.textContent = '00:00';
            hint.textContent = '再次点击停止录音';
            resultArea.style.display = 'none';
        }
    });
})();

function renderQuickResult(data, container) {
    if (!data.success) {
        container.innerHTML = `<div class="error-msg">${data.error || '处理失败'}</div>`;
        return;
    }

    const t = data.transcription || {};
    const r = data.routing || {};

    let html = '<h3>转录结果</h3>';
    html += `<div class="transcription-text">${t.text || '(无内容)'}</div>`;

    if (r.assignee || r.department) {
        const pClass = r.priority || 'medium';
        html += `<div class="routing-card priority-${pClass}">`;
        html += `<div class="row"><span class="label">任务：</span><span class="value">${r.task_description || ''}</span></div>`;
        html += `<div class="row"><span class="label">分配给：</span><span class="value">${r.assignee || '-'}</span></div>`;
        html += `<div class="row"><span class="label">部门：</span><span class="value">${r.department || '-'}</span></div>`;
        html += `<div class="row"><span class="label">优先级：</span><span class="priority-badge ${pClass}">${{high:'高',medium:'中',low:'低'}[pClass] || pClass}</span></div>`;
        if (r.reason) html += `<div class="row"><span class="label">理由：</span><span class="value">${r.reason}</span></div>`;
        html += '</div>';
    }

    container.innerHTML = html;
}

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

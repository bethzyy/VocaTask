# VocaTask 技术验证可行性论证报告

> 三人攻坚技术专家团队论证 | 2026-04-26
> 基于 `timeline.md` Section 3.6 技术验证清单（19 项）
> 所有工作量估算基于 Claude Code 辅助开发

---

## 结论总览

| 结论 | 数量 | 验证点 |
|------|------|--------|
| ✅ 必然通过 | 4 | A1, A2, M5, E4 |
| ⚠️ 需要调整 | 12 | V1, V2, V3, A3, M2, M4, S1, S2, S3, E1, E2, E3 |
| ❌ 可能不通过 | 3 | V4, M3, (M2 iOS 纯 Web) |

> **核心判断**：19 项验证中 4 项已确认可行，12 项通过明确的代码调整可解决，3 项需要架构级决策。**没有任何一项存在根本性的技术不可能**。项目在技术上完全可行，关键在于实施顺序和资源分配。

---

## 一、语音处理链路

### V1: ASR 工业噪声识别准确率 — ⚠️ 需要调整

**当前状态**：GLM-ASR-2512 在安静环境下表现良好，但 SNR < 5dB 工业场景下 WER 可能飙至 25-40%。`asr.py` 的 `_convert_to_wav()` 仅做格式转换，**没有任何前端降噪**。

**实施方案**：

1. **ffmpeg 滤波链降噪**（最小改动，30 分钟）
   - 修改 `asr.py` 第 154-158 行的 ffmpeg 命令：
   ```
   -af "highpass=f=80,lowpass=f=8000,afftdn=nf=-25"
   ```
   - 去除工业低频噪声（风机、压缩机）和高频噪声（金属碰撞）

2. **高精度备选 ASR**（如果 GLM-ASR 不达标，2-3 小时）
   - [FunASR Paraformer-large](https://github.com/modelscope/FunASR) — 阿里达摩院开源中文 ASR，Paraformer-large 在工业场景 WER < 8%
   - 可作为本地部署的高精度备选通道
   - 安装：`pip install funasr modelscope`

**通过标准**：关键信息准确率 ≥ 90%，WER ≤ 15%

**工作量**：ffmpeg 降噪 30 分钟 | FunASR 备选 2-3 小时

---

### V2: iOS Safari 录音 → ASR 全链路 — ⚠️ 需要调整

**问题定位**：`app.js` 第 92-98 行 `_pickMimeType()` 的四个候选格式（webm/ogg）**iOS Safari 全部不支持**。Safari 会 fallback 到 MP4/AAC，但第 58 行 `ext` 硬编码从 mimeType 推导，导致扩展名不匹配。

**实施方案**：

1. **修改 `_pickMimeType()` + 扩展名映射**（30-60 分钟）
   ```javascript
   _pickMimeType() {
       const types = [
           'audio/webm;codecs=opus', 'audio/webm',
           'audio/ogg;codecs=opus', 'audio/ogg',
           'audio/mp4',  // iOS Safari fallback
       ];
       for (const t of types) {
           if (MediaRecorder.isTypeSupported(t)) return t;
       }
       return '';
   }
   ```
   同时修改 `onStop` 中 ext 的推导逻辑，根据实际 MIME 映射正确扩展名（`mp4` → `m4a`）。

2. **备选方案：[RecordRTC](https://github.com/muaz-khan/RecordRTC)**（2 小时）
   - RecordRTC 统一处理跨浏览器录音格式，自动选择最佳编码器
   - CDN 引入即可，无需构建工具

**通过标准**：iOS 录音 → ffmpeg 转 WAV → ASR 成功

**工作量**：MIME 修复 30-60 分钟 | RecordRTC 替换 2 小时

---

### V3: 90 分钟长篇转录 — ⚠️ 需要调整

**当前问题**：90 分钟 = 216 个 25 秒分片。串行 ASR 约 7-25 分钟，时间上可通过。核心问题是**固定 25 秒切割会在句子中间断开**，降低每片识别率。

**实施方案**：

1. **Silero VAD 智能分片**（推荐，3-4 小时）
   - [Silero VAD](https://github.com/snakers4/silero-vad) — 轻量语音活动检测，ONNX 推理，CPU 即可运行
   - 在静音处切割而非固定时长，保留语义完整性
   - 替换 `asr.py` 第 170-196 行的 `_segment_audio()` 方法
   ```python
   # 使用 Silero VAD 在静音处分段
   # 每 10-30 秒的语义段独立转录
   ```

2. **增加 API 速率保护**（30 分钟）
   - 每 500ms 一次 ASR 调用，防止触发 ZhipuAI QPS 限制
   - 在 `asr.py` 第 86 行循环中添加 `time.sleep(0.5)`

3. **增加 ffmpeg 分片超时**（15 分钟）
   - `asr.py` 第 187 行 `timeout=120` 对大文件可能不够
   - 改为动态超时：`timeout = max(120, file_size_mb * 3)`

**通过标准**：30 分钟内完成，无崩溃无丢片

**工作量**：VAD 智能分片 3-4 小时 | 速率保护 + 超时调整 45 分钟

---

### V4: 中文说话人分离 — ❌ 可能不通过

**当前状态**：完全未实现。GLM-ASR-2512 仅输出单说话人文本。

**技术方案评估**：

| 方案 | 中文 DER | GPU 需求 | 成本 | 可行性 |
|------|---------|---------|------|--------|
| [pyannote-audio 3.x](https://github.com/pyannote/pyannote-audio) | ~20-25% | 必须（4GB+） | 免费 + HuggingFace token | ⚠️ 无 GPU 则不可行 |
| [FunASR SOND](https://github.com/modelscope/FunASR) | ~15-20% | 推荐 | 免费 | ⚠️ 中文优化但需调优 |
| [讯飞说话人分离 API](https://www.xfyun.cn/doc/asr/lfasr/API.html) | <15% | 不需要 | ~0.03 元/分钟 | ✅ 推荐 |
| [阿里云智能语音](https://help.aliyun.com/product/30413.html) | <15% | 不需要 | ~0.02 元/分钟 | ✅ 推荐 |

**推荐方案**：

1. **短期**（MVP）：不做说话人分离，单人场景已经满足核心业务
2. **中期**（有需求时）：接入讯飞/阿里云商业 API，2-3 天可集成
3. **长期**（自部署）：FunASR SOND + GPU 服务器

**关键决策**：requirements.md 要求了说话人分离，但工厂上报场景是单人。建议与客户确认是否为 PoC 验收的硬性要求。

**工作量**：商业 API 集成 2-3 天 | 开源自部署 1-2 周

---

## 二、AI 模型能力

### A1: GLM-4-flash 路由准确率 — ✅ 必然通过

**理由**：`router.py` 设计完备——`tool_choice` 强制 function calling + 详细人名检测 prompt + 30 个别名匹配 + keyword fallback 双保险 + `_ensure_fields()` 兜底。5 部门 10 人职责清晰，估计准确率 85-90%+。

**验证方法**：构造 50 条测试用例，覆盖人名直呼、部门暗示、跨部门、安全紧急、含图片场景。

**如果准确率不达标**：`config.py` 改 `ROUTING_MODEL = "glm-4"` 升级到非 flash 模型。

**工作量**：构造测试集 1-2 小时

---

### A2: 函数调用 JSON 稳定性 — ✅ 必然通过

**理由**：三层防护已到位：
1. `tool_choice={"type": "function", "function": {"name": "route_task"}}` 强制调用
2. `json.loads()` + `JSONDecodeError` 处理 → 降级到 `keyword_route`
3. `_ensure_fields()` 兜底补全所有必填字段

`temperature=0.1` + `max_tokens=500` 进一步降低输出随机性和截断风险。100 次连续调用测试预计成功率 > 99%。

**工作量**：验证测试 30 分钟

---

### A3: Vision 模型图片描述质量 — ⚠️ 需要调整

**当前状态**：`vision.py` 使用 GLM-4V-Flash，Prompt 设计精良，但对工业细节（仪表读数、细小裂纹、远处铭牌）识别率可能不足。

**实施方案**：

1. **升级视觉模型**（最快速，5 分钟）
   - `config.py` 改 `VISION_MODEL = "glm-4v-plus"`
   - GLM-4V-Plus 细节识别能力显著提升

2. **图片预处理增强**（2 小时）
   - 使用 Pillow 调整尺寸、增强对比度、锐化
   - 对暗光照片自动提亮

3. **文字 OCR 辅助**（如果图片含文字，3-4 小时）
   - [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) — 百度开源 OCR，中英文识别能力强
   - 提取铭牌、仪表盘上的文字信息，补充 Vision 描述
   - 安装：`pip install paddleocr paddlepaddle`

**工作量**：模型升级 5 分钟 | 预处理 2 小时 | PaddleOCR 集成 3-4 小时

---

## 三、移动端兼容性

### M2: iOS Safari HTTPS + 麦克风 — ⚠️ 需要调整

**问题**：iOS Safari 不信任自签证书，`getUserMedia` 在非受信 HTTPS 下直接拒绝。

**实施方案（三选一）**：

| 方案 | 适用场景 | 工作量 |
|------|---------|--------|
| **Cloudflare Tunnel** | PoC 演示、开发测试 | 30 分钟 |
| **Let's Encrypt + 域名** | 生产部署 | 1-2 小时 |
| **mkcert 本地证书** | 仅开发调试 | 30 分钟 |

**推荐方案：Cloudflare Tunnel**（PoC 阶段最快）

1. 安装：`winget install Cloudflare.cloudflared`
2. 运行：`cloudflared tunnel --url http://localhost:8010`
3. 手机访问分配的 `*.trycloudflare.com` HTTPS URL
4. iOS Safari 完全信任 Cloudflare 证书

生产阶段切换为 Let's Encrypt + [Certbot](https://github.com/certbot/certbot) 自动续期。

**关键文件**：
- [cloudflared](https://github.com/cloudflare/cloudflared) — Cloudflare Tunnel 客户端
- [Certbot](https://github.com/certbot/certbot) — Let's Encrypt 证书管理
- [mkcert](https://github.com/FiloSottile/mkcert) — 本地开发证书

---

### M3: 后台/锁屏录音 — ❌ 纯 Web 不可行

**结论**：iOS Safari 切后台后 JS 1-5 秒内被挂起，MediaRecorder 无法继续。**这是操作系统级别的限制，无法绕过。**

**唯一可行方案：Capacitor + 原生插件**

1. 初始化 Capacitor 项目（见 M5）
2. iOS 端配置 `Info.plist`：
   ```xml
   <key>UIBackgroundModes</key>
   <array><string>audio</string></array>
   ```
3. Android 端创建 Foreground Service（前台通知 + 录音）

**开源工具**：
- [capacitor-background-mode](https://github.com/nickvdp/capacitor-background-mode) — Capacitor 后台运行

**风险**：App Store 审核要求后台录音时显示可见的录音指示器。

**工作量**：1-2 天（需原生代码）

**决策建议**：如果 90 分钟长篇录音是硬性需求，必须走 Capacitor 原生路线。如果可以接受"录音时保持屏幕常亮"，Web 方案 + [Wake Lock API](https://developer.mozilla.org/en-US/docs/Web/API/Screen_Wake_Lock_API) 即可。

---

### M4: 弱网上传可靠性 — ⚠️ 需要调整

**当前问题**：`app.js` 第 189 行裸 `fetch` 调用，无重试、无超时控制、无断点续传。

**实施方案（三个层次，按需选择）**：

1. **最小方案：重试封装**（1-2 小时）
   ```javascript
   static async fetchWithRetry(url, options, maxRetries = 3) {
       for (let attempt = 1; attempt <= maxRetries; attempt++) {
           const controller = new AbortController();
           const timeout = setTimeout(() => controller.abort(), 120000);
           try {
               const res = await fetch(url, { ...options, signal: controller.signal });
               clearTimeout(timeout);
               return await res.json();
           } catch (err) {
               if (attempt === maxRetries) throw err;
               await new Promise(r => setTimeout(r, 1000 * Math.pow(2, attempt)));
           }
       }
   }
   ```

2. **中等方案：分片上传**（半天）
   - 前端 2MB 分片 + 后端合并
   - 需新增 `/api/upload-chunk` 和 `/api/merge-chunks` 路由

3. **完整方案：[tus 协议](https://tus.io/)**（1-2 天）
   - [tus-js-client](https://github.com/tus/tus-js-client) — 前端断点续传
   - [tusd](https://github.com/tus/tusd) — Go 语言 tus 服务端
   - 支持跨设备断点续传、网络切换自动恢复

**推荐**：先用最小方案（重试），实测不够再升级到分片。

---

### M5: Capacitor 包装可行性 — ✅ 必然通过

**理由**：当前 `web/` 目录是纯静态 HTML + JS + CSS，无构建工具、无 SPA 路由，API 调用使用相对路径——**完美适配 Capacitor WebView**。

**实施步骤**：

1. 初始化：`npm init -y && npm install @capacitor/core @capacitor/cli @capacitor/android @capacitor/ios`
2. 配置：`npx cap init VocaTask com.vocatask.app --web-dir=web`
3. **唯一代码改动** — API 基础 URL（app.js + crm.js 各约 5 行）：
   ```javascript
   const API_BASE = window.Capacitor ? 'https://vocatask.example.com' : '';
   ```
4. 权限配置（Info.plist + AndroidManifest.xml）
5. 构建：`npx cap sync && npx cap open android`

**开源工具**：
- [Capacitor](https://github.com/ionic-team/capacitor) — Web → 原生 App 包装

**注意**：
- `capacitor.config.ts` 中必须设置 `androidScheme: 'https'`，否则 WebView 内 `getUserMedia` 被拒绝
- iOS App Store 审核对 WebView 应用较严格，需有足够原生功能（推送、后台录音等）

**工作量**：3-4 小时

---

## 四、并发与稳定性

### S1: SQLite 10+ 并发写入 — ⚠️ 需要调整

**当前问题**：`_conn()` 没有设置 `busy_timeout`，默认为 0，遇到锁立即抛 `database is locked`。

**实施方案**（1.5-2 小时）：

修改 `storage.py` 和 `crm_storage.py` 的 `_conn()` 方法：

```python
@contextmanager
def _conn(self):
    conn = sqlite3.connect(self.db_path, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")     # 30s 等待锁
    conn.execute("PRAGMA synchronous=NORMAL")     # WAL 下足够安全
    conn.execute("PRAGMA cache_size=-64000")       # 64MB 缓存
    conn.execute("PRAGMA temp_store=MEMORY")       # 临时表在内存
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
```

**压力测试**：20 并行 POST 请求到 `/api/transcribe-and-route`，验证全部成功。

**如果 20 并发仍失败**：迁移 PostgreSQL（见 E3）。

**参考**：[SQLite WAL 模式文档](https://www.sqlite.org/wal.html)

---

### S2: 24 小时持续运行 — ⚠️ 需要调整

**当前问题**：`debug=True` 启动 Flask（安全风险 + reloader 不稳定），ZhipuAI SDK 长连接可能泄漏。

**实施方案**：

1. **生产模式启动**（30 分钟）
   - `debug=False`，或通过环境变量控制：`FLASK_DEBUG=0 python server.py`
   - 添加 `/api/health` 端点返回内存、线程数、运行时间

2. **Gunicorn + Supervisor**（2-3 小时）
   - [Gunicorn](https://github.com/benoitc/gunicorn) — 生产级 WSGI 服务器
   - [Supervisor](https://github.com/Supervisor/supervisor) — 进程守护，自动重启
   ```bash
   pip install gunicorn
   gunicorn wsgi:application --bind 0.0.0.0:8010 --workers 2 --threads 4 --timeout 120
   ```

3. **内存监控**（1 小时）
   - [psutil](https://github.com/giampaolo/psutil) — 进程资源监控
   - health 端点返回 `memory_mb`、`threads`、`open_files`

**注意**：Gunicorn 多 worker 下 `TranscriptionQueue` 后台线程会重复启动，需用文件锁或独立进程控制。

---

### S3: 大文件上传（50MB） — ⚠️ 需要调整

**实施方案**（2-3 小时）：

1. **动态 ffmpeg 超时**：根据文件大小计算，每 MB 给 5 秒
2. **大文件自动走长篇转录路径**：>20MB 的文件自动调用 `transcribe_long`
3. **Nginx 配置**（如有）：`client_max_body_size 100m` + `proxy_read_timeout 300s`

**参考**：[ffmpeg-python](https://github.com/kkroening/ffmpeg-python) — 更好的进度回调

---

## 五、外部依赖

### E1: 智谱 API 限流 — ⚠️ 需要调整

**当前状态**：`asr.py` 指数退避（1s/2s/3s）合理，但**没有专门处理 429 (Too Many Requests)**。`ai_router.py` **完全没有重试**。

**实施方案**（30 分钟）：

1. 区分 429 错误，使用更长退避（5s/15s/45s）
2. 用 [tenacity](https://github.com/jd/tenacity) 统一替换手写退避：
   ```python
   from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
   
   @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=30))
   def _call_asr(self, audio_path):
       ...
   ```

**智谱限流参考**：GLM-4-Flash 免费层 ~300 RPM，VocaTask 峰值 10 并发约 30 RPM，远低于限制。具体数字需在 [智谱控制台](https://open.bigmodel.cn/usage) 确认。

---

### E2: 智谱 Anthropic 兼容接口 — ⚠️ 需要调整

**当前问题**：项目存在两条 AI 调用路径：
- `router.py` + `vision.py` → `zhipuai` 原生 SDK
- `ai_router.py` → `anthropic.Anthropic(base_url="...")` 兼容接口

兼容接口是智谱的"次要接口"，稳定性承诺不如原生接口。

**推荐方案**：将 `ai_router.py` 改为 `zhipuai` 原生 SDK（与 `router.py` 一致），消除兼容层不确定性。

**工作量**：20 分钟（约 15 行代码改动）

---

### E3: PostgreSQL 迁移 — ⚠️ 需要调整

**需修改的 SQL 方言差异**：

| 差异 | SQLite | PostgreSQL | 影响位置 |
|------|--------|-----------|---------|
| 参数占位符 | `?` | `%s` | 全部 26 条 SQL |
| WAL PRAGMA | `PRAGMA journal_mode=WAL` | 删除 | storage.py, crm_storage.py |
| 自增列 | `AUTOINCREMENT` | `SERIAL` | CREATE TABLE |
| 错误类型 | `sqlite3.OperationalError` | `psycopg2.errors.*` | 异常处理 |
| INSERT 返回 ID | `cursor.lastrowid` | `RETURNING id` | INSERT 语句 |

**推荐方案**：使用 [SQLAlchemy ORM](https://www.sqlalchemy.org/) 作为抽象层，一套代码兼容 SQLite（开发）和 PostgreSQL（生产）。

**替代方案**：
- [Turso](https://turso.tech/) — SQLite 兼容云数据库，无需改 SQL
- [Litestream](https://litestream.io/) — SQLite 实时备份到 S3

**工作量**：SQLAlchemy ORM 迁移 3-4 小时 | 直接改 SQL 2-3 小时

---

### E4: Cloudflare Tunnel PoC 演示 — ✅ 必然通过

**操作步骤**（30 分钟）：

1. 安装：`winget install Cloudflare.cloudflared`
2. 两个终端分别运行：
   ```bash
   cloudflared tunnel --url http://localhost:8010  # 主服务
   cloudflared tunnel --url http://localhost:8011  # CRM
   ```
3. 手机访问分配的 `*.trycloudflare.com` HTTPS URL
4. 去掉 `server.py` 中的 `ssl_context="adhoc"`（Cloudflare 负责 TLS）

**参考**：[cloudflared](https://github.com/cloudflare/cloudflared)

---

## 六、额外项：多 ASR 供应商

由于智谱 ASR 是单点故障（ASR + 路由 + 视觉三层全绑智谱），需要备用 ASR 方案。

**推荐：腾讯云 ASR 作为主备选**

| 供应商 | 价格 | 免费额度 | 中文效果 | SDK 成熟度 |
|--------|------|---------|---------|-----------|
| 智谱 GLM-ASR-2512（当前） | 按量 | 有 | ★★★★ | ★★★☆ |
| [腾讯云 ASR](https://cloud.tencent.com/product/asr) | 0.006 元/次 | 10h/月 | ★★★★★ | ★★★★★ |
| [讯飞 ASR](https://www.xfyun.cn/doc/asr/lfasr/API.html) | 0.003 元/次 | 5h/月 | ★★★★★ | ★★★★★ |
| [阿里云 ASR](https://help.aliyun.com/product/30413.html) | 0.008 元/次 | 2h/月 | ★★★★☆ | ★★★★★ |

**开源替代**：[faster-whisper](https://github.com/SYSTRAN/faster-whisper) — 完全离线运行，消除供应商依赖，但需要 GPU。

**推荐架构**：ASR 供应商抽象层（工厂模式），`config.py` 增加 `ASR_PROVIDER` 环境变量，运行时切换。

**工作量**：2-3 小时

---

## 七、集成架构建议

### 推荐的生产级架构

```
┌──────────────────────────────────────────────────┐
│  Nginx (TLS termination + reverse proxy)         │
│  ├─ :443 → vocatask.example.com → Flask :8010    │
│  └─ :443 → crm.vocatask.example.com → Flask :8011│
└──────────────────────────────────────────────────┘
                        │
┌───────────────────────┴──────────────────────────┐
│  Flask (Gunicorn, debug=False)                    │
│  ├─ server.py  (8010) — 主服务                     │
│  │   ├─ ASR: ZhipuAI (主) + 腾讯云 (备)            │
│  │   ├─ Router: GLM-4-flash (zhipuai 原生 SDK)    │
│  │   └─ Vision: GLM-4V-Plus                       │
│  └─ crm_server.py (8011) — CRM                    │
│       └─ 共享 PostgreSQL 数据库                    │
└──────────────────────────────────────────────────┘
                        │
┌───────────────────────┴──────────────────────────┐
│  PostgreSQL (生产) / SQLite WAL (开发)             │
│  SQLAlchemy ORM — 同一套代码                       │
└──────────────────────────────────────────────────┘
```

### 关键架构决策

| 决策 | 推荐 | 理由 |
|------|------|------|
| AI 调用统一 | `zhipuai` 原生 SDK | 消除 Anthropic 兼容层不确定性 |
| 数据库 | SQLAlchemy ORM | 一套代码兼容 SQLite + PostgreSQL |
| 进程管理 | Gunicorn + Supervisor | 生产级稳定性，自动重启 |
| ASR 备用 | 腾讯云 ASR | 价格最低，SDK 成熟，消除单点故障 |
| 客户端 | Capacitor（如需 APP） | 复用现有前端，3-4 小时完成 |

### 实施路线（按优先级）

**Phase 0 — 快速验证（1-2 天）**
- V2: iOS MIME 修复（30 分钟）
- S1: SQLite busy_timeout（1.5 小时）
- E4: Cloudflare Tunnel 演示（30 分钟）
- A1: 路由准确率测试集（1-2 小时）

**Phase 1 — 服务端加固（2-3 天）**
- V1: ffmpeg 降噪（30 分钟）
- E1: API 重试逻辑（30 分钟）
- E2: 统一到原生 SDK（20 分钟）
- S2: Gunicorn + Supervisor（2-3 小时）
- S3: 大文件超时（2-3 小时）

**Phase 2 — 移动端完善（2-3 天）**
- M2: iOS HTTPS（Cloudflare Tunnel / Let's Encrypt）
- M5: Capacitor 打包（3-4 小时）
- M4: 弱网重试（1-2 小时）

**Phase 3 — 高级功能（按需）**
- V3: Silero VAD 智能分片（3-4 小时）
- A3: Vision 模型升级（5 分钟）
- E3: PostgreSQL 迁移（3-4 小时）
- V4: 说话人分离（如客户需要，2-3 天）
- M3: 后台录音（如需长篇录制，1-2 天）

**总工作量**：Claude Code 辅助下约 **5-8 个工作日**完成全部验证和架构改造。

---

## 附录：关键开源项目索引

| 项目 | URL | 用途 | 验证点 |
|------|-----|------|--------|
| FunASR | https://github.com/modelscope/FunASR | 高精度中文 ASR + 说话人分离 | V1, V4 |
| Silero VAD | https://github.com/snakers4/silero-vad | 语音活动检测，智能分片 | V3 |
| RecordRTC | https://github.com/muaz-khan/RecordRTC | 跨浏览器录音统一库 | V2 |
| PaddleOCR | https://github.com/PaddlePaddle/PaddleOCR | 中英文 OCR | A3 |
| pyannote-audio | https://github.com/pyannote/pyannote-audio | 说话人分离（需 GPU） | V4 |
| Capacitor | https://github.com/ionic-team/capacitor | Web → 原生 App | M5, M3 |
| cloudflared | https://github.com/cloudflare/cloudflared | Cloudflare Tunnel | E4, M2 |
| Certbot | https://github.com/certbot/certbot | Let's Encrypt 证书 | M2 |
| mkcert | https://github.com/FiloSottile/mkcert | 本地开发证书 | M2 |
| Gunicorn | https://github.com/benoitc/gunicorn | 生产级 WSGI 服务器 | S2 |
| Supervisor | https://github.com/Supervisor/supervisor | 进程守护 | S2 |
| psutil | https://github.com/giampaolo/psutil | 进程资源监控 | S2 |
| tenacity | https://github.com/jd/tenacity | Python 重试库 | E1 |
| SQLAlchemy | https://www.sqlalchemy.org/ | ORM（SQLite/PG 双模式） | E3 |
| faster-whisper | https://github.com/SYSTRAN/faster-whisper | 离线 ASR（需 GPU） | 多 ASR |
| tus-js-client | https://github.com/tus/tus-js-client | 前端断点续传上传 | M4 |
| ffmpeg-python | https://github.com/kkroening/ffmpeg-python | Python ffmpeg 包装 | V1, S3 |

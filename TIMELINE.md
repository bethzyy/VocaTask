# VocaTask — Timeline Estimate

> All estimates based on AI-assisted development (Claude Code).

---

## Current Status

| Module | Status |
|--------|--------|
| Voice recording + upload | Done |
| ASR transcription (ZhipuAI GLM-ASR-2512) | Done |
| Task routing (GLM-4-flash function calling + keyword fallback) | Done |
| Long-form transcription queue (background worker + ffmpeg segmentation) | Done |
| Browser UI (recording, results display, status polling) | Done |
| Mock org data (10 people, 5 departments, hardcoded) | Done |

---

## PoC Timeline: Already Functional / Minor Polish: 2-4 Hours

The core task delegation pipeline is already working. Only minor polish needed before demo.

| Task | Time |
|------|------|
| Save routed tasks to a simple list (in-memory or SQLite, no full CRM) | 1h |
| Add task history view in UI (list of past routed tasks) | 1h |
| Test with real voice input in browser, fix any issues | 1-2h |

### PoC Deliverables

- Working web app: record voice → AI transcribes → routes to person/department → shows result
- Long-form recording → queued → transcribed → stored
- Task history: list of all routed tasks from this session
- Mock org data sufficient for demo purposes

### What's NOT in PoC (deferred to later)

- CRM management UI (departments/people CRUD)
- User authentication
- Database migration (SQLite → PostgreSQL)
- Notifications
- Photo attachments

### How Task Delegation Works

The system uses an employee list with responsibilities to match tasks to the right person:

1. **Employee list** defined in `core/org_structure.py` — each person has name, department, title, and responsibilities
2. **Voice input** → ASR transcribes → text sent to GLM-4-flash
3. **AI routing** — GLM receives the org structure as context, uses function calling to pick the best assignee based on task content and employee responsibilities
4. **Fallback** — if AI unavailable, keyword matching against responsibilities (e.g. "设备" → equipment department)
5. **Result** — task description + assigned person + department + priority + reason displayed in UI

**To customize for client**: replace the mock data in `core/org_structure.py` with real employee names and responsibilities. No code changes needed, just data.

---

## Production Timeline: 2-3 Weeks

Build a reliable, deployable system. CRM integration added as a separate phase after core delegation is solid.

### Week 1: Hardening + Deploy / 第1周：加固 + 部署

| Task | Time |
|------|------|
| Replace hardcoded org data with SQLite tables + simple seed | 1 day |
| Long-form audio: robust chunked upload with retry/resume | 1 day |
| Audio format compatibility (WAV, MP3, M4A, WebM) | 1 day |
| Error handling: graceful degradation, clear error messages in Chinese | 1 day |
| Cloud server setup + nginx reverse proxy + deploy | 1 day |

### Week 2: Task Lifecycle + Notifications / 第2周：任务生命周期 + 通知

| Task | Time |
|------|------|
| Task lifecycle: pending → assigned → in_progress → completed → archived | 1 day |
| User authentication (login, sessions) | 1 day |
| Task assignment notifications (email or push) | 1 day |
| Task dashboard: filters, status tracking | 1 day |
| Transcript review/approval UI (for long-form) | 1 day |

### Week 3 (if needed): CRM Integration + Polish / 第3周（如需）：CRM 集成 + 打磨

| Task | Time |
|------|------|
| Migrate SQLite → PostgreSQL | 1 day |
| CRM integration or lightweight CRM build | 2-3 days |
| Photo attachment support | 1 day |

### Production Deliverables

- Deployed on cloud server
- Voice task delegation → AI routing → task saved and tracked
- User login and task ownership
- Task lifecycle with notifications
- Long-form transcription with real-time progress
- CRM integration (or built-in lightweight CRM)

---

## Summary

| Phase | Time | What You Get |
|-------|------|-------------|
| **PoC** | Done + 2-4h polish | Voice → route → result, working demo |
| **Production** | 2-3 weeks | Deployed system, auth, notifications, CRM |

---

---

# VocaTask — 时间评估

> 所有时间估算基于 AI 辅助开发（Claude Code）。

---

## 当前进度

| 模块 | 状态 |
|------|------|
| 语音录制 + 上传 | 已完成 |
| ASR 转录（智谱 GLM-ASR-2512） | 已完成 |
| 任务路由（GLM-4-flash 函数调用 + 关键词 fallback） | 已完成 |
| 长篇转录队列（后台 Worker + ffmpeg 分片） | 已完成 |
| 浏览器 UI（录音、结果展示、状态轮询） | 已完成 |
| 模拟组织数据（10 人、5 部门，硬编码） | 已完成 |

---

## PoC 时间：功能已完成 / 微调打磨：2-4 小时

任务委派核心流程已经跑通，只需微调即可用于演示。

| 任务 | 时间 |
|------|------|
| 将路由结果保存为简单列表（内存或 SQLite，不做完整 CRM） | 1h |
| 添加任务历史记录界面（展示过去路由过的任务） | 1h |
| 用真实语音输入测试，修复问题 | 1-2h |

### PoC 交付物

- 可运行的 Web 应用：录音 → AI 转录 → 路由到人员/部门 → 展示结果
- 长篇录音 → 排队 → 转录 → 存储
- 任务历史：当前会话所有路由任务的列表
- 模拟组织数据足够演示使用

### PoC 不包含（后续再做）

- CRM 管理界面（部门/人员增删改查）
- 用户认证
- 数据库迁移（SQLite → PostgreSQL）
- 通知推送
- 照片附件

### 任务委派逻辑

系统通过员工及其职责列表来智能匹配任务：

1. **员工列表** 定义在 `core/org_structure.py` — 每人有姓名、部门、职位、职责范围
2. **语音输入** → ASR 转录 → 文本发送给 GLM-4-flash
3. **AI 路由** — GLM 接收组织架构作为上下文，通过函数调用根据任务内容和员工职责选择最合适的委派人
4. **Fallback** — AI 不可用时，按职责关键词匹配（如"设备"→设备部门）
5. **结果** — 任务描述 + 委派人 + 部门 + 优先级 + 理由，展示在界面

**为客户定制**：将 `core/org_structure.py` 中的模拟数据替换为真实员工姓名和职责即可，无需改代码，只改数据。

---

## 生产版时间：2-3 周

搭建可靠、可部署的系统。CRM 集成作为核心委派功能稳定后的独立阶段。

### 第1周：加固 + 部署

| 任务 | 时间 |
|------|------|
| 将硬编码组织数据替换为 SQLite 表 + 简单初始化 | 1 天 |
| 长篇音频：分块上传 + 断点续传 + 重试 | 1 天 |
| 音频格式兼容（WAV、MP3、M4A、WebM） | 1 天 |
| 错误处理：优雅降级、中文错误提示 | 1 天 |
| 云服务器搭建 + nginx 反向代理 + 部署 | 1 天 |

### 第2周：任务生命周期 + 通知

| 任务 | 时间 |
|------|------|
| 任务生命周期：pending → assigned → in_progress → completed → archived | 1 天 |
| 用户认证（登录、会话） | 1 天 |
| 任务分配通知（邮件或推送） | 1 天 |
| 任务看板：筛选、状态追踪 | 1 天 |
| 转录审核/确认界面（长篇转录） | 1 天 |

### 第3周（如需）：CRM 集成 + 打磨

| 任务 | 时间 |
|------|------|
| SQLite 迁移至 PostgreSQL | 1 天 |
| CRM 集成或搭建轻量级 CRM | 2-3 天 |
| 照片附件支持 | 1 天 |

### 生产版交付物

- 部署在云服务器上
- 语音任务委派 → AI 路由 → 任务保存并追踪
- 用户登录和任务归属
- 完整任务生命周期 + 通知
- 长篇转录 + 实时进度
- CRM 集成（或自建轻量 CRM）

---

## 总结

| 阶段 | 时间 | 交付内容 |
|------|------|---------|
| **PoC** | 已完成 + 2-4h 打磨 | 语音 → 路由 → 结果，可运行演示 |
| **生产版** | 2-3 周 | 部署上线的系统，认证、通知、CRM |

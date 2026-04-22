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

## PoC Timeline: 1-2 Days

Build a rudimentary but functional version. All data manageable through basic UI.

### Day 1: Database + API

| Task | Time |
|------|------|
| Replace hardcoded data with SQLite tables (departments, people, tasks) | 1-2h |
| Seed DB with current mock data (auto-populate on first run) | 30min |
| CRUD API endpoints for departments (GET/POST/PUT/DELETE) | 1h |
| CRUD API endpoints for people (GET/POST/PUT/DELETE) | 1h |
| Tasks API: list all, update status | 30min |
| Router reads org structure from DB instead of hardcoded dict | 1h |
| Voice-routed tasks auto-save to tasks table | 30min |

### Day 2: UI + Testing

| Task | Time |
|------|------|
| Add "CRM" tab with departments table (view, add, delete) | 1h |
| Add people table with department dropdown | 1h |
| Add tasks table with status update (pending → completed) | 1h |
| End-to-end test: record → route → task appears in CRM table | 1h |
| Fix bugs, polish basic layout | 1-2h |

### PoC Deliverables

- Working web app on localhost:8010
- Voice task delegation → AI routing → task saved to DB
- Long-form recording → queued → transcribed → stored
- Basic management: add/edit/remove departments and people
- Task list with status tracking

---

## Production Timeline: 3-4 Weeks

Build a reliable, deployable system ready for real office use.

### Week 1: Database + Auth + CRM

| Task | Time |
|------|------|
| Migrate SQLite → PostgreSQL | 1 day |
| User authentication (login, sessions) | 1 day |
| Role-based access (admin vs. regular user) | 1 day |
| Full CRM UI: departments, people, tasks with search/filter | 1 day |
| Data import tool (CSV/Excel bulk import for existing org data) | 1 day |

### Week 2: Voice Pipeline Hardening

| Task | Time |
|------|------|
| Long-form audio: robust chunked upload with retry/resume | 1 day |
| Processing status: real-time progress via WebSocket or SSE | 1 day |
| Audio format compatibility (WAV, MP3, M4A, WebM) | 1 day |
| Error handling: graceful degradation, clear error messages in Chinese | 1 day |
| Fallback AI pipeline (if primary model unavailable) | 1 day |

### Week 3: Task Management + Notifications

| Task | Time |
|------|------|
| Task lifecycle: pending → assigned → in_progress → completed → archived | 1 day |
| Task assignment notifications (email or push) | 1 day |
| Task dashboard: statistics, filters, overdue alerts | 1 day |
| Photo attachment support (upload, store, display) | 1 day |
| Transcript review/approval UI (for long-form) | 1 day |

### Week 4: Deploy + Polish

| Task | Time |
|------|------|
| Cloud server setup + PostgreSQL + nginx reverse proxy | 1 day |
| HTTPS + basic security hardening | 1 day |
| Load testing (simulate concurrent users) | 1 day |
| Mobile-responsive UI polish | 1 day |
| Documentation + deployment runbook | 1 day |

### Production Deliverables

- Deployed on cloud server with PostgreSQL
- User login and role-based access
- Full task lifecycle with notifications
- Long-form transcription with real-time progress
- Photo attachments
- Mobile-responsive interface
- Deployment documentation

---

## Summary

| Phase | Time | What You Get |
|-------|------|-------------|
| **PoC** | 1-2 days | Working demo, basic CRM, all core features functional |
| **Production** | 3-4 weeks | Deployed system, auth, notifications, hardened pipeline |

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

## PoC 时间：1-2 天

搭建一个简陋但能跑通的版本，所有数据可以通过基础界面管理。

### 第1天：数据库 + API

| 任务 | 时间 |
|------|------|
| 将硬编码数据替换为 SQLite 表（部门、人员、任务） | 1-2h |
| 用现有模拟数据初始化数据库（首次运行自动填充） | 30min |
| 部门 CRUD API（GET/POST/PUT/DELETE） | 1h |
| 人员 CRUD API（GET/POST/PUT/DELETE） | 1h |
| 任务 API：列表、更新状态 | 30min |
| 路由器从数据库读取组织架构（替代硬编码） | 1h |
| 语音路由结果自动存入任务表 | 30min |

### 第2天：界面 + 测试

| 任务 | 时间 |
|------|------|
| 添加"CRM管理"Tab，部门表格（查看、新增、删除） | 1h |
| 人员表格，含部门下拉选择 | 1h |
| 任务表格，含状态更新（pending → completed） | 1h |
| 端到端测试：录音 → 路由 → 任务出现在 CRM 表中 | 1h |
| 修 Bug，基础布局调整 | 1-2h |

### PoC 交付物

- localhost:8010 上可运行的 Web 应用
- 语音任务委派 → AI 路由 → 任务存入数据库
- 长篇录音 → 排队 → 转录 → 存储
- 基础管理：增删改查部门和人员
- 任务列表及状态追踪

---

## 生产版时间：3-4 周

搭建一个可靠、可部署、适合办公室实际使用的系统。

### 第1周：数据库 + 认证 + CRM

| 任务 | 时间 |
|------|------|
| SQLite 迁移至 PostgreSQL | 1 天 |
| 用户认证（登录、会话） | 1 天 |
| 角色权限（管理员 vs 普通用户） | 1 天 |
| 完整 CRM 界面：部门、人员、任务，含搜索/筛选 | 1 天 |
| 数据导入工具（CSV/Excel 批量导入现有组织数据） | 1 天 |

### 第2周：语音管道加固

| 任务 | 时间 |
|------|------|
| 长篇音频：分块上传 + 断点续传 + 重试 | 1 天 |
| 处理状态：WebSocket 或 SSE 实时进度 | 1 天 |
| 音频格式兼容（WAV、MP3、M4A、WebM） | 1 天 |
| 错误处理：优雅降级、中文错误提示 | 1 天 |
| 备用 AI 管道（主力模型不可用时自动切换） | 1 天 |

### 第3周：任务管理 + 通知

| 任务 | 时间 |
|------|------|
| 任务生命周期：pending → assigned → in_progress → completed → archived | 1 天 |
| 任务分配通知（邮件或推送） | 1 天 |
| 任务看板：统计、筛选、逾期预警 | 1 天 |
| 照片附件支持（上传、存储、展示） | 1 天 |
| 转录审核/确认界面（长篇转录） | 1 天 |

### 第4周：部署 + 打磨

| 任务 | 时间 |
|------|------|
| 云服务器搭建 + PostgreSQL + nginx 反向代理 | 1 天 |
| HTTPS + 基础安全加固 | 1 天 |
| 负载测试（模拟并发用户） | 1 天 |
| 移动端适配 UI 打磨 | 1 天 |
| 文档 + 部署手册 | 1 天 |

### 生产版交付物

- 部署在云服务器上，使用 PostgreSQL
- 用户登录和角色权限
- 完整任务生命周期 + 通知
- 长篇转录 + 实时进度
- 照片附件
- 移动端适配界面
- 部署文档

---

## 总结

| 阶段 | 时间 | 交付内容 |
|------|------|---------|
| **PoC** | 1-2 天 | 可运行演示，基础 CRM，核心功能全部跑通 |
| **生产版** | 3-4 周 | 部署上线的系统，认证、通知、加固管道 |

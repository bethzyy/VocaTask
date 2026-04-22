# VocaTask — Timeline Estimate / 时间评估

> All estimates based on AI-assisted development (Claude Code).
> 所有时间估算基于 AI 辅助开发（Claude Code）。

---

## Current Status / 当前进度

| Module | Status |
|--------|--------|
| Voice recording + upload | Done |
| ASR transcription (ZhipuAI GLM-ASR-2512) | Done |
| Task routing (GLM-4-flash function calling + keyword fallback) | Done |
| Long-form transcription queue (background worker + ffmpeg segmentation) | Done |
| Browser UI (recording, results display, status polling) | Done |
| Mock org data (10 people, 5 departments, hardcoded) | Done |

---

## PoC Timeline: 1-2 Days / PoC 时间：1-2 天

Build a rudimentary but functional version. All data manageable through basic UI.
搭建一个简陋但能跑通的版本，所有数据可以通过基础界面管理。

### Day 1: Database + API / 第1天：数据库 + API

| Task | Time |
|------|------|
| Replace hardcoded data with SQLite tables (departments, people, tasks) | 1-2h |
| Seed DB with current mock data (auto-populate on first run) | 30min |
| CRUD API endpoints for departments (GET/POST/PUT/DELETE) | 1h |
| CRUD API endpoints for people (GET/POST/PUT/DELETE) | 1h |
| Tasks API: list all, update status | 30min |
| Router reads org structure from DB instead of hardcoded dict | 1h |
| Voice-routed tasks auto-save to tasks table | 30min |

### Day 2: UI + Testing / 第2天：界面 + 测试

| Task | Time |
|------|------|
| Add "CRM" tab with departments table (view, add, delete) | 1h |
| Add people table with department dropdown | 1h |
| Add tasks table with status update (pending → completed) | 1h |
| End-to-end test: record → route → task appears in CRM table | 1h |
| Fix bugs, polish basic layout | 1-2h |

### PoC Deliverables / PoC 交付物

- Working web app on localhost:8010
- Voice task delegation → AI routing → task saved to DB
- Long-form recording → queued → transcribed → stored
- Basic management: add/edit/remove departments and people
- Task list with status tracking

---

## Production Timeline: 3-4 Weeks / 生产版时间：3-4 周

Build a reliable, deployable system ready for real office use.
搭建一个可靠、可部署、适合办公室实际使用的系统。

### Week 1: Database + Auth + CRM / 第1周：数据库 + 认证 + CRM

| Task | Time |
|------|------|
| Migrate SQLite → PostgreSQL | 1 day |
| User authentication (login, sessions) | 1 day |
| Role-based access (admin vs. regular user) | 1 day |
| Full CRM UI: departments, people, tasks with search/filter | 1 day |
| Data import tool (CSV/Excel bulk import for existing org data) | 1 day |

### Week 2: Voice Pipeline Hardening / 第2周：语音管道加固

| Task | Time |
|------|------|
| Long-form audio: robust chunked upload with retry/resume | 1 day |
| Processing status: real-time progress via WebSocket or SSE | 1 day |
| Audio format compatibility (WAV, MP3, M4A, WebM) | 1 day |
| Error handling: graceful degradation, clear error messages in Chinese | 1 day |
| Fallback AI pipeline (if primary model unavailable) | 1 day |

### Week 3: Task Management + Notifications / 第3周：任务管理 + 通知

| Task | Time |
|------|------|
| Task lifecycle: pending → assigned → in_progress → completed → archived | 1 day |
| Task assignment notifications (email or push) | 1 day |
| Task dashboard: statistics, filters, overdue alerts | 1 day |
| Photo attachment support (upload, store, display) | 1 day |
| Transcript review/approval UI (for long-form) | 1 day |

### Week 4: Deploy + Polish / 第4周：部署 + 打磨

| Task | Time |
|------|------|
| Cloud server setup + PostgreSQL + nginx reverse proxy | 1 day |
| HTTPS + basic security hardening | 1 day |
| Load testing (simulate concurrent users) | 1 day |
| Mobile-responsive UI polish | 1 day |
| Documentation + deployment runbook | 1 day |

### Production Deliverables / 生产版交付物

- Deployed on cloud server with PostgreSQL
- User login and role-based access
- Full task lifecycle with notifications
- Long-form transcription with real-time progress
- Photo attachments
- Mobile-responsive interface
- Deployment documentation

---

## Summary / 总结

| Phase | Time | What You Get |
|-------|------|-------------|
| **PoC** | 1-2 days | Working demo, basic CRM, all core features functional |
| **Production** | 3-4 weeks | Deployed system, auth, notifications, hardened pipeline |

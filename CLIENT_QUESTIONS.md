# VocaTask — Client Confirmation Questions

> Information needed to estimate timelines for PoC and production versions.
> All time estimates below are based on AI-assisted development (Claude Code), not manual development.

---

## CRM Decision: CONFIRMED — Build Our Own

Client confirmed: They currently use **Zoho CRM** but plan to discontinue it. We will build a lightweight CRM from scratch.

- **PoC**: Rudimentary CRM with SQLite (basic people/departments/tasks CRUD)
- **Production**: Migrate to PostgreSQL with full task lifecycle management (replacing Zoho)

This eliminates the need for any external CRM integration. All data stays in our own system.

---

## Remaining Questions

### 1. Usage Scenario

- Usage environment: office / factory floor / outdoor construction site?
- How many users? Peak concurrent users?
- Long-form transcription (90 min) scenario: meetings / site inspections / training recordings?
- Are photo attachments required or optional?

**Impact on timeline:** Noisy environments need noise reduction (+2-4 days). High concurrency affects architecture (+2-3 days). Photos feature (+2-3 days).

### 2. AI Models

- Do you have an Anthropic API account (Claude)? Or other AI services?
- Gemma 4 E2B local inference — do you have a GPU server?
- Is speaker diarization (identifying who is speaking) a hard requirement?

**Impact on timeline:** Claude API works out of the box. Other models need adaptation (+2-3 days). Speaker diarization without GPU needs alternative solution (+1-2 weeks).

### 3. Infrastructure

- Do you have existing servers? What are the specs?
- Deployment target: cloud server / company intranet / self-hosted?
- Do you have operations/maintenance staff?

**Impact on timeline:** Existing servers: deploy in 1 day. Build from scratch: +3-4 days. On-premise security config: +3-4 days.

### 4. Budget

- AI API monthly budget
- Server hosting budget
- Development budget

**Impact on timeline:** Ample budget enables parallel development and stronger AI models — shorter timeline. Limited budget requires cost-effective solutions — potentially longer cycle.

---

---

# VocaTask — 客户确认问题清单

> 以下信息用于估算原型（PoC）和生产级产品的开发时间。
> 所有时间估算均基于 AI 辅助开发（Claude Code），非人工开发。

---

## CRM 决策：已确认 — 自建 CRM

客户确认：目前使用 **Zoho CRM** 但计划停用。我们将从零搭建轻量级 CRM。

- **PoC 阶段**：用 SQLite 做最基础的 CRM（人员/部门/任务的增删改查）
- **生产版**：迁移到 PostgreSQL，完整的任务生命周期管理（替代 Zoho）

无需对接任何外部 CRM 系统，所有数据都在自有系统内。

---

## 待确认问题

### 1. 使用场景

- 使用环境：办公室 / 工厂车间 / 户外工地？
- 大概多少人用？同时在线高峰多少人？
- 长篇转录（90分钟）场景：会议录音 / 巡检记录 / 培训记录？
- 照片附件是必须的还是可选的？

**对时间估算的影响：** 嘈杂环境需降噪处理（+2-4 天）；多人并发影响架构设计（+2-3 天）；照片附件（+2-3 天）。

### 2. AI 模型

- 有没有 Anthropic API 账号（Claude）？还是用其他 AI 服务？
- Gemma 4 E2B 本地推理 — 有 GPU 服务器吗？
- 说话人分离（区分谁在说话）是硬性需求吗？

**对时间估算的影响：** Claude API 直接可用；其他模型需适配（+2-3 天）。说话人分离无 GPU 需另找方案（+1-2 周）。

### 3. 基础设施

- 有没有现成的服务器？配置如何？
- 部署在哪里？云服务器 / 公司内网 / 客户自己搭？
- 有运维人员吗？

**对时间估算的影响：** 有现成服务器 1 天部署；从零搭建（+3-4 天）；内网安全配置（+3-4 天）。

### 4. 预算

- AI API 费用预算（按月）
- 服务器费用预算
- 开发费用预算

**对时间估算的影响：** 预算充足可并行开发、用更强模型，时间更短；预算有限需选性价比方案，可能拉长周期。

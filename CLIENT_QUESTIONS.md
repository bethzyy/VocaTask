# VocaTask — Client Confirmation Questions

> Information needed to estimate timelines for PoC and production versions.

---

## Prerequisite: Clarify the CRM Situation

We need to understand whether a CRM system currently exists at all. This is the single most important question, because the entire backend architecture depends on it:

| CRM Status | What We Build | Estimated Extra Time |
|------------|--------------|---------------------|
| CRM exists with API | Integration layer only | 1-2 weeks |
| CRM exists but no API | Direct DB connection or workaround | 3-5 weeks |
| No CRM at all | Full task management system from scratch | +4-6 weeks |

**Please confirm first: Does the organization currently have a CRM or task management system in use?**

If yes → please provide API documentation, database schema, or any technical documentation.
If no → we will plan to build the data management layer ourselves.

---

## 1. CRM System

Please provide CRM API documentation or database schema, and system access address.

- What is the CRM system? (Custom / DingTalk / Feishu / WeCom / Other)
- Does the CRM have an API for reading and writing data?
- What does "write results back to CRM" mean? Create task / send notification / update ticket?
- Where is the CRM deployed? (Cloud / on-premise) Can our backend access it?

**Impact on timeline:** With API docs: 1-2 weeks integration. Reverse engineering: 3-5 weeks. No CRM: +4-6 weeks to build.

## 2. Usage Scenario

- Usage environment: office / factory floor / outdoor construction site?
- How many users? Peak concurrent users?
- Long-form transcription (90 min) scenario: meetings / site inspections / training recordings?
- Are photo attachments required or optional?

**Impact on timeline:** Noisy environments need noise reduction (+1-2 weeks). High concurrency affects architecture (+1 week). Photos feature (+1 week).

## 3. AI Models

- Do you have an Anthropic API account (Claude)? Or other AI services?
- Gemma 4 E2B local inference — do you have a GPU server?
- Is speaker diarization (identifying who is speaking) a hard requirement?

**Impact on timeline:** Claude API works out of the box. Other models need adaptation (+1 week). Speaker diarization without GPU needs alternative solution (+2-3 weeks).

## 4. Infrastructure

- Do you have existing servers? What are the specs?
- The spec mentions PostgreSQL — existing instance or need to set up?
- Deployment target: cloud server / company intranet / self-hosted?
- Do you have operations/maintenance staff?

**Impact on timeline:** Existing servers + DB: deploy in 1-2 days. Build from scratch: +1 week. On-premise security config: +1 week.

## 5. Budget

- AI API monthly budget
- Server hosting budget
- Development budget

**Impact on timeline:** Ample budget enables parallel development and stronger AI models — shorter timeline. Limited budget requires cost-effective solutions — potentially longer cycle.

---

---

# VocaTask — 客户确认问题清单

> 以下信息用于估算原型（PoC）和生产级产品的开发时间。

---

## 前置确认：CRM 现状

首先需要搞清楚客户当前到底有没有 CRM 系统。这是最关键的问题，整个后端架构取决于此：

| CRM 现状 | 我们要做什么 | 额外时间 |
|----------|------------|---------|
| 有 CRM，且有 API | 只做集成层 | 1-2 周 |
| 有 CRM，但没有 API | 直连数据库或找其他方案 | 3-5 周 |
| 完全没有 CRM | 从零搭建整个任务管理系统 | +4-6 周 |

**请先确认：公司目前有没有在用 CRM 或任务管理系统？**

如果有 → 请提供 API 文档、数据库表结构、或任何技术文档。
如果没有 → 我们将自行规划数据管理层。

---

## 1. CRM 系统

请提供 CRM 的 API 文档或数据库表结构，以及系统访问地址。

- CRM 是什么系统？（自建/钉钉/飞书/企业微信/其他）
- 有没有 API 接口可以读写数据？
- "结果回写 CRM" 是建任务、发通知、还是更新工单？
- CRM 部署在哪里？（云上/内网）我们的后端能否访问到？

**对时间估算的影响：** 有现成 API 文档则 1-2 周；逆向分析或直连数据库则 3-5 周；没有 CRM 则额外 4-6 周。

## 2. 使用场景

- 使用环境：办公室 / 工厂车间 / 户外工地？
- 大概多少人用？同时在线高峰多少人？
- 长篇转录（90分钟）场景：会议录音 / 巡检记录 / 培训记录？
- 照片附件是必须的还是可选的？

**对时间估算的影响：** 嘈杂环境需降噪处理（+1-2 周）；多人并发影响架构设计（+1 周）；照片附件（+1 周）。

## 3. AI 模型

- 有没有 Anthropic API 账号（Claude）？还是用其他 AI 服务？
- Gemma 4 E2B 本地推理 — 有 GPU 服务器吗？
- 说话人分离（区分谁在说话）是硬性需求吗？

**对时间估算的影响：** Claude API 直接可用；其他模型需适配（+1 周）。说话人分离无 GPU 需另找方案（+2-3 周）。

## 4. 基础设施

- 有没有现成的服务器？配置如何？
- 需求中提到 PostgreSQL，有现成的还是要搭建？
- 部署在哪里？云服务器 / 公司内网 / 客户自己搭？
- 有运维人员吗？

**对时间估算的影响：** 有现成服务器和数据库 1-2 天部署；从零搭建（+1 周）；内网安全配置（+1 周）。

## 5. 预算

- AI API 费用预算（按月）
- 服务器费用预算
- 开发费用预算

**对时间估算的影响：** 预算充足可并行开发、用更强模型，时间更短；预算有限需选性价比方案，可能拉长周期。

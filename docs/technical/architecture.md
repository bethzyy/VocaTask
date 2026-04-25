# VocaTask — 技术架构文档

**版本**: v1.0  
**日期**: 2026-04-25  
**受众**: 开发者、接手维护者  
**关联文档**: [prd.md](../product/prd.md)（产品需求）、[timeline.md](../planning/timeline.md)（路线图）

---

## 1. 系统全貌

VocaTask 由**两个独立后端进程**驱动，共用一个 SQLite 数据库。

```
┌──────────────────────┐    ┌──────────────────────┐
│  web/index.html      │    │  web/crm/index.html  │
│  VocaTask 发任务前端  │    │  CRM 处理前端         │
│  （领导/工人，手机）  │    │  （员工/主管，电脑）  │
└──────────┬───────────┘    └──────────┬───────────┘
           │ fetch /api/*              │ fetch /api/crm/*
           ▼                           ▼
┌──────────────────────┐    ┌──────────────────────┐
│  server.py           │    │  crm_server.py       │
│  后端 A — port 8010  │    │  后端 B — port 8011  │
│                      │    │                      │
│  · 接收录音/图片      │    │  · 任务列表/详情     │
│  · ASR 转录          │    │  · 状态流转          │
│  · Vision 图片描述    │    │  · 添加笔记          │
│  · GLM 路由分配       │    │  · Claude 后台分析   │
│  · 写入数据库         │    │  · 读取数据库         │
└──────────┬───────────┘    └──────────┬───────────┘
           └──────────────┬────────────┘
                          ▼
               ┌──────────────────┐
               │  data/help.db    │
               │  SQLite WAL 模式  │
               └──────────────────┘
```

**关键特性**：
- 两个后端**独立进程**，互不依赖对方存活，可分别重启
- 共享同一 SQLite 文件（WAL 模式支持多进程并发读写）
- 后端 A 主写（领导发任务），后端 B 主读+更新状态（员工处理）
- 两个前端均为纯原生 JS，无构建步骤，工厂内网环境友好

---

## 2. API Key 安全架构

**结论：API Key 只存在于后端服务器，浏览器永远看不到。**

```
Browser（前端）              Flask 后端（server.py）      第三方 API
      │                          │                           │
      │── POST /api/transcribe ─▶│                           │
      │   (音频二进制，无 Key)    │── ASR  (ZHIPU_API_KEY) ──▶│
      │                          │◀── 转录文字 ───────────────│
      │                          │── Vision (ZHIPU_API_KEY) ─▶│
      │                          │◀── 图片描述 ───────────────│
      │                          │── Route  (ZHIPU_API_KEY) ─▶│
      │                          │◀── 路由 JSON ──────────────│
      │◀── 返回路由结果 JSON ─────│
      │    (只有结果，无 Key)
```

- Key 存于服务器**环境变量**（`.env` 文件，已加入 `.gitignore`，不入代码库）
- 浏览器 DevTools → Network 中只能看到音频二进制上传和 JSON 结果返回，**看不到任何 Key**
- Anthropic / 智谱官方文档均明确要求：API Key 只能在服务端使用

---

## 3. 主请求数据流

### 3.1 `/api/transcribe-and-route`（核心流程）

```
① 前端 POST multipart：音频文件 + 可选图片（最多 5 张）
② 后端保存文件
     data/audio/<uuid>.webm
     data/images/<uuid>.jpg  × N
③ ThreadPoolExecutor 并发执行（ASR 与 Vision 互不依赖）：
     ├─ ASR 分支：ffmpeg 转 16kHz WAV → GLM-ASR-2512 → 转录文字
     └─ Vision 分支 × N：GLM-4V-Flash → 每张图一句话描述（并行）
④ GLM-4-flash 函数调用路由（需要 ③ 两路结果后才能执行）
     输入：转录文字 + 图片描述合并 + 组织架构
     输出：assignee / department / priority / reason
⑤ 写入数据库
     routing_history（主记录）
     task_attachments（图片路径 + 描述）
⑥ 返回 JSON → 前端渲染气泡
```

### 3.2 CRM Claude 后台 Worker

`crm_server.py` 启动时开启守护线程，对已路由但未经 Claude 二次分析的任务进行深度解析：

```
每 8 秒一轮：
  ① 查询 routing_history WHERE claude_analyzed = 0
  ② 对每条任务调用 claude-sonnet-4-6
     输入：transcribed_text + image_context + 组织架构
     输出：assignee / department / priority / task_description / reason
  ③ 写回 routing_history（claude_* 字段）
  ④ CRM 前端展示 Claude 版解析结果（优先级高于 GLM 版）
```

GLM 路由（实时，~1s）负责即时响应，Claude 分析（异步，8s 内）负责更高质量的二次解读。

---

## 4. 数据库表关系

```
routing_history（主表）
  id, transcribed_text, assignee, department, priority, method
  image_context, status, claude_analyzed
  claude_assignee, claude_department, claude_priority
  claude_task_description, claude_reason
  created_at, updated_at
      │
      ├──▶ task_attachments
      │      routing_id → image_path, original_filename, description
      │
      └──▶ task_notes
             routing_id → note_text, note_by, created_at

transcription_jobs（独立，长篇转录队列）
  id, file_path, filename, status
  text_result, error_message, progress
  created_at, updated_at
```

---

## 5. 转录管道性能设计

### 5.1 并发优化（2026-04-25 引入）

ASR 和 Vision 原为串行，改为 `ThreadPoolExecutor` 并发后：

| 场景 | 改前 | 改后 | 节省 |
|------|------|------|------|
| 纯语音（无图） | ~3s | ~3s | — |
| 语音 + 1 张图 | ~5s | ~3.5s | ~1.5s |
| 语音 + 3 张图 | ~8s | ~3.5s | ~4.5s |

### 5.2 重试策略

ASR 调用失败时指数退避重试，最多 3 次：

| 尝试 | 等待 |
|------|------|
| 第 1 次失败 | 1s |
| 第 2 次失败 | 2s |
| 第 3 次失败 | 返回错误 |

---

## 6. 技术选型理由

| 选择 | 替代方案 | 理由 |
|------|---------|------|
| SQLite WAL | PostgreSQL | PoC 阶段零运维；WAL 支持多进程并发读写 |
| 两个 Flask 进程 | 单进程多蓝图 | 按角色独立部署；独立重启互不影响 |
| ThreadPoolExecutor | asyncio | Flask 同步环境，线程池改动最小 |
| 原生 JS | React / Vue | 零构建依赖；内网离线环境直接可用 |
| GLM-4-flash 路由 | Claude 直接路由 | 低延迟实时响应；Claude 作异步二次分析 |
| SQLite → 生产用 PostgreSQL | — | 并发压力大时迁移，接口层不需改动 |

---

## 7. 目录结构

```
VocaTask/
├── server.py           # 后端 A（发任务，:8010）
├── crm_server.py       # 后端 B（CRM，:8011）
├── config.py           # 统一配置（端口、路径、模型名）
├── core/
│   ├── asr.py          # ASR 服务（GLM-ASR-2512 + ffmpeg）
│   ├── vision.py       # 图片描述（GLM-4V-Flash）
│   ├── router.py       # GLM 路由（函数调用）
│   ├── claude_router.py# Claude 二次分析
│   ├── storage.py      # 音频/图片存储 + 主库 ORM
│   ├── crm_storage.py  # CRM 专用查询
│   ├── org_structure.py# 组织架构（人员/部门/别名）
│   └── queue.py        # 长篇转录后台队列
├── web/
│   ├── index.html      # 发任务前端
│   ├── crm/
│   │   └── index.html  # CRM 前端
│   └── static/
│       ├── app.js      # 发任务前端逻辑
│       ├── style.css   # 发任务前端样式
│       ├── crm.js      # CRM 前端逻辑
│       └── crm.css     # CRM 前端样式
├── data/               # 运行时数据（.gitignore）
│   ├── help.db
│   ├── audio/
│   └── images/
├── .env                # API Key（.gitignore，不入库）
├── .env.example        # Key 模板（入库）
├── PRD.md              # 产品需求文档
├── ARCH.md             # 本文档
└── TIMELINE.md         # 路线图
```

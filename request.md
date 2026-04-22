# MOBILE TASK ROUTING AND TRANSCRIPTION APP — DESIGN DOCUMENT

An Android app that can operate primarily on voice commands.

---

## 1. OVERVIEW

Voice-controlled mobile app for task delegation and long-form transcription. Two distinct workflows: Quick task routing (voice plus optional photo) and extended transcription mode (voice, photos, long context for batch server processing).

## 2. TECH STACK

- Mobile: React Native (iOS and Android)
- Backend: Python (in-house)
- Database: PostgreSQL
- Primary AI: Claude Haiku 4.5 (real-time task routing)
- Fallback AI: Gemma 4 E2B (local inference)
- Speech Processing: Claude API transcription plus Gemma diarization for speaker ID

## 3. ARCHITECTURE LAYERS

### Mobile Layer (React Native)

- Voice capture and recording
- Photo attachment
- UI for mode selection (quick task vs. long transcription)
- Local audio buffering
- API calls to backend

### Backend Layer (Python)

- API endpoint for voice/photo intake
- Speaker diarization preprocessing (Gemma 4 E2B)
- Claude API integration for task understanding and routing
- CRM data queries (org structure, team assignments)
- Batch queue for long-form transcription
- Results writing back to CRM

### Data Layer (PostgreSQL)

- Organization structure (departments, teams, people)
- Task assignments and history
- Transcripts and metadata
- Photo storage references
- Processing status and audit trail

## 4. WORKFLOWS

### Workflow A: Quick Task Delegation

- User speaks task description, optionally attaches photo
- Mobile sends audio to backend
- Backend transcribes via Claude
- Claude processes context, calls routing tool
- Tool matches to person/department based on org structure
- Result written to CRM, user notified
- Latency: sub-second to a few seconds

### Workflow B: Long-Form Transcription

- User captures extended audio and photos (site walkthrough, documentation) — up to 90 minutes
- Mobile queues everything, sends to backend
- Backend stores in processing queue
- Later: batch process through Claude with extended thinking or Opus
- Python can perform custom analysis
- Results saved to persistent knowledge system in CRM
- User reviews and approves when ready

## 5. KEY INTEGRATIONS

### Claude API

- Transcription (up to 1 hour audio)
- Task understanding and routing logic
- Tool use for CRM queries and writes

### Gemma 4 E2B (Fallback)

- Local speaker diarization
- Lightweight fallback if Claude unavailable
- Can run on backend infrastructure

### CRM System (In-House)

- Stores org structure
- Task and transcript storage
- Historical context for routing decisions
- Photo and file attachments

## 6. TOOL DEFINITIONS

- `route_task(task_description, priority, attachments)` → person/department
- `query_org_structure()` → departments, teams, members
- `save_task(assigned_to, description, attachments)` → CRM ID
- `save_transcript(content, metadata, attachments)` → CRM ID
- `get_person_availability()` → current workload for routing

## 7. SPEAKER DIARIZATION

- Preprocess audio with Gemma 4 E2B speaker ID before Claude transcription
- Tag speakers in transcript output
- Store speaker metadata with transcript for context

## 8. ERROR HANDLING & FALLBACK

- If Claude unavailable: route to Gemma 4 E2B locally
- Network failure: queue locally, sync when restored
- Ambiguous routing: flag for manual review
- Processing errors: log and notify admin

## 9. DATA FLOW SUMMARY

Quick task:
```
Mobile (voice + photo) → Backend API → Preprocessing (diarization) → Claude transcription & routing → CRM write → Mobile notification
```

Long-form:
```
Mobile queue → Backend batch → Claude/Opus processing → Python analysis → CRM storage → Knowledge system
```

---
---

# 移动任务路由与转录应用 — 设计文档

一款以语音操作为主的 Android 应用。

---

## 1. 概述

基于语音控制的移动应用，用于任务委派和长篇转录。包含两个独立工作流：快速任务路由（语音+可选照片）和扩展转录模式（语音、照片、长上下文，用于批量服务器处理）。

## 2. 技术栈

- 移动端：React Native（iOS 和 Android）
- 后端：Python（自建）
- 数据库：PostgreSQL
- 主 AI：Claude Haiku 4.5（实时任务路由）
- 备用 AI：Gemma 4 E2B（本地推理）
- 语音处理：Claude API 转录 + Gemma 说话人分离用于识别说话人

## 3. 架构层次

### 移动端层（React Native）

- 语音捕获和录制
- 照片附件
- 模式选择界面（快速任务 vs. 长篇转录）
- 本地音频缓冲
- 后端 API 调用

### 后端层（Python）

- 语音/照片接收 API 端点
- 说话人分离预处理（Gemma 4 E2B）
- Claude API 集成 — 任务理解和路由
- CRM 数据查询（组织架构、团队分配）
- 长篇转录批量队列
- 结果回写至 CRM

### 数据层（PostgreSQL）

- 组织架构（部门、团队、人员）
- 任务分配和历史记录
- 转录文本和元数据
- 照片存储引用
- 处理状态和审计追踪

## 4. 工作流程

### 工作流 A：快速任务委派

- 用户口述任务描述，可选附带照片
- 移动端发送音频至后端
- 后端通过 Claude 转录
- Claude 处理上下文，调用路由工具
- 工具根据组织架构匹配到具体人员/部门
- 结果写入 CRM，通知用户
- 延迟：亚秒级到数秒

### 工作流 B：长篇转录

- 用户采集长时间音频和照片（现场巡检、文档记录）— 最长90分钟
- 移动端将所有内容排队，发送至后端
- 后端存入处理队列
- 稍后：通过 Claude 扩展思考或 Opus 模型进行批量处理
- Python 可执行自定义分析
- 结果保存到 CRM 中的持久化知识系统
- 用户在方便时审核和确认

## 5. 关键集成

### Claude API

- 转录（最长 1 小时音频）
- 任务理解和路由逻辑
- 工具调用进行 CRM 查询和写入

### Gemma 4 E2B（备用）

- 本地说话人分离
- Claude 不可用时的轻量级备选
- 可在后端基础设施上运行

### CRM 系统（自建）

- 存储组织架构
- 任务和转录存储
- 路由决策的历史上下文
- 照片和文件附件

## 6. 工具定义

- `route_task(task_description, priority, attachments)` → 人员/部门
- `query_org_structure()` → 部门、团队、成员
- `save_task(assigned_to, description, attachments)` → CRM ID
- `save_transcript(content, metadata, attachments)` → CRM ID
- `get_person_availability()` → 当前工作负载（用于路由决策）

## 7. 说话人分离

- 在 Claude 转录之前，使用 Gemma 4 E2B 进行说话人识别预处理
- 在转录输出中标记各说话人
- 将说话人元数据与转录文本一起存储，提供上下文

## 8. 错误处理与降级策略

- Claude 不可用时：切换到本地 Gemma 4 E2B
- 网络故障时：本地排队，恢复后同步
- 路由不明确时：标记为人工审核
- 处理错误时：记录日志并通知管理员

## 9. 数据流概览

快速任务：
```
移动端（语音+照片）→ 后端 API → 预处理（说话人分离）→ Claude 转录和路由 → CRM 写入 → 移动端通知
```

长篇转录：
```
移动端队列 → 后端批量处理 → Claude/Opus 处理 → Python 分析 → CRM 存储 → 知识系统
```

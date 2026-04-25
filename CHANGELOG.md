# Changelog

所有文档与产品的重要变更记录于此。格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)。

---

## [未发布]

### 文档
- 重组文档结构：所有文档统一移至 `docs/` 目录，按 product / technical / planning 分类
- 新增 `README.md`（项目入口，含快速启动）
- 新增 `CHANGELOG.md`（本文件）
- `ARCH.md` 改名为 `docs/technical/architecture.md`（标准命名）
- `PRD_v0.md` 归档至 `docs/archive/prd-v0.1.md`

---

## [0.2.0] — 2026-04-25

### 新增
- CRM 后端（`crm_server.py` + `core/crm_storage.py`）：任务列表、状态流转、笔记
- 图片附件支持：Vision 描述（GLM-4V-Flash）纳入路由判断
- Claude 后台 Worker：对已路由任务进行 claude-sonnet-4-6 二次深度分析
- VocaTask 前端重写为聊天气泡样式（豆包风格）
- CRM 前端新增任务卡片、排序、统计、详情页
- Minimax 设计系统：品牌蓝 #1456f0、DM Sans + Outfit 字体、pill 圆角

### 优化
- 转录管道并发化：ASR 与 Vision 通过 ThreadPoolExecutor 并行执行，有图片时节省 1.5–3 秒
- ASR 重试等待从 5/10/15s 缩短至 1/2/3s

### 修复
- 昵称路由：「小张」在句首/句中/句尾均能正确识别并分配，组织架构新增别名列表

### 文档
- 新增 `ARCH.md`（技术架构文档，含系统图、API Key 安全流、数据流）
- PRD 升级至 v0.2：新增部署方案 A/B/C、环境变量配置说明

---

## [0.1.0] — 2026-04-24

### 新增
- 语音录音与 ASR 转录（ZhipuAI GLM-ASR-2512）
- GLM-4-flash 函数调用任务路由
- 关键词兜底路由（AI 不可用时）
- 长篇转录队列（ffmpeg 分片 + 后台线程处理）
- SQLite 数据库（WAL 模式）
- 初版 PRD（`docs/archive/prd-v0.1.md`）

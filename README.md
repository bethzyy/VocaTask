# VocaTask

工厂现场语音任务路由系统。工人用手机说一句话，AI 自动判断任务类型并分配给对应负责人，管理人员在电脑 CRM 上实时跟进处理。

**当前阶段**: PoC（概念验证）

---

## 快速启动

**前置条件**: Python 3.11+、ffmpeg、ZhipuAI API Key

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 ZHIPU_API_KEY 和 FFMPEG_PATH

# 2. 安装依赖
pip install flask zhipuai anthropic python-dotenv flask-cors

# 3. 启动发任务端（领导/工人）
python server.py          # → http://localhost:8010

# 4. 启动 CRM 端（另开终端，员工/主管）
python crm_server.py      # → http://localhost:8011
```

---

## 文档导航

| 文档 | 说明 |
|------|------|
| [docs/prd.md](docs/prd.md) | 产品需求、功能清单、验收标准 |
| [docs/architecture.md](docs/architecture.md) | 系统架构、数据流、API Key 安全、DB 表结构 |
| [docs/timeline.md](docs/timeline.md) | 项目路线图与里程碑 |
| [docs/faq.md](docs/faq.md) | 客户确认问题清单 |
| [docs/requirements.md](docs/requirements.md) | 原始需求简报 |
| [CHANGELOG.md](CHANGELOG.md) | 版本变更记录 |

---

## 项目结构

```
VocaTask/
├── server.py           # 后端 A — 发任务端 (:8010)
├── crm_server.py       # 后端 B — CRM 端 (:8011)
├── config.py           # 统一配置
├── core/               # 核心服务模块
│   ├── asr.py          # 语音转文字
│   ├── vision.py       # 图片描述
│   ├── router.py       # GLM 任务路由
│   ├── ai_router.py    # AI 路由（多模型）
│   └── org_structure.py# 组织架构数据
├── web/                # 前端页面
│   ├── index.html      # 发任务前端
│   ├── crm/index.html  # CRM 前端
│   └── static/         # JS / CSS
├── docs/               # 项目文档
└── data/               # 运行时数据（.gitignore）
```

---

## 已知限制（PoC 阶段）

- 手机浏览器需 HTTPS 才能调用麦克风（局域网 IP 下不可用）
- 无用户登录与权限管理
- SQLite 不适合高并发生产环境

详见 [docs/prd.md — 第 7 节](docs/prd.md)

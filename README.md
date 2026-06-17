# AI Interview Copilot

AI 模拟面试助手 — 简历解析、JD 分析、RAG 智能追问、多维度评分报告。

## 🚀 快速开始

```bash
# 1. 启动基础设施
docker-compose up -d

# 2. 后端
cd back-end
cp .env.example .env   # 编辑 .env 填入 LLM API Key
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000

# 3. 前端
cd front-end
pnpm install
pnpm dev
```

访问 http://localhost:3000

## 🏗️ 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Next.js 16 + React 19 + TypeScript + Zustand + Tailwind CSS 4 |
| 后端 | FastAPI + SQLAlchemy async + Pydantic + JWT |
| 数据库 | PostgreSQL 15 + Milvus 2.5+ (向量检索) |
| LLM | 阿里百炼 (OpenAI 兼容) — qwen3.7-plus |
| 部署 | Docker Compose (PG + Milvus + etcd + MinIO) |

## 📐 核心架构

```
用户 → 上传简历/JD → AI解析 → 向量化存储 → 模拟面试
                                         ↓
                              RAG检索 → ReAct推理 → LLM追问
                                         ↓
                              结束面试 → 多维评分 → 雷达图报告
```

## 📋 功能矩阵

| 模块 | 功能 |
|------|------|
| 🔐 认证 | 注册/登录/登出，JWT + bcrypt + Token黑名单 + 限流 |
| 📄 简历 | 上传 PDF/TXT，LLM 提取技能/经历/学历，技能分类 |
| 📋 JD | 上传/粘贴岗位描述，LLM 分析技能需求，简历匹配度 |
| 💬 面试 | AI 面试官 RAG 追问，SSE 流式对话，阶段管理 |
| 📊 报告 | 5维度评分（技术/沟通/解决问题/学习/匹配），雷达图，建议 |
| 🔍 分析 | GitHub/LeetCode 外部数据集成 |
| 🧠 Agent | ReAct 推理 + Memory 系统 + 动态追问策略 |

## 📁 项目结构

```
AI_Interview_Copilot/
├── back-end/
│   ├── src/
│   │   ├── agents/          # 智能体层 (Resume/JD/Interview/Evaluation/ReAct/Memory/MCP)
│   │   ├── api/             # FastAPI 路由 (auth/resume/jd/interview/report/external)
│   │   ├── services/        # 业务服务 (LLM/Embedding/Retrieval/Rerank/RAG)
│   │   ├── models/          # SQLAlchemy ORM
│   │   ├── schemas/         # Pydantic 数据模型
│   │   ├── core/            # 配置/安全/日志/Token黑名单
│   │   ├── db/              # PostgreSQL + Milvus 连接
│   │   └── utils/           # 工具函数 (PDF解析/文件处理/Prompt构建)
│   └── requirements.txt
├── front-end/
│   ├── app/                 # Next.js App Router 页面
│   │   ├── login/ register/ dashboard/ resume/ jd/ interview/ report/ external/
│   ├── components/          # 组件 (auth/chat/common/jd/report/resume)
│   ├── store/               # Zustand 状态管理
│   ├── services/            # API 调用封装
│   ├── hooks/               # 自定义 Hooks
│   └── types/               # TypeScript 类型定义
└── docker-compose.yml       # PostgreSQL + Milvus + etcd + MinIO
```

## 🔑 环境变量

参考 `back-end/.env.example`:

```env
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ai_interview
LLM_API_KEY=your-dashscope-api-key
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode
LLM_MODEL=qwen3.7-plus
MILVUS_HOST=localhost
MILVUS_PORT=19530
```

## 📖 详细文档

- [项目亮点总结](./PROJECT_HIGHLIGHTS.md) — 12 大技术亮点
- [后端文档](./back-end/docs/)

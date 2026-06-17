# 系统架构

## 概览

AI Interview Copilot 采用前后端分离架构：

- **前端**：Next.js App Router
- **后端**：FastAPI + SQLAlchemy
- **向量库**：Milvus
- **关系库**：PostgreSQL
- **LLM**：DeepSeek API

## 核心流程

```
用户上传简历/JD
    ↓
解析 & 向量化 (PyMuPDF + BGE-M3)
    ↓
存入 PostgreSQL + Milvus
    ↓
创建面试会话
    ↓
RAG 检索 (Milvus) → Rerank (BGE-Reranker) → LLM 生成追问
    ↓
结束面试 → 评估 Agent 生成评分报告
```

## 目录结构

| 模块 | 职责 |
|------|------|
| `api/` | FastAPI 路由层 |
| `services/` | 业务逻辑与 RAG 管线 |
| `agents/` | V2 多 Agent 编排 |
| `models/` | SQLAlchemy ORM |
| `schemas/` | Pydantic 请求/响应模型 |
| `db/` | PostgreSQL & Milvus 连接 |
| `utils/` | PDF 解析、分块、Prompt 构建 |
| `core/` | 配置、JWT、日志 |

## V1 vs V2

- **V1**：`services/` 直接调用 LLM + RAG
- **V2**：`agents/` 接管分析、面试、评估的多步推理

# 部署指南

## 环境要求

- Python 3.11+
- PostgreSQL 15+
- Milvus 2.5+（可选，未连接时 RAG 降级）
- DeepSeek API Key

## 本地开发

```bash
cd back-end
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
cp .env.example .env          # 编辑配置
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

## Docker Compose（推荐）

```yaml
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: ai_interview
    ports:
      - "5432:5432"

  milvus:
    image: milvusdb/milvus:latest
    ports:
      - "19530:19530"
```

## 环境变量

见 `.env.example`，生产环境务必修改 `SECRET_KEY` 并配置 HTTPS。

## 健康检查

```
GET http://localhost:8000/health
```

## 与前端联调

前端默认 API 地址：`http://localhost:8000/api`

```env
# front-end/.env.local
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api
```

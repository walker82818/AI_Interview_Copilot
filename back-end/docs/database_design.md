# 数据库设计

## PostgreSQL 表

### users

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID (str) | 主键 |
| email | varchar(255) | 唯一 |
| name | varchar(100) | 姓名 |
| hashed_password | varchar(255) | bcrypt |
| created_at | timestamptz | 创建时间 |

### resumes

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| user_id | FK → users | 所属用户 |
| file_name | varchar(255) | 原始文件名 |
| file_path | varchar(512) | 存储路径 |
| raw_text | text | 解析文本 |
| status | varchar(20) | pending / parsed / failed |
| analysis_json | text | 解析结果 JSON |
| uploaded_at | timestamptz | 上传时间 |

### job_descriptions

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| user_id | FK → users | 所属用户 |
| title | varchar(255) | 职位名称 |
| company | varchar(255) | 公司 |
| content | text | JD 正文 |
| file_path | varchar(512) | 可选文件路径 |
| status | varchar(20) | pending / analyzed / failed |
| analysis_json | text | 分析结果 JSON |
| uploaded_at | timestamptz | 创建时间 |

### interview_sessions

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| user_id | FK → users | 所属用户 |
| resume_id | FK → resumes | 关联简历 |
| jd_id | FK → job_descriptions | 关联 JD |
| status | varchar(20) | active / completed |
| started_at | timestamptz | 开始时间 |
| ended_at | timestamptz | 结束时间 |

### messages

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| session_id | FK → interview_sessions | 所属会话 |
| role | varchar(20) | user / assistant / system |
| content | text | 消息内容 |
| created_at | timestamptz | 发送时间 |

## Milvus Collection

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int64 | 主键 |
| doc_id | varchar | 文档 ID（resume/jd） |
| chunk_index | int | 分块序号 |
| text | varchar | 文本内容 |
| embedding | float_vector | BGE-M3 向量 |

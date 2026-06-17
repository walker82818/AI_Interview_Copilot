# API 设计

Base URL: `http://localhost:8000/api`

## Auth

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/auth/register` | 注册 |
| POST | `/auth/login` | 登录 |
| GET | `/auth/me` | 当前用户 |
| POST | `/auth/logout` | 登出 |

## Resume

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/resumes/upload` | 上传简历 |
| GET | `/resumes` | 列表 |
| GET | `/resumes/{id}` | 详情 |
| GET | `/resumes/{id}/analysis` | 解析结果 |
| DELETE | `/resumes/{id}` | 删除 |

## JD

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/jd/upload` | 上传 JD 文件 |
| POST | `/jd` | 粘贴 JD 文本 |
| GET | `/jd` | 列表 |
| GET | `/jd/{id}` | 详情 |
| GET | `/jd/{id}/analysis` | 技能分析 |
| DELETE | `/jd/{id}` | 删除 |

## Interview

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/interviews` | 创建面试 |
| GET | `/interviews/recent` | 最近面试 |
| GET | `/interviews/{id}` | 会话详情 |
| POST | `/interviews/{id}/messages` | 发送消息 |
| POST | `/interviews/{id}/messages/stream` | 流式回复 |
| POST | `/interviews/{id}/end` | 结束面试 |

## Report

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/reports/{sessionId}` | 获取报告 |
| POST | `/reports/{sessionId}/generate` | 生成报告 |

## 认证

请求头：`Authorization: Bearer <token>`

## 响应格式

JSON 字段采用 camelCase，与前端 TypeScript 类型对齐。

# TinyLearn

每天一条学习记录，自动构建知识体系。

## 功能

- 输入每日学习内容，自动结构化（提炼概念、命题、关系）
- 按周/月/季/年生成知识体系报告
- 自动识别知识漏洞并给出修复建议

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 填入 API Key

# 3. 启动服务
uvicorn app.main:app --reload

# 4. 访问
# 输入页面: http://localhost:8000/
# 报告页面: http://localhost:8000/review
# API 文档: http://localhost:8000/docs
```

## 配置

编辑 `.env` 文件：

```
# 选择 LLM: openai 或 claude
LLM_PROVIDER=openai

# OpenAI
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4o

# Claude (如果使用)
ANTHROPIC_API_KEY=sk-ant-xxx
CLAUDE_MODEL=claude-sonnet-4-20250514
```

## API

- `POST /entries` - 提交学习记录
- `GET /entries` - 获取记录列表
- `POST /reports/{week|month|quarter|year}/{key}` - 生成报告
- `GET /reports/{week|month|quarter|year}/{key}` - 获取报告

## 技术栈

- FastAPI + SQLite + Jinja2
- OpenAI / Claude API
- Pydantic for structured output

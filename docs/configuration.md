# PaperGuide 配置指南

## 环境变量

所有配置通过 `.env` 文件管理。复制 `.env.example` 创建你的配置：

```bash
cp .env.example .env
```

## 配置项详解

### LLM 配置

| 变量 | 说明 | 默认值 | 必填 |
|------|------|--------|------|
| `LLM_PROVIDER` | LLM 提供商 | `openai` | 否 |
| `OPENAI_API_KEY` | OpenAI API Key | - | 是* |
| `OPENAI_MODEL` | OpenAI 模型 | `gpt-4o` | 否 |
| `OPENAI_BASE_URL` | 自定义 API 地址 | - | 否 |
| `ANTHROPIC_API_KEY` | Claude API Key | - | 是* |
| `CLAUDE_MODEL` | Claude 模型 | `claude-sonnet-4-20250514` | 否 |
| `ANTHROPIC_BASE_URL` | 自定义 API 地址 | - | 否 |
| `SUPPORT_IMAGES` | 是否支持图片分析 | `true` | 否 |

> *根据 `LLM_PROVIDER` 选择，至少需要一个 API Key

### 搜索配置

| 变量 | 说明 | 默认值 | 必填 |
|------|------|--------|------|
| `SEARCH_PROVIDER` | 搜索引擎 | `brave` | 否 |
| `BRAVE_API_KEY` | Brave Search API Key | - | 否 |

### 其他配置

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `OUTPUT_DIR` | 输出目录 | `outputs` |

## 配置示例

### 使用 OpenAI

```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4o
```

### 使用 Claude

```bash
LLM_PROVIDER=claude
ANTHROPIC_API_KEY=sk-ant-xxx
CLAUDE_MODEL=claude-sonnet-4-20250514
```

### 使用兼容 API（如 OpenRouter）

```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-or-xxx
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=anthropic/claude-3.5-sonnet
```

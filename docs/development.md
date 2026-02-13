# PaperGuide 开发指南

## 开发环境设置

### 1. 克隆项目

```bash
git clone https://github.com/xxx/PaperGuide.git
cd PaperGuide
```

### 2. 创建虚拟环境

```bash
conda create -n paperguide python=3.11 -y
conda activate paperguide
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填入 API Key
```

### 5. 启动开发服务器

```bash
streamlit run app.py
```

## 项目结构

```
PaperGuide/
├── app.py              # Streamlit 入口
├── config.py           # 配置管理 (pydantic-settings)
├── core/               # 核心模块
│   ├── agent.py        # Agent 主逻辑
│   ├── pdf_parser.py   # PDF 解析
│   ├── arxiv_downloader.py
│   ├── llm_client.py   # LLM 客户端
│   └── search/         # 搜索模块
│       ├── base.py     # 抽象接口
│       └── brave.py    # Brave 实现
├── prompts/            # 提示词模板
├── templates/          # MD 模板
├── docs/               # 文档
└── outputs/            # 输出目录
```

## 开发规范

### 代码风格

- Python 3.11+，使用类型注解
- 遵循 PEP 8
- 每个模块不超过 200 行

### 提交规范

```
feat: 新功能
fix: 修复 bug
docs: 文档更新
refactor: 重构
```

## 扩展开发

### 添加新的 LLM Provider

1. 在 `core/llm_client.py` 添加新类
2. 实现 `LLMProvider` 接口
3. 在 `get_llm_provider()` 添加工厂逻辑

### 添加新的搜索引擎

1. 在 `core/search/` 创建新文件
2. 实现 `SearchProvider` 接口
3. 在 `base.py` 的 `get_search_provider()` 添加

### 添加新的提示词

1. 在 `prompts/` 创建 `.md` 文件
2. 使用 `{variable}` 作为占位符
3. 通过 `agent._load_prompt()` 加载

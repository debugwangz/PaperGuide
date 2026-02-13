# PaperGuide 📄

帮助任何人（哪怕对领域一无所知）通过与AI对话，理解论文核心，同时学习论文省略的背景知识。

## 功能特点

- **PDF/arXiv 支持** - 上传PDF或输入arXiv链接
- **智能解读** - 自动生成结构化的论文解读
- **知识补充** - 通过网络搜索补充论文省略的背景知识
- **对话问答** - 不懂的地方随时问，AI实时解答
- **文档更新** - 对话中的重要知识会更新到解读文档

## 快速开始

```bash
# 1. 创建conda环境
conda create -n paperguide python=3.11 -y
conda activate paperguide

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 填入 API Key

# 4. 启动应用
streamlit run app.py
```

## 配置说明

编辑 `.env` 文件：

```bash
# LLM 提供商: openai 或 claude
LLM_PROVIDER=openai

# OpenAI 配置
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4o

# 搜索 API
BRAVE_API_KEY=BSA-xxx
```

## 项目结构

```
PaperGuide/
├── app.py              # Streamlit 主入口
├── config.py           # 配置管理
├── core/               # 核心模块
│   ├── agent.py        # Agent 主逻辑
│   ├── pdf_parser.py   # PDF 解析
│   ├── arxiv_downloader.py  # arXiv 下载
│   ├── llm_client.py   # LLM 客户端
│   └── search/         # 搜索模块
├── prompts/            # 提示词模板
├── templates/          # MD 模板
└── outputs/            # 输出目录
```

## License

MIT

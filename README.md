# PaperGuide 📄

帮助任何人（哪怕对领域一无所知）通过与AI对话，理解论文核心，同时学习论文省略的背景知识。

## 与其他 AI 读论文工具的区别

大多数 AI 读论文工具是**对话式问答**——你问一句，AI 答一句，聊完就没了。

PaperGuide 不同：

| 传统工具 | PaperGuide |
|---------|------------|
| 对话完就没了 | 生成**持久化的 Markdown 文档** |
| 问什么答什么 | **主动补充**论文省略的背景知识 |
| 每次从头问 | 文档**动态更新**，越聊越完善 |
| 产出是对话记录 | 产出是**完整的知识文档** |

**核心理念**：对话只是过程，最终产出是一份**零基础也能看懂的论文解读文档**。

```
你：这个 RoPE 是什么？
AI：[简短回答]
    ↓
  自动更新 review.md，添加 RoPE 的详细解释
    ↓
你：那 Flow Matching 呢？
AI：[简短回答]
    ↓
  继续更新 review.md...
    ↓
最终：一份完整的、逻辑清晰的论文解读文档
```

## 功能特点

- **PDF/arXiv 支持** - 上传PDF或输入arXiv链接
- **智能解读** - 自动生成结构化的论文解读
- **知识补充** - 通过网络搜索补充论文省略的背景知识
- **对话问答** - 不懂的地方随时问，AI实时解答
- **文档更新** - 对话中的重要知识会更新到解读文档
- **会话持久化** - 历史记录保留，下次可继续对话

## 快速开始

### 前置要求

- Python 3.11+
- [OpenClaw](https://github.com/anthropics/openclaw) - AI Agent 框架

### 安装

```bash
# 1. 克隆项目
git clone https://github.com/yourusername/PaperGuide.git
cd PaperGuide

# 2. 创建conda环境
conda create -n paperguide python=3.11 -y
conda activate paperguide

# 3. 安装依赖
pip install -r requirements.txt

# 4. 注册 OpenClaw Agent
openclaw agents add paperguide \
  --workspace ./agent_workspace \
  --model claude-proxy/claude-opus-4-5

# 5. 启动应用
streamlit run app.py
```

## 项目结构

```
PaperGuide/
├── app.py                      # Streamlit 主应用
├── agent_workspace/            # OpenClaw Agent 工作区
│   ├── IDENTITY.md             # Agent 身份定义
│   ├── SOUL.md                 # 核心行为规范
│   ├── AGENTS.md               # 工作流程定义
│   ├── skills/
│   │   └── paper-explainer/    # 论文解读技能
│   │       └── SKILL.md
│   ├── uploads/                # 用户上传的 PDF
│   └── outputs/                # 生成的解读文档
│       └── {paper_id}/
│           ├── review.md       # 论文解读
│           └── session.json    # 对话历史
├── docs/                       # 项目文档
└── logs/                       # 日志目录
```

## 技术架构

```
┌─────────────────────────────────────────────────┐
│              Streamlit UI (app.py)              │
│  ┌─────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │ PDF上传 │  │ 文档展示    │  │ 对话问答    │  │
│  └─────────┘  └─────────────┘  └─────────────┘  │
└──────────────────────┬──────────────────────────┘
                       │ subprocess
                       ▼
┌─────────────────────────────────────────────────┐
│     OpenClaw Agent (paperguide)                 │
│  • 使用 paper-explainer skill                   │
│  • 支持工具调用、网络搜索                       │
│  • 自动处理 PDF 解析                            │
└─────────────────────────────────────────────────┘
```

## License

MIT License

Copyright (c) 2025 PaperGuide

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

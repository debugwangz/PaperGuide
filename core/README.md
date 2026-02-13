# Core 模块

包含 PaperGuide 的核心业务逻辑。

## 模块说明

| 文件 | 功能 |
|------|------|
| `agent.py` | Agent 主逻辑，协调各模块完成论文分析和对话 |
| `pdf_parser.py` | PDF 解析，提取文本、章节、图片 |
| `arxiv_downloader.py` | arXiv 论文下载 |
| `llm_client.py` | LLM 客户端，支持 OpenAI 和 Claude |
| `search/` | 网络搜索模块（解耦设计） |

## 使用示例

```python
from core.agent import PaperGuideAgent

agent = PaperGuideAgent()
agent.set_user_background("计算机本科生")
agent.load_pdf("paper.pdf")  # 或 agent.load_arxiv("2401.12345")
review = agent.analyze_paper()
response = agent.chat("这个方法为什么有效？")
```

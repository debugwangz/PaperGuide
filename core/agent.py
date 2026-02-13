"""PaperGuide Agent core logic.

Handles paper analysis, conversation, and MD generation/updates.
"""
import json
from pathlib import Path
from dataclasses import dataclass, field
from .pdf_parser import parse_pdf, ParsedPaper
from .arxiv_downloader import download_arxiv_paper
from .search import get_search_provider
from .llm_client import get_llm_provider, LLMProvider
from config import get_settings


@dataclass
class Session:
    """Session state for a paper analysis."""
    user_background: str = "完全的新手，对领域一无所知"
    key_questions: list[str] = field(default_factory=list)
    clarified_concepts: list[str] = field(default_factory=list)
    pending_gaps: list[str] = field(default_factory=list)
    conversation_history: list[dict] = field(default_factory=list)


class PaperGuideAgent:
    """Main agent for paper analysis and conversation."""

    def __init__(self, output_dir: Path | None = None):
        settings = get_settings()
        self.output_dir = output_dir or Path(settings.output_dir)
        self.llm = get_llm_provider()
        self.search = get_search_provider(settings.search_provider)
        self.paper: ParsedPaper | None = None
        self.review_md: str = ""
        self.session = Session()
        self.paper_dir: Path | None = None

    def _load_prompt(self, name: str, **kwargs) -> str:
        """Load and format a prompt template."""
        prompt_path = Path(__file__).parent.parent / "prompts" / f"{name}.md"
        content = prompt_path.read_text(encoding="utf-8")
        for key, value in kwargs.items():
            content = content.replace(f"{{{key}}}", str(value))
        return content

    def _save_session(self):
        """Save session state to JSON."""
        if self.paper_dir:
            session_path = self.paper_dir / "session.json"
            session_path.write_text(json.dumps({
                "user_background": self.session.user_background,
                "key_questions": self.session.key_questions,
                "clarified_concepts": self.session.clarified_concepts,
                "pending_gaps": self.session.pending_gaps,
            }, ensure_ascii=False, indent=2), encoding="utf-8")

    def _save_review(self):
        """Save review MD to file."""
        if self.paper_dir:
            review_path = self.paper_dir / "review.md"
            review_path.write_text(self.review_md, encoding="utf-8")

    def set_user_background(self, background: str):
        """Set user background information."""
        self.session.user_background = background if background else "完全的新手，对领域一无所知"

    def load_pdf(self, pdf_path: str | Path) -> ParsedPaper:
        """Load and parse a PDF file."""
        pdf_path = Path(pdf_path)
        paper_name = pdf_path.stem
        self.paper_dir = self.output_dir / paper_name
        self.paper_dir.mkdir(parents=True, exist_ok=True)
        images_dir = self.paper_dir / "images"
        self.paper = parse_pdf(pdf_path, images_dir)
        return self.paper

    def load_arxiv(self, url_or_id: str) -> ParsedPaper | None:
        """Download and parse an arXiv paper."""
        arxiv_paper = download_arxiv_paper(url_or_id, self.output_dir)
        if not arxiv_paper or not arxiv_paper.pdf_path:
            return None
        return self.load_pdf(arxiv_paper.pdf_path)

    def _extract_key_content(self, max_chars: int = 30000) -> str:
        """智能提取论文关键内容，优先保留重要章节。"""
        if not self.paper:
            return ""

        # 如果没有解析出章节，直接截断
        if not self.paper.sections:
            return self.paper.full_text[:max_chars]

        # 定义章节优先级（越小越重要）
        priority = {
            "abstract": 1,
            "introduction": 2,
            "method": 3, "methodology": 3, "methods": 3, "approach": 3,
            "conclusion": 4, "conclusions": 4,
            "experiment": 5, "experiments": 5, "results": 5,
            "related work": 6, "background": 6,
            "discussion": 7,
        }

        # 按优先级排序章节
        def get_priority(section):
            title_lower = section.title.lower()
            for key, prio in priority.items():
                if key in title_lower:
                    return prio
            return 99  # 其他章节最低优先级

        sorted_sections = sorted(self.paper.sections, key=get_priority)

        # 按优先级累加，直到达到字符限制
        content_parts = []
        current_len = 0

        for section in sorted_sections:
            section_text = f"\n## {section.title}\n\n{section.content}\n"
            if current_len + len(section_text) > max_chars:
                # 如果是高优先级章节，截断也要加入
                if get_priority(section) <= 5:
                    remaining = max_chars - current_len
                    if remaining > 500:  # 至少保留 500 字符
                        content_parts.append(section_text[:remaining] + "\n... (内容过长已截断)")
                break
            content_parts.append(section_text)
            current_len += len(section_text)

        # 如果没提取到任何章节，回退到全文截断
        if not content_parts:
            return self.paper.full_text[:max_chars]

        return "".join(content_parts)

    def analyze_paper(self) -> str:
        """Analyze the loaded paper and generate initial review MD."""
        if not self.paper:
            raise ValueError("No paper loaded")

        # 智能提取关键内容
        paper_content = self._extract_key_content(max_chars=30000)

        # Prepare prompt
        system_prompt = self._load_prompt(
            "system",
            user_background=self.session.user_background
        )
        analysis_prompt = self._load_prompt(
            "paper_analysis",
            title=self.paper.title,
            paper_content=paper_content,
            user_background=self.session.user_background
        )

        # Generate analysis
        self.review_md = self.llm.generate(system_prompt, analysis_prompt)
        self._save_review()
        self._save_session()
        return self.review_md

    def chat(self, user_message: str) -> dict:
        """Handle user chat message and return response with update suggestion.

        Returns:
            dict: {
                "answer": str,           # AI 的回答
                "should_update": bool,   # 是否需要更新文档
                "update_section": str,   # 更新的章节名（可选）
                "update_content": str,   # 更新的内容（可选）
            }
        """
        if not self.paper:
            return {"answer": "请先上传论文或输入arXiv链接", "should_update": False}

        # Add to conversation history
        self.session.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        self.session.key_questions.append(user_message)

        # Build context - 让 AI 同时回答问题和判断是否需要更新文档
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[Chat] review_md 长度: {len(self.review_md)} 字符")
        if len(self.review_md) < 100:
            logger.warning(f"[Chat] review_md 可能为空或太短！内容: {self.review_md[:200]}")

        system_prompt = self._load_prompt(
            "system",
            user_background=self.session.user_background
        )
        context = f"""## 当前 Review 文档

{self.review_md}

## 用户问题

{user_message}

## 任务

请完成两件事：

### 1. 回答用户问题（answer 字段）

**要求**：
- 直接回答问题，不要说"我来解释"、"让我讲一下"这种元描述
- 简洁清晰，3-5 句话

**错误示范（❌ 元描述）**：
"你说得对，我会把这个概念讲清楚的。"

**正确示范（✅ 直接回答）**：
"Flow Matching 通过学习一个速度场来生成图片。速度场告诉模型在每个时刻应该怎么调整图片，从纯噪声一步步变成清晰图片。"

### 2. 更新文档（update_content 字段）

**如果用户的问题涉及 Review 文档中解释不够详细的内容**，则需要更新文档。

**update_content 的质量要求**（非常重要！）：

每个概念必须包含：

1. **一句话定义** — 用最简单的话解释，不用其他术语
2. **类比** — 用生活中的例子让人秒懂
3. **为什么重要** — 在本文中的作用，不懂会怎样
4. **具体例子** — 代码或数学（标注可跳过）
5. **常见误区** — 容易搞错的地方（如果有）

**错误示范（❌ 太简略）**：
```markdown
### ODE
ODE 是常微分方程，用来描述变量随时间的变化。
```

**正确示范（✅ 详细丰富）**：
```markdown
### ODE（常微分方程）

**一句话**：描述"确定性变化"的数学工具。

**类比**：坐地铁。你在 A 站上车，沿着固定轨道行驶，一定会到达 B 站。无论坐多少次，路线都完全一样。

**为什么重要**：Flow Matching 用 ODE 来描述从噪声到图片的过程。理解 ODE 才能理解为什么原始模型是"确定性"的，无法做强化学习的"探索"。

**数学形式（可跳过）**：
$dx/dt = v(x, t)$

意思是：位置 $x$ 的变化速度等于速度场 $v$。给定初始位置，整个轨迹就确定了。

**和 SDE 的关键区别**：ODE 是确定的（同样起点永远同样终点），SDE 有随机性（同样起点可能不同终点）。
```

## 输出格式

```json
{{
    "answer": "直接回答问题（不要元描述）",
    "should_update": true或false,
    "update_section": "要更新的章节名",
    "update_content": "详细丰富的内容（按上述格式，包含：一句话定义、类比、为什么重要、具体例子）"
}}
```

只输出 JSON，不要其他内容。"""

        # Generate response
        raw_response = self.llm.generate(system_prompt, context)

        # Parse JSON response
        import logging
        import re
        logger = logging.getLogger(__name__)
        logger.info(f"[Chat] 原始响应长度: {len(raw_response)} 字符")

        result = None
        try:
            # 提取 JSON
            if "```" in raw_response:
                json_str = raw_response.split("```")[1]
                if json_str.startswith("json"):
                    json_str = json_str[4:]
                json_str = json_str.strip()
            else:
                json_str = raw_response.strip()

            result = json.loads(json_str)
            logger.info(f"[Chat] JSON 解析成功")
        except (json.JSONDecodeError, IndexError) as e:
            logger.warning(f"[Chat] 标准 JSON 解析失败: {e}，尝试正则提取")

            # 尝试用正则提取各字段
            try:
                answer_match = re.search(r'"answer"\s*:\s*"(.*?)"\s*,\s*"should_update"', json_str, re.DOTALL)
                should_update_match = re.search(r'"should_update"\s*:\s*(true|false)', json_str, re.IGNORECASE)

                if answer_match and should_update_match:
                    answer = answer_match.group(1).replace('\\n', '\n').replace('\\"', '"')
                    should_update = should_update_match.group(1).lower() == 'true'

                    result = {
                        "answer": answer,
                        "should_update": should_update,
                    }

                    if should_update:
                        section_match = re.search(r'"update_section"\s*:\s*"(.*?)"', json_str, re.DOTALL)
                        if section_match:
                            result["update_section"] = section_match.group(1)

                        # update_content 提取：找到 "update_content": " 后面的所有内容直到最后
                        content_start = json_str.find('"update_content"')
                        if content_start != -1:
                            # 找到 : " 的位置
                            colon_pos = json_str.find(':', content_start)
                            if colon_pos != -1:
                                # 找到第一个引号
                                quote_start = json_str.find('"', colon_pos + 1)
                                if quote_start != -1:
                                    # 从引号后到最后一个 " 之前（去掉结尾的 "\n}）
                                    content = json_str[quote_start + 1:]
                                    # 去掉结尾的 "\n} 或 "}
                                    content = content.rstrip()
                                    if content.endswith('}'):
                                        content = content[:-1].rstrip()
                                    if content.endswith('"'):
                                        content = content[:-1]
                                    result["update_content"] = content.replace('\\n', '\n').replace('\\"', '"')
                                    logger.info(f"[Chat] update_content 提取成功，长度: {len(content)}")

                        if "update_content" not in result:
                            logger.warning(f"[Chat] update_content 提取失败，json_str 末尾: {json_str[-200:]}")

                    logger.info(f"[Chat] 正则提取成功")
            except Exception as regex_error:
                logger.error(f"[Chat] 正则提取也失败: {regex_error}")

        # 最终回退
        if result is None:
            logger.error(f"[Chat] 所有解析方法都失败，返回原始响应")
            result = {"answer": raw_response, "should_update": False}

        logger.info(f"[Chat] should_update: {result.get('should_update')}")
        logger.info(f"[Chat] answer 长度: {len(result.get('answer', ''))} 字符")
        logger.info(f"[Chat] update_content 长度: {len(result.get('update_content', ''))} 字符")

        # Add to history
        self.session.conversation_history.append({
            "role": "assistant",
            "content": result.get("answer", raw_response)
        })

        self._save_session()
        return result

    def check_should_update(self, user_question: str, response: str) -> dict:
        """Check if MD should be updated based on conversation."""
        prompt = self._load_prompt(
            "md_update",
            current_review=self.review_md,
            user_question=user_question,
            agent_response=response
        )
        system_prompt = "你是一个判断是否需要更新文档的助手。只输出JSON，不要其他内容。"

        try:
            result = self.llm.generate(system_prompt, prompt)
            # Extract JSON
            if "```" in result:
                result = result.split("```")[1]
                if result.startswith("json"):
                    result = result[4:]
            return json.loads(result.strip())
        except (json.JSONDecodeError, IndexError):
            return {"should_update": False, "reason": "解析失败"}

    def update_review(self, section: str, content: str):
        """Update a section of the review MD."""
        # Simple append for now
        self.review_md += f"\n\n### 补充: {section}\n\n{content}"
        self._save_review()

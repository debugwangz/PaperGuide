"""PaperGuide - Streamlit Web Application.

使用 OpenClaw 作为后端 Agent 处理论文解读。
"""
import streamlit as st
import subprocess
import json
import uuid
import re
import time
import logging

from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("PaperGuide")

# 配置
WORKSPACE = Path(__file__).parent / "agent_workspace"
UPLOADS_DIR = WORKSPACE / "uploads"
OUTPUTS_DIR = WORKSPACE / "outputs"

# 确保目录存在
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
logger.info("PaperGuide 启动，工作目录: %s", WORKSPACE)


def extract_paper_id(filename: str = None, arxiv_input: str = None) -> str:
    """从文件名或 arXiv 输入提取论文 ID 作为目录名"""
    if filename:
        # 去掉 .pdf 后缀，清理特殊字符
        name = Path(filename).stem
        # 替换空格和特殊字符为下划线
        name = re.sub(r'[\s\-]+', '_', name)
        name = re.sub(r'[^\w_]', '', name)
        return name[:50]  # 限制长度

    if arxiv_input:
        # 提取 arXiv ID，支持多种格式
        # https://arxiv.org/abs/2512.03041 -> 2512.03041
        # arxiv:2512.03041 -> 2512.03041
        # 2512.03041 -> 2512.03041
        match = re.search(r'(\d{4}\.\d{4,5})', arxiv_input)
        if match:
            return f"arxiv_{match.group(1)}"
        # 如果没匹配到，清理输入作为 ID
        clean = re.sub(r'[^\w]', '_', arxiv_input)
        return clean[:50]

    return str(uuid.uuid4())[:8]


def save_session(paper_id: str, messages: list, session_id: str):
    """保存会话到文件"""
    if not paper_id:
        return
    session_dir = OUTPUTS_DIR / paper_id
    session_dir.mkdir(parents=True, exist_ok=True)
    session_file = session_dir / "session.json"
    data = {
        "session_id": session_id,
        "messages": messages
    }
    session_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def load_session(paper_id: str) -> dict:
    """加载会话"""
    session_file = OUTPUTS_DIR / paper_id / "session.json"
    if session_file.exists():
        return json.loads(session_file.read_text(encoding="utf-8"))
    return {"session_id": str(uuid.uuid4())[:8], "messages": []}



def get_agent_model() -> str:
    """从 OpenClaw 获取 paperguide agent 的模型信息"""
    try:
        result = subprocess.run(
            ["openclaw", "agents", "list"],
            capture_output=True, text=True, timeout=10
        )
        in_paperguide = False
        for line in result.stdout.split("\n"):
            if "- paperguide" in line:
                in_paperguide = True
            elif line.startswith("- ") and "paperguide" not in line:
                in_paperguide = False
            elif in_paperguide and "Model:" in line:
                return line.split("Model:")[-1].strip()
    except Exception:
        pass
    return "unknown"


def list_papers() -> list:
    """列出所有已分析的论文，返回 (paper_id, title) 列表"""
    papers = []
    if OUTPUTS_DIR.exists():
        for d in sorted(OUTPUTS_DIR.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
            if d.is_dir() and (d / "review.md").exists():
                # 尝试从 review.md 提取标题
                title = d.name  # 默认用目录名
                review_path = d / "review.md"
                try:
                    content = review_path.read_text(encoding="utf-8")
                    # 提取第一行 # 开头的标题
                    for line in content.split("\n"):
                        line = line.strip()
                        if line.startswith("# "):
                            title = line[2:].strip()
                            # 截断过长的标题
                            if len(title) > 40:
                                title = title[:37] + "..."
                            break
                except:
                    pass
                papers.append((d.name, title))
    return papers

# Page config
st.set_page_config(
    page_title="PaperGuide",
    page_icon="📄",
    layout="wide"
)


def call_openclaw_stream(message: str, session_id: str, status_placeholder) -> str:
    """通过 OpenClaw CLI 调用 agent，流式输出"""
    logger.info("流式调用 OpenClaw: session=%s, message=%s", session_id, message[:80])
    try:
        process = subprocess.Popen(
            [
                "openclaw", "agent",
                "--local",
                "--agent", "paperguide",
                "--session-id", session_id,
                "--message", message
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=str(WORKSPACE)
        )

        output_lines = []
        status_lines = []  # 状态信息（工具调用等）

        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                # 过滤插件注册日志
                if "[plugins]" in line or "feishu_" in line:
                    continue
                # 工具调用日志显示为状态
                if line.startswith("[tools]"):
                    logger.info("工具调用: %s", line.strip())
                    status_lines.append(line.strip())
                    status_placeholder.info("\n".join(status_lines[-3:]))
                else:
                    output_lines.append(line)
                    # 实时更新输出
                    status_placeholder.markdown("".join(output_lines))

        process.wait()
        if process.returncode != 0:
            logger.error("OpenClaw 流式调用失败, returncode=%d", process.returncode)
            st.error(f"OpenClaw 错误 (code {process.returncode})")
            return ""

        logger.info("流式调用完成，输出 %d 行", len(output_lines))
        return "".join(output_lines).strip()

    except Exception as e:
        logger.exception("流式调用异常")
        st.error(f"调用失败: {str(e)}")
        return ""


def call_openclaw(message: str, session_id: str) -> str:
    """通过 OpenClaw CLI 调用 agent（阻塞式，用于初始分析）"""
    logger.info("阻塞式调用 OpenClaw: session=%s, message=%s", session_id, message[:80])
    try:
        result = subprocess.run(
            [
                "openclaw", "agent",
                "--local",
                "--agent", "paperguide",
                "--session-id", session_id,
                "--message", message,
                "--json"
            ],
            capture_output=True,
            text=True,
            timeout=600,
            cwd=str(WORKSPACE)
        )

        if result.returncode != 0:
            logger.error("OpenClaw 阻塞调用失败: returncode=%d, stderr=%s", result.returncode, result.stderr[:200])
            st.error(f"OpenClaw 错误: {result.stderr}")
            return ""

        logger.info("阻塞调用完成，stdout 长度: %d", len(result.stdout))

        # 解析 JSON 响应
        try:
            data = json.loads(result.stdout)
            payloads = data.get("payloads", [])
            if payloads:
                return payloads[0].get("text", "")
        except json.JSONDecodeError:
            # 可能输出包含日志前缀，尝试找到 JSON 部分
            stdout = result.stdout
            json_start = stdout.find('{')
            if json_start != -1:
                try:
                    data = json.loads(stdout[json_start:])
                    payloads = data.get("payloads", [])
                    if payloads:
                        return payloads[0].get("text", "")
                except:
                    pass
            return stdout

        return ""
    except subprocess.TimeoutExpired:
        logger.error("阻塞调用超时（600秒）")
        st.error("请求超时，请重试")
        return ""
    except Exception as e:
        logger.exception("阻塞调用异常")
        st.error(f"调用失败: {str(e)}")
        return ""


def get_review_content(paper_id: str) -> str:
    """读取 Agent 生成的 review 文件"""
    review_path = OUTPUTS_DIR / paper_id / "review.md"
    if review_path.exists():
        return review_path.read_text(encoding="utf-8")
    return ""


def main():
    st.title("📄 PaperGuide")
    st.caption("帮助任何人理解学术论文 | Powered by OpenClaw")
    st.caption(f"🤖 {get_agent_model()} via OpenClaw")

    # Initialize session state
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())[:8]
    if "paper_id" not in st.session_state:
        st.session_state.paper_id = None  # 论文 ID，用于目录名
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "paper_loaded" not in st.session_state:
        st.session_state.paper_loaded = False
    if "review_md" not in st.session_state:
        st.session_state.review_md = ""

    # Sidebar
    with st.sidebar:
        st.header("📤 上传论文")

        # PDF upload
        uploaded_file = st.file_uploader(
            "上传 PDF 文件",
            type=["pdf"],
            help="支持 PDF 格式的学术论文"
        )

        # arXiv input
        arxiv_input = st.text_input(
            "或输入 arXiv 链接/ID",
            placeholder="例如: 2401.12345 或 https://arxiv.org/abs/2401.12345"
        )

        # User background
        user_background = st.text_area(
            "你的背景（可选）",
            placeholder="例如：计算机本科生，了解基础机器学习",
            help="帮助 AI 调整解释的深度"
        )

        # Analyze button
        if st.button("🔍 开始分析", type="primary", use_container_width=True):
            # 新论文分析时生成新的 session_id
            session_id = str(uuid.uuid4())[:8]
            st.session_state.session_id = session_id

            with st.spinner("正在分析论文..."):
                if uploaded_file:
                    # 提取论文 ID 作为目录名
                    paper_id = extract_paper_id(filename=uploaded_file.name)
                    st.session_state.paper_id = paper_id
                    logger.info("上传 PDF: %s, paper_id=%s", uploaded_file.name, paper_id)

                    # 保存上传的 PDF
                    pdf_path = UPLOADS_DIR / f"{paper_id}.pdf"
                    pdf_path.write_bytes(uploaded_file.read())

                    # 构建消息（包含 paper_id 以便 agent 知道输出目录）
                    background_info = f"\n\n用户背景：{user_background}" if user_background else ""
                    message = f"[paper_id: {paper_id}]\n请解读这篇论文：{pdf_path}{background_info}"

                elif arxiv_input:
                    # 提取 arXiv ID 作为目录名
                    paper_id = extract_paper_id(arxiv_input=arxiv_input)
                    st.session_state.paper_id = paper_id
                    logger.info("arXiv 输入: %s, paper_id=%s", arxiv_input, paper_id)

                    background_info = f"\n\n用户背景：{user_background}" if user_background else ""
                    message = f"[paper_id: {paper_id}]\n请解读这篇论文（arXiv: {arxiv_input}）{background_info}"

                else:
                    st.warning("请先上传 PDF 或输入 arXiv 链接")
                    return

                # 调用 OpenClaw
                response = call_openclaw(message, session_id)

                if response:
                    logger.info("分析完成, paper_id=%s", paper_id)
                    # 从文件读取完整的 review 内容（不是用 response）
                    review_content = get_review_content(paper_id)
                    if review_content:
                        st.session_state.review_md = review_content
                    else:
                        # 如果文件还没生成，用 response 作为临时内容
                        st.session_state.review_md = response
                    st.session_state.paper_loaded = True
                    st.session_state.messages = []
                    # 保存初始会话
                    save_session(paper_id, [], session_id)
                    st.success("分析完成！")
                    st.rerun()

        # 新建会话
        if st.button("🔄 新建会话", use_container_width=True):
            st.session_state.session_id = str(uuid.uuid4())[:8]
            st.session_state.paper_id = None
            st.session_state.messages = []
            st.session_state.paper_loaded = False
            st.session_state.review_md = ""
            st.rerun()

        # 历史记录
        st.divider()
        st.header("📚 历史记录")
        papers = list_papers()
        if papers:
            for paper_id, title in papers:
                col1, col2 = st.columns([4, 1])
                with col1:
                    if st.button(f"📄 {title}", key=f"history_{paper_id}", use_container_width=True):
                        # 加载历史会话
                        session_data = load_session(paper_id)
                        st.session_state.session_id = session_data.get("session_id", str(uuid.uuid4())[:8])
                        st.session_state.paper_id = paper_id
                        st.session_state.messages = session_data.get("messages", [])
                        st.session_state.review_md = get_review_content(paper_id)
                        st.session_state.paper_loaded = True
                        # 重置处理状态
                        st.session_state.is_processing = False
                        st.session_state.processing_start_time = None
                        st.rerun()
                with col2:
                    if st.button("🗑️", key=f"delete_{paper_id}", help="删除此记录"):
                        import shutil
                        shutil.rmtree(OUTPUTS_DIR / paper_id, ignore_errors=True)
                        st.rerun()
        else:
            st.caption("暂无历史记录")

    # Main content
    if st.session_state.paper_loaded:
        # Two columns: Review and Chat
        col1, col2 = st.columns([1, 1])

        with col1:
            st.header("📝 论文解读")

            # 尝试从文件读取最新内容
            if st.session_state.paper_id:
                file_review = get_review_content(st.session_state.paper_id)
                if file_review:
                    st.session_state.review_md = file_review

            # 使用 unsafe_allow_html 支持锚点跳转
            st.markdown(st.session_state.review_md, unsafe_allow_html=True)

        with col2:
            st.header("💬 问答对话")
            render_chat()
    else:
        # Welcome message
        st.info("👈 请在左侧上传 PDF 或输入 arXiv 链接开始分析")
        st.markdown("""
        ### 使用说明

        1. **上传论文** - 支持 PDF 文件或 arXiv 链接
        2. **填写背景** - 帮助 AI 调整解释深度（可选）
        3. **开始分析** - AI 会生成论文解读
        4. **对话问答** - 有不懂的随时问

        ### 特点

        - 🎯 **零基础友好** - 假设你对领域一无所知
        - 🔗 **逻辑清晰** - 每个概念都有动机和类比
        - 📚 **补充知识** - 自动填补论文省略的背景
        - 💬 **对话式** - 随时提问，实时更新文档
        """)


def render_chat():
    """Render chat interface."""
    # 初始化状态
    if "is_processing" not in st.session_state:
        st.session_state.is_processing = False
    if "processing_start_time" not in st.session_state:
        st.session_state.processing_start_time = None

    # 超时检测（120秒）
    TIMEOUT_SECONDS = 120
    if st.session_state.is_processing and st.session_state.processing_start_time:
        elapsed = time.time() - st.session_state.processing_start_time
        if elapsed > TIMEOUT_SECONDS:
            st.session_state.is_processing = False
            st.session_state.processing_start_time = None
            st.error(f"请求超时（{TIMEOUT_SECONDS}秒），请重试")

    # 消息容器
    messages_container = st.container()

    # Chat input（始终在最底部，处理中时禁用）
    prompt = st.chat_input(
        "有什么不懂的？问我吧..." if not st.session_state.is_processing else "等待回复中...",
        disabled=st.session_state.is_processing
    )

    # 在消息容器中显示内容
    with messages_container:
        # 显示历史消息
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # 如果正在处理，流式获取响应
        if st.session_state.is_processing:
            with st.chat_message("assistant"):
                # 创建一个 placeholder 用于流式更新
                status_placeholder = st.empty()
                status_placeholder.info("思考中...")

                # 获取要发送的消息（可能包含章节上下文）
                message_to_send = st.session_state.get(
                    "full_message_to_send",
                    st.session_state.messages[-1]["content"]
                )
                response = call_openclaw_stream(
                    message_to_send,
                    st.session_state.session_id,
                    status_placeholder
                )

                # 清空 placeholder，显示最终结果
                status_placeholder.empty()
                st.markdown(response)

            # 清理临时变量
            if "full_message_to_send" in st.session_state:
                del st.session_state.full_message_to_send

            # 保存 AI 响应
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.session_state.is_processing = False
            st.session_state.processing_start_time = None

            # 保存会话
            if st.session_state.paper_id:
                save_session(
                    st.session_state.paper_id,
                    st.session_state.messages,
                    st.session_state.session_id
                )

                # 检查是否有文档更新
                new_review = get_review_content(st.session_state.paper_id)
                if new_review and new_review != st.session_state.review_md:
                    st.session_state.review_md = new_review
                    st.toast("📝 文档已更新", icon="✅")

            st.rerun()

    # 处理用户输入
    if prompt and not st.session_state.is_processing:
        logger.info("用户提问: %s", prompt[:80])
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.full_message_to_send = prompt
        st.session_state.is_processing = True
        st.session_state.processing_start_time = time.time()
        st.rerun()


if __name__ == "__main__":
    main()

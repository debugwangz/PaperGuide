"""模拟实际论文分析调用"""
import time
import httpx
from pathlib import Path
from anthropic import Anthropic

# 配置
BASE_URL = "https://yunyi.cfd/claude"
API_KEY = "DNQG1JV5-8FT7-ZE5R-T5NG-SH7M42KV374H"
MODEL = "claude-opus-4-5"

# 读取实际 prompt
system_prompt = Path('prompts/system.md').read_text(encoding='utf-8')
analysis_template = Path('prompts/paper_analysis.md').read_text(encoding='utf-8')

# 模拟论文内容（30000 字符）
fake_paper = "这是一篇关于深度学习的论文。" * 1000 + \
    "\n## Abstract\n本文提出了一种新的方法..." * 100 + \
    "\n## Method\n我们的方法基于..." * 100
fake_paper = fake_paper[:30000]

# 替换变量
user_prompt = analysis_template.replace('{title}', '测试论文标题')
user_prompt = user_prompt.replace('{paper_content}', fake_paper)
user_prompt = user_prompt.replace('{user_background}', '计算机本科生')

print(f"System prompt 长度: {len(system_prompt)} 字符")
print(f"User prompt 长度: {len(user_prompt)} 字符")
print(f"总长度: {len(system_prompt) + len(user_prompt)} 字符")
print()

client = Anthropic(
    api_key=API_KEY,
    base_url=BASE_URL,
    timeout=httpx.Timeout(600.0, connect=30.0),
    max_retries=2,
)

print("开始调用 Claude API...")
start = time.time()

try:
    response = client.messages.create(
        model=MODEL,
        max_tokens=8192,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}]
    )
    elapsed = time.time() - start
    print(f"\n✅ 成功! 耗时: {elapsed:.1f}秒")
    print(f"响应长度: {len(response.content[0].text)} 字符")
    print(f"\n响应预览:\n{response.content[0].text[:500]}...")
except Exception as e:
    elapsed = time.time() - start
    print(f"\n❌ 失败! 耗时: {elapsed:.1f}秒")
    print(f"错误类型: {type(e).__name__}")
    print(f"错误信息: {e}")

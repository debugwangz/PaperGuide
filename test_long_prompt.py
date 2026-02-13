"""测试长 prompt 是否能成功"""
import time
import httpx
from anthropic import Anthropic

# 配置
BASE_URL = "https://yunyi.cfd/claude"
API_KEY = "DNQG1JV5-8FT7-ZE5R-T5NG-SH7M42KV374H"
MODEL = "claude-opus-4-5"

# 构造不同长度的 prompt
short_prompt = "请用一句话介绍什么是机器学习"
medium_prompt = "请详细解释什么是机器学习，包括监督学习、无监督学习、强化学习的区别" + "请举例说明" * 100
long_prompt = "这是一篇关于机器学习的论文，请帮我分析。" + "内容" * 5000  # 约 2 万字符

client = Anthropic(
    api_key=API_KEY,
    base_url=BASE_URL,
    timeout=httpx.Timeout(600.0, connect=30.0),
    max_retries=2,
)

def test_prompt(name: str, prompt: str):
    print(f"\n{'='*50}")
    print(f"测试: {name}")
    print(f"Prompt 长度: {len(prompt)} 字符")
    print("="*50)

    start = time.time()
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=500,  # 限制输出长度
            messages=[{"role": "user", "content": prompt}]
        )
        elapsed = time.time() - start
        print(f"✅ 成功! 耗时: {elapsed:.1f}秒")
        print(f"响应长度: {len(response.content[0].text)} 字符")
        print(f"响应预览: {response.content[0].text[:100]}...")
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ 失败! 耗时: {elapsed:.1f}秒")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {e}")

if __name__ == "__main__":
    # 先测短的
    test_prompt("短 prompt", short_prompt)

    # 再测中等
    test_prompt("中等 prompt", medium_prompt)

    # 最后测长的
    test_prompt("长 prompt", long_prompt)

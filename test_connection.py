"""测试 LLM API 连接"""
import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 50)
print("测试 Claude 代理 API (yunyi.cfd)")
print("=" * 50)

# 使用参考脚本中的配置
BASE_URL = "https://yunyi.cfd/claude"
API_KEY = "DNQG1JV5-8FT7-ZE5R-T5NG-SH7M42KV374H"
MODEL = "claude-opus-4-5"

print(f"  BASE_URL: {BASE_URL}")
print(f"  MODEL: {MODEL}")
print("=" * 50)

print("\n测试 Claude API...")
from anthropic import Anthropic
try:
    client = Anthropic(
        api_key=API_KEY,
        base_url=BASE_URL,
    )
    response = client.messages.create(
        model=MODEL,
        max_tokens=50,
        messages=[{"role": "user", "content": "说 hello"}]
    )
    print(f"✅ 连接成功!")
    print(f"   响应: {response.content[0].text}")
except Exception as e:
    print(f"❌ 连接失败: {type(e).__name__}")
    print(f"   错误: {e}")

"""测试 JSON 解析 - 模拟真实换行符"""
import json
import re

# 模拟实际返回的响应（有真实换行符，不是 \n 转义）
raw_response = '''```json
{
    "answer": "你说得对，前置知识确实太简略了。",
    "should_update": true,
    "update_section": "3. 前置知识",
    "update_content": "## 3. 前置知识

### 3.1 什么是图像生成？

**一句话**：AI 画画。

**类比**：画家。"
}
```'''

print("测试1: 有真实换行符的 JSON")
print("原始响应长度:", len(raw_response))
print("="*50)

# 提取 JSON 字符串
if "```" in raw_response:
    json_str = raw_response.split("```")[1]
    if json_str.startswith("json"):
        json_str = json_str[4:]
    json_str = json_str.strip()
else:
    json_str = raw_response.strip()

# 方法1: 直接解析
print("\n方法1: 直接 json.loads")
try:
    result = json.loads(json_str)
    print("✅ 成功!")
except Exception as e:
    print(f"❌ 失败: {e}")

# 方法2: 先替换真实换行符为转义换行符
print("\n方法2: 替换换行符后解析")
try:
    # 在字符串值内部，真实换行符需要变成 \n
    # 但要小心不要替换 JSON 结构的换行
    # 简单方法：把整个字符串的换行都替换
    fixed_json = json_str.replace('\n', '\\n')
    result = json.loads(fixed_json)
    print("✅ 成功!")
    print(f"  answer: {result.get('answer')}")
except Exception as e:
    print(f"❌ 失败: {e}")

# 方法3: 用正则提取
print("\n方法3: 正则提取")
try:
    answer_match = re.search(r'"answer"\s*:\s*"(.*?)"\s*,\s*"should_update"', json_str, re.DOTALL)
    should_update_match = re.search(r'"should_update"\s*:\s*(true|false)', json_str, re.IGNORECASE)

    if answer_match and should_update_match:
        answer = answer_match.group(1)
        should_update = should_update_match.group(1).lower() == 'true'
        print("✅ 成功!")
        print(f"  answer: {answer}")
        print(f"  should_update: {should_update}")

        # 提取 update_content
        content_match = re.search(r'"update_content"\s*:\s*"(.*?)"\s*\}', json_str, re.DOTALL)
        if content_match:
            content = content_match.group(1)
            print(f"  update_content 长度: {len(content)}")
            print(f"  update_content 前100字符: {content[:100]}")
    else:
        print("❌ 匹配失败")
except Exception as e:
    print(f"❌ 失败: {e}")

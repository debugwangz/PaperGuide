"""测试 JSON 解析"""
import json
import re

# 模拟实际返回的响应（有问题的 JSON）
raw_response = '''```json
{
    "answer": "你说得对，前置知识部分确实太简略了。我会把每个概念都展开讲透，特别是 Flow Matching 和 ODE/SDE 这两个核心概念——它们是理解整篇论文的关键，但原文只用了几句话带过，新手确实很难建立直觉。",
    "should_update": true,
    "update_section": "3. 前置知识",
    "update_content": "## 3. 前置知识\n\n### 3.1 强化学习（Reinforcement Learning, RL）\n\n#### 3.1.1 为什么要讲强化学习？\n\n这是第一行\n这是第二行\n\n**问题**：什么是"引号测试"？"
}
```'''

print("原始响应长度:", len(raw_response))
print("="*50)

# 方法1: 标准 JSON 解析
print("\n方法1: 标准 JSON 解析")
try:
    if "```" in raw_response:
        json_str = raw_response.split("```")[1]
        if json_str.startswith("json"):
            json_str = json_str[4:]
        json_str = json_str.strip()
    else:
        json_str = raw_response.strip()

    result = json.loads(json_str)
    print("✅ 成功!")
    print(f"  answer: {result.get('answer')[:50]}...")
    print(f"  should_update: {result.get('should_update')}")
except Exception as e:
    print(f"❌ 失败: {e}")
    print(f"  json_str 前200字符: {json_str[:200]}")

# 方法2: 正则提取
print("\n方法2: 正则提取")
try:
    answer_match = re.search(r'"answer"\s*:\s*"(.*?)"\s*,\s*"should_update"', json_str, re.DOTALL)
    should_update_match = re.search(r'"should_update"\s*:\s*(true|false)', json_str, re.IGNORECASE)

    if answer_match and should_update_match:
        answer = answer_match.group(1).replace('\\n', '\n').replace('\\"', '"')
        should_update = should_update_match.group(1).lower() == 'true'
        print("✅ 成功!")
        print(f"  answer: {answer[:50]}...")
        print(f"  should_update: {should_update}")
    else:
        print("❌ 匹配失败")
except Exception as e:
    print(f"❌ 失败: {e}")

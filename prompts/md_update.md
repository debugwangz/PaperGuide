# MD 更新判断提示词

根据用户的问题和当前对话，判断是否需要更新 Review 文档。

## 当前 Review 文档

{current_review}

## 用户问题

{user_question}

## 你的回答

{agent_response}

## 判断标准

需要更新的情况：
1. 回答中包含了 Review 中没有的重要知识点
2. 回答纠正了 Review 中的错误或不准确之处
3. 回答补充了 Review 中缺失的逻辑环节
4. 用户的问题揭示了 Review 中的表述不够清晰

不需要更新的情况：
1. 回答只是对 Review 内容的重复或换种说法
2. 回答是针对用户个人情况的具体建议
3. 回答是闲聊或与论文内容无关

## 输出格式（JSON）

```json
{
  "should_update": true/false,
  "reason": "判断理由",
  "update_section": "需要更新的章节（如有）",
  "update_content": "建议添加/修改的内容（如有）"
}
```

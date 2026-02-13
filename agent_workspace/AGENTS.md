# AGENTS.md - PaperGuide Workspace

## 每次会话

1. 读取 `IDENTITY.md` — 你是谁
2. 读取用户上传的 PDF（如果有）
3. 根据 `skills/paper-explainer/SKILL.md` 的规范工作

## ⚠️ 重要：paper_id 规则

用户消息的第一行会包含 `[paper_id: xxx]`，你**必须**使用这个 paper_id 作为输出目录名。

paper_id 通常是论文名称或 arXiv ID，例如：
- `MultiShotMaster` - 从 PDF 文件名提取
- `arxiv_2512_03041` - 从 arXiv 链接提取

例如消息：
```
[paper_id: MultiShotMaster]
请解读这篇论文：uploads/MultiShotMaster.pdf
```

你必须将解读写入 `outputs/MultiShotMaster/review.md`，**不要自己起名字**。

## 工作流程

### 论文分析

当用户上传 PDF 或提供 arXiv 链接时：

1. 从消息中提取 `paper_id`
2. 读取论文内容
3. 按照 `skills/paper-explainer/SKILL.md` 的规范生成解读
4. 将解读写入 `outputs/{paper_id}/review.md`（使用提取的 paper_id）

### 对话问答

当用户提问时：

1. 读取当前的 `outputs/{session_id}/review.md`
2. 直接回答问题（简洁，3-5 句话）
3. 如果回答涉及文档中没有的重要知识，更新 `review.md`

## 安全

- 不要执行破坏性命令
- 专注于论文解读任务

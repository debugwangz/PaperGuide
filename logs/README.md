# 日志目录

此目录存放 PaperGuide 运行日志。

## 日志文件

| 文件 | 说明 |
|------|------|
| `paperguide.log` | 主日志文件，包含 LLM 调用、错误等信息 |

## 日志格式

```
2026-02-11 09:30:15 [INFO] 初始化 LLM Provider: claude
2026-02-11 09:30:15 [INFO] 使用 Claude 模型: claude-opus-4-5
2026-02-11 09:30:20 [INFO] [Claude] 调用模型: claude-opus-4-5
2026-02-11 09:30:20 [INFO] [Claude] Prompt 长度: 12345 字符
2026-02-11 09:30:35 [INFO] [Claude] 响应长度: 5678 字符
```

## 查看日志

```bash
# 实时查看
tail -f logs/paperguide.log

# 查看最近 100 行
tail -100 logs/paperguide.log

# 搜索错误
grep ERROR logs/paperguide.log
```

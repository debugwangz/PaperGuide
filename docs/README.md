# PaperGuide 文档

## 项目愿景

**让任何人都能读懂任何论文。**

学术论文往往假设读者具备大量背景知识，对新手极不友好。PaperGuide 通过 AI 填补这一鸿沟。

## 文档目录

| 文档 | 内容 |
|------|------|
| [架构设计](./architecture.md) | 系统架构、数据流、模块详解 |
| [配置指南](./configuration.md) | 环境变量、配置项详解 |
| [开发指南](./development.md) | 开发环境、项目结构、扩展开发 |
| [产品路线图](./roadmap.md) | 功能规划、未来方向 |

## 核心设计原则

### 1. 提示词分离

所有提示词放在 `prompts/` 目录，便于迭代优化，不需要改代码。

### 2. 搜索解耦

`core/search/` 使用抽象接口设计，支持轻松替换搜索引擎。

### 3. LLM 可切换

支持 OpenAI 和 Claude，通过环境变量一键切换。

### 4. 会话持久化

每个论文分析会话保存在 `outputs/{paper_name}/session.json`，
即使对话历史被截断，关键信息也不会丢失。

## 快速链接

- [快速开始](../README.md#快速开始)
- [Core 模块](../core/README.md)
- [提示词说明](../prompts/README.md)

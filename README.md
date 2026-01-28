# Obsidian Auto-Link Core (Python Edition)

> **Auto-Link Core** 是一个面向极客和程序员的“全自动知识库园丁”。它设计为在后台静默运行（Set and Forget），利用本地 LLM 或 API，每天自动整理你的 Obsidian 笔记库，生成标签并发现笔记间的深度关联。

---

## 📖 目录 / Table of Contents

- [Obsidian Auto-Link Core (Python Edition)](#obsidian-auto-link-core-python-edition)
  - [📖 目录 / Table of Contents](#-目录--table-of-contents)
- [中文说明](#中文说明)
  - [✨ 核心特性](#-核心特性)
  - [快速开始](#快速开始)
    - [1. 安装](#1-安装)
    - [2. 配置](#2-配置)
    - [3. 初始化与运行](#3-初始化与运行)
  - [标签管理系统](#标签管理系统)
  - [高级配置](#高级配置)
  - [下一步计划](#下一步计划)
- [English Documentation](#english-documentation)
  - [✨ Core Features](#-core-features)
  - [Quick Start](#quick-start)
    - [1. Installation](#1-installation)
    - [2. Configuration](#2-configuration)
    - [3. Usage](#3-usage)
  - [Tag Management System](#tag-management-system)
  - [Advanced Configuration](#advanced-configuration)

---

# 中文说明

## ✨ 核心特性

1.  **🧠 智能向量化与检索**
    *   基于 **ChromaDB** 构建本地向量索引。
    *   支持本地 **HuggingFace** 模型（隐私优先）或 OpenAI/DeepSeek API。
    *   自动发现笔记间的深度语义关联。

2.  **🏷️ 智能标签系统 (Smart Tagging)**
    *   **自动打标**：LLM 阅读笔记并生成最相关的标签。
    *   **自动学习 (Harvesting)**：当你手动在笔记中写了新标签，系统会自动将其加入白名单。
    *   **黑名单机制**：支持过滤 `todo`, `draft` 等临时标签，防止 AI 生成噪音。

3.  **🔗 深度关联 (Deep Linking)**
    *   检索相关历史笔记，并生成带有洞察力的 **Callout** 链接块，解释为什么这两篇笔记相关。

4.  **🛡️ 安全回滚系统**
    *   所有修改前自动进行物理文件备份。
    *   提供 CLI 命令一键回滚（按日期或按文件）。

## 快速开始

### 1. 安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/obsidian-auto-link-python.git
cd obsidian-auto-link-python

# 创建虚拟环境 (推荐使用 conda)
conda env create -f environment.yml
conda activate obsidian-auto-link
```

### 2. 配置

修改 `config.yaml`，填入你的 LLM API Key (支持 DeepSeek, OpenAI, Anthropic, Google)。

```yaml
# 示例：使用 DeepSeek
active_provider: "deepseek-api"
providers:
  deepseek-api:
    provider_type: "openai_compatible"
    base_url: "https://api.deepseek.com"
    api_key: "${DEEPSEEK_API_KEY}" # 支持环境变量
    model: "deepseek-chat"
```

### 3. 初始化与运行

```bash
# 初始化向量库 (首次运行会自动下载模型)
python -m src.main init

# 运行每日更新任务 (自动扫描变更 -> 备份 -> 智能整理)
python -m src.main update
```

## 标签管理系统

Auto-Link 拥有强大的标签治理能力，你可以通过命令行轻松管理。

*   **白名单 (Whitelist)**: AI 会优先从中选择标签。
*   **黑名单 (Blacklist)**: AI 绝不会生成这些标签，也不会学习它们。

```bash
# --- 白名单管理 ---
python -m src.main tags list          # 查看所有标签
python -m src.main tags add "AI"      # 手动添加
python -m src.main tags remove "AI"   # 手动删除

# --- 黑名单管理 ---
python -m src.main blacklist list
python -m src.main blacklist add "todo" # 拉黑 "todo"，防止 AI 生成它
```

## 高级配置

*   **Prompt 自定义**: 编辑 `prompts.yaml`，你可以完全控制 AI 的语气和指令。
*   **环境变量**: 可以在 `config.yaml` 中使用 `${VAR_NAME}` 引用环境变量，避免密钥泄露。
*   **安全回滚**:
    ```bash
    # 恢复今天被 AI 修改过的所有文件
    python -m src.main restore --date 2024-01-27
    ```

## 下一步计划

- 新增Report功能，每次执行完成任务后生成任务摘要。 

---

# English Documentation

**Obsidian Auto-Link Core** is a "Fully Automated Knowledge Base Gardener" designed for geeks and developers. It follows a "Set and Forget" philosophy, running silently in the background to automatically organize your Obsidian vault daily using local LLMs or APIs.

## ✨ Core Features

1.  **🧠 Smart Vectorization**
    *   Builds a local vector index using **ChromaDB**.
    *   Supports local **HuggingFace** models (Privacy First) or OpenAI/DeepSeek APIs.

2.  **🏷️ Smart Tagging System**
    *   **Auto-Tagging**: LLM reads notes and generates relevant tags.
    *   **Auto-Harvesting**: When you manually add tags to notes, the system automatically learns and adds them to the whitelist.
    *   **Blacklist Mechanism**: Filters out temporary tags like `todo` or `draft` to prevent AI noise.

3.  **🔗 Deep Linking**
    *   Discovers semantically related notes and appends insightful **Callout** blocks explaining the connection.

4.  **🛡️ Safety & Rollback**
    *   Automatic physical file backup before any modification.
    *   CLI commands for one-click rollback (by date or by file).

## Quick Start

### 1. Installation

```bash
# Clone repository
git clone https://github.com/yourusername/obsidian-auto-link-python.git
cd obsidian-auto-link-python

# Create virtual environment (Conda recommended)
conda env create -f environment.yml
conda activate obsidian-auto-link
```

### 2. Configuration

Edit `config.yaml` and set up your LLM provider.

```yaml
# Example: Using DeepSeek
active_provider: "deepseek-api"
providers:
  deepseek-api:
    provider_type: "openai_compatible"
    base_url: "https://api.deepseek.com"
    api_key: "${DEEPSEEK_API_KEY}" # Environment variables supported
    model: "deepseek-chat"
```

### 3. Usage

```bash
# Initialize vector store (First run downloads models automatically)
python -m src.main init

# Run daily update task (Scan -> Backup -> Organize)
python -m src.main update
```

## Tag Management System

Auto-Link comes with powerful tag governance tools managed via CLI.

*   **Whitelist**: AI prioritizes tags from this list.
*   **Blacklist**: AI will never generate or learn tags from this list.

```bash
# --- Whitelist Management ---
python -m src.main tags list          # List all known tags
python -m src.main tags add "AI"      # Add tag manually
python -m src.main tags remove "AI"   # Remove tag

# --- Blacklist Management ---
python -m src.main blacklist list
python -m src.main blacklist add "todo" # Block "todo" tag
```

## Advanced Configuration

*   **Custom Prompts**: Edit `prompts.yaml` to fully customize AI persona and instructions.
*   **Environment Variables**: Use `${VAR_NAME}` in `config.yaml` to keep secrets safe.
*   **Safety Rollback**:
    ```bash
    # Restore all files modified today
    python -m src.main restore --date 2024-01-27
    ```

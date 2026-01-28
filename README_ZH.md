# Obsidian Auto-Link (Python Core)

> [English Version](README.md) | [详细需求文档 (PRD)](PRD_PYTHON_ZH.md)

**Obsidian Auto-Link Core** 是一个面向极客和程序员的“全自动知识库园丁”。它设计为在后台静默运行（Set and Forget），利用本地 LLM 或 API，每天自动整理你的 Obsidian 笔记库，生成标签并发现笔记间的深度关联。

## ✨ 核心特性

*   **🧠 智能向量化**：基于 ChromaDB/FAISS 构建本地向量索引，支持本地 HuggingFace 模型（隐私优先）或 OpenAI/DeepSeek API。
*   **🏷️ 自动打标 (Tagging)**：自动阅读新笔记，基于上下文智能生成 YAML Frontmatter 标签。
*   **🔗 深度关联 (Linking)**：发现语义相关的历史笔记，并生成带有见解的 Callout 链接块。
*   **🛡️ 安全回滚系统**：
    *   所有修改前自动进行物理文件备份。
    *   提供 CLI 命令一键回滚（按日期或按文件）。
    *   生成每日变更日报 (Markdown)，让你对 AI 的修改了如指掌。

## 🚀 快速开始

### 环境要求
*   Python 3.10+
*   Obsidian Vault

### 安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/obsidian-auto-link-python.git
cd obsidian-auto-link-python

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 配置

在项目根目录创建 `config.yaml`：

```yaml
vault_path: "/Users/username/Documents/MyVault"

embedding:
  type: "local"
  model_name: "BAAI/bge-large-zh-v1.5"

llm:
  provider: "openai_compatible"
  base_url: "https://api.deepseek.com"
  api_key: "sk-..."

safety:
  enable_backup: true
```

### 使用方法

```bash
# 初始化向量库（首次运行）
python main.py init

# 运行每日更新任务
python main.py update

# 恢复昨天被修改的文件（如果结果不满意）
python main.py restore --date yesterday
```

## 📄 文档

详细的功能规范和设计细节，请参阅 [产品需求文档 (PRD)](PRD_PYTHON_ZH.md)。

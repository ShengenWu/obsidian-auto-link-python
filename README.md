# Obsidian Auto-Link (Python Core)

> [中文版](README_ZH.md) | [Product Requirements Document (PRD)](PRD_PYTHON_EN.md)

**Obsidian Auto-Link Core** is a "Fully Automated Knowledge Base Gardener" designed for geeks and developers. It follows a "Set and Forget" philosophy, running silently in the background to automatically organize your Obsidian vault daily using local LLMs or APIs.

## ✨ Core Features

*   **🧠 Smart Vectorization**: Builds a local vector index using ChromaDB/FAISS. Supports local HuggingFace models (Privacy First) or OpenAI/DeepSeek APIs.
*   **🏷️ Auto-Tagging**: Automatically reads new notes and generates intelligent YAML Frontmatter tags based on context.
*   **🔗 Deep Linking**: Discovers semantically related historical notes and appends insightful Callout link blocks.
*   **🛡️ Safety & Rollback System**:
    *   Automatic physical file backup before any modification.
    *   CLI commands for one-click rollback (by date or by file).
    *   Generates a Daily Change Report (Markdown) to keep you informed of all AI modifications.

## 🚀 Quick Start

### Requirements
*   Python 3.10+
*   Obsidian Vault

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/obsidian-auto-link-python.git
cd obsidian-auto-link-python

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create `config.yaml` in the project root:

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

### Usage

```bash
# Initialize vector store (First run)
python main.py init

# Run daily update task
python main.py update

# Restore files modified yesterday (If needed)
python main.py restore --date yesterday
```

## 📄 Documentation

For detailed functional specifications and design details, please refer to the [Product Requirements Document (PRD)](PRD_PYTHON_EN.md).

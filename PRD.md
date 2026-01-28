# PRD 1: Auto-Link Core (Python Edition)

**项目代号**：Auto-Link Core

**定位**：面向极客/程序员的“全自动知识库园丁”

**核心哲学**：Set and Forget（配置一次，静默运行，每天早上坐享其成）

**技术栈**：Python, LangChain, ChromaDB/FAISS, Typer (CLI), Pydantic

## 1. 目标用户 (Target Audience)

- 有编程基础，熟悉 Python 环境（如 `uv`, `conda`）。
    
- 拥有长期运行的设备（Mac Mini, NAS, 服务器）。
    
- 追求高性能检索，希望使用本地 LLM (Ollama) 或更强大的 Embedding 模型。
    

## 2. 核心功能 (Core Features)

### 2.1 全量/增量 向量化 (Vectorization)

- **本地向量库**：在本地构建并维护一个持久化的向量数据库 (ChromaDB/FAISS)。
    
- **模型自由**：
    
    - 支持调用 OpenAI/DeepSeek API 进行 Embedding。
        
    - **独有特性**：支持本地 HuggingFace 模型 (如 `bge-m3`, `nomic-embed-text`)，无需 API 费用，隐私性极高。
        
- **同步策略**：
    
    - `init`：全量扫描 Vault，建立初始索引。
        
    - `update`：仅扫描 `mtime` (修改时间) 在上次运行之后的文件，更新向量库。
        

### 2.2 每日自动整理 (Daily Batch Processing)

- **运行方式**：通过 `crontab` 或 Systemd 定时触发（如每日凌晨 04:00）。
    
- **任务队列**：
    
    1. **Tagging**：扫描昨日新增笔记 -> 读取全文 -> LLM 决策 Tags -> 修改 Frontmatter。
        
    2. **Linking**：新笔记 Embedding -> 在向量库检索 Top-k -> LLM 生成关联见解 -> 追加 Callout。
        
Linking示例：
> [!NOTE] 🤖 Auto-Link 见解 > 这篇关于 "Text-to-SQL" 的笔记，补充了你之前对 SQL 生成准确率低的原因分析。 > - 关联：[[2025-08-15-Schema-Linking]] (关于 Schema Linking 的难点) > - 关联：[[2024-12-01-RAG-Optimization]] (检索增强优化)

### 2.3 高级配置 (Configuration `config.yaml`)

YAML

```
vault_path: "./my_vault"
embedding:
  type: "local" # or "api"
  model_name: "BAAI/bge-large-zh-v1.5" # Python版可以跑这种大模型
llm:
  provider: "openai_compatible"
  base_url: "https://api.deepseek.com"
  api_key: "${ENV_VAR}"
  temperature: 0.3
pipeline:
  dry_run: false # True则只打印不修改文件
  backup: true # 修改前自动备份当前文件
```

## 3. 技术实现细节

- **文件安全**：使用 `frontmatter` 库进行“手术式”修改，严禁重写整个文件导致格式丢失。
    
- **并发控制**：虽然是后台脚本，但为了防止文件损坏，建议单线程顺序处理文件。
    
- **日志系统**：生成详细的 `run.log`，记录哪些文件被修改了，方便用户回溯。
    

---

# PRD 2: Auto-Link Plugin (Obsidian Edition)

**项目代号**：Obsidian Auto-Link

**定位**：面向普通用户的“即时灵感助手”

**核心哲学**：Human-in-the-loop（用户触发，AI 建议，用户确认）

**技术栈**：TypeScript, Obsidian API, React (UI组件)

## 1. 目标用户 (Target Audience)

- 不想折腾代码的普通 Obsidian 用户。
    
- 希望在写作过程中获得即时反馈，而不是等第二天。
    
- 需要在多端（Mac, Windows, iOS）同步使用。
    

## 2. 核心功能 (Core Features)

### 2.1 交互式打标 (Interactive Tagging)

- **触发机制**：
    
    - 命令面板：`Auto-Link: Generate Tags for current file`。
        
    - 侧边栏/Ribbon 按钮。
        
- **UI 交互**：
    
    - 不直接修改文件。
        
    - 弹出一个 **建议模态框 (Modal)**，列出 LLM 建议的标签。
        
    - 用户可以勾选/取消勾选，点击“Apply”后写入 Frontmatter。
        
- **标签源**：读取 `app.metadataCache` 获取 Vault 现有标签，作为 Prompt 上下文，防止标签分裂（如防止同时出现 `#AI` 和 `#ArtificialIntelligence`）。
    

### 2.2 轻量化关联检索 (Lightweight Retrieval)

- **限制条件**：由于插件环境限制，不运行重型向量库。
    
- **检索策略 (两套方案供用户选)**：
    
    1. **纯文本/TF-IDF (传统方法)**：基于关键词匹配计算相关性。优点：极快，无额外费用，本地纯 JS 实现。
        
    2. **API 实时 Embedding**：将当前笔记 + 最近修改的 N 篇笔记摘要发给 API 计算相似度。
        
- **展现形式**：
    
    - 在右侧边栏 (Sidebar) 增加一个 "Auto-Link" 视图，显示推荐的关联笔记。
        
    - 提供“Insert Link”按钮，点击将关联插入到当前光标位置。
        

### 2.3 设置界面 (Settings Tab)

- **API 配置**：输入 API Key, Base URL (适配 OpenAI, DeepSeek, Claude)。
    
- **Prompt 自定义**：允许高级用户修改 System Prompt。
    
- **黑名单**：设置不处理的文件夹（如 `Daily Notes/`, `Templates/`）。
    

## 3. 技术实现细节

- **网络请求**：使用 `requestUrl` (Obsidian API) 绕过 CORS 限制。
    
- **性能优化**：不在主线程进行繁重的文本处理，避免卡顿 UI。
    
- **缓存机制**：简单的 `localStorage` 缓存，避免对同一篇未修改的笔记重复调用 API 浪费 Token。
    

---

### 总结：两者的关键区别

|**特性**|**Python Core (后端版)**|**Obsidian Plugin (插件版)**|
|---|---|---|
|**主要场景**|批量清洗、大规模知识库维护|写作辅助、单篇精修|
|**检索能力**|**强** (ChromaDB + BERT/BGE 大模型)|**中/弱** (关键词匹配 / 依赖外部 API)|
|**触发方式**|定时任务 (Cron)|手动触发 / 打开文件时|
|**修改逻辑**|直接覆写文件 (高风险，需备份)|通过 Obsidian API 修改 (安全，带撤销栈)|
|**部署难度**|高 (需 Python 环境)|低 (插件市场一键安装)|

您可以根据这个拆分，决定先启动哪个项目。通常建议先做 **Python 版** 的 MVP，因为不需要处理前端 UI，能更快验证 Prompt 的效果和 Embedding 的质量。

# 以下是新功能：
# PRD 1: Auto-Link Core (Python Edition) v0.2

**新增重点**：文件级备份、CLI 回滚命令、Markdown 格式的每日变更日报。

## 1. 目标用户 & 核心哲学 (保持不变)

- **定位**：Set and Forget，但在后台必须“有据可查，有悔可追”。
    

## 2. 核心功能 (Core Features)

### 2.1 ~ 2.2 (向量化 & 每日整理)

_(保持 v0.1 内容)_

### 2.3 安全与回溯系统 (Safety & Rollback System) **[NEW]**

为了防止 LLM 幻觉导致的数据覆盖或错误打标，必须建立独立于 Git/网盘之外的本地快照机制。

- **备份机制 (Snapshot Strategy)**：
    
    - 每次修改文件前，将原文件完整复制到 `.auto_link_backups/{YYYY-MM-DD}/{Filename}.md`。
        
    - **保留策略**：默认保留最近 **7天** 的备份（用户要求至少 3 天），过期自动清理。
        
    - **结构示例**：
        
        Plaintext
        
        ```
        .auto_link_backups/
        ├── 2026-01-26/
        │   ├── 笔记A.md
        │   └── 笔记B.md
        ├── 2026-01-27/
        ```
        
- **回滚操作 (CLI Restore)**：
    
    - 提供命令行工具快速回滚。
        
    - `auto-link restore --date yesterday`：将昨天被修改过的所有文件恢复原状。
        
    - `auto-link restore --file "笔记A.md"`：仅恢复特定文件到修改前的状态。
        

### 2.4 变更总结报告 (Change Summary Report) **[NEW]**

每次任务执行完毕后，必须让用户知道“AI 到底改了什么”。

- **报告生成**：
    
    - 每次运行结束后，在 Vault 的指定目录（如 `System/Auto-Link-Logs/`）生成一篇 Markdown 日志。
        
    - **文件名**：`Log_{YYYY-MM-DD}_{RunID}.md`
        
- **报告内容结构**：
    
    1. **概览**：处理文件数、新增 Tag 数、新增 Link 数、消耗 Token/时间。
        
    2. **详细变更列表 (Diff View)**：
        
        - **[Modified] 笔记标题**:
            
            - _Tags_: `+llm`, `+python` (原: `coding`)
                
            - _Links_: 增加了指向 `[[Schema Linking]]` 的引用。
                
    3. **异常记录**：列出解析失败或跳过的文件。
        

### 2.5 高级配置 (`config.yaml`) 更新

YAML

```
safety:
  enable_backup: true
  backup_retention_days: 7 # 至少 3 天
  backup_path: "./.auto_link_backups"

reporting:
  enable_summary: true
  log_folder: "System/Auto-Link-Logs"
  summary_template: "markdown" # or json
```

---

# PRD 2: Auto-Link Plugin (Obsidian Edition) v0.2

**新增重点**：基于 IndexedDB 的操作历史栈、UI 撤销按钮、弹窗式总结报告。

## 1. 目标用户 & 核心哲学 (保持不变)

- **定位**：交互式辅助，强调即时反馈和可视化的“后悔药”。
    

## 2. 核心功能 (Core Features)

### 2.1 ~ 2.2 (交互打标 & 关联检索)

_(保持 v0.1 内容)_

### 2.3 历史回溯与撤销 (History & Undo) **[NEW]**

插件环境不适合大量复制文件（受限于移动端性能），因此采用“差异记录”模式。

- **变更堆栈 (Change Stack)**：
    
    - 使用 `plugin-data.json` 或 `IndexedDB` 存储最近 50 条操作记录。
        
    - 记录结构：
        
        JSON
        
        ```
        {
          "timestamp": 1738000000,
          "filePath": "Notes/AI.md",
          "operation": "auto-tag",
          "changes": {
            "oldFrontmatter": { "tags": ["wip"] },
            "newFrontmatter": { "tags": ["wip", "llm"] }
          }
        }
        ```
        
- **撤销交互**：
    
    - **即时撤销**：操作完成后，Notice 弹窗显示 "Tags added. [Undo]" 按钮，点击立即还原。
        
    - **历史面板**：在插件设置页或侧边栏提供 "History" 选项卡，按时间倒序列出最近修改的文件。
        
    - **一键回退**：每条记录后提供 "Revert" 按钮，点击即可将该文件的 Frontmatter 恢复至操作前状态。
        
    - **保留期限**：自动清理超过 3 天的操作记录。
        

### 2.4 运行总结与通知 (Operation Summary) **[NEW]**

针对“一键处理”或“定时任务”产生的批量修改，提供可视化报告。

- **单文件处理**：
    
    - 使用 Obsidian 原生 Notice 组件，简短提示：“已添加 3 个标签，生成 1 个关联。”
        
- **批量处理/定时任务**：
    
    - 任务完成后，自动弹出一个 **Modal（模态框）**。
        
    - **Modal 内容**：
        
        - 标题：Auto-Link 运行报告 (2026-01-27)
            
        - 统计：处理了 5 篇笔记。
            
        - 列表：
            
            - `笔记A`：新增标签 `#obsidian`
                
            - `笔记B`：新增关联 `[[笔记C]]`
                
    - **底部动作条**：提供 **"Confirm All" (确认所有)** 和 **"Undo All" (全部撤销)** 按钮。
        
- **日志归档 (可选)**：
    
    - 用户可在设置中开启“写入日志文件”，将上述 Modal 的内容追加到 `Daily Note` 或特定日志文件中。
        

### 2.5 设置界面更新

- **History Retention**: 滑动条，设置历史记录保留天数（默认 3 天，最大 30 天）。
    
- **Notification Level**:
    
    - Detailed (每次操作都弹窗 + 总结)
        
    - Summary Only (仅批量操作后弹窗)
        
    - Silent (静默运行，仅记录在 History 面板)
        

---

### 开发建议

1. **Python 版**：优先实现 `shutil.copy2` 进行物理文件备份。这是最“笨”但最可靠的方法，完全不依赖 Obsidian 的 API 或状态，确保数据绝对安全。
    
2. **插件版**：利用 Obsidian API 中的 `FileManager.processFrontMatter` 进行修改时，最好先手动读取一次旧值存入 `this.history` 数组中。不要过度依赖 Obsidian 自身的 "Undo" (Cmd+Z)，因为跨文件批量操作时，Cmd+Z 的行为可能不可控。
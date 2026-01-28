import typer
from rich.console import Console
from rich.panel import Panel
from typing import Optional
from pathlib import Path
import time
import sys

# 将项目根目录添加到 sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.core.config import load_config, AppConfig
from src.core.safety import BackupManager
from src.core.scanner import VaultScanner
from src.core.vector_store import VectorStoreManager
from src.core.tag_manager import TagManager
from src.core.llm import LLMClient
from src.core.modifier import FileModifier

# 初始化 Typer 应用
app = typer.Typer(help="Obsidian Auto-Link Core: 你的全自动知识库园丁")
tags_app = typer.Typer(help="管理 Tag 白名单")
blacklist_app = typer.Typer(help="管理 Tag 黑名单")

app.add_typer(tags_app, name="tags")
app.add_typer(blacklist_app, name="blacklist")

console = Console()
LAST_RUN_FILE = Path(".last_run")

# ... (Helpers) ...

# -----------------------------------------------------------------------------
# Tag Management Commands (Whitelist)
# -----------------------------------------------------------------------------
# ... (existing tags commands) ...

# -----------------------------------------------------------------------------
# Blacklist Management Commands
# -----------------------------------------------------------------------------
@blacklist_app.command("list")
def list_blacklist():
    """列出黑名单中的所有标签"""
    mgr = TagManager()
    tags = mgr.get_blacklist()
    if not tags:
        console.print("[dim]黑名单为空。[/dim]")
    else:
        console.print(Panel(", ".join(tags), title=f"黑名单标签 ({len(tags)})", border_style="red"))

@blacklist_app.command("add")
def add_blacklist(tag: str):
    """添加标签到黑名单 (这会将其从白名单中移除)"""
    mgr = TagManager()
    if mgr.add_to_blacklist(tag):
        console.print(f"[green]✔ 标签 '{tag}' 已加入黑名单[/green]")
    else:
        console.print(f"[yellow]标签 '{tag}' 已在黑名单中[/yellow]")

@blacklist_app.command("remove")
def remove_blacklist(tag: str):
    """从黑名单中移除标签"""
    mgr = TagManager()
    if mgr.remove_from_blacklist(tag):
        console.print(f"[green]✔ 标签 '{tag}' 已从黑名单移除[/green]")
    else:
        console.print(f"[red]标签 '{tag}' 不在黑名单中[/red]")

# -----------------------------------------------------------------------------
# Main Commands
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def get_config_or_exit(config_path: str) -> AppConfig:
    """辅助函数：加载配置，失败则退出"""
    try:
        return load_config(config_path)
    except Exception as e:
        console.print(f"[bold red]❌ 配置加载失败:[/bold red] {e}")
        raise typer.Exit(code=1)

def get_backup_manager(cfg: AppConfig) -> BackupManager:
    return BackupManager(cfg.safety, cfg.vault_path)

def save_last_run_time():
    """保存当前时间为最后运行时间"""
    with open(LAST_RUN_FILE, "w") as f:
        f.write(str(time.time()))

def get_last_run_time() -> float:
    """获取上次运行时间，如果不存在则返回 0"""
    if not LAST_RUN_FILE.exists():
        return 0.0
    try:
        with open(LAST_RUN_FILE, "r") as f:
            return float(f.read().strip())
    except:
        return 0.0

# -----------------------------------------------------------------------------
# Tag Management Commands
# -----------------------------------------------------------------------------
@tags_app.command("list")
def list_tags():
    """列出所有已知的标签"""
    mgr = TagManager()
    tags = mgr.get_all_tags()
    if not tags:
        console.print("[dim]当前没有标签。[/dim]")
    else:
        console.print(Panel(", ".join(tags), title=f"已知标签 ({len(tags)})", border_style="blue"))

@tags_app.command("add")
def add_tag(tag: str):
    """手动添加标签"""
    mgr = TagManager()
    if mgr.add_tag(tag):
        console.print(f"[green]✔ 标签 '{tag}' 已添加[/green]")
    else:
        console.print(f"[yellow]标签 '{tag}' 已存在或无效[/yellow]")

@tags_app.command("remove")
def remove_tag(tag: str):
    """手动删除标签"""
    mgr = TagManager()
    if mgr.remove_tag(tag):
        console.print(f"[green]✔ 标签 '{tag}' 已删除[/green]")
    else:
        console.print(f"[red]标签 '{tag}' 不存在[/red]")

# -----------------------------------------------------------------------------
# Main Commands
# -----------------------------------------------------------------------------
@app.command()
def init(
    config_path: str = typer.Option("config.yaml", "--config", "-c", help="配置文件路径"),
    force: bool = typer.Option(False, "--force", "-f", help="强制重新初始化向量库")
):
    """
    全量扫描 Vault，建立初始向量索引。
    """
    cfg = get_config_or_exit(config_path)
    # 确保 TagManager 初始化
    TagManager()

    backup_mgr = get_backup_manager(cfg)
    scanner = VaultScanner(cfg.vault_path)

    console.print(Panel(f"[bold green]开始初始化[/bold green]\n"
                        f"配置文件: {config_path}\n"
                        f"Vault路径: {cfg.vault_path}\n"
                        f"Embedding模型: {cfg.embedding.model_name}"))

    if not cfg.vault_path.exists():
        console.print(f"[bold red]错误：Vault 路径不存在: {cfg.vault_path}[/bold red]")
        raise typer.Exit(code=1)

    # 初始化向量管理器
    try:
        vector_mgr = VectorStoreManager(cfg.embedding, cfg.get_active_llm_config())
    except Exception as e:
        console.print(f"[red]Vector Store 初始化失败: {e}[/red]")
        raise typer.Exit(code=1)

    if force:
        console.print("[yellow]警告：强制模式已开启，现有索引将被重置。[/yellow]")
        vector_mgr.reset()

    console.print("[bold blue]正在全量扫描 Vault...[/bold blue]")

    files = scanner.scan_all()
    console.print(f"[green]发现 {len(files)} 个 Markdown 笔记[/green]")

    if files:
        texts = []
        metadatas = []
        with console.status(f"[bold green]正在读取并向量化 {len(files)} 个文档...[/bold green]"):
            for p in files:
                try:
                    content = p.read_text(encoding="utf-8", errors="ignore")
                    if content.strip():
                        texts.append(content)
                        metadatas.append({"source": str(p.name), "path": str(p)})
                except Exception as e:
                    console.print(f"[red]读取文件 {p.name} 失败: {e}[/red]")

            if texts:
                vector_mgr.add_texts(texts, metadatas)
                console.print(f"[green]成功索引了 {len(texts)} 个文档！[/green]")

    save_last_run_time()
    console.print("[bold green]✔ 初始化完成！索引已建立。[/bold green]")

@app.command()
def update(
    config_path: str = typer.Option("config.yaml", "--config", "-c", help="配置文件路径"),
    dry_run: bool = typer.Option(False, "--dry-run", help="仅模拟运行，不修改文件"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="显示详细日志")
):
    """
    每日任务：扫描新增/修改的笔记，自动打标并生成链接。
    """
    cfg = get_config_or_exit(config_path)
    backup_mgr = get_backup_manager(cfg)
    scanner = VaultScanner(cfg.vault_path)
    tag_mgr = TagManager()

    # 初始化组件
    try:
        llm_client = LLMClient(cfg)
        vector_mgr = VectorStoreManager(cfg.embedding, cfg.get_active_llm_config())
    except Exception as e:
        console.print(f"[red]组件初始化失败: {e}[/red]")
        raise typer.Exit(code=1)

    if dry_run:
        cfg.pipeline.dry_run = True

    mode = "[bold yellow]DRY RUN (模拟)[/bold yellow]" if cfg.pipeline.dry_run else "[bold red]LIVE (实弹)[/bold red]"
    console.print(Panel(f"[bold blue]开始每日更新[/bold blue]\n模式: {mode}"))

    backup_mgr.prune_old_backups()

    last_run = get_last_run_time()
    console.print("正在检查变更文件...")
    changed_files = scanner.scan_changes(last_run)

    if not changed_files:
        console.print("[dim]没有发现变更。[/dim]")
        return

    console.print(f"[green]发现 {len(changed_files)} 个变更文件[/green]")

    for file_path in changed_files:
        try:
            rel_path = file_path.relative_to(cfg.vault_path)
            console.print(f"\n[bold]处理文件: {rel_path}[/bold]")

            # 1. 备份
            if not cfg.pipeline.dry_run:
                backup_mgr.backup_file(file_path)

            # 2. 初始化 FileModifier 进行内容读取和操作
            try:
                modifier = FileModifier(file_path)
                content = modifier.post.content # 正文内容

                # --- 自动收割现有 Tags ---
                current_tags = modifier.post.get("tags", [])

                # 确保 current_tags 是列表
                if current_tags is None:
                    current_tags = []
                elif isinstance(current_tags, str):
                    current_tags = [current_tags]

                # 如果还不是列表（比如是 int/float），强制转为列表
                if not isinstance(current_tags, list):
                    current_tags = [str(current_tags)]

                # 收割逻辑
                for t in current_tags:
                    t = str(t).strip()
                    if t and t not in tag_mgr.get_all_tags() and not tag_mgr.is_blacklisted(t):
                        if not cfg.pipeline.dry_run:
                            if tag_mgr.add_tag(t):
                                console.print(f"  [cyan]🎓 学习到用户自定义标签: {t}[/cyan]")

            except Exception as e:
                console.print(f"[yellow]文件解析警告: {e}，跳过处理[/yellow]")
                continue

            if not content.strip():
                continue

            # 3. LLM Tagging
            existing_tags = tag_mgr.get_all_tags()
            new_tags = llm_client.generate_tags(content, existing_tags)

            # 过滤黑名单标签
            valid_new_tags = [t for t in new_tags if not tag_mgr.is_blacklisted(t)]
            if len(valid_new_tags) < len(new_tags):
                console.print(f"  [dim]已过滤 {len(new_tags)-len(valid_new_tags)} 个黑名单标签[/dim]")

            console.print(f"  🤖 建议标签: {valid_new_tags}")

            # 应用标签 (FileModifier 会自动合并去重)
            if modifier.update_tags(valid_new_tags):
                console.print("  [green]✔ 标签已更新[/green]")
                # 学习新标签
                if not cfg.pipeline.dry_run:
                    for t in valid_new_tags:
                        if tag_mgr.add_tag(t):
                            console.print(f"  [dim]新标签 '{t}' 已加入白名单[/dim]")

            # 4. LLM Linking
            # 先检索
            related_docs_raw = vector_mgr.search(content, k=3)
            # [调试] 打印检索到的原始结果
            console.print(f"[debug] 原始检索结果: {[doc.metadata.get('source') for doc, score in related_docs_raw]}")

            related_docs = []
            for doc, score in related_docs_raw:
                if doc.metadata.get("source") == file_path.name:
                    continue
                related_docs.append({
                    "source": doc.metadata.get("source", "Unknown"),
                    "path": doc.metadata.get("path", ""),
                    "content": doc.page_content
                })

            if related_docs:
                console.print(f"  🔍 检索到 {len(related_docs)} 篇相关笔记: {[d['source'] for d in related_docs]}")
                insight = llm_client.generate_insight(file_path.stem, content, related_docs)
                if insight:
                    console.print(Panel(insight, title="生成的关联见解", border_style="magenta"))
                    modifier.append_callout(insight)
                    console.print("  [green]✔ 见解已追加[/green]")

            # 5. 保存修改 & 更新向量库
            if not cfg.pipeline.dry_run:
                # FileModifier.save() 会负责根据标签数量自动调整 YAML 格式
                modifier.save()

                # 存入向量库
                vector_mgr.add_texts([content], [{"source": file_path.name, "path": str(file_path)}])

        except Exception as e:
            console.print(f"[red]处理文件 {file_path.name} 出错: {e}[/red]")
            # 打印完整的错误栈以便调试
            # import traceback; traceback.print_exc()

    if not cfg.pipeline.dry_run:
        save_last_run_time()

    console.print("[bold green]✔ 更新完成！[/bold green]")

@app.command()
def restore(
    config_path: str = typer.Option("config.yaml", "--config", "-c", help="配置文件路径"),
    date: Optional[str] = typer.Option(None, help="恢复该日期修改的所有文件 (格式: YYYY-MM-DD)"),
    file: Optional[str] = typer.Option(None, help="恢复特定文件 (相对路径)"),
    confirm: bool = typer.Option(False, "--yes", "-y", help="跳过确认提示")
):
    """
    回滚操作：将文件恢复到修改前的状态。
    """
    cfg = get_config_or_exit(config_path)
    backup_mgr = get_backup_manager(cfg)

    if not date and not file:
        console.print("[bold red]错误：必须指定 --date 或 --file[/bold red]")
        raise typer.Exit(code=1)

    console.print(Panel(f"[bold red]启动回滚程序[/bold red]\n备份路径: {cfg.safety.backup_path}"))

    if date:
        console.print(f"准备回滚日期: [bold]{date}[/bold]")
    if file:
        console.print(f"准备回滚文件: [bold]{file}[/bold]")

    if not confirm:
        if not typer.confirm("你确定要执行回滚吗？这将覆盖当前文件。"):
            console.print("[yellow]操作已取消[/yellow]")
            raise typer.Exit()

    if date:
        count = backup_mgr.restore_by_date(date)
        if count > 0:
            console.print(f"[bold green]成功恢复了 {count} 个文件！[/bold green]")
        else:
            console.print("[yellow]没有文件被恢复。[/yellow]")

    if file:
        success = backup_mgr.restore_file(file)
        if not success:
             raise typer.Exit(code=1)

    console.print("[bold green]✔ 回滚操作结束！[/bold green]")

if __name__ == "__main__":
    app()

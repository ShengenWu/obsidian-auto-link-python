import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional
from rich.console import Console
import os

from src.core.config import SafetyConfig

console = Console()

class BackupManager:
    def __init__(self, config: SafetyConfig, vault_root: Path):
        self.config = config
        self.vault_root = vault_root.resolve()
        # 备份根目录 (绝对路径)
        self.backup_root = Path(config.backup_path).resolve()

    def _get_today_backup_dir(self) -> Path:
        """获取今日的备份目录"""
        today_str = datetime.now().strftime("%Y-%m-%d")
        dir_path = self.backup_root / today_str
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path

    def backup_file(self, file_path: Path) -> Optional[Path]:
        """
        备份单个文件
        :param file_path: 原始文件路径 (绝对路径)
        :return: 备份文件的路径
        """
        if not self.config.enable_backup:
            return None

        file_path = file_path.resolve()
        if not file_path.exists():
            console.print(f"[yellow]警告：尝试备份不存在的文件 {file_path}[/yellow]")
            return None

        # 计算相对路径，以保持备份目录结构
        try:
            rel_path = file_path.relative_to(self.vault_root)
        except ValueError:
            # 如果文件不在 Vault 内，直接用文件名
            rel_path = Path(file_path.name)

        backup_dir = self._get_today_backup_dir()
        dest_path = backup_dir / rel_path

        # 确保目标文件的父目录存在
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # copy2 保留文件元数据 (mtime等)
            shutil.copy2(file_path, dest_path)
            # console.print(f"[dim]已备份: {file_path.name} -> {dest_path}[/dim]")
            return dest_path
        except Exception as e:
            console.print(f"[bold red]备份失败 {file_path}: {e}[/bold red]")
            return None

    def restore_file(self, rel_file_path: str) -> bool:
        """
        从最近的备份中恢复文件
        :param rel_file_path: 相对于 Vault 的路径 (例如 "Notes/AI.md")
        """
        target_path = (self.vault_root / rel_file_path).resolve()

        # 查找该文件的所有备份，按时间倒序
        backups = []
        if not self.backup_root.exists():
            console.print("[red]没有找到任何备份记录[/red]")
            return False

        # 遍历日期文件夹
        for date_dir in self.backup_root.iterdir():
            if not date_dir.is_dir():
                continue

            potential_backup = date_dir / rel_file_path
            if potential_backup.exists():
                backups.append(potential_backup)

        if not backups:
            console.print(f"[red]未找到文件 {rel_file_path} 的任何备份[/red]")
            return False

        # 取最新的备份 (这里假设日期文件夹名排序即时间排序)
        # 更好的做法是读取文件mtime，但简单起见直接按目录名排序
        backups.sort(key=lambda p: p.parent.parent.name, reverse=True) # 父目录的父目录是日期目录？不对
        # 目录结构是 backup_root / YYYY-MM-DD / rel_path
        # 所以 backup.parts 里面包含了日期
        # 简单按字符串排序即可，因为路径包含YYYY-MM-DD
        backups.sort(key=str, reverse=True)

        latest_backup = backups[0]

        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(latest_backup, target_path)
            console.print(f"[green]✔ 已恢复: {rel_file_path} (来源: {latest_backup.parent})[/green]")
            return True
        except Exception as e:
            console.print(f"[bold red]恢复失败: {e}[/bold red]")
            return False

    def restore_by_date(self, date_str: str) -> int:
        """
        恢复指定日期的所有文件
        :return: 恢复的文件数量
        """
        backup_dir = self.backup_root / date_str
        if not backup_dir.exists():
            console.print(f"[red]未找到日期 {date_str} 的备份[/red]")
            return 0

        count = 0
        # 遍历该日期下的所有文件
        for backup_file in backup_dir.rglob("*"):
            if backup_file.is_file():
                # 计算出它在 Vault 中的原始位置
                rel_path = backup_file.relative_to(backup_dir)
                target_path = self.vault_root / rel_path

                try:
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(backup_file, target_path)
                    console.print(f"[dim]恢复: {rel_path}[/dim]")
                    count += 1
                except Exception as e:
                    console.print(f"[red]文件 {rel_path} 恢复失败: {e}[/red]")

        return count

    def prune_old_backups(self):
        """清理超过保留天数的备份"""
        retention_days = self.config.backup_retention_days
        if retention_days <= 0:
            return

        cutoff_date = datetime.now() - timedelta(days=retention_days)

        if not self.backup_root.exists():
            return

        for date_dir in self.backup_root.iterdir():
            if not date_dir.is_dir():
                continue

            try:
                dir_date = datetime.strptime(date_dir.name, "%Y-%m-%d")
                if dir_date < cutoff_date:
                    console.print(f"[yellow]清理过期备份: {date_dir.name}[/yellow]")
                    shutil.rmtree(date_dir)
            except ValueError:
                continue # 忽略非日期命名的文件夹

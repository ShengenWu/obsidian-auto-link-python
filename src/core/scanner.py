from pathlib import Path
from typing import List, Generator, Set
from datetime import datetime
import os

class VaultScanner:
    # 默认忽略的目录名
    IGNORED_DIRS = {
        ".git",
        ".obsidian",
        ".trash",
        ".auto_link_backups",
        "System", # 假设用户把系统日志放在这里
        "templates", # 常见模版目录
        "Templates"
    }

    def __init__(self, vault_root: Path):
        self.vault_root = vault_root.resolve()

    def _is_ignored(self, path: Path) -> bool:
        """检查路径是否包含被忽略的目录"""
        # 检查路径中的每一部分是否在黑名单中
        # 例如: /Notes/.obsidian/plugins/ Should be ignored
        rel_parts = path.relative_to(self.vault_root).parts

        # 只要路径中任何一部分在忽略列表中，就跳过
        for part in rel_parts:
            if part in self.IGNORED_DIRS:
                return True
        return False

    def scan_all(self) -> List[Path]:
        """扫描所有 Markdown 文件"""
        files = []
        # 使用 rglob 递归查找
        for p in self.vault_root.rglob("*.md"):
            if p.is_file() and not self._is_ignored(p):
                files.append(p)
        return files

    def scan_changes(self, last_run_time: float) -> List[Path]:
        """
        扫描自上次运行以来修改过的文件
        :param last_run_time: 上次运行的时间戳 (float)
        :return: 修改过的文件列表
        """
        changed_files = []
        for p in self.vault_root.rglob("*.md"):
            if not p.is_file() or self._is_ignored(p):
                continue

            # 获取文件最后修改时间
            mtime = p.stat().st_mtime
            if mtime > last_run_time:
                changed_files.append(p)

        return changed_files

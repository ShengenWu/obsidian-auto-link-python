from pathlib import Path
from typing import List, Set
import json
from rich.console import Console

console = Console()

class TagManager:
    def __init__(self,
                 whitelist_path: Path = Path("tags.json"),
                 blacklist_path: Path = Path("tags_blacklist.json")):
        self.whitelist_path = whitelist_path
        self.blacklist_path = blacklist_path

        # 初始化时只创建空列表，不预置任何默认值
        self.whitelist: Set[str] = self._load_or_create_json(whitelist_path, set())
        self.blacklist: Set[str] = self._load_or_create_json(blacklist_path, set())

    def _load_or_create_json(self, path: Path, default: Set[str]) -> Set[str]:
        """通用加载 JSON 集合，如果不存在则创建并写入默认值"""
        if not path.exists():
            # 立即创建文件 (写入空列表)
            self._save_json(path, default)
            console.print(f"[dim]已创建空白配置文件: {path}[/dim]")
            return default

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return set(data)
        except Exception as e:
            console.print(f"[red]文件 {path} 加载失败: {e}[/red]")
            return default

    def _save_json(self, path: Path, data: Set[str]):
        """通用保存 JSON 集合"""
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(sorted(list(data)), f, indent=2, ensure_ascii=False)
        except Exception as e:
            console.print(f"[red]文件 {path} 保存失败: {e}[/red]")

    # --- Whitelist Operations ---
    def get_all_tags(self) -> List[str]:
        return sorted(list(self.whitelist))

    def add_tag(self, tag: str) -> bool:
        """添加标签到白名单 (如果不在黑名单中)"""
        tag = tag.strip()
        if not tag:
            return False

        # 检查黑名单
        if tag in self.blacklist:
            console.print(f"[yellow]拒绝添加标签 '{tag}' (在黑名单中)[/yellow]")
            return False

        if tag in self.whitelist:
            return False

        self.whitelist.add(tag)
        self._save_json(self.whitelist_path, self.whitelist)
        return True

    def remove_tag(self, tag: str) -> bool:
        if tag not in self.whitelist:
            return False
        self.whitelist.remove(tag)
        self._save_json(self.whitelist_path, self.whitelist)
        return True

    # --- Blacklist Operations ---
    def get_blacklist(self) -> List[str]:
        return sorted(list(self.blacklist))

    def add_to_blacklist(self, tag: str) -> bool:
        """添加到黑名单 (并从白名单中移除)"""
        tag = tag.strip()
        if not tag:
            return False

        if tag in self.blacklist:
            return False

        self.blacklist.add(tag)
        self._save_json(self.blacklist_path, self.blacklist)

        # 如果白名单里有，由于互斥原则，应该移除
        if tag in self.whitelist:
            self.remove_tag(tag)
            console.print(f"[yellow]标签 '{tag}' 已从白名单移至黑名单[/yellow]")

        return True

    def remove_from_blacklist(self, tag: str) -> bool:
        if tag not in self.blacklist:
            return False
        self.blacklist.remove(tag)
        self._save_json(self.blacklist_path, self.blacklist)
        return True

    def is_blacklisted(self, tag: str) -> bool:
        return tag in self.blacklist

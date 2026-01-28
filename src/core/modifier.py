import frontmatter
from pathlib import Path
from typing import List, Union, Any
from rich.console import Console

console = Console()

class FileModifier:
    def __init__(self, file_path: Path):
        self.file_path = file_path
        try:
            # 显式转换为 str，满足类型检查和兼容性
            self.post = frontmatter.load(str(file_path))
        except Exception as e:
            # 如果加载失败（例如非 utf-8 文件），抛出异常让上层处理
            raise ValueError(f"无法解析文件 Frontmatter: {e}")

    def update_tags(self, new_tags: List[str]) -> bool:
        """
        更新文件的 tags。
        合并现有 tags 和 new_tags，去重。
        """
        current_tags_raw = self.post.get("tags", [])

        # 规范化 current_tags 为列表
        if current_tags_raw is None:
            current_tags = []
        elif isinstance(current_tags_raw, str):
            current_tags = [current_tags_raw]
        elif isinstance(current_tags_raw, list):
            current_tags = current_tags_raw
        else:
            # 可能是 int, float 等意外类型
            current_tags = [str(current_tags_raw)]

        # 转换为 set 去重
        tag_set = set(current_tags)
        tag_set.update(new_tags)

        # 转回列表并排序
        final_tags = sorted(list(tag_set))

        # 如果没有变化，直接返回 False
        if final_tags == sorted(current_tags):
            return False

        self.post["tags"] = final_tags
        return True

    def append_callout(self, callout_content: str):
        """
        在文末追加 Callout
        """
        if not callout_content:
            return

        # 确保与正文有空行分隔
        content = self.post.content
        if not content.endswith("\n"):
            content += "\n"
        if not content.endswith("\n\n"):
            content += "\n"

        self.post.content = content + callout_content + "\n"

    def save(self):
        """
        保存文件，根据标签数量决定 YAML 格式
        tags <= 5: 行内列表 [a, b]
        tags > 5: 多行列表 - a
        """
        # 手动序列化 Frontmatter 以控制格式
        # 注意：这是一种折衷方案，为了满足特定的格式需求
        tags = self.post.get("tags", [])

        # 再次确保 tags 是列表
        if not isinstance(tags, list):
            if tags is None: tags = []
            else: tags = [str(tags)]

        # 构造 YAML 头
        yaml_lines = ["---"]

        # 处理其他 metadata (保留除了 tags 以外的所有字段)
        for key, value in self.post.metadata.items():
            if key == "tags":
                continue
            # 简单的 key: value 序列化
            # 如果 value 是复杂对象（如 dict/list），这里直接转 str 可能会不美观
            # 但对于普通 Obsidian 笔记，metadata 通常比较简单
            yaml_lines.append(f"{key}: {value}")

        # 专门处理 Tags
        if tags:
            if len(tags) <= 5:
                # 行内格式: tags: [a, b, c]
                tags_str = ", ".join(tags)
                yaml_lines.append(f"tags: [{tags_str}]")
            else:
                # 多行格式
                yaml_lines.append("tags:")
                for t in tags:
                    yaml_lines.append(f"  - {t}")

        yaml_lines.append("---\n")

        # 写入文件
        new_content = "\n".join(yaml_lines) + self.post.content
        try:
            self.file_path.write_text(new_content, encoding="utf-8")
            console.print(f"[green]✔ 文件 {self.file_path.name} 已更新[/green]")
        except Exception as e:
            console.print(f"[bold red]文件写入失败: {e}[/bold red]")

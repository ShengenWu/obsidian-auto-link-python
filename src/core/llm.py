from typing import List, Dict, Any, Optional
from rich.console import Console
import json
import re
import yaml
from pathlib import Path

# LangChain Clients
from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.core.config import AppConfig, ProviderConfig

console = Console()

class LLMClient:
    def __init__(self, config: AppConfig):
        self.app_config = config
        self.llm_config = config.get_active_llm_config()
        self.prompts = self._load_prompts(config.prompt_file)
        self.llm = self._init_llm_model()

    def _load_prompts(self, prompt_file: str) -> Dict[str, Any]:
        """加载外部 Prompt 配置文件"""
        path = Path(prompt_file)
        if not path.exists():
            console.print(f"[yellow]警告: Prompt 文件 {prompt_file} 未找到，将使用默认模板[/yellow]")
            return {}

        try:
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            console.print(f"[red]Prompt 文件加载失败: {e}[/red]")
            return {}

    def _init_llm_model(self) -> BaseChatModel:
        """根据 provider_type 初始化对应的 LLM 客户端"""
        p_type = self.llm_config.provider_type
        cfg = self.llm_config

        try:
            if p_type in ["openai", "openai_compatible"]:
                return ChatOpenAI(
                    model=cfg.model,
                    openai_api_key=cfg.api_key or "dummy",
                    openai_api_base=cfg.base_url,
                    temperature=cfg.temperature,
                    max_tokens=2048
                )

            elif p_type == "anthropic":
                try:
                    from langchain_anthropic import ChatAnthropic
                    return ChatAnthropic(
                        model=cfg.model,
                        api_key=cfg.api_key,
                        temperature=cfg.temperature,
                        max_tokens=2048
                    )
                except ImportError:
                    raise ImportError("请安装 langchain-anthropic 以使用 Claude 模型")

            elif p_type == "google":
                try:
                    from langchain_google_genai import ChatGoogleGenerativeAI
                    return ChatGoogleGenerativeAI(
                        model=cfg.model,
                        google_api_key=cfg.api_key,
                        temperature=cfg.temperature,
                        max_output_tokens=2048
                    )
                except ImportError:
                    raise ImportError("请安装 langchain-google-genai 以使用 Gemini 模型")

            else:
                raise ValueError(f"不支持的 provider_type: {p_type}")

        except Exception as e:
            console.print(f"[bold red]LLM 初始化失败 ({p_type}): {e}[/bold red]")
            raise e

    def _get_prompt_template(self, key: str, default: str) -> str:
        """获取 Prompt 模板，优先从文件读取，否则使用默认值"""
        if self.prompts and key in self.prompts:
            return self.prompts[key].get("template", default)
        return default

    def generate_tags(self, content: str, existing_tags: List[str] = None) -> List[str]:
        """根据笔记内容生成标签"""
        default_template = """你是一个专业的知识管理助手。请提取 3-5 个核心标签。
        现有标签：{existing_tags}
        仅输出 JSON 列表，如 ["tag1", "tag2"]。
        内容：{content}"""

        template = self._get_prompt_template("tagging", default_template)
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.llm | StrOutputParser()

        tags_str = ", ".join(existing_tags) if existing_tags else "无"

        try:
            response = chain.invoke({
                "content": content[:3000],
                "existing_tags": tags_str
            })
            cleaned_response = re.sub(r"```json|```", "", response).strip()
            # 尝试提取列表部分（防止 LLM 说废话）
            match = re.search(r'\[.*\]', cleaned_response, re.DOTALL)
            if match:
                cleaned_response = match.group(0)

            tags = json.loads(cleaned_response)
            return tags if isinstance(tags, list) else []
        except Exception as e:
            console.print(f"[red]生成标签失败: {e}[/red]")
            return []

    def generate_insight(self, current_note_title: str, current_note_content: str, related_docs: List[Dict]) -> str:
        """生成关联见解"""
        if not related_docs:
            return ""

        context_str = ""
        for i, doc in enumerate(related_docs):
            context_str += f"\n[参考笔记 {i+1}]: {doc['source']}\n内容摘要: {doc['path']}\n" # 这里简单用path代替content摘要，节省token

        default_template = """分析关联并生成 Obsidian Callout。
        当前笔记：{current_title}
        参考：{context}
        内容：{current_content}"""

        template = self._get_prompt_template("linking", default_template)
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.llm | StrOutputParser()

        try:
            response = chain.invoke({
                "current_title": current_note_title,
                "context": context_str,
                "current_content": current_note_content[:2000]
            })
            if "NO_RELATION" in response:
                return ""
            return response
        except Exception as e:
            console.print(f"[red]生成见解失败: {e}[/red]")
            return ""

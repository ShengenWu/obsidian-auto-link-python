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
        self.prompts = self._load_prompts(config.prompt_file)

        # 1. 初始化主模型
        self.main_config = config.get_active_llm_config()
        self.llm = self._init_llm_model(self.main_config)

        # 2. 初始化摘要模型 (如果需要)
        sum_cfg = config.summarization
        if sum_cfg.enable and sum_cfg.provider:
            if sum_cfg.provider not in config.providers:
                console.print(f"[yellow]摘要 Provider '{sum_cfg.provider}' 未定义，将回退到主模型[/yellow]")
                self.summary_llm = self.llm
            else:
                self.summary_llm = self._init_llm_model(config.providers[sum_cfg.provider])
        else:
            self.summary_llm = self.llm # 复用主模型

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

    def _init_llm_model(self, cfg: ProviderConfig) -> BaseChatModel:
        """初始化 LLM 客户端"""
        p_type = cfg.provider_type

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
        if self.prompts and key in self.prompts:
            return self.prompts[key].get("template", default)
        return default

    def generate_tags(self, content: str, existing_tags: List[str] = None) -> List[str]:
        """根据笔记内容生成标签 (使用主模型)"""
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
            match = re.search(r'\[.*\]', cleaned_response, re.DOTALL)
            if match:
                cleaned_response = match.group(0)

            tags = json.loads(cleaned_response)
            return tags if isinstance(tags, list) else []
        except Exception as e:
            # 抛出异常以便上层（main.py）感知失败
            raise Exception(f"生成标签失败: {e}")

    def summarize_content(self, content: str) -> str:
        """为长文本生成摘要 (使用摘要模型)"""
        cfg = self.app_config.summarization

        default_template = """请生成 200 字以内的摘要。内容：{content}"""
        template = self._get_prompt_template("summarize", default_template)
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.summary_llm | StrOutputParser() # 使用摘要模型

        try:
            # 使用配置的 max_input_length 进行截断
            return chain.invoke({"content": content[:cfg.max_input_length]})
        except Exception as e:
            # 摘要失败可以降级为截断，不必视为整个任务失败，但最好记录日志
            console.print(f"[yellow]摘要生成失败: {e}，将截取原文[/yellow]")
            return content[:500] + "..."

    def generate_insight(self, current_note_title: str, current_note_content: str, related_docs: List[Dict]) -> str:
        """生成关联见解 (使用主模型)"""
        if not related_docs:
            return ""

        sum_cfg = self.app_config.summarization

        context_str = ""
        for i, doc in enumerate(related_docs):
            raw_content = doc.get('content', '')

            # --- 摘要/截断策略 ---
            if len(raw_content) > sum_cfg.threshold:
                if sum_cfg.enable:
                    # 开启摘要：调用模型
                    # console.print(f"[dim]正在为参考笔记 {doc['source']} 生成摘要...[/dim]")
                    summary = self.summarize_content(raw_content)
                    display_content = f"[AI摘要] {summary}"
                else:
                    # 关闭摘要：硬截断
                    limit = sum_cfg.hard_truncate_length
                    display_content = raw_content[:limit] + f"... (截断至{limit}字)"
            else:
                # 短文直接用
                display_content = raw_content

            context_str += f"\n[参考笔记 {i+1}]: {doc['source']}\n内容: {display_content}\n"

        default_template = """分析关联并生成 Obsidian Callout。
        当前笔记：{current_title}
        参考：{context}
        内容：{current_content}"""

        template = self._get_prompt_template("linking", default_template)
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.llm | StrOutputParser() # 使用主模型

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
            raise Exception(f"生成见解失败: {e}")

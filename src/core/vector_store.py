import shutil
from pathlib import Path
from typing import List, Dict, Any, Tuple
from rich.console import Console

# LangChain Imports
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

from src.core.config import EmbeddingConfig, ProviderConfig

console = Console()

class VectorStoreManager:
    def __init__(self, embedding_config: EmbeddingConfig, llm_config: ProviderConfig, persist_directory: str = "./chroma_db"):
        self.config = embedding_config
        self.persist_directory = persist_directory
        self.embedding_function = self._init_embedding_model(embedding_config, llm_config)
        self.db = self._init_db()

    def _init_embedding_model(self, emb_cfg: EmbeddingConfig, llm_cfg: ProviderConfig):
        """初始化 Embedding 模型"""
        try:
            if emb_cfg.type == "local":
                console.print(f"[blue]正在加载本地 Embedding 模型: {emb_cfg.model_name}...[/blue]")
                console.print("[dim]首次运行可能需要下载模型，请耐心等待...[/dim]")
                # 使用 CPU 推理，保证兼容性
                return HuggingFaceEmbeddings(
                    model_name=emb_cfg.model_name,
                    model_kwargs={'device': 'cpu'},
                    encode_kwargs={'normalize_embeddings': True}
                )
            elif emb_cfg.type == "api":
                console.print(f"[blue]正在初始化 API Embedding 模型...[/blue]")
                if not llm_cfg.api_key:
                    console.print("[yellow]警告: 未配置 API Key，API Embedding 可能失败[/yellow]")

                return OpenAIEmbeddings(
                    model=emb_cfg.model_name,
                    openai_api_key=llm_cfg.api_key,
                    openai_api_base=llm_cfg.base_url
                )
            else:
                raise ValueError(f"不支持的 Embedding 类型: {emb_cfg.type}")
        except Exception as e:
            console.print(f"[bold red]Embedding 模型初始化失败: {e}[/bold red]")
            raise e

    def _init_db(self):
        """初始化 Chroma 向量库"""
        return Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embedding_function
        )

    def add_texts(self, texts: List[str], metadatas: List[Dict[str, Any]]):
        """添加文本到向量库 (先删后加，防止重复)"""
        if not texts:
            return

        # 1. 清理旧数据
        # 提取所有涉及到 source 文件名
        sources_to_delete = list(set([m.get("source") for m in metadatas if m.get("source")]))

        if sources_to_delete:
            try:
                # 使用 where 过滤器删除旧记录
                # Chroma 的 filter 语法: where={"source": {"$in": sources_to_delete}}
                # 但 delete 方法通常接受 ids 或 where
                # 逐个删除比较稳妥，防止过滤器语法兼容性问题
                for source in sources_to_delete:
                    self.db.delete(where={"source": source})
                    # console.print(f"[dim]已清理旧向量: {source}[/dim]")
            except Exception as e:
                console.print(f"[yellow]清理旧向量失败 (可能是首次运行): {e}[/yellow]")

        # 2. 存入新数据
        console.print(f"正在存入 {len(texts)} 条向量数据...")
        self.db.add_texts(texts=texts, metadatas=metadatas)

    def search(self, query: str, k: int = 3) -> List[Tuple[Document, float]]:
        """相似度搜索"""
        # 返回结果为 (Document, score) 列表
        return self.db.similarity_search_with_score(query, k=k)

    def reset(self):
        """重置向量库 (物理删除数据库文件)"""
        console.print(f"[yellow]正在重置向量数据库: {self.persist_directory}[/yellow]")

        # 尝试通过 API 删除集合 (如果有必要)
        try:
            self.db.delete_collection()
        except:
            pass

        # 物理删除文件夹，确保彻底重置
        if Path(self.persist_directory).exists():
             shutil.rmtree(self.persist_directory)
             console.print("[dim]已删除旧数据库文件[/dim]")

        # 重新初始化
        self.db = self._init_db()

from typing import Optional, Literal, Dict, Any
from pathlib import Path
import yaml
import os
import re
from pydantic import BaseModel, Field, ValidationError

class EmbeddingConfig(BaseModel):
    type: Literal["local", "api"] = "local"
    model_name: str = "BAAI/bge-large-zh-v1.5"

class ProviderConfig(BaseModel):
    provider_type: Literal["openai", "openai_compatible", "anthropic", "google"]
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model: str
    temperature: float = 0.3

class PipelineConfig(BaseModel):
    dry_run: bool = False
    backup: bool = True

class SafetyConfig(BaseModel):
    enable_backup: bool = True
    backup_retention_days: int = 7
    backup_path: str = "./.auto_link_backups"

class ReportingConfig(BaseModel):
    enable_summary: bool = True
    log_folder: str = "System/Auto-Link-Logs"
    summary_template: Literal["markdown", "json"] = "markdown"

class AppConfig(BaseModel):
    vault_path: Path
    active_provider: str
    providers: Dict[str, ProviderConfig]
    prompt_file: str = "prompts.yaml"

    embedding: EmbeddingConfig
    pipeline: PipelineConfig = Field(default_factory=PipelineConfig)
    safety: SafetyConfig = Field(default_factory=SafetyConfig)
    reporting: ReportingConfig = Field(default_factory=ReportingConfig)

    def get_active_llm_config(self) -> ProviderConfig:
        """获取当前激活的 LLM 配置"""
        if self.active_provider not in self.providers:
            raise ValueError(f"当前激活的 provider '{self.active_provider}' 未在 providers 中定义")
        return self.providers[self.active_provider]

def expand_env_vars(data: Any) -> Any:
    """递归处理字典/列表中的环境变量占位符 ${VAR_NAME}"""
    if isinstance(data, dict):
        return {k: expand_env_vars(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [expand_env_vars(v) for v in data]
    elif isinstance(data, str):
        # 匹配 ${VAR_NAME} 格式
        pattern = re.compile(r'\$\{([^}]+)\}')

        def replace(match):
            var_name = match.group(1)
            return os.environ.get(var_name, match.group(0)) # 如果环境变量不存在，保持原样

        return pattern.sub(replace, data)
    else:
        return data

def load_config(config_path: str = "config.yaml") -> AppConfig:
    """加载并校验配置文件 (支持环境变量替换)"""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"配置文件未找到: {config_path}")

    with open(path, "r", encoding="utf-8") as f:
        try:
            raw_config = yaml.safe_load(f)
            if raw_config is None:
                raw_config = {}

            # 预处理：替换环境变量
            expanded_config = expand_env_vars(raw_config)

            return AppConfig(**expanded_config)
        except yaml.YAMLError as e:
            raise ValueError(f"配置文件 YAML 格式错误: {e}")
        except ValidationError as e:
            raise ValueError(f"配置校验失败:\n{e}")

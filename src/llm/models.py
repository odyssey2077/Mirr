from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


class Role(str, Enum):
    """Message roles"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class Message:
    """Represents a single message in a conversation"""
    role: Role
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary format for litellm"""
        return {"role": self.role.value, "content": self.content}


@dataclass
class Usage:
    """Token usage and cost information"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    prompt_cost: float
    completion_cost: float
    total_cost: float
    model: str
    
    @property
    def cost_breakdown(self) -> Dict[str, Any]:
        return {
            "prompt": {"tokens": self.prompt_tokens, "cost": self.prompt_cost},
            "completion": {"tokens": self.completion_tokens, "cost": self.completion_cost},
            "total": {"tokens": self.total_tokens, "cost": self.total_cost},
            "model": self.model
        }


@dataclass
class Response:
    """LLM response with metadata"""
    content: str
    usage: Usage
    model: str
    response_time: float  # seconds
    timestamp: datetime = field(default_factory=datetime.now)
    raw_response: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class ModelConfig:
    """Configuration for a specific model"""
    name: str
    provider: str
    max_tokens: Optional[int] = None
    temperature: float = 0.7
    top_p: float = 1.0
    stream: bool = False
    timeout: int = 60
    retry_count: int = 3
    api_base: Optional[str] = None
    api_key: Optional[str] = None
    
    # Cost per 1K tokens (in USD)
    input_cost_per_1k: Optional[float] = None
    output_cost_per_1k: Optional[float] = None
    
    @property
    def litellm_model_name(self) -> str:
        """Get the model name in litellm format"""
        if self.provider == "openai":
            return self.name
        elif self.provider == "anthropic":
            return f"claude-{self.name}" if not self.name.startswith("claude-") else self.name
        elif self.provider == "google":
            return f"gemini/{self.name}" if not self.name.startswith("gemini/") else self.name
        elif self.provider == "deepseek":
            return f"deepseek/{self.name}" if not self.name.startswith("deepseek/") else self.name
        else:
            return self.name


# Preset model configurations
MODEL_PRESETS = {
    # OpenAI models
    "gpt-4": ModelConfig(
        name="gpt-4", 
        provider="openai",
        input_cost_per_1k=0.03,
        output_cost_per_1k=0.06
    ),
    "gpt-4-turbo": ModelConfig(
        name="gpt-4-turbo-preview",
        provider="openai", 
        input_cost_per_1k=0.01,
        output_cost_per_1k=0.03
    ),
    "gpt-3.5-turbo": ModelConfig(
        name="gpt-3.5-turbo",
        provider="openai",
        input_cost_per_1k=0.0005,
        output_cost_per_1k=0.0015
    ),
    
    # Anthropic models
    "claude-3-opus": ModelConfig(
        name="claude-3-opus-20240229",
        provider="anthropic",
        max_tokens=4096,
        input_cost_per_1k=0.015,
        output_cost_per_1k=0.075
    ),
    "claude-3-sonnet": ModelConfig(
        name="claude-3-sonnet-20240229",
        provider="anthropic",
        max_tokens=4096,
        input_cost_per_1k=0.003,
        output_cost_per_1k=0.015
    ),
    "claude-3-haiku": ModelConfig(
        name="claude-3-haiku-20240307",
        provider="anthropic",
        max_tokens=4096,
        input_cost_per_1k=0.00025,
        output_cost_per_1k=0.00125
    ),
    
    # Google models
    "gemini-pro": ModelConfig(
        name="gemini-pro",
        provider="google",
        input_cost_per_1k=0.000125,
        output_cost_per_1k=0.000375
    ),
    
    # DeepSeek models
    "deepseek-coder": ModelConfig(
        name="deepseek-coder",
        provider="deepseek",
        input_cost_per_1k=0.0001,
        output_cost_per_1k=0.0002
    ),
}
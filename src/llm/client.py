import os
import time
import json
from typing import List, Optional, Union, Dict, Any
from datetime import datetime
import litellm
from litellm import completion, completion_cost
from dotenv import load_dotenv

from .models import Message, Response, Usage, ModelConfig, Role, MODEL_PRESETS
from .history import ConversationHistory

# Load environment variables
load_dotenv()

# Configure litellm
litellm.drop_params = True  # Drop unsupported params instead of erroring
litellm.set_verbose = False  # Set to True for debugging


class LLMClient:
    """
    Unified LLM client supporting multiple providers via litellm
    
    Features:
    - Multi-model support (OpenAI, Anthropic, Google, DeepSeek, etc.)
    - Cost tracking per call and per session
    - Conversation history with persistence
    - Automatic retries with exponential backoff
    - Raw input/output logging for debugging
    """
    
    def __init__(
        self,
        model: Optional[str] = None,
        config: Optional[ModelConfig] = None,
        history_file: Optional[str] = None,
        log_dir: str = "logs/llm"
    ):
        """
        Initialize LLM client
        
        Args:
            model: Model name (e.g., "gpt-4", "claude-3-opus")
            config: Custom ModelConfig (overrides model preset)
            history_file: Path to save conversation history
            log_dir: Directory for raw input/output logs
        """
        # Set up model configuration
        if config:
            self.config = config
        elif model and model in MODEL_PRESETS:
            self.config = MODEL_PRESETS[model]
        else:
            # Default to Gemini Pro
            default_model = os.getenv("DEFAULT_MODEL", "gemini-pro")
            self.config = MODEL_PRESETS.get(default_model, MODEL_PRESETS["gemini-pro"])
        
        # Initialize history and logging
        self.history = ConversationHistory(history_file)
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        # Session tracking
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_usage = {
            "total_tokens": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_cost": 0.0,
            "input_cost": 0.0,
            "output_cost": 0.0,
            "call_count": 0
        }
    
    def _get_api_key(self) -> Optional[str]:
        """Get API key for current provider"""
        if self.config.api_key:
            return self.config.api_key
        
        # Map provider to environment variable
        key_map = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "google": "GEMINI_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY"
        }
        
        env_var = key_map.get(self.config.provider)
        return os.getenv(env_var) if env_var else None
    
    def _log_raw_io(self, messages: List[Dict[str, str]], response: Any, usage: Usage):
        """Log raw input/output for debugging"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "model": self.config.litellm_model_name,
            "input": messages,
            "output": response,
            "usage": usage.cost_breakdown,
            "response_time": usage.response_time if hasattr(usage, 'response_time') else None
        }
        
        # Save to timestamped file
        log_file = os.path.join(
            self.log_dir,
            f"{self.session_id}_{int(time.time())}.json"
        )
        with open(log_file, 'w') as f:
            json.dump(log_entry, f, indent=2, default=str)
    
    def _calculate_cost(self, usage_info: Dict[str, int]) -> Usage:
        """Calculate token usage and costs"""
        prompt_tokens = usage_info.get("prompt_tokens", 0)
        completion_tokens = usage_info.get("completion_tokens", 0)
        total_tokens = usage_info.get("total_tokens", prompt_tokens + completion_tokens)
        
        # Try to get cost from litellm first
        try:
            total_cost = completion_cost(
                model=self.config.litellm_model_name,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens
            )
            prompt_cost = (prompt_tokens / 1000) * (self.config.input_cost_per_1k or 0)
            completion_cost = (completion_tokens / 1000) * (self.config.output_cost_per_1k or 0)
        except:
            # Fall back to manual calculation
            prompt_cost = (prompt_tokens / 1000) * (self.config.input_cost_per_1k or 0)
            completion_cost = (completion_tokens / 1000) * (self.config.output_cost_per_1k or 0)
            total_cost = prompt_cost + completion_cost
        
        return Usage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            prompt_cost=prompt_cost,
            completion_cost=completion_cost,
            total_cost=total_cost,
            model=self.config.litellm_model_name
        )
    
    def chat(
        self,
        messages: Union[List[Message], List[Dict[str, str]], str],
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Response:
        """
        Send messages to LLM and get response
        
        Args:
            messages: List of Message objects, dicts, or a single string
            system_prompt: Optional system prompt to prepend
            **kwargs: Additional parameters passed to litellm
            
        Returns:
            Response object with content, usage, and metadata
        """
        start_time = time.time()
        
        # Convert messages to proper format
        formatted_messages = []
        
        # Add system prompt if provided
        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})
        
        # Handle different input formats
        if isinstance(messages, str):
            formatted_messages.append({"role": "user", "content": messages})
        elif isinstance(messages, list):
            for msg in messages:
                if isinstance(msg, Message):
                    formatted_messages.append(msg.to_dict())
                elif isinstance(msg, dict):
                    formatted_messages.append(msg)
                else:
                    raise ValueError(f"Invalid message type: {type(msg)}")
        else:
            raise ValueError(f"Invalid messages type: {type(messages)}")
        
        # Prepare completion parameters
        completion_params = {
            "model": self.config.litellm_model_name,
            "messages": formatted_messages,
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
            "stream": False,  # Always False for now
            "timeout": self.config.timeout,
            **kwargs
        }
        
        # Add max_tokens if specified
        if self.config.max_tokens:
            completion_params["max_tokens"] = self.config.max_tokens
        
        # Add API key if available
        api_key = self._get_api_key()
        if api_key:
            completion_params["api_key"] = api_key
        
        # Add custom API base if specified
        if self.config.api_base:
            completion_params["api_base"] = self.config.api_base
        
        # Retry logic
        last_error = None
        for attempt in range(self.config.retry_count):
            try:
                # Make API call
                response = completion(**completion_params)
                
                # Extract content and usage
                content = response.choices[0].message.content
                usage = self._calculate_cost(response.usage)
                
                # Update session tracking
                self.session_usage["total_tokens"] += usage.total_tokens
                self.session_usage["input_tokens"] += usage.prompt_tokens
                self.session_usage["output_tokens"] += usage.completion_tokens
                self.session_usage["total_cost"] += usage.total_cost
                self.session_usage["input_cost"] += usage.prompt_cost
                self.session_usage["output_cost"] += usage.completion_cost
                self.session_usage["call_count"] += 1
                
                # Create response object
                response_obj = Response(
                    content=content,
                    usage=usage,
                    model=self.config.litellm_model_name,
                    response_time=time.time() - start_time,
                    raw_response=response.model_dump() if hasattr(response, 'model_dump') else None
                )
                
                # Log raw I/O
                self._log_raw_io(formatted_messages, response_obj.raw_response, usage)
                
                # Add to history
                for msg in formatted_messages:
                    if msg["role"] != "system":  # Don't store system prompts in history
                        self.history.add_message(Role(msg["role"]), msg["content"])
                self.history.add_message(Role.ASSISTANT, content)
                
                return response_obj
                
            except Exception as e:
                last_error = e
                if attempt < self.config.retry_count - 1:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                else:
                    # Final attempt failed
                    error_response = Response(
                        content="",
                        usage=Usage(0, 0, 0, 0.0, 0.0, 0.0, self.config.litellm_model_name),
                        model=self.config.litellm_model_name,
                        response_time=time.time() - start_time,
                        error=str(last_error)
                    )
                    
                    # Log error
                    self._log_raw_io(formatted_messages, {"error": str(last_error)}, error_response.usage)
                    
                    raise RuntimeError(f"LLM call failed after {self.config.retry_count} attempts: {last_error}")
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current session usage"""
        call_count = max(1, self.session_usage["call_count"])
        return {
            "session_id": self.session_id,
            "model": self.config.litellm_model_name,
            "total_calls": self.session_usage["call_count"],
            "total_tokens": self.session_usage["total_tokens"],
            "input_tokens": self.session_usage["input_tokens"],
            "output_tokens": self.session_usage["output_tokens"],
            "total_cost": round(self.session_usage["total_cost"], 4),
            "input_cost": round(self.session_usage["input_cost"], 4),
            "output_cost": round(self.session_usage["output_cost"], 4),
            "average_tokens_per_call": round(self.session_usage["total_tokens"] / call_count, 2),
            "average_input_tokens_per_call": round(self.session_usage["input_tokens"] / call_count, 2),
            "average_output_tokens_per_call": round(self.session_usage["output_tokens"] / call_count, 2),
            "average_cost_per_call": round(self.session_usage["total_cost"] / call_count, 4)
        }
    
    def clear_history(self):
        """Clear conversation history"""
        self.history.clear()
    
    def save_history(self):
        """Save conversation history to file"""
        self.history.save()
    
    def switch_model(self, model: str):
        """Switch to a different model"""
        if model in MODEL_PRESETS:
            self.config = MODEL_PRESETS[model]
        else:
            raise ValueError(f"Unknown model: {model}. Available: {list(MODEL_PRESETS.keys())}")
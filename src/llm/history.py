import json
import os
from typing import List, Dict, Optional, Any
from datetime import datetime
from .models import Message, Role


class ConversationHistory:
    """
    Manages conversation history with persistence
    
    Features:
    - Add/remove messages
    - Save/load from file
    - Export in various formats
    - Token counting (approximate)
    """
    
    def __init__(self, filepath: Optional[str] = None):
        """
        Initialize conversation history
        
        Args:
            filepath: Optional path to save/load history
        """
        self.filepath = filepath
        self.messages: List[Message] = []
        self.metadata: Dict[str, Any] = {
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }
        
        # Load existing history if file exists
        if filepath and os.path.exists(filepath):
            self.load()
    
    def add_message(self, role: Role, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Add a message to history"""
        message = Message(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        self.messages.append(message)
        self.metadata["last_updated"] = datetime.now().isoformat()
    
    def get_messages(self, limit: Optional[int] = None) -> List[Message]:
        """Get messages, optionally limiting to most recent N"""
        if limit:
            return self.messages[-limit:]
        return self.messages
    
    def get_formatted_messages(self, limit: Optional[int] = None) -> List[Dict[str, str]]:
        """Get messages formatted for LLM input"""
        messages = self.get_messages(limit)
        return [msg.to_dict() for msg in messages]
    
    def clear(self):
        """Clear all messages"""
        self.messages = []
        self.metadata["last_updated"] = datetime.now().isoformat()
    
    def save(self, filepath: Optional[str] = None):
        """Save history to file"""
        save_path = filepath or self.filepath
        if not save_path:
            raise ValueError("No filepath specified for saving")
        
        data = {
            "metadata": self.metadata,
            "messages": [
                {
                    "role": msg.role.value,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "metadata": msg.metadata
                }
                for msg in self.messages
            ]
        }
        
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load(self, filepath: Optional[str] = None):
        """Load history from file"""
        load_path = filepath or self.filepath
        if not load_path:
            raise ValueError("No filepath specified for loading")
        
        with open(load_path, 'r') as f:
            data = json.load(f)
        
        self.metadata = data.get("metadata", {})
        self.messages = []
        
        for msg_data in data.get("messages", []):
            message = Message(
                role=Role(msg_data["role"]),
                content=msg_data["content"],
                timestamp=datetime.fromisoformat(msg_data["timestamp"]),
                metadata=msg_data.get("metadata", {})
            )
            self.messages.append(message)
    
    def export_markdown(self) -> str:
        """Export conversation as markdown"""
        lines = [f"# Conversation History\n"]
        lines.append(f"Created: {self.metadata.get('created_at', 'Unknown')}\n")
        lines.append(f"Last Updated: {self.metadata.get('last_updated', 'Unknown')}\n")
        lines.append("---\n")
        
        for msg in self.messages:
            role_display = msg.role.value.title()
            timestamp = msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            lines.append(f"## {role_display} ({timestamp})\n")
            lines.append(f"{msg.content}\n")
            lines.append("---\n")
        
        return "\n".join(lines)
    
    def estimate_tokens(self) -> int:
        """
        Estimate total tokens in conversation
        Note: This is a rough estimate (4 chars ≈ 1 token)
        """
        total_chars = sum(len(msg.content) for msg in self.messages)
        return total_chars // 4
    
    def truncate_to_token_limit(self, max_tokens: int, keep_system: bool = True):
        """
        Truncate history to fit within token limit
        Keeps most recent messages and optionally system messages
        """
        if self.estimate_tokens() <= max_tokens:
            return
        
        # Separate system and non-system messages
        system_messages = [msg for msg in self.messages if msg.role == Role.SYSTEM]
        other_messages = [msg for msg in self.messages if msg.role != Role.SYSTEM]
        
        # Start with system messages if keeping them
        if keep_system:
            new_messages = system_messages[:]
            available_tokens = max_tokens - sum(len(msg.content) // 4 for msg in system_messages)
        else:
            new_messages = []
            available_tokens = max_tokens
        
        # Add other messages from most recent
        for msg in reversed(other_messages):
            msg_tokens = len(msg.content) // 4
            if msg_tokens <= available_tokens:
                new_messages.insert(len(system_messages) if keep_system else 0, msg)
                available_tokens -= msg_tokens
            else:
                break
        
        self.messages = new_messages
    
    def __len__(self) -> int:
        return len(self.messages)
    
    def __repr__(self) -> str:
        return f"ConversationHistory(messages={len(self.messages)}, tokens≈{self.estimate_tokens()})"
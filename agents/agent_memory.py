from typing import List, Dict, Any
from dataclasses import dataclass, field

@dataclass
class AgentMemory:
    """Simple memory system for agent conversations"""
    messages: List[Dict[str, str]] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    max_messages: int = 20

    def add_message(self, role: str, content: str):
        """Add message to memory"""
        self.messages.append({"role": role, "content": content})

        # Keep only last max_messages
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]

    def get_conversation_history(self) -> str:
        """Get formatted conversation history"""
        history = []
        for msg in self.messages[-10:]:  # Last 10 messages
            history.append(f"{msg['role']}: {msg['content']}")
        return "\n".join(history)

    def clear(self):
        """Clear memory"""
        self.messages.clear()
        self.context.clear()

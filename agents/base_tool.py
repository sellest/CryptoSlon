from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable

class BaseTool(ABC):
    """Abstract base class for agent tools"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description for LLM"""
        pass

    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        """Tool parameters schema"""
        pass

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """Execute the tool"""
        pass

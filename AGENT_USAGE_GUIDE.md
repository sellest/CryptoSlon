# BaseAgent Usage Guide

## Overview

The `BaseAgent` system provides a flexible AI agent framework that can:
- Use multiple tools to perform actions
- Maintain conversation memory
- Integrate with RAG for knowledge retrieval
- Support multiple LLM providers

## Quick Start

```bash
# Make sure your environment is set up
pip install -r requirements.txt

# Set up your API keys in .env (copy from .env.example)
cp .env.example .env
# Edit .env with your API keys

# Run the example
python example_agent_usage.py
```

## Architecture Components

### 1. BaseAgent (`agents/base_agent.py`)
Main orchestrator that:
- Manages conversation with LLM
- Executes tool calls
- Maintains memory and context
- Implements reasoning loop

### 2. Tools (`agents/tools/`)
_These tools are built as an example_

**Security Tools:**
- `PasswordAnalyzerTool` - Analyze password strength
- `HashGeneratorTool` - Generate secure hashes 
- `VulnerabilityCheckerTool` - Check code for security issues

**Search Tools:**
- `WebSearchTool` - Search the web for current information
- `KnowledgeSearchTool` - Search local knowledge base

### 3. Supporting Components
- `AgentMemory` - Conversation history management
- `ToolManager` - Tool registration and execution
- `RAGHelper` - Knowledge base integration

## Example Usage

```python
from agents.base_agent import BaseAgent
from agents.tools.security_tool import PasswordAnalyzerTool

# Create agent
agent = BaseAgent("SecurityBot", llm_provider="gigachat")

# Register tools
agent.register_tool(PasswordAnalyzerTool())

# Process requests
response = agent.process_request("Analyze the password 'test123'")
print(response)
```

## Tool Call Format

Tools are called via JSON format in LLM responses:
```json
{
  "tool": "password_analyzer",
  "parameters": {
    "password": "MyP@ssw0rd123"
  }
}
```

## Example Interactions

**Password Analysis:**
- Input: "Analyze the password 'MyP@ssw0rd123' for security"
- The agent will use `password_analyzer` tool and provide detailed analysis

**Vulnerability Check:**
- Input: "Check this code: cursor.execute('SELECT * FROM users WHERE id = ' + user_id)"  
- The agent will detect SQL injection vulnerability

**Hash Generation:**
- Input: "Generate a SHA-256 hash for 'sensitive_data'"
- The agent will use `hash_generator` tool

## Extending with Custom Tools

1. Create a tool class inheriting from `BaseTool`:
```python
from agents.base_tool import BaseTool

class MyCustomTool(BaseTool):
    @property
    def name(self) -> str:
        return "my_tool"
    
    @property 
    def description(self) -> str:
        return "Description for LLM"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {"param1": {"type": "string", "description": "..."}}
    
    def execute(self, **kwargs) -> Any:
        # Your tool logic here
        return result
```

2. Register with agent:
```python
agent.register_tool(MyCustomTool())
```

## Configuration Options

- `llm_provider`: "gigachat", "openai", "google", "groq"  
- `max_iterations`: Maximum reasoning loop iterations
- `vector_db_collection`: Optional RAG knowledge base

## Error Handling

The agent handles errors gracefully:
- Tool execution failures are reported to LLM
- LLM errors return user-friendly messages
- Maximum iteration limits prevent infinite loops

## For Hackathon Development

This agent framework is ideal for cybersecurity hackathon projects:
- Quick tool development and integration
- Multi-provider LLM support
- Built-in security-focused tools
- Easy to extend for specific use cases
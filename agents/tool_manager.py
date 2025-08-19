import json
import logging
from typing import Dict, Any, Optional, List
from agents.base_tool import BaseTool
from dataclasses import dataclass

@dataclass
class ToolResult:
    tool_name: str
    parameters: Dict[str, Any]
    result: Optional[Any] = None
    success: bool = False
    error_message: Optional[str] = None

class ToolManager:
    """Simple tool management for agents"""
    
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self.logger = logging.getLogger("tool_manager")
    
    def register_tool(self, tool: BaseTool):
        """Register a tool"""
        self.tools[tool.name] = tool
        self.logger.info(f"Registered tool: {tool.name}")
    
    def get_tools_description(self) -> str:
        """Get formatted description of available tools"""
        if not self.tools:
            return "No tools available"
        
        descriptions = []
        for tool in self.tools.values():
            descriptions.append(f"- {tool.name}: {tool.description}")
        
        return "\n".join(descriptions)
    
    def parse_tool_call(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse tool call from LLM response"""
        try:
            import re
            
            # First, try to extract from markdown code blocks
            code_block_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
            code_matches = re.findall(code_block_pattern, response, re.DOTALL)
            
            for code_match in code_matches:
                try:
                    parsed = json.loads(code_match.strip())
                    if isinstance(parsed, dict):
                        # Try to infer tool call from available tools
                        if 'password' in parsed and hasattr(self, 'tools') and 'password_analyzer' in self.tools:
                            self.logger.debug(f"Inferring password_analyzer tool call from: {parsed}")
                            return {
                                "tool": "password_analyzer",
                                "parameters": parsed
                            }
                        # Check if it's already a proper tool call
                        if 'tool' in parsed:
                            if 'parameters' not in parsed:
                                parsed['parameters'] = {}
                            return parsed
                except json.JSONDecodeError:
                    continue
            
            # Try multiple approaches to find JSON
            # Approach 1: Look for complete JSON objects with nested structure
            json_patterns = [
                r'\{[^{}]*"tool"[^{}]*"parameters"[^{}]*\{[^{}]*\}[^{}]*\}',  # Nested structure
                r'\{[^{}]*"tool"[^{}]*"parameters"[^{}]*\}',  # Simple structure
                r'\{.*?"tool".*?"parameters".*?\}',  # Greedy match
            ]
            
            for pattern in json_patterns:
                matches = re.findall(pattern, response, re.DOTALL)
                self.logger.debug(f"Pattern '{pattern}' found matches: {matches}")
                
                for match in matches:
                    try:
                        # Clean up the match
                        clean_match = match.strip()
                        parsed = json.loads(clean_match)
                        self.logger.debug(f"Successfully parsed JSON: {parsed}")
                        
                        if 'tool' in parsed and 'parameters' in parsed:
                            self.logger.debug(f"Valid tool call found: {parsed}")
                            return parsed
                        else:
                            self.logger.debug(f"JSON missing required keys: {list(parsed.keys())}")
                    except json.JSONDecodeError as e:
                        self.logger.debug(f"JSON decode error for '{match}': {e}")
                        continue
            
            # Approach 2: Try to find and parse any valid JSON in the response
            self.logger.debug("Trying to find any JSON objects in response")
            possible_jsons = self._extract_json_objects(response)
            
            for json_str in possible_jsons:
                try:
                    parsed = json.loads(json_str)
                    if isinstance(parsed, dict):
                        # Try to infer tool call from context
                        if 'password' in parsed and hasattr(self, 'tools') and 'password_analyzer' in self.tools:
                            self.logger.debug(f"Inferring password_analyzer tool call from: {parsed}")
                            return {
                                "tool": "password_analyzer", 
                                "parameters": parsed
                            }
                        elif 'tool' in parsed:
                            # Allow missing parameters key - create empty dict
                            if 'parameters' not in parsed:
                                parsed['parameters'] = {}
                            self.logger.debug(f"Valid tool call found (added empty parameters): {parsed}")
                            return parsed
                except json.JSONDecodeError:
                    continue
                    
        except Exception as e:
            self.logger.debug(f"Tool call parsing failed: {e}")
        
        self.logger.debug("No valid tool call found in response")
        return None
    
    def _extract_json_objects(self, text: str) -> List[str]:
        """Extract potential JSON objects from text"""
        import re
        json_objects = []
        
        # Find all potential JSON objects
        brace_level = 0
        start_idx = -1
        
        for i, char in enumerate(text):
            if char == '{':
                if brace_level == 0:
                    start_idx = i
                brace_level += 1
            elif char == '}':
                brace_level -= 1
                if brace_level == 0 and start_idx != -1:
                    json_objects.append(text[start_idx:i+1])
                    start_idx = -1
        
        return json_objects
    
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> ToolResult:
        """Execute a tool and return the result"""
        result = ToolResult(tool_name=tool_name, parameters=parameters)
        
        if tool_name not in self.tools:
            result.error_message = f"Tool '{tool_name}' not found"
            return result
        
        try:
            tool = self.tools[tool_name]
            result.result = tool.execute(**parameters)
            result.success = True
            self.logger.info(f"Tool '{tool_name}' executed successfully")
        except Exception as e:
            result.error_message = str(e)
            self.logger.error(f"Tool '{tool_name}' execution failed: {e}")
        
        return result

# -*- coding: utf-8 -*-
# agents/base_agent.py - Base class for AI agents

import logging
from typing import Dict, Any, Optional
from LLMs.factory import get_llm_client
from agents.base_tool import BaseTool
from agents.agent_memory import AgentMemory
from agents.tool_manager import ToolManager
from agents.rag_helper import RAGHelper

class BaseAgent:
    """
    Base class for AI agents that can use tools and reason about tasks.
    
    Key differences from RAG:
    - Agents can take actions via tools, not just answer questions
    - Agents have memory and can maintain conversation state
    - Agents can plan multistep tasks and decide which tools to use
    """
    
    def __init__(
        self,
        agent_name: str,
        llm_provider: str = "gigachat",
        vector_db_collection: Optional[str] = None,
        max_iterations: int = 10
    ):
        self.agent_name = agent_name
        self.logger = logging.getLogger(f"agent.{agent_name}")
        
        # Core components
        self.llm = get_llm_client(llm_provider)
        self.memory = AgentMemory()
        self.tool_manager = ToolManager()
        self.max_iterations = max_iterations
        
        # RAG helper (optional)
        self.rag_helper = RAGHelper(vector_db_collection) if vector_db_collection else None
        
        # Agent configuration
        self.system_prompt = self._get_default_system_prompt()
        
        self.logger.info(f"Agent '{agent_name}' initialized")
    
    def _get_default_system_prompt(self) -> str:
        """Default system prompt for the agent"""
        tools_desc = self.tool_manager.get_tools_description()
        
        return f"""You are {self.agent_name}, an AI assistant that can use tools to help users.

Available tools:
{tools_desc}

CRITICAL INSTRUCTIONS:
1. Analyze the user's request carefully
2. ONLY use tools when the user specifically asks for:
   - Password analysis (use password_analyzer)
   - Hash generation (use hash_generator) 
   - Code vulnerability checking (use vulnerability_checker)
   - Current web information (use web_search)
3. Do NOT use tools for general conversation, questions about yourself, or simple explanations
4. If you need to use a tool, respond with EXACTLY this JSON format:
   {{"tool": "tool_name", "parameters": {{"param1": "value1", "param2": "value2"}}}}
5. Do NOT use markdown code blocks when calling tools - just return the JSON
6. AFTER you receive tool results, provide a COMPLETE final answer in Russian
7. Do NOT call the same tool multiple times

For general questions, respond directly in Russian without using any tools.

Example tool call:
{{"tool": "password_analyzer", "parameters": {{"password": "mypassword123"}}}}"""
    
    def register_tool(self, tool: BaseTool):
        """Register a tool with the agent"""
        self.tool_manager.register_tool(tool)
        # Update system prompt with new tools
        self.system_prompt = self._get_default_system_prompt()

    def process_request(self, user_input: str) -> str:
        """
        Main method to process user requests.
        This is where the agent reasoning happens.
        """
        self.logger.info(f"Processing request: {user_input}")
        
        # Add user message to memory
        self.memory.add_message("user", user_input)
        
        # Search knowledge base for context if RAG helper is available
        context = None
        if self.rag_helper:
            context = self.rag_helper.search_knowledge_base(user_input)
        
        # Build enhanced prompt with context and memory
        enhanced_prompt = self._build_enhanced_prompt(user_input, context)
        
        # Track called tools to prevent loops
        called_tools = set()
        
        # Agent reasoning loop
        for iteration in range(self.max_iterations):
            self.logger.debug(f"Agent iteration {iteration + 1}")
            
            try:
                # Get LLM response
                response = self.llm.chat_one(enhanced_prompt, self.system_prompt)
                self.logger.debug(f"LLM response: {response}")
                
                # Check if LLM wants to use a tool
                tool_call = self.tool_manager.parse_tool_call(response)
                self.logger.debug(f"Parsed tool call: {tool_call}")
                
                if tool_call:
                    tool_name = tool_call['tool']
                    tool_key = f"{tool_name}_{str(tool_call.get('parameters', {}))}"
                    
                    # Check if this exact tool call was already made
                    if tool_key in called_tools:
                        self.logger.warning(f"Tool {tool_name} already called with same parameters, providing final response")
                        final_response = "Я уже проанализировал ваш запрос с помощью соответствующего инструмента. Результат уже получен."
                        self.memory.add_message("assistant", final_response)
                        return final_response
                    
                    called_tools.add(tool_key)
                    
                    # Execute tool
                    tool_result = self.tool_manager.execute_tool(
                        tool_name, 
                        tool_call.get('parameters', {})
                    )
                    
                    # Add tool result to context for next iteration
                    if tool_result.success:
                        enhanced_prompt += f"\n\nTool '{tool_result.tool_name}' result: {tool_result.result}"
                        self.logger.debug(f"Tool result added to context: {str(tool_result.result)[:200]}...")
                    else:
                        enhanced_prompt += f"\n\nTool '{tool_result.tool_name}' failed: {tool_result.error_message}"
                        self.logger.debug(f"Tool error added to context: {tool_result.error_message}")
                    
                    # Continue reasoning with tool results
                    continue
                else:
                    # No tool call - this is the final response
                    self.memory.add_message("assistant", response)
                    self.logger.info("Request processed successfully")
                    return response
                    
            except Exception as e:
                error_msg = f"Agent processing error: {e}"
                self.logger.error(error_msg)
                return f"I encountered an error while processing your request: {e}"
        
        # Max iterations reached
        fallback_msg = "I've reached my maximum thinking limit. Let me provide what I can help with so far."
        self.memory.add_message("assistant", fallback_msg)
        return fallback_msg
    
    def _build_enhanced_prompt(self, user_input: str, context: Optional[str] = None) -> str:
        """Build enhanced prompt with context and memory"""
        prompt_parts = []
        
        # Add conversation history
        history = self.memory.get_conversation_history()
        if history:
            prompt_parts.append(f"Conversation history:\n{history}")
        
        # Add knowledge base context
        if context:
            prompt_parts.append(f"Relevant knowledge:\n{context}")
        
        # Add current user input
        prompt_parts.append(f"Current request: {user_input}")
        
        return "\n\n".join(prompt_parts)
    
    def reset_memory(self):
        """Reset agent memory"""
        self.memory.clear()
        self.logger.info("Agent memory reset")
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status information"""
        return {
            "name": self.agent_name,
            "tools": list(self.tool_manager.tools.keys()),
            "memory_messages": len(self.memory.messages),
            "rag_enabled": self.rag_helper is not None
        }

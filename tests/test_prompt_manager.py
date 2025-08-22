# -*- coding: utf-8 -*-
"""
Test the new PromptManager integration with BaseAgent
"""

import sys
import os

# Add paths
sys.path.append(os.path.join(os.path.dirname(__file__), 'agents'))

from prompts.PromptManager import PromptManager
from agents.base_agent import BaseAgent
from agents.tools.security_tool import PasswordAnalyzerTool

def test_prompt_manager():
    """Test PromptManager functionality"""
    
    print("🧪 Testing PromptManager")
    print("=" * 40)
    
    # Test 1: Direct PromptManager usage
    print("\n1. Testing PromptManager directly:")
    
    pm = PromptManager()
    print(f"Available templates: {pm.list_templates()}")
    
    # Test loading template
    try:
        prompt = pm.get_system_prompt(
            "example",
            agent_name="TestAgent",
            tools_desc="- test_tool: A test tool"
        )
        print(f"✅ Template loaded successfully")
        print(f"Prompt length: {len(prompt)} chars")
        print(f"Preview: {prompt[:200]}...")
        
    except Exception as e:
        print(f"❌ Template loading failed: {e}")
        return
    
    # Test 2: BaseAgent with PromptManager
    print("\n2. Testing BaseAgent with PromptManager:")
    
    try:
        agent = BaseAgent(
            agent_name="TestSecurityBot",
            prompt_template="base_agent_instructions"
        )
        
        # Register a tool
        agent.register_tool(PasswordAnalyzerTool())
        
        print(f"✅ Agent created successfully")
        print(f"System prompt length: {len(agent.system_prompt)} chars")
        print(f"Agent status: {agent.get_status()}")
        
    except Exception as e:
        print(f"❌ Agent creation failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_prompt_manager()

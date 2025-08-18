"""
Simplified agent debugging script - step by step execution
"""

import logging
import sys
import os

# Add agents directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'agents'))

from agents.base_agent import BaseAgent
from agents.tools.security_tool import PasswordAnalyzerTool, HashGeneratorTool

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def debug_step_by_step():
    """Step-by-step agent debugging"""

    print("🔍 DEBUG MODE: Agent Step-by-Step Execution")
    print("=" * 50)

    try:
        # Create agent with debug logging
        print("\n1️⃣ Creating agent...")
        agent = BaseAgent(
            agent_name="DebugAgent",
            llm_provider="gigachat",
            max_iterations=3  # Reduced for debugging
        )

        # Register a simple tool
        print("\n2️⃣ Registering password analyzer tool...")
        password_tool = PasswordAnalyzerTool()
        agent.register_tool(password_tool)

        print(f"\n🤖 Agent Status: {agent.get_status()}")
        print(f"\n📋 System Prompt:\n{agent.system_prompt}")

        # Test with a very explicit query
        test_query = "Use the password_analyzer tool to analyze password 'test123'"
        print(f"\n3️⃣ Processing query: '{test_query}'")

        # Add debugging to see what LLM receives
        print(f"\n📤 LLM will receive:")
        print(f"User prompt: {test_query}")
        print(f"System prompt: {agent.system_prompt[:200]}...")

        # Process request with detailed tracing
        print(f"\n4️⃣ Starting agent.process_request()...")
        response = agent.process_request(test_query)

        print(f"\n✅ Final response: {response}")

    except Exception as e:
        print(f"\n❌ Error during debugging: {e}")
        import traceback
        traceback.print_exc()


def test_tool_directly():
    """Test tool execution directly"""
    print("\n🔧 DIRECT TOOL TEST")
    print("=" * 30)

    try:
        tool = PasswordAnalyzerTool()
        print(f"Tool name: {tool.name}")
        print(f"Tool description: {tool.description}")
        print(f"Tool parameters: {tool.parameters}")

        result = tool.execute(password="test123")
        print(f"Direct tool result: {result}")

    except Exception as e:
        print(f"❌ Direct tool test failed: {e}")
        import traceback
        traceback.print_exc()


def test_tool_manager():
    """Test tool manager parsing"""
    print("\n🛠️  TOOL MANAGER TEST")
    print("=" * 30)

    try:
        from agents.tool_manager import ToolManager

        manager = ToolManager()
        manager.register_tool(PasswordAnalyzerTool())

        # Test different response formats
        test_responses = [
            '{"tool": "password_analyzer", "parameters": {"password": "test123"}}',
            'I need to use {"tool": "password_analyzer", "parameters": {"password": "test123"}} to analyze this.',
            'Let me analyze this password: {"tool": "password_analyzer", "parameters": {"password": "test123"}}',
        ]

        for i, response in enumerate(test_responses, 1):
            print(f"\nTest {i}: {response}")
            parsed = manager.parse_tool_call(response)
            print(f"Parsed: {parsed}")

            if parsed:
                result = manager.execute_tool(parsed['tool'], parsed.get('parameters', {}))
                print(f"Execution result: success={result.success}")
                if result.success:
                    print(f"Result: {result.result}")
                else:
                    print(f"Error: {result.error_message}")

    except Exception as e:
        print(f"❌ Tool manager test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("Choose debugging method:")
    print("1. Direct tool test")
    print("2. Tool manager test")
    print("3. Full agent step-by-step")

    choice = input("Enter choice (1-3): ").strip()

    if choice == "1":
        test_tool_directly()
    elif choice == "2":
        test_tool_manager()
    elif choice == "3":
        debug_step_by_step()
    else:
        print("Testing all methods...")
        test_tool_directly()
        test_tool_manager()
        debug_step_by_step()

# -*- coding: utf-8 -*-
"""
Simple usage example for BaseAgent - Cybersecurity AI Assistant
"""

import logging
import sys
import os

# Add agents directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'agents'))

from agents.base_agent import BaseAgent
from agents.tools.search_tool import WebSearchTool
from agents.tools.security_tool import PasswordAnalyzerTool, HashGeneratorTool, VulnerabilityCheckerTool

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(name)s - %(message)s')

# Disable noisy loggers
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

def main():
    """Simple example showing how to use BaseAgent for cybersecurity tasks"""
    
    print("🔒 Cybersecurity AI Agent Example")
    print("=" * 40)
    
    try:
        # Create cybersecurity-focused agent
        agent = BaseAgent(
            agent_name="CyberSecurityAssistant",
            llm_provider="gigachat",
            max_iterations=5
        )
        
        # Register tools
        tools_registered = 0
        
        # Web search tool for current threat intelligence
        try:
            web_search = WebSearchTool()
            agent.register_tool(web_search)
            print("✅ Web search tool registered")
            tools_registered += 1
        except ValueError as e:
            print(f"⚠️  Web search disabled: {e}")
        
        # Security-specific tools
        security_tools = [
            PasswordAnalyzerTool(),
            HashGeneratorTool(), 
            VulnerabilityCheckerTool()
        ]
        
        for tool in security_tools:
            agent.register_tool(tool)
            tools_registered += 1
            
        print(f"✅ {tools_registered} security tools registered")
        
        # Example cybersecurity queries with tool usage
        example_queries = [
            "Analyze the password 'MyP@ssw0rd123' for security",
            "Generate a SHA-256 hash for 'sensitive_data'",
            "Check this code for vulnerabilities: cursor.execute('SELECT * FROM users WHERE id = ' + user_id)",
            "What are the latest ransomware threats this month?",
        ]
        
        print("\n📋 Example queries you can try:")
        for i, query in enumerate(example_queries, 1):
            print(f"  {i}. {query}")
        
        print(f"\n🤖 Agent Status: {agent.get_status()}")
        
        # Interactive mode
        print("\n💬 Interactive Mode (type 'quit' to exit):")
        while True:
            try:
                user_input = input("\n🔒 Security Question: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                    
                if not user_input:
                    continue
                
                print("\n🤔 Agent thinking...")
                response = agent.process_request(user_input)
                print(f"\n🤖 Response:\n{response}")
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        print("💡 Make sure your environment variables are set correctly!")


if __name__ == "__main__":
    main()

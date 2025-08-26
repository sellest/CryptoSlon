#!/usr/bin/env python3
"""
Test script for SAST Agent - demonstrates full pipeline capabilities
"""

import logging
import os
import sys
from pathlib import Path

# Add parent directories to path for robust imports
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(current_dir))

try:
    from sast_agent import create_sast_agent
except ImportError as e:
    print(f"❌ Failed to import sast_agent: {e}")
    print("Make sure you're running from the correct directory and all dependencies are installed")
    sys.exit(1)


def test_sast_agent_basic():
    """Test basic SAST agent functionality"""
    print("🧪 Testing SAST Agent Basic Functionality")
    print("=" * 50)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Create SAST agent
        print("1. Creating SAST agent...")
        agent = create_sast_agent(llm_provider="gpt-4o-mini")
        
        # Check agent status
        print("2. Checking agent status...")
        status = agent.get_pipeline_status()
        print(f"   Agent initialized: {status['agent_status']['name']}")
        print(f"   Tools available: {len(status['agent_status']['tools'])}")
        
        # Test tool descriptions
        print("3. Available SAST tools:")
        for tool_desc in status['available_tools']:
            print(f"   - {tool_desc}")
        
        print("\n✅ Basic functionality test passed!")
        return agent
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return None


def test_sast_pipeline_simulation():
    """Simulate SAST pipeline without actual code"""
    print("\n🔬 Testing SAST Pipeline Simulation")
    print("=" * 50)
    
    try:
        # Create agent
        agent = create_sast_agent()
        
        # Test agent conversation capabilities
        print("1. Testing agent reasoning with SAST questions...")
        
        test_questions = [
            "What are the 4 stages of your SAST pipeline?",
            "How do you prioritize vulnerabilities?",
            "What happens during the fix generation stage?",
            "What safety measures do you take when modifying code?"
        ]
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n   Question {i}: {question}")
            try:
                response = agent.process_request(question)
                print(f"   Agent Response: {response[:200]}...")
            except Exception as e:
                print(f"   Error: {e}")
        
        print("\n✅ Pipeline simulation test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Pipeline simulation test failed: {e}")
        return False


def test_tool_parameter_validation():
    """Test tool parameter validation"""
    print("\n🔍 Testing Tool Parameter Validation")
    print("=" * 50)
    
    try:
        agent = create_sast_agent()
        
        # Test each tool's parameter structure
        tools = ["sast_analysis", "sast_triage", "sast_fix_generation", "sast_code_injection"]
        
        for tool_name in tools:
            print(f"1. Testing {tool_name} tool parameters...")
            
            if tool_name in agent.tool_manager.tools:
                tool = agent.tool_manager.tools[tool_name]
                params = tool.parameters
                print(f"   Required parameters: {list(params.keys())}")
                
                # Check for required vs optional parameters
                required_params = []
                optional_params = []
                
                for param_name, param_info in params.items():
                    if isinstance(param_info, dict):
                        if param_info.get('required', True):  # Assume required by default
                            required_params.append(param_name)
                        else:
                            optional_params.append(param_name)
                    else:
                        required_params.append(param_name)
                
                print(f"   Likely required: {required_params}")
                print(f"   Likely optional: {optional_params}")
            else:
                print(f"   ❌ Tool {tool_name} not found")
        
        print("\n✅ Parameter validation test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Parameter validation test failed: {e}")
        return False


def interactive_demo():
    """Interactive demo of SAST agent"""
    print("\n🎮 Interactive SAST Agent Demo")
    print("=" * 50)
    
    try:
        agent = create_sast_agent()
        
        print("SAST Agent is ready! Try these example commands:")
        print("- 'Explain your SAST pipeline'")
        print("- 'What security vulnerabilities do you detect?'") 
        print("- 'How do you generate fixes for vulnerabilities?'")
        print("- 'What backup measures do you take?'")
        print("- 'quit' to exit")
        
        while True:
            try:
                user_input = input("\n🔐 SAST> ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                elif user_input.lower() == 'status':
                    status = agent.get_pipeline_status()
                    print(f"Pipeline Status: {status['pipeline_state']}")
                elif user_input.lower() == 'reset':
                    agent.reset_pipeline()
                    print("🔄 Pipeline reset completed")
                else:
                    # Let agent process the request
                    print("🤔 Agent thinking...")
                    response = agent.process_request(user_input)
                    print(f"🤖 Agent: {response}")
                    
            except KeyboardInterrupt:
                print("\n👋 Demo interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
        
    except Exception as e:
        print(f"❌ Interactive demo failed: {e}")


def main():
    """Run all tests and demo"""
    print("🚀 SAST Agent Test Suite")
    print("=" * 60)
    
    # Run tests
    agent = test_sast_agent_basic()
    if agent:
        test_sast_pipeline_simulation()
        test_tool_parameter_validation()
    
    # Ask if user wants interactive demo
    try:
        demo_choice = input("\n🎮 Run interactive demo? [y/N]: ").strip().lower()
        if demo_choice in ['y', 'yes']:
            interactive_demo()
        else:
            print("👋 Test suite completed!")
    except KeyboardInterrupt:
        print("\n👋 Test suite completed!")


if __name__ == "__main__":
    main()
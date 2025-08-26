# -*- coding: utf-8 -*-
"""
SAST Agent - Complete Static Application Security Testing Pipeline Agent

This agent combines 4 SAST tools to provide a complete vulnerability detection and fixing pipeline:
1. SAST Analysis - Run Semgrep + Bandit + Report merging + Aggregation  
2. SAST Triage - LLM-based vulnerability prioritization and analysis
3. Fix Generation - Extract code snippets + Generate LLM fixes
4. Code Injection - Apply fixes to source files with backup

Usage:
    agent = SASTAgent()
    result = agent.process_request("Analyze /path/to/code for vulnerabilities and generate fixes")
"""

import logging
import os
from typing import Dict, Any, Optional
from agents.base_agent import BaseAgent
from agents.tools.sast_tools import (
    SASTAnalysisTool,
    SASTTriageTool, 
    SASTFixGenerationTool,
    SASTCodeInjectionTool,
    SASTFullPipelineTool
)


class SASTAgent(BaseAgent):
    """
    Specialized agent for Static Application Security Testing (SAST) workflows.
    
    This agent orchestrates a complete SAST pipeline using 4 specialized tools:
    - Complete vulnerability analysis (Semgrep + Bandit)
    - LLM-based vulnerability triage and prioritization
    - Automated fix generation using LLM
    - Safe code injection with backup and verification
    
    The agent can handle complex multi-step SAST workflows and provides detailed
    reporting and progress tracking throughout the pipeline.
    """
    
    def __init__(
        self,
        llm_provider: str = "gpt-4o-mini",
        vector_db_collection: Optional[str] = None,
        max_iterations: int = 15,
        prompt_template: str = "sast_agent_instructions"
    ):
        """
        Initialize SAST Agent
        
        Args:
            llm_provider: LLM provider to use for analysis and reasoning
            vector_db_collection: Optional RAG collection for context
            max_iterations: Maximum reasoning iterations
            prompt_template: Agent prompt template name
        """
        super().__init__(
            agent_name="SAST_Security_Agent",
            llm_provider=llm_provider,
            vector_db_collection=vector_db_collection,
            max_iterations=max_iterations,
            prompt_template=prompt_template
        )
        
        # Register SAST tools
        self._register_sast_tools()
        
        # Agent state tracking
        self.current_analysis_session = None
        self.pipeline_state: Dict[str, Any] = {
            "analysis_completed": False,
            "triage_completed": False,
            "fixes_generated": False,
            "code_injected": False,
            "output_directory": None,
            "target_path": None
        }
        
        self.logger.info("SAST Agent initialized with 5 specialized tools")
    
    def _register_sast_tools(self):
        """Register all SAST pipeline tools"""
        tools = [
            SASTAnalysisTool(),
            SASTTriageTool(),
            SASTFixGenerationTool(),
            SASTCodeInjectionTool(),
            SASTFullPipelineTool()  # New complete pipeline tool
        ]
        
        for tool in tools:
            self.register_tool(tool)
            self.logger.debug(f"Registered SAST tool: {tool.name}")
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get current pipeline status"""
        return {
            "agent_status": self.get_status(),
            "pipeline_state": self.pipeline_state.copy(),
            "available_tools": [
                "sast_analysis - Complete SAST analysis (Semgrep + Bandit)",
                "sast_triage - LLM-based vulnerability prioritization",
                "sast_fix_generation - Extract code snippets and generate fixes",
                "sast_code_injection - Apply fixes to source files"
            ]
        }
    
    def reset_pipeline(self):
        """Reset pipeline state for new analysis"""
        self.pipeline_state = {
            "analysis_completed": False,
            "triage_completed": False,
            "fixes_generated": False,
            "code_injected": False,
            "output_directory": None,
            "target_path": None
        }
        self.reset_memory()
        self.logger.info("Pipeline state and memory reset")


# Convenience function for direct usage
def create_sast_agent(
    llm_provider: str = "gigachat-pro",
    vector_db_collection: Optional[str] = None
) -> SASTAgent:
    """
    Create a configured SAST agent
    
    Args:
        llm_provider: LLM provider for reasoning and fix generation
        vector_db_collection: Optional RAG collection for context
        
    Returns:
        Configured SASTAgent instance
    """
    return SASTAgent(
        llm_provider=llm_provider,
        vector_db_collection=vector_db_collection
    )


def main():
    """Example usage of SAST Agent"""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Create SAST agent
        agent = create_sast_agent(llm_provider="gpt-5-mini")
        
        # Example 1: Interactive agent usage
        print("🤖 SAST Security Agent ready!")
        print("Available commands:")
        print("- 'status' - Get pipeline status")
        print("- 'reset' - Reset pipeline state")
        print("- 'quit' - Exit")
        
        # Example automated pipeline (uncomment to test)
        # target_code = "/path/to/your/code"
        # results = agent.analyze_code(
        #     target_path=target_code,
        #     output_dir="./sast_results",
        #     full_pipeline=True,
        #     interactive_injection=False
        # )
        # print(f"Pipeline completed: {results['final_summary']}")
        
        # Interactive mode
        while True:
            try:
                user_input = input("\n> ").strip()
                
                if user_input.lower() == 'quit':
                    break
                elif user_input.lower() == 'status':
                    status = agent.get_pipeline_status()
                    print(f"Agent Status: {status}")
                elif user_input.lower() == 'reset':
                    agent.reset_pipeline()
                    print("Pipeline reset completed")
                else:
                    # Let the agent handle other requests
                    response = agent.process_request(user_input)
                    print(f"Agent: {response}")
                    
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"Error: {e}")
                
    except Exception as e:
        print(f"Failed to initialize SAST agent: {e}")
        logging.error(f"SAST agent initialization failed: {e}")


if __name__ == "__main__":
    main()

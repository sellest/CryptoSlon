#!/usr/bin/env python3
"""
SAST Triage - Analyzes aggregated SAST reports using LLM with prompt templates.
Processes SAST findings and provides vulnerability triage with human-readable analysis.
"""

import json
import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Setup logging
logger = logging.getLogger(__name__)

# Add parent directory to path to import LLMs and prompts
sys.path.append(str(Path(__file__).parent.parent))

from LLMs.factory import get_llm_client
from prompts.PromptManager import PromptManager
from progress_indicator import ProgressIndicator

class SASTTriageAnalyzer:
    def __init__(self, model: str = "gpt-4o-mini", template_name: str = "sast_v4"):
        """
        Initialize SAST Triage Analyzer
        
        Args:
            model: LLM model to use for analysis
            template_name: Prompt template name (without .json extension)
        """
        self.model = model
        self.template_name = template_name
        self.progress_indicator = ProgressIndicator()
        logger.debug(f"Initialized SASTTriageAnalyzer - model: {model}, template: {template_name}")
        
        # Initialize LLM client
        try:
            self.llm_client = get_llm_client(model)
            logger.info(f"Initialized LLM client: {model}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM client: {e}")
            raise
        
        # Initialize prompt manager
        try:
            self.prompt_manager = PromptManager()
            logger.info(f"Initialized prompt manager")
            logger.debug(f"Available templates: {self.prompt_manager.list_templates()}")
        except Exception as e:
            logger.error(f"Failed to initialize prompt manager: {e}")
            raise
    
    def load_sast_report(self, report_path: str) -> Dict[str, Any]:
        """Load SAST report from JSON file."""
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                report = json.load(f)
            logger.info(f"Loaded SAST report: {report_path}")
            return report
        except FileNotFoundError:
            logger.error(f"SAST report file not found: {report_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in SAST report: {e}")
            raise
    
    def prepare_messages(self, sast_report: Dict[str, Any]) -> List[Dict[str, str]]:
        """Prepare messages for LLM using prompt template."""
        try:
            # Load template data
            template_data = self.prompt_manager.load_template(self.template_name)
            
            # Prepare template variables
            template_vars = {
                "sast_report": json.dumps(sast_report, ensure_ascii=False, indent=2)
            }
            
            messages = []
            
            # Process each message in template
            for message in template_data.get("messages", []):
                role = message.get("role", "user")
                content = message.get("content", "")
                
                # Substitute variables in content using double curly braces {{variable}}
                for var_name, var_value in template_vars.items():
                    placeholder = f"{{{{{var_name}}}}}"
                    content = content.replace(placeholder, str(var_value))
                
                messages.append({
                    "role": role,
                    "content": content
                })
            
            logger.info(f"Prepared {len(messages)} messages for LLM")
            
            # Debug: Show message structure
            for i, msg in enumerate(messages):
                role = msg["role"]
                content_preview = msg["content"][:100].replace('\n', ' ')
                logger.debug(f"  Message {i+1}: {role} - {content_preview}...")
            
            return messages
            
        except Exception as e:
            logger.error(f"Failed to prepare messages: {e}")
            raise
    
    def analyze_sast_report(self, report_path: str, output_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Main method to analyze SAST report using LLM.
        
        Args:
            report_path: Path to aggregated SAST report JSON
            output_file: Optional output file path for analysis results
            
        Returns:
            Analysis results from LLM
        """
        logger.info(f"Starting SAST triage analysis...")
        logger.info(f"Report: {report_path}")
        logger.info(f"Model: {self.model}")
        logger.info(f"Template: {self.template_name}")
        
        # Load SAST report
        sast_report = self.load_sast_report(report_path)
        
        # Display report summary
        summary = sast_report.get("summary", {})
        logger.info(f"Report Summary:")
        logger.info(f"  Total findings: {summary.get('total_findings', 'N/A')}")
        logger.info(f"  Unique vulnerability types: {summary.get('total_unique_rules', 'N/A')}")
        logger.info(f"  Severity distribution: {summary.get('severity_distribution', 'N/A')}")
        
        # Prepare messages using prompt template
        messages = self.prepare_messages(sast_report)
        
        # Call LLM for analysis
        logger.info(f"Calling {self.model} for analysis...")
        
        # Start progress indicator
        self.progress_indicator.start(f"Waiting for {self.model} response")
        
        try:
            response = self.llm_client.chat_raw(messages)
            
            # Stop progress indicator
            self.progress_indicator.stop()
            logger.info(f"Received response from LLM")
            
            # Try to parse as JSON if possible
            json_content = response
            
            # Handle JSON wrapped in markdown code blocks
            if response.strip().startswith("```json") and response.strip().endswith("```"):
                json_content = response.strip()[7:-3].strip()
                logger.debug(f"Extracted JSON from markdown code blocks")
            elif response.strip().startswith("```") and response.strip().endswith("```"):
                json_content = response.strip()[3:-3].strip()
                logger.debug(f"Extracted content from code blocks")
            
            try:
                analysis_result = json.loads(json_content)
                logger.info(f"Successfully parsed JSON response")
            except json.JSONDecodeError:
                logger.warning(f"Response is not valid JSON, treating as text")
                analysis_result = {
                    "analysis_text": response,
                    "metadata": {
                        "model": self.model,
                        "template": self.template_name,
                        "source_report": report_path,
                        "is_json": False
                    }
                }
            
            # Add metadata if JSON was successfully parsed
            if "metadata" not in analysis_result:
                analysis_result["metadata"] = {
                    "model": self.model,
                    "template": self.template_name,
                    "source_report": report_path,
                    "is_json": True
                }
            
            # Save results if output file specified
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(analysis_result, f, indent=2, ensure_ascii=False)
                logger.info(f"Analysis saved to: {output_file}")
            
            return analysis_result
            
        except Exception as e:
            # Make sure to stop progress indicator on error
            self.progress_indicator.stop()
            logger.error(f"LLM analysis failed: {e}")
            logger.exception("Full traceback:")
            raise
    
    def display_analysis_summary(self, analysis: Dict[str, Any]):
        """Display a summary of the analysis results."""
        print(f"\n📋 Analysis Summary:")
        print("=" * 60)
        
        if analysis.get("metadata", {}).get("is_json", False):
            # If it's structured JSON, try to display key sections
            if "result" in analysis:
                results = analysis["result"]
                print(f"🎯 Top {len(results)} Critical Vulnerabilities:")
                for i, vuln in enumerate(results, 1):
                    print(f"  {i}. {vuln.get('Название', 'N/A')} - {vuln.get('Риск', 'N/A')}")
            
            if "verdict" in analysis:
                print(f"\n🔍 Verdict:")
                verdict = analysis["verdict"]
                if isinstance(verdict, str):
                    print(f"  {verdict}")
                elif isinstance(verdict, dict):
                    for key, value in verdict.items():
                        print(f"  {key}: {value}")
        else:
            # If it's text, display first part
            text = analysis.get("analysis_text", "")
            lines = text.split('\n')
            print(f"📝 Analysis (first 10 lines):")
            for line in lines[:10]:
                if line.strip():
                    print(f"  {line}")
            if len(lines) > 10:
                print(f"  ... ({len(lines) - 10} more lines)")


def run_sast_triage(**kwargs) -> Dict[str, Any]:
    """
    Agent-friendly helper function for SAST triage analysis.
    
    Args:
        input_file (str): Path to aggregated SAST report JSON file (required)
        output_file (str, optional): Output file path for analysis results
        model (str, optional): LLM model to use (default: 'gpt-4o-mini')
        template (str, optional): Prompt template name (default: 'sast')
        show_summary (bool, optional): Whether to display analysis summary (default: False)
        log_level (str, optional): Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR')
        
    Returns:
        Dict with standardized format:
        {
            "success": bool,
            "data": {
                "analysis_result": analysis dict or None,
                "is_json": bool,
                "total_findings": int,
                "unique_rules": int,
                "severity_distribution": dict,
                "output_file": str,
                "model_used": str,
                "template_used": str
            },
            "error": str or None,
            "metadata": {
                "input_file": str,
                "model": str,
                "template": str,
                "show_summary": bool
            }
        }
    """
    # Set logging level if provided
    if 'log_level' in kwargs:
        logger.setLevel(getattr(logging, kwargs['log_level'].upper(), logging.INFO))
    
    # Validate required parameters
    if 'input_file' not in kwargs:
        return {
            "success": False,
            "data": None,
            "error": "input_file is required",
            "metadata": {}
        }
    
    # Extract parameters with defaults
    input_file = kwargs['input_file']
    output_file = kwargs.get('output_file')
    model = kwargs.get('model', 'gigachat-max')
    template = kwargs.get('template', 'sast_v4')
    show_summary = kwargs.get('show_summary', False)

    try:
        # Initialize analyzer
        triage_analyzer = SASTTriageAnalyzer(model=model, template_name=template)
        
        # Load report to extract summary info
        sast_report = triage_analyzer.load_sast_report(input_file)
        summary = sast_report.get("summary", {})
        
        # Run analysis
        analysis_result = triage_analyzer.analyze_sast_report(input_file, output_file)
        
        # Display summary if requested
        if show_summary:
            triage_analyzer.display_analysis_summary(analysis_result)
        
        if analysis_result is None:
            return {
                "success": False,
                "data": None,
                "error": "Analysis failed or produced no results",
                "metadata": {
                    "input_file": str(input_file),
                    "model": str(model),
                    "template": str(template),
                    "show_summary": show_summary
                }
            }
        
        # Extract metadata
        metadata = analysis_result.get("metadata", {})
        
        return {
            "success": True,
            "data": {
                "analysis_result": analysis_result,
                "is_json": metadata.get("is_json", False),
                "total_findings": summary.get("total_findings", 0),
                "unique_rules": summary.get("total_unique_rules", 0),
                "severity_distribution": summary.get("severity_distribution", {}),
                "output_file": output_file if output_file else "not_saved",
                "model_used": model,
                "template_used": template
            },
            "error": None,
            "metadata": {
                "input_file": str(input_file),
                "model": str(model),
                "template": str(template),
                "show_summary": show_summary
            }
        }
        
    except Exception as e:
        logger.exception("Exception occurred during SAST triage analysis")
        return {
            "success": False,
            "data": None,
            "error": str(e),
            "metadata": {
                "input_file": str(input_file),
                "model": str(model),
                "template": str(template),
                "show_summary": show_summary
            }
        }


def analyze_sast_report(
    input_file: str,
    output_file: Optional[str] = None,
    model: str = "gpt-4o-mini",
    template: str = "sast",
    show_summary: bool = True
) -> Dict[str, Any]:
    """
    Analyze SAST report programmatically.
    
    Args:
        input_file: Path to aggregated SAST report JSON file
        output_file: Optional output file path for analysis results
        model: LLM model to use (default: gpt-4o-mini)
        template: Prompt template name (default: sast)
        show_summary: Whether to display analysis summary
        
    Returns:
        Analysis results dictionary
        
    Example:
        result = analyze_sast_report(
            input_file="aggregated_sast_report_semantic_v1.json",
            output_file="triage_analysis.json",
            model="gpt-4o",
            show_summary=True
        )
    """
    try:
        # Initialize analyzer
        triage_analyzer = SASTTriageAnalyzer(model=model, template_name=template)
        
        # Run analysis
        analysis_result = triage_analyzer.analyze_sast_report(input_file, output_file)
        
        # Display summary if requested
        if show_summary:
            triage_analyzer.display_analysis_summary(analysis_result)
        
        logger.info(f"SAST triage analysis completed successfully!")
        return analysis_result
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise


def main():
    """Example usage of the agent-friendly helper function."""
    # Example usage of the helper function
    dir_path = "/Users/izelikson/python/CryptoSlon/SAST/reports/"
    input_file = f"{dir_path}/aggregated_report.json"
    output_file = f"{dir_path}/triage_analysis.json"
    
    result = run_sast_triage(
        input_file=input_file,
        output_file=output_file,
        model="gigachat-max",
        template="sast_v4",
        show_summary=False,
        log_level="INFO"
    )
    
    if result["success"]:
        print(f"\n✅ SAST triage analysis successful!")
        data = result["data"]
        print(f"Model used: {data['model_used']}")
        print(f"Template used: {data['template_used']}")
        print(f"Total findings analyzed: {data['total_findings']}")
        print(f"Response format: {'JSON' if data['is_json'] else 'Text'}")
        print(f"Results saved to: {data['output_file']}")
    else:
        print(f"\n❌ SAST triage analysis failed: {result['error']}")
    
    return result


if __name__ == "__main__":
    main()

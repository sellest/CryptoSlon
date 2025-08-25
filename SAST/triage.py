#!/usr/bin/env python3
"""
SAST Triage - Analyzes aggregated SAST reports using LLM with prompt templates.
Processes SAST findings and provides vulnerability triage with human-readable analysis.
"""

import json
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add parent directory to path to import LLMs and prompts
sys.path.append(str(Path(__file__).parent.parent))

from LLMs.factory import get_llm_client
from prompts.PromptManager import PromptManager
from progress_indicator import ProgressIndicator

class SASTTriageAnalyzer:
    def __init__(self, model: str = "gpt-4o-mini", template_name: str = "sast"):
        """
        Initialize SAST Triage Analyzer
        
        Args:
            model: LLM model to use for analysis
            template_name: Prompt template name (without .json extension)
        """
        self.model = model
        self.template_name = template_name
        self.progress_indicator = ProgressIndicator()
        
        # Initialize LLM client
        try:
            self.llm_client = get_llm_client(model)
            print(f"✅ Initialized LLM client: {model}")
        except Exception as e:
            print(f"❌ Failed to initialize LLM client: {e}")
            raise
        
        # Initialize prompt manager
        try:
            self.prompt_manager = PromptManager()
            print(f"✅ Initialized prompt manager")
            print(f"Available templates: {self.prompt_manager.list_templates()}")
        except Exception as e:
            print(f"❌ Failed to initialize prompt manager: {e}")
            raise
    
    def load_sast_report(self, report_path: str) -> Dict[str, Any]:
        """Load SAST report from JSON file."""
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                report = json.load(f)
            print(f"✅ Loaded SAST report: {report_path}")
            return report
        except FileNotFoundError:
            print(f"❌ SAST report file not found: {report_path}")
            raise
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in SAST report: {e}")
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
            
            print(f"✅ Prepared {len(messages)} messages for LLM")
            
            # Debug: Show message structure
            for i, msg in enumerate(messages):
                role = msg["role"]
                content_preview = msg["content"][:100].replace('\n', ' ')
                print(f"  Message {i+1}: {role} - {content_preview}...")
            
            return messages
            
        except Exception as e:
            print(f"❌ Failed to prepare messages: {e}")
            raise
    
    def analyze_sast_report(self, report_path: str, output_file: str = None) -> Dict[str, Any]:
        """
        Main method to analyze SAST report using LLM.
        
        Args:
            report_path: Path to aggregated SAST report JSON
            output_file: Optional output file path for analysis results
            
        Returns:
            Analysis results from LLM
        """
        print(f"🔍 Starting SAST triage analysis...")
        print(f"Report: {report_path}")
        print(f"Model: {self.model}")
        print(f"Template: {self.template_name}")
        print("=" * 60)
        
        # Load SAST report
        sast_report = self.load_sast_report(report_path)
        
        # Display report summary
        summary = sast_report.get("summary", {})
        print(f"\n📊 Report Summary:")
        print(f"  Total findings: {summary.get('total_findings', 'N/A')}")
        print(f"  Unique vulnerability types: {summary.get('total_unique_rules', 'N/A')}")
        print(f"  Severity distribution: {summary.get('severity_distribution', 'N/A')}")
        
        # Prepare messages using prompt template
        messages = self.prepare_messages(sast_report)
        
        # Call LLM for analysis
        print(f"\n🤖 Calling {self.model} for analysis...")
        
        # Start progress indicator
        self.progress_indicator.start(f"Waiting for {self.model} response")
        
        try:
            response = self.llm_client.chat_raw(messages)
            
            # Stop progress indicator
            self.progress_indicator.stop()
            print(f"✅ Received response from LLM")
            
            # Try to parse as JSON if possible
            analysis_result = {}
            json_content = response
            
            # Handle JSON wrapped in markdown code blocks
            if response.strip().startswith("```json") and response.strip().endswith("```"):
                json_content = response.strip()[7:-3].strip()
                print(f"🔧 Extracted JSON from markdown code blocks")
            elif response.strip().startswith("```") and response.strip().endswith("```"):
                json_content = response.strip()[3:-3].strip()
                print(f"🔧 Extracted content from code blocks")
            
            try:
                analysis_result = json.loads(json_content)
                print(f"✅ Successfully parsed JSON response")
            except json.JSONDecodeError:
                print(f"⚠️  Response is not valid JSON, treating as text")
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
                print(f"💾 Analysis saved to: {output_file}")
            
            return analysis_result
            
        except Exception as e:
            # Make sure to stop progress indicator on error
            self.progress_indicator.stop()
            print(f"❌ LLM analysis failed: {e}")
            import traceback
            traceback.print_exc()
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


def analyze_sast_report(
    input_file: str,
    output_file: str = None,
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
        analyzer = SASTTriageAnalyzer(model=model, template_name=template)
        
        # Run analysis
        analysis_result = analyzer.analyze_sast_report(input_file, output_file)
        
        # Display summary if requested
        if show_summary:
            analyzer.display_analysis_summary(analysis_result)
        
        print(f"\n✅ SAST triage analysis completed successfully!")
        return analysis_result
        
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        raise


def main():
    """Command line interface (optional)."""
    parser = argparse.ArgumentParser(description="SAST Triage - Analyze aggregated SAST reports using LLM")
    parser.add_argument("--input", required=True, help="Path to aggregated SAST report JSON file")
    parser.add_argument("--output", help="Output file path for analysis results")
    parser.add_argument("--model", default="gpt-4o-mini", help="LLM model to use (default: gpt-4o-mini)")
    parser.add_argument("--template", default="sast", help="Prompt template name (default: sast)")
    parser.add_argument("--summary", action="store_true", help="Display analysis summary after completion")
    
    args = parser.parse_args()
    
    analyze_sast_report(
        input_file=args.input,
        output_file=args.output,
        model=args.model,
        template=args.template,
        show_summary=args.summary
    )


if __name__ == "__main__":
    # main()

    # Initialize analyzer with specific model
    analyzer = SASTTriageAnalyzer(
        model="gpt-5",
        template_name="sast_v2"
    )

    dir_path = "/Users/izelikson/python/CryptoSlon/SAST/reports/test_5/"
    # Run analysis
    result = analyzer.analyze_sast_report(
        report_path=f"{dir_path}aggregated_report.json",
        output_file=f"{dir_path}triage_analysis.json"
    )

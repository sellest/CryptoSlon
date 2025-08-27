#!/usr/bin/env python3
"""
Simple SAST analyzer using semgrep for Python vulnerability detection.
"""

import subprocess
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# Setup logging
logger = logging.getLogger(__name__)


class SemgrepAnalyzer:
    def __init__(self, target_path: str, rules_path: Optional[str] = None):
        self.target_path = Path(target_path)
        self.rules_path = Path(rules_path) if rules_path else Path(__file__).parent / "rules"
        logger.debug(f"Initialized SemgrepAnalyzer - target: {self.target_path}, rules: {self.rules_path}")
        
    def run_analysis(self, output_format: str = "json") -> Tuple[str, str, int]:
        """Run semgrep analysis on target directory."""
        format_flag = {
            "json": "--json",
            "sarif": "--sarif",
            "text": "--text"
        }.get(output_format, "--json")
        
        cmd = [
            "semgrep",
            "--config", str(self.rules_path),
            format_flag,
            "--no-git-ignore",  # Scan all files, not just git-tracked ones
            str(self.target_path)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            return result.stdout, result.stderr, result.returncode
        except FileNotFoundError:
            raise Exception("Semgrep not found. Install with: pip install semgrep")
    
    def analyze_and_save(self, output_file: str = "sast_results.json", output_format: str = "json") -> Optional[Any]:
        """Run analysis and save results to file."""
        stdout, stderr, returncode = self.run_analysis(output_format)
        
        if returncode != 0 and stderr:
            logger.error(f"Error running semgrep: {stderr}")
            return None
            
        # For text format, save as plain text
        if output_format == "text":
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(stdout)
            logger.info(f"Analysis complete. Results saved to: {output_file}")
            return stdout
            
        # For JSON and SARIF formats, parse and save
        try:
            results = json.loads(stdout) if stdout else {"results": []}
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            # Count issues based on format
            if output_format == "sarif":
                issue_count = sum(len(run.get("results", [])) for run in results.get("runs", []))
            else:
                issue_count = len(results.get("results", []))
                
            logger.info(f"Analysis complete. Found {issue_count} issues.")
            logger.info(f"Results saved to: {output_file}")
            return results
            
        except json.JSONDecodeError:
            logger.error("Failed to parse semgrep output")
            return None
    
    def analyze_sarif(self, output_file: str = "sast_results.sarif") -> Optional[Any]:
        """Run analysis and save results in SARIF format."""
        return self.analyze_and_save(output_file, "sarif")


def run_semgrep_analysis(**kwargs) -> Dict[str, Any]:
    """
    Agent-friendly helper function for running Semgrep analysis.
    
    Args:
        target_path (str): Path to the code to analyze (required)
        rules_path (str, optional): Path to Semgrep rules file
        output_file (str, optional): Output file path (default: 'sast_results.json')
        output_format (str, optional): Output format ('json', 'sarif', 'text')
        log_level (str, optional): Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR')
        
    Returns:
        Dict with standardized format:
        {
            "success": bool,
            "data": {
                "results": parsed results or None,
                "issue_count": int,
                "output_file": str,
                "output_format": str
            },
            "error": str or None,
            "metadata": {
                "target_path": str,
                "rules_path": str
            }
        }
    """
    # Set logging level if provided
    if 'log_level' in kwargs:
        logger.setLevel(getattr(logging, kwargs['log_level'].upper(), logging.INFO))
    
    # Validate required parameters
    if 'target_path' not in kwargs:
        return {
            "success": False,
            "data": None,
            "error": "target_path is required",
            "metadata": {}
        }
    
    # Extract parameters with defaults
    target_path = kwargs['target_path']
    rules_path = kwargs.get('rules_path')
    output_file = kwargs.get('output_file', 'sast_results.json')
    output_format = kwargs.get('output_format', 'json')
    
    try:
        # Initialize analyzer
        analyzer = SemgrepAnalyzer(target_path=target_path, rules_path=rules_path)
        
        # Run analysis
        results = analyzer.analyze_and_save(output_file=output_file, output_format=output_format)
        
        if results is None:
            return {
                "success": False,
                "data": None,
                "error": "Analysis failed or produced no results",
                "metadata": {
                    "target_path": str(target_path),
                    "rules_path": str(rules_path) if rules_path else "default"
                }
            }
        
        # Calculate issue count based on format
        issue_count = 0
        if output_format == "text":
            # For text format, we can't easily count issues
            issue_count = -1  # Indicates count not available
        elif output_format == "sarif" and isinstance(results, dict):
            issue_count = sum(len(run.get("results", [])) for run in results.get("runs", []))
        elif isinstance(results, dict):
            issue_count = len(results.get("results", []))
        
        return {
            "success": True,
            "data": {
                "results": results if output_format != "text" else None,
                "issue_count": issue_count,
                "output_file": output_file,
                "output_format": output_format
            },
            "error": None,
            "metadata": {
                "target_path": str(target_path),
                "rules_path": str(rules_path) if rules_path else "default"
            }
        }
        
    except Exception as e:
        logger.exception("Exception occurred during Semgrep analysis")
        return {
            "success": False,
            "data": None,
            "error": str(e),
            "metadata": {
                "target_path": str(target_path),
                "rules_path": str(rules_path) if rules_path else "default"
            }
        }


def main():
    """Example usage of the agent-friendly helper function."""
    # Example usage of the helper function
    target_path = "/Users/izelikson/python/CryptoSlon/SAST/code_for_sast/taskstate_19"
    rules_path = "/Users/izelikson/python/CryptoSlon/SAST/rules/python-security.yml"
    output_file = "/Users/izelikson/python/CryptoSlon/SAST/reports/semgrep_report.sarif"

    result = run_semgrep_analysis(
        target_path=target_path,
        rules_path=rules_path,
        output_file=output_file,
        output_format="sarif",
        log_level="INFO"
    )
    
    if result["success"]:
        print(f"\n✅ Semgrep analysis successful!")
        print(f"Found {result['data']['issue_count']} issues")
        print(f"Results saved to: {result['data']['output_file']}")
    else:
        print(f"\n❌ Analysis failed: {result['error']}")
    
    return result


if __name__ == "__main__":
    main()

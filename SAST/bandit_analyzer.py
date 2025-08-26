#!/usr/bin/env python3
"""
Simple SAST analyzer using bandit for Python security vulnerability detection.
"""

import os
import subprocess
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# Setup logging
logger = logging.getLogger(__name__)


class BanditAnalyzer:
    def __init__(self, target_path: str, config_path: Optional[str] = None):
        self.target_path = Path(target_path)
        self.config_path = Path(config_path) if config_path else None
        logger.debug(f"Initialized BanditAnalyzer - target: {self.target_path}, config: {self.config_path}")
        
    def run_analysis(self, output_format: str = "json") -> Tuple[str, str, int]:
        """Run bandit analysis on target directory."""
        # Supported formats: csv, custom, html, json, sarif, screen, txt, xml, yaml
        supported_formats = ["json", "sarif", "txt", "csv", "xml", "yaml", "html"]
        format_to_use = output_format if output_format in supported_formats else "json"
        
        cmd = [
            "bandit",
            "-r",  # recursive
            "-f", format_to_use,
            str(self.target_path)
        ]
        
        # Add config file if specified
        if self.config_path:
            cmd.extend(["-c", str(self.config_path)])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            return result.stdout, result.stderr, result.returncode
        except FileNotFoundError:
            raise Exception("Bandit not found. Install with: pip install bandit")
    
    def analyze_and_save(self, output_file: str = "bandit_results.json", output_format: str = "json") -> Optional[Any]:
        """Run analysis and save results to file."""
        stdout, stderr, returncode = self.run_analysis(output_format)
        
        # Bandit returns 1 when issues are found, which is normal
        if returncode > 1 and stderr:
            logger.error(f"Error running bandit: {stderr}")
            return None
            
        # For non-JSON formats, save as plain text
        if output_format in ["txt", "csv", "xml", "yaml", "html"]:
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
                # SARIF has different structure - count from runs[].results[]
                issue_count = sum(len(run.get("results", [])) for run in results.get("runs", []))
            else:
                # Standard bandit JSON format
                issue_count = len(results.get("results", []))
                
            logger.info(f"Analysis complete. Found {issue_count} issues.")
            logger.info(f"Results saved to: {output_file}")
            return results
            
        except json.JSONDecodeError:
            logger.error("Failed to parse bandit output")
            return None
    
    def analyze_sarif(self, output_file: str = "bandit_results.sarif") -> Optional[Any]:
        """Run analysis and save results in SARIF format."""
        return self.analyze_and_save(output_file, "sarif")


def run_bandit_analysis(**kwargs) -> Dict[str, Any]:
    """
    Agent-friendly helper function for running Bandit analysis.
    
    Args:
        target_path (str): Path to the code to analyze (required)
        config_path (str, optional): Path to Bandit config file
        output_file (str, optional): Output file path (default: 'bandit_results.json')
        output_format (str, optional): Output format ('json', 'sarif', 'txt', 'csv', 'xml', 'yaml', 'html')
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
                "config_path": str
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
    config_path = kwargs.get('config_path')
    output_file = kwargs.get('output_file', 'bandit_results.json')
    output_format = kwargs.get('output_format', 'json')
    
    try:
        # Initialize analyzer
        analyzer = BanditAnalyzer(target_path=target_path, config_path=config_path)
        
        # Run analysis
        results = analyzer.analyze_and_save(output_file=output_file, output_format=output_format)
        
        if results is None:
            return {
                "success": False,
                "data": None,
                "error": "Analysis failed or produced no results",
                "metadata": {
                    "target_path": str(target_path),
                    "config_path": str(config_path) if config_path else "default"
                }
            }
        
        # Calculate issue count based on format
        issue_count = 0
        if output_format in ["txt", "csv", "xml", "yaml", "html"]:
            # For text-based formats, we can't easily count issues
            issue_count = -1  # Indicates count not available
        elif output_format == "sarif" and isinstance(results, dict):
            issue_count = sum(len(run.get("results", [])) for run in results.get("runs", []))
        elif isinstance(results, dict):
            issue_count = len(results.get("results", []))
        
        return {
            "success": True,
            "data": {
                "results": results if output_format in ["json", "sarif"] else None,
                "issue_count": issue_count,
                "output_file": output_file,
                "output_format": output_format
            },
            "error": None,
            "metadata": {
                "target_path": str(target_path),
                "config_path": str(config_path) if config_path else "default"
            }
        }
        
    except Exception as e:
        logger.exception("Exception occurred during Bandit analysis")
        return {
            "success": False,
            "data": None,
            "error": str(e),
            "metadata": {
                "target_path": str(target_path),
                "config_path": str(config_path) if config_path else "default"
            }
        }


def main():
    """Example usage of the agent-friendly helper function."""
    # Example usage of the helper function
    target_path = "/Users/izelikson/python/CryptoSlon/SAST/code_for_sast/taskstate_5"
    output_file = "/Users/izelikson/python/CryptoSlon/SAST/reports/test_7/bandit_report.sarif"
    
    result = run_bandit_analysis(
        target_path=target_path,
        output_file=output_file,
        output_format="sarif",
        log_level="INFO"
    )
    
    if result["success"]:
        print(f"\n✅ Bandit analysis successful!")
        print(f"Found {result['data']['issue_count']} issues")
        print(f"Results saved to: {result['data']['output_file']}")
    else:
        print(f"\n❌ Analysis failed: {result['error']}")
    
    return result


if __name__ == "__main__":
    main()

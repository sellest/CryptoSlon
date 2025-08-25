#!/usr/bin/env python3
"""
Simple SAST analyzer using bandit for Python security vulnerability detection.
"""

import os
import subprocess
import json
import argparse
from pathlib import Path


class BanditAnalyzer:
    def __init__(self, target_path, config_path=None):
        self.target_path = Path(target_path)
        self.config_path = Path(config_path) if config_path else None
        
    def run_analysis(self, output_format="json"):
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
    
    def analyze_and_save(self, output_file="bandit_results.json", output_format="json"):
        """Run analysis and save results to file."""
        stdout, stderr, returncode = self.run_analysis(output_format)
        
        # Bandit returns 1 when issues are found, which is normal
        if returncode > 1 and stderr:
            print(f"Error running bandit: {stderr}")
            return None
            
        # For non-JSON formats, save as plain text
        if output_format in ["txt", "csv", "xml", "yaml", "html"]:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(stdout)
            print(f"Analysis complete. Results saved to: {output_file}")
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
                
            print(f"Analysis complete. Found {issue_count} issues.")
            print(f"Results saved to: {output_file}")
            return results
            
        except json.JSONDecodeError:
            print("Failed to parse bandit output")
            return None
    
    def analyze_sarif(self, output_file="bandit_results.sarif"):
        """Run analysis and save results in SARIF format."""
        return self.analyze_and_save(output_file, "sarif")


def main():
    dir_path = "/Users/izelikson/python/CryptoSlon/SAST/reports/test_5/"

    # Где лежит код
    target_path = "/Users/izelikson/python/CryptoSlon/SAST/code_for_sast/taskstate_3/"

    # Куда сложить результат
    output_path = f"{dir_path}/bandit_report.sarif"
    
    analyzer = BanditAnalyzer(target_path=target_path)
    # Test SARIF output
    analyzer.analyze_sarif(output_path)


if __name__ == "__main__":
    main()

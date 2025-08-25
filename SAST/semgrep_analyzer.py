#!/usr/bin/env python3
"""
Simple SAST analyzer using semgrep for Python vulnerability detection.
"""

import os
import subprocess
import json
import argparse
from pathlib import Path


class SemgrepAnalyzer:
    def __init__(self, target_path, rules_path=None):
        self.target_path = Path(target_path)
        self.rules_path = Path(rules_path) if rules_path else Path(__file__).parent / "rules"
        
    def run_analysis(self, output_format="json"):
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
            str(self.target_path)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            return result.stdout, result.stderr, result.returncode
        except FileNotFoundError:
            raise Exception("Semgrep not found. Install with: pip install semgrep")
    
    def analyze_and_save(self, output_file="sast_results.json", output_format="json"):
        """Run analysis and save results to file."""
        stdout, stderr, returncode = self.run_analysis(output_format)
        
        if returncode != 0 and stderr:
            print(f"Error running semgrep: {stderr}")
            return None
            
        # For text format, save as plain text
        if output_format == "text":
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
                issue_count = sum(len(run.get("results", [])) for run in results.get("runs", []))
            else:
                issue_count = len(results.get("results", []))
                
            print(f"Analysis complete. Found {issue_count} issues.")
            print(f"Results saved to: {output_file}")
            return results
            
        except json.JSONDecodeError:
            print("Failed to parse semgrep output")
            return None
    
    def analyze_sarif(self, output_file="sast_results.sarif"):
        """Run analysis and save results in SARIF format."""
        return self.analyze_and_save(output_file, "sarif")


def main():
    # Configure paths
    dir_path = "/Users/izelikson/python/CryptoSlon/SAST/reports/test_5"

    # Где лежит код
    target_path = "/Users/izelikson/python/CryptoSlon/SAST/code_for_sast/taskstate_3"
    # Правила
    rules_path = "/Users/izelikson/python/CryptoSlon/SAST/rules/python-security.yml"
    # Куда выгрузить
    output_path = f"{dir_path}/semgrep_report.sarif"
    
    analyzer = SemgrepAnalyzer(target_path=target_path, rules_path=rules_path)
    # Run analysis with custom output path
    analyzer.analyze_sarif(output_path)


if __name__ == "__main__":
    main()

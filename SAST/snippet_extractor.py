#!/usr/bin/env python3
"""
Snippet Extractor - Extracts code snippets from vulnerable locations
and creates detailed vulnerability objects with code context.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional


class SnippetExtractor:
    def __init__(self, triage_analysis_path: str, code_base_path: str = ""):
        """
        Initialize Snippet Extractor
        
        Args:
            triage_analysis_path: Path to triage analysis JSON
            code_base_path: Base path for code files (if paths in report are relative)
        """
        self.triage_analysis_path = triage_analysis_path
        self.code_base_path = code_base_path
        
        # Load triage analysis report
        self.triage_data = self._load_json(triage_analysis_path)
        self.vulnerabilities = self.triage_data.get("result", [])
    
    def _load_json(self, file_path: str) -> Dict[str, Any]:
        """Load JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"✅ Loaded: {file_path}")
            return data
        except FileNotFoundError:
            print(f"❌ File not found: {file_path}")
            raise
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in {file_path}: {e}")
            raise
    
    def _read_file_lines(self, file_path: str) -> List[str]:
        """Read a file and return lines."""
        full_path = file_path
        
        # If file_path starts with /, it's likely a prefix we need to remove
        if file_path.startswith("/"):
            # Find the first "/" after the initial one to get the relative path
            # Examples: 
            # "/taskstate/tsapp/routes.py" -> "tsapp/routes.py"
            # "/taskstate_copy/app.py" -> "app.py"
            # "/any_prefix/some/path/file.py" -> "some/path/file.py"
            
            # Remove leading slash
            path_without_leading_slash = file_path[1:]
            
            # Find the next slash (if any) to skip the prefix directory
            next_slash_idx = path_without_leading_slash.find("/")
            
            if next_slash_idx != -1:
                # Has subdirectories after prefix: extract everything after the prefix
                relative_path = path_without_leading_slash[next_slash_idx + 1:]
            else:
                # No subdirectories, the whole thing after "/" is the file
                # This handles cases like "/prefix/file.py" -> "file.py"
                relative_path = path_without_leading_slash
            
            # If we have a code_base_path, join with the relative path
            if self.code_base_path:
                full_path = str(Path(self.code_base_path) / relative_path)
            else:
                full_path = relative_path
        elif self.code_base_path and not file_path.startswith("/"):
            # Handle regular relative paths
            full_path = str(Path(self.code_base_path) / file_path)
        
        print(f"🔍 Looking for file: {file_path} -> {full_path}")
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            print(f"✅ Read {len(lines)} lines from: {full_path}")
            return lines
        except FileNotFoundError:
            print(f"❌ File not found: {full_path}")
            # Let's also check if the file exists without path transformations
            print(f"🔍 Also tried: {file_path}")
            return []
        except Exception as e:
            print(f"❌ Error reading file {full_path}: {e}")
            return []
    
    def _extract_snippet(self, 
                        file_path: str, 
                        start_line: int, 
                        end_line: int,
                        context_lines: int = 3) -> dict:
        """
        Extract code snippet with context.
        
        Args:
            file_path: Path to the source file
            start_line: Starting line number (1-indexed)
            end_line: Ending line number (1-indexed)
            context_lines: Number of additional lines to include before and after
            
        Returns:
            Dictionary with vulnerable_lines_only, before_context, after_context
        """
        lines = self._read_file_lines(file_path)
        
        if not lines:
            return {
                "vulnerable_lines_only": "// Unable to read source file",
                "before_context": "",
                "after_context": ""
            }
        
        # Adjust for 0-indexed array (file lines are 1-indexed)
        start_idx = start_line - 1
        end_idx = end_line
        
        # Extract vulnerable lines only
        vulnerable_lines = []
        for i in range(start_idx, min(end_idx, len(lines))):
            line_num = i + 1
            vulnerable_lines.append(f"{line_num:4d} >>> {lines[i].rstrip()}")
        
        # Extract context before
        before_start_idx = max(0, start_line - 1 - context_lines)
        before_lines = []
        for i in range(before_start_idx, start_idx):
            line_num = i + 1
            before_lines.append(f"{line_num:4d}     {lines[i].rstrip()}")
        
        # Extract context after
        after_end_idx = min(len(lines), end_line + context_lines)
        after_lines = []
        for i in range(end_idx, after_end_idx):
            line_num = i + 1
            after_lines.append(f"{line_num:4d}     {lines[i].rstrip()}")
        
        return {
            "vulnerable_lines_only": "\n".join(vulnerable_lines),
            "before_context": "\n".join(before_lines),
            "after_context": "\n".join(after_lines)
        }
    
    def _parse_location(self, location: str) -> tuple:
        """
        Parse location string like '/taskstate/tsapp/routes.py:416-429'
        
        Returns:
            Tuple of (file_path, start_line, end_line)
        """
        if ":" not in location:
            return location, 0, 0
        
        file_path, line_range = location.rsplit(":", 1)
        
        if "-" in line_range:
            start_line, end_line = line_range.split("-")
            try:
                start_line = int(start_line)
                end_line = int(end_line)
            except ValueError:
                start_line = end_line = 0
        else:
            try:
                start_line = end_line = int(line_range)
            except ValueError:
                start_line = end_line = 0
        
        return file_path, start_line, end_line

    def extract_vulnerability_snippets(self, context_lines: int = 3) -> List[Dict[str, Any]]:
        """
        Extract code snippets for all vulnerabilities from triage analysis.
        
        Args:
            context_lines: Number of context lines to include around vulnerable code
            
        Returns:
            List of vulnerability objects with code snippets
        """
        print(f"🔍 Extracting code snippets for {len(self.vulnerabilities)} vulnerabilities...")
        
        extracted_vulnerabilities = []
        
        for vuln in self.vulnerabilities:
            # Extract basic vulnerability info - now using English field names
            vulnerability_name = vuln.get("Name", "")
            
            # Handle CWE - can be object or string
            cwe_data = vuln.get("CWE", "")
            if isinstance(cwe_data, dict):
                cwe = f"{cwe_data.get('id', '')} {cwe_data.get('name', '')}"
            else:
                cwe = cwe_data
            
            risk = vuln.get("Risk", "")
            fix = vuln.get("Fix", "")
            
            # Extract severity from risk field or from Count
            severity = "UNKNOWN"
            count_data = vuln.get("Count", {})
            if count_data and "severity" in count_data:
                severity = count_data["severity"]
            elif risk.startswith("HIGH"):
                severity = "HIGH"
            elif risk.startswith("MEDIUM"):
                severity = "MEDIUM"
            elif risk.startswith("LOW"):
                severity = "LOW"
            
            # Process each representative evidence location
            evidence = vuln.get("RepresentativeEvidence", [])
            if not isinstance(evidence, list):
                print(f"⚠️  No valid evidence for vulnerability: {vulnerability_name}")
                continue
            
            for evidence_item in evidence:
                # New structure: direct file, start_line, end_line
                if "file" in evidence_item and "start_line" in evidence_item:
                    file_path = evidence_item.get("file", "")
                    start_line = evidence_item.get("start_line", 0)
                    end_line = evidence_item.get("end_line", start_line)
                # Old structure: location string
                elif "location" in evidence_item:
                    location = evidence_item.get("location", "")
                    if not location:
                        continue
                    file_path, start_line, end_line = self._parse_location(location)
                else:
                    continue
                
                if start_line == 0 and end_line == 0:
                    print(f"⚠️  No valid line numbers for {file_path}")
                    continue
                
                # Extract code snippet
                snippet_data = self._extract_snippet(
                    file_path, 
                    start_line, 
                    end_line,
                    context_lines
                )
                
                # Create vulnerability object with new format
                vuln_with_snippet = {
                    "vulnerability": vulnerability_name,
                    "file": file_path,
                    "location": {
                        "start_line": start_line,
                        "end_line": end_line,
                        "vulnerable_lines_only": snippet_data["vulnerable_lines_only"]
                    },
                    "context": {
                        "before": snippet_data["before_context"],
                        "after": snippet_data["after_context"]
                    },
                    "suggested_fix": fix,
                    "risk": risk,
                    "severity": severity,
                    "cwe": cwe,
                    "sources": [vuln.get("Source", "unknown")]
                }
                
                extracted_vulnerabilities.append(vuln_with_snippet)
        
        print(f"✅ Extracted snippets for {len(extracted_vulnerabilities)} vulnerabilities")
        return extracted_vulnerabilities
    
    def save_snippet_report(self, 
                           vulnerabilities: List[Dict[str, Any]], 
                           output_file: str):
        """Save vulnerability snippets to JSON file."""
        report = {
            "metadata": {
                "source_report": self.triage_analysis_path,
                "code_base_path": self.code_base_path,
                "generated_at": "2025-08-24T00:00:00Z",
                "total_snippets": len(vulnerabilities)
            },
            "vulnerabilities": vulnerabilities
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Snippet report saved to: {output_file}")
    
    def generate_markdown_report(self, 
                                vulnerabilities: List[Dict[str, Any]], 
                                output_file: str):
        """Generate a markdown report with code snippets."""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# Vulnerability Report with Code Snippets\n\n")
            f.write(f"Total vulnerabilities: {len(vulnerabilities)}\n\n")
            
            # Group by severity
            by_severity = {}
            for vuln in vulnerabilities:
                severity = vuln.get("severity", "UNKNOWN")
                if severity not in by_severity:
                    by_severity[severity] = []
                by_severity[severity].append(vuln)
            
            # Write vulnerabilities by severity
            for severity in ["HIGH", "MEDIUM", "LOW", "UNKNOWN"]:
                if severity not in by_severity:
                    continue
                    
                f.write(f"## {severity} Severity ({len(by_severity[severity])} issues)\n\n")
                
                for i, vuln in enumerate(by_severity[severity], 1):
                    f.write(f"### {i}. {vuln['vulnerability']}\n\n")
                    f.write(f"**File:** `{vuln['file']}`\n")
                    f.write(f"**Location:** Lines {vuln['location']}\n")
                    f.write(f"**CWE:** {vuln['cwe']}\n")
                    f.write(f"**Risk:** {vuln['risk']}\n\n")
                    
                    f.write("**Vulnerable Code:**\n```python\n")
                    f.write(vuln['location']['vulnerable_lines_only'])
                    f.write("\n```\n\n")
                    
                    if vuln['suggested_fix']:
                        f.write(f"**Suggested Fix:** {vuln['suggested_fix']}\n\n")
                    
                    f.write("---\n\n")
        
        print(f"📝 Markdown report saved to: {output_file}")


def extract_snippets(
    triage_analysis: str,
    output_file: str = "vulnerability_snippets.json",
    markdown_output: str = None,
    code_base_path: str = "",
    context_lines: int = 10,
    show_samples: bool = True
) -> List[Dict[str, Any]]:
    """
    Extract code snippets from triage analysis report.
    
    Args:
        triage_analysis: Path to triage analysis JSON
        output_file: Output JSON file for snippets
        markdown_output: Optional markdown report output
        code_base_path: Base path for code files
        context_lines: Number of context lines around vulnerable code
        show_samples: Whether to show sample extracted snippets
        
    Returns:
        List of vulnerability objects with code snippets
    """
    extractor = SnippetExtractor(triage_analysis, code_base_path)
    vulnerabilities = extractor.extract_vulnerability_snippets(context_lines)
    
    # Save JSON report
    extractor.save_snippet_report(vulnerabilities, output_file)
    
    # Generate markdown report if requested
    if markdown_output:
        extractor.generate_markdown_report(vulnerabilities, markdown_output)
    
    # Show samples if requested
    if show_samples and vulnerabilities:
        print(f"\n📋 Sample extracted vulnerabilities:")
        for vuln in vulnerabilities[:2]:  # Show first 2
            print(f"\n🔸 {vuln['vulnerability']}")
            print(f"  File: {vuln['file']} (lines {vuln['location']})")
            print(f"  Severity: {vuln['severity']}")
            print(f"  Fix: {vuln['suggested_fix'][:100]}...")
            print(f"  Code snippet preview:")
            snippet_lines = vuln['location']['vulnerable_lines_only'].split('\n')[:5]
            for line in snippet_lines:
                print(f"    {line}")
    
    return vulnerabilities


def main():
    """Example usage with Python parameters."""
    try:
        # Extract snippets from triage analysis report
        dir_path = "/Users/izelikson/python/CryptoSlon/SAST/reports/test_5"
        vulnerabilities = extract_snippets(
            triage_analysis=f"{dir_path}/triage_analysis.json",
            output_file=f"{dir_path}/vulnerability_snippets.json",
            # markdown_output="/Users/izelikson/python/CryptoSlon/SAST/reports/first_test/vulnerability_report_v2.md",
            code_base_path="/Users/izelikson/python/CryptoSlon/SAST/code_for_sast/taskstate_3",  # Base path for relative file paths
            context_lines=5,  # Show K lines before and after vulnerable code
            show_samples=True
        )
        
        print(f"\n✅ Snippet extraction completed successfully!")
        print(f"📝 Extracted {len(vulnerabilities)} vulnerability snippets")
        
        # Example: Programmatic access to results
        if vulnerabilities:
            # Count by severity
            severity_counts = {}
            for vuln in vulnerabilities:
                severity = vuln.get("severity", "UNKNOWN")
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            print(f"\n📊 Summary by severity:")
            for severity, count in severity_counts.items():
                print(f"  {severity}: {count}")
        
        return vulnerabilities
        
    except Exception as e:
        print(f"\n❌ Snippet extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return []


if __name__ == "__main__":
    # Direct Python usage
    result = main()

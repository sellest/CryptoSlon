#!/usr/bin/env python3
"""
SARIF Report Merger - Combines semgrep and bandit SARIF reports.
Categorizes findings as "both", "semgrep", or "bandit" based on location matching.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any

# Setup logging
logger = logging.getLogger(__name__)


class SARIFReportMerger:
    def __init__(self, semgrep_sarif_path: Optional[str] = None, bandit_sarif_path: Optional[str] = None, mappings_file: Optional[str] = None):
        # Check that at least one report path is provided
        if not semgrep_sarif_path and not bandit_sarif_path:
            raise ValueError("At least one report path (semgrep or bandit) must be provided")
        
        # Store paths and check file existence
        self.semgrep_path = Path(semgrep_sarif_path) if semgrep_sarif_path else None
        self.bandit_path = Path(bandit_sarif_path) if bandit_sarif_path else None
        
        self.semgrep_exists = self.semgrep_path and self.semgrep_path.exists()
        self.bandit_exists = self.bandit_path and self.bandit_path.exists()
        
        # Check that at least one file exists
        if not self.semgrep_exists and not self.bandit_exists:
            error_msg = []
            if self.semgrep_path:
                error_msg.append(f"Semgrep report not found: {self.semgrep_path}")
            if self.bandit_path:
                error_msg.append(f"Bandit report not found: {self.bandit_path}")
            raise FileNotFoundError("No report files found. " + " ".join(error_msg))
        
        # Log which files are available
        logger.info(f"Report files status:")
        if self.semgrep_exists:
            logger.info(f"  - Semgrep: {self.semgrep_path} (found)")
        elif self.semgrep_path:
            logger.warning(f"  - Semgrep: {self.semgrep_path} (not found, will skip)")
        else:
            logger.info(f"  - Semgrep: not specified")
            
        if self.bandit_exists:
            logger.info(f"  - Bandit: {self.bandit_path} (found)")
        elif self.bandit_path:
            logger.warning(f"  - Bandit: {self.bandit_path} (not found, will skip)")
        else:
            logger.info(f"  - Bandit: not specified")
        
        # Load rule mappings from external file
        if mappings_file is None:
            mappings_file = Path(__file__).parent / "rule_mappings.json"
        
        self.rule_to_cwe = self._load_rule_mappings(mappings_file)
    
    def _load_rule_mappings(self, mappings_file: Path) -> Dict[str, str]:
        """Load rule to CWE mappings from external JSON file."""
        try:
            with open(mappings_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Combine semgrep and bandit rules into one mapping
            mappings = {}
            mappings.update(data.get("rule_to_cwe", {}).get("semgrep_rules", {}))
            mappings.update(data.get("rule_to_cwe", {}).get("bandit_rules", {}))
            
            # Store CWE severity mappings and descriptions
            self.cwe_severity_mappings = data.get("cwe_severity_mapping", {})
            self.cwe_descriptions = data.get("cwe_descriptions", {})
            
            logger.info(f"Loaded {len(mappings)} rule mappings from {mappings_file}")
            return mappings
            
        except FileNotFoundError:
            logger.warning(f"Mappings file {mappings_file} not found. Using empty mappings.")
            self.cwe_severity_mappings = {}
            self.cwe_descriptions = {}
            return {}
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON in {mappings_file}: {e}. Using empty mappings.")
            self.cwe_severity_mappings = {}
            self.cwe_descriptions = {}
            return {}
        
    def load_sarif(self, sarif_path: Path) -> Optional[Dict]:
        """Load and parse SARIF file, returns None if file doesn't exist."""
        if not sarif_path or not sarif_path.exists():
            return None
        
        try:
            with open(sarif_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load SARIF file {sarif_path}: {e}")
            return None
    
    def extract_findings(self, sarif_data: Dict, tool_name: str) -> List[Dict]:
        """Extract findings from SARIF data with normalized structure."""
        findings = []
        
        for run in sarif_data.get("runs", []):
            for result in run.get("results", []):
                # Extract location info
                locations = result.get("locations", [])
                if not locations:
                    continue
                    
                location = locations[0].get("physicalLocation", {})
                artifact = location.get("artifactLocation", {})
                region = location.get("region", {})
                
                file_path = self._normalize_file_path(artifact.get("uri", ""))
                start_line = region.get("startLine", 0)
                end_line = region.get("endLine", start_line)
                
                # Extract code snippet
                snippet = self._extract_snippet(location)
                
                # Create normalized finding
                original_rule_id = result.get("ruleId", "unknown")
                cwe_id = self._convert_to_cwe(original_rule_id)
                finding = {
                    "tool": tool_name,
                    "rule_id": cwe_id,
                    "rule_description": self.cwe_descriptions.get(cwe_id, ""),
                    "original_rule_id": original_rule_id,
                    "message": result.get("message", {}).get("text", ""),
                    "file_path": file_path,
                    "start_line": start_line,
                    "end_line": end_line,
                    "severity": self._get_severity_for_cwe(cwe_id, result),
                    "snippet": snippet,
                    "location_key": f"{file_path}:{start_line}-{end_line}",
                    "original_result": result
                }
                
                findings.append(finding)
        
        return findings
    
    def _extract_severity(self, result: Dict) -> str:
        """Extract severity from SARIF result."""
        # Check for level in result
        level = result.get("level", "")
        if level:
            return self._normalize_severity(level)
            
        # Check for severity in properties
        properties = result.get("properties", {})
        if "severity" in properties:
            return self._normalize_severity(properties["severity"])
            
        return "LOW"
    
    def _normalize_severity(self, severity: str) -> str:
        """Normalize severity levels to LOW/MEDIUM/HIGH."""
        severity_lower = severity.lower()
        
        if severity_lower in ["error", "high"]:
            return "HIGH"
        elif severity_lower in ["warning", "medium"]:
            return "MEDIUM"
        elif severity_lower in ["note", "info", "low"]:
            return "LOW"
        else:
            return "LOW"  # default fallback
    
    def _normalize_file_path(self, file_path: str) -> str:
        """Normalize file path by removing file:// URI prefix and making it relative."""
        # # Remove file:// URI prefix first
        # if file_path.startswith("file://"):
        #     file_path = file_path[7:]  # Remove "file://"
        # elif file_path.startswith("file:/"):
        #     file_path = file_path[6:]  # Remove "file:/"
        
        # Make path relative by finding the SAST/taskstate part
        if "/taskstate" in file_path:
            # Extract everything from /taskstate onwards
            sast_index = file_path.find("/taskstate")
            return file_path[sast_index:]  # +5 to skip "/SAST" part, keeping "/taskstate"
        
        return file_path
    
    def _convert_to_cwe(self, rule_id: str) -> str:
        """Convert tool-specific rule ID to CWE format."""
        return self.rule_to_cwe.get(rule_id, rule_id)
    
    def _get_severity_for_cwe(self, cwe_id: str, sarif_result: Dict) -> str:
        """Get severity based on CWE mapping first, then fall back to SARIF severity."""
        # First, try to get severity from CWE mapping
        for severity_level, cwe_list in self.cwe_severity_mappings.items():
            if cwe_id in cwe_list:
                return severity_level
        
        # Fall back to SARIF-based severity extraction
        return self._extract_severity(sarif_result)
    
    def _extract_snippet(self, location: Dict) -> str:
        """Extract code snippet from SARIF location."""
        # Try to get snippet from region
        region = location.get("region", {})
        snippet = region.get("snippet", {})
        if snippet and "text" in snippet:
            return snippet["text"]
        
        # Try to get snippet from contextRegion
        context_region = location.get("contextRegion", {})
        if context_region:
            context_snippet = context_region.get("snippet", {})
            if context_snippet and "text" in context_snippet:
                return context_snippet["text"]
        
        return ""
    
    def match_findings(self, semgrep_findings: Optional[List[Dict]], bandit_findings: Optional[List[Dict]]) -> Dict:
        """Match findings by location and categorize them."""
        
        # Handle cases where one tool has no findings
        semgrep_findings = semgrep_findings or []
        bandit_findings = bandit_findings or []
        
        # Create location maps for efficient matching
        semgrep_locations = {f["location_key"]: f for f in semgrep_findings}
        bandit_locations = {f["location_key"]: f for f in bandit_findings}
        
        # Find matches
        both_locations = set(semgrep_locations.keys()) & set(bandit_locations.keys())
        semgrep_only = set(semgrep_locations.keys()) - set(bandit_locations.keys())
        bandit_only = set(bandit_locations.keys()) - set(semgrep_locations.keys())
        
        categorized = {
            "both": [],
            "semgrep": [],
            "bandit": []
        }
        
        # Add matched findings (both tools found issues at same location)
        for location_key in both_locations:
            semgrep_finding = semgrep_locations[location_key]
            bandit_finding = bandit_locations[location_key]
            
            merged_finding = {
                "category": "both",
                "location_key": location_key,
                "file_path": semgrep_finding["file_path"],
                "start_line": semgrep_finding["start_line"],
                "end_line": semgrep_finding["end_line"],
                "snippet": semgrep_finding["snippet"] or bandit_finding["snippet"],
                "semgrep": {
                    "rule_id": semgrep_finding["rule_id"],
                    "rule_description": semgrep_finding["rule_description"],
                    "message": semgrep_finding["message"],
                    "severity": semgrep_finding["severity"],
                    "snippet": semgrep_finding["snippet"]
                },
                "bandit": {
                    "rule_id": bandit_finding["rule_id"],
                    "rule_description": bandit_finding["rule_description"],
                    "message": bandit_finding["message"],
                    "severity": bandit_finding["severity"],
                    "snippet": bandit_finding["snippet"]
                }
            }
            categorized["both"].append(merged_finding)
        
        # Add semgrep-only findings
        for location_key in semgrep_only:
            finding = semgrep_locations[location_key]
            categorized["semgrep"].append({
                "category": "semgrep",
                "location_key": location_key,
                "file_path": finding["file_path"],
                "start_line": finding["start_line"],
                "end_line": finding["end_line"],
                "rule_id": finding["rule_id"],
                "rule_description": finding["rule_description"],
                "message": finding["message"],
                "severity": finding["severity"],
                "snippet": finding["snippet"]
            })
        
        # Add bandit-only findings
        for location_key in bandit_only:
            finding = bandit_locations[location_key]
            categorized["bandit"].append({
                "category": "bandit",
                "location_key": location_key,
                "file_path": finding["file_path"],
                "start_line": finding["start_line"],
                "end_line": finding["end_line"],
                "rule_id": finding["rule_id"],
                "rule_description": finding["rule_description"],
                "message": finding["message"],
                "severity": finding["severity"],
                "snippet": finding["snippet"]
            })
        
        return categorized
    
    def generate_summary(self, categorized: Dict) -> Dict:
        """Generate summary statistics."""
        return {
            "total_findings": sum(len(findings) for findings in categorized.values()),
            "both_tools": len(categorized["both"]),
            "semgrep_only": len(categorized["semgrep"]),
            "bandit_only": len(categorized["bandit"]),
            "coverage": {
                "both_percentage": len(categorized["both"]) / max(1, sum(len(findings) for findings in categorized.values())) * 100,
                "agreement_rate": len(categorized["both"]) / max(1, len(categorized["both"]) + len(categorized["semgrep"]) + len(categorized["bandit"])) * 100
            }
        }
    
    def merge_reports(self, output_file: str = "merged_sast_report.json") -> Dict:
        """Main method to merge SARIF reports."""
        
        # Load SARIF files (only if they exist)
        semgrep_data = None
        bandit_data = None
        
        if self.semgrep_exists:
            logger.info(f"Loading semgrep report: {self.semgrep_path}")
            semgrep_data = self.load_sarif(self.semgrep_path)
            if not semgrep_data:
                logger.warning("Failed to load semgrep data, continuing without it")
        else:
            logger.info("Semgrep report not available, skipping")
        
        if self.bandit_exists:
            logger.info(f"Loading bandit report: {self.bandit_path}")
            bandit_data = self.load_sarif(self.bandit_path)
            if not bandit_data:
                logger.warning("Failed to load bandit data, continuing without it")
        else:
            logger.info("Bandit report not available, skipping")
        
        # Extract findings
        logger.info("Extracting findings...")
        semgrep_findings = self.extract_findings(semgrep_data, "semgrep") if semgrep_data else []
        bandit_findings = self.extract_findings(bandit_data, "bandit") if bandit_data else []
        
        logger.info(f"Found {len(semgrep_findings)} semgrep findings")
        logger.info(f"Found {len(bandit_findings)} bandit findings")
        
        # Match and categorize findings
        logger.info("Matching findings by location...")
        categorized = self.match_findings(semgrep_findings, bandit_findings)
        
        # Generate summary
        summary = self.generate_summary(categorized)
        
        # Create final report
        metadata = {
            "generated_at": "2025-08-24T00:00:00Z"  # You could use datetime.now().isoformat()
        }
        
        # Only add file paths for files that were actually processed
        if self.semgrep_exists:
            metadata["semgrep_file"] = str(self.semgrep_path)
        if self.bandit_exists:
            metadata["bandit_file"] = str(self.bandit_path)
        
        # Note which files were missing
        if self.semgrep_path and not self.semgrep_exists:
            metadata["semgrep_missing"] = str(self.semgrep_path)
        if self.bandit_path and not self.bandit_exists:
            metadata["bandit_missing"] = str(self.bandit_path)
            
        merged_report = {
            "metadata": metadata,
            "summary": summary,
            "findings": categorized
        }
        
        # Save report
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(merged_report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Merged report saved to: {output_file}")
        logger.info(f"Summary:")
        logger.info(f"  Total findings: {summary['total_findings']}")
        logger.info(f"  Found by both tools: {summary['both_tools']}")
        logger.info(f"  Semgrep only: {summary['semgrep_only']}")
        logger.info(f"  Bandit only: {summary['bandit_only']}")
        logger.info(f"  Agreement rate: {summary['coverage']['agreement_rate']:.1f}%")
        
        return merged_report


def run_report_merger(**kwargs) -> Dict[str, Any]:
    """
    Agent-friendly helper function for merging SARIF reports.
    
    Args:
        semgrep_file (str, optional): Path to semgrep SARIF file
        bandit_file (str, optional): Path to bandit SARIF file  
        output_file (str, optional): Output file path (default: 'merged_sast_report.json')
        mappings_file (str, optional): Path to rule mappings JSON file
        log_level (str, optional): Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR')
        
    Note: At least one of semgrep_file or bandit_file must be provided.
        
    Returns:
        Dict with standardized format:
        {
            "success": bool,
            "data": {
                "merged_report": report dict or None,
                "total_findings": int,
                "semgrep_findings": int,
                "bandit_findings": int,
                "both_tools": int,
                "agreement_rate": float,
                "output_file": str
            },
            "error": str or None,
            "metadata": {
                "semgrep_file": str or None,
                "bandit_file": str or None,
                "mappings_file": str
            }
        }
    """
    # Set logging level if provided
    if 'log_level' in kwargs:
        logger.setLevel(getattr(logging, kwargs['log_level'].upper(), logging.INFO))
    
    # Check that at least one report file is provided
    if 'semgrep_file' not in kwargs and 'bandit_file' not in kwargs:
        return {
            "success": False,
            "data": None,
            "error": "At least one report file (semgrep_file or bandit_file) must be provided",
            "metadata": {}
        }
    
    # Extract parameters with defaults
    semgrep_file = kwargs.get('semgrep_file')
    bandit_file = kwargs.get('bandit_file')
    output_file = kwargs.get('output_file', 'merged_sast_report.json')
    mappings_file = kwargs.get('mappings_file')
    
    try:
        # Initialize merger
        merger = SARIFReportMerger(semgrep_file, bandit_file, mappings_file)
        
        # Run merge
        merged_report = merger.merge_reports(output_file)
        
        if merged_report is None:
            return {
                "success": False,
                "data": None,
                "error": "Report merging failed or produced no results",
                "metadata": {
                    "semgrep_file": str(semgrep_file) if semgrep_file else None,
                    "bandit_file": str(bandit_file) if bandit_file else None,
                    "mappings_file": str(mappings_file) if mappings_file else "default"
                }
            }
        
        # Extract summary data
        summary = merged_report.get("summary", {})
        findings = merged_report.get("findings", {})
        
        return {
            "success": True,
            "data": {
                "merged_report": merged_report,
                "total_findings": summary.get("total_findings", 0),
                "semgrep_findings": len(findings.get("semgrep", [])),
                "bandit_findings": len(findings.get("bandit", [])),
                "both_tools": summary.get("both_tools", 0),
                "agreement_rate": summary.get("coverage", {}).get("agreement_rate", 0.0),
                "output_file": output_file
            },
            "error": None,
            "metadata": {
                "semgrep_file": str(semgrep_file) if semgrep_file else None,
                "bandit_file": str(bandit_file) if bandit_file else None,
                "mappings_file": str(mappings_file) if mappings_file else "default"
            }
        }
        
    except Exception as e:
        logger.exception("Exception occurred during report merging")
        return {
            "success": False,
            "data": None,
            "error": str(e),
            "metadata": {
                "semgrep_file": str(semgrep_file) if semgrep_file else None,
                "bandit_file": str(bandit_file) if bandit_file else None,
                "mappings_file": str(mappings_file) if mappings_file else "default"
            }
        }


def merge_sast_reports(
    semgrep_file: Optional[str] = "sast_results_v3.sarif",
    bandit_file: Optional[str] = "bandit_results_v3.sarif",
    output_file: str = "merged_report_v11.json",
    mappings_file: Optional[str] = None
) -> Dict:
    """
    Merge semgrep and bandit SARIF reports.
    
    Args:
        semgrep_file: Path to semgrep SARIF file (optional)
        bandit_file: Path to bandit SARIF file (optional)
        output_file: Output file path for merged report
        mappings_file: Path to rule mappings JSON (optional)
        
    Note: At least one of semgrep_file or bandit_file must be provided.
        
    Returns:
        Merged report dictionary
    """
    merger = SARIFReportMerger(semgrep_file, bandit_file, mappings_file)
    return merger.merge_reports(output_file)


def main():
    """Example usage of the agent-friendly helper function."""
    # Example usage of the helper function
    dir_path = "/Users/izelikson/python/CryptoSlon/SAST/reports/"
    semgrep_file = f"{dir_path}/semgrep_report.sarif"
    bandit_file = f"{dir_path}/bandit_report.sarif"
    output_file = f"{dir_path}/merged_report.json"
    
    result = run_report_merger(
        semgrep_file=semgrep_file,
        bandit_file=bandit_file,
        output_file=output_file,
        log_level="INFO"
    )
    
    if result["success"]:
        print(f"\n✅ Report merging successful!")
        data = result["data"]
        print(f"Total findings: {data['total_findings']}")
        print(f"Agreement rate: {data['agreement_rate']:.1f}%")
        print(f"Results saved to: {data['output_file']}")
    else:
        print(f"\n❌ Report merging failed: {result['error']}")
    
    return result


if __name__ == "__main__":
    main()

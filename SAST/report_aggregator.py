#!/usr/bin/env python3
"""
Report Aggregator - Groups merged SAST report findings by rule_id.
Creates aggregated view of vulnerabilities for better analysis.
"""

import json
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict


class ReportAggregator:
    def __init__(self, merged_report_path: str, mappings_file: str = None):
        self.report_path = Path(merged_report_path)
        
        # Load rule mappings from external file
        if mappings_file is None:
            mappings_file = Path(__file__).parent / "rule_mappings.json"
        
        self.semantic_groupings = self._load_semantic_groupings(mappings_file)
    
    def _load_semantic_groupings(self, mappings_file: Path) -> Dict:
        """Load semantic groupings from external JSON file."""
        try:
            with open(mappings_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            groupings = data.get("semantic_groupings", {})
            print(f"Loaded {len(groupings)} semantic groupings from {mappings_file}")
            return groupings
            
        except FileNotFoundError:
            print(f"Warning: Mappings file {mappings_file} not found. Using empty groupings.")
            return {}
        except json.JSONDecodeError as e:
            print(f"Warning: Invalid JSON in {mappings_file}: {e}. Using empty groupings.")
            return {}
        
    def load_merged_report(self) -> Dict:
        """Load the merged SAST report."""
        with open(self.report_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def aggregate_by_rule_id(self, merged_report: Dict) -> Dict:
        """Aggregate findings by rule_id."""
        aggregated = defaultdict(lambda: {
            "rule_id": "",
            "rule_description": "",
            "message": "",
            "severity": "",
            "sources": set(),
            "count": 0,
            "files": set(),
            "evidence_locations": set()
        })
        
        # Track unique (rule_id, location_key) combinations to avoid double counting
        processed_combinations = set()
        
        findings = merged_report.get("findings", {})
        
        # Process all finding categories
        for category in ["both", "semgrep", "bandit"]:
            category_findings = findings.get(category, [])
            
            for finding in category_findings:
                if category == "both":
                    # For "both" category, we have nested semgrep and bandit data
                    location_key = finding.get("location_key", "")
                    file_path = finding.get("file_path", "")
                    
                    for tool in ["semgrep", "bandit"]:
                        tool_data = finding.get(tool, {})
                        rule_id = tool_data.get("rule_id", "unknown")
                        
                        # Create unique combination key
                        combination_key = (rule_id, location_key)
                        
                        # Initialize rule if not seen before
                        if rule_id not in aggregated:
                            aggregated[rule_id]["rule_id"] = rule_id
                            aggregated[rule_id]["rule_description"] = tool_data.get("rule_description", "")
                            aggregated[rule_id]["message"] = tool_data.get("message", "")
                            aggregated[rule_id]["severity"] = tool_data.get("severity", "LOW")
                        
                        aggregated[rule_id]["sources"].add(tool)
                        
                        # Only count each unique (rule_id, location) combination once
                        if combination_key not in processed_combinations:
                            aggregated[rule_id]["count"] += 1
                            aggregated[rule_id]["files"].add(file_path)
                            aggregated[rule_id]["evidence_locations"].add(location_key)
                            processed_combinations.add(combination_key)
                else:
                    # For "semgrep" or "bandit" only categories
                    rule_id = finding.get("rule_id", "unknown")
                    location_key = finding.get("location_key", "")
                    file_path = finding.get("file_path", "")
                    
                    # Create unique combination key
                    combination_key = (rule_id, location_key)
                    
                    # Initialize rule if not seen before
                    if rule_id not in aggregated:
                        aggregated[rule_id]["rule_id"] = rule_id
                        aggregated[rule_id]["rule_description"] = finding.get("rule_description", "")
                        aggregated[rule_id]["message"] = finding.get("message", "")
                        aggregated[rule_id]["severity"] = finding.get("severity", "LOW")
                    
                    aggregated[rule_id]["sources"].add(category)
                    
                    # Only count each unique (rule_id, location) combination once
                    if combination_key not in processed_combinations:
                        aggregated[rule_id]["count"] += 1
                        aggregated[rule_id]["files"].add(file_path)
                        aggregated[rule_id]["evidence_locations"].add(location_key)
                        processed_combinations.add(combination_key)
        
        # Convert sets to sorted lists for JSON serialization
        for rule_id in aggregated:
            aggregated[rule_id]["sources"] = sorted(list(aggregated[rule_id]["sources"]))
            aggregated[rule_id]["files"] = sorted(list(aggregated[rule_id]["files"]))
            aggregated[rule_id]["evidence_locations"] = sorted(list(aggregated[rule_id]["evidence_locations"]))
        
        return dict(aggregated)
    
    def aggregate_by_semantic_groups(self, rule_aggregated_data: Dict) -> Dict:
        """Aggregate rule-based data into semantic groups."""
        if not self.semantic_groupings:
            print("No semantic groupings available. Returning rule-based aggregation.")
            return rule_aggregated_data
        
        semantic_aggregated = {}
        unmatched_rules = {}
        
        # Create a reverse mapping from CWE to group_id
        cwe_to_group = {}
        for group_id, group_info in self.semantic_groupings.items():
            for cwe in group_info.get("cwes", []):
                cwe_to_group[cwe] = group_id
        
        # Process each rule and assign to semantic group or keep individual
        for rule_id, rule_data in rule_aggregated_data.items():
            group_id = cwe_to_group.get(rule_id)
            
            if group_id:
                # This rule belongs to a semantic group
                if group_id not in semantic_aggregated:
                    group_info = self.semantic_groupings[group_id]
                    semantic_aggregated[group_id] = {
                        "rule_id": group_id,
                        "rule_description": group_info.get("display_name", ""),
                        "message": group_info.get("description", ""),
                        "severity": group_info.get("severity", "MEDIUM"),
                        "sources": set(),
                        "count": 0,
                        "files": set(),
                        "evidence_locations": set(),
                        "grouped_cwes": []
                    }
                
                # Merge this rule into the semantic group
                semantic_aggregated[group_id]["sources"].update(rule_data["sources"])
                semantic_aggregated[group_id]["count"] += rule_data["count"]
                semantic_aggregated[group_id]["files"].update(rule_data["files"])
                semantic_aggregated[group_id]["evidence_locations"].update(rule_data["evidence_locations"])
                
                # Track which CWEs were grouped
                semantic_aggregated[group_id]["grouped_cwes"].append({
                    "cwe": rule_id,
                    "count": rule_data["count"],
                    "original_description": rule_data["rule_description"]
                })
                
            else:
                # This rule doesn't belong to any semantic group - keep it individual
                unmatched_rules[rule_id] = rule_data
        
        # Convert sets to sorted lists for JSON serialization
        for group_id in semantic_aggregated:
            semantic_aggregated[group_id]["sources"] = sorted(list(semantic_aggregated[group_id]["sources"]))
            semantic_aggregated[group_id]["files"] = sorted(list(semantic_aggregated[group_id]["files"]))
            semantic_aggregated[group_id]["evidence_locations"] = sorted(list(semantic_aggregated[group_id]["evidence_locations"]))
            # Sort grouped CWEs by count descending
            semantic_aggregated[group_id]["grouped_cwes"] = sorted(
                semantic_aggregated[group_id]["grouped_cwes"], 
                key=lambda x: x["count"], 
                reverse=True
            )
        
        # Combine semantic groups and unmatched individual rules
        final_aggregated = {}
        final_aggregated.update(semantic_aggregated)
        final_aggregated.update(unmatched_rules)
        
        print(f"Created {len(semantic_aggregated)} semantic groups, kept {len(unmatched_rules)} individual rules")
        
        return final_aggregated
    
    def generate_summary_stats(self, aggregated_data: Dict) -> Dict:
        """Generate summary statistics for aggregated data."""
        total_rules = len(aggregated_data)
        total_findings = sum(rule_data["count"] for rule_data in aggregated_data.values())
        
        # Count by severity
        severity_counts = defaultdict(int)
        for rule_data in aggregated_data.values():
            severity_counts[rule_data["severity"]] += rule_data["count"]
        
        # Count by source tools
        source_counts = defaultdict(int)
        for rule_data in aggregated_data.values():
            for source in rule_data["sources"]:
                source_counts[source] += rule_data["count"]
        
        # Top vulnerabilities by count
        top_vulnerabilities = sorted(
            [(rule_id, data["count"], data["severity"]) for rule_id, data in aggregated_data.items()],
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        return {
            "total_unique_rules": total_rules,
            "total_findings": total_findings,
            "severity_distribution": dict(severity_counts),
            "source_distribution": dict(source_counts),
            "top_10_vulnerabilities": [
                {
                    "rule_id": rule_id,
                    "count": count,
                    "severity": severity
                } for rule_id, count, severity in top_vulnerabilities
            ]
        }
    
    def aggregate_report(self, output_file: str = "aggregated_sast_report.json", use_semantic_groups: bool = True) -> Dict:
        """Main method to aggregate the merged report."""
        
        print(f"Loading merged report: {self.report_path}")
        merged_report = self.load_merged_report()
        
        print("Aggregating findings by rule_id...")
        rule_aggregated_data = self.aggregate_by_rule_id(merged_report)
        
        # Apply semantic grouping if enabled
        if use_semantic_groups and self.semantic_groupings:
            print("Applying semantic grouping...")
            aggregated_data = self.aggregate_by_semantic_groups(rule_aggregated_data)
            aggregation_type = "by_semantic_groups"
        else:
            aggregated_data = rule_aggregated_data
            aggregation_type = "by_rule_id"
        
        print("Generating summary statistics...")
        summary_stats = self.generate_summary_stats(aggregated_data)
        
        # Create final aggregated report
        aggregated_report = {
            "metadata": {
                "source_report": str(self.report_path),
                "generated_at": "2025-08-24T00:00:00Z",
                "aggregation_type": aggregation_type
            },
            "summary": summary_stats,
            "aggregated_findings": aggregated_data
        }
        
        # Save aggregated report
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(aggregated_report, f, indent=2, ensure_ascii=False)
        
        print(f"\nAggregated report saved to: {output_file}")
        print(f"Summary:")
        print(f"  Unique vulnerability types: {summary_stats['total_unique_rules']}")
        print(f"  Total findings: {summary_stats['total_findings']}")
        print(f"  Severity distribution: {summary_stats['severity_distribution']}")
        print(f"  Source distribution: {summary_stats['source_distribution']}")
        
        # Show top vulnerabilities
        print(f"\nTop 5 most frequent vulnerabilities:")
        for i, vuln in enumerate(summary_stats['top_10_vulnerabilities'][:5], 1):
            print(f"  {i}. {vuln['rule_id']} ({vuln['severity']}): {vuln['count']} occurrences")
        
        return aggregated_report


def aggregate_sast_report(
    input_file: str = "merged_report_v11.json",
    output_file: str = "aggregated_sast_report_v4.json",
    mappings_file: str = None,
    use_semantic_groups: bool = True
) -> Dict:
    """
    Aggregate merged SAST report by rule_id or semantic groups.
    
    Args:
        input_file: Path to merged report JSON file
        output_file: Output file path for aggregated report
        mappings_file: Path to rule mappings JSON (optional)
        use_semantic_groups: Enable semantic grouping
        
    Returns:
        Aggregated report dictionary
    """
    aggregator = ReportAggregator(input_file, mappings_file)
    return aggregator.aggregate_report(output_file, use_semantic_groups)


def main():
    """Example usage with Python parameters."""
    try:
        # Aggregate SAST report with semantic grouping
        dir_path = "/Users/izelikson/python/CryptoSlon/SAST/reports/test_5/"
        result = aggregate_sast_report(
            input_file=f"{dir_path}/merged_report.json",
            output_file=f"{dir_path}/aggregated_report.json",
            mappings_file=None,  # Uses default rule_mappings.json
            use_semantic_groups=True
        )
        
        print(f"\n✅ Report aggregation completed successfully!")
        print(f"📊 Generated {len(result['aggregated_findings'])} aggregated findings")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Report aggregation failed: {e}")
        import traceback
        traceback.print_exc()
        return {}


if __name__ == "__main__":
    main()

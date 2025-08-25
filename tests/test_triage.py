#!/usr/bin/env python3
"""
Example of using SAST triage programmatically.
This shows how to call triage analysis with different models and settings.
"""

from ..SAST.triage import analyze_sast_report, SASTTriageAnalyzer

def example_basic_usage():
    """Basic usage example with default settings."""
    print("🔥 Basic SAST Triage Analysis")
    print("=" * 50)
    
    result = analyze_sast_report(
        input_file="../SAST/reports/test_1/aggregated_sast_report_semantic_v1.json",
        output_file="triage_basic_example.json",
        model="gpt-4o-mini",
        show_summary=True
    )
    
    print(f"Analysis completed! Found {len(result.get('result', []))} vulnerabilities.")
    return result

def example_advanced_usage():
    """Advanced usage with different model and custom settings."""
    print("\n🚀 Advanced SAST Triage Analysis")
    print("=" * 50)
    
    result = analyze_sast_report(
        input_file="../SAST/reports/test_1/aggregated_sast_report_semantic_v1.json",
        output_file="triage_advanced_example.json",
        model="gpt-4o",  # Using more powerful model
        template="sast",
        show_summary=False  # Don't show summary
    )
    
    # Custom processing of results
    if result.get("metadata", {}).get("is_json", False):
        vulnerabilities = result.get("result", [])
        print(f"\n📊 Custom Analysis Summary:")
        print(f"Total vulnerabilities analyzed: {len(vulnerabilities)}")
        
        # Count by risk level
        risk_counts = {}
        for vuln in vulnerabilities:
            risk = vuln.get("Риск", "UNKNOWN").split(" - ")[0]
            risk_counts[risk] = risk_counts.get(risk, 0) + 1
        
        print(f"Risk distribution:")
        for risk, count in risk_counts.items():
            print(f"  {risk}: {count}")
    
    return result

def example_class_usage():
    """Example using the SASTTriageAnalyzer class directly."""
    print("\n🔧 Direct Class Usage Example")
    print("=" * 50)
    
    # Initialize analyzer with specific model
    analyzer = SASTTriageAnalyzer(
        model="gpt-4o-mini",
        template_name="sast"
    )
    
    # Run analysis
    result = analyzer.analyze_sast_report(
        report_path="../SAST/reports/test_1/aggregated_sast_report_semantic_v1.json",
        output_file="triage_class_example.json"
    )
    
    # Display custom summary
    if result.get("metadata", {}).get("is_json", False):
        print(f"\n📋 Custom Summary Display:")
        vulnerabilities = result.get("result", [])
        for i, vuln in enumerate(vulnerabilities, 1):
            name = vuln.get("Название", "Unknown")
            cwe = vuln.get("CWE", "Unknown")
            print(f"  {i}. {name} ({cwe})")
    
    return result

def main():
    """Run all examples."""
    try:
        # Example 1: Basic usage
        result1 = example_basic_usage()
        
        # Example 2: Advanced usage
        result2 = example_advanced_usage()
        
        # Example 3: Direct class usage
        result3 = example_class_usage()
        
        print(f"\n✅ All examples completed successfully!")
        print(f"Generated {len([r for r in [result1, result2, result3] if r])} analysis reports.")
        
    except Exception as e:
        print(f"\n❌ Example failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

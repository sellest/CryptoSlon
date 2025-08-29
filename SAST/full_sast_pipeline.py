#!/usr/bin/env python3
"""
Full SAST Pipeline - Complete Static Application Security Testing workflow
Orchestrates all 8 SAST modules in the correct sequence for end-to-end vulnerability analysis and fixing.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Import all SAST modules
from semgrep_analyzer import run_semgrep_analysis
from bandit_analyzer import run_bandit_analysis
from report_merger import run_report_merger
from report_aggregator import run_report_aggregator
from triage import run_sast_triage
from snippet_extractor import run_snippet_extractor
from vulnerability_fixer import run_vulnerability_fixer
from code_injector import run_code_injector


class FullSASTPipeline:
    """
    Complete SAST pipeline that runs all 8 modules in sequence:
    1. Semgrep analysis
    2. Bandit analysis  
    3. Report merging
    4. Report aggregation
    5. Vulnerability triage
    6. Code snippet extraction
    7. Vulnerability fix generation
    8. Code injection
    """
    
    def __init__(self, reports_path: str, code_base_path: str, log_level: str = "INFO"):
        """
        Initialize SAST pipeline
        
        Args:
            reports_path: Directory where all reports will be stored
            code_base_path: Path to the code base to analyze
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        """
        self.reports_path = Path(reports_path)
        self.code_base_path = Path(code_base_path)
        self.log_level = log_level
        
        # Create reports directory if it doesn't exist
        self.reports_path.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Pipeline state tracking
        self.pipeline_results = {
            "start_time": datetime.now(),
            "reports_directory": str(self.reports_path),
            "code_base_path": str(self.code_base_path),
            "stages": {},
            "overall_success": False,
            "error_summary": []
        }
        
        self.logger.info(f"SAST Pipeline initialized - Reports: {self.reports_path}, Code: {self.code_base_path}")
    
    def run_full_pipeline(
        self,
        semgrep_config: str = None,
        triage_model: str = "gigachat-pro",
        triage_template: str = "sast_v4",
        fix_model: str = "gigachat-pro",
        fix_template: str = "vulnerability_fix_v7",
        max_vulnerabilities: Optional[int] = None,
        context_lines: int = 5,
        interactive_injection: bool = False,
        skip_injection: bool = False,
        use_bandit: bool = True
    ) -> Dict[str, Any]:
        """
        Run the complete 8-stage SAST pipeline
        
        Args:
            semgrep_config: Semgrep configuration/ruleset
            triage_model: LLM model for triage analysis
            triage_template: Prompt template for triage
            fix_model: LLM model for fix generation
            fix_template: Prompt template for fix generation
            max_vulnerabilities: Limit fixes for testing (None = no limit)
            context_lines: Lines of context around vulnerable code
            interactive_injection: Ask for confirmation before applying fixes
            skip_injection: Skip final code injection stage (safety)
            use_bandit: Additional vulnerability check with bandit lib
            
        Returns:
            Complete pipeline results dictionary
        """
        self.logger.info("Starting full SAST pipeline execution")
        
        try:
            # Stage 1: Semgrep Analysis
            self._run_semgrep_stage(semgrep_config)
            
            # Stage 2: Bandit Analysis
            if use_bandit:
                self._run_bandit_stage()
            
            # Stage 3: Report Merging
            self._run_merger_stage()
            
            # Stage 4: Report Aggregation
            self._run_aggregator_stage()
            
            # Stage 5: Vulnerability Triage
            self._run_triage_stage(triage_model, triage_template)
            
            # Stage 6: Code Snippet Extraction
            self._run_snippet_extraction_stage(context_lines)
            
            # Stage 7: Vulnerability Fix Generation
            self._run_fix_generation_stage(fix_model, fix_template, max_vulnerabilities)
            
            # Stage 8: Code Injection (optional)
            if not skip_injection:
                self._run_code_injection_stage(interactive_injection)
            else:
                self.logger.info("Stage 8: Code injection skipped (skip_injection=True)")
                self.pipeline_results["stages"]["code_injection"] = {
                    "success": True,
                    "skipped": True,
                    "message": "Code injection skipped by user request"
                }
            
        except Exception as e:
            self.logger.error(f"Pipeline execution failed: {e}")
            self.pipeline_results["overall_success"] = False
            self.pipeline_results["fatal_error"] = str(e)
        
        # Always set end_time and calculate duration
        self.pipeline_results["end_time"] = datetime.now()
        duration = self.pipeline_results["end_time"] - self.pipeline_results["start_time"]
        self.pipeline_results["total_duration"] = duration.total_seconds()
        
        # Determine overall success based on completed stages
        successful_stages = sum(1 for stage in self.pipeline_results["stages"].values() if stage.get("success", False))
        total_stages = len(self.pipeline_results["stages"])
        self.pipeline_results["successful_stages"] = successful_stages
        self.pipeline_results["total_stages"] = total_stages
        self.pipeline_results["overall_success"] = successful_stages >= total_stages - 1  # Allow 1 stage to fail
        
        return self.pipeline_results
    
    def _run_semgrep_stage(self, config: str = None):
        """Stage 1: Semgrep Analysis"""
        self.logger.info("Stage 1: Running Semgrep analysis...")
        stage_name = "semgrep_analysis"
        
        # Resolve config path dynamically if not provided
        if config is None:
            # Get the SAST directory relative to this file
            sast_dir = Path(__file__).parent
            rules_file = sast_dir / "rules" / "python-security.yml"
            
            if rules_file.exists():
                config = str(rules_file)
                self.logger.info(f"Using project semgrep config: {config}")
            else:
                config = "auto"
                self.logger.info("Project semgrep config not found, using 'auto'")
        elif config and not config.startswith(("auto", "p/", "r/")):
            # Handle relative paths by making them absolute relative to SAST dir
            if not Path(config).is_absolute():
                sast_dir = Path(__file__).parent
                config_path = sast_dir / config
                if config_path.exists():
                    config = str(config_path)
                    self.logger.info(f"Using resolved semgrep config: {config}")
                else:
                    self.logger.warning(f"Config file {config} not found, using 'auto'")
                    config = "auto"
        
        try:
            result = run_semgrep_analysis(
                target_path=str(self.code_base_path),
                output_file=str(self.reports_path / "semgrep_report.sarif"),
                output_format="sarif",
                config=config,
                log_level=self.log_level
            )
            
            self.pipeline_results["stages"][stage_name] = {
                "success": result["success"],
                "data": result["data"] if result["success"] else None,
                "error": result.get("error"),
                "output_file": str(self.reports_path / "semgrep_report.sarif")
            }
            
            if result["success"]:
                issue_count = result["data"]["issue_count"]
                self.logger.info(f"Semgrep analysis completed: {issue_count} issues found")
            else:
                self.logger.error(f"Semgrep analysis failed: {result['error']}")
                raise RuntimeError(f"Semgrep stage failed: {result['error']}")
                
        except Exception as e:
            self.logger.error(f"Semgrep stage error: {e}")
            self.pipeline_results["stages"][stage_name] = {
                "success": False,
                "error": str(e)
            }
            raise
    
    def _run_bandit_stage(self):
        """Stage 2: Bandit Analysis"""
        self.logger.info("Stage 2: Running Bandit analysis...")
        stage_name = "bandit_analysis"
        
        try:
            result = run_bandit_analysis(
                target_path=str(self.code_base_path),
                output_file=str(self.reports_path / "bandit_report.sarif"),
                output_format="sarif",
                log_level=self.log_level
            )
            
            self.pipeline_results["stages"][stage_name] = {
                "success": result["success"],
                "data": result["data"] if result["success"] else None,
                "error": result.get("error"),
                "output_file": str(self.reports_path / "bandit_report.sarif")
            }
            
            if result["success"]:
                issue_count = result["data"]["issue_count"]
                self.logger.info(f"Bandit analysis completed: {issue_count} issues found")
            else:
                self.logger.error(f"Bandit analysis failed: {result['error']}")
                raise RuntimeError(f"Bandit stage failed: {result['error']}")
                
        except Exception as e:
            self.logger.error(f"Bandit stage error: {e}")
            self.pipeline_results["stages"][stage_name] = {
                "success": False,
                "error": str(e)
            }
            raise
    
    def _run_merger_stage(self):
        """Stage 3: Report Merging"""
        self.logger.info("Stage 3: Merging SARIF reports...")
        stage_name = "report_merger"
        
        try:
            result = run_report_merger(
                semgrep_file=str(self.reports_path / "semgrep_report.sarif"),
                bandit_file=str(self.reports_path / "bandit_report.sarif"),
                output_file=str(self.reports_path / "merged_report.json"),
                log_level=self.log_level
            )
            
            self.pipeline_results["stages"][stage_name] = {
                "success": result["success"],
                "data": result["data"] if result["success"] else None,
                "error": result.get("error"),
                "output_file": str(self.reports_path / "merged_report.json")
            }
            
            if result["success"]:
                total_findings = result["data"]["total_findings"]
                agreement_rate = result["data"]["agreement_rate"]
                self.logger.info(f"Report merging completed: {total_findings} total findings, {agreement_rate:.1f}% agreement")
            else:
                self.logger.error(f"Report merging failed: {result['error']}")
                raise RuntimeError(f"Merger stage failed: {result['error']}")
                
        except Exception as e:
            self.logger.error(f"Merger stage error: {e}")
            self.pipeline_results["stages"][stage_name] = {
                "success": False,
                "error": str(e)
            }
            raise
    
    def _run_aggregator_stage(self):
        """Stage 4: Report Aggregation"""
        self.logger.info("Stage 4: Aggregating vulnerability findings...")
        stage_name = "report_aggregator"
        
        try:
            result = run_report_aggregator(
                input_file=str(self.reports_path / "merged_report.json"),
                output_file=str(self.reports_path / "aggregated_report.json"),
                log_level=self.log_level
            )
            
            self.pipeline_results["stages"][stage_name] = {
                "success": result["success"],
                "data": result["data"] if result["success"] else None,
                "error": result.get("error"),
                "output_file": str(self.reports_path / "aggregated_report.json")
            }
            
            if result["success"]:
                total_findings = result["data"]["total_findings"]
                unique_cwe = len(result["data"]["severity_distribution"])
                self.logger.info(f"Report aggregation completed: {total_findings} findings across {unique_cwe} CWE types")
            else:
                self.logger.error(f"Report aggregation failed: {result['error']}")
                raise RuntimeError(f"Aggregator stage failed: {result['error']}")
                
        except Exception as e:
            self.logger.error(f"Aggregator stage error: {e}")
            self.pipeline_results["stages"][stage_name] = {
                "success": False,
                "error": str(e)
            }
            raise
    
    def _run_triage_stage(self, model: str, template: str):
        """Stage 5: Vulnerability Triage"""
        self.logger.info("Stage 5: Running vulnerability triage analysis...")
        stage_name = "vulnerability_triage"
        
        try:
            result = run_sast_triage(
                input_file=str(self.reports_path / "aggregated_report.json"),
                output_file=str(self.reports_path / "triage_analysis.json"),
                model=model,
                template=template,
                show_summary=False,
                log_level=self.log_level
            )
            
            self.pipeline_results["stages"][stage_name] = {
                "success": result["success"],
                "data": result["data"] if result["success"] else None,
                "error": result.get("error"),
                "output_file": str(self.reports_path / "triage_analysis.json")
            }
            
            if result["success"]:
                model_used = result["data"]["model_used"]
                total_findings = result["data"]["total_findings"]
                self.logger.info(f"Triage analysis completed: {total_findings} findings analyzed with {model_used}")
            else:
                self.logger.error(f"Triage analysis failed: {result['error']}")
                raise RuntimeError(f"Triage stage failed: {result['error']}")
                
        except Exception as e:
            self.logger.error(f"Triage stage error: {e}")
            self.pipeline_results["stages"][stage_name] = {
                "success": False,
                "error": str(e)
            }
            raise
    
    def _run_snippet_extraction_stage(self, context_lines: int):
        """Stage 6: Code Snippet Extraction"""
        self.logger.info("Stage 6: Extracting vulnerability code snippets...")
        stage_name = "snippet_extraction"
        
        try:
            result = run_snippet_extractor(
                triage_analysis=str(self.reports_path / "triage_analysis.json"),
                output_file=str(self.reports_path / "vulnerability_snippets.json"),
                code_base_path=str(self.code_base_path),
                context_lines=context_lines,
                show_samples=False,
                log_level=self.log_level
            )
            
            self.pipeline_results["stages"][stage_name] = {
                "success": result["success"],
                "data": result["data"] if result["success"] else None,
                "error": result.get("error"),
                "output_file": str(self.reports_path / "vulnerability_snippets.json")
            }
            
            if result["success"]:
                total_snippets = result["data"]["total_snippets"]
                self.logger.info(f"Snippet extraction completed: {total_snippets} snippets extracted")
            else:
                self.logger.error(f"Snippet extraction failed: {result['error']}")
                raise RuntimeError(f"Snippet extraction stage failed: {result['error']}")
                
        except Exception as e:
            self.logger.error(f"Snippet extraction stage error: {e}")
            self.pipeline_results["stages"][stage_name] = {
                "success": False,
                "error": str(e)
            }
            raise
    
    def _run_fix_generation_stage(self, model: str, template: str, max_vulnerabilities: Optional[int]):
        """Stage 7: Vulnerability Fix Generation"""
        self.logger.info("Stage 7: Generating vulnerability fixes...")
        stage_name = "fix_generation"
        
        try:
            result = run_vulnerability_fixer(
                snippet_report=str(self.reports_path / "vulnerability_snippets.json"),
                output_file=str(self.reports_path / "vulnerability_fixes.json"),
                model=model,
                template=template,
                max_vulnerabilities=max_vulnerabilities,
                show_summary=False,
                show_progress=False,
                log_level=self.log_level
            )
            
            self.pipeline_results["stages"][stage_name] = {
                "success": result["success"],
                "data": result["data"] if result["success"] else None,
                "error": result.get("error"),
                "output_file": str(self.reports_path / "vulnerability_fixes.json")
            }
            
            if result["success"]:
                total_fixes = result["data"]["total_fixes"]
                successful_fixes = result["data"]["successful_fixes"]
                success_rate = result["data"]["success_rate"]
                self.logger.info(f"Fix generation completed: {successful_fixes}/{total_fixes} fixes generated ({success_rate:.1f}% success)")
            else:
                self.logger.error(f"Fix generation failed: {result['error']}")
                raise RuntimeError(f"Fix generation stage failed: {result['error']}")
                
        except Exception as e:
            self.logger.error(f"Fix generation stage error: {e}")
            self.pipeline_results["stages"][stage_name] = {
                "success": False,
                "error": str(e)
            }
            raise
    
    def _run_code_injection_stage(self, interactive: bool):
        """Stage 8: Code Injection"""
        self.logger.info("Stage 8: Applying vulnerability fixes...")
        stage_name = "code_injection"
        
        try:
            result = run_code_injector(
                fixes_report=str(self.reports_path / "vulnerability_fixes.json"),
                code_base_path=str(self.code_base_path),
                backup_dir=None,  # Auto-generate backup directory
                interactive=interactive,
                show_summary=False,
                log_level=self.log_level
            )
            
            self.pipeline_results["stages"][stage_name] = {
                "success": result["success"],
                "data": result["data"] if result["success"] else None,
                "error": result.get("error"),
                "backup_directory": result["data"]["backup_dir"] if result["success"] else None
            }
            
            if result["success"]:
                total_fixes = result["data"]["total_fixes"]
                applied = result["data"]["applied"]
                success_rate = result["data"]["success_rate"]
                backup_dir = result["data"]["backup_dir"]
                self.logger.info(f"Code injection completed: {applied}/{total_fixes} fixes applied ({success_rate:.1f}% success)")
                self.logger.info(f"Backup created at: {backup_dir}")
            else:
                self.logger.error(f"Code injection failed: {result['error']}")
                raise RuntimeError(f"Code injection stage failed: {result['error']}")
                
        except Exception as e:
            self.logger.error(f"Code injection stage error: {e}")
            self.pipeline_results["stages"][stage_name] = {
                "success": False,
                "error": str(e)
            }
            raise
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a concise pipeline summary"""
        if not self.pipeline_results.get("end_time"):
            return {"status": "running", "message": "Pipeline still executing"}
        
        summary = {
            "overall_success": self.pipeline_results["overall_success"],
            "successful_stages": self.pipeline_results.get("successful_stages", 0),
            "total_stages": self.pipeline_results.get("total_stages", 0),
            "duration_seconds": self.pipeline_results.get("total_duration", 0),
            "reports_directory": self.pipeline_results["reports_directory"],
            "stage_summary": {}
        }
        
        for stage_name, stage_data in self.pipeline_results["stages"].items():
            summary["stage_summary"][stage_name] = {
                "success": stage_data["success"],
                "output_file": stage_data.get("output_file"),
                "error": stage_data.get("error") if not stage_data["success"] else None
            }
        
        return summary


def pipeline_run(**kwargs) -> Dict[str, Any]:
    """
    Agent-friendly function to run the full SAST pipeline
    
    Args:
        code_base_path (str, required): Path to code base to analyze
        reports_path (str, optional): Directory for reports (default: "./sast_reports")
        log_level (str, optional): Logging level (default: "INFO")
        semgrep_config (str, optional): Semgrep configuration (default: None - auto-detect)
        triage_model (str, optional): LLM model for triage (default: "gigachat-pro")
        triage_template (str, optional): Prompt template for triage (default: "sast_v4")
        fix_model (str, optional): LLM model for fix generation (default: "gigachat-pro")
        fix_template (str, optional): Prompt template for fixes (default: "vulnerability_fix_v7")
        max_vulnerabilities (int, optional): Limit fixes for testing (default: 20)
        context_lines (int, optional): Context lines around vulnerable code (default: 5)
        interactive_injection (bool, optional): Interactive code injection (default: False)
        skip_injection (bool, optional): Skip code injection stage (default: False)
        use_bandit (bool, optional): Use additional vulnerability scan (default: True)
        
    Returns:
        Dict with standardized format:
        {
            "success": bool,
            "data": {
                "pipeline_results": complete pipeline results dict,
                "summary": pipeline summary dict,
                "reports_directory": str,
                "overall_success": bool,
                "successful_stages": int,
                "total_stages": int,
                "duration_seconds": float
            },
            "error": str or None
        }
    """
    # Extract parameters with defaults
    code_base_path = kwargs.get("code_base_path")
    if not code_base_path:
        return {
            "success": False,
            "error": "Required parameter 'code_base_path' is missing",
            "data": None
        }
    
    reports_path = kwargs.get("reports_path", "./sast_reports")
    log_level = kwargs.get("log_level", "INFO")
    
    # Pipeline configuration parameters
    semgrep_config = kwargs.get("semgrep_config", "rules/python-security.yml")
    triage_model = kwargs.get("triage_model", "gigachat-max")
    triage_template = kwargs.get("triage_template", "sast_v4")
    fix_model = kwargs.get("fix_model", "gigachat-max")
    fix_template = kwargs.get("fix_template", "vulnerability_fix_v7")
    max_vulnerabilities = kwargs.get("max_vulnerabilities", 20)
    context_lines = kwargs.get("context_lines", 5)
    interactive_injection = kwargs.get("interactive_injection", False)
    skip_injection = kwargs.get("skip_injection", False)
    use_bandit = kwargs.get("use_bandit", True)
    
    try:
        # Initialize pipeline
        pipeline = FullSASTPipeline(
            reports_path=reports_path,
            code_base_path=code_base_path,
            log_level=log_level
        )
        
        # Run full pipeline
        pipeline_results = pipeline.run_full_pipeline(
            semgrep_config=semgrep_config,
            triage_model=triage_model,
            triage_template=triage_template,
            fix_model=fix_model,
            fix_template=fix_template,
            max_vulnerabilities=max_vulnerabilities,
            context_lines=context_lines,
            interactive_injection=interactive_injection,
            skip_injection=skip_injection
        )
        
        # Get summary
        summary = pipeline.get_summary()
        
        return {
            "success": True,
            "data": {
                "pipeline_results": pipeline_results,
                "summary": summary,
                "reports_directory": summary["reports_directory"],
                "overall_success": summary["overall_success"],
                "successful_stages": summary["successful_stages"],
                "total_stages": summary["total_stages"],
                "duration_seconds": summary["duration_seconds"]
            },
            "error": None
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "data": None
        }

def usage_example():
    result = pipeline_run(
        code_base_path="/Users/izelikson/python/CryptoSlon/SAST/code_for_sast/taskstate_control_3",
        reports_path="/Users/izelikson/python/CryptoSlon/SAST/reports",
        triage_model="gpt-5",
        fix_model="gigachat-max",
        context_lines=5,
        max_vulnerabilities=10,
        skip_injection=False,
        use_bandit=False
    )
    
    if result["success"]:
        summary = result["data"]["summary"]
        print(f"Analysis completed in {summary['duration_seconds']:.1f} seconds")
        
        # Access detailed stage results
        for stage_name, stage_info in summary['stage_summary'].items():
            if stage_info['success']:
                print(f"✅ {stage_name}: {stage_info['output_file']}")
            else:
                print(f"❌ {stage_name}: {stage_info['error']}")
    
    return result


if __name__ == "__main__":
    usage_example()

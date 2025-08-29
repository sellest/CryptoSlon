# -*- coding: utf-8 -*-
"""
SAST Pipeline Tools for AI agents - Combines all SAST modules into 4 comprehensive tools
"""

import logging
import sys
import os
from pathlib import Path
from typing import Dict, Any
from agents.base_tool import BaseTool

# Add SAST directory to path - multiple approaches for robustness
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent  # /Users/.../CryptoSlon/
sast_dir = project_root / "SAST"

# Add both absolute and relative paths
sys.path.insert(0, str(sast_dir))
sys.path.insert(0, str(project_root))

# Try different import approaches
try:
    # Direct imports from SAST directory
    from semgrep_analyzer import run_semgrep_analysis
    from bandit_analyzer import run_bandit_analysis
    from report_merger import run_report_merger
    from report_aggregator import run_report_aggregator
    from triage import run_sast_triage
    from snippet_extractor import run_snippet_extractor
    from vulnerability_fixer import run_vulnerability_fixer
    from code_injector import run_code_injector
except ImportError as e:
    # Fallback: try importing from SAST module
    try:
        from SAST.semgrep_analyzer import run_semgrep_analysis
        from SAST.bandit_analyzer import run_bandit_analysis
        from SAST.report_merger import run_report_merger
        from SAST.report_aggregator import run_report_aggregator
        from SAST.triage import run_sast_triage
        from SAST.snippet_extractor import run_snippet_extractor
        from SAST.vulnerability_fixer import run_vulnerability_fixer
        from SAST.code_injector import run_code_injector
    except ImportError as e2:
        raise ImportError(f"Could not import SAST modules. Original errors: {e} | {e2}")


class SASTAnalysisTool(BaseTool):
    """
    Tool 1: Complete SAST analysis pipeline
    Combines semgrep, bandit, report merger, and aggregator
    """

    @property
    def name(self) -> str:
        return "sast_analysis"

    @property
    def description(self) -> str:
        return "Run complete SAST analysis: Semgrep + Bandit + Report merging + Aggregation. Returns comprehensive vulnerability report."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "code_base_path": {
                "type": "string",
                "description": "Path to code directory to analyze (required)"
            },
            "output_dir": {
                "type": "string", 
                "description": "Output directory for reports (default: current directory)"
            },
            "semgrep_config": {
                "type": "string",
                "description": "Semgrep config/ruleset (default: 'auto')"
            },
            "log_level": {
                "type": "string",
                "description": "Logging level (DEBUG, INFO, WARNING, ERROR)"
            }
        }

    def execute(self, code_base_path: str, output_dir: str = None, semgrep_config: str = "../SAST/rules/python-security.yml", log_level: str = "INFO") -> Dict[str, Any]:
        """Execute complete SAST analysis pipeline"""
        logger = logging.getLogger(f"tool.{self.name}")
        logger.info(f"Running SAST analysis on: {code_base_path}")
        print("Активирован инструмент: sast_analysis")
        
        # Auto-create output directory if not specified
        if output_dir is None:
            from pathlib import Path
            code_base = Path(code_base_path).resolve()
            output_dir = str(code_base.parent / "reports" / f"sast_analysis_{code_base.name}")
            logger.info(f"Auto-created output directory: {output_dir}")
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"Reports will be saved to: {output_dir}")
        
        try:
            results = {
                "success": True,
                "pipeline_step": "sast_analysis",
                "steps_completed": [],
                "data": {},
                "errors": []
            }
            
            # Step 1: Run Semgrep analysis
            logger.info("Step 1: Running Semgrep analysis...")
            semgrep_result = run_semgrep_analysis(
                target_path=code_base_path,
                output_file=f"{output_dir}/semgrep_report.sarif",
                output_format="sarif",
                config=semgrep_config,
                log_level=log_level
            )
            
            if semgrep_result["success"]:
                results["steps_completed"].append("semgrep")
                results["data"]["semgrep"] = semgrep_result["data"]
                logger.info(f"Semgrep found {semgrep_result['data']['issue_count']} issues")
            else:
                results["errors"].append(f"Semgrep failed: {semgrep_result['error']}")
                logger.error(f"Semgrep analysis failed: {semgrep_result['error']}")
            
            # Step 2: Run Bandit analysis
            logger.info("Step 2: Running Bandit analysis...")
            bandit_result = run_bandit_analysis(
                target_path=code_base_path,
                output_file=f"{output_dir}/bandit_report.sarif",
                output_format="sarif",
                log_level=log_level
            )
            
            if bandit_result["success"]:
                results["steps_completed"].append("bandit")
                results["data"]["bandit"] = bandit_result["data"]
                logger.info(f"Bandit found {bandit_result['data']['issue_count']} issues")
            else:
                results["errors"].append(f"Bandit failed: {bandit_result['error']}")
                logger.error(f"Bandit analysis failed: {bandit_result['error']}")
            
            # Step 3: Merge reports (only if both tools succeeded)
            if "semgrep" in results["steps_completed"] and "bandit" in results["steps_completed"]:
                logger.info("Step 3: Merging SARIF reports...")
                merger_result = run_report_merger(
                    semgrep_file=f"{output_dir}/semgrep_report.sarif",
                    bandit_file=f"{output_dir}/bandit_report.sarif",
                    output_file=f"{output_dir}/merged_report.json",
                    log_level=log_level
                )
                
                if merger_result["success"]:
                    results["steps_completed"].append("merger")
                    results["data"]["merger"] = merger_result["data"]
                    logger.info("Report merging completed successfully")
                else:
                    results["errors"].append(f"Report merger failed: {merger_result['error']}")
                    logger.error(f"Report merger failed: {merger_result['error']}")
            
                # Step 4: Aggregate findings (only if merge succeeded)
                if "merger" in results["steps_completed"]:
                    logger.info("Step 4: Aggregating vulnerability findings...")
                    aggregator_result = run_report_aggregator(
                        input_file=f"{output_dir}/merged_report.json",
                        output_file=f"{output_dir}/aggregated_report.json",
                        log_level=log_level
                    )
                    
                    if aggregator_result["success"]:
                        results["steps_completed"].append("aggregator")
                        results["data"]["aggregator"] = aggregator_result["data"]
                        logger.info(f"Aggregation completed: {aggregator_result['data']['total_findings']} total findings")
                    else:
                        results["errors"].append(f"Aggregator failed: {aggregator_result['error']}")
                        logger.error(f"Aggregator failed: {aggregator_result['error']}")
            
            # Determine overall success
            results["success"] = len(results["steps_completed"]) >= 2  # At least 2 steps must succeed
            
            # Summary
            results["summary"] = {
                "target_analyzed": code_base_path,
                "output_directory": output_dir,
                "steps_completed": len(results["steps_completed"]),
                "total_errors": len(results["errors"]),
                "final_report": f"{output_dir}/aggregated_report.json" if "aggregator" in results["steps_completed"] else None
            }
            
            return results
            
        except Exception as e:
            logger.error(f"SAST analysis pipeline failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "pipeline_step": "sast_analysis"
            }


class SASTTriageTool(BaseTool):
    """
    Tool 2: SAST Triage Analysis
    Uses LLM to analyze and prioritize vulnerability findings
    """

    @property
    def name(self) -> str:
        return "sast_triage"

    @property
    def description(self) -> str:
        return "Analyze aggregated SAST report using LLM to prioritize and triage vulnerabilities. Requires aggregated report from sast_analysis tool."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "aggregated_report": {
                "type": "string",
                "description": "Path to aggregated SAST report JSON file (required)"
            },
            "output_file": {
                "type": "string",
                "description": "Output file for triage analysis (default: triage_analysis.json)"
            },
            "model": {
                "type": "string", 
                "description": "LLM model to use (default: gigachat-pro)"
            },
            "template": {
                "type": "string",
                "description": "Prompt template name (default: sast)"
            },
            "log_level": {
                "type": "string",
                "description": "Logging level (DEBUG, INFO, WARNING, ERROR)"
            }
        }

    def execute(self, aggregated_report: str, output_file: str = "triage_analysis.json", 
                model: str = "gigachat-pro", template: str = "sast_v4", log_level: str = "INFO") -> Dict[str, Any]:
        """Execute SAST triage analysis"""
        logger = logging.getLogger(f"tool.{self.name}")
        logger.info(f"Running SAST triage analysis on: {aggregated_report}")
        print("Активирован инструмент: triage_analysis")
        
        try:
            # Run triage analysis
            triage_result = run_sast_triage(
                input_file=aggregated_report,
                output_file=output_file,
                model=model,
                template=template,
                show_summary=False,
                log_level=log_level
            )
            
            if triage_result["success"]:
                logger.info("Triage analysis completed successfully")
                
                return {
                    "success": True,
                    "pipeline_step": "triage",
                    "data": triage_result["data"],
                    "summary": {
                        "input_report": aggregated_report,
                        "output_file": output_file,
                        "model_used": triage_result["data"]["model_used"],
                        "template_used": triage_result["data"]["template_used"],
                        "total_findings": triage_result["data"]["total_findings"],
                        "response_format": "JSON" if triage_result["data"]["is_json"] else "Text"
                    }
                }
            else:
                logger.error(f"Triage analysis failed: {triage_result['error']}")
                return {
                    "success": False,
                    "error": triage_result["error"],
                    "pipeline_step": "triage"
                }
                
        except Exception as e:
            logger.error(f"SAST triage pipeline failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "pipeline_step": "triage"
            }


class SASTFixGenerationTool(BaseTool):
    """
    Tool 3: Vulnerability Fix Generation
    Extracts code snippets and generates LLM fixes
    """

    @property
    def name(self) -> str:
        return "sast_fix_generation"

    @property
    def description(self) -> str:
        return "Extract vulnerable code snippets and generate LLM-based fixes. Requires triage analysis from sast_triage tool."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "triage_analysis": {
                "type": "string",
                "description": "Path to triage analysis JSON file (required)"
            },
            "code_base_path": {
                "type": "string",
                "description": "Base path for code files (required)"
            },
            "output_dir": {
                "type": "string",
                "description": "Output directory for snippets and fixes (default: current directory)"
            },
            "model": {
                "type": "string",
                "description": "LLM model to use for fix generation (default: gpt-4o-mini)"
            },
            "template": {
                "type": "string", 
                "description": "Fix generation template (default: vulnerability_fix_v7)"
            },
            "max_vulnerabilities": {
                "type": "integer",
                "description": "Limit number of vulnerabilities to process (for testing)"
            },
            "context_lines": {
                "type": "integer",
                "description": "Number of context lines around vulnerable code (default: 10)"
            },
            "log_level": {
                "type": "string",
                "description": "Logging level (DEBUG, INFO, WARNING, ERROR)"
            }
        }

    def execute(self, triage_analysis: str, code_base_path: str, output_dir: str = ".",
                model: str = "gpt-4o-mini", template: str = "vulnerability_fix_v7",
                max_vulnerabilities: int = None, context_lines: int = 10, log_level: str = "INFO") -> Dict[str, Any]:
        """Execute vulnerability fix generation pipeline"""
        logger = logging.getLogger(f"tool.{self.name}")
        logger.info(f"Generating fixes for triage analysis: {triage_analysis}")
        print("Активирован инструмент: fix_generation")
        
        try:
            results = {
                "success": True,
                "pipeline_step": "fix_generation",
                "steps_completed": [],
                "data": {},
                "errors": []
            }
            
            # Step 1: Extract vulnerability snippets
            logger.info("Step 1: Extracting vulnerability code snippets...")
            snippets_result = run_snippet_extractor(
                triage_analysis=triage_analysis,
                output_file=f"{output_dir}/vulnerability_snippets.json",
                code_base_path=code_base_path,
                context_lines=context_lines,
                show_samples=False,
                log_level=log_level
            )
            
            if snippets_result["success"]:
                results["steps_completed"].append("snippet_extraction")
                results["data"]["snippets"] = snippets_result["data"]
                logger.info(f"Extracted {snippets_result['data']['total_snippets']} vulnerability snippets")
            else:
                results["errors"].append(f"Snippet extraction failed: {snippets_result['error']}")
                logger.error(f"Snippet extraction failed: {snippets_result['error']}")
                return {
                    "success": False,
                    "error": snippets_result["error"],
                    "pipeline_step": "fix_generation"
                }
            
            # Step 2: Generate fixes using LLM
            logger.info("Step 2: Generating LLM fixes...")
            fixes_result = run_vulnerability_fixer(
                snippet_report=f"{output_dir}/vulnerability_snippets.json",
                output_file=f"{output_dir}/vulnerability_fixes.json",
                model=model,
                template=template,
                max_vulnerabilities=max_vulnerabilities,
                show_summary=False,
                show_progress=False,
                log_level=log_level
            )
            
            if fixes_result["success"]:
                results["steps_completed"].append("fix_generation")
                results["data"]["fixes"] = fixes_result["data"]
                logger.info(f"Generated {fixes_result['data']['successful_fixes']} successful fixes out of {fixes_result['data']['total_fixes']}")
            else:
                results["errors"].append(f"Fix generation failed: {fixes_result['error']}")
                logger.error(f"Fix generation failed: {fixes_result['error']}")
            
            # Determine overall success
            results["success"] = len(results["steps_completed"]) == 2  # Both steps must succeed
            
            # Summary
            results["summary"] = {
                "triage_input": triage_analysis,
                "code_base_path": code_base_path,
                "output_directory": output_dir,
                "model_used": model,
                "template_used": template,
                "snippets_extracted": snippets_result["data"]["total_snippets"] if "snippets" in results["data"] else 0,
                "fixes_generated": fixes_result["data"]["successful_fixes"] if "fixes" in results["data"] else 0,
                "success_rate": fixes_result["data"]["success_rate"] if "fixes" in results["data"] else 0,
                "snippets_file": f"{output_dir}/vulnerability_snippets.json",
                "fixes_file": f"{output_dir}/vulnerability_fixes.json"
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Fix generation pipeline failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "pipeline_step": "fix_generation"
            }


class SASTCodeInjectionTool(BaseTool):
    """
    Tool 4: Code Injection 
    Applies generated fixes to source files
    """

    @property
    def name(self) -> str:
        return "sast_code_injection"

    @property
    def description(self) -> str:
        return "Apply LLM-generated fixes to source code files with backup. Requires vulnerability fixes from sast_fix_generation tool."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "fixes_report": {
                "type": "string",
                "description": "Path to vulnerability fixes JSON file (required)"
            },
            "code_base_path": {
                "type": "string",
                "description": "Base path for code files (required)"
            },
            "backup_dir": {
                "type": "string",
                "description": "Directory for backups (default: auto-generated)"
            },
            "interactive": {
                "type": "boolean",
                "description": "Whether to ask for confirmation (default: false)"
            },
            "log_level": {
                "type": "string",
                "description": "Logging level (DEBUG, INFO, WARNING, ERROR)"
            }
        }

    def execute(self, fixes_report: str, code_base_path: str, backup_dir: str = None,
                interactive: bool = False, log_level: str = "INFO") -> Dict[str, Any]:
        """Execute code injection pipeline"""
        logger = logging.getLogger(f"tool.{self.name}")
        logger.info(f"Injecting fixes from: {fixes_report}")
        print("Активирован инструмент: code_injector")
        
        try:
            # Run code injection
            injection_result = run_code_injector(
                fixes_report=fixes_report,
                code_base_path=code_base_path,
                backup_dir=backup_dir,
                interactive=interactive,
                show_summary=False,
                log_level=log_level
            )
            
            if injection_result["success"]:
                logger.info("Code injection completed successfully")
                
                return {
                    "success": True,
                    "pipeline_step": "code_injection",
                    "data": injection_result["data"],
                    "summary": {
                        "fixes_input": fixes_report,
                        "code_base_path": code_base_path,
                        "backup_directory": injection_result["data"]["backup_dir"],
                        "total_fixes": injection_result["data"]["total_fixes"],
                        "applied": injection_result["data"]["applied"],
                        "skipped": injection_result["data"]["skipped"],
                        "failed": injection_result["data"]["failed"],
                        "success_rate": injection_result["data"]["success_rate"],
                        "backup_created": injection_result["data"]["backup_created"]
                    }
                }
            else:
                logger.error(f"Code injection failed: {injection_result['error']}")
                return {
                    "success": False,
                    "error": injection_result["error"],
                    "pipeline_step": "code_injection"
                }
                
        except Exception as e:
            logger.error(f"Code injection pipeline failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "pipeline_step": "code_injection"
            }


class SASTFullPipelineTool(BaseTool):
    """
    Tool 5: Complete SAST Pipeline
    Runs all 8 SAST modules in sequence for end-to-end vulnerability analysis and remediation
    """

    @property
    def name(self) -> str:
        return "sast_full_pipeline"

    @property
    def description(self) -> str:
        return "Execute complete SAST pipeline end-to-end: automated vulnerability discovery, triage, fix generation, and remediation in one command."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "code_base_path": {
                "type": "string",
                "description": "Path to code base to analyze (required)"
            },
            "reports_path": {
                "type": "string",
                "description": "Directory for all reports (default: ./sast_reports)"
            },
            "semgrep_config": {
                "type": "string",
                "description": "Semgrep configuration (default: auto-detect project rules)"
            },
            "triage_model": {
                "type": "string",
                "description": "LLM model for triage (default: gigachat-max)"
            },
            "fix_model": {
                "type": "string",
                "description": "LLM model for fix generation (default: gigachat-max)"
            },
            "max_vulnerabilities": {
                "type": "integer",
                "description": "Limit number of fixes for testing (default: None - no limit)"
            },
            "context_lines": {
                "type": "integer",
                "description": "Context lines around vulnerable code (default: 5)"
            },
            "skip_injection": {
                "type": "boolean",
                "description": "Skip code injection stage for safety (default: false)"
            },
            "interactive_injection": {
                "type": "boolean",
                "description": "Ask for confirmation before applying fixes (default: false)"
            },
            "log_level": {
                "type": "string",
                "description": "Logging level (DEBUG, INFO, WARNING, ERROR)"
            }
        }

    def execute(self, code_base_path: str, reports_path: str = None,
                semgrep_config: str = None, triage_model: str = "gigachat-max",
                fix_model: str = "gigachat-max", max_vulnerabilities: int = None,
                context_lines: int = 5, skip_injection: bool = False,
                interactive_injection: bool = False, log_level: str = "INFO") -> Dict[str, Any]:
        """Execute complete SAST pipeline"""
        logger = logging.getLogger(f"tool.{self.name}")
        logger.info(f"Running full SAST pipeline on: {code_base_path}")
        print("Активирован инструмент: full_pipeline")
        
        # Auto-create reports directory if not specified
        if reports_path is None:
            from pathlib import Path
            
            # Create reports directory relative to code base
            code_base = Path(code_base_path).resolve()
            reports_path = str(code_base.parent / "reports" / f"sast_analysis_{code_base.name}")
            logger.info(f"Auto-created reports directory: {reports_path}")
        
        # Ensure reports directory exists
        os.makedirs(reports_path, exist_ok=True)
        logger.info(f"Reports will be saved to: {reports_path}")
        
        try:
            # Import pipeline_run from full_sast_pipeline
            try:
                from full_sast_pipeline import pipeline_run
            except ImportError:
                try:
                    from SAST.full_sast_pipeline import pipeline_run
                except ImportError as e:
                    logger.error(f"Could not import pipeline_run: {e}")
                    return {
                        "success": False,
                        "error": "Failed to import full_sast_pipeline module",
                        "pipeline_step": "initialization"
                    }
            
            # Run the full pipeline
            result = pipeline_run(
                code_base_path=code_base_path,
                reports_path=reports_path,
                semgrep_config=semgrep_config,
                triage_model=triage_model,
                fix_model=fix_model,
                max_vulnerabilities=max_vulnerabilities,
                context_lines=context_lines,
                skip_injection=skip_injection,
                interactive_injection=interactive_injection,
                log_level=log_level
            )
            print("Пайплайн завершен")
            if result["success"]:
                summary = result["data"]["summary"]
                logger.info(f"Pipeline completed: {summary.get('successful_stages', 'unknown')}/{summary.get('total_stages', 'unknown')} stages successful")
                
                # Debug: log the actual summary structure
                logger.debug(f"Full pipeline summary keys: {list(summary.keys())}")
                
                return {
                    "success": True,
                    "pipeline_step": "full_pipeline",
                    "data": {
                        "overall_success": summary.get("overall_success", True),
                        "successful_stages": summary.get("successful_stages", 0),
                        "total_stages": summary.get("total_stages", 0),
                        "duration_seconds": summary.get("duration_seconds", 0),
                        "reports_directory": summary.get("reports_directory") or summary.get("sast_reports") or reports_path,
                        "stage_summary": summary.get("stage_summary", {})
                    },
                    "summary": {
                        "reports_directory": summary.get("reports_directory") or summary.get("sast_reports") or reports_path,
                        "pipeline_status": f"{summary.get('successful_stages', 0)}/{summary.get('total_stages', 0)} stages completed",
                        "overall_success": summary.get("overall_success", True),
                        "duration": f"{summary.get('duration_seconds', 0):.1f}s"
                    }
                }
            else:
                logger.error(f"Pipeline failed: {result['error']}")
                return {
                    "success": False,
                    "error": result["error"],
                    "pipeline_step": "full_pipeline"
                }
                
        except Exception as e:
            logger.error(f"Full pipeline execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "pipeline_step": "full_pipeline"
            }
#!/usr/bin/env python3
"""
Code Injector - Applies LLM-generated fixes to original source files
with both automatic and interactive modes.
"""

import json
import logging
import os
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Setup logging
logger = logging.getLogger(__name__)


class CodeInjector:
    """
    Applies LLM-generated vulnerability fixes to original source files with backup and interactive modes.
    
    This class takes vulnerability fixes (from VulnerabilityFixer) and injects them into source files.
    It creates backups, resolves file paths, cleans LLM responses, and provides both interactive and
    automatic modes for applying fixes. The fixes are applied by commenting out vulnerable code
    and adding the fixed version alongside.
    
    Attributes:
        fixes_report_path (str): Path to the vulnerability fixes JSON file
        code_base_path (str): Base path for resolving relative file paths
        backup_dir (str): Directory path for storing file backups
        fixes_data (Dict[str, Any]): Loaded fixes report data
        fixes (List[Dict[str, Any]]): List of fix objects to apply
        stats (Dict[str, Any]): Statistics tracking applied/skipped/failed fixes
        
    Example:
        injector = CodeInjector("fixes.json", "/code", "/backup")
        stats = injector.apply_all_fixes(interactive=False)
        print(f"Applied {stats['applied']} fixes")
    """
    
    def __init__(self, 
                 fixes_report_path: str,
                 code_base_path: str = "",
                 backup_dir: Optional[str] = None) -> None:
        """
        Initialize Code Injector
        
        Args:
            fixes_report_path: Path to vulnerability fixes JSON
            code_base_path: Base path for code files
            backup_dir: Directory for backups (defaults to {code_base_path}_backup)
        """
        self.fixes_report_path = fixes_report_path
        self.code_base_path = code_base_path
        
        # Set default backup directory
        if backup_dir is None:
            if code_base_path:
                self.backup_dir = f"{code_base_path.rstrip('/')}_backup"
            else:
                self.backup_dir = "code_backup"
        else:
            self.backup_dir = backup_dir
        
        # Load fixes report
        self.fixes_data = self._load_json(fixes_report_path)
        self.fixes = self.fixes_data.get("fixes", [])
        
        # Statistics
        self.stats = {
            "total_fixes": 0,
            "applied": 0,
            "skipped": 0,
            "failed": 0,
            "backup_created": False
        }
    
    def _load_json(self, file_path: str) -> Dict[str, Any]:
        """Load JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"Loaded: {file_path}")
            return data
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {file_path}: {e}")
            raise
    
    def _resolve_file_path(self, file_path: str) -> str:
        """Resolve file path from vulnerability report to actual filesystem path."""
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
        
        return full_path
    
    def _parse_location(self, location: Dict[str, int]) -> Tuple[int, int]:
        """
        Parse location dict like {'start_line': 416, 'end_line': 429}
        
        Returns:
            Tuple of (start_line, end_line)
        """
        if isinstance(location, dict):
            start_line = location.get("start_line", 0)
            end_line = location.get("end_line", 0)
        else:
            # Fallback for old string format
            if "-" in str(location):
                start_line, end_line = str(location).split("-")
                try:
                    start_line = int(start_line)
                    end_line = int(end_line)
                except ValueError:
                    start_line = end_line = 0
            else:
                try:
                    start_line = end_line = int(location)
                except ValueError:
                    start_line = end_line = 0
        
        return start_line, end_line
    
    def _get_fix_start_line(self, fix: Dict[str, Any]) -> int:
        """
        Extract start line number from a fix for sorting purposes.
        
        Args:
            fix: Fix object from vulnerability_fixes.json
            
        Returns:
            Start line number (0 if parsing fails)
        """
        vulnerability_info = fix.get("vulnerability_info", {})
        location = vulnerability_info.get("location", "")
        start_line, _ = self._parse_location(location)
        return start_line
    
    def _clean_llm_response(self, llm_response: str) -> str:
        """
        Clean LLM response by removing line number artifacts only.
        Keep LLM markers intact.
        
        Args:
            llm_response: Raw LLM response string
            
        Returns:
            Cleaned code string
        """
        import re
        
        # Split into lines for cleaning
        lines = llm_response.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Remove line numbers and arrows like "3 >>> " or "217 >>> "
            # But preserve the indentation that comes after the arrows
            # Pattern matches: optional whitespace + number + spaces + >>> + optional space
            # The content after >>> (including any indentation) is preserved
            if '>>>' in line and re.match(r'^\s*\d+\s*>>>', line):
                # Find where the actual content starts after the arrow
                match = re.match(r'^(\s*\d+\s*>>>)(.*)', line)
                if match:
                    # Keep only the content part (which includes any indentation)
                    cleaned_line = match.group(2)
                else:
                    cleaned_line = line
            else:
                cleaned_line = line
            cleaned_lines.append(cleaned_line)
        
        # Join back and return
        return '\n'.join(cleaned_lines)
    
    def _create_backup(self, file_path: str) -> bool:
        """Create backup of file before modification."""
        try:
            # Create backup directory if it doesn't exist
            os.makedirs(self.backup_dir, exist_ok=True)
            
            # Calculate relative path for backup structure
            if self.code_base_path and file_path.startswith(self.code_base_path):
                rel_path = os.path.relpath(file_path, self.code_base_path)
            else:
                rel_path = os.path.basename(file_path)
            
            backup_path = os.path.join(self.backup_dir, rel_path)
            
            # Create subdirectories if needed
            backup_parent = os.path.dirname(backup_path)
            if backup_parent:
                os.makedirs(backup_parent, exist_ok=True)
            
            # Copy file to backup
            shutil.copy2(file_path, backup_path)
            logger.info(f"Backup created: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create backup for {file_path}: {e}")
            return False
    
    def _read_file_lines(self, file_path: str) -> List[str]:
        """Read file and return lines."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            return lines
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return []
    
    def _write_file_lines(self, file_path: str, lines: List[str]) -> bool:
        """Write lines to file."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            logger.info(f"File updated: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error writing file {file_path}: {e}")
            return False
    
    def _apply_fix_to_lines(self, 
                           lines: List[str], 
                           start_line: int, 
                           end_line: int, 
                           fixed_code: str,
                           cwe_info: str = "") -> List[str]:
        """
        Apply fix to specific lines in file content by commenting old code and adding fixed code.
        
        Args:
            lines: Original file lines
            start_line: Start line number (1-indexed)
            end_line: End line number (1-indexed)
            fixed_code: LLM-generated fixed code
            cwe_info: CWE information for comment
            
        Returns:
            Modified lines
        """
        # Convert to 0-indexed
        start_idx = start_line - 1
        end_idx = end_line
        
        # Clean the fixed code by removing LLM markers and line number artifacts
        clean_fixed_code = self._clean_llm_response(fixed_code)
        
        # Split fixed code into lines - keep empty lines
        fixed_lines = clean_fixed_code.split('\n')
        
        # Don't add newlines yet - we'll handle that when appending
        
        # Get indentation from the first original line
        original_indent = ""
        if start_idx < len(lines) and lines[start_idx].strip():
            original_indent = lines[start_idx][:len(lines[start_idx]) - len(lines[start_idx].lstrip())]
        
        
        # Create the new lines with comments
        new_lines_section = []
        
        # Add CWE comment above
        if cwe_info:
            new_lines_section.append(f"{original_indent}# VULNERABILITY FOUND: {cwe_info}\n")
        
        # Comment out original vulnerable lines
        for i in range(start_idx, min(end_idx, len(lines))):
            original_line = lines[i]
            if original_line.strip():  # Only comment non-empty lines
                # Get the actual indentation of this line
                line_indent = original_line[:len(original_line) - len(original_line.lstrip())]
                # Comment it out while preserving its indentation
                commented_line = line_indent + "# " + original_line.lstrip()
                if not commented_line.endswith('\n'):
                    commented_line += '\n'
                new_lines_section.append(commented_line)
        
        # Add fixed code - preserve all lines including empty ones
        for fixed_line in fixed_lines:
            # Add newline if not present
            if not fixed_line.endswith('\n'):
                fixed_line += '\n'
            new_lines_section.append(fixed_line)
        
        # Replace the vulnerable lines with commented + fixed code
        new_lines = lines[:start_idx] + new_lines_section + lines[end_idx:]
        
        return new_lines
    
    def _show_diff_preview(self, 
                          original_lines: List[str], 
                          new_lines: List[str], 
                          start_line: int, 
                          end_line: int,
                          context_lines: int = 3) -> None:
        """Show a diff preview of the changes."""
        logger.info("CHANGE PREVIEW")
        # Header already logged above
        # Separator already logged above
        
        # Show original vulnerable code with context
        start_idx = max(0, start_line - 1 - context_lines)
        end_idx = min(len(original_lines), end_line + context_lines)
        
        logger.info("ORIGINAL CODE:")
        for i in range(start_idx, end_idx):
            line_num = i + 1
            line_content = original_lines[i].rstrip()
            if start_line <= line_num <= end_line:
                logger.debug(f"{line_num:4d} >>> {line_content}")
            else:
                logger.debug(f"{line_num:4d}     {line_content}")
        
        # Show new code with same context range
        logger.info("FIXED CODE:")
        # Calculate how many lines the fix takes
        original_line_count = end_line - start_line + 1
        new_line_count = len(new_lines) - len(original_lines) + original_line_count
        
        # Show context before
        for i in range(start_idx, start_line - 1):
            line_num = i + 1
            line_content = original_lines[i].rstrip()
            logger.debug(f"{line_num:4d}     {line_content}")
        
        # Show fixed lines
        fixed_start_idx = start_line - 1
        for i in range(new_line_count):
            line_num = start_line + i
            if fixed_start_idx + i < len(new_lines):
                line_content = new_lines[fixed_start_idx + i].rstrip()
                logger.debug(f"{line_num:4d} +++ {line_content}")
        
        # Show context after (adjust for line count difference)
        line_diff = len(new_lines) - len(original_lines)
        for i in range(end_line, min(len(original_lines), end_line + context_lines)):
            adjusted_line_num = i + 1 + line_diff
            if i < len(original_lines):
                line_content = original_lines[i].rstrip()
                logger.debug(f"{adjusted_line_num:4d}     {line_content}")
    
    def _get_user_confirmation(self, vulnerability_info: Dict[str, Any]) -> str:
        """Get user confirmation for applying fix (similar to Claude's prompt)."""
        logger.info(f"Vulnerability: {vulnerability_info.get('type', 'Unknown')}")
        logger.info(f"File: {vulnerability_info.get('file', 'Unknown')}")
        logger.info(f"Location: Lines {vulnerability_info.get('location', 'Unknown')}")
        logger.info(f"Severity: {vulnerability_info.get('severity', 'Unknown')}")
        logger.info(f"CWE: {vulnerability_info.get('cwe', 'Unknown')}")
        
        while True:
            choice = input("\nApply this fix? [y]es/[n]o/[s]kip all remaining/[q]uit: ").lower().strip()
            if choice in ['y', 'yes']:
                return 'apply'
            elif choice in ['n', 'no']:
                return 'skip'
            elif choice in ['s', 'skip']:
                return 'skip_all'
            elif choice in ['q', 'quit']:
                return 'quit'
            else:
                logger.warning("Please enter 'y', 'n', 's', or 'q'")
    
    def apply_single_fix(self, 
                        fix: Dict[str, Any], 
                        interactive: bool = True,
                        force_skip_all: bool = False) -> str:
        """
        Apply a single fix to the source file.
        
        Args:
            fix: Fix object from vulnerability_fixes.json
            interactive: Whether to ask for confirmation
            force_skip_all: Skip without asking (for skip_all mode)
            
        Returns:
            'applied', 'skipped', 'failed', 'quit'
        """
        vulnerability_info = fix.get("vulnerability_info", {})
        fixed_code = fix.get("llm_response", "")
        
        if not fixed_code or not fixed_code.strip():
            logger.warning(f"No fix available for: {vulnerability_info.get('type', 'Unknown')}")
            return 'skipped'
        
        # Resolve file path
        file_path = self._resolve_file_path(vulnerability_info.get("file", ""))
        location = vulnerability_info.get("location", "")
        
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return 'failed'
        
        # Parse location
        start_line, end_line = self._parse_location(location)
        if start_line == 0 or end_line == 0:
            logger.error(f"Invalid location: {location}")
            return 'failed'
        
        # Read original file
        original_lines = self._read_file_lines(file_path)
        if not original_lines:
            return 'failed'
        
        # Get CWE info for comment
        cwe_info = vulnerability_info.get("cwe", "Unknown CWE")
        
        # Apply fix
        try:
            new_lines = self._apply_fix_to_lines(original_lines, start_line, end_line, fixed_code, cwe_info)
        except Exception as e:
            logger.error(f"Failed to apply fix: {e}")
            return 'failed'
        
        # Show preview and get confirmation if interactive
        if interactive and not force_skip_all:
            self._show_diff_preview(original_lines, new_lines, start_line, end_line)
            
            user_choice = self._get_user_confirmation(vulnerability_info)
            if user_choice == 'skip':
                return 'skipped'
            elif user_choice == 'skip_all':
                return 'skip_all'
            elif user_choice == 'quit':
                return 'quit'
        elif force_skip_all:
            return 'skipped'
        
        # Create backup for this file if not already backed up
        if not hasattr(self, '_backed_up_files'):
            self._backed_up_files = set()
        
        if file_path not in self._backed_up_files:
            backup_success = self._create_backup(file_path)
            if backup_success:
                self._backed_up_files.add(file_path)
                self.stats["backup_created"] = True
        
        # Apply the fix
        if self._write_file_lines(file_path, new_lines):
            logger.info(f"Applied fix to {file_path} (lines {start_line}-{end_line})")
            return 'applied'
        else:
            return 'failed'
    
    def apply_all_fixes(self, interactive: bool = True) -> Dict[str, Any]:
        """
        Apply all fixes with optional interactive confirmation.
        
        Args:
            interactive: Whether to ask for confirmation for each fix
            
        Returns:
            Statistics dictionary
        """
        logger.info(f"Processing {len(self.fixes)} vulnerability fixes...")
        logger.info(f"Code base: {self.code_base_path}")
        logger.info(f"Backup directory: {self.backup_dir}")
        logger.info(f"Mode: {'Interactive' if interactive else 'Automatic'}")
        
        if interactive:
            logger.info("Starting interactive mode. You'll be asked to confirm each fix.")
        else:
            logger.info("Starting automatic mode. All fixes will be applied without confirmation.")
        
        self.stats["total_fixes"] = len(self.fixes)
        skip_all_remaining = False
        
        # Group fixes by file to handle line number drift within each file
        fixes_by_file = {}
        for fix in self.fixes:
            vulnerability_info = fix.get("vulnerability_info", {})
            file_path = self._resolve_file_path(vulnerability_info.get("file", ""))
            if file_path not in fixes_by_file:
                fixes_by_file[file_path] = []
            fixes_by_file[file_path].append(fix)
        
        # Sort fixes within each file by line number in REVERSE order (bottom to top)
        # This prevents line number drift issues
        for file_path in fixes_by_file:
            fixes_by_file[file_path].sort(key=lambda f: self._get_fix_start_line(f), reverse=True)
            logger.info(f"Sorted {len(fixes_by_file[file_path])} fixes for {file_path} in reverse line order")
        
        # Process fixes file by file
        fix_counter = 0
        for file_path, file_fixes in fixes_by_file.items():
            logger.info(f"Processing {len(file_fixes)} fixes for file: {file_path}")
            
            for fix in file_fixes:
                fix_counter += 1
                vulnerability_info = fix.get("vulnerability_info", {})
                logger.info(f"[{fix_counter}/{len(self.fixes)}] Processing: {vulnerability_info.get('type', 'Unknown')[:50]}...")
                
                # Apply fix
                result = self.apply_single_fix(fix, interactive, skip_all_remaining)
                
                # Update statistics
                if result == 'applied':
                    self.stats["applied"] += 1
                elif result == 'skipped':
                    self.stats["skipped"] += 1
                elif result == 'failed':
                    self.stats["failed"] += 1
                elif result == 'skip_all':
                    self.stats["skipped"] += 1
                    skip_all_remaining = True
                elif result == 'quit':
                    logger.info(f"Stopped at user request")
                    break
            
            if skip_all_remaining or result == 'quit':
                break
        
        # Generate summary
        self._print_summary()
        return self.stats
    
    def _print_summary(self) -> None:
        """Print execution summary."""
        logger.info(f"CODE INJECTION SUMMARY")
        logger.info(f"Total fixes processed: {self.stats['total_fixes']}")
        logger.info(f"Successfully applied: {self.stats['applied']}")
        logger.info(f"Skipped: {self.stats['skipped']}")
        logger.info(f"Failed: {self.stats['failed']}")
        
        if self.stats['total_fixes'] > 0:
            success_rate = (self.stats['applied'] / self.stats['total_fixes']) * 100
            logger.info(f"Success rate: {success_rate:.1f}%")
        
        if self.stats["backup_created"]:
            logger.info(f"Backups created in: {self.backup_dir}")
        # Summary complete


def run_code_injector(**kwargs) -> Dict[str, Any]:
    """
    Agent-friendly helper function for injecting vulnerability fixes into source files.
    
    Args:
        fixes_report (str): Path to vulnerability fixes JSON file (required)
        code_base_path (str, optional): Base path for code files (default: '')
        backup_dir (str, optional): Directory for backups (default: None for auto-generated)
        interactive (bool, optional): Whether to ask for confirmation (default: False)
        show_summary (bool, optional): Whether to display injection summary (default: False)
        log_level (str, optional): Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR')
        
    Returns:
        Dict with standardized format:
        {
            "success": bool,
            "data": {
                "stats": dict with injection statistics,
                "total_fixes": int,
                "applied": int,
                "skipped": int,
                "failed": int,
                "success_rate": float,
                "backup_created": bool,
                "backup_dir": str,
                "code_base_path": str
            },
            "error": str or None,
            "metadata": {
                "fixes_report": str,
                "interactive": bool,
                "show_summary": bool
            }
        }
    """
    # Set logging level if provided
    if 'log_level' in kwargs:
        logger.setLevel(getattr(logging, kwargs['log_level'].upper(), logging.INFO))
    
    # Validate required parameters
    if 'fixes_report' not in kwargs:
        return {
            "success": False,
            "data": None,
            "error": "fixes_report is required",
            "metadata": {}
        }
    
    # Extract parameters with defaults
    fixes_report = kwargs['fixes_report']
    code_base_path = kwargs.get('code_base_path', '')
    backup_dir = kwargs.get('backup_dir')
    interactive = kwargs.get('interactive', False)
    show_summary = kwargs.get('show_summary', False)
    
    try:
        # Initialize injector
        injector = CodeInjector(fixes_report, code_base_path, backup_dir)
        
        # Apply fixes
        stats = injector.apply_all_fixes(interactive)
        
        # Calculate success rate
        success_rate = 0.0
        if stats['total_fixes'] > 0:
            success_rate = (stats['applied'] / stats['total_fixes']) * 100
        
        # Display summary if requested
        if show_summary:
            logger.info(f"CODE INJECTION SUMMARY")
            logger.info(f"Total fixes processed: {stats['total_fixes']}")
            logger.info(f"Successfully applied: {stats['applied']}")
            logger.info(f"Skipped: {stats['skipped']}")
            logger.info(f"Failed: {stats['failed']}")
            logger.info(f"Success rate: {success_rate:.1f}%")
            if stats["backup_created"]:
                logger.info(f"Backups created in: {injector.backup_dir}")
        
        return {
            "success": True,
            "data": {
                "stats": stats,
                "total_fixes": stats['total_fixes'],
                "applied": stats['applied'],
                "skipped": stats['skipped'],
                "failed": stats['failed'],
                "success_rate": success_rate,
                "backup_created": stats['backup_created'],
                "backup_dir": injector.backup_dir,
                "code_base_path": code_base_path
            },
            "error": None,
            "metadata": {
                "fixes_report": str(fixes_report),
                "interactive": interactive,
                "show_summary": show_summary
            }
        }
        
    except Exception as e:
        logger.exception("Exception occurred during code injection")
        return {
            "success": False,
            "data": None,
            "error": str(e),
            "metadata": {
                "fixes_report": str(fixes_report),
                "interactive": interactive,
                "show_summary": show_summary
            }
        }


def inject_fixes(
    fixes_report: str,
    code_base_path: str = "",
    backup_dir: Optional[str] = None,
    interactive: bool = True,
    show_summary: bool = True
) -> Dict[str, Any]:
    """
    Inject vulnerability fixes into source files.
    
    Args:
        fixes_report: Path to vulnerability fixes JSON
        code_base_path: Base path for code files
        backup_dir: Directory for backups
        interactive: Whether to ask for confirmation
        show_summary: Whether to show summary
        
    Returns:
        Statistics dictionary
    """
    injector = CodeInjector(fixes_report, code_base_path, backup_dir)
    stats = injector.apply_all_fixes(interactive)
    
    if show_summary:
        logger.info(f"Code injection completed!")
        
    return stats


def main():
    """Example usage of the agent-friendly helper function."""
    # Example usage of the helper function
    dir_path = "/Users/izelikson/python/CryptoSlon/SAST/reports"
    
    result = run_code_injector(
        fixes_report=f"{dir_path}/vulnerability_fixes.json",
        code_base_path="/Users/izelikson/python/CryptoSlon/SAST/code_for_sast/taskstate_29/",
        backup_dir=None,  # Will use default: {code_base_path}_backup
        interactive=False,  # Set to False for automatic mode
        show_summary=False,
        log_level="INFO"
    )
    
    if result["success"]:
        print(f"\n✅ Code injection successful!")
        data = result["data"]
        print(f"Total fixes: {data['total_fixes']}")
        print(f"Applied: {data['applied']}")
        print(f"Skipped: {data['skipped']}")
        print(f"Failed: {data['failed']}")
        print(f"Success rate: {data['success_rate']:.1f}%")
        print(f"Code base path: {data['code_base_path']}")
        print(f"Backup directory: {data['backup_dir']}")
        print(f"Backup created: {data['backup_created']}")
    else:
        print(f"\n❌ Code injection failed: {result['error']}")
    
    return result


if __name__ == "__main__":
    # Direct Python usage
    result = main()

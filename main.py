#!/usr/bin/env python3
"""
CryptoSlon - AI Security Agent Platform
Main entry point for launching SAST security agent
"""

import sys
import logging
from pathlib import Path
import os

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def validate_directory(path_str: str) -> bool:
    """Validate that the provided path is an absolute path to an existing directory"""
    try:
        path = Path(path_str)
        if not path.is_absolute():
            print(f"Error: Path must be absolute. Got: {path_str}")
            return False
        if not path.exists():
            print(f"Error: Directory does not exist: {path_str}")
            return False
        if not path.is_dir():
            print(f"Error: Path is not a directory: {path_str}")
            return False
        return True
    except Exception as e:
        print(f"Error validating path: {e}")
        return False


def get_valid_directory() -> str:
    """Prompt user for a valid absolute directory path"""
    while True:
        path = input("Enter absolute path to directory: ").strip()
        if validate_directory(path):
            return path
        print("Please try again.\n")


def run_automated_mode(command: str, model: str = "gigachat-pro"):
    """Run SAST agent in automated mode with specified command"""
    from agents.sast_agent import automated_launch
    
    print("\nStarting SAST Agent in automated mode...")
    print(f"Command: {command}")
    print(f"Model: {model}")
    print("=" * 60)
    
    result = automated_launch(
        command=command,
        llm_provider=model,
        log_level="INFO"
    )
    
    if result["success"]:
        print("\n" + "=" * 60)
        print("SAST Agent completed successfully")
        print("Full response saved to: sast_report.txt")
    else:
        print("\n" + "=" * 60)
        print("SAST Agent failed")
        print(f"Error: {result.get('response', 'Unknown error')}")


def run_interactive_mode():
    """Run SAST agent in interactive mode"""
    from agents.sast_agent import interactive_launch
    
    print("\nStarting SAST Agent in interactive mode...")
    print("Model: gigachat-pro")
    print("=" * 60)
    interactive_launch()


def display_menu():
    """Display main menu options"""
    print("\n" + "=" * 60)
    print("CryptoSlon - SAST Security Agent")
    print("=" * 60)
    print("\nSelect an option:")
    print("1. Analyze code for vulnerabilities (automated)")
    print("2. Run full SAST pipeline (automated)")
    print("3. Interactive mode")
    print("4. Exit")
    print()


def main(log_level="INFO"):
    """Main entry point with menu-driven interface
    
    Args:
        log_level: Logging level as string. Options: "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
                  Can also accept lowercase versions like "info", "warning", etc.
    """
    
    # Convert log_level string to logging constant
    log_level = log_level.upper()
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if log_level not in valid_levels:
        print(f"Invalid log level: {log_level}. Using INFO instead.")
        log_level = "INFO"
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Suppress noisy httpx logs (keep them at WARNING minimum)
    httpx_level = max(logging.WARNING, getattr(logging, log_level))
    logging.getLogger("httpx").setLevel(httpx_level)
    
    print("\nWelcome to CryptoSlon Security Platform!")
    
    while True:
        display_menu()
        
        try:
            choice = input("Enter your choice (1-4): ").strip()
            
            if choice == "1":
                # Option 1: Analyze code for vulnerabilities
                print("\nOption 1: Analyze code for vulnerabilities")
                print("-" * 40)
                directory = get_valid_directory()
                command = f"perform semgrep analysis in {directory}"
                run_automated_mode(command, "gigachat-pro")
                
            elif choice == "2":
                # Option 2: Run full SAST pipeline
                print("\nOption 2: Run full SAST pipeline")
                print("-" * 40)
                directory = get_valid_directory()
                command = f"run full sast pipeline for {directory}"
                run_automated_mode(command, "gigachat-pro")
                
            elif choice == "3":
                # Option 3: Interactive mode
                print("\nOption 3: Interactive mode")
                print("-" * 40)
                run_interactive_mode()
                
            elif choice == "4":
                # Exit
                print("\nThank you for using CryptoSlon. Goodbye!")
                sys.exit(0)
                
            else:
                print("\nInvalid choice. Please select 1-4.")
                
        except KeyboardInterrupt:
            print("\n\nOperation cancelled. Returning to menu...")
        except EOFError:
            print("\n\nExiting...")
            sys.exit(0)
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            print(f"\nError: {e}")
            print("Returning to menu...")


if __name__ == "__main__":
    import argparse
    
    # Parse command line arguments for log level
    parser = argparse.ArgumentParser(description='CryptoSlon SAST Security Agent')
    parser.add_argument(
        '--log-level', '-l',
        type=str,
        default='WARNING',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Set the logging level (default: INFO)'
    )
    
    args = parser.parse_args()
    
    try:
        main(log_level=args.log_level)
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Critical error: {e}")
        print(f"\nCritical error: {e}")
        sys.exit(1)

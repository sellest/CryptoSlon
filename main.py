#!/usr/bin/env python3
"""
CryptoSlon - AI Security Agent Platform
Main entry point for launching various security agents
"""

import argparse
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def launch_sast_agent(args):
    """Launch SAST Security Agent"""
    from agents.sast_agent import interactive_launch, automated_launch
    
    if args.mode == 'interactive':
        print("Starting SAST Agent in interactive mode...")
        print("=" * 60)
        interactive_launch()
    else:  # automated mode
        if not args.command:
            print("Error: --command is required for automated mode")
            sys.exit(1)
        
        print(f"Starting SAST Agent in automated mode...")
        print(f"Command: {args.command}")
        print(f"Model: {args.model}")
        print("=" * 60)
        
        result = automated_launch(
            command=args.command,
            llm_provider=args.model,
            log_level=args.log_level
        )
        
        if result["success"]:
            print("\n" + "=" * 60)
            print("SAST Agent completed successfully")
            # print(f"Pipeline Status: {result.get('pipeline_status', 'N/A')}")
            print("Full response saved to: sast_report.txt")
        else:
            print("\n" + "=" * 60)
            print("SAST Agent failed")
            print(f"Error: {result.get('response', 'Unknown error')}")
            sys.exit(1)


def main():
    """Main entry point with CLI argument parsing"""
    parser = argparse.ArgumentParser(
        description='CryptoSlon - AI Security Agent Platform',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Create subparsers for different agents
    subparsers = parser.add_subparsers(
        title='agents',
        description='Available security agents',
        help='Choose an agent to launch',
        dest='agent'
    )
    
    # SAST Agent subparser
    sast_parser = subparsers.add_parser(
        'sast',
        help='Static Application Security Testing (SAST) Agent',
        description='Launch SAST agent for vulnerability analysis and remediation'
    )
    
    sast_parser.add_argument(
        'mode',
        choices=['interactive', 'automated'],
        help='Agent execution mode'
    )
    
    sast_parser.add_argument(
        '-c', '--command',
        type=str,
        help='Command to execute (required for automated mode). Example: "run full pipeline for /path/to/code"'
    )
    
    sast_parser.add_argument(
        '-m', '--model',
        type=str,
        default='gigachat-pro',
        choices=['gigachat-pro', 'gigachat-max', 'gpt-5', 'gpt-5-mini'],
        help='LLM model to use (default: gigachat-pro)'
    )
    
    sast_parser.add_argument(
        '-l', '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level (default: INFO)'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Show help if no agent specified
    if not args.agent:
        parser.print_help()
        sys.exit(0)
    
    # Route to appropriate agent launcher
    if args.agent == 'sast':
        launch_sast_agent(args)
    else:
        print(f"Unknown agent: {args.agent}")
        sys.exit(1)


if __name__ == "__main__":
    # Example usage:
    # python main.py sast interactive
    # python main.py sast automated -c "run full pipeline for /path/to/code"
    # python main.py sast automated -c "analyze /path/to/code" -m gigachat-pro -l DEBUG
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        print(f"\nError: {e}")
        sys.exit(1)

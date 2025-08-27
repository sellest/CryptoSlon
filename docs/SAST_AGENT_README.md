# SAST Agent - Complete Static Application Security Testing Pipeline

## Overview

The SAST Agent is a specialized AI agent that provides a complete Static Application Security Testing (SAST) pipeline. It combines multiple security analysis tools with LLM-powered reasoning to discover, analyze, prioritize, and automatically fix security vulnerabilities in source code.

## Architecture

### 4-Stage Pipeline

The SAST Agent orchestrates a comprehensive 4-stage security analysis pipeline:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Stage 1:      │    │   Stage 2:      │    │   Stage 3:      │    │   Stage 4:      │
│ SAST Analysis   │───▶│ Vulnerability   │───▶│ Fix Generation  │───▶│ Code Injection  │
│                 │    │ Triage          │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Stage Details

#### Stage 1: SAST Analysis (`sast_analysis`)
- **Tools**: Semgrep + Bandit security scanners
- **Process**: Runs both tools, merges SARIF reports, aggregates findings
- **Output**: Comprehensive vulnerability report with CWE mappings and severity distribution
- **File**: `aggregated_report.json`

#### Stage 2: Vulnerability Triage (`sast_triage`)
- **Tools**: LLM-powered analysis using configurable prompt templates
- **Process**: Prioritizes vulnerabilities, filters false positives, provides risk assessment
- **Output**: Triaged vulnerability analysis with business impact assessment
- **File**: `triage_analysis.json`

#### Stage 3: Fix Generation (`sast_fix_generation`)
- **Tools**: Code snippet extractor + LLM fix generator
- **Process**: Extracts vulnerable code with context, generates secure fixes using LLM
- **Output**: Detailed fixes with explanations and improved code
- **Files**: `vulnerability_snippets.json`, `vulnerability_fixes.json`

#### Stage 4: Code Injection (`sast_code_injection`)
- **Tools**: Safe code modification with backup
- **Process**: Applies fixes to source files, creates backups, preserves original code as comments
- **Output**: Modified source files with automatic backup
- **Backup**: `{code_base_path}_backup/`

## Installation & Setup

### Prerequisites

```bash
# Install required dependencies
pip install -r requirements.txt

# Ensure SAST tools are available
pip install semgrep bandit

# Set up API keys in .env file
OPENAI_API_KEY=your_openai_key
GIGACHAT_CREDENTIALS=your_gigachat_key
```

### File Structure

```
agents/
├── sast_agent.py              # Main SAST Agent class
├── tools/
│   └── sast_tools.py          # 4 SAST pipeline tools
├── test_sast_agent.py         # Test suite
└── SAST_AGENT_README.md       # This file

prompts/
└── sast_agent_instructions.json  # Agent system prompt

SAST/
├── semgrep_analyzer.py        # Semgrep integration
├── bandit_analyzer.py         # Bandit integration
├── report_merger.py           # SARIF report merger
├── report_aggregator.py       # Vulnerability aggregator
├── triage.py                  # LLM triage analysis
├── snippet_extractor.py       # Code snippet extraction
├── vulnerability_fixer.py     # LLM fix generation
└── code_injector.py          # Safe code modification
```

## Usage

### Quick Start

```python
from agents.sast_agent import create_sast_agent

# Create SAST agent
agent = create_sast_agent(llm_provider="gpt-4o-mini")

# Run complete pipeline
results = agent.analyze_code(
    target_path="/path/to/your/code",
    output_dir="./sast_results",
    full_pipeline=True,
    interactive_injection=False  # Set True for manual confirmation
)

print(f"Pipeline Status: {results['final_summary']}")
```

### Interactive Mode

```python
# Interactive conversation with agent
response = agent.process_request("Analyze my Python project for SQL injection vulnerabilities")
print(f"Agent: {response}")

# Check pipeline status
status = agent.get_pipeline_status()
print(f"Current State: {status['pipeline_state']}")
```

### Programmatic Pipeline Control

```python
# Run individual stages
from agents.tools.sast_tools import SASTAnalysisTool

tool = SASTAnalysisTool()
result = tool.execute(
    target_path="/path/to/code",
    output_dir="./output"
)

if result["success"]:
    print(f"Found {result['data']['aggregator']['total_findings']} vulnerabilities")
```

## Tool Reference

### 1. sast_analysis

Runs complete SAST analysis with Semgrep and Bandit.

**Parameters:**
- `target_path` (required): Path to code directory
- `output_dir`: Output directory for reports
- `semgrep_config`: Semgrep ruleset ("auto", "security", etc.)
- `log_level`: Logging verbosity

**Returns:**
```json
{
  "success": true,
  "steps_completed": ["semgrep", "bandit", "merger", "aggregator"],
  "data": {
    "semgrep": {"issue_count": 15, "output_file": "..."},
    "bandit": {"issue_count": 8, "output_file": "..."},
    "aggregator": {"total_findings": 20, "severity_distribution": {...}}
  },
  "summary": {
    "final_report": "./output/aggregated_report.json"
  }
}
```

### 2. sast_triage

LLM-powered vulnerability prioritization and analysis.

**Parameters:**
- `aggregated_report` (required): Path to aggregated report JSON
- `output_file`: Output file for triage results
- `model`: LLM model ("gpt-4o-mini", "gigachat-pro", etc.)
- `template`: Prompt template ("sast", "sast_v4", etc.)

**Returns:**
```json
{
  "success": true,
  "data": {
    "analysis_result": {...},
    "total_findings": 20,
    "model_used": "gpt-4o-mini",
    "is_json": true
  },
  "summary": {
    "response_format": "JSON"
  }
}
```

### 3. sast_fix_generation

Extracts vulnerable code and generates LLM fixes.

**Parameters:**
- `triage_analysis` (required): Path to triage analysis JSON
- `code_base_path` (required): Base path for source code
- `output_dir`: Output directory
- `model`: LLM model for fix generation
- `max_vulnerabilities`: Limit number of fixes (for testing)
- `context_lines`: Lines of context around vulnerable code

**Returns:**
```json
{
  "success": true,
  "data": {
    "snippets": {"total_snippets": 15},
    "fixes": {
      "total_fixes": 15,
      "successful_fixes": 12,
      "success_rate": 80.0
    }
  },
  "summary": {
    "snippets_file": "./output/vulnerability_snippets.json",
    "fixes_file": "./output/vulnerability_fixes.json"
  }
}
```

### 4. sast_code_injection

Applies generated fixes to source files with backup.

**Parameters:**
- `fixes_report` (required): Path to vulnerability fixes JSON
- `code_base_path` (required): Base path for source code
- `backup_dir`: Custom backup directory
- `interactive`: Whether to ask for confirmation

**Returns:**
```json
{
  "success": true,
  "data": {
    "total_fixes": 12,
    "applied": 10,
    "skipped": 1,
    "failed": 1,
    "success_rate": 83.3,
    "backup_created": true
  },
  "summary": {
    "backup_directory": "/path/to/code_backup"
  }
}
```

## Configuration

### LLM Models

Supported LLM providers:
- `gpt-4o-mini` (default) - Fast and cost-effective
- `gpt-4o` - Higher quality analysis
- `gigachat-pro` - Russian language support
- `claude-3-sonnet` - Alternative high-quality model

### Prompt Templates

Available templates in `prompts/`:
- `sast` - Standard SAST analysis template
- `sast_v4` - Enhanced analysis with business context
- `vulnerability_fix` - Fix generation template
- `vulnerability_fix_v6` - Advanced fix generation

### Output Formats

- **SARIF**: Standard format for security analysis results
- **JSON**: Structured vulnerability data
- **Markdown**: Human-readable reports (optional)

## Safety Features

### Backup System
- Automatic backup creation before code modification
- Preserves directory structure
- Timestamped backup directories

### Interactive Mode
- Manual confirmation for each fix
- Diff preview before application
- Skip/apply/quit options

### Code Preservation
- Original vulnerable code commented out
- CWE annotations added
- Fix explanations included

## Testing

```bash
# Run test suite
cd agents/
python test_sast_agent.py

# Interactive testing
python test_sast_agent.py
# Then choose 'y' for interactive demo
```

## Example Workflows

### Full Security Audit

```python
agent = create_sast_agent()

# Complete security pipeline
results = agent.analyze_code(
    target_path="/project/src",
    output_dir="/project/security_audit",
    full_pipeline=True,
    interactive_injection=True  # Review each fix
)

# Review results
for step in results['steps_completed']:
    print(f"✅ {step}: {results['outputs'][step]['summary']}")
```

### Vulnerability Discovery Only

```python
# Run analysis and triage only (no fixes)
results = agent.analyze_code(
    target_path="/project/src",
    full_pipeline=False  # Skip fix generation and injection
)

# Access triage results
triage = results['outputs']['triage']
print(f"Critical vulnerabilities: {triage['data']['total_findings']}")
```

### Custom Fix Generation

```python
# Use specific models and limits
agent.tool_manager.execute_tool("sast_fix_generation", {
    "triage_analysis": "./triage_analysis.json",
    "code_base_path": "/project/src",
    "model": "gpt-4o",  # Higher quality model
    "max_vulnerabilities": 5,  # Limit for focused fixes
    "context_lines": 15  # More context for complex fixes
})
```

## Troubleshooting

### Common Issues

1. **Tool not found**: Ensure semgrep/bandit are installed
   ```bash
   pip install semgrep bandit
   ```

2. **API key errors**: Check `.env` file configuration
   ```bash
   echo $OPENAI_API_KEY
   ```

3. **File path issues**: Use absolute paths for reliability
   ```python
   target_path = os.path.abspath("/project/src")
   ```

4. **Pipeline failures**: Check intermediate files exist
   ```bash
   ls -la ./output/
   ```

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

agent = create_sast_agent()
# Now see detailed execution logs
```

## Contributing

### Adding New SAST Tools

1. Create new tool in `agents/tools/sast_tools.py`
2. Inherit from `BaseTool` base class
3. Implement required methods: `name`, `description`, `parameters`, `execute`
4. Register tool in `SASTAgent.__init__()`

### Custom Prompt Templates

1. Create new template in `prompts/`
2. Follow existing JSON structure
3. Include tool usage examples
4. Test with agent

### Integration Testing

Create test cases in `test_sast_agent.py` for new functionality.

## License

Part of the CryptoSlon cybersecurity toolkit. See main project license.
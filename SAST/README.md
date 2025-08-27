# SAST Analysis with Semgrep

Simple vulnerability scanner for Python code using semgrep.

## Setup

Install semgrep:
```bash
pip install semgrep
```

Install bandit:
```bash
pip install bandit
```

## Usage

Run analysis on a directory:
```bash
python semgrep_analyzer.py /path/to/target/directory
```

Use custom rules:
```bash
python semgrep_analyzer.py /path/to/target --rules ./rules --output results.json
```

## Custom Rules

The `rules/python-security.yml` file contains custom security rules for:
- Hardcoded passwords/secrets
- SQL injection vulnerabilities  
- Command injection
- Insecure random number generation
- Use of eval()
- Debug mode in production
# -*- coding: utf-8 -*-
"""
Cybersecurity-focused tools for AI agents
"""

import re
import hashlib
import base64
import logging
from typing import Dict, Any, List
from agents.base_tool import BaseTool
import zxcvbn


class PasswordAnalyzerTool(BaseTool):
    """Tool for analyzing password strength and security"""

    @property
    def name(self) -> str:
        return "password_analyzer"

    @property
    def description(self) -> str:
        return "Анализ надежности пароля и рекоммендации по его улучшению"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "password": {
                "type": "string",
                "description": "Password to analyze (will not be logged)"
            }
        }

    def execute(self, password: str) -> Dict[str, Any]:
        """Analyze password strength"""
        logger = logging.getLogger(f"tool.{self.name}")
        logger.info(f"Password analyzer tool called with password length: {len(password)}")
        
        try:
            result = zxcvbn.zxcvbn(password)
            score_text = {
                0: "Очень слабый",
                1: "Слабый",
                2: "Средний",
                3: "Хороший",
                4: "Очень хороший"
            }

            suggestions = result["feedback"]["suggestions"]
            formatted_suggestions = "Нет конкретных советов"
            if suggestions:
                formatted_suggestions = "- " + "\n- ".join(suggestions)

            analysis = (
                f"Пароль: {password}\n"
                f"Оценка надёжности: {score_text.get(result['score'], 'Неизвестно')} (score={result['score']})\n"
                f"Время взлома online (без ограничений): {result['crack_times_display']['online_no_throttling_10_per_second']}\n"
                f"Время взлома offline (hash): {result['crack_times_display']['offline_fast_hashing_1e10_per_second']}\n"
                f"Советы по улучшению:\n{formatted_suggestions}"
            )
            return {
                "success": True,
                "analysis": analysis
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


class HashGeneratorTool(BaseTool):
    """Tool for generating secure hashes"""

    @property
    def name(self) -> str:
        return "hash_generator"

    @property
    def description(self) -> str:
        return "Generate secure hashes (SHA-256, MD5, etc.) for text or verify hash integrity"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "text": {
                "type": "string",
                "description": "Text to hash"
            },
            "algorithm": {
                "type": "string",
                "description": "Hash algorithm (sha256, sha1, md5)",
                "default": "sha256"
            }
        }

    def execute(self, text: str, algorithm: str = "sha256") -> Dict[str, Any]:
        """Generate hash for text"""
        logger = logging.getLogger(f"tool.{self.name}")
        logger.info(f"Hash generator tool called with algorithm: {algorithm}, text length: {len(text)}")
        
        try:
            # Encode text to bytes
            text_bytes = text.encode('utf-8')

            # Generate hash based on algorithm
            if algorithm.lower() == "sha256":
                hash_obj = hashlib.sha256(text_bytes)
            elif algorithm.lower() == "sha1":
                hash_obj = hashlib.sha1(text_bytes)
            elif algorithm.lower() == "md5":
                hash_obj = hashlib.md5(text_bytes)
            else:
                return {
                    "success": False,
                    "error": f"Unsupported algorithm: {algorithm}"
                }

            hex_hash = hash_obj.hexdigest()

            return {
                "success": True,
                "algorithm": algorithm.upper(),
                "hash": hex_hash,
                "length": len(hex_hash),
                "input_length": len(text)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


class VulnerabilityCheckerTool(BaseTool):
    """Tool for basic vulnerability pattern detection"""

    @property
    def name(self) -> str:
        return "vulnerability_checker"

    @property
    def description(self) -> str:
        return "Check code snippets for common security vulnerabilities and patterns"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "code": {
                "type": "string",
                "description": "Code snippet to analyze"
            },
            "language": {
                "type": "string",
                "description": "Programming language (python, javascript, sql, etc.)",
                "default": "python"
            }
        }

    def execute(self, code: str, language: str = "python") -> Dict[str, Any]:
        """Check code for vulnerability patterns"""
        logger = logging.getLogger(f"tool.{self.name}")
        logger.info(f"Vulnerability checker tool called for {language} code, length: {len(code)}")
        
        try:
            vulnerabilities = []

            # Common SQL injection patterns
            sql_patterns = [
                (r'SELECT.*\+.*\+', "Possible SQL injection via string concatenation"),
                (r'execute\s*\(.*\+', "Dynamic SQL execution with concatenation"),
                (r'query.*%.*%', "String formatting in SQL queries"),
                (r'cursor\.execute.*%', "Unsafe parameter substitution")
            ]

            # Python-specific patterns
            python_patterns = [
                (r'eval\s*\(', "Use of dangerous eval() function"),
                (r'exec\s*\(', "Use of dangerous exec() function"),
                (r'os\.system\s*\(', "Direct system command execution"),
                (r'subprocess.*shell=True', "Shell injection risk"),
                (r'pickle\.loads?\s*\(', "Unsafe deserialization"),
                (r'input\s*\(.*\)', "Direct user input usage")
            ]

            # JavaScript patterns  
            js_patterns = [
                (r'eval\s*\(', "Use of dangerous eval() function"),
                (r'innerHTML\s*=', "Possible XSS via innerHTML"),
                (r'document\.write\s*\(', "Dynamic content injection risk"),
                (r'setTimeout\s*\(\s*["\']', "String-based setTimeout"),
            ]

            # Select patterns based on language
            if language.lower() in ['python', 'py']:
                patterns = sql_patterns + python_patterns
            elif language.lower() in ['javascript', 'js', 'node']:
                patterns = sql_patterns + js_patterns
            elif language.lower() in ['sql']:
                patterns = sql_patterns
            else:
                patterns = sql_patterns  # Default to SQL patterns

            # Check for patterns
            for pattern, description in patterns:
                if re.search(pattern, code, re.IGNORECASE):
                    vulnerabilities.append({
                        "pattern": pattern,
                        "description": description,
                        "severity": "High" if "injection" in description.lower() else "Medium"
                    })

            # Security recommendations
            recommendations = []
            if vulnerabilities:
                recommendations.extend([
                    "Use parameterized queries for database operations",
                    "Validate and sanitize all user inputs",
                    "Use safe libraries and avoid dynamic code execution",
                    "Implement proper error handling"
                ])
            else:
                recommendations.append(
                    "No obvious vulnerability patterns detected, but consider comprehensive security testing")

            return {
                "success": True,
                "language": language,
                "vulnerabilities_found": len(vulnerabilities),
                "vulnerabilities": vulnerabilities,
                "recommendations": recommendations,
                "risk_level": "High" if any(v["severity"] == "High" for v in vulnerabilities) else "Low"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

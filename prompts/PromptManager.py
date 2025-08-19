"""
PromptManager - Manages prompt templates for agents and RAG pipeline
"""

import json
import os
from typing import Dict, Any, Optional
from string import Template

class PromptManager:
    """Manages prompt templates from JSON files"""
    
    def __init__(self, templates_dir: str = None):
        if templates_dir is None:
            templates_dir = os.path.join(os.path.dirname(__file__), "templates")
        self.templates_dir = templates_dir
        self._cache = {}
    
    def load_template(self, template_name: str) -> Dict[str, Any]:
        """Load template from JSON file"""
        if template_name in self._cache:
            return self._cache[template_name]
        
        template_path = os.path.join(self.templates_dir, f"{template_name}.json")
        
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template '{template_name}' not found at {template_path}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template_data = json.load(f)
        
        self._cache[template_name] = template_data
        return template_data
    
    def get_prompt(self, template_name: str, template_vars: Dict[str, Any] = None) -> str:
        """Get formatted prompt from template"""
        template_data = self.load_template(template_name)
        
        if 'system' not in template_data:
            raise ValueError(f"Template '{template_name}' missing 'system' key")
        
        prompt_template = template_data['system']
        
        if template_vars:
            # Use Python's string Template for safe variable substitution
            template = Template(prompt_template)
            return template.safe_substitute(template_vars)
        
        return prompt_template
    
    def get_system_prompt(self, template_name: str, **kwargs) -> str:
        """Get system prompt with keyword arguments"""
        return self.get_prompt(template_name, kwargs)
    
    def list_templates(self) -> list:
        """List available templates"""
        templates = []
        if os.path.exists(self.templates_dir):
            for file in os.listdir(self.templates_dir):
                if file.endswith('.json'):
                    templates.append(file[:-5])  # Remove .json extension
        return templates
    
    def clear_cache(self):
        """Clear template cache"""
        self._cache.clear()
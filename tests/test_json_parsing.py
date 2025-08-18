# -*- coding: utf-8 -*-
"""
Direct test of JSON parsing logic
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'agents'))

from agents.tool_manager import ToolManager
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

def test_json_parsing():
    """Test JSON parsing directly"""
    
    from agents.tools.security_tool import PasswordAnalyzerTool
    
    manager = ToolManager()
    manager.register_tool(PasswordAnalyzerTool())  # Register tool for inference
    
    test_cases = [
        # Case 1: Simple JSON
        '{"tool": "password_analyzer", "parameters": {"password": "test123"}}',
        
        # Case 2: JSON in text
        'I need to use {"tool": "password_analyzer", "parameters": {"password": "test123"}} to analyze this.',
        
        # Case 3: Formatted JSON
        '''Let me analyze this password: 
        {
            "tool": "password_analyzer", 
            "parameters": {"password": "test123"}
        }''',
        
        # Case 4: Missing parameters
        '{"tool": "password_analyzer"}',
        
        # Case 5: Russian response with JSON
        'Я использую {"tool": "password_analyzer", "parameters": {"password": "test123"}} для анализа.',
        
        # Case 6: GigaChat actual response format
        '''Чтобы оценить надежность указанного пароля, я воспользуюсь инструментом **password_analyzer**.

```
{
  "password": "password123"
}
``` 

После анализа инструмента предоставит оценку и рекомендации по улучшению пароля.''',

        # Case 7: Code block with json
        '''```json
{
  "password": "test123"
}
```''',
    ]
    
    print("Testing JSON parsing...")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i} ---")
        print(f"Input: {test_case}")
        
        result = manager.parse_tool_call(test_case)
        print(f"Parsed result: {result}")
        
        if result:
            print(f"✅ Success! Tool: {result.get('tool')}, Parameters: {result.get('parameters')}")
        else:
            print("❌ Failed to parse")
    
    # Test the helper method directly
    print("\n--- Testing JSON extraction method ---")
    test_text = 'Some text {"tool": "test", "parameters": {"key": "value"}} more text'
    json_objects = manager._extract_json_objects(test_text)
    print(f"Extracted JSON objects: {json_objects}")


if __name__ == "__main__":
    test_json_parsing()

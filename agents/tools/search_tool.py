# -*- coding: utf-8 -*-
# agents/tools/search_tool.py - Web search tool for agents

import requests
import os
from typing import Dict, Any, List
from dotenv import load_dotenv
from agents.base_tool import BaseTool


class WebSearchTool(BaseTool):
    """Tool for searching the web using Serper API"""
    
    def __init__(self):
        # Загружаем переменные окружения из .env файла
        load_dotenv()
        self.api_key = os.getenv("SERPER_API_KEY")
        if not self.api_key:
            raise ValueError("SERPER_API_KEY not found in environment variables. Please add it to your .env file.")
    
    @property
    def name(self) -> str:
        return "web_search"
    
    @property
    def description(self) -> str:
        return "Search the web for current information. Use this when you need up-to-date information not in your knowledge base."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "query": {
                "type": "string",
                "description": "Search query"
            },
            "num_results": {
                "type": "integer", 
                "description": "Number of results to return (default: 5)",
                "default": 5
            }
        }
    
    def execute(self, query: str = None, search_query: str = None, num_results: int = 5) -> Dict[str, Any]:
        """Execute web search"""
        # Handle both parameter names for flexibility
        search_term = query or search_query
        if not search_term:
            return {
                "success": False,
                "error": "No search query provided",
                "results": []
            }
            
        try:
            url = "https://google.serper.dev/search"
            
            payload = {
                "q": search_term,
                "num": min(num_results, 10)  # Limit to 10 results max
            }
            
            headers = {
                "X-API-KEY": self.api_key,
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract organic results
            results = []
            for item in data.get("organic", []):
                results.append({
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", ""),
                    "link": item.get("link", "")
                })
            
            return {
                "success": True,
                "query": search_term,
                "results": results,
                "total_found": len(results)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query": search_term,
                "results": []
            }


class KnowledgeSearchTool(BaseTool):
    """Tool for searching local knowledge base"""
    
    def __init__(self, vector_db, query_prep=None):
        self.vector_db = vector_db
        self.query_prep = query_prep
    
    @property
    def name(self) -> str:
        return "knowledge_search"
    
    @property
    def description(self) -> str:
        return "Search the local knowledge base for relevant information from ingested documents."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "query": {
                "type": "string",
                "description": "Search query for knowledge base"
            },
            "top_k": {
                "type": "integer",
                "description": "Number of results to return (default: 3)",
                "default": 3
            }
        }
    
    def execute(self, query: str, top_k: int = 3) -> Dict[str, Any]:
        """Execute knowledge base search"""
        try:
            # Preprocess query if available
            if self.query_prep:
                prep_result = self.query_prep.run(query)
                search_query = prep_result.rewritten or query
                entities = prep_result.entities
            else:
                search_query = query
                entities = []
            
            # Search vector database
            results = self.vector_db.search(search_query, top_k=top_k)
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "content": result["document"],
                    "filename": result["metadata"].get("filename", "Unknown"),
                    "distance": result["distance"],
                    "relevant": result["distance"] < 0.8
                })
            
            return {
                "success": True,
                "original_query": query,
                "enhanced_query": search_query,
                "entities_found": entities,
                "results": formatted_results,
                "total_found": len(formatted_results)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "results": []
            }

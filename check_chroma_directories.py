#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check all ChromaDB directories and collections
"""

import os
import sys
from pathlib import Path

# Add current directory to path so we can import our modules
sys.path.append(os.path.dirname(__file__))

from VectorDB.base_chroma_db import BaseChromaDB

def check_directory(dir_path: str):
    """Check a directory for ChromaDB collections"""
    print(f"\n🔍 Checking directory: {dir_path}")
    
    if not os.path.exists(dir_path):
        print(f"  ❌ Directory does not exist")
        return
    
    # Check if directory has ChromaDB files
    if os.path.exists(os.path.join(dir_path, "chroma.sqlite3")):
        print(f"  ✅ Found chroma.sqlite3")
    else:
        print(f"  ❌ No chroma.sqlite3 found")
        return
    
    # Try to list collections
    try:
        collections = BaseChromaDB.list_all_collections(dir_path)
        if collections:
            print(f"  📚 Found {len(collections)} collection(s):")
            for collection in collections:
                print(f"     - {collection['name']} ({collection['total_documents']} docs)")
        else:
            print(f"  📭 No collections found")
    except Exception as e:
        print(f"  ⚠️ Error listing collections: {e}")

def main():
    """Check all possible ChromaDB directories"""
    print("🔎 CHROMADB DIRECTORY DIAGNOSTIC")
    print("=" * 50)
    
    # List of possible ChromaDB directories
    directories_to_check = [
        "./chroma_db",           # Root level
        "./VectorDB/chroma_db",  # In VectorDB
        "./rag/chroma_db",       # In rag
        "../chroma_db"           # Parent directory
    ]
    
    for directory in directories_to_check:
        check_directory(directory)
    
    print(f"\n🏁 Diagnostic complete!")
    
    # Test creating a simple collection to see default path
    print(f"\n🧪 Testing default BaseChromaDB path...")
    try:
        test_db = BaseChromaDB("diagnostic_test")
        info = test_db.get_collection_info()
        print(f"  ✅ Default path works: {test_db.client._system._settings.persist_directory}")
        print(f"  📊 Test collection info: {info}")
        
        # Clean up test collection
        try:
            test_db.client.delete_collection("diagnostic_test")
            print(f"  🧹 Cleaned up test collection")
        except:
            pass
            
    except Exception as e:
        print(f"  ❌ Default path failed: {e}")

if __name__ == "__main__":
    main()
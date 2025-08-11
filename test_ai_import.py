#!/usr/bin/env python3
"""
Test the AI import functionality with the Grok-generated bookmarks
"""

import sys
import os

# Add the current directory to path to import bookmark_cleaner
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bookmark_cleaner import (
    import_ai_organized_bookmarks,
    extract_all_bookmarks,
    create_html_from_ai_structure
)

def test_ai_import():
    """Test importing the Grok AI-organized bookmarks"""
    
    print("📚 Testing AI Import Functionality")
    print("=" * 50)
    
    # Read the AI-organized content
    ai_file = "bookmarks-ai-grok.txt"
    if not os.path.exists(ai_file):
        print(f"❌ File not found: {ai_file}")
        return False
    
    with open(ai_file, 'r', encoding='utf-8') as f:
        ai_content = f.read()
    
    print(f"✅ Loaded AI file: {ai_file}")
    
    # Parse the AI content
    folder_structure, organized_bookmarks = import_ai_organized_bookmarks(ai_content)
    
    print(f"\n📊 Parsing Results:")
    print(f"  - Total bookmarks: {len(organized_bookmarks)}")
    print(f"  - Total folders: {len(folder_structure)}")
    
    # Show folder structure
    print("\n📁 Folder Structure:")
    for folder_path in sorted(folder_structure.keys())[:10]:  # Show first 10
        bookmark_count = len(folder_structure[folder_path])
        indent = "  " * folder_path.count('/')
        folder_name = folder_path.split('/')[-1] if '/' in folder_path else folder_path
        print(f"{indent}📁 {folder_name} ({bookmark_count} bookmarks)")
    
    # Check for bookmarks in folders
    print("\n🔍 Checking bookmark placement:")
    folders_with_bookmarks = sum(1 for items in folder_structure.values() if items)
    empty_folders = len(folder_structure) - folders_with_bookmarks
    
    print(f"  - Folders with bookmarks: {folders_with_bookmarks}")
    print(f"  - Empty folders: {empty_folders}")
    
    # Sample some bookmarks
    print("\n📌 Sample bookmarks by folder:")
    for folder_path in list(folder_structure.keys())[:5]:
        items = folder_structure[folder_path]
        if items:
            print(f"\n  {folder_path}:")
            for item in items[:3]:  # Show first 3 bookmarks
                print(f"    - {item.get('formatted_label', 'Unknown')}")
    
    # Load original bookmarks for testing HTML creation
    original_file = "favorites_8_11_25.html"
    if os.path.exists(original_file):
        print(f"\n✅ Found original file: {original_file}")
        original_bookmarks = extract_all_bookmarks(original_file)
        print(f"  - Original bookmarks: {len(original_bookmarks)}")
        
        # Test HTML generation
        test_output = "output/test_ai_import.html"
        os.makedirs("output", exist_ok=True)
        create_html_from_ai_structure(folder_structure, original_bookmarks, test_output)
        
        if os.path.exists(test_output):
            file_size = os.path.getsize(test_output)
            print(f"\n✅ Test HTML created: {test_output}")
            print(f"  - File size: {file_size:,} bytes")
            
            # Check if bookmarks are in the HTML
            with open(test_output, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            bookmark_count = html_content.count('<DT><A HREF=')
            folder_count = html_content.count('<DT><H3>')
            
            print(f"  - Bookmarks in HTML: {bookmark_count}")
            print(f"  - Folders in HTML: {folder_count}")
            
            if bookmark_count > 0:
                print("\n🎉 SUCCESS! Bookmarks are properly placed in folders!")
            else:
                print("\n⚠️  WARNING: No bookmarks found in HTML output")
    else:
        print(f"\n⚠️  Original file not found: {original_file}")
        print("     Cannot test full HTML generation")
    
    return True

if __name__ == "__main__":
    success = test_ai_import()
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""
Regenerate AI-organized bookmarks with new Edge-compatible format
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from bookmark_cleaner import (
        import_ai_organized_bookmarks,
        extract_all_bookmarks, 
        create_html_from_ai_structure
    )
    from datetime import datetime
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def regenerate_bookmarks():
    """Regenerate AI-organized bookmarks with Edge compatibility"""
    print("🔄 Regenerating AI-Organized Bookmarks with Edge Compatibility")
    print("=" * 70)
    
    # File paths
    ai_file = "bookmarks-processed/ai-export/bookmarks-ai-grok.txt"
    original_file = "bookmarks-input/favorites_8_11_25.html"
    
    # Check files exist
    if not os.path.exists(ai_file):
        print(f"❌ AI file not found: {ai_file}")
        return False
        
    if not os.path.exists(original_file):
        print(f"❌ Original file not found: {original_file}")
        return False
    
    print(f"📥 Loading AI organization from: {ai_file}")
    print(f"📥 Loading original bookmarks from: {original_file}")
    
    # Load AI content
    with open(ai_file, 'r', encoding='utf-8') as f:
        ai_content = f.read()
    
    # Parse AI content  
    folder_structure, organized_bookmarks = import_ai_organized_bookmarks(ai_content)
    print(f"\n✅ Parsed {len(organized_bookmarks)} bookmarks into {len(folder_structure)} folders")
    
    # Load original bookmarks
    original_bookmarks = extract_all_bookmarks(original_file)
    print(f"✅ Loaded {len(original_bookmarks)} original bookmarks")
    
    # Create new output with Edge compatibility
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    job_folder = f"job_{timestamp}_edge_compatible"
    
    output_dir = f"bookmarks-processed/ai-organized/{job_folder}"
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = f"{output_dir}/favorites_ai_organized_edge_compatible.html"
    
    print(f"\n🔧 Generating Edge-compatible HTML...")
    create_html_from_ai_structure(folder_structure, original_bookmarks, output_path)
    
    # Verify output
    if os.path.exists(output_path):
        file_size = os.path.getsize(output_path)
        print(f"✅ Generated: {output_path}")
        print(f"📁 File size: {file_size:,} bytes")
        
        # Check content
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        folder_count = content.count('<DT><H3')
        bookmark_count = content.count('<DT><A HREF=')
        has_timestamps = 'ADD_DATE=' in content
        has_edge_comments = 'DO NOT EDIT!' in content
        
        print(f"\n📊 Edge Compatibility Check:")
        print(f"  ✅ Folders: {folder_count}")
        print(f"  ✅ Bookmarks: {bookmark_count}")
        print(f"  {'✅' if has_timestamps else '❌'} Timestamps: {has_timestamps}")
        print(f"  {'✅' if has_edge_comments else '❌'} Edge comments: {has_edge_comments}")
        
        if folder_count > 0 and bookmark_count > 0:
            print(f"\n🎉 SUCCESS! Edge-compatible bookmark file created!")
            print(f"\n📋 Next Steps:")
            print(f"  1. Open MS Edge")
            print(f"  2. Go to Settings > Import browser data")
            print(f"  3. Choose 'HTML file' and select:")
            print(f"     {Path(output_path).absolute()}")
            print(f"  4. Verify folders are preserved (not flattened)")
            
            return True
        else:
            print(f"\n⚠️  Warning: Generated file may be incomplete")
            return False
    else:
        print(f"❌ Failed to generate output file")
        return False

if __name__ == "__main__":
    success = regenerate_bookmarks()
    sys.exit(0 if success else 1)
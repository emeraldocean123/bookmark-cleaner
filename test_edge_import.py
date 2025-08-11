#!/usr/bin/env python3
"""
Test script to create a simple Edge-compatible bookmark file
"""

import os
import time
import sys
from pathlib import Path

def create_edge_test_bookmark():
    """Create a test bookmark file with Edge-compatible format"""
    
    timestamp = str(int(time.time()))
    
    html_content = f"""<!DOCTYPE NETSCAPE-Bookmark-file-1>
<!-- This is an automatically generated file.
     It will be read and overwritten.
     DO NOT EDIT! -->
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
<DL><p>
    <DT><H3 ADD_DATE="{timestamp}" LAST_MODIFIED="{timestamp}">Test Folder</H3>
    <DL><p>
        <DT><A HREF="https://github.com">github.com | GitHub</A>
        <DT><A HREF="https://google.com">google.com | Google</A>
        <DT><H3 ADD_DATE="{timestamp}" LAST_MODIFIED="{timestamp}">Subfolder</H3>
        <DL><p>
            <DT><A HREF="https://stackoverflow.com">stackoverflow.com | Stack Overflow</A>
        </DL><p>
    </DL><p>
    <DT><H3 ADD_DATE="{timestamp}" LAST_MODIFIED="{timestamp}">Another Folder</H3>
    <DL><p>
        <DT><A HREF="https://youtube.com">youtube.com | YouTube</A>
        <DT><A HREF="https://netflix.com">netflix.com | Netflix</A>
    </DL><p>
</DL><p>"""
    
    # Create test output
    output_dir = Path("bookmarks-processed/test")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    test_file = output_dir / "edge_test_bookmarks.html"
    
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Created test bookmark file: {test_file}")
    print(f"📁 File size: {test_file.stat().st_size:,} bytes")
    
    # Validate structure
    with open(test_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    folder_count = content.count('<DT><H3')
    bookmark_count = content.count('<DT><A HREF=')
    dl_tags = content.count('<DL><p>')
    
    print(f"\n📊 Structure Analysis:")
    print(f"  - Folders: {folder_count}")
    print(f"  - Bookmarks: {bookmark_count}")
    print(f"  - DL tags: {dl_tags}")
    print(f"  - Has timestamps: {'ADD_DATE' in content}")
    print(f"  - Has Edge comments: {'DO NOT EDIT!' in content}")
    
    print(f"\n🧪 Test this file by importing it into MS Edge:")
    print(f"  1. Open MS Edge")
    print(f"  2. Go to Settings > Import browser data")
    print(f"  3. Choose 'HTML file' and select: {test_file.absolute()}")
    print(f"  4. Check if folders are preserved in the bookmark structure")
    
    return test_file

if __name__ == "__main__":
    print("🔧 Creating Edge-Compatible Test Bookmark File")
    print("=" * 60)
    
    test_file = create_edge_test_bookmark()
    
    print(f"\n✨ Test file ready! Import this into Edge to verify folder structure is preserved.")
    sys.exit(0)
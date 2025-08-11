#!/usr/bin/env python3
"""
Test the new folder organization structure
"""

import os
import sys
from pathlib import Path
from datetime import datetime

def test_folder_structure():
    """Test that the new folder structure is properly organized"""
    print("🧪 Testing New Folder Organization")
    print("=" * 50)
    
    base_dir = Path(__file__).parent
    
    # Expected folder structure
    expected_folders = [
        "bookmarks-input",
        "bookmarks-backups", 
        "bookmarks-processed",
        "bookmarks-processed/cleaned",
        "bookmarks-processed/ai-export", 
        "bookmarks-processed/ai-organized",
        "bookmarks-processed/reports"
    ]
    
    print("📁 Checking folder structure...")
    all_good = True
    
    for folder in expected_folders:
        folder_path = base_dir / folder
        if folder_path.exists():
            print(f"  ✅ {folder}")
        else:
            print(f"  ❌ Missing: {folder}")
            all_good = False
    
    # Check if files were moved correctly
    print("\n📋 Checking file organization...")
    
    # Check input files
    input_dir = base_dir / "bookmarks-input"
    if input_dir.exists():
        input_files = list(input_dir.glob("*.html"))
        print(f"  📥 Input files: {len(input_files)}")
        for file in input_files:
            print(f"    - {file.name}")
    
    # Check backup files
    backup_dir = base_dir / "bookmarks-backups"
    if backup_dir.exists():
        backup_files = list(backup_dir.glob("*_backup_*.html"))
        print(f"  💾 Backup files: {len(backup_files)}")
        for file in backup_files:
            print(f"    - {file.name}")
    
    # Check processed files
    processed_dir = base_dir / "bookmarks-processed"
    if processed_dir.exists():
        for subdir in ["cleaned", "ai-export", "ai-organized", "reports"]:
            subdir_path = processed_dir / subdir
            if subdir_path.exists():
                files = list(subdir_path.glob("**/*"))
                files = [f for f in files if f.is_file()]
                print(f"  📊 {subdir}: {len(files)} files")
                for file in files[:3]:  # Show first 3
                    rel_path = file.relative_to(processed_dir)
                    print(f"    - {rel_path}")
                if len(files) > 3:
                    print(f"    ... and {len(files) - 3} more")
    
    print("\n🏗️  Testing job folder creation...")
    
    # Test timestamp generation
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    job_folder = f"job_{timestamp}_test"
    print(f"  Sample job folder: {job_folder}")
    
    # Test if we can create the structure
    try:
        test_dirs = [
            processed_dir / "cleaned" / job_folder,
            processed_dir / "ai-export" / job_folder,
            processed_dir / "ai-organized" / job_folder,
            processed_dir / "reports" / job_folder
        ]
        
        created_dirs = []
        for test_dir in test_dirs:
            if not test_dir.exists():
                test_dir.mkdir(parents=True, exist_ok=True)
                created_dirs.append(test_dir)
                print(f"  ✅ Created: {test_dir.relative_to(base_dir)}")
        
        # Clean up test directories
        for test_dir in created_dirs:
            test_dir.rmdir()
            print(f"  🧹 Cleaned up: {test_dir.relative_to(base_dir)}")
            
        print("\n🎉 Folder structure test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error testing folder creation: {e}")
        all_good = False
    
    # Check script configuration
    print("\n⚙️  Checking script configuration...")
    try:
        import bookmark_cleaner
        config = bookmark_cleaner.DEFAULT_CONFIG
        
        print(f"  📁 Output directory: {config['output_dir']}")
        print(f"  📁 Input directory: {config['input_dir']}")
        print(f"  📁 Backup directory: {config['backup_dir']}")
        
        if (config['output_dir'] == 'bookmarks-processed' and
            config['input_dir'] == 'bookmarks-input' and
            config['backup_dir'] == 'bookmarks-backups'):
            print("  ✅ Script configuration matches folder structure")
        else:
            print("  ⚠️  Script configuration may not match folders")
            
    except ImportError as e:
        print(f"  ⚠️  Could not import bookmark_cleaner: {e}")
    
    return all_good

if __name__ == "__main__":
    success = test_folder_structure()
    print(f"\n{'✅ ALL TESTS PASSED' if success else '❌ SOME TESTS FAILED'}")
    sys.exit(0 if success else 1)
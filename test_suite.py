#!/usr/bin/env python3
"""
Consolidated test suite for bookmark cleaner functionality
Replaces multiple individual test scripts with a unified testing interface
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from bookmark_cleaner import (
        import_ai_organized_bookmarks,
        extract_all_bookmarks,
        create_html_from_ai_structure
    )
except ImportError as e:
    print(f"ERROR: Could not import bookmark_cleaner: {e}")
    sys.exit(1)

class BookmarkTester:
    """Consolidated bookmark testing functionality"""
    
    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.ai_file = self.script_dir / "bookmarks-processed" / "ai-export" / "bookmarks-ai-grok.txt"
        self.original_file = self.script_dir / "bookmarks-input" / "favorites_8_11_25.html"
    
    def test_ai_parsing(self, verbose=False):
        """Test AI bookmark parsing functionality"""
        print("Testing AI Parsing...")
        print("=" * 50)
        
        if not self.ai_file.exists():
            print(f"ERROR: AI file not found: {self.ai_file}")
            return False
        
        with open(self.ai_file, 'r', encoding='utf-8') as f:
            ai_content = f.read()
        
        if verbose:
            print(f"Loaded AI file: {len(ai_content.splitlines())} lines")
        
        # Parse with optional debug output
        if verbose:
            folder_structure, organized_bookmarks = import_ai_organized_bookmarks(ai_content)
        else:
            # Temporarily redirect output for clean testing
            import io
            import contextlib
            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                folder_structure, organized_bookmarks = import_ai_organized_bookmarks(ai_content)
        
        print(f"Results: {len(organized_bookmarks)} bookmarks in {len(folder_structure)} folders")
        
        if verbose:
            print("\nFolder Summary:")
            for folder_path, items in sorted(folder_structure.items()):
                print(f"  '{folder_path}': {len(items)} items")
        
        return len(organized_bookmarks) > 50  # Should be much more than 17
    
    def test_full_workflow(self, verbose=False):
        """Test complete AI import workflow"""
        print("Testing Complete AI Workflow...")
        print("=" * 50)
        
        if not self.original_file.exists():
            print(f"ERROR: Original file not found: {self.original_file}")
            return False
        
        # Prepare inputs for automated testing
        inputs = f"{self.ai_file}\n{self.original_file}\n"
        
        try:
            # Run the full workflow
            result = subprocess.run([
                "py",
                str(self.script_dir / "bookmark_cleaner.py"),
                "--import-ai",
                "--output-dir", str(self.script_dir / "bookmarks-processed")
            ], input=inputs, capture_output=True, text=True, timeout=60)
            
            if verbose:
                print("STDOUT:")
                print(result.stdout)
                if result.stderr:
                    print("\nSTDERR:")
                    print(result.stderr)
            
            success = result.returncode == 0
            
            if success:
                print("Workflow completed successfully!")
                # Check for output file
                output_dir = self.script_dir / "bookmarks-processed" / "ai-organized"
                if any(output_dir.glob("**/favorites_*_ai_organized.html")):
                    print("Output HTML file generated successfully!")
                else:
                    print("WARNING: No output HTML file found")
                    success = False
            else:
                print(f"Workflow failed with return code: {result.returncode}")
            
            return success
            
        except subprocess.TimeoutExpired:
            print("ERROR: Workflow timed out")
            return False
        except Exception as e:
            print(f"ERROR: {e}")
            return False
    
    def test_syntax_validation(self):
        """Test Python syntax validation"""
        print("Testing Python Syntax...")
        print("=" * 50)
        
        python_files = [
            "bookmark_cleaner.py",
        ]
        
        all_valid = True
        for file_name in python_files:
            file_path = self.script_dir / file_name
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        compile(f.read(), file_path, 'exec')
                    print(f"PASS {file_name}")
                except SyntaxError as e:
                    print(f"FAIL {file_name}: Syntax error at line {e.lineno}: {e.msg}")
                    all_valid = False
                except Exception as e:
                    print(f"FAIL {file_name}: {e}")
                    all_valid = False
            else:
                print(f"? {file_name}: File not found")
        
        return all_valid
    
    def run_all_tests(self, verbose=False):
        """Run all tests"""
        print("Running Bookmark Cleaner Test Suite")
        print("=" * 60)
        
        results = {}
        
        # Test 1: Syntax validation
        results['syntax'] = self.test_syntax_validation()
        print()
        
        # Test 2: AI parsing
        results['parsing'] = self.test_ai_parsing(verbose)
        print()
        
        # Test 3: Full workflow (only if parsing works)
        if results['parsing']:
            results['workflow'] = self.test_full_workflow(verbose)
        else:
            print("Skipping workflow test due to parsing failure")
            results['workflow'] = False
        
        print("=" * 60)
        print("Test Results Summary:")
        
        for test_name, passed in results.items():
            status = "PASS" if passed else "FAIL"
            print(f"  {test_name.title()}: {status}")
        
        all_passed = all(results.values())
        overall = "ALL TESTS PASSED" if all_passed else "SOME TESTS FAILED"
        print(f"\nOverall: {overall}")
        
        return all_passed

def main():
    """Main test runner with command line interface"""
    parser = argparse.ArgumentParser(description='Bookmark Cleaner Test Suite')
    parser.add_argument('--test', choices=['parsing', 'workflow', 'syntax', 'all'], 
                       default='all', help='Specific test to run')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Enable verbose output')
    
    args = parser.parse_args()
    
    tester = BookmarkTester()
    
    if args.test == 'parsing':
        success = tester.test_ai_parsing(args.verbose)
    elif args.test == 'workflow':
        success = tester.test_full_workflow(args.verbose)
    elif args.test == 'syntax':
        success = tester.test_syntax_validation()
    else:  # 'all'
        success = tester.run_all_tests(args.verbose)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
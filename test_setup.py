#!/usr/bin/env python3
"""
Test setup script for Bookmark Cleaner

Validates that all dependencies are installed and working correctly.
"""

import sys
import importlib
from typing import List, Tuple


def test_python_version() -> Tuple[bool, str]:
    """Test if Python version is suitable"""
    if sys.version_info < (3, 7):
        return False, f"Python 3.7+ required, found {sys.version_info.major}.{sys.version_info.minor}"
    return True, f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def test_dependencies() -> List[Tuple[str, bool, str]]:
    """Test if all required dependencies are available"""
    dependencies = [
        ('beautifulsoup4', 'bs4'),
        ('requests', 'requests'),  
        ('lxml', 'lxml'),
    ]
    
    results = []
    for package_name, import_name in dependencies:
        try:
            module = importlib.import_module(import_name)
            version = getattr(module, '__version__', 'unknown')
            results.append((package_name, True, version))
        except ImportError:
            results.append((package_name, False, 'not installed'))
    
    return results


def test_bookmark_cleaner_import() -> Tuple[bool, str]:
    """Test if bookmark_cleaner module can be imported"""
    try:
        import bookmark_cleaner
        return True, "bookmark_cleaner.py imports successfully"
    except ImportError as e:
        return False, f"Failed to import bookmark_cleaner.py: {e}"
    except Exception as e:
        return False, f"Error in bookmark_cleaner.py: {e}"


def main():
    """Run all setup tests"""
    print("🧪 Testing Bookmark Cleaner Setup")
    print("=" * 40)
    
    all_passed = True
    
    # Test Python version
    python_ok, python_msg = test_python_version()
    status = "✅" if python_ok else "❌"
    print(f"{status} Python Version: {python_msg}")
    if not python_ok:
        all_passed = False
    
    print()
    
    # Test dependencies
    print("📦 Testing Dependencies:")
    dep_results = test_dependencies()
    for package, success, version in dep_results:
        status = "✅" if success else "❌"
        print(f"  {status} {package}: {version}")
        if not success:
            all_passed = False
    
    print()
    
    # Test main module import
    import_ok, import_msg = test_bookmark_cleaner_import()
    status = "✅" if import_ok else "❌"
    print(f"{status} Module Import: {import_msg}")
    if not import_ok:
        all_passed = False
    
    print()
    print("=" * 40)
    
    if all_passed:
        print("🎉 All tests passed! Bookmark Cleaner is ready to use.")
        print()
        print("To get started:")
        print("  python bookmark_cleaner.py --help")
        print("  python bookmark_cleaner.py path/to/bookmarks.html")
        return 0
    else:
        print("❌ Some tests failed. Please check the errors above.")
        print()
        print("To fix issues:")
        print("  1. Make sure Python 3.7+ is installed")
        print("  2. Run: pip install -r requirements.txt")
        print("  3. Run this test again")
        return 1


if __name__ == "__main__":
    sys.exit(main())
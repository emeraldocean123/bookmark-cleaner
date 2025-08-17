#!/usr/bin/env python3
"""
Quick syntax validation for bookmark_cleaner.py
"""

import ast
import sys
import os

# Ensure proper Unicode output on Windows
if os.name == 'nt':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def validate_syntax(filename):
    """Validate Python syntax without executing"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # Parse the AST to check for syntax errors
        ast.parse(source)
        print(f"[PASS] Syntax validation passed for {filename}")
        return True
        
    except SyntaxError as e:
        print(f"[FAIL] Syntax error in {filename}:")
        print(f"  Line {e.lineno}: {e.msg}")
        if e.text:
            print(f"  Code: {e.text.strip()}")
        return False
    except Exception as e:
        print(f"[ERROR] Error reading {filename}: {e}")
        return False

if __name__ == "__main__":
    result = validate_syntax("bookmark_cleaner.py")
    sys.exit(0 if result else 1)
#!/usr/bin/env python3
"""
Comprehensive test runner for bookmark cleaner project
Runs all test suites including security, performance, and functionality tests
"""

import sys
import os
import unittest
import time
from pathlib import Path

# Ensure proper Unicode output on Windows
if os.name == 'nt':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_all_tests():
    """Run all test suites and generate a comprehensive report"""
    print("=" * 80)
    print("BOOKMARK CLEANER - COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    
    start_time = time.time()
    
    # Discover and run all tests
    loader = unittest.TestLoader()
    
    # Load original test suite
    print("\n1. Running Original Test Suite...")
    print("-" * 40)
    try:
        from test_suite import BookmarkTester
        original_tester = BookmarkTester()
        original_results = original_tester.run_all_tests(verbose=False)
        print(f"Original tests: {'PASSED' if original_results else 'FAILED'}")
    except Exception as e:
        print(f"Original tests: ERROR - {e}")
        original_results = False
    
    # Load security tests
    print("\n2. Running Security Tests...")
    print("-" * 40)
    try:
        security_suite = loader.discover('tests', pattern='test_security.py')
        security_runner = unittest.TextTestRunner(verbosity=2)
        security_result = security_runner.run(security_suite)
        security_passed = security_result.wasSuccessful()
        print(f"Security tests: {'PASSED' if security_passed else 'FAILED'}")
    except Exception as e:
        print(f"Security tests: ERROR - {e}")
        security_passed = False
    
    # Load performance tests
    print("\n3. Running Performance Tests...")
    print("-" * 40)
    try:
        performance_suite = loader.discover('tests', pattern='test_performance.py')
        performance_runner = unittest.TextTestRunner(verbosity=2)
        performance_result = performance_runner.run(performance_suite)
        performance_passed = performance_result.wasSuccessful()
        print(f"Performance tests: {'PASSED' if performance_passed else 'FAILED'}")
    except Exception as e:
        print(f"Performance tests: ERROR - {e}")
        performance_passed = False
    
    # Final summary
    total_time = time.time() - start_time
    print("\n" + "=" * 80)
    print("FINAL TEST RESULTS SUMMARY")
    print("=" * 80)
    print(f"Original Test Suite:    {'✓ PASSED' if original_results else '✗ FAILED'}")
    print(f"Security Tests:         {'✓ PASSED' if security_passed else '✗ FAILED'}")
    print(f"Performance Tests:      {'✓ PASSED' if performance_passed else '✗ FAILED'}")
    print(f"\nTotal execution time: {total_time:.2f} seconds")
    
    all_passed = original_results and security_passed and performance_passed
    overall_status = "ALL TESTS PASSED" if all_passed else "SOME TESTS FAILED"
    print(f"\nOverall Status: {overall_status}")
    print("=" * 80)
    
    return all_passed

def run_quick_tests():
    """Run just the essential tests for quick validation"""
    print("QUICK TEST SUITE")
    print("=" * 40)
    
    # Run syntax validation
    print("1. Syntax Validation...")
    try:
        from test_suite import BookmarkTester
        tester = BookmarkTester()
        syntax_ok = tester.test_syntax_validation()
        print(f"   Syntax: {'✓ PASSED' if syntax_ok else '✗ FAILED'}")
    except Exception as e:
        print(f"   Syntax: ERROR - {e}")
        syntax_ok = False
    
    # Quick security check
    print("2. Security Check...")
    try:
        from tests.test_security import TestSecurityFeatures
        suite = unittest.TestLoader().loadTestsFromTestCase(TestSecurityFeatures)
        result = unittest.TextTestRunner(verbosity=0).run(suite)
        security_ok = result.wasSuccessful()
        print(f"   Security: {'✓ PASSED' if security_ok else '✗ FAILED'}")
    except Exception as e:
        print(f"   Security: ERROR - {e}")
        security_ok = False
    
    quick_passed = syntax_ok and security_ok
    print(f"\nQuick tests: {'✓ PASSED' if quick_passed else '✗ FAILED'}")
    return quick_passed

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Bookmark Cleaner Test Runner')
    parser.add_argument('--quick', action='store_true', 
                       help='Run only quick validation tests')
    parser.add_argument('--security', action='store_true', 
                       help='Run only security tests')
    parser.add_argument('--performance', action='store_true', 
                       help='Run only performance tests')
    
    args = parser.parse_args()
    
    if args.quick:
        success = run_quick_tests()
    elif args.security:
        loader = unittest.TestLoader()
        suite = loader.discover('tests', pattern='test_security.py')
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        success = result.wasSuccessful()
    elif args.performance:
        loader = unittest.TestLoader()
        suite = loader.discover('tests', pattern='test_performance.py')
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        success = result.wasSuccessful()
    else:
        success = run_all_tests()
    
    sys.exit(0 if success else 1)
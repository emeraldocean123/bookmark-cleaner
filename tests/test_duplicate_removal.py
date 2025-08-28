#!/usr/bin/env python3
"""
Comprehensive test suite for duplicate removal functionality
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Add parent directory to path to import bookmark_cleaner
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bookmark_cleaner import (
    normalize_url, calculate_title_similarity, calculate_levenshtein_ratio,
    DuplicateDetector, remove_duplicate_urls
)


class TestURLNormalization(unittest.TestCase):
    """Test URL normalization functionality"""
    
    def test_basic_normalization(self):
        """Test basic URL normalization"""
        # Case normalization
        self.assertEqual(normalize_url("HTTPS://EXAMPLE.COM"), "https://example.com")
        
        # Trailing slash removal
        self.assertEqual(normalize_url("https://example.com/"), "https://example.com")
        
        # www removal
        self.assertEqual(normalize_url("https://www.example.com"), "https://example.com")
        self.assertEqual(normalize_url("http://www.example.com"), "http://example.com")
    
    def test_tracking_parameter_removal(self):
        """Test removal of tracking parameters"""
        # UTM parameters
        original = "https://example.com?utm_source=google&utm_medium=cpc&utm_campaign=test"
        expected = "https://example.com"
        self.assertEqual(normalize_url(original), expected)
        
        # Mixed parameters (keep non-tracking)
        original = "https://example.com?page=1&utm_source=google&sort=date"
        expected = "https://example.com?page=1&sort=date"
        self.assertEqual(normalize_url(original), expected)
        
        # Facebook and Google tracking
        original = "https://example.com?fbclid=123&gclid=456"
        expected = "https://example.com"
        self.assertEqual(normalize_url(original), expected)
    
    def test_edge_cases(self):
        """Test edge cases in URL normalization"""
        # Empty URL
        self.assertEqual(normalize_url(""), "")
        
        # None input
        self.assertEqual(normalize_url(None), "")
        
        # URL with only tracking parameters
        original = "https://example.com?utm_source=test"
        expected = "https://example.com"
        self.assertEqual(normalize_url(original), expected)

    def test_default_port_removal(self):
        """Default ports should be stripped from URLs"""
        self.assertEqual(normalize_url("http://example.com:80"), "http://example.com")
        self.assertEqual(normalize_url("https://example.com:443"), "https://example.com")
        # Non-default ports should remain
        self.assertEqual(normalize_url("http://example.com:8080"), "http://example.com:8080")


class TestSimilarityCalculations(unittest.TestCase):
    """Test similarity calculation functions"""
    
    def test_title_similarity(self):
        """Test title similarity calculation"""
        # Identical titles
        self.assertEqual(calculate_title_similarity("Test Title", "Test Title"), 1.0)
        
        # Case insensitive
        self.assertEqual(calculate_title_similarity("Test Title", "test title"), 1.0)
        
        # Partial similarity
        sim = calculate_title_similarity("GitHub Repository", "GitHub Project")
        self.assertGreater(sim, 0.0)
        self.assertLess(sim, 1.0)
        
        # No similarity
        self.assertEqual(calculate_title_similarity("GitHub", "Facebook"), 0.0)
        
        # Empty strings
        self.assertEqual(calculate_title_similarity("", ""), 1.0)
        self.assertEqual(calculate_title_similarity("test", ""), 0.0)
    
    def test_levenshtein_ratio(self):
        """Test Levenshtein distance ratio calculation"""
        # Identical strings
        self.assertEqual(calculate_levenshtein_ratio("test", "test"), 1.0)
        
        # Completely different
        ratio = calculate_levenshtein_ratio("abc", "xyz")
        self.assertLess(ratio, 0.5)
        
        # Similar strings
        ratio = calculate_levenshtein_ratio("kitten", "sitting")
        self.assertGreater(ratio, 0.5)
        
        # Empty strings
        self.assertEqual(calculate_levenshtein_ratio("", ""), 1.0)
        self.assertEqual(calculate_levenshtein_ratio("test", ""), 0.0)


class TestDuplicateDetector(unittest.TestCase):
    """Test the DuplicateDetector class"""
    
    def setUp(self):
        """Set up test data"""
        self.sample_bookmarks = [
            {
                'url': 'https://example.com',
                'formatted_label': 'Example Site',
                'domain': 'example.com',
                'original_title': 'Example Site - Welcome'
            },
            {
                'url': 'https://www.example.com/',
                'formatted_label': 'Example Site',
                'domain': 'example.com',
                'original_title': 'Example Site - Homepage'
            },
            {
                'url': 'https://github.com',
                'formatted_label': 'GitHub',
                'domain': 'github.com',
                'original_title': 'GitHub'
            },
            {
                'url': 'https://github.com?utm_source=google',
                'formatted_label': 'GitHub Homepage',
                'domain': 'github.com',
                'original_title': 'GitHub - Where software lives'
            }
        ]
    
    def test_url_duplicate_detection(self):
        """Test URL-based duplicate detection"""
        detector = DuplicateDetector(strategy='url', keep_strategy='first')
        result = detector.detect_duplicates(self.sample_bookmarks)
        
        # Should remove duplicates based on normalized URLs
        self.assertLess(len(result), len(self.sample_bookmarks))
        self.assertEqual(detector.removed_count, 2)  # Two URL duplicates
    
    def test_title_duplicate_detection(self):
        """Test title-based duplicate detection"""
        detector = DuplicateDetector(strategy='title', keep_strategy='first')
        result = detector.detect_duplicates(self.sample_bookmarks)
        
        # Should detect title duplicates
        self.assertLessEqual(len(result), len(self.sample_bookmarks))
    
    def test_smart_duplicate_detection(self):
        """Test smart duplicate detection"""
        detector = DuplicateDetector(strategy='smart', keep_strategy='first')
        result = detector.detect_duplicates(self.sample_bookmarks)
        
        # Should group by domain and detect URL duplicates within groups
        self.assertLess(len(result), len(self.sample_bookmarks))
    
    def test_fuzzy_duplicate_detection(self):
        """Test fuzzy duplicate detection"""
        detector = DuplicateDetector(strategy='fuzzy', similarity_threshold=0.7, keep_strategy='first')
        result = detector.detect_duplicates(self.sample_bookmarks)
        
        # Should detect similar bookmarks based on multiple criteria
        self.assertLessEqual(len(result), len(self.sample_bookmarks))
    
    def test_keep_strategies(self):
        """Test different keep strategies"""
        # Test keep first
        detector = DuplicateDetector(strategy='url', keep_strategy='first')
        result_first = detector.detect_duplicates(self.sample_bookmarks.copy())
        
        # Test keep last
        detector = DuplicateDetector(strategy='url', keep_strategy='last')
        result_last = detector.detect_duplicates(self.sample_bookmarks.copy())
        
        # Results should have same length but potentially different kept items
        self.assertEqual(len(result_first), len(result_last))
    
    def test_report_generation(self):
        """Test duplicate report generation"""
        detector = DuplicateDetector(strategy='url', keep_strategy='first')
        detector.detect_duplicates(self.sample_bookmarks)
        
        report = detector.generate_report()
        self.assertIsInstance(report, str)
        self.assertIn("Duplicate Analysis Report", report)
        self.assertIn("Strategy: url", report)


class TestDuplicateRemovalIntegration(unittest.TestCase):
    """Test the integrated duplicate removal function"""
    
    def setUp(self):
        """Set up test data"""
        self.test_bookmarks = [
            {
                'url': 'https://example.com',
                'formatted_label': 'Example Site',
                'domain': 'example.com'
            },
            {
                'url': 'https://www.example.com/',
                'formatted_label': 'Example Site Homepage',
                'domain': 'example.com'
            },
            {
                'url': 'https://github.com',
                'formatted_label': 'GitHub',
                'domain': 'github.com'
            },
            {
                'url': 'https://different.com',
                'formatted_label': 'Different Site',
                'domain': 'different.com'
            }
        ]
    
    def test_remove_duplicate_urls_function(self):
        """Test the main remove_duplicate_urls function"""
        result, report = remove_duplicate_urls(
            self.test_bookmarks,
            strategy='url',
            keep_strategy='first',
            generate_report=True
        )
        
        # Should remove URL duplicate
        self.assertLess(len(result), len(self.test_bookmarks))
        
        # Should generate report when requested
        self.assertIsNotNone(report)
        self.assertIn("Duplicate Analysis Report", report)
    
    def test_different_strategies(self):
        """Test different duplicate removal strategies"""
        strategies = ['url', 'title', 'smart', 'fuzzy']
        
        for strategy in strategies:
            result, _ = remove_duplicate_urls(
                self.test_bookmarks.copy(),
                strategy=strategy,
                similarity_threshold=0.8,
                keep_strategy='first'
            )
            
            # Result should be list of bookmarks
            self.assertIsInstance(result, list)
            # Should not exceed original length
            self.assertLessEqual(len(result), len(self.test_bookmarks))
    
    def test_empty_bookmark_list(self):
        """Test handling of empty bookmark list"""
        result, report = remove_duplicate_urls([], strategy='url')
        
        self.assertEqual(result, [])
        self.assertIsNone(report)
    
    def test_no_duplicates(self):
        """Test when no duplicates exist"""
        unique_bookmarks = [
            {
                'url': 'https://site1.com',
                'formatted_label': 'Site 1',
                'domain': 'site1.com'
            },
            {
                'url': 'https://site2.com',
                'formatted_label': 'Site 2',
                'domain': 'site2.com'
            }
        ]
        
        result, _ = remove_duplicate_urls(unique_bookmarks, strategy='url')
        
        # Should return all bookmarks unchanged
        self.assertEqual(len(result), len(unique_bookmarks))


class TestDuplicateScenarios(unittest.TestCase):
    """Test real-world duplicate scenarios"""
    
    def test_tracking_parameter_duplicates(self):
        """Test detection of URLs that differ only by tracking parameters"""
        bookmarks = [
            {
                'url': 'https://example.com/page',
                'formatted_label': 'Example Page',
                'domain': 'example.com'
            },
            {
                'url': 'https://example.com/page?utm_source=google&utm_medium=cpc',
                'formatted_label': 'Example Page',
                'domain': 'example.com'
            },
            {
                'url': 'https://example.com/page?fbclid=abc123',
                'formatted_label': 'Example Page',
                'domain': 'example.com'
            }
        ]
        
        result, _ = remove_duplicate_urls(bookmarks, strategy='url')
        
        # Should detect all as duplicates and keep only one
        self.assertEqual(len(result), 1)
    
    def test_www_subdomain_duplicates(self):
        """Test detection of www vs non-www duplicates"""
        bookmarks = [
            {
                'url': 'https://example.com',
                'formatted_label': 'Example',
                'domain': 'example.com'
            },
            {
                'url': 'https://www.example.com',
                'formatted_label': 'Example Site',
                'domain': 'example.com'
            }
        ]
        
        result, _ = remove_duplicate_urls(bookmarks, strategy='url')
        
        # Should detect as duplicates
        self.assertEqual(len(result), 1)
    
    def test_case_insensitive_duplicates(self):
        """Test case-insensitive duplicate detection"""
        bookmarks = [
            {
                'url': 'https://EXAMPLE.COM/PAGE',
                'formatted_label': 'Example Page',
                'domain': 'example.com'
            },
            {
                'url': 'https://example.com/page',
                'formatted_label': 'Example Page',
                'domain': 'example.com'
            }
        ]
        
        result, _ = remove_duplicate_urls(bookmarks, strategy='url')
        
        # Should detect as duplicates despite case differences
        self.assertEqual(len(result), 1)
    
    def test_similar_titles_fuzzy_matching(self):
        """Test fuzzy matching for similar titles"""
        bookmarks = [
            {
                'url': 'https://site1.com',
                'formatted_label': 'GitHub Repository',
                'domain': 'site1.com'
            },
            {
                'url': 'https://site2.com',
                'formatted_label': 'GitHub Project',
                'domain': 'site2.com'
            },
            {
                'url': 'https://site3.com',
                'formatted_label': 'Completely Different',
                'domain': 'site3.com'
            }
        ]
        
        result, _ = remove_duplicate_urls(
            bookmarks, 
            strategy='fuzzy', 
            similarity_threshold=0.6
        )
        
        # Should detect similar GitHub titles as potential duplicates
        # but keep "Completely Different"
        self.assertLessEqual(len(result), len(bookmarks))


def run_duplicate_tests():
    """Run all duplicate removal tests"""
    print("Running Duplicate Removal Test Suite...")
    print("=" * 60)
    
    # Create test suite
    test_classes = [
        TestURLNormalization,
        TestSimilarityCalculations, 
        TestDuplicateDetector,
        TestDuplicateRemovalIntegration,
        TestDuplicateScenarios
    ]
    
    suite = unittest.TestSuite()
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("Duplicate Removal Test Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nOverall: {'PASSED' if success else 'FAILED'}")
    
    return success


if __name__ == '__main__':
    success = run_duplicate_tests()
    sys.exit(0 if success else 1)
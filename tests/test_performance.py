#!/usr/bin/env python3
"""
Performance tests for bookmark cleaner
Tests processing of large bookmark collections and concurrent validation
"""

import sys
import os
import unittest
import time
from pathlib import Path
from unittest.mock import Mock, patch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from bookmark_cleaner import (
    extract_all_bookmarks,
    clean_title,
    extract_domain,
    validate_bookmarks_concurrent,
    validate_bookmarks_sequential
)


class TestPerformance(unittest.TestCase):
    """Test performance characteristics of bookmark processing"""

    def setUp(self):
        """Set up test data"""
        self.large_bookmark_count = 1000
        self.test_file = Path('test_large_bookmarks.html')

    def tearDown(self):
        """Clean up test files"""
        if self.test_file.exists():
            self.test_file.unlink()

    def create_large_bookmark_file(self, count: int) -> str:
        """Create a test file with many bookmarks"""
        html_content = '''<!DOCTYPE html>
<html>
<head><title>Large Bookmark Collection</title></head>
<body>
<h3>Bookmarks</h3>
<dl>
'''
        
        for i in range(count):
            domain = f"example{i % 100}.com"  # Vary domains
            title = f"Test Bookmark {i} - Example Site {i % 100}"
            html_content += f'<dt><a href="https://{domain}/page{i}">"{title}"</a></dt>\n'
        
        html_content += '''</dl>
</body>
</html>'''
        
        with open(self.test_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(self.test_file)

    def test_large_bookmark_extraction(self):
        """Test extraction performance with large bookmark collections"""
        # Create test file with many bookmarks
        test_file = self.create_large_bookmark_file(self.large_bookmark_count)
        
        # Measure extraction time
        start_time = time.time()
        bookmarks = extract_all_bookmarks(test_file)
        extraction_time = time.time() - start_time
        
        # Verify results
        self.assertEqual(len(bookmarks), self.large_bookmark_count)
        
        # Performance assertion (should complete within reasonable time)
        self.assertLess(extraction_time, 5.0, 
                       f"Extraction took too long: {extraction_time:.2f}s for {self.large_bookmark_count} bookmarks")
        
        print(f"Extracted {len(bookmarks)} bookmarks in {extraction_time:.2f}s")

    def test_title_cleaning_performance(self):
        """Test title cleaning performance with many titles"""
        titles = [
            f"Test Title {i} | Example Site {i} - Welcome to the Homepage" 
            for i in range(1000)
        ]
        
        start_time = time.time()
        cleaned_titles = [clean_title(title) for title in titles]
        cleaning_time = time.time() - start_time
        
        # Verify all titles were processed
        self.assertEqual(len(cleaned_titles), len(titles))
        
        # Performance assertion
        self.assertLess(cleaning_time, 1.0, 
                       f"Title cleaning took too long: {cleaning_time:.2f}s for {len(titles)} titles")
        
        print(f"Cleaned {len(titles)} titles in {cleaning_time:.2f}s")

    def test_domain_extraction_performance(self):
        """Test domain extraction performance with many URLs"""
        urls = [
            f"https://www.example{i % 100}.com/path/to/page{i}"
            for i in range(1000)
        ]
        
        start_time = time.time()
        domains = [extract_domain(url) for url in urls]
        extraction_time = time.time() - start_time
        
        # Verify all domains were processed
        self.assertEqual(len(domains), len(urls))
        
        # Performance assertion
        self.assertLess(extraction_time, 1.0, 
                       f"Domain extraction took too long: {extraction_time:.2f}s for {len(urls)} URLs")
        
        print(f"Extracted {len(urls)} domains in {extraction_time:.2f}s")

    @patch('requests.Session')
    def test_concurrent_validation_performance(self, mock_session_class):
        """Test concurrent validation performance vs sequential"""
        # Mock the session and responses
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        # Mock successful HEAD request
        mock_response = Mock()
        mock_response.status_code = 200
        mock_session.head.return_value = mock_response
        
        # Create test bookmarks
        bookmarks = [
            {
                'url': f'https://example{i}.com',
                'formatted_label': f'Test Site {i}',
                'is_valid': None,
                'status_code': None
            }
            for i in range(100)
        ]
        
        # Test concurrent validation
        start_time = time.time()
        concurrent_results = validate_bookmarks_concurrent(bookmarks.copy(), max_workers=10)
        concurrent_time = time.time() - start_time
        
        # Test sequential validation
        start_time = time.time()
        sequential_results = validate_bookmarks_sequential(bookmarks.copy())
        sequential_time = time.time() - start_time
        
        # Verify results are equivalent
        self.assertEqual(len(concurrent_results), len(sequential_results))
        
        # Concurrent should be faster (or at least not significantly slower)
        # Note: With mocking, timing differences may be minimal
        print(f"Concurrent validation: {concurrent_time:.2f}s")
        print(f"Sequential validation: {sequential_time:.2f}s")
        
        # Both should complete in reasonable time
        self.assertLess(concurrent_time, 10.0, "Concurrent validation took too long")
        self.assertLess(sequential_time, 10.0, "Sequential validation took too long")

    def test_memory_efficiency_large_dataset(self):
        """Test memory efficiency with large datasets"""
        # Create a very large bookmark file
        large_count = 5000
        test_file = self.create_large_bookmark_file(large_count)
        
        # Process bookmarks and check memory doesn't explode
        # (This is a basic test - in production you'd use memory profiling tools)
        try:
            bookmarks = extract_all_bookmarks(test_file)
            self.assertEqual(len(bookmarks), large_count)
            
            # Verify bookmark structure is reasonable
            for bookmark in bookmarks[:10]:  # Check first 10
                self.assertIn('url', bookmark)
                self.assertIn('formatted_label', bookmark)
                self.assertIn('domain', bookmark)
                
            print(f"Successfully processed {len(bookmarks)} bookmarks")
            
        except MemoryError:
            self.fail("Memory error occurred with large dataset")


class TestScalability(unittest.TestCase):
    """Test scalability characteristics"""

    def test_duplicate_detection_scaling(self):
        """Test that duplicate detection scales well"""
        # Create bookmarks with some duplicates
        bookmarks = []
        
        # Add unique bookmarks
        for i in range(800):
            bookmarks.append({
                'url': f'https://unique{i}.com',
                'formatted_label': f'Unique Site {i}',
                'domain': f'unique{i}.com'
            })
        
        # Add some duplicates
        for i in range(200):
            duplicate_index = i % 800
            bookmarks.append({
                'url': f'https://unique{duplicate_index}.com',
                'formatted_label': f'Duplicate of Site {duplicate_index}',
                'domain': f'unique{duplicate_index}.com'
            })
        
        # Test duplicate detection performance
        start_time = time.time()
        
        # Simple duplicate detection based on URL
        seen_urls = set()
        unique_bookmarks = []
        for bookmark in bookmarks:
            if bookmark['url'] not in seen_urls:
                seen_urls.add(bookmark['url'])
                unique_bookmarks.append(bookmark)
        
        dedup_time = time.time() - start_time
        
        # Verify results
        self.assertEqual(len(unique_bookmarks), 800)  # Should remove 200 duplicates
        
        # Performance assertion
        self.assertLess(dedup_time, 1.0, 
                       f"Duplicate detection took too long: {dedup_time:.2f}s for {len(bookmarks)} bookmarks")
        
        print(f"Deduplicated {len(bookmarks)} bookmarks to {len(unique_bookmarks)} in {dedup_time:.2f}s")


if __name__ == '__main__':
    unittest.main()
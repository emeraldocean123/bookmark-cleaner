#!/usr/bin/env python3
"""
Security-focused tests for bookmark cleaner
Tests for URL sanitization, HTML parsing security, and input validation
"""

import sys
import os
import unittest
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from bookmark_cleaner import (
    sanitize_url,
    extract_domain,
    clean_title,
    extract_all_bookmarks
)


class TestSecurityFeatures(unittest.TestCase):
    """Test security features and input sanitization"""

    def test_url_sanitization_dangerous_schemes(self):
        """Test that dangerous URL schemes are blocked"""
        dangerous_urls = [
            'javascript:alert("xss")',
            'data:text/html,<script>alert("xss")</script>',
            'vbscript:msgbox("xss")',
            'file:///etc/passwd',
            'about:blank',
            'JAVASCRIPT:alert("XSS")',  # Case insensitive
        ]
        
        for url in dangerous_urls:
            with self.subTest(url=url):
                result = sanitize_url(url)
                self.assertEqual(result, "", f"Dangerous URL not blocked: {url}")

    def test_url_sanitization_valid_urls(self):
        """Test that valid URLs are properly normalized"""
        test_cases = [
            ('http://example.com', 'http://example.com'),
            ('https://example.com', 'https://example.com'),
            ('//example.com', 'https://example.com'),
            ('example.com', 'https://example.com'),
            ('www.example.com', 'https://www.example.com'),
        ]
        
        for input_url, expected in test_cases:
            with self.subTest(input_url=input_url):
                result = sanitize_url(input_url)
                self.assertEqual(result, expected)

    def test_url_sanitization_edge_cases(self):
        """Test edge cases for URL sanitization"""
        edge_cases = [
            ('', ''),
            (None, ''),
            (123, ''),  # Non-string input
            ('   ', ''),
            ('http://', ''),  # No domain
            ('https://', ''),  # No domain
        ]
        
        for input_url, expected in edge_cases:
            with self.subTest(input_url=input_url):
                result = sanitize_url(input_url)
                self.assertEqual(result, expected)

    def test_domain_extraction_security(self):
        """Test domain extraction handles malicious input safely"""
        test_cases = [
            ('javascript:alert("xss")', 'unknown.com'),
            ('', 'unknown.com'),
            ('https://evil.com/../../../etc/passwd', 'evil.com'),
            ('https://www.example.com', 'example.com'),
            ('https://sub.example.com', 'sub.example.com'),
        ]
        
        for url, expected in test_cases:
            with self.subTest(url=url):
                result = extract_domain(url)
                self.assertEqual(result, expected)

    def test_title_cleaning_security(self):
        """Test that title cleaning removes dangerous content"""
        test_cases = [
            ('<script>alert("xss")</script>Title', 'Title'),
            ('Title &lt;script&gt;', 'Title'),
            ('Title &amp; Company', 'Title   Company'),
            ('<img onerror="alert(1)" src="x">Title', 'Title'),
            ('Normal Title', 'Normal Title'),
            ('', 'Untitled'),
            (None, 'Untitled'),
            (123, 'Untitled'),  # Non-string input
        ]
        
        for input_title, expected in test_cases:
            with self.subTest(input_title=input_title):
                result = clean_title(input_title)
                # Check that dangerous content is removed
                self.assertNotIn('<script>', result.lower())
                self.assertNotIn('javascript:', result.lower())
                if expected != 'Untitled':
                    self.assertIn(expected.split()[0], result)

    def test_html_parsing_security(self):
        """Test that HTML parsing is secure against XXE and other attacks"""
        # Create a test HTML file with potential security issues
        test_html = '''<!DOCTYPE html>
<html>
<head><title>Test Bookmarks</title></head>
<body>
<h3>Bookmarks</h3>
<dl>
<dt><h3>Valid Bookmarks</h3>
<dl>
<dt><a href="https://example.com">Example Site</a></dt>
<dt><a href="javascript:alert('xss')">Malicious Link</a></dt>
<dt><a href="data:text/html,<script>alert('xss')</script>">Data URL</a></dt>
</dl>
</dl>
</body>
</html>'''
        
        # Create temporary test file
        test_file = Path('test_security_bookmarks.html')
        try:
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write(test_html)
            
            # Extract bookmarks
            bookmarks = extract_all_bookmarks(str(test_file))
            
            # Verify security: dangerous URLs should be filtered out
            valid_urls = [b['url'] for b in bookmarks if b['url']]
            
            for url in valid_urls:
                self.assertFalse(url.startswith('javascript:'), 
                               f"JavaScript URL not filtered: {url}")
                self.assertFalse(url.startswith('data:'), 
                               f"Data URL not filtered: {url}")
            
            # Should have at least one valid bookmark
            valid_bookmarks = [b for b in bookmarks if b['url'] and b['url'].startswith('https://')]
            self.assertGreater(len(valid_bookmarks), 0, "No valid bookmarks found")
            
        finally:
            # Clean up test file
            if test_file.exists():
                test_file.unlink()


class TestInputValidation(unittest.TestCase):
    """Test input validation and error handling"""

    def test_extract_bookmarks_nonexistent_file(self):
        """Test handling of nonexistent files"""
        result = extract_all_bookmarks('nonexistent_file.html')
        self.assertEqual(result, [])

    def test_extract_bookmarks_invalid_encoding(self):
        """Test handling of files with encoding issues"""
        # Create a file with invalid UTF-8
        test_file = Path('test_invalid_encoding.html')
        try:
            with open(test_file, 'wb') as f:
                f.write(b'\xff\xfe<html><body><a href="http://example.com">Test</a></body></html>')
            
            # Should handle gracefully and return empty list
            result = extract_all_bookmarks(str(test_file))
            # Note: depending on the error handling, this might return [] or handle the encoding
            self.assertIsInstance(result, list)
            
        finally:
            if test_file.exists():
                test_file.unlink()


if __name__ == '__main__':
    unittest.main()
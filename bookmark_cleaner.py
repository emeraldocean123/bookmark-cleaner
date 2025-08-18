#!/usr/bin/env python3
"""
Bookmark Cleaner - Clean labels and preserve folder structure

This script cleans browser bookmarks by:
- Preserving original folder structure
- Cleaning bookmark labels for consistency
- Handling duplicates intelligently
- Optional URL validation
- AI-powered organization assistance
"""

import sys
import os
import subprocess
import importlib.util
from datetime import datetime
import shutil

# Check and install dependencies if needed
def check_and_install_dependencies():
    """Check if dependencies are installed and offer to install them"""
    required_packages = {
        'bs4': 'beautifulsoup4',
        'requests': 'requests',
        'lxml': 'lxml',
        'pyperclip': 'pyperclip'
    }
    
    missing_packages = []
    for module, package in required_packages.items():
        if importlib.util.find_spec(module) is None:
            missing_packages.append(package)
    
    if missing_packages:
        print("⚠️  Missing required packages:")
        for package in missing_packages:
            print(f"  - {package}")
        
        response = input("\n📦 Would you like to install them now? (y/n): ").strip().lower()
        if response.startswith('y'):
            print("\n📥 Installing dependencies...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
                print("✅ Dependencies installed successfully!")
                print("Please restart the script to continue.\n")
                sys.exit(0)
            except subprocess.CalledProcessError:
                print("❌ Failed to install dependencies.")
                print("Please run: pip install -r requirements.txt")
                sys.exit(1)
        else:
            print("\n❌ Cannot proceed without required dependencies.")
            print("Please run: pip install -r requirements.txt")
            sys.exit(1)

# Check dependencies before importing them
check_and_install_dependencies()

# Now import the required modules
from bs4 import BeautifulSoup
import json
import requests
from urllib.parse import urlparse, urlunparse
import re
import time
import argparse
import logging
from typing import Dict, List, Optional, Union, Tuple
import concurrent.futures
import pyperclip
from pathlib import Path
import ssl
import warnings
from urllib3.exceptions import InsecureRequestWarning


# Configuration defaults
DEFAULT_CONFIG = {
    'timeout': 10,
    'max_workers': 10,  # Increased for better performance
    'title_max_length': 60,  # Increased for better readability
    'validation_delay': 0.05,  # Reduced delay for better performance
    'output_dir': 'bookmarks-processed',
    'input_dir': 'bookmarks-input',
    'backup_dir': 'bookmarks-backups',
    'batch_size': 100,  # Process bookmarks in batches
    'max_redirects': 3,  # Limit redirects for security
    'connect_timeout': 5,  # Separate connect timeout
    'read_timeout': 10  # Separate read timeout
}


def setup_logging() -> None:
    """Setup logging configuration with proper encoding"""
    # Clear any existing handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    # Create file handler with UTF-8 encoding
    file_handler = logging.FileHandler('bookmark_cleaner.log', encoding='utf-8')
    
    # Create console handler with proper encoding
    console_handler = logging.StreamHandler(sys.stdout)
    if hasattr(sys.stdout, 'reconfigure'):
        # Python 3.7+ - reconfigure stdout to use UTF-8
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except:
            pass
    
    # Set format for both handlers
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    logging.root.setLevel(logging.INFO)
    logging.root.addHandler(file_handler)
    logging.root.addHandler(console_handler)


def sanitize_url(url: str) -> str:
    """Sanitize and validate URL to prevent security issues"""
    if not url or not isinstance(url, str):
        return ""
    
    # Remove potential XSS attempts and dangerous schemes
    url = url.strip()
    dangerous_schemes = ['javascript:', 'data:', 'vbscript:', 'file:', 'about:']
    url_lower = url.lower()
    
    for scheme in dangerous_schemes:
        if url_lower.startswith(scheme):
            return ""
    
    # Only allow http and https
    if not (url_lower.startswith('http://') or url_lower.startswith('https://')):
        # Try to fix common issues
        if url.startswith('//'):
            url = 'https:' + url
        elif not url.startswith(('http://', 'https://')):
            url = 'https://' + url
    
    try:
        parsed = urlparse(url)
        if not parsed.netloc:
            return ""
        # Reconstruct URL to normalize it
        return urlunparse(parsed)
    except Exception:
        return ""

def extract_domain(url: str) -> str:
    """Extract clean domain name from URL in consistent format"""
    try:
        sanitized = sanitize_url(url)
        if not sanitized:
            return "unknown.com"
        
        parsed = urlparse(sanitized)
        domain = parsed.netloc.lower()
        # Remove www. prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        # Ensure consistent format - always include .com/.org/.net etc
        return domain
    except Exception:
        return "unknown.com"


def clean_title(title: Optional[str], max_length: int = DEFAULT_CONFIG['title_max_length']) -> str:
    """Clean up bookmark title by removing common suffixes and junk"""
    if not title or not isinstance(title, str):
        return "Untitled"
    
    # Escape potential HTML entities and remove dangerous content
    title = re.sub(r'<[^>]*>', '', title)  # Remove HTML tags
    title = re.sub(r'&[a-zA-Z0-9#]+;', ' ', title)  # Remove HTML entities

    # Remove common website suffixes and separators
    cleanup_patterns = [
        r'\s*\|\s*.*$',  # Everything after |
        r'\s*-\s*.*$',   # Everything after -
        r'\s*:\s*.*$',   # Everything after :
        r'\s*\.\.\.$',   # Trailing ...
        r'^\s*',         # Leading whitespace
        r'\s*$',         # Trailing whitespace
    ]

    cleaned = title
    for pattern in cleanup_patterns:
        cleaned = re.sub(pattern, '', cleaned)

    # If we cleaned too much, fall back to original but trim
    if len(cleaned) < 3 and len(title) > len(cleaned):
        cleaned = title.strip()

    # Remove common junk phrases
    junk_phrases = [
        'Welcome to',
        'Official Site',
        'Official Website',
        'Home Page',
        'Homepage',
        'Main Page',
        'Index',
    ]

    for junk in junk_phrases:
        if cleaned.lower().startswith(junk.lower()):
            cleaned = cleaned[len(junk):].strip()

    # Remove trailing periods and other punctuation
    cleaned = re.sub(r'[.,;:]+$', '', cleaned)

    # Limit length to keep it simple
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length-3] + "..."

    return cleaned or "Untitled"


def extract_all_bookmarks(file_path: str) -> List[Dict[str, Union[str, bool, int, None]]]:
    """Extract all bookmarks from HTML file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
    except (UnicodeDecodeError, IOError) as e:
        logging.error(f"Failed to read file {file_path}: {e}")
        return []

    # Use 'html.parser' instead of 'lxml' for better security
    # and to avoid XML entity expansion attacks
    soup = BeautifulSoup(content, 'html.parser')

    # Find all A tags with href attributes
    a_tags = soup.find_all('a', href=True)

    bookmarks = []
    domain_counts = {}

    # First pass: collect all bookmarks and count domains
    for a_tag in a_tags:
        url = a_tag.get('href', '').strip()
        title = a_tag.get_text().strip()

        # Sanitize URL and title
        url = sanitize_url(url)
        title = clean_title(title)

        if url and title:  # Only include if both exist and are valid
            domain = extract_domain(url)
            clean_label = title

            bookmark = {
                'original_title': title,
                'clean_title': clean_label,
                'url': url,
                'domain': domain,
                'icon': a_tag.get('icon'),
                'add_date': a_tag.get('add_date')
            }
            bookmarks.append(bookmark)

            # Count domain occurrences
            domain_counts[domain] = domain_counts.get(domain, 0) + 1

    # Second pass: create formatted labels with unique identifiers
    # for duplicates
    domain_usage = {}
    for bookmark in bookmarks:
        domain = bookmark['domain']

        if domain_counts[domain] > 1:
            # Multiple bookmarks for this domain, need unique labels
            if domain not in domain_usage:
                domain_usage[domain] = []

            # Extract unique identifier from URL path
            unique_part = ""
            try:
                parsed_url = urlparse(bookmark['url'])
                path = parsed_url.path.strip('/')
                excluded = ['index.html', 'index.php']
                path_parts = [p for p in path.split('/')
                              if p and p not in excluded]

                # Check if this is a homepage
                common_paths = ['en', 'us', 'home', 'index']
                is_homepage = (not path_parts or
                               (len(path_parts) == 1 and
                                path_parts[0].lower() in common_paths))

                if is_homepage:
                    unique_part = "Homepage"
                elif 'full-node' in bookmark['url']:
                    unique_part = "Full Node"
                elif 'calculator' in bookmark['url']:
                    unique_part = "Calculator"
                elif len(path_parts) >= 2:
                    part = path_parts[-1]
                    unique_part = part.replace('-', ' ').replace('_', ' ')
                    unique_part = unique_part.title()
                else:
                    part = path_parts[0]
                    unique_part = part.replace('-', ' ').replace('_', ' ')
                    unique_part = unique_part.title()

                # Clean up meaningless parts
                meaningless = ['en', 'us', 'index', 'home', 'main']
                if unique_part.lower() in meaningless:
                    unique_part = "Homepage"

                # Try URL fragment if no good path
                if not unique_part and parsed_url.fragment:
                    fragment = parsed_url.fragment
                    fragment_clean = fragment.replace('-', ' ')
                    fragment_clean = fragment_clean.replace('_', ' ')
                    fragment_title = fragment_clean.title()
                    excluded_fragments = ['en', 'us', 'index', 'home']
                    if fragment_title.lower() not in excluded_fragments:
                        unique_part = fragment_title

            except Exception:
                pass

            # Fallback to clean title if URL extraction failed
            excluded_parts = ['en', 'us', 'index', 'home', 'main', 'page']
            if not unique_part or unique_part.lower() in excluded_parts:
                clean_label = bookmark['clean_title']
                excluded_labels = [domain.split('.')[0], 'en', 'us', 'home',
                                   'homepage', 'main', 'index']
                if clean_label.lower() not in excluded_labels:
                    unique_part = clean_label
                else:
                    orig_words = bookmark['original_title'].split()
                    excluded_words = ['en', 'us', 'home', 'the', 'and', 'or',
                                      'of', 'in', 'to', 'for']
                    meaningful_words = [w for w in orig_words
                                        if w.lower() not in excluded_words]
                    if len(meaningful_words) > 1:
                        unique_part = ' '.join(meaningful_words[:3])
                    else:
                        unique_part = f"Page {len(domain_usage[domain]) + 1}"

            # Ensure uniqueness within this domain
            original_unique = unique_part
            counter = 1
            while unique_part in domain_usage[domain]:
                counter += 1
                unique_part = f"{original_unique} {counter}"

            domain_usage[domain].append(unique_part)
            formatted_label = f"{domain} | {unique_part}"
        else:
            # Single bookmark for this domain
            formatted_label = f"{domain} | {bookmark['clean_title']}"

        bookmark['formatted_label'] = formatted_label

    return bookmarks


def create_html_with_clean_labels(original_file, bookmarks):
    """Create HTML maintaining structure but with cleaned labels and removed duplicates"""
    with open(original_file, 'r', encoding='utf-8') as file:
        content = file.read()

    # Create a set of URLs to keep and their labels
    urls_to_keep = {b['url'] for b in bookmarks}
    bookmark_lookup = {b['url']: b['formatted_label'] for b in bookmarks}
    
    # Debug: Keeping unique URLs from bookmarks

    soup = BeautifulSoup(content, 'html.parser')

    # Track seen URLs to handle duplicates in the original HTML
    seen_urls = set()
    removed_count = 0
    
    # Find all bookmark A tags and process them
    # We need to collect them first to avoid modifying while iterating
    # Only process actual bookmarks, not folder headers
    a_tags = []
    for dt in soup.find_all('dt'):
        # Skip if this is a folder (has H3 child)
        if dt.find('h3'):
            continue
        a_tag = dt.find('a', href=True)
        if a_tag:
            a_tags.append((a_tag, dt))
    
    tags_to_remove = []
    
    for a_tag, parent_dt in a_tags:
        url = a_tag.get('href', '').strip()
        
        if url not in urls_to_keep:
            # This URL was removed during deduplication - remove from HTML
            tags_to_remove.append(parent_dt)
        elif url in seen_urls:
            # This is a duplicate in the original HTML - remove it
            tags_to_remove.append(parent_dt)
        else:
            # First occurrence of a kept URL - update label
            seen_urls.add(url)
            if url in bookmark_lookup:
                a_tag.string = bookmark_lookup[url]
    
    # Now remove the duplicate entries
    for dt in tags_to_remove:
        dt.decompose()
        removed_count += 1

    # Debug: Removed duplicate bookmark entries from HTML

    # Add comment about cleaning and duplicate removal
    comment_text = f'<!-- Bookmark labels cleaned and {removed_count} duplicates removed by Bookmark Cleaner -->'
    comment = soup.new_string(comment_text)
    if soup.find('meta'):
        soup.find('meta').insert_after(comment)

    return str(soup)


def validate_bookmark(bookmark: Dict[str, Union[str, bool, int, None]], 
                      session: requests.Session, 
                      timeout: int = DEFAULT_CONFIG['timeout']) -> Dict[str, Union[str, bool, int, None]]:
    """Validate a single bookmark with security measures"""
    url = bookmark.get('url', '')
    
    # Re-sanitize URL before validation
    url = sanitize_url(url)
    if not url:
        bookmark['is_valid'] = False
        bookmark['status_code'] = None
        bookmark['error'] = 'Invalid or dangerous URL'
        return bookmark
    
    # Update bookmark with sanitized URL
    bookmark['url'] = url
    
    try:
        # Try HEAD request first (more efficient and safer)
        response = session.head(url, timeout=timeout, allow_redirects=True, stream=False)
        bookmark['is_valid'] = True
        bookmark['status_code'] = response.status_code
        return bookmark
    except requests.exceptions.SSLError as e:
        bookmark['is_valid'] = False
        bookmark['status_code'] = None
        bookmark['error'] = f'SSL Error: {str(e)[:100]}'
        return bookmark
    except requests.exceptions.Timeout:
        bookmark['is_valid'] = False
        bookmark['status_code'] = None
        bookmark['error'] = 'Request timeout'
        return bookmark
    except requests.exceptions.ConnectionError:
        bookmark['is_valid'] = False
        bookmark['status_code'] = None
        bookmark['error'] = 'Connection error'
        return bookmark
    except Exception as e:
        try:
            # Fallback to GET request with limited response size
            response = session.get(url, timeout=timeout, allow_redirects=True, 
                                 stream=True, headers={'Range': 'bytes=0-1024'})
            bookmark['is_valid'] = True
            bookmark['status_code'] = response.status_code
            response.close()  # Close connection immediately
            return bookmark
        except Exception as e2:
            bookmark['is_valid'] = False
            bookmark['status_code'] = None
            bookmark['error'] = f'Validation failed: {str(e2)[:100]}'
            return bookmark


def validate_bookmarks_concurrent(bookmarks: List[Dict[str, Union[str, bool, int, None]]], 
                                  max_workers: int = DEFAULT_CONFIG['max_workers']) -> List[Dict[str, Union[str, bool, int, None]]]:
    """Validate all bookmarks concurrently for better performance"""
    session = requests.Session()
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    
    # Configure secure session
    session.headers.update({
        'User-Agent': user_agent,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    })
    
    # Configure SSL/TLS settings for security
    session.verify = True  # Always verify SSL certificates
    
    # Suppress only specific warnings, not all SSL warnings
    warnings.filterwarnings('ignore', category=InsecureRequestWarning)

    print(f"🔍 Validating {len(bookmarks)} bookmarks using {max_workers} concurrent workers...")

    validated = []
    completed_count = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all bookmark validation tasks
        future_to_bookmark = {
            executor.submit(validate_bookmark, bookmark.copy(), session): bookmark 
            for bookmark in bookmarks
        }
        
        # Process completed tasks
        for future in concurrent.futures.as_completed(future_to_bookmark):
            validated_bookmark = future.result()
            validated.append(validated_bookmark)
            completed_count += 1
            
            status = "✓" if validated_bookmark['is_valid'] else "✗"
            label = validated_bookmark['formatted_label'][:50]
            print(f"[{completed_count}/{len(bookmarks)}] {status} {label}...")
            
            # Small delay to be respectful to servers
            time.sleep(DEFAULT_CONFIG['validation_delay'])

    return validated


def validate_bookmarks_sequential(bookmarks: List[Dict[str, Union[str, bool, int, None]]], 
                                  max_workers: int = DEFAULT_CONFIG['max_workers']) -> List[Dict[str, Union[str, bool, int, None]]]:
    """Validate all bookmarks sequentially (legacy method)"""
    session = requests.Session()
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    
    # Configure secure session
    session.headers.update({
        'User-Agent': user_agent,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    })
    
    # Configure SSL/TLS settings for security
    session.verify = True  # Always verify SSL certificates

    print(f"🔍 Validating {len(bookmarks)} bookmarks sequentially...")

    validated = []
    for i, bookmark in enumerate(bookmarks):
        validated_bookmark = validate_bookmark(bookmark, session)
        validated.append(validated_bookmark)
        status = "✓" if validated_bookmark['is_valid'] else "✗"
        label = bookmark['formatted_label'][:50]
        print(f"[{i+1}/{len(bookmarks)}] {status} {label}...")
        time.sleep(DEFAULT_CONFIG['validation_delay'])  # Be nice to servers

    return validated


def generate_ai_instructions() -> str:
    """Generate comprehensive instructions for AI to reorganize bookmarks"""
    return """# AI Bookmark Organization Instructions

You are helping reorganize browser bookmarks into a logical folder structure. 

## Your Task:
1. Analyze the provided bookmarks list
2. Group bookmarks into logical categories/folders
3. Create a hierarchical folder structure that makes sense
4. Output in the EXACT format specified below

## Output Format:
Use this EXACT structure (maintain spacing and symbols):

```
FOLDER: Work & Professional
  github.com | GitHub Homepage
  linkedin.com | LinkedIn Profile
  
  FOLDER: Development Tools
    stackoverflow.com | Stack Overflow
    developer.mozilla.org | MDN Web Docs
  
FOLDER: Entertainment & Media
  youtube.com | YouTube
  netflix.com | Netflix
  
  FOLDER: News & Articles
    bbc.com | BBC News
    reuters.com | Reuters
```

## Formatting Rules:
- Use "FOLDER: Name" for folders (with colon)
- Indent bookmarks with 2 spaces under their folder
- Indent subfolders with 2 spaces, bookmarks under subfolders with 4 spaces  
- Keep bookmark format: "domain | title"
- Use descriptive folder names (Work, Entertainment, Tech, etc.)
- Create max 3 levels deep (Main Folder > Subfolder > Bookmarks)
- Group similar sites together logically

## Guidelines:
- Create 5-10 main categories maximum
- Use subcategories for better organization
- Keep folder names clear and intuitive
- Group by purpose/topic, not just domain
- Consider user workflow and access patterns

Please organize the following bookmarks:

"""


def export_bookmarks_for_ai(bookmarks: List[Dict[str, Union[str, bool, int, None]]]) -> str:
    """Export bookmarks in AI-ready format with instructions"""
    ai_instructions = generate_ai_instructions()
    
    bookmark_list = []
    for bookmark in bookmarks:
        bookmark_list.append(f"{bookmark['formatted_label']}")
    
    return ai_instructions + "\n".join(bookmark_list)


def export_bookmarks_flattened(bookmarks: List[Dict[str, Union[str, bool, int, None]]]) -> str:
    """Export bookmarks as flat list"""
    output = ["# Flattened Bookmarks List", ""]
    
    for bookmark in bookmarks:
        output.append(f"{bookmark['formatted_label']}")
    
    return "\n".join(output)


def extract_folder_structure_from_html(file_path: str) -> Dict[str, List[Dict]]:
    """Extract original folder structure from HTML bookmarks"""
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    folder_structure = {"root": []}
    
    def parse_dl(dl_element, current_path="root"):
        """Recursively parse DL elements to extract folder structure"""
        current_list = folder_structure.setdefault(current_path, [])
        
        for child in dl_element.children:
            if hasattr(child, 'name'):
                if child.name == 'dt':
                    # Check if this is a folder (has H3) or bookmark (has A)
                    h3_element = child.find('h3')
                    a_element = child.find('a', href=True)
                    
                    if h3_element:
                        # This is a folder
                        folder_name = h3_element.get_text().strip()
                        folder_path = f"{current_path}/{folder_name}" if current_path != "root" else folder_name
                        current_list.append({"type": "folder", "name": folder_name, "path": folder_path})
                        
                        # Look for next sibling DD with nested DL
                        next_sibling = child.find_next_sibling('dd')
                        if next_sibling:
                            nested_dl = next_sibling.find('dl')
                            if nested_dl:
                                parse_dl(nested_dl, folder_path)
                    
                    elif a_element:
                        # This is a bookmark
                        url = a_element.get('href', '').strip()
                        title = a_element.get_text().strip()
                        if url and title:
                            current_list.append({
                                "type": "bookmark",
                                "url": url,
                                "title": title,
                                "path": current_path
                            })
    
    # Find the main bookmark structure
    main_dl = soup.find('dl')
    if main_dl:
        parse_dl(main_dl)
    
    return folder_structure


def export_bookmarks_preserve_structure(file_path: str, bookmarks: List[Dict[str, Union[str, bool, int, None]]]) -> str:
    """Export bookmarks preserving original folder structure"""
    folder_structure = extract_folder_structure_from_html(file_path)
    
    # Create lookup for clean labels
    bookmark_lookup = {b['url']: b['formatted_label'] for b in bookmarks}
    
    output = ["# Bookmarks with Original Structure Preserved", ""]
    
    def format_structure(items, indent_level=0):
        indent = "  " * indent_level
        result = []
        
        for item in items:
            if item["type"] == "folder":
                result.append(f"{indent}FOLDER: {item['name']}")
                # Get items in this folder
                folder_items = folder_structure.get(item["path"], [])
                if folder_items:
                    result.extend(format_structure(folder_items, indent_level + 1))
            elif item["type"] == "bookmark":
                clean_label = bookmark_lookup.get(item["url"], f"{extract_domain(item['url'])} | {clean_title(item['title'])}")
                result.append(f"{indent}{clean_label}")
        
        return result
    
    # Format root level items
    if "root" in folder_structure:
        output.extend(format_structure(folder_structure["root"]))
    
    return "\n".join(output)


def import_ai_organized_bookmarks(ai_content: str) -> Tuple[Dict, List[Dict]]:
    """Parse AI-organized bookmark content back into structure
    
    Expected format:
    - Root folders: 0 spaces, "FOLDER: Name"
    - Root bookmarks: 2 spaces, "domain | title"
    - Sub-folders: 2 spaces, "FOLDER: Name"
    - Sub-bookmarks: 4 spaces, "domain | title"
    - Sub-sub-folders: 4 spaces, "FOLDER: Name"
    - Sub-sub-bookmarks: 6 spaces, "domain | title"
    """
    lines = ai_content.strip().split('\n')
    folder_structure = {}
    all_bookmarks = []
    folder_stack = []  # Track current folder hierarchy
    
    print(f"Parsing AI file: {len(lines)} lines")
    
    for line_num, line in enumerate(lines, 1):
        original_line = line
        line = line.rstrip()
        if not line:
            continue
            
        # Count actual spaces for indentation
        leading_spaces = len(line) - len(line.lstrip())
        content = line.strip()
        
        if content.startswith('FOLDER:'):
            folder_name = content[7:].strip()
            
            # Determine folder level based on indentation
            # 0 spaces = root level, 2 spaces = level 1, 4 spaces = level 2, etc.
            folder_level = leading_spaces // 2
            
            # Adjust folder stack to current level
            if folder_level == 0:
                # Root level folder
                folder_stack = [folder_name]
            elif folder_level == 1:
                # Sub-folder under root
                if len(folder_stack) >= 1:
                    folder_stack = folder_stack[:1] + [folder_name]
                else:
                    # No root folder yet, treat as root
                    folder_stack = [folder_name]
            elif folder_level >= 2:
                # Sub-sub-folder or deeper
                target_level = min(folder_level, 2)  # Max 3 levels
                if len(folder_stack) > target_level:
                    folder_stack = folder_stack[:target_level] + [folder_name]
                else:
                    # Extend stack to target level
                    while len(folder_stack) < target_level:
                        folder_stack.append("Unknown")
                    folder_stack.append(folder_name)
            
            folder_path = "/".join(folder_stack)
            if folder_path not in folder_structure:
                folder_structure[folder_path] = []
            
            print(f"  FOLDER Line {line_num} (spaces:{leading_spaces}, level:{folder_level}): {folder_path}")
                
        elif ' | ' in content and not content.startswith('#'):
            # This is a bookmark
            parts = content.split(' | ', 1)
            if len(parts) == 2:
                domain, title = parts
                
                # Determine which folder this bookmark belongs to based on indentation
                # 2 spaces = root folder bookmark, 4 spaces = sub-folder bookmark, etc.
                bookmark_level = leading_spaces // 2
                
                # Assign to appropriate folder
                if bookmark_level == 0:
                    # Should not happen for bookmarks, but handle gracefully
                    current_folder = folder_stack[0] if folder_stack else "root"
                elif bookmark_level == 1:
                    # Bookmark under root folder (2 spaces)
                    current_folder = folder_stack[0] if folder_stack else "root"
                elif bookmark_level == 2:
                    # Bookmark under sub-folder (4 spaces)
                    if len(folder_stack) >= 2:
                        current_folder = "/".join(folder_stack[:2])
                    elif len(folder_stack) == 1:
                        current_folder = folder_stack[0]
                    else:
                        current_folder = "root"
                else:
                    # Deeper levels (6+ spaces)
                    # Use the deepest folder available
                    current_folder = "/".join(folder_stack) if folder_stack else "root"
                
                bookmark = {
                    "domain": domain.strip(),
                    "title": title.strip(),
                    "folder_path": current_folder,
                    "formatted_label": content
                }
                
                all_bookmarks.append(bookmark)
                folder_structure.setdefault(current_folder, []).append(bookmark)
                
                print(f"  BOOKMARK Line {line_num} (spaces:{leading_spaces}): {domain.strip()[:30]}... -> {current_folder}")
        
        else:
            print(f"  SKIPPING Line {line_num}: '{content[:50]}...'")
    
    print(f"Parsing complete: {len(folder_structure)} folders, {len(all_bookmarks)} bookmarks")
    return folder_structure, all_bookmarks


def create_html_from_ai_structure(folder_structure: Dict, original_bookmarks: List[Dict], output_path: str) -> None:
    """Create HTML bookmark file from AI-organized structure"""
    # Create multiple lookup methods for better matching
    bookmark_lookup = {b['formatted_label']: b for b in original_bookmarks}
    
    # Also create lookups by domain for fallback matching
    domain_lookup = {}
    for b in original_bookmarks:
        domain = b['domain']
        if domain not in domain_lookup:
            domain_lookup[domain] = []
        domain_lookup[domain].append(b)
    
    # Create Edge-compatible structure with Favorites bar
    favorites_timestamp = str(int(time.time()))
    html_content = f"""<!DOCTYPE NETSCAPE-Bookmark-file-1>
<!-- This is an automatically generated file.
     It will be read and overwritten.
     DO NOT EDIT! -->
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
<DL><p>
    <DT><H3 ADD_DATE="{favorites_timestamp}" LAST_MODIFIED="0" PERSONAL_TOOLBAR_FOLDER="true">Favorites bar</H3>
    <DL><p>
"""
    
    def generate_folder_html(folder_path: str, indent_level: int = 1) -> str:
        indent = "    " * indent_level
        folder_html = ""
        
        # Get items in this folder
        items = folder_structure.get(folder_path, [])
        if not items:
            return ""
        
        # Group items by type
        folders = []
        bookmarks = []
        
        for item in items:
            if isinstance(item, dict) and 'formatted_label' in item:
                bookmarks.append(item)
        
        # Find subfolders
        subfolders = [key for key in folder_structure.keys() if key.startswith(f"{folder_path}/") and key.count('/') == folder_path.count('/') + 1]
        for subfolder in subfolders:
            if subfolder not in folders:
                folders.append(subfolder)
        
        # Generate bookmarks first
        for bookmark in bookmarks:
            original = bookmark_lookup.get(bookmark['formatted_label'])
            
            # If exact match not found, try to find by domain
            if not original and bookmark.get('domain'):
                domain = bookmark['domain']
                if domain in domain_lookup:
                    # Try to find best match by comparing titles
                    candidates = domain_lookup[domain]
                    if len(candidates) == 1:
                        original = candidates[0]
                    else:
                        # Try to match by partial title
                        bookmark_title = bookmark.get('title', '').lower()
                        for candidate in candidates:
                            if bookmark_title in candidate.get('clean_title', '').lower() or \
                               bookmark_title in candidate.get('original_title', '').lower():
                                original = candidate
                                break
                        # If still no match, use first candidate
                        if not original and candidates:
                            original = candidates[0]
            
            if original:
                folder_html += f'{indent}<DT><A HREF="{original["url"]}"'
                if original.get('add_date'):
                    folder_html += f' ADD_DATE="{original["add_date"]}"'
                if original.get('icon'):
                    folder_html += f' ICON="{original["icon"]}"'
                # Use the AI's label to preserve any edits made
                folder_html += f'>{bookmark["formatted_label"]}</A>\n'
            else:
                # If no original found, create a basic bookmark with just the domain as URL
                domain = bookmark.get('domain', 'unknown.com')
                if not domain.startswith('http'):
                    url = f'https://{domain}'
                else:
                    url = domain
                folder_html += f'{indent}<DT><A HREF="{url}">{bookmark["formatted_label"]}</A>\n'
        
        # Generate subfolders with proper Edge format
        for subfolder_path in folders:
            if subfolder_path in folder_structure:
                folder_name = subfolder_path.split('/')[-1]
                # Add timestamps for Edge compatibility
                timestamp = str(int(time.time()))
                folder_html += f'{indent}<DT><H3 ADD_DATE="{timestamp}" LAST_MODIFIED="{timestamp}">{folder_name}</H3>\n'
                folder_html += f'{indent}<DL><p>\n'
                folder_html += generate_folder_html(subfolder_path, indent_level + 1)
                folder_html += f'{indent}</DL><p>\n'
        
        return folder_html
    
    # Generate root level and all folders with proper Edge structure
    # Now nested under Favorites bar, so use 2 levels of indentation
    for folder_path in sorted(folder_structure.keys()):
        if '/' not in folder_path and folder_path != 'root':
            # This is a top-level folder under Favorites bar
            folder_name = folder_path
            timestamp = str(int(time.time()))
            html_content += f'        <DT><H3 ADD_DATE="{timestamp}" LAST_MODIFIED="{timestamp}">{folder_name}</H3>\n'
            html_content += f'        <DL><p>\n'
            html_content += generate_folder_html(folder_path, 3)
            html_content += f'        </DL><p>\n'
    
    # Add root level bookmarks
    if 'root' in folder_structure:
        root_items = folder_structure['root']
        for item in root_items:
            if isinstance(item, dict) and 'formatted_label' in item:
                original = bookmark_lookup.get(item['formatted_label'])
                
                # If exact match not found, try to find by domain
                if not original and item.get('domain'):
                    domain = item['domain']
                    if domain in domain_lookup:
                        candidates = domain_lookup[domain]
                        if len(candidates) == 1:
                            original = candidates[0]
                        else:
                            # Try to match by partial title
                            item_title = item.get('title', '').lower()
                            for candidate in candidates:
                                if item_title in candidate.get('clean_title', '').lower() or \
                                   item_title in candidate.get('original_title', '').lower():
                                    original = candidate
                                    break
                            if not original and candidates:
                                original = candidates[0]
                
                if original:
                    html_content += f'        <DT><A HREF="{original["url"]}"'
                    if original.get('add_date'):
                        html_content += f' ADD_DATE="{original["add_date"]}"'
                    if original.get('icon'):
                        html_content += f' ICON="{original["icon"]}"'
                    html_content += f'>{item["formatted_label"]}</A>\n'
                else:
                    # Create basic bookmark with domain as URL
                    domain = item.get('domain', 'unknown.com')
                    if not domain.startswith('http'):
                        url = f'https://{domain}'
                    else:
                        url = domain
                    html_content += f'        <DT><A HREF="{url}">{item["formatted_label"]}</A>\n'
    
    # Close the Favorites bar structure
    html_content += "    </DL><p>\n"  # Close Favorites bar content
    html_content += "</DL><p>"         # Close main DL
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)


def handle_export_workflow(bookmarks: List[Dict[str, Union[str, bool, int, None]]], 
                          original_file: str, args: argparse.Namespace, 
                          job_folder: Optional[str] = None) -> None:
    """Handle the export workflow based on selected format"""
    print("\n🤖 AI-Powered Bookmark Organization")
    print("=" * 50)
    
    export_options = [
        "1. Preserve original folder structure",
        "2. Flatten all bookmarks (no folders)", 
        "3. Prepare for AI organization (with instructions)"
    ]
    
    print("Choose export format:")
    for option in export_options:
        print(f"  {option}")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        content = export_bookmarks_preserve_structure(original_file, bookmarks)
        filename = "bookmarks_structured.txt"
    elif choice == "2":
        content = export_bookmarks_flattened(bookmarks)
        filename = "bookmarks_flattened.txt"
    elif choice == "3":
        content = export_bookmarks_for_ai(bookmarks)
        filename = "bookmarks_for_ai.txt"
    else:
        print("❌ Invalid choice")
        return
    
    # Create job folder if not provided
    if not job_folder:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        original_name = Path(original_file).stem
        job_folder = f"job_{timestamp}_{original_name}"
    
    # Save to AI export directory with job folder
    export_dir = os.path.join(args.output_dir, "ai-export", job_folder)
    os.makedirs(export_dir, exist_ok=True)
    
    output_path = os.path.join(export_dir, filename)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\n✅ Exported to: {output_path}")
    
    # Offer clipboard option
    try:
        copy_choice = input("\n📋 Copy to clipboard for easy AI sharing? (y/n): ").strip().lower()
        if copy_choice.startswith('y'):
            pyperclip.copy(content)
            print("✅ Content copied to clipboard!")
    except ImportError:
        print("ℹ️  pyperclip not available for clipboard functionality")
    except Exception as e:
        print(f"⚠️  Clipboard copy failed: {e}")
    
    if choice == "3":
        print("\n🔄 Next Steps:")
        print("1. Share the content with an AI (Claude, ChatGPT, etc.)")
        print("2. Ask the AI to organize your bookmarks")
        print("3. Copy the AI's organized response")
        print("4. Use --import-ai flag to create new bookmark file")
        print("\nExample AI prompt:")
        print("'Please organize these bookmarks into logical folders following the format provided.'")


def handle_ai_import(args: argparse.Namespace) -> None:
    """Handle importing AI-organized bookmarks"""
    print("\nImport AI-Organized Bookmarks")
    print("=" * 40)
    
    # Get AI content
    ai_file = input("Enter path to AI-organized file (or press Enter to paste): ").strip()
    # Remove quotes if present
    if ai_file and ai_file[0] in ('"', "'") and ai_file[-1] in ('"', "'"):
        ai_file = ai_file[1:-1]
    
    if ai_file:
        if not os.path.exists(ai_file):
            print(f"ERROR: File not found: {ai_file}")
            return
        with open(ai_file, 'r', encoding='utf-8') as f:
            ai_content = f.read()
    else:
        print("Paste the AI-organized content (press Ctrl+D when done):")
        lines = []
        try:
            while True:
                line = input()
                lines.append(line)
        except EOFError:
            ai_content = '\n'.join(lines)
    
    if not ai_content.strip():
        print("ERROR: No content provided")
        return
    
    try:
        # Parse AI content
        folder_structure, organized_bookmarks = import_ai_organized_bookmarks(ai_content)
        
        print(f"\nParsed {len(organized_bookmarks)} bookmarks into {len(folder_structure)} folders")
        
        # Load original bookmarks for metadata
        original_file = input("Enter path to original bookmarks file: ").strip()
        # Remove quotes if present
        if original_file and original_file[0] in ('"', "'") and original_file[-1] in ('"', "'"):
            original_file = original_file[1:-1]
        if not os.path.exists(original_file):
            print(f"ERROR: Original file not found: {original_file}")
            return
            
        original_bookmarks = extract_all_bookmarks(original_file)
        
        # Create timestamped job folder for AI organized output
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        original_name = Path(original_file).stem
        job_folder = f"job_{timestamp}_{original_name}_ai_organized"
        
        ai_organized_dir = os.path.join(args.output_dir, "ai-organized", job_folder)
        os.makedirs(ai_organized_dir, exist_ok=True)
        
        output_path = os.path.join(ai_organized_dir, f"{original_name}_ai_organized.html")
        create_html_from_ai_structure(folder_structure, original_bookmarks, output_path)
        
        print(f"SUCCESS: Created organized bookmark file: {output_path}")
        print("You can now import this file into your browser!")
        
    except Exception as e:
        logging.error(f"Failed to import AI content: {e}")
        print(f"ERROR: Failed to parse AI content: {e}")


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Clean browser bookmarks and organize them with AI assistance',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Basic cleaning
  python bookmark_cleaner.py bookmarks.html
  
  # Clean and export for AI organization
  python bookmark_cleaner.py bookmarks.html --ai-export
  
  # Import AI-organized bookmarks
  python bookmark_cleaner.py --import-ai
  
  # Advanced options
  python bookmark_cleaner.py bookmarks.html --validate --concurrent --max-workers 10
        '''
    )
    
    parser.add_argument('input_file', nargs='?', 
                       help='Path to bookmarks HTML file')
    parser.add_argument('--output-dir', default=DEFAULT_CONFIG['output_dir'],
                       help=f'Output directory (default: {DEFAULT_CONFIG["output_dir"]})')
    
    # AI-powered organization options
    parser.add_argument('--ai-export', action='store_true',
                       help='Export bookmarks for AI organization (interactive menu)')
    parser.add_argument('--import-ai', action='store_true',
                       help='Import AI-organized bookmarks from file or clipboard')
    
    # URL validation options  
    parser.add_argument('--validate', action='store_true',
                       help='Validate all URLs (skip interactive prompt)')
    parser.add_argument('--no-validate', action='store_true',
                       help='Skip URL validation (skip interactive prompt)')
    parser.add_argument('--concurrent', action='store_true',
                       help='Use concurrent validation for better performance')
    parser.add_argument('--max-workers', type=int, default=DEFAULT_CONFIG['max_workers'],
                       help=f'Number of concurrent workers (default: {DEFAULT_CONFIG["max_workers"]})')
    parser.add_argument('--timeout', type=int, default=DEFAULT_CONFIG['timeout'],
                       help=f'Request timeout in seconds (default: {DEFAULT_CONFIG["timeout"]})')
    
    # General options
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--no-backup', action='store_true',
                       help='Skip creating backup (not recommended)')
    parser.add_argument('--backup-dir', type=str,
                       help='Custom directory for backup files')
    # Duplicate removal options
    parser.add_argument('--remove-duplicates', action='store_true',
                       help='Remove exact URL duplicates (keeps first occurrence)')
    parser.add_argument('--duplicate-strategy', choices=['url', 'title', 'smart', 'fuzzy'], 
                       default='url', help='Strategy for duplicate detection (default: url)')
    parser.add_argument('--similarity-threshold', type=float, default=0.85, 
                       help='Similarity threshold for fuzzy matching (0.0-1.0, default: 0.85)')
    parser.add_argument('--keep-strategy', choices=['first', 'last', 'shortest', 'longest'], 
                       default='first', help='Which duplicate to keep (default: first)')
    parser.add_argument('--duplicate-report', action='store_true',
                       help='Generate detailed duplicate analysis report')
    
    return parser.parse_args()


def create_backup(file_path: str, custom_location: Optional[str] = None) -> str:
    """Create a backup of the bookmark file before processing
    
    Args:
        file_path: Path to the original bookmark file
        custom_location: Optional custom backup directory
        
    Returns:
        Path to the backup file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    original_name = Path(file_path).stem
    backup_name = f"{original_name}_backup_{timestamp}.html"
    
    if custom_location:
        # Use custom location
        backup_dir = Path(custom_location)
        if not backup_dir.exists():
            backup_dir.mkdir(parents=True, exist_ok=True)
    else:
        # Use default backup directory
        backup_dir = Path(DEFAULT_CONFIG['backup_dir'])
        if not backup_dir.exists():
            backup_dir.mkdir(parents=True, exist_ok=True)
    
    backup_path = backup_dir / backup_name
    
    try:
        shutil.copy2(file_path, backup_path)
        print(f"\n💾 Backup created successfully!")
        print(f"   Location: {backup_path}")
        print(f"   Size: {os.path.getsize(backup_path):,} bytes")
        return str(backup_path)
    except Exception as e:
        print(f"⚠️  Warning: Could not create backup: {e}")
        response = input("Continue without backup? (y/n): ").strip().lower()
        if not response.startswith('y'):
            print("❌ Operation cancelled.")
            sys.exit(1)
        return None


def prompt_for_backup(file_path: str) -> str:
    """Prompt user for backup options
    
    Args:
        file_path: Path to the original bookmark file
        
    Returns:
        Path to the backup file
    """
    print("\n📂 Backup Options:")
    print("1. Save backup in same directory as bookmark file (default)")
    print("2. Choose custom backup location")
    print("3. Skip backup (not recommended)")
    
    choice = input("\nEnter choice (1-3) or press Enter for default: ").strip() or "1"
    
    if choice == "1" or choice == "":
        return create_backup(file_path)
    elif choice == "2":
        custom_location = input("Enter backup directory path: ").strip()
        # Remove quotes if present
        if custom_location and custom_location[0] in ('"', "'") and custom_location[-1] in ('"', "'"):
            custom_location = custom_location[1:-1]
        if not custom_location:
            print("Using same directory as bookmark file.")
            return create_backup(file_path)
        return create_backup(file_path, custom_location)
    elif choice == "3":
        response = input("⚠️  Are you sure you want to proceed without backup? (y/n): ").strip().lower()
        if response.startswith('y'):
            return None
        else:
            print("Creating backup in same directory...")
            return create_backup(file_path)
    else:
        print("Invalid choice. Using default option...")
        return create_backup(file_path)


def process_bookmarks(file_path: str) -> List[Dict[str, Union[str, bool, int, None]]]:
    """Extract and clean bookmarks from HTML file"""
    print("Extracting bookmarks and cleaning labels...")
    bookmarks = extract_all_bookmarks(file_path)
    print(f"Found {len(bookmarks)} bookmarks")
    print("Cleaned labels and handled duplicates")
    
    return bookmarks


def show_cleaning_examples(bookmarks: List[Dict[str, Union[str, bool, int, None]]], count: int = 5) -> None:
    """Show examples of cleaned labels"""
    print("\nLabel Cleaning Examples:")
    for i, bookmark in enumerate(bookmarks[:count]):
        print(f"  Original: {bookmark['original_title'][:60]}...")
        print(f"  Cleaned:  {bookmark['formatted_label']}")
        print()


def normalize_url(url: str) -> str:
    """Normalize URL for duplicate detection"""
    if not url:
        return ""
    
    # Remove common URL variations
    url = url.lower().strip()
    
    # Remove trailing slashes
    if url.endswith('/'):
        url = url[:-1]
    
    # Remove www prefix
    if url.startswith('http://www.'):
        url = url.replace('http://www.', 'http://', 1)
    elif url.startswith('https://www.'):
        url = url.replace('https://www.', 'https://', 1)
    
    # Remove common tracking parameters
    tracking_params = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
                      'fbclid', 'gclid', '_ga', 'ref', 'source', 'campaign']
    
    if '?' in url:
        base_url, params = url.split('?', 1)
        param_pairs = params.split('&')
        clean_params = []
        
        for param in param_pairs:
            if '=' in param:
                key = param.split('=')[0]
                if key not in tracking_params:
                    clean_params.append(param)
        
        if clean_params:
            url = base_url + '?' + '&'.join(clean_params)
        else:
            url = base_url
    
    return url


def calculate_title_similarity(title1: str, title2: str) -> float:
    """Calculate similarity between two titles using simple algorithms"""
    # Handle None inputs
    if title1 is None:
        title1 = ""
    if title2 is None:
        title2 = ""
    
    # Normalize titles
    t1 = title1.lower().strip()
    t2 = title2.lower().strip()
    
    # Both empty strings are identical
    if not t1 and not t2:
        return 1.0
    
    # One empty, one non-empty
    if not t1 or not t2:
        return 0.0
    
    # Exact match
    if t1 == t2:
        return 1.0
    
    # Calculate Jaccard similarity based on words
    words1 = set(t1.split())
    words2 = set(t2.split())
    
    if not words1 and not words2:
        return 1.0
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union)


def calculate_levenshtein_ratio(s1: str, s2: str) -> float:
    """Calculate Levenshtein distance ratio between two strings"""
    if not s1 and not s2:
        return 1.0
    if not s1 or not s2:
        return 0.0
    
    if len(s1) < len(s2):
        s1, s2 = s2, s1
    
    if len(s2) == 0:
        return 0.0
    
    # Create matrix
    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    distance = previous_row[-1]
    max_len = max(len(s1), len(s2))
    return (max_len - distance) / max_len


class DuplicateDetector:
    """Advanced duplicate detection with multiple strategies"""
    
    def __init__(self, strategy: str = 'url', similarity_threshold: float = 0.85, 
                 keep_strategy: str = 'first'):
        self.strategy = strategy
        self.similarity_threshold = similarity_threshold
        self.keep_strategy = keep_strategy
        self.duplicate_groups = []
        self.removed_count = 0
    
    def detect_duplicates(self, bookmarks: List[Dict[str, Union[str, bool, int, None]]]) -> List[Dict[str, Union[str, bool, int, None]]]:
        """Detect and remove duplicates based on selected strategy"""
        if self.strategy == 'url':
            return self._remove_url_duplicates(bookmarks)
        elif self.strategy == 'title':
            return self._remove_title_duplicates(bookmarks)
        elif self.strategy == 'smart':
            return self._remove_smart_duplicates(bookmarks)
        elif self.strategy == 'fuzzy':
            return self._remove_fuzzy_duplicates(bookmarks)
        else:
            return bookmarks
    
    def _remove_url_duplicates(self, bookmarks: List[Dict[str, Union[str, bool, int, None]]]) -> List[Dict[str, Union[str, bool, int, None]]]:
        """Remove bookmarks with duplicate URLs"""
        seen_urls = {}
        duplicate_groups = []
        
        for i, bookmark in enumerate(bookmarks):
            normalized_url = normalize_url(bookmark['url'])
            
            if normalized_url in seen_urls:
                # Found duplicate
                original_index = seen_urls[normalized_url]
                duplicate_groups.append([original_index, i])
            else:
                seen_urls[normalized_url] = i
        
        return self._apply_keep_strategy(bookmarks, duplicate_groups)
    
    def _remove_title_duplicates(self, bookmarks: List[Dict[str, Union[str, bool, int, None]]]) -> List[Dict[str, Union[str, bool, int, None]]]:
        """Remove bookmarks with identical titles"""
        seen_titles = {}
        duplicate_groups = []
        
        for i, bookmark in enumerate(bookmarks):
            title = bookmark.get('formatted_label', '').lower().strip()
            
            if title and title in seen_titles:
                original_index = seen_titles[title]
                duplicate_groups.append([original_index, i])
            elif title:
                seen_titles[title] = i
        
        return self._apply_keep_strategy(bookmarks, duplicate_groups)
    
    def _remove_smart_duplicates(self, bookmarks: List[Dict[str, Union[str, bool, int, None]]]) -> List[Dict[str, Union[str, bool, int, None]]]:
        """Smart duplicate removal: URL normalization + domain + title similarity"""
        groups = {}
        duplicate_groups = []
        
        for i, bookmark in enumerate(bookmarks):
            url = bookmark['url']
            domain = bookmark.get('domain', '')
            title = bookmark.get('formatted_label', '')
            
            # Group by domain first
            if domain not in groups:
                groups[domain] = []
            groups[domain].append((i, bookmark))
        
        # Check for duplicates within each domain group
        for domain, group_bookmarks in groups.items():
            if len(group_bookmarks) <= 1:
                continue
            
            # Check for URL duplicates within domain
            seen_urls = {}
            for idx, bookmark in group_bookmarks:
                normalized_url = normalize_url(bookmark['url'])
                if normalized_url in seen_urls:
                    duplicate_groups.append([seen_urls[normalized_url], idx])
                else:
                    seen_urls[normalized_url] = idx
        
        return self._apply_keep_strategy(bookmarks, duplicate_groups)
    
    def _remove_fuzzy_duplicates(self, bookmarks: List[Dict[str, Union[str, bool, int, None]]]) -> List[Dict[str, Union[str, bool, int, None]]]:
        """Fuzzy duplicate removal using similarity thresholds"""
        duplicate_groups = []
        processed = set()
        
        for i in range(len(bookmarks)):
            if i in processed:
                continue
            
            current_group = [i]
            bookmark1 = bookmarks[i]
            
            for j in range(i + 1, len(bookmarks)):
                if j in processed:
                    continue
                
                bookmark2 = bookmarks[j]
                
                # Calculate similarities
                url_sim = 1.0 if normalize_url(bookmark1['url']) == normalize_url(bookmark2['url']) else 0.0
                title_sim = calculate_title_similarity(bookmark1.get('formatted_label', ''), 
                                                     bookmark2.get('formatted_label', ''))
                domain_sim = 1.0 if bookmark1.get('domain', '') == bookmark2.get('domain', '') else 0.0
                
                # Weighted similarity score
                overall_sim = (url_sim * 0.5) + (title_sim * 0.3) + (domain_sim * 0.2)
                
                if overall_sim >= self.similarity_threshold:
                    current_group.append(j)
                    processed.add(j)
            
            if len(current_group) > 1:
                duplicate_groups.append(current_group)
            
            processed.add(i)
        
        return self._apply_keep_strategy(bookmarks, duplicate_groups)
    
    def _apply_keep_strategy(self, bookmarks: List[Dict[str, Union[str, bool, int, None]]], 
                           duplicate_groups: List[List[int]]) -> List[Dict[str, Union[str, bool, int, None]]]:
        """Apply the keep strategy to duplicate groups"""
        indices_to_remove = set()
        self.duplicate_groups = duplicate_groups
        
        for group in duplicate_groups:
            if len(group) <= 1:
                continue
            
            # Determine which bookmark to keep based on strategy
            if self.keep_strategy == 'first':
                keep_index = min(group)
            elif self.keep_strategy == 'last':
                keep_index = max(group)
            elif self.keep_strategy == 'shortest':
                keep_index = min(group, key=lambda i: len(bookmarks[i].get('formatted_label', '')))
            elif self.keep_strategy == 'longest':
                keep_index = max(group, key=lambda i: len(bookmarks[i].get('formatted_label', '')))
            else:
                keep_index = group[0]  # Default to first
            
            # Mark others for removal
            for idx in group:
                if idx != keep_index:
                    indices_to_remove.add(idx)
        
        # Create new list without duplicates
        unique_bookmarks = [bookmark for i, bookmark in enumerate(bookmarks) 
                          if i not in indices_to_remove]
        
        self.removed_count = len(indices_to_remove)
        return unique_bookmarks
    
    def generate_report(self) -> str:
        """Generate detailed duplicate analysis report"""
        if not self.duplicate_groups:
            return "No duplicates found."
        
        report = []
        report.append(f"Duplicate Analysis Report - Strategy: {self.strategy}")
        report.append(f"Similarity Threshold: {self.similarity_threshold}")
        report.append(f"Keep Strategy: {self.keep_strategy}")
        report.append(f"Total Duplicates Removed: {self.removed_count}")
        report.append(f"Duplicate Groups Found: {len(self.duplicate_groups)}")
        report.append("\nDuplicate Groups:")
        
        for i, group in enumerate(self.duplicate_groups, 1):
            if len(group) > 1:
                report.append(f"\nGroup {i}: {len(group)} duplicates")
                for idx in group:
                    report.append(f"  - Index {idx}")
        
        return "\n".join(report)


def remove_duplicate_urls(bookmarks: List[Dict[str, Union[str, bool, int, None]]], 
                         strategy: str = 'url', similarity_threshold: float = 0.85,
                         keep_strategy: str = 'first', generate_report: bool = False
                         ) -> Tuple[List[Dict[str, Union[str, bool, int, None]]], Optional[str]]:
    """Enhanced duplicate removal with multiple strategies"""
    if not bookmarks:
        return bookmarks, None
    
    detector = DuplicateDetector(strategy, similarity_threshold, keep_strategy)
    unique_bookmarks = detector.detect_duplicates(bookmarks)
    
    if detector.removed_count > 0:
        print(f"\nDuplicate Removal Results:")
        print(f"Strategy: {strategy.title()}")
        print(f"Removed {detector.removed_count} duplicate bookmarks")
        print(f"Bookmarks reduced from {len(bookmarks)} to {len(unique_bookmarks)}")
        
        if strategy == 'fuzzy':
            print(f"Similarity threshold: {similarity_threshold}")
        print(f"Keep strategy: {keep_strategy}")
    else:
        print("No duplicates found.")
    
    report = detector.generate_report() if generate_report else None
    return unique_bookmarks, report


def handle_validation(bookmarks: List[Dict[str, Union[str, bool, int, None]]], 
                      args: argparse.Namespace) -> List[Dict[str, Union[str, bool, int, None]]]:
    """Handle bookmark validation based on arguments"""
    should_validate = args.validate
    
    # Interactive prompt if not specified via arguments
    if not args.validate and not args.no_validate:
        response = input("Validate all URLs? This may take a while (y/n): ")
        should_validate = response.lower().startswith('y')
    
    if should_validate:
        validate_func = validate_bookmarks_concurrent if args.concurrent else validate_bookmarks_sequential
        validated_bookmarks = validate_func(bookmarks, args.max_workers)
        
        print_validation_summary(validated_bookmarks)
        return validated_bookmarks
    
    return bookmarks


def print_validation_summary(bookmarks: List[Dict[str, Union[str, bool, int, None]]]) -> None:
    """Print validation summary and broken links"""
    total = len(bookmarks)
    valid = sum(1 for b in bookmarks if b.get('is_valid', False))
    invalid = sum(1 for b in bookmarks if b.get('is_valid') is False)

    print("\n📈 Validation Summary:")
    print(f"  Total bookmarks: {total}")
    print(f"  Valid bookmarks: {valid}")
    print(f"  Invalid bookmarks: {invalid}")
    if (valid + invalid) > 0:
        success_rate = valid / (valid + invalid) * 100
        print(f"  Success rate: {success_rate:.1f}%")
    else:
        print("  No validation performed")

    # Show broken links
    broken_links = [b for b in bookmarks if b.get('is_valid') is False]
    if broken_links:
        print(f"\n❌ Broken links ({len(broken_links)}):")
        for link in broken_links[:10]:  # Show first 10
            print(f"  - {link['formatted_label'][:60]}...")
        if len(broken_links) > 10:
            print(f"  ... and {len(broken_links) - 10} more")


def generate_outputs(file_path: str, bookmarks: List[Dict[str, Union[str, bool, int, None]]], 
                     output_dir: str) -> str:
    """Generate HTML and JSON output files in timestamped job folder
    
    Returns:
        Path to the job folder for this processing run
    """
    # Create timestamped job folder
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    original_name = Path(file_path).stem
    job_folder = f"job_{timestamp}_{original_name}"
    
    # Create subdirectories for this job
    cleaned_dir = os.path.join(output_dir, "cleaned", job_folder)
    reports_dir = os.path.join(output_dir, "reports", job_folder)
    
    os.makedirs(cleaned_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)
    
    print(f"\nGenerating outputs for job: {job_folder}")
    
    # Generate HTML with original structure but clean labels
    html_output = create_html_with_clean_labels(file_path, bookmarks)
    output_html_path = os.path.join(cleaned_dir, f'{original_name}_cleaned.html')
    with open(output_html_path, 'w', encoding='utf-8') as f:
        f.write(html_output)
    
    # Generate JSON report
    json_report = {
        "generation_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source_file": file_path,
        "job_id": job_folder,
        "summary": {
            "total_bookmarks": len(bookmarks),
            "original_structure_preserved": True,
            "labels_cleaned": True,
            "duplicates_handled": True
        },
        "bookmarks": [
            {
                "original_title": b['original_title'],
                "clean_title": b['clean_title'],
                "formatted_label": b['formatted_label'],
                "domain": b['domain'],
                "url": b['url'],
                "is_valid": b.get('is_valid'),
                "status_code": b.get('status_code')
            } for b in bookmarks
        ]
    }
    
    output_json_path = os.path.join(reports_dir, f'{original_name}_report.json')
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(json_report, f, indent=2)
    
    print("Files generated:")
    print(f"  HTML: {output_html_path}")
    print(f"  JSON: {output_json_path}")
    
    return job_folder


def main() -> int:
    """Main function with improved error handling and argument parsing"""
    try:
        args = parse_arguments()
        
        # Setup logging
        if args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        setup_logging()
        
        # Create output directory
        os.makedirs(args.output_dir, exist_ok=True)
        
        # Handle AI import workflow (doesn't need input file)
        if args.import_ai:
            handle_ai_import(args)
            return 0
        
        # Get input file path for all other operations
        file_path = args.input_file
        if not file_path:
            file_path = input("📁 Enter path to bookmarks HTML file: ").strip()
            # Remove quotes if user wrapped the path in quotes
            if file_path and file_path[0] in ('"', "'") and file_path[-1] in ('"', "'"):
                file_path = file_path[1:-1]
        
        # Validate input file
        if not file_path:
            print("ERROR: No input file specified")
            return 1
            
        if not os.path.exists(file_path):
            print(f"ERROR: File not found: {file_path}")
            return 1
        
        # Update global config with command line args
        DEFAULT_CONFIG['timeout'] = args.timeout
        DEFAULT_CONFIG['max_workers'] = args.max_workers
        DEFAULT_CONFIG['output_dir'] = args.output_dir
        
        logging.info(f"Processing bookmarks from: {file_path}")
        
        # Create backup before processing
        if args.no_backup:
            print("WARNING: Proceeding without backup (--no-backup flag)")
            backup_path = None
        elif args.backup_dir:
            # Use specified backup directory
            backup_path = create_backup(file_path, args.backup_dir)
            if backup_path:
                print(f"Backup saved. You can restore from: {backup_path}\n")
        else:
            # Interactive backup prompt
            backup_path = prompt_for_backup(file_path)
            if backup_path:
                print(f"Backup saved. You can restore from: {backup_path}\n")
        
        # Process bookmarks
        bookmarks = process_bookmarks(file_path)
        show_cleaning_examples(bookmarks)
        
        # Remove duplicates if requested
        if args.remove_duplicates:
            bookmarks, duplicate_report = remove_duplicate_urls(
                bookmarks, 
                strategy=args.duplicate_strategy,
                similarity_threshold=args.similarity_threshold,
                keep_strategy=args.keep_strategy,
                generate_report=args.duplicate_report
            )
            
            # Save duplicate report if requested
            if duplicate_report and args.duplicate_report:
                # Create timestamp for duplicate report
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                report_path = os.path.join(args.output_dir, f"duplicate_report_{timestamp}.txt")
                os.makedirs(args.output_dir, exist_ok=True)
                with open(report_path, 'w', encoding='utf-8') as f:
                    f.write(duplicate_report)
                print(f"Duplicate analysis report saved to: {report_path}")
        
        # Handle AI export workflow
        if args.ai_export:
            handle_export_workflow(bookmarks, file_path, args)
            return 0
        
        # Handle validation (for normal workflow)
        bookmarks = handle_validation(bookmarks, args)
        
        # Generate standard outputs and get job folder
        job_folder = generate_outputs(file_path, bookmarks, args.output_dir)
        
        # Offer AI organization option
        print("\nAI Organization Available!")
        ai_choice = input("Would you like to export for AI organization? (y/n): ").strip().lower()
        if ai_choice.startswith('y'):
            handle_export_workflow(bookmarks, file_path, args, job_folder)
        
        print("\nSUCCESS: Done! Bookmarks cleaned while preserving original folder structure!")
        return 0
        
    except KeyboardInterrupt:
        print("\nERROR: Operation cancelled by user")
        return 1
    except FileNotFoundError as e:
        print(f"ERROR: File not found - {e}")
        return 1
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        print(f"ERROR: Unexpected error occurred. Check bookmark_cleaner.log for details.")
        return 1


if __name__ == "__main__":
    main()

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
from urllib.parse import urlparse
import re
import time
import argparse
import logging
from typing import Dict, List, Optional, Union, Tuple
import concurrent.futures
import pyperclip
from pathlib import Path


# Configuration defaults
DEFAULT_CONFIG = {
    'timeout': 10,
    'max_workers': 5,
    'title_max_length': 40,
    'validation_delay': 0.1,
    'output_dir': 'bookmarks-processed',
    'input_dir': 'bookmarks-input',
    'backup_dir': 'bookmarks-backups'
}


def setup_logging() -> None:
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('bookmark_cleaner.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def extract_domain(url: str) -> str:
    """Extract clean domain name from URL in consistent format"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        # Remove www. prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        # Ensure consistent format - always include .com/.org/.net etc
        return domain
    except Exception:
        return "unknown.com"


def clean_title(title: str, max_length: int = DEFAULT_CONFIG['title_max_length']) -> str:
    """Clean up bookmark title by removing common suffixes and junk"""
    if not title:
        return "Untitled"

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
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    soup = BeautifulSoup(content, 'html.parser')

    # Find all A tags with href attributes
    a_tags = soup.find_all('a', href=True)

    bookmarks = []
    domain_counts = {}

    # First pass: collect all bookmarks and count domains
    for a_tag in a_tags:
        url = a_tag.get('href', '').strip()
        title = a_tag.get_text().strip()

        if url and title:  # Only include if both exist
            domain = extract_domain(url)
            clean_label = clean_title(title)

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
    """Create HTML maintaining original structure but with cleaned labels"""
    with open(original_file, 'r', encoding='utf-8') as file:
        content = file.read()

    # Create a lookup for clean labels by URL
    bookmark_lookup = {b['url']: b['formatted_label'] for b in bookmarks}

    soup = BeautifulSoup(content, 'html.parser')

    # Find all A tags and replace their text with clean labels
    a_tags = soup.find_all('a', href=True)
    for a_tag in a_tags:
        url = a_tag.get('href', '').strip()
        if url in bookmark_lookup:
            # Replace the text content with clean label
            a_tag.string = bookmark_lookup[url]

    # Add comment about cleaning
    comment_text = '<!-- Bookmark labels cleaned by Bookmark Cleaner -->'
    comment = soup.new_string(comment_text)
    if soup.find('meta'):
        soup.find('meta').insert_after(comment)

    return str(soup)


def validate_bookmark(bookmark: Dict[str, Union[str, bool, int, None]], 
                      session: requests.Session, 
                      timeout: int = DEFAULT_CONFIG['timeout']) -> Dict[str, Union[str, bool, int, None]]:
    """Validate a single bookmark"""
    try:
        response = session.head(bookmark['url'], timeout=timeout,
                                allow_redirects=True)
        bookmark['is_valid'] = True
        bookmark['status_code'] = response.status_code
        return bookmark
    except Exception:
        try:
            response = session.get(bookmark['url'], timeout=timeout,
                                   allow_redirects=True)
            bookmark['is_valid'] = True
            bookmark['status_code'] = response.status_code
            return bookmark
        except Exception:
            bookmark['is_valid'] = False
            bookmark['status_code'] = None
            return bookmark


def validate_bookmarks_concurrent(bookmarks: List[Dict[str, Union[str, bool, int, None]]], 
                                  max_workers: int = DEFAULT_CONFIG['max_workers']) -> List[Dict[str, Union[str, bool, int, None]]]:
    """Validate all bookmarks concurrently for better performance"""
    session = requests.Session()
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    session.headers.update({
        'User-Agent': user_agent
    })

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
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    session.headers.update({
        'User-Agent': user_agent
    })

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
    """Parse AI-organized bookmark content back into structure"""
    lines = ai_content.strip().split('\n')
    folder_structure = {}
    all_bookmarks = []
    current_folder_path = []
    
    for line in lines:
        line = line.rstrip()
        if not line:
            continue
            
        # Count indentation level
        indent_level = (len(line) - len(line.lstrip())) // 2
        content = line.strip()
        
        if content.startswith('FOLDER:'):
            folder_name = content[7:].strip()
            # Adjust current path based on indent level
            current_folder_path = current_folder_path[:indent_level]
            current_folder_path.append(folder_name)
            
            folder_path = "/".join(current_folder_path)
            if folder_path not in folder_structure:
                folder_structure[folder_path] = []
                
        elif ' | ' in content:
            # This is a bookmark
            parts = content.split(' | ', 1)
            if len(parts) == 2:
                domain, title = parts
                folder_path = "/".join(current_folder_path) if current_folder_path else "root"
                
                bookmark = {
                    "domain": domain,
                    "title": title,
                    "folder_path": folder_path,
                    "formatted_label": content
                }
                
                all_bookmarks.append(bookmark)
                folder_structure.setdefault(folder_path, []).append(bookmark)
    
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
    
    html_content = """<!DOCTYPE NETSCAPE-Bookmark-file-1>
<!-- This is an automatically generated file. -->
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
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
        
        # Generate subfolders
        for subfolder_path in folders:
            if subfolder_path in folder_structure:
                folder_name = subfolder_path.split('/')[-1]
                folder_html += f'{indent}<DT><H3>{folder_name}</H3>\n'
                folder_html += f'{indent}<DD><DL><p>\n'
                folder_html += generate_folder_html(subfolder_path, indent_level + 1)
                folder_html += f'{indent}</DL><p>\n'
        
        return folder_html
    
    # Generate root level and all folders
    for folder_path in sorted(folder_structure.keys()):
        if '/' not in folder_path and folder_path != 'root':
            # This is a top-level folder
            folder_name = folder_path
            html_content += f'    <DT><H3>{folder_name}</H3>\n'
            html_content += f'    <DD><DL><p>\n'
            html_content += generate_folder_html(folder_path, 2)
            html_content += f'    </DL><p>\n'
    
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
                    html_content += f'    <DT><A HREF="{original["url"]}"'
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
                    html_content += f'    <DT><A HREF="{url}">{item["formatted_label"]}</A>\n'
    
    html_content += "</DL><p>"
    
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
    print("\n📥 Import AI-Organized Bookmarks")
    print("=" * 40)
    
    # Get AI content
    ai_file = input("Enter path to AI-organized file (or press Enter to paste): ").strip()
    # Remove quotes if present
    if ai_file and ai_file[0] in ('"', "'") and ai_file[-1] in ('"', "'"):
        ai_file = ai_file[1:-1]
    
    if ai_file:
        if not os.path.exists(ai_file):
            print(f"❌ File not found: {ai_file}")
            return
        with open(ai_file, 'r', encoding='utf-8') as f:
            ai_content = f.read()
    else:
        print("📋 Paste the AI-organized content (press Ctrl+D when done):")
        lines = []
        try:
            while True:
                line = input()
                lines.append(line)
        except EOFError:
            ai_content = '\n'.join(lines)
    
    if not ai_content.strip():
        print("❌ No content provided")
        return
    
    try:
        # Parse AI content
        folder_structure, organized_bookmarks = import_ai_organized_bookmarks(ai_content)
        
        print(f"\n✅ Parsed {len(organized_bookmarks)} bookmarks into {len(folder_structure)} folders")
        
        # Load original bookmarks for metadata
        original_file = input("Enter path to original bookmarks file: ").strip()
        # Remove quotes if present
        if original_file and original_file[0] in ('"', "'") and original_file[-1] in ('"', "'"):
            original_file = original_file[1:-1]
        if not os.path.exists(original_file):
            print(f"❌ Original file not found: {original_file}")
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
        
        print(f"🎉 Created organized bookmark file: {output_path}")
        print("You can now import this file into your browser!")
        
    except Exception as e:
        logging.error(f"Failed to import AI content: {e}")
        print(f"❌ Failed to parse AI content: {e}")


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
    print("🔄 Extracting bookmarks and cleaning labels...")
    bookmarks = extract_all_bookmarks(file_path)
    print(f"✓ Found {len(bookmarks)} bookmarks")
    print("✓ Cleaned labels and handled duplicates")
    
    return bookmarks


def show_cleaning_examples(bookmarks: List[Dict[str, Union[str, bool, int, None]]], count: int = 5) -> None:
    """Show examples of cleaned labels"""
    print("\n🏷️  Label Cleaning Examples:")
    for i, bookmark in enumerate(bookmarks[:count]):
        print(f"  Original: {bookmark['original_title'][:60]}...")
        print(f"  Cleaned:  {bookmark['formatted_label']}")
        print()


def handle_validation(bookmarks: List[Dict[str, Union[str, bool, int, None]]], 
                      args: argparse.Namespace) -> List[Dict[str, Union[str, bool, int, None]]]:
    """Handle bookmark validation based on arguments"""
    should_validate = args.validate
    
    # Interactive prompt if not specified via arguments
    if not args.validate and not args.no_validate:
        response = input("🔍 Validate all URLs? This may take a while (y/n): ")
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
    
    print(f"\n💾 Generating outputs for job: {job_folder}")
    
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
    
    print("✅ Files generated:")
    print(f"  📄 {output_html_path}")
    print(f"  📊 {output_json_path}")
    
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
            print("❌ Error: No input file specified")
            return 1
            
        if not os.path.exists(file_path):
            print(f"❌ Error: File not found: {file_path}")
            return 1
        
        # Update global config with command line args
        DEFAULT_CONFIG['timeout'] = args.timeout
        DEFAULT_CONFIG['max_workers'] = args.max_workers
        DEFAULT_CONFIG['output_dir'] = args.output_dir
        
        logging.info(f"Processing bookmarks from: {file_path}")
        
        # Create backup before processing
        if args.no_backup:
            print("⚠️  Proceeding without backup (--no-backup flag)")
            backup_path = None
        elif args.backup_dir:
            # Use specified backup directory
            backup_path = create_backup(file_path, args.backup_dir)
            if backup_path:
                print(f"✅ Backup saved. You can restore from: {backup_path}\n")
        else:
            # Interactive backup prompt
            backup_path = prompt_for_backup(file_path)
            if backup_path:
                print(f"✅ Backup saved. You can restore from: {backup_path}\n")
        
        # Process bookmarks
        bookmarks = process_bookmarks(file_path)
        show_cleaning_examples(bookmarks)
        
        # Handle AI export workflow
        if args.ai_export:
            handle_export_workflow(bookmarks, file_path, args)
            return 0
        
        # Handle validation (for normal workflow)
        bookmarks = handle_validation(bookmarks, args)
        
        # Generate standard outputs and get job folder
        job_folder = generate_outputs(file_path, bookmarks, args.output_dir)
        
        # Offer AI organization option
        print("\n🤖 AI Organization Available!")
        ai_choice = input("Would you like to export for AI organization? (y/n): ").strip().lower()
        if ai_choice.startswith('y'):
            handle_export_workflow(bookmarks, file_path, args, job_folder)
        
        print("\n🎉 Done! Bookmarks cleaned while preserving original folder structure!")
        return 0
        
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        return 1
    except FileNotFoundError as e:
        print(f"❌ Error: File not found - {e}")
        return 1
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        print(f"❌ Unexpected error occurred. Check bookmark_cleaner.log for details.")
        return 1


if __name__ == "__main__":
    main()

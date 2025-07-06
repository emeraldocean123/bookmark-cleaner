#!/usr/bin/env python3
"""
Bookmark Cleaner - Clean labels and preserve folder structure

This script cleans browser bookmarks by:
- Preserving original folder structure
- Cleaning bookmark labels for consistency
- Handling duplicates intelligently
- Optional URL validation
"""

from bs4 import BeautifulSoup
import json
import requests
from urllib.parse import urlparse
import re
import time
import os


def extract_domain(url):
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


def clean_title(title):
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
    if len(cleaned) > 40:
        cleaned = cleaned[:37] + "..."
    
    return cleaned or "Untitled"


def extract_all_bookmarks(file_path):
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


def validate_bookmark(bookmark, session, timeout=10):
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


def validate_bookmarks(bookmarks, max_workers=5):
    """Validate all bookmarks"""
    session = requests.Session()
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    session.headers.update({
        'User-Agent': user_agent
    })
    
    print(f"Validating {len(bookmarks)} bookmarks...")
    
    validated = []
    for i, bookmark in enumerate(bookmarks):
        validated_bookmark = validate_bookmark(bookmark, session)
        validated.append(validated_bookmark)
        status = "✓" if validated_bookmark['is_valid'] else "✗"
        label = bookmark['formatted_label'][:50]
        print(f"[{i+1}/{len(bookmarks)}] {status} {label}...")
        time.sleep(0.1)  # Be nice to servers
    
    return validated


def main():
    file_path = r"C:\Users\emera\Downloads\favorites_7_5_25.html"
    
    print("🔄 Extracting bookmarks and cleaning labels...")
    bookmarks = extract_all_bookmarks(file_path)
    print(f"✓ Found {len(bookmarks)} bookmarks")
    print("✓ Cleaned labels and handled duplicates")
    
    # Show some examples of cleaned labels
    print("\n🏷️  Label Cleaning Examples:")
    for i, bookmark in enumerate(bookmarks[:5]):
        print(f"  Original: {bookmark['original_title'][:60]}...")
        print(f"  Cleaned:  {bookmark['formatted_label']}")
        print()
    
    # Validate bookmarks
    response = input("🔍 Validate all URLs? This may take a while (y/n): ")
    if response.lower().startswith('y'):
        validated_bookmarks = validate_bookmarks(bookmarks)
        bookmarks = validated_bookmarks
        
        # Generate validation report
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
    
    # Generate output with original structure but clean labels
    print("\n💾 Generating HTML with original folders and clean labels...")
    html_output = create_html_with_clean_labels(file_path, bookmarks)
    
    # Create output directory if it doesn't exist
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Write files to output directory
    output_html_path = os.path.join(output_dir, 'clean_bookmarks.html')
    with open(output_html_path, 'w', encoding='utf-8') as f:
        f.write(html_output)
    
    print("💾 Generating detailed JSON report...")
    json_report = {
        "generation_date": time.strftime("%Y-%m-%d %H:%M:%S"),
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
    
    output_json_path = os.path.join(output_dir, 'bookmarks_report.json')
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(json_report, f, indent=2)
    
    print("✅ Files generated:")
    print(f"  📄 {output_html_path} - Original structure with clean labels")
    print(f"  📊 {output_json_path} - Detailed report")
    print("\n🎉 Done! Bookmarks cleaned while preserving original folder "
          "structure!")


if __name__ == "__main__":
    main()

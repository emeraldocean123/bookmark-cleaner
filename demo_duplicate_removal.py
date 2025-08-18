#!/usr/bin/env python3
"""
Demonstration of Advanced Duplicate Removal Features
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bookmark_cleaner import remove_duplicate_urls

def create_sample_bookmarks():
    """Create sample bookmarks with various types of duplicates"""
    return [
        # Exact URL duplicates
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
        
        # Tracking parameter duplicates
        {
            'url': 'https://github.com',
            'formatted_label': 'GitHub',
            'domain': 'github.com',
            'original_title': 'GitHub'
        },
        {
            'url': 'https://github.com?utm_source=google&utm_medium=cpc',
            'formatted_label': 'GitHub Homepage',
            'domain': 'github.com',
            'original_title': 'GitHub - Where software lives'
        },
        
        # Case differences
        {
            'url': 'https://STACKOVERFLOW.COM/questions',
            'formatted_label': 'Stack Overflow Questions',
            'domain': 'stackoverflow.com',
            'original_title': 'Questions - Stack Overflow'
        },
        {
            'url': 'https://stackoverflow.com/questions/',
            'formatted_label': 'Stack Overflow Q&A',
            'domain': 'stackoverflow.com',
            'original_title': 'Stack Overflow - Questions'
        },
        
        # Similar titles (different URLs)
        {
            'url': 'https://site1.com/python-tutorial',
            'formatted_label': 'Python Programming Tutorial',
            'domain': 'site1.com',
            'original_title': 'Learn Python Programming'
        },
        {
            'url': 'https://site2.com/python-guide',
            'formatted_label': 'Python Programming Guide',
            'domain': 'site2.com',
            'original_title': 'Python Programming Tutorial'
        },
        
        # Unique bookmarks (should not be removed)
        {
            'url': 'https://unique1.com',
            'formatted_label': 'Unique Site 1',
            'domain': 'unique1.com',
            'original_title': 'Unique Site 1'
        },
        {
            'url': 'https://unique2.com',
            'formatted_label': 'Unique Site 2', 
            'domain': 'unique2.com',
            'original_title': 'Unique Site 2'
        }
    ]

def demonstrate_strategy(strategy, bookmarks, **kwargs):
    """Demonstrate a specific duplicate removal strategy"""
    print(f"\\n{'='*60}")
    print(f"STRATEGY: {strategy.upper()}")
    print(f"{'='*60}")
    
    # Show parameters
    if kwargs:
        print("Parameters:")
        for key, value in kwargs.items():
            print(f"  {key}: {value}")
        print()
    
    # Apply duplicate removal
    result, report = remove_duplicate_urls(
        bookmarks.copy(),
        strategy=strategy,
        generate_report=True,
        **kwargs
    )
    
    print(f"Original bookmarks: {len(bookmarks)}")
    print(f"After removal: {len(result)}")
    print(f"Duplicates removed: {len(bookmarks) - len(result)}")
    
    if report:
        print(f"\\nDetailed Report:")
        print("-" * 40)
        print(report)
    
    return result

def main():
    """Main demonstration function"""
    print("ADVANCED DUPLICATE REMOVAL DEMONSTRATION")
    print("="*60)
    print()
    
    # Create sample data
    bookmarks = create_sample_bookmarks()
    
    print("SAMPLE BOOKMARKS:")
    print("-" * 40)
    for i, bookmark in enumerate(bookmarks, 1):
        print(f"{i:2d}. {bookmark['formatted_label']}")
        print(f"    URL: {bookmark['url']}")
        print(f"    Domain: {bookmark['domain']}")
        print()
    
    # Demonstrate each strategy
    strategies = [
        ('url', {}),
        ('title', {}),
        ('smart', {}),
        ('fuzzy', {'similarity_threshold': 0.7}),
        ('fuzzy', {'similarity_threshold': 0.9})
    ]
    
    results = {}
    
    for strategy, params in strategies:
        strategy_key = f"{strategy}_{params.get('similarity_threshold', 'default')}"
        results[strategy_key] = demonstrate_strategy(strategy, bookmarks, **params)
    
    # Summary comparison
    print(f"\\n{'='*60}")
    print("STRATEGY COMPARISON SUMMARY")
    print(f"{'='*60}")
    print(f"{'Strategy':<20} {'Bookmarks Left':<15} {'Removed':<10}")
    print("-" * 45)
    
    original_count = len(bookmarks)
    for strategy_key, result in results.items():
        removed = original_count - len(result)
        print(f"{strategy_key:<20} {len(result):<15} {removed:<10}")
    
    # Demonstrate keep strategies
    print(f"\\n{'='*60}")
    print("KEEP STRATEGY DEMONSTRATION")
    print(f"{'='*60}")
    
    keep_strategies = ['first', 'last', 'shortest', 'longest']
    
    for keep_strategy in keep_strategies:
        print(f"\\nKeep Strategy: {keep_strategy}")
        print("-" * 30)
        
        result, _ = remove_duplicate_urls(
            bookmarks.copy(),
            strategy='url',
            keep_strategy=keep_strategy,
            generate_report=False
        )
        
        print(f"Bookmarks remaining: {len(result)}")
    
    print(f"\\n{'='*60}")
    print("DEMONSTRATION COMPLETE")
    print(f"{'='*60}")
    print()
    print("Key Features Demonstrated:")
    print("+ URL normalization (www, case, tracking parameters)")
    print("+ Multiple detection strategies (URL, title, smart, fuzzy)")
    print("+ Configurable similarity thresholds")
    print("+ Different keep strategies (first, last, shortest, longest)")
    print("+ Detailed duplicate analysis reports")
    print()
    print("Try these commands with your own bookmarks:")
    print("  python bookmark_cleaner.py file.html --remove-duplicates")
    print("  python bookmark_cleaner.py file.html --remove-duplicates --duplicate-strategy smart")
    print("  python bookmark_cleaner.py file.html --remove-duplicates --duplicate-strategy fuzzy --similarity-threshold 0.8")
    print("  python bookmark_cleaner.py file.html --remove-duplicates --duplicate-report")

if __name__ == '__main__':
    main()
# Bookmark Cleaner

A Python tool for cleaning browser bookmarks while preserving their original folder structure.

## Features

- **Preserves Original Folder Structure**: Never moves bookmarks between folders
- **Clean Bookmark Labels**: Removes marketing fluff and creates consistent `domain.com | title` format
- **Smart Duplicate Handling**: For multiple bookmarks from the same domain, creates unique identifiers
- **URL Validation**: Optional feature to check if links are still working
- **Browser Compatible**: Generates standard HTML bookmark files

## Installation

1. Install Python 3.7 or higher
2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the script with your exported bookmarks file:

```bash
python bookmark_cleaner.py
```

The script will:
1. Parse your bookmarks from `C:\Users\emera\Downloads\favorites_7_5_25.html`
2. Clean all bookmark labels to `domain.com | clean_title` format
3. Handle duplicates intelligently with unique identifiers
4. Preserve your original folder structure completely
5. Optionally validate all URLs
6. Generate clean output files

## Label Cleaning Examples

**Before:**
```
Capital One | Personal Banking Services & Products
Charles Schwab | A modern approach to investing & retirement
PayPal | Send Money, Pay Online or Set Up a Merchant Account
```

**After:**
```
capitalone.com | Capital One
schwab.com | Charles Schwab  
paypal.com | PayPal
```

## Duplicate Handling

For multiple bookmarks from the same domain:

```
github.com | Homepage              (from github.com/en/)
github.com | Cactbot               (from github.com/quisquous/cactbot)
github.com | Ember Overlay         (from github.com/GoldenChrysus/ffxiv-ember-overlay)
```

## Output Files

All output files are generated in the `output/` subfolder:

- **`output/clean_bookmarks.html`** - Your cleaned bookmarks with original folder structure
- **`output/bookmarks_report.json`** - Detailed report with all bookmark data

## Key Principles

- ✅ **Never moves bookmarks** between folders
- ✅ **Only cleans labels** for consistency and readability  
- ✅ **Preserves all folder structure** exactly as exported
- ✅ **Handles duplicates** with meaningful identifiers
- ✅ **Browser compatible** output for easy import

## Requirements

- Python 3.7+
- BeautifulSoup4
- Requests
- lxml

## License

MIT License
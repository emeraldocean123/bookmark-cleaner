# Bookmark Cleaner

A Python tool for cleaning browser bookmarks while preserving their original folder structure.

## Features

- **Preserves Original Folder Structure**: Never moves bookmarks between folders
- **Clean Bookmark Labels**: Removes marketing fluff and creates consistent `domain.com | title` format
- **Smart Duplicate Handling**: For multiple bookmarks from the same domain, creates unique identifiers
- **URL Validation**: Optional feature to check if links are still working
- **Browser Compatible**: Generates standard HTML bookmark files

## Installation

### Option 1: Quick Setup (Windows)
1. Install Python 3.7 or higher from [python.org](https://www.python.org/)
2. Run the batch installer:
   ```cmd
   install_dependencies.bat
   ```
3. Test the setup:
   ```cmd
   python test_setup.py
   ```

### Option 2: Manual Setup
1. Install Python 3.7 or higher
2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Usage
```bash
# Interactive mode - prompts for file path
python bookmark_cleaner.py

# Specify file directly  
python bookmark_cleaner.py bookmarks.html

# Custom output directory
python bookmark_cleaner.py bookmarks.html --output-dir ./cleaned
```

### Advanced Options
```bash
# Validate URLs with concurrent processing (faster)
python bookmark_cleaner.py bookmarks.html --validate --concurrent

# Skip validation entirely
python bookmark_cleaner.py bookmarks.html --no-validate

# Configure performance
python bookmark_cleaner.py bookmarks.html --max-workers 10 --timeout 15

# Verbose logging
python bookmark_cleaner.py bookmarks.html --verbose

# Get help
python bookmark_cleaner.py --help
```

### What the script does:
1. **Parse** your exported bookmarks HTML file
2. **Clean** all bookmark labels to `domain.com | clean_title` format  
3. **Handle** duplicates intelligently with unique identifiers
4. **Preserve** your original folder structure completely
5. **Optionally validate** all URLs (concurrent or sequential)
6. **Generate** clean output files in `output/` directory

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
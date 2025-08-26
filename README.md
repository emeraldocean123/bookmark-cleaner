# Bookmark Cleaner

A Python tool for cleaning browser bookmarks and organizing them intelligently with AI assistance.

## Features

### Core Functionality
- **Automatic Backups**: Creates timestamped backups before processing (configurable location)
- **Auto-Dependency Installation**: Detects missing packages and offers to install them
- **Clean Bookmark Labels**: Removes marketing fluff and creates consistent `domain.com | title` format
- **Duplicate Removal**: Remove exact URL duplicates with `--remove-duplicates` flag (NEW!)
- **Smart Duplicate Handling**: For multiple bookmarks from the same domain, creates unique identifiers
- **URL Validation**: Optional concurrent validation to check if links are still working
- **Browser Compatible**: Generates standard HTML bookmark files

### 🤖 AI-Powered Organization (NEW!)
- **Export for AI**: Prepare bookmarks with detailed instructions for AI reorganization
- **Three Export Formats**: Preserve structure, flatten all, or AI-ready with instructions
- **Clipboard Integration**: Copy/paste workflow for easy AI interaction
- **Import AI Results**: Recreate organized bookmark files from AI responses
- **Intelligent Structure**: AI creates logical folder hierarchies based on content and usage patterns

## Installation

### Option 1: Quick Setup (Windows)
1. Install Python 3.7 or higher from [python.org](https://www.python.org/)
2. Run the batch installer:
   ```cmd
   install_dependencies.bat
   ```
3. Test the setup:
   ```cmd
   python test_suite.py
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

# Remove duplicate URLs (keeps first occurrence)
python bookmark_cleaner.py bookmarks.html --remove-duplicates

# Advanced duplicate removal with different strategies
python bookmark_cleaner.py bookmarks.html --remove-duplicates --duplicate-strategy smart
python bookmark_cleaner.py bookmarks.html --remove-duplicates --duplicate-strategy fuzzy --similarity-threshold 0.8
python bookmark_cleaner.py bookmarks.html --remove-duplicates --keep-strategy last

# Generate detailed duplicate analysis report
python bookmark_cleaner.py bookmarks.html --remove-duplicates --duplicate-report

# Custom output directory
python bookmark_cleaner.py bookmarks.html --output-dir ./cleaned
```

### 🤖 AI-Powered Organization Workflow

#### Step 1: Export for AI
```bash
# Export bookmarks for AI organization (interactive menu)
python bookmark_cleaner.py bookmarks.html --ai-export

# Choose from:
# 1. Preserve original folder structure
# 2. Flatten all bookmarks (no folders)  
# 3. Prepare for AI organization (with detailed instructions)
```

#### Step 2: AI Organization
1. Copy the generated content to your clipboard
2. Share with an AI (Claude, ChatGPT, etc.) using this prompt:

> "Please organize these bookmarks into logical folders following the format provided in the instructions."

3. Copy the AI's organized response

#### Step 3: Import AI Results
```bash
# Import AI-organized bookmarks
python bookmark_cleaner.py --import-ai

# Options:
# - Paste AI response directly
# - Load from file
# - Automatically creates browser-importable HTML
```

### Backup Options

The script automatically creates backups before processing:

```bash
# Default: Interactive prompt for backup location
python bookmark_cleaner.py bookmarks.html

# Specify custom backup directory
python bookmark_cleaner.py bookmarks.html --backup-dir ./backups

# Skip backup (not recommended)
python bookmark_cleaner.py bookmarks.html --no-backup
```

**Backup Features:**
- Timestamped backup files (e.g., `bookmarks_backup_20250111_143022.html`)
- Default location: Same directory as source file
- Option to choose custom backup directory
- Shows backup location and file size
- Preserves original file completely unchanged

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

## Advanced Duplicate Removal

### Duplicate Detection Strategies

#### 1. **URL Strategy (Default)**
Removes bookmarks with identical normalized URLs:
- Normalizes case, removes www, strips tracking parameters
- Handles `utm_*`, `fbclid`, `gclid` parameters
- Example: `https://example.com` = `https://www.example.com?utm_source=google`

#### 2. **Title Strategy**
Removes bookmarks with identical titles:
- Case-insensitive comparison
- Useful for bookmarks with different URLs but same content

#### 3. **Smart Strategy**
Intelligent duplicate detection:
- Groups bookmarks by domain first
- Detects URL duplicates within each domain
- Preserves meaningful variations while removing true duplicates

#### 4. **Fuzzy Strategy**
Advanced similarity-based detection:
- Combines URL, title, and domain similarity
- Configurable similarity threshold (0.0-1.0)
- Uses weighted scoring: URL (50%) + Title (30%) + Domain (20%)

### Keep Strategies

Choose which duplicate to keep when multiple are found:

- **`first`** (default) - Keep the first occurrence
- **`last`** - Keep the last occurrence  
- **`shortest`** - Keep bookmark with shortest title
- **`longest`** - Keep bookmark with longest title

### Duplicate Analysis Report

Generate detailed reports with `--duplicate-report`:

```
Duplicate Analysis Report - Strategy: smart
Similarity Threshold: 0.85
Keep Strategy: first
Total Duplicates Removed: 45
Duplicate Groups Found: 12

Duplicate Groups:
Group 1: 3 duplicates
  - Index 5: https://example.com
  - Index 23: https://www.example.com/
  - Index 67: https://example.com?utm_source=google
```

### Examples

#### Basic Duplicate Removal
```bash
# Remove exact URL duplicates
python bookmark_cleaner.py bookmarks.html --remove-duplicates
```

#### Smart Detection
```bash
# Use smart strategy to group by domain
python bookmark_cleaner.py bookmarks.html --remove-duplicates --duplicate-strategy smart
```

#### Fuzzy Matching
```bash
# Use fuzzy matching with custom threshold
python bookmark_cleaner.py bookmarks.html --remove-duplicates \
  --duplicate-strategy fuzzy \
  --similarity-threshold 0.7 \
  --keep-strategy longest
```

#### Analysis Report
```bash
# Generate detailed duplicate analysis
python bookmark_cleaner.py bookmarks.html --remove-duplicates \
  --duplicate-strategy smart \
  --duplicate-report
```

### Smart Domain Grouping

For multiple bookmarks from the same domain, smart strategy creates meaningful groupings:

```
github.com | Homepage              (from github.com/en/)
github.com | Cactbot               (from github.com/quisquous/cactbot)
github.com | Ember Overlay         (from github.com/GoldenChrysus/ffxiv-ember-overlay)
```

Each represents a unique project/page, so all are preserved.

## 🤖 AI Organization Format

The AI export creates content with explicit formatting instructions:

### Input to AI:
```
github.com | GitHub Homepage
stackoverflow.com | Stack Overflow  
youtube.com | YouTube
netflix.com | Netflix
bbc.com | BBC News
```

### Expected AI Output:
```
FOLDER: Development & Work
  github.com | GitHub Homepage
  stackoverflow.com | Stack Overflow
  
  FOLDER: Documentation
    developer.mozilla.org | MDN Web Docs

FOLDER: Entertainment & Media  
  youtube.com | YouTube
  netflix.com | Netflix
  
FOLDER: News & Information
  bbc.com | BBC News
```

### Key Format Rules:
- Use `FOLDER: Name` for folders (with colon)
- Indent bookmarks with 2 spaces under folders
- Indent subfolders with 2 spaces, their bookmarks with 4 spaces
- Keep bookmark format: `domain | title`
- Max 3 levels deep for organization

## Output Files

All output files are organized in timestamped job folders within the `bookmarks-processed/` directory:

### Folder Structure
```
bookmarks-processed/
├── ai-export/                    # AI export files
│   ├── bookmarks_for_ai.txt     
│   └── bookmarks-ai-grok.txt    
├── ai-organized/                 # AI organized results
│   └── job_YYYYMMDD_HHMMSS_name/
│       └── name_ai_organized.html
├── cleaned/                      # Standard cleaned bookmarks
│   └── job_YYYYMMDD_HHMMSS_name/
│       └── name_cleaned.html
└── reports/                      # Detailed JSON reports
    └── job_YYYYMMDD_HHMMSS_name/
        └── name_report.json
```

### File Types
- **Cleaned HTML**: Browser-importable files with clean labels and preserved folder structure
- **AI Organized HTML**: Browser-importable files with AI-generated folder organization  
- **JSON Reports**: Detailed metadata including validation results and processing statistics
- **AI Export Files**: Text files formatted for AI organization with detailed instructions

### Testing
Run the comprehensive test suite to verify functionality:
```bash
# Run all tests
python test_suite.py

# Run specific tests
python test_suite.py --test parsing
python test_suite.py --test workflow  
python test_suite.py --test syntax

# Verbose output
python test_suite.py --verbose
```

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
- pyperclip (for clipboard functionality)

## License

MIT License
## Contributing

- Use Conventional Commits for messages: `type(scope)?: subject`.
- Repo commit template: `.commit-template.txt` is configured.
- Shared hooks: global `core.hooksPath` → `Documents/dev/dotfiles/githooks` (pre-commit checks and commit-msg enforcement).

## Review Routing

- CODEOWNERS routes PR reviews to `@emeraldocean123` automatically.

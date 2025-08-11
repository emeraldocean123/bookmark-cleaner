# 📁 Bookmark Cleaner - Folder Organization Guide

## 🎯 Overview

The bookmark-cleaner now uses an organized folder structure to keep track of all bookmark files by job. Each processing run creates a timestamped job folder for easy tracking and management.

## 📂 Folder Structure

```
bookmark-cleaner/
├── 📁 bookmarks-input/           # Your original bookmark files
│   ├── favorites_8_11_25.html
│   └── other_bookmarks.html
│
├── 📁 bookmarks-backups/         # Automatic backups before processing
│   ├── favorites_backup_20250811_132400.html
│   └── favorites_backup_20250811_140530.html
│
├── 📁 bookmarks-processed/       # All processed outputs, organized by job
│   ├── 📁 cleaned/              # Standard cleaned bookmark files
│   │   ├── 📁 job_20250811_132400_favorites/
│   │   │   └── favorites_cleaned.html
│   │   └── 📁 job_20250811_140530_favorites/
│   │       └── favorites_cleaned.html
│   │
│   ├── 📁 ai-export/            # Files prepared for AI organization
│   │   ├── 📁 job_20250811_132400_favorites/
│   │   │   ├── bookmarks_for_ai.txt
│   │   │   ├── bookmarks_flattened.txt
│   │   │   └── bookmarks_structured.txt
│   │   └── 📁 job_20250811_140530_favorites/
│   │       └── bookmarks_for_ai.txt
│   │
│   ├── 📁 ai-organized/         # Final AI-organized bookmark files
│   │   ├── 📁 job_20250811_132400_favorites_ai_organized/
│   │   │   └── favorites_ai_organized.html
│   │   └── 📁 job_20250811_140530_favorites_ai_organized/
│   │       └── favorites_ai_organized.html
│   │
│   └── 📁 reports/              # Processing reports and analytics
│       ├── 📁 job_20250811_132400_favorites/
│       │   └── favorites_report.json
│       └── 📁 job_20250811_140530_favorites/
│           └── favorites_report.json
│
└── 📁 [scripts and docs]        # Main scripts and documentation
    ├── bookmark_cleaner.py
    ├── README.md
    ├── AI_WORKFLOW_GUIDE.md
    └── requirements.txt
```

## 🏷️ Job Naming Convention

Each processing job gets a unique folder name:
```
job_YYYYMMDD_HHMMSS_filename
```

**Example:**
- `job_20250811_132400_favorites` - Processed on Aug 11, 2025 at 13:24:00 from favorites.html
- `job_20250811_140530_bookmarks_ai_organized` - AI organized on Aug 11, 2025 at 14:05:30

## 📋 File Types by Folder

### 📁 bookmarks-input/
- **Purpose:** Store your original bookmark files
- **Files:** `.html` files exported from browsers
- **Usage:** Place bookmark files here before processing

### 📁 bookmarks-backups/
- **Purpose:** Automatic backups created before any processing
- **Files:** `filename_backup_YYYYMMDD_HHMMSS.html`
- **Usage:** Restore from here if something goes wrong

### 📁 bookmarks-processed/cleaned/
- **Purpose:** Standard cleaned bookmark files with original structure
- **Files:** `filename_cleaned.html`
- **Usage:** Import into browser for cleaned labels with original folders

### 📁 bookmarks-processed/ai-export/
- **Purpose:** Files prepared for AI organization
- **Files:** 
  - `bookmarks_for_ai.txt` - Ready for AI with instructions
  - `bookmarks_flattened.txt` - Simple flat list
  - `bookmarks_structured.txt` - Preserves original structure
- **Usage:** Share `bookmarks_for_ai.txt` with AI models

### 📁 bookmarks-processed/ai-organized/
- **Purpose:** Final AI-organized bookmark files ready for browser import
- **Files:** `filename_ai_organized.html`
- **Usage:** Import into browser for AI-organized folder structure

### 📁 bookmarks-processed/reports/
- **Purpose:** Detailed processing reports and analytics
- **Files:** `filename_report.json`
- **Usage:** Review processing statistics and bookmark details

## 🛠️ How the Script Uses These Folders

### Input Processing
1. Script looks for input files in `bookmarks-input/`
2. Creates backup in `bookmarks-backups/`
3. Processes and creates job folder with timestamp

### Standard Workflow
```bash
python bookmark_cleaner.py bookmarks-input/favorites.html
```
**Creates:**
- `bookmarks-backups/favorites_backup_YYYYMMDD_HHMMSS.html`
- `bookmarks-processed/cleaned/job_YYYYMMDD_HHMMSS_favorites/favorites_cleaned.html`
- `bookmarks-processed/reports/job_YYYYMMDD_HHMMSS_favorites/favorites_report.json`

### AI Export Workflow
```bash
python bookmark_cleaner.py bookmarks-input/favorites.html --ai-export
```
**Creates:**
- Backup and cleaned files (as above)
- `bookmarks-processed/ai-export/job_YYYYMMDD_HHMMSS_favorites/bookmarks_for_ai.txt`

### AI Import Workflow
```bash
python bookmark_cleaner.py --import-ai
```
**Creates:**
- `bookmarks-processed/ai-organized/job_YYYYMMDD_HHMMSS_favorites_ai_organized/favorites_ai_organized.html`

## 📊 Benefits of This Organization

### ✅ **Easy Tracking**
- Each job has a unique timestamp
- Clear separation between input, backup, and output files
- Easy to find files from specific processing runs

### ✅ **No File Conflicts**
- Timestamped folders prevent overwrites
- Multiple processing runs of same file stay separate
- Clear history of all processing attempts

### ✅ **Workflow Clarity**
- Input files clearly separated from outputs
- Different processing types in separate folders
- Easy to understand file purposes

### ✅ **Backup Safety**
- All backups automatically organized by timestamp
- Easy to restore from specific backup dates
- No risk of losing original files

## 🔧 Configuration

The script uses these default folder names (can be changed in `bookmark_cleaner.py`):

```python
DEFAULT_CONFIG = {
    'output_dir': 'bookmarks-processed',
    'input_dir': 'bookmarks-input',
    'backup_dir': 'bookmarks-backups'
}
```

## 💡 Tips for Use

1. **Keep Input Files Organized:** Place all bookmark files in `bookmarks-input/`
2. **Regular Cleanup:** Archive old job folders periodically
3. **Backup Safety:** The `bookmarks-backups/` folder is your safety net
4. **Job Tracking:** Use timestamps in folder names to track when files were processed
5. **Browser Import:** Always use files from `cleaned/` or `ai-organized/` folders for importing

## 🗂️ File Locations Quick Reference

| What you want | Where to find it |
|---------------|------------------|
| **Original files** | `bookmarks-input/filename.html` |
| **Backups** | `bookmarks-backups/filename_backup_*.html` |
| **Cleaned bookmarks** | `bookmarks-processed/cleaned/job_*/filename_cleaned.html` |
| **AI export files** | `bookmarks-processed/ai-export/job_*/bookmarks_for_ai.txt` |
| **AI organized** | `bookmarks-processed/ai-organized/job_*/filename_ai_organized.html` |
| **Processing reports** | `bookmarks-processed/reports/job_*/filename_report.json` |

This organization makes it easy to track your bookmark processing history and find exactly what you need for each step of the workflow! 🎯
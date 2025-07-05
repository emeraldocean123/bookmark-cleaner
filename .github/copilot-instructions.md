# Copilot Instructions

<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

This is a Python project for cleaning browser bookmarks. The project should:

1. Parse HTML bookmark files exported from browsers
2. Clean bookmark labels for better readability and consistency
3. Handle duplicate domains intelligently  
4. Preserve original folder structure completely
5. Validate URLs to check if they're still working
6. Generate clean, organized bookmark HTML files

Key guidelines:
- Use proper HTML parsing libraries like BeautifulSoup
- Implement URL validation with appropriate error handling
- Organize code into clear, modular functions
- Provide clear output and reporting functionality
- Handle edge cases in bookmark parsing gracefully
- NEVER move bookmarks between folders - only clean labels

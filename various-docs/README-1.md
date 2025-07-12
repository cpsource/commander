Looking at your code, I'll modify it to support the `-x` command line switch for specifying file extensions. Here's the updated version:**Key changes made:**

1. **Added `-x` command line argument** that accepts a comma-separated string of extensions
2. **Renamed `PythonFileProcessor` to `FileProcessor`** since it now handles multiple file types
3. **Added `parse_extensions()` function** to clean up the extension string (handles spaces, removes dots)
4. **Added `get_language_for_extension()` method** to map file extensions to proper language identifiers for code fencing
5. **Updated prompt creation** to use appropriate language identifiers in code fences
6. **Modified file data structure** to store both content and language type
7. **Updated all variable names and comments** to reflect multi-language support

**Usage examples:**

```bash
# Default behavior (Python files only)
python commander.py

# Python and JSON files
python commander.py -x "py,json"

# Web development files
python commander.py -x "js,html,css" -r

# Documentation files
python commander.py -x "md,txt,rst"

# Mixed project files
python commander.py -x "py, json, md, txt" -r
```

The tool now properly formats different file types with appropriate code fencing, so Gemini gets the right context for each file type. For example, JavaScript files will be wrapped in ````javascript` blocks, JSON files in ````json` blocks, etc.


I'll create a Python program that acts like a code-processing commander using Gemini 2.5 Pro. Think of it as a smart batch processor that can understand natural language instructions and apply them to multiple Python files at once.Now let me create a requirements.txt file for the dependencies:Here's your `commander.py` program! Think of it as a smart assistant that can read a room full of Python files and modify them all according to your written instructions.

## How it works (with analogies):

**Like a skilled editor with a style guide**: Just as a newspaper editor reads a style guide and applies it to multiple articles, this program reads your `commander.txt` file and applies those instructions to multiple Python files.

**Like a batch processor with AI**: Instead of manually editing each file, it's like having a very smart intern who can understand natural language instructions and apply them consistently across all your code.

## Key Components:

1. **PythonFileProcessor**: Like a librarian who knows how to find all the books (Python files) in a library, optionally going through all the floors (recursive search)

2. **CommanderInstructions**: Like reading a recipe card - it knows how to read and understand your `commander.txt` file

3. **GeminiProcessor**: The smart assistant that talks to Gemini AI, formatting your request properly and handling the conversation

4. **ResponseParser**: Like a skilled translator who can extract the modified code from Gemini's response and write it back to files

## Usage Examples:

```bash
# Process Python files in current directory only
python commander.py

# Process Python files recursively through subdirectories  
python commander.py -r
```

## Setup:

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Create ~/.env file** with your Google API key:
   ```
   GOOGLE_API_KEY=your_actual_api_key_here
   ```

3. **Create commander.txt** with your instructions, like:
   ```
   Add type hints to all function parameters and return values.
   Add docstrings to any functions that don't have them.
   Make sure all imports are organized alphabetically.
   ```

## Safety Features:

- **Automatic backups**: Creates `.backup` files before modifying anything
- **Confirmation prompt**: Asks before making changes
- **Error handling**: Gracefully handles missing files, API errors, etc.
- **Trace information**: Shows you exactly what it's doing at each step

The program is like having a very careful, methodical assistant who never forgets to make backups and always asks permission before making changes!


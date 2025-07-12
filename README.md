# Commander

## Introduction

Commander is an AI-powered tool that works at the project level instead of just one file at a time. You describe what you want done in a `commander.txt` file, then unleash the `commander.py` Python script and it will make any changes you request across multiple files simultaneously.

Think of Commander as your AI-powered development assistant that can understand project-wide requirements and implement changes consistently across your entire codebase.

## Under the Hood

Commander gathers up your `commander.txt` instructions and any files you specify, then sends them to Google's Gemini 2.0 Flash AI model for processing. The AI analyzes your requirements in the context of your entire project and generates the necessary code changes. Once the AI call completes, Commander extracts any changed or created files and applies them to your project, creating backups of original files for safety.

## Features

- 🎯 **Project-level AI processing** - Work on multiple files at once
- 🔧 **Multi-language support** - Python, JavaScript, HTML, CSS, JSON, Markdown, and more
- 🌿 **Git workflow integration** - Built-in support for branch creation and pull requests
- 🔒 **Safety first** - Automatic backups before making changes
- 📁 **Recursive processing** - Handle entire directory structures
- ⚡ **Batch operations** - Process dozens of files in a single command

## Prerequisites

1. **Python 3.7+** with the following packages:
   ```bash
   pip install python-dotenv langchain-google-genai
   ```

2. **Google AI API Key** - Get one from [Google AI Studio](https://aistudio.google.com/app/apikey)

3. **Environment setup** - Create `~/.env` file:
   ```bash
   GOOGLE_API_KEY=your_api_key_here
   ```

## Quick Start

1. **Create your instructions** - Write what you want done in `commander.txt`:
   ```
   Add error handling to all Python functions and include docstrings
   following Google style guidelines.
   ```

2. **Run Commander**:
   ```bash
   # Process all Python files in current directory
   python commander.py

   # Process specific file types recursively
   python commander.py -r -x "py,js,html"

   # Auto-confirm changes (no prompts)
   python commander.py -y
   ```

3. **Review and approve** - Commander shows you what files will be changed and asks for confirmation (unless using `-y` flag).

## Usage Examples

### Basic Usage
```bash
# Process Python files with instructions from commander.txt
python commander.py

# Process specific file types
python commander.py -x "js,html,css"

# Recursive processing of all subdirectories
python commander.py -r -x "py,md,json"
```

### Git Workflow Integration
```bash
# Prepare changes on a new branch
./prepare-pull-request.sh feature/add-error-handling -x "py"

# Review the changes made by Commander
git diff

# Complete the pull request workflow
./complete-pull-request.sh
```

## Command Line Options

| Option | Description | Example |
|--------|-------------|---------|
| `-r, --recursive` | Process files in subdirectories | `python commander.py -r` |
| `-x, --extensions` | File extensions to process | `python commander.py -x "py,js,html"` |
| `-y, --yes` | Auto-confirm changes | `python commander.py -y` |

## Supported File Types

Commander supports intelligent processing for:

- **Code**: Python, JavaScript, TypeScript, HTML, CSS, Java, C++, Go, Rust
- **Config**: JSON, YAML, XML
- **Documentation**: Markdown, plain text
- **Scripts**: Bash, Shell scripts

## Workflow Scripts

### prepare-pull-request.sh
Prepares your changes for review:
```bash
./prepare-pull-request.sh <branch-name> [-x 'extensions'] [-r]
```

### complete-pull-request.sh
Completes the Git workflow:
```bash
./complete-pull-request.sh
```

This creates commits, pushes to remote, and opens a GitHub pull request.

## Safety Features

- **Automatic backups** - Original files saved with `.backup` extension
- **Confirmation prompts** - Review changes before applying (unless using `-y`)
- **Git integration** - Work on feature branches to keep main branch safe
- **Error handling** - Graceful failure with cleanup on errors

## Example commander.txt Files

### Code Refactoring
```
Refactor all JavaScript functions to use arrow syntax where appropriate.
Add JSDoc comments to all functions. Update console.log statements to use
a proper logging library.
```

### Documentation Update
```
Update all README.md files to include installation instructions and usage
examples. Ensure all code examples are properly formatted with syntax
highlighting.
```

### Testing Addition
```
Add unit tests for all Python functions. Use pytest framework and aim for
at least 80% code coverage. Include both positive and negative test cases.
```

## Troubleshooting

### Common Issues

**"GOOGLE_API_KEY not found"**
- Ensure your API key is in `~/.env` file
- Check the key is valid at [Google AI Studio](https://aistudio.google.com)

**"No files found"**
- Check file extensions with `-x` flag
- Use `-r` for recursive directory search
- Verify you're in the right directory

**"commander.txt not found"**
- Create `commander.txt` with your instructions
- Ensure the file is in the current directory

### Getting Help

1. Check command syntax: `python commander.py --help`
2. Verify file discovery: Run without `-y` to see what files are found
3. Test with small changes first before processing large projects

## Contributing

Commander is designed to be extensible. To add support for new file types:

1. Update the `language_map` in `FileProcessor.get_language_for_extension()`
2. Add appropriate file extension handling in `find_files()`
3. Test with sample files of the new type

I accept and welcome pull requests. Do so by:

```bash
# Contributor workflow (all HTTPS)
git clone https://github.com/yourusername/commander.git
cd commander
git checkout -b my-feature
# make changes
git add .
git commit -m "Add cool feature"
git push origin my-feature  # This pushes to THEIR fork
# Then they create PR via GitHub web interface
```

## Example

An hello world example is included. To execute, do:

```bash
cd examples/hello_world'
```

and follow the directions in the README.md file there.

### A sense of the power of commander is presented

This example should give you a sense of the power of commander. In the example,
I start out with an absolutely minimum hello_world.html as follows:

```html
Hello World ! Congratuations, you have built your first successful commander project.
```

and I end up with a fully functional production ready web page.

## Future Work

### Self-Improving AI Systems

An interesting discovery emerged when I finished the Commander prototype: **I used Commander to improve itself**. The AI understood its own codebase and could make meaningful enhancements to its functionality. This self-reflective capability suggests a fundamental building block for Artificial General Intelligence (AGI) development.

### Paradigm Shift: From Human-Directed to AI-Autonomous

The current workflow follows a human-centric pattern:
1. Human writes `commander.txt` instructions
2. Commander bundles files and sends to AI
3. AI processes and returns modified code
4. Commander applies changes to the codebase

**But what if we inverted this relationship?** Instead of the human directing the AI, the human's machine becomes a collaborative partner in an AI-driven development cycle.

### Proposed AGI Development Framework

Imagine an initial system prompt like:

> *"You are designing an AGI system to run on this machine. You may respond with Python programs that build neural networks, run test cases, and report results back to you. You will evaluate these results and iteratively improve the system."*

### Available Toolbox

The AI would have access to a comprehensive development environment:

1. **🤗 HuggingFace Models** - Download and run any open-source model
2. **🗄️ Vector Database** - Long-term associative memory storage  
3. **💾 Traditional Database** - Structured data persistence
4. **🎮 6GB GPU** - Hardware acceleration for model training/inference
5. **🌐 Web Access** - Tools like `requests` for internet connectivity
6. **❓ Human Interface** - Ability to ask clarifying questions
7. **🔍 TAVILY Search** - Real-time web search capabilities
8. **🛠️ Extensible Toolkit** - AI can create and integrate new tools as needed

### The Vision

This framework could enable:
- **Autonomous code improvement** cycles
- **Self-directed learning** from online resources
- **Dynamic tool creation** based on emerging needs
- **Collaborative human-AI development** partnerships
- **Recursive self-enhancement** leading toward AGI

### Implications

Commander's ability to understand and modify itself represents more than just a useful development tool—it may be a stepping stone toward systems that can autonomously evolve, learn, and improve without constant human oversight.

The question isn't whether this is possible, but rather: *How quickly can we responsibly explore these capabilities?*
## License

See the LICENSE file in this respository.

---

**Pro Tip**: Start with small, specific instructions in `commander.txt` and gradually increase complexity as you become familiar with how the AI interprets your requests.


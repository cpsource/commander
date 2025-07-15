#!/usr/bin/env python3
"""
commander.py - A smart code processor using Gemini 2.5 Pro

This tool reads files (optionally recursively), reads instructions from
commander.txt, and applies those instructions to all files using Gemini AI.

Usage:
    python commander.py [-r] [-x "ext1,ext2,ext3"] [-y]
    
    -r: Process files recursively through subdirectories
    -x: Comma-separated list of file extensions (default: "py")
        Example: -x "py,json,md" or -x "js,html,css"
    -y: Automatically confirm file modifications (skip confirmation prompt)
    
    .skip-commander: Place this file in any directory to skip processing that directory
"""

import os
import sys
import argparse
import glob
from pathlib import Path
from typing import List, Dict, Tuple
import re
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage

def read_system_txt(filename: str = "system.txt") -> str:
    """Read system.txt, skipping comment lines starting with '#'."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        non_comment_lines = [line for line in lines if not line.strip().startswith('#')]
        return "".join(non_comment_lines).strip()
    except FileNotFoundError:
        return ""
    except Exception as e:
        print(f"Error reading {filename}: {e}")
        return ""

class FileProcessor:
    """Handles finding and reading files with specified extensions"""
    
    def __init__(self, recursive: bool = False, extensions: List[str] = None):
        self.recursive = recursive
        self.extensions = extensions if extensions else ['py']
        self.files_found = []
        self.skipped_directories = []
        
    def _should_skip_directory(self, directory_path: Path) -> bool:
        """Check if directory contains .skip-commander file"""
        skip_file = directory_path / ".skip-commander"
        return skip_file.exists()
    
    def _find_files_non_recursive(self, directory: str = ".") -> List[str]:
        """Find files in current directory only (non-recursive mode)"""
        found_files = []
        directory_path = Path(directory)
        
        # Check if current directory should be skipped
        if self._should_skip_directory(directory_path):
            print(f"⏭️  Skipping directory: {directory_path} (contains .skip-commander)")
            self.skipped_directories.append(str(directory_path))
            return found_files
        
        # Search for files with specified extensions in current directory only
        for file_type in self.extensions:
            file_type = file_type.lstrip('.')
            pattern = f"*.{file_type}"
            found_files.extend(directory_path.glob(pattern))
        
        return [str(f) for f in found_files]
    
    def _find_files_recursive(self, directory: str = ".") -> List[str]:
        """Find files recursively, respecting .skip-commander files"""
        found_files = []
        directory_path = Path(directory)
        
        # Check if root directory should be skipped
        if self._should_skip_directory(directory_path):
            print(f"⏭️  Skipping directory: {directory_path} (contains .skip-commander)")
            self.skipped_directories.append(str(directory_path))
            return found_files
        
        # Process current directory first
        for file_type in self.extensions:
            file_type = file_type.lstrip('.')
            # Find files in current directory
            for file_path in directory_path.glob(f"*.{file_type}"):
                if file_path.is_file():
                    found_files.append(file_path)
        
        # Recursively process subdirectories
        for item in directory_path.iterdir():
            if item.is_dir():
                # Skip hidden directories and __pycache__
                if item.name.startswith('.') or item.name.startswith('__pycache__'):
                    continue
                
                # Check if subdirectory should be skipped
                if self._should_skip_directory(item):
                    print(f"⏭️  Skipping directory: {item} (contains .skip-commander)")
                    self.skipped_directories.append(str(item))
                    continue
                
                # Recursively search subdirectory
                subdirectory_files = self._find_files_recursive(str(item))
                found_files.extend(Path(f) for f in subdirectory_files)
        
        return [str(f) for f in found_files]
    
    def find_files(self, directory: str = ".") -> List[str]:
        """Find all files with specified extensions in the directory"""
        if self.recursive:
            found_files = self._find_files_recursive(directory)
        else:
            found_files = self._find_files_non_recursive(directory)
        
        # Filter out unwanted files and convert to strings
        filtered_files = []
        for file_path in found_files:
            file_path_obj = Path(file_path)
            
            # Skip files in __pycache__ or hidden directories
            if not any(part.startswith('__pycache__') or part.startswith('.') 
                      for part in file_path_obj.parts):
                filtered_files.append(str(file_path_obj))
        
        self.files_found = filtered_files
        
        # Report skipped directories
        if self.skipped_directories:
            print(f"\n📁 Skipped {len(self.skipped_directories)} directories due to .skip-commander:")
            for skipped_dir in self.skipped_directories:
                print(f"  • {skipped_dir}")
        
        return filtered_files
    
    def read_file_content(self, file_path: str) -> str:
        """Read the content of a file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Warning: Could not read {file_path}: {e}")
            return ""
    
    def get_language_for_extension(self, file_path: str) -> str:
        """Get the appropriate language identifier for code fencing"""
        extension = Path(file_path).suffix.lower().lstrip('.')
        
        # Map extensions to language identifiers
        language_map = {
            'py': 'python',
            'js': 'javascript',
            'ts': 'typescript',
            'html': 'html',
            'css': 'css',
            'json': 'json',
            'md': 'markdown',
            'yml': 'yaml',
            'yaml': 'yaml',
            'xml': 'xml',
            'sql': 'sql',
            'sh': 'bash',
            'bash': 'bash',
            'txt': '',  # Plain text, no language specifier
            'c': 'c',
            'cpp': 'cpp',
            'java': 'java',
            'php': 'php',
            'rb': 'ruby',
            'go': 'go',
            'rs': 'rust',
        }
        
        return language_map.get(extension, '')


class CommanderInstructions:
    """Handles reading and processing commander.txt instructions"""
    
    def __init__(self, instructions_file: str = "commander.txt"):
        self.instructions_file = instructions_file
        self.instructions = ""
        
    def read_instructions(self) -> str:
        """Read the instructions from commander.txt"""
        try:
            with open(self.instructions_file, 'r', encoding='utf-8') as f:
                self.instructions = f.read().strip()
                return self.instructions
        except FileNotFoundError:
            print(f"Error: {self.instructions_file} not found!")
            print("Please create commander.txt with your processing instructions.")
            sys.exit(1)
        except Exception as e:
            print(f"Error reading {self.instructions_file}: {e}")
            sys.exit(1)


class GeminiProcessor:
    """Handles communication with Gemini AI"""
    
    def __init__(self, api_key: str):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",  # Using the latest available model
            google_api_key=api_key,
            temperature=0.1  # Low temperature for consistent code generation
        )
        
    def create_prompt(self, instructions: str, files_data: Dict[str, Tuple[str, str]]) -> str:
        """Create a comprehensive prompt for Gemini"""
        prompt = f"""You are a skilled developer tasked with modifying multiple files according to specific instructions.

INSTRUCTIONS:
{instructions}

FILES TO PROCESS:
"""
        
        for filename, (content, language) in files_data.items():
            if language:
                prompt += f"\n---{filename}---\n```{language}\n{content}\n```\n"
            else:
                prompt += f"\n---{filename}---\n```\n{content}\n```\n"
        
        prompt += """

RESPONSE FORMAT:
For any files you wish to return in your reply, they must have this format:

---<full-file-spec>---
```<filetype>
< file contents here >
```

Only return files that need to be changed. If a file doesn't need modification, don't include it in your response.
Ensure all code is syntactically correct and follows best practices for the respective language.
"""
        
        return prompt
    
    def process_files(self, instructions: str, files_data: Dict[str, Tuple[str, str]]) -> str:
        """Send files to Gemini for processing"""
        prompt = self.create_prompt(instructions, files_data)
        
        try:
            messages = [
                SystemMessage(content="You are an expert developer who carefully modifies code according to instructions."),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            return response.content
            
        except Exception as e:
            print(f"Error communicating with Gemini: {e}")
            return ""


class ResponseParser:
    """Parses Gemini's response and extracts modified files"""

    def parse_response(self, response: str) -> Dict[str, str]:
        """Parse Gemini's response and extract modified files using simple line-by-line approach."""
        modified_files = {}
        
        # Convert response to lines for processing
        lines = response.split('\n')
        
        i = 0
        # Skip first line if it's ```tool_code
        if i < len(lines) and lines[i].strip() == '```tool_code':
            print("✅ Skipping ```tool_code line")
            i = 1
        
        current_file = None
        file_content = []
        
        while i < len(lines):
            line = lines[i]
            line_stripped = line.strip()
            
            # Check if we're starting a new file
            if line_stripped.startswith('---') and line_stripped.endswith('---') and current_file is None:
                # Extract filespec by chopping off first 3 and last 3 characters
                filespec = line_stripped[3:-3]
                print(f"📄 Found file: {filespec}")
                
                # Skip the next line (the ```<type> line)
                i += 1
                if i < len(lines):
                    print(f"   Skipping: {lines[i].strip()}")
                    i += 1
                
                # Start collecting content for this file
                current_file = filespec
                file_content = []
                print(f"✍️  Processing: {filespec}")
            
            # Check if we're ending current file
            elif line_stripped == '```' and current_file is not None:
                # Determine whether we should skip this ``` line
                next_line_is_new_file_or_eof = False
                if (i + 1) < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line.startswith('---') and next_line.endswith('---'):
                        next_line_is_new_file_or_eof = True
                else:
                    # We are at end-of-file
                    next_line_is_new_file_or_eof = True

                if next_line_is_new_file_or_eof:
                    # Do NOT store this ``` line
                    content = '\n'.join(file_content)
                    modified_files[current_file] = content
                    print(f"✅ Completed: {current_file} ({len(content)} characters)")
                    current_file = None
                    file_content = []
                    i += 1  # skip the ``` line
                    continue
                else:
                    # This ``` belongs in the file content
                    file_content.append(line)
            
            # Collect content for current file
            elif current_file is not None:
                file_content.append(line)
            
            i += 1
        
        # Handle any remaining open file (EOF case)
        if current_file is not None and file_content:
            content = '\n'.join(file_content)
            modified_files[current_file] = content
            print(f"✅ Completed: {current_file} (EOF) ({len(content)} characters)")
        
        return modified_files
    
    def write_modified_files(self, modified_files: Dict[str, str]) -> None:
        """Write the modified files back to disk"""
        for filename, content in modified_files.items():
            try:
                # Ensure directory structure exists (equivalent to mkdir -p)
                file_path = Path(filename)
                if file_path.parent != Path('.'):  # Only if not in current directory
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    print(f"📂 Created directory: {file_path.parent}")
                
                # Create backup
                backup_name = f"{filename}.backup"
                if os.path.exists(filename):
                    os.rename(filename, backup_name)
                    print(f"📁 Created backup: {backup_name}")
                
                # Write new content
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✅ Updated: {filename}")
                
            except Exception as e:
                print(f"❌ Error writing {filename}: {e}")


def parse_extensions(extensions_string: str) -> List[str]:
    """Parse comma-separated extensions string into a list"""
    if not extensions_string:
        return ['py']
    
    # Split by comma and clean up whitespace
    extensions = [ext.strip().lstrip('.') for ext in extensions_string.split(',')]
    # Remove empty strings
    extensions = [ext for ext in extensions if ext]
    
    return extensions if extensions else ['py']


def main():
    """Main execution function"""
    # Load environment variables
    load_dotenv(os.path.expanduser("~/.env"))
    
    # Get API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY not found in ~/.env file")
        print("Please add your Google API key to ~/.env as: GOOGLE_API_KEY=your_key_here")
        sys.exit(1)
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Process files with Gemini AI")
    parser.add_argument("-r", "--recursive", action="store_true", 
                       help="Process files recursively through subdirectories")
    parser.add_argument("-x", "--extensions", type=str, default="py",
                       help="Comma-separated list of file extensions (default: py). Example: 'py,json,md'")
    parser.add_argument("-y", "--yes", action="store_true",
                       help="Automatically confirm file modifications (skip confirmation prompt)")
    parser.add_argument("-f", "--files", type=str,
                        help="Comma-separated list of files to process instead of searching the directory tree."
    )

    args = parser.parse_args()

    file_list = []
    if args.files:
        file_list = [f.strip() for f in args.files.split(",") if f.strip()]

    # Parse extensions
    extensions = parse_extensions(args.extensions)
    
    print("🚀 Commander.py - Multi-Language File Processor")
    print("=" * 50)
    print(f"📋 Target extensions: {', '.join(extensions)}")
    print(f"💡 Tip: Place '.skip-commander' file in directories to skip them")
    
    # Step 1: Find files

    found_files = []
    file_processor = FileProcessor(args.recursive, extensions)

    if file_list:
        # Validate files exist
        missing_files = [f for f in file_list if not os.path.isfile(f)]
        if missing_files:
            print("❌ Error: The following files do not exist:")
            for f in missing_files:
                print(f"  • {f}")
            sys.exit(1)
        else:
            found_files = file_list
            print(f"✅ Using explicitly provided file list ({len(found_files)} files):")
            for f in found_files:
                print(f"  • {f}")
    else:
        print(f"📂 Finding files {'(recursive)' if args.recursive else '(current directory only)'}...")
        found_files = file_processor.find_files()

#    print(f"📂 Finding files {'(recursive)' if args.recursive else '(current directory only)'}...")
#    file_processor = FileProcessor(args.recursive, extensions)
#    found_files = file_processor.find_files()
    
    if not found_files:
        print(f"No files found with extensions: {', '.join(extensions)}")
        if file_processor.skipped_directories:
            print("(Some directories were skipped due to .skip-commander files)")
        sys.exit(1)
    
    print(f"Found {len(found_files)} files:")
    for file in found_files:
        print(f"  • {file}")

    # Step 2a: Read system.txt
    print("\n📋 Reading system.txt (if exists)...")
    system_text = read_system_txt()
    if system_text:
        print(f"Instructions loaded: {len(system_text)} characters")
    
    # Step 2b: Read instructions
    print("\n📋 Reading instructions from commander.txt...")
    instructions_reader = CommanderInstructions()
    instructions = instructions_reader.read_instructions()
    print(f"Instructions loaded: {len(instructions)} characters")

    # Combine system and commander instructions
    if system_text:
        instructions = system_text + "\n\n" + instructions
    
    # Step 3: Read file contents
    print("\n📖 Reading file contents...")
    files_data = {}
    for file_path in found_files:
        content = file_processor.read_file_content(file_path)
        if content:
            language = file_processor.get_language_for_extension(file_path)
            files_data[file_path] = (content, language)
            print(f"  • Read {file_path}: {len(content)} characters [{language or 'text'}]")
    
    if not files_data:
        print("No files could be read!")
        sys.exit(1)

    # debug - stop for now
    #print("Exiting")
    #sys.exit(0)
    
    # Step 4: Process with Gemini
    print("\n🤖 Processing files with Gemini AI...")
    gemini_processor = GeminiProcessor(api_key)
    response = gemini_processor.process_files(instructions, files_data)
    
    if not response:
        print("No response from Gemini!")
        sys.exit(1)
    
    print(f"Received response: {len(response)} characters")
    # Write Gemini response to commander.log
    try:
        with open("commander.log", "w", encoding="utf-8") as log_file:
            log_file.write(response)
        print(f"✅ Gemini response saved to commander.log ({len(response)} characters)")
    except Exception as e:
        print(f"❌ Failed to write commander.log: {e}")

#    print(response)
    
    # Step 5: Parse response and update files
    print("\n🔄 Parsing response and updating files...")
    response_parser = ResponseParser()
    modified_files = response_parser.parse_response(response)

    # Patch - ensure directories exist before writing files
    for filename in modified_files.keys():
        file_path = Path(filename)
        if file_path.parent != Path('.'):
            try:
                file_path.parent.mkdir(parents=True, exist_ok=True)
                print(f"📂 Ensured directory exists: {file_path.parent}")
            except Exception as e:
                print(f"❌ Failed to create directory {file_path.parent}: {e}")
            
    if not modified_files:
        print("No files were modified by Gemini.")
        return
    
    print(f"Files to be modified: {len(modified_files)}")
    for filename in modified_files.keys():
        print(f"  • {filename}")
    
    # Ask for confirmation
    if args.yes:
        print("\nAuto-confirming file modifications (--yes flag provided)")
    else:
        confirm = input("\nProceed with file modifications? (y/N): ")
        if confirm.lower() != 'y':
            print("Operation cancelled.")
            return
    
    # Write modified files
    response_parser.write_modified_files(modified_files)
    
    print("\n✨ Processing complete!")
    print("Backups created with .backup extension")
    
    if file_processor.skipped_directories:
        print(f"\n📁 Note: {len(file_processor.skipped_directories)} directories were skipped due to .skip-commander files")


if __name__ == "__main__":
    main()

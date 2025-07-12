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


class FileProcessor:
    """Handles finding and reading files with specified extensions"""
    
    def __init__(self, recursive: bool = False, extensions: List[str] = None):
        self.recursive = recursive
        self.extensions = extensions if extensions else ['py']
        self.files_found = []
        
    def find_files(self, directory: str = ".") -> List[str]:
        """Find all files with specified extensions in the directory"""
        found_files = []
        
        # Search one extension at a time
        for file_type in self.extensions:
            # Remove leading dot if present
            file_type = file_type.lstrip('.')
            pattern = f"**/*.{file_type}" if self.recursive else f"*.{file_type}"
            found_files.extend(Path(directory).glob(pattern))
        
        # Filter out __pycache__ and other unwanted directories
        filtered_files = []
        for file_path in found_files:
            if not any(part.startswith('__pycache__') or part.startswith('.') 
                      for part in file_path.parts):
                filtered_files.append(str(file_path))
        
        self.files_found = filtered_files
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
Please return the modified files in the exact same format, with each file preceded by its filename marker and appropriate code fencing:
---filename.ext---
```language
[modified code here]
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
        """Parse Gemini's response and extract modified files"""
        modified_files = {}
        
        # Pattern to match file blocks: ---filename--- followed by ```language code ```
        # Made more flexible to handle different languages
        pattern = r'---([^-]+)---\s*```(?:\w+)?\s*\n(.*?)\n```'
        matches = re.findall(pattern, response, re.DOTALL)
        
        for filename, code in matches:
            filename = filename.strip()
            code = code.strip()
            modified_files[filename] = code
            
        return modified_files
    
    def write_modified_files(self, modified_files: Dict[str, str]) -> None:
        """Write the modified files back to disk"""
        for filename, content in modified_files.items():
            try:
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
    args = parser.parse_args()
    
    # Parse extensions
    extensions = parse_extensions(args.extensions)
    
    print("🚀 Commander.py - Multi-Language File Processor")
    print("=" * 50)
    print(f"📋 Target extensions: {', '.join(extensions)}")
    
    # Step 1: Find files
    print(f"📂 Finding files {'(recursive)' if args.recursive else '(current directory only)'}...")
    file_processor = FileProcessor(args.recursive, extensions)
    found_files = file_processor.find_files()
    
    if not found_files:
        print(f"No files found with extensions: {', '.join(extensions)}")
        sys.exit(1)
    
    print(f"Found {len(found_files)} files:")
    for file in found_files:
        print(f"  • {file}")
    
    # Step 2: Read instructions
    print("\n📋 Reading instructions from commander.txt...")
    instructions_reader = CommanderInstructions()
    instructions = instructions_reader.read_instructions()
    print(f"Instructions loaded: {len(instructions)} characters")
    
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
    
    # Step 4: Process with Gemini
    print("\n🤖 Processing files with Gemini AI...")
    gemini_processor = GeminiProcessor(api_key)
    response = gemini_processor.process_files(instructions, files_data)
    
    if not response:
        print("No response from Gemini!")
        sys.exit(1)
    
    print(f"Received response: {len(response)} characters")
    
    # Step 5: Parse response and update files
    print("\n🔄 Parsing response and updating files...")
    response_parser = ResponseParser()
    modified_files = response_parser.parse_response(response)
    
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


if __name__ == "__main__":
    main()


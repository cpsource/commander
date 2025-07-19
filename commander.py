#!/usr/bin/env python3
"""
commander.py - A smart code processor using multiple LLM providers

This tool reads files (optionally recursively), reads instructions from
commander.txt, and applies those instructions to all files using various AI models.

Usage:
    python commander.py [-r] [-x "ext1,ext2,ext3"] [-y] [-m model]
    
    -r: Process files recursively through subdirectories
    -x: Comma-separated list of file extensions (default: "py")
        Example: -x "py,json,md" or -x "js,html,css" or -x "docx,txt"
    -y: Automatically confirm file modifications (skip confirmation prompt)
    -m: Model to use (default: "gemini")
        Options: gemini, claude, chatgpt, xai, watsonx
    
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

# Determine the script's home directory and add to Python path
SCRIPT_DIR = Path(__file__).parent.absolute()
sys.path.insert(0, str(SCRIPT_DIR))

# Import the comutl library
try:
    from comutl import get_llm_class, MODEL_REGISTRY
except ImportError as e:
    print(f"❌ Error importing comutl library: {e}")
    print(f"📂 Script directory: {SCRIPT_DIR}")
    print(f"🐍 Python path: {sys.path}")
    print("💡 Make sure the comutl/ directory exists in the same location as commander.py")
    sys.exit(1)

def read_system_txt(filename: str = "system.txt") -> str:
    """Read system.txt, skipping comment lines starting with '#'."""
    # Try current directory first, then script directory
    search_paths = [Path.cwd() / filename, SCRIPT_DIR / filename]
    
    for path in search_paths:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            non_comment_lines = [line for line in lines if not line.strip().startswith('#')]
            print(f"📋 Found {filename} at: {path}")
            return "".join(non_comment_lines).strip()
        except FileNotFoundError:
            continue
        except Exception as e:
            print(f"Error reading {path}: {e}")
            continue
    
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
    
    def read_docx_content(self, file_path: str) -> str:
        """Read content from a .docx file"""
        try:
            import mammoth
            with open(file_path, 'rb') as docx_file:
                result = mammoth.extract_raw_text(docx_file)
                return result.value
        except ImportError:
            print(f"⚠️  mammoth library required for .docx files. Install with: pip install mammoth")
            print(f"⚠️  Skipping {file_path}")
            return ""
        except Exception as e:
            print(f"Warning: Could not read .docx file {file_path}: {e}")
            return ""
    
    def read_file_content(self, file_path: str) -> str:
        """Read the content of a file"""
        file_extension = Path(file_path).suffix.lower()
        
        # Handle .docx files specially
        if file_extension == '.docx':
            return self.read_docx_content(file_path)
        
        # Handle regular text files
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Try different encodings for text files
            for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        print(f"⚠️  Used {encoding} encoding for {file_path}")
                        return f.read()
                except UnicodeDecodeError:
                    continue
            print(f"Warning: Could not decode {file_path} with any common encoding")
            return ""
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
            'txt': 'text',
            'docx': 'text',  # .docx files are treated as text
            'doc': 'text',   # .doc files (if supported in future)
            'c': 'c',
            'cpp': 'cpp',
            'java': 'java',
            'php': 'php',
            'rb': 'ruby',
            'go': 'go',
            'rs': 'rust',
        }
        
        return language_map.get(extension, 'text')


class CommanderInstructions:
    """Handles reading and processing commander.txt instructions"""
    
    def __init__(self, instructions_file: str = "commander.txt"):
        self.instructions_file = instructions_file
        self.instructions = ""
        
    def read_instructions(self) -> str:
        """Read the instructions from commander.txt"""
        # Try current directory first, then script directory
        search_paths = [Path.cwd() / self.instructions_file, SCRIPT_DIR / self.instructions_file]
        
        for path in search_paths:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    self.instructions = f.read().strip()
                    print(f"📋 Found {self.instructions_file} at: {path}")
                    return self.instructions
            except FileNotFoundError:
                continue
            except Exception as e:
                print(f"Error reading {path}: {e}")
                continue
        
        print(f"Error: {self.instructions_file} not found!")
        print("Searched in:")
        for path in search_paths:
            print(f"  • {path}")
        print(f"Please create {self.instructions_file} with your processing instructions.")
        sys.exit(1)

class ResponseParser:
    """Parses LLM response and extracts modified files with optional debugging"""
    
    def __init__(self, use_debugging: bool = False):
        self.use_debugging = use_debugging

    def parse_response(self, response: str) -> Dict[str, str]:
        """Parse LLM response and extract modified files using simple line-by-line approach."""
        modified_files = {}
        
        if self.use_debugging:
            print(f"🔍 DEBUG: Full response length: {len(response)}")
            print(f"🔍 DEBUG: Full response:")
            print("=" * 50)
            print(repr(response))  # Show exact characters including newlines
            print("=" * 50)
        
        # Convert response to lines for processing
        lines = response.split('\n')
        
        if self.use_debugging:
            print(f"🔍 DEBUG: Split into {len(lines)} lines:")
            for idx, line in enumerate(lines):
                print(f"  Line {idx}: {repr(line)}")
        
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
            
            if self.use_debugging:
                print(f"🔍 DEBUG: Processing line {i}: {repr(line)} (stripped: {repr(line_stripped)})")
            
            # Check if we're starting a new file
            if line_stripped.startswith('---') and line_stripped.endswith('---') and current_file is None:
                # Extract filespec by chopping off first 3 and last 3 characters
                filespec = line_stripped[3:-3]
                print(f"📄 Found file: {filespec}")
                
                # Skip the next line (the ```<type> line)
                i += 1
                if i < len(lines):
                    print(f"   Skipping line {i}: {repr(lines[i])}" if self.use_debugging else f"   Skipping: {lines[i].strip()}")
                    i += 1
                
                # Start collecting content for this file
                current_file = filespec
                file_content = []
                print(f"✍️  Processing: {filespec}")
                continue
            
            # Check if we're ending current file
            elif line_stripped == '```' and current_file is not None:
                if self.use_debugging:
                    print(f"🔍 DEBUG: Found closing ``` for file {current_file}")
                    print(f"🔍 DEBUG: Current file_content has {len(file_content)} lines: {file_content}")
                
                # Check if next line is a new file OR we're at end of response
                next_line_is_new_file_or_eof = False
                if (i + 1) < len(lines):
                    next_line = lines[i + 1].strip()
                    if self.use_debugging:
                        print(f"🔍 DEBUG: Next line {i+1}: {repr(next_line)}")
                    if next_line.startswith('---') and next_line.endswith('---'):
                        next_line_is_new_file_or_eof = True
                        if self.use_debugging:
                            print("🔍 DEBUG: Next line is a new file")
                    elif not next_line:  # Empty line after ``` - check line after that
                        if (i + 2) >= len(lines):  # No more lines after empty line
                            next_line_is_new_file_or_eof = True
                            if self.use_debugging:
                                print("🔍 DEBUG: Empty line and EOF")
                        else:
                            next_next_line = lines[i + 2].strip()
                            if self.use_debugging:
                                print(f"🔍 DEBUG: Line after empty {i+2}: {repr(next_next_line)}")
                            if next_next_line.startswith('---') and next_next_line.endswith('---'):
                                next_line_is_new_file_or_eof = True
                                if self.use_debugging:
                                    print("🔍 DEBUG: Line after empty is new file")
                    else:
                        if self.use_debugging:
                            print("🔍 DEBUG: Next line is not empty and not new file")
                else:
                    # We are at end-of-file
                    next_line_is_new_file_or_eof = True
                    if self.use_debugging:
                        print("🔍 DEBUG: At end of file")

                if next_line_is_new_file_or_eof:
                    # Do NOT store this ``` line
                    content = '\n'.join(file_content)
                    modified_files[current_file] = content
                    print(f"✅ Completed: {current_file} ({len(content)} characters)")
                    if self.use_debugging:
                        print(f"🔍 DEBUG: File content: {repr(content)}")
                    current_file = None
                    file_content = []
                    i += 1  # skip the ``` line
                    continue
                else:
                    # This ``` belongs in the file content
                    if self.use_debugging:
                        print("🔍 DEBUG: ``` belongs to file content")
                    file_content.append(line)
            
            # Collect content for current file
            elif current_file is not None:
                if self.use_debugging:
                    print(f"🔍 DEBUG: Adding to file content: {repr(line)}")
                file_content.append(line)
            else:
                if self.use_debugging:
                    print(f"🔍 DEBUG: Ignoring line outside file: {repr(line)}")
            
            i += 1
        
        # Handle any remaining open file (EOF case)
        if current_file is not None:
            if self.use_debugging:
                print(f"🔍 DEBUG: EOF - finishing file {current_file} with {len(file_content)} lines")
                print(f"🔍 DEBUG: Final file_content: {file_content}")
            content = '\n'.join(file_content)
            modified_files[current_file] = content
            print(f"✅ Completed: {current_file} (EOF) ({len(content)} characters)")
            if self.use_debugging:
                print(f"🔍 DEBUG: Final content: {repr(content)}")
        
        if self.use_debugging:
            print(f"🔍 FINAL DEBUG: Found {len(modified_files)} files total")
            for filename, content in modified_files.items():
                print(f"  📄 {filename}: {len(content)} chars")
                print(f"     Content: {repr(content)}")
        
        return modified_files
    
    def write_modified_files(self, modified_files: Dict[str, str]) -> None:
        """Write the modified files back to disk"""
        if self.use_debugging:
            print(f"🔍 DEBUG: write_modified_files called with {len(modified_files)} files")
        
        for filename, content in modified_files.items():
            if self.use_debugging:
                print(f"🔍 DEBUG: Writing file {filename} with content: {repr(content)}")
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
                
                # Check if this is a .docx file - we can't write those back
                if filename.lower().endswith('.docx'):
                    print(f"⚠️  Cannot write back to .docx format. Saving as {filename}.txt instead")
                    filename = f"{filename}.txt"
                
                # Write new content
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✅ Updated: {filename}")
                
                # Verify the file was written (only in debug mode)
                if self.use_debugging:
                    with open(filename, 'r', encoding='utf-8') as f:
                        written_content = f.read()
                        print(f"🔍 DEBUG: Verified file contents: {repr(written_content)}")
                
            except Exception as e:
                print(f"❌ Error writing {filename}: {e}")
                if self.use_debugging:
                    import traceback
                    traceback.print_exc()        
        
class ResponseParser2:
    """Parses LLM response and extracts modified files with detailed debugging"""

    def parse_response(self, response: str) -> Dict[str, str]:
        """Parse LLM response and extract modified files using simple line-by-line approach."""
        modified_files = {}
        
        print(f"🔍 DEBUG: Full response length: {len(response)}")
        print(f"🔍 DEBUG: Full response:")
        print("=" * 50)
        print(repr(response))  # Show exact characters including newlines
        print("=" * 50)
        
        # Convert response to lines for processing
        lines = response.split('\n')
        print(f"🔍 DEBUG: Split into {len(lines)} lines:")
        for idx, line in enumerate(lines):
            print(f"  Line {idx}: {repr(line)}")
        
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
            print(f"🔍 DEBUG: Processing line {i}: {repr(line)} (stripped: {repr(line_stripped)})")
            
            # Check if we're starting a new file
            if line_stripped.startswith('---') and line_stripped.endswith('---') and current_file is None:
                # Extract filespec by chopping off first 3 and last 3 characters
                filespec = line_stripped[3:-3]
                print(f"📄 Found file: {filespec}")
                
                # Skip the next line (the ```<type> line)
                i += 1
                if i < len(lines):
                    print(f"   Skipping line {i}: {repr(lines[i])}")
                    i += 1
                
                # Start collecting content for this file
                current_file = filespec
                file_content = []
                print(f"✍️  Processing: {filespec}")
                continue
            
            # Check if we're ending current file
            elif line_stripped == '```' and current_file is not None:
                print(f"🔍 DEBUG: Found closing ``` for file {current_file}")
                print(f"🔍 DEBUG: Current file_content has {len(file_content)} lines: {file_content}")
                
                # Check if next line is a new file OR we're at end of response
                next_line_is_new_file_or_eof = False
                if (i + 1) < len(lines):
                    next_line = lines[i + 1].strip()
                    print(f"🔍 DEBUG: Next line {i+1}: {repr(next_line)}")
                    if next_line.startswith('---') and next_line.endswith('---'):
                        next_line_is_new_file_or_eof = True
                        print("🔍 DEBUG: Next line is a new file")
                    elif not next_line:  # Empty line after ``` - check line after that
                        if (i + 2) >= len(lines):  # No more lines after empty line
                            next_line_is_new_file_or_eof = True
                            print("🔍 DEBUG: Empty line and EOF")
                        else:
                            next_next_line = lines[i + 2].strip()
                            print(f"🔍 DEBUG: Line after empty {i+2}: {repr(next_next_line)}")
                            if next_next_line.startswith('---') and next_next_line.endswith('---'):
                                next_line_is_new_file_or_eof = True
                                print("🔍 DEBUG: Line after empty is new file")
                    else:
                        print("🔍 DEBUG: Next line is not empty and not new file")
                else:
                    # We are at end-of-file
                    next_line_is_new_file_or_eof = True
                    print("🔍 DEBUG: At end of file")

                if next_line_is_new_file_or_eof:
                    # Do NOT store this ``` line
                    content = '\n'.join(file_content)
                    modified_files[current_file] = content
                    print(f"✅ Completed: {current_file} ({len(content)} characters)")
                    print(f"🔍 DEBUG: File content: {repr(content)}")
                    current_file = None
                    file_content = []
                    i += 1  # skip the ``` line
                    continue
                else:
                    # This ``` belongs in the file content
                    print("🔍 DEBUG: ``` belongs to file content")
                    file_content.append(line)
            
            # Collect content for current file
            elif current_file is not None:
                print(f"🔍 DEBUG: Adding to file content: {repr(line)}")
                file_content.append(line)
            else:
                print(f"🔍 DEBUG: Ignoring line outside file: {repr(line)}")
            
            i += 1
        
        # Handle any remaining open file (EOF case)
        if current_file is not None:
            print(f"🔍 DEBUG: EOF - finishing file {current_file} with {len(file_content)} lines")
            print(f"🔍 DEBUG: Final file_content: {file_content}")
            content = '\n'.join(file_content)
            modified_files[current_file] = content
            print(f"✅ Completed: {current_file} (EOF) ({len(content)} characters)")
            print(f"🔍 DEBUG: Final content: {repr(content)}")
        
        print(f"🔍 FINAL DEBUG: Found {len(modified_files)} files total")
        for filename, content in modified_files.items():
            print(f"  📄 {filename}: {len(content)} chars")
            print(f"     Content: {repr(content)}")
        
        return modified_files
    
    def write_modified_files(self, modified_files: Dict[str, str]) -> None:
        """Write the modified files back to disk"""
        print(f"🔍 DEBUG: write_modified_files called with {len(modified_files)} files")
        
        for filename, content in modified_files.items():
            print(f"🔍 DEBUG: Writing file {filename} with content: {repr(content)}")
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
                
                # Check if this is a .docx file - we can't write those back
                if filename.lower().endswith('.docx'):
                    print(f"⚠️  Cannot write back to .docx format. Saving as {filename}.txt instead")
                    filename = f"{filename}.txt"
                
                # Write new content
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✅ Updated: {filename}")
                
                # Verify the file was written
                with open(filename, 'r', encoding='utf-8') as f:
                    written_content = f.read()
                    print(f"🔍 DEBUG: Verified file contents: {repr(written_content)}")
                
            except Exception as e:
                print(f"❌ Error writing {filename}: {e}")
                import traceback
                traceback.print_exc()
        
class ResponseParser1:
    """Parses LLM response and extracts modified files"""

    def parse_response(self, response: str) -> Dict[str, str]:
        """Parse LLM response and extract modified files using simple line-by-line approach."""
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
                # Check if next line is a new file OR we're at end of response
                next_line_is_new_file_or_eof = False
                if (i + 1) < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line.startswith('---') and next_line.endswith('---'):
                        next_line_is_new_file_or_eof = True
                    elif not next_line:  # Empty line after ``` - check line after that
                        if (i + 2) >= len(lines):  # No more lines after empty line
                            next_line_is_new_file_or_eof = True
                        else:
                            next_next_line = lines[i + 2].strip()
                            if next_next_line.startswith('---') and next_next_line.endswith('---'):
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
        
        # IMPROVED: Handle any remaining open file (EOF case) - even without final newline
        if current_file is not None:
            content = '\n'.join(file_content)
            modified_files[current_file] = content
            print(f"✅ Completed: {current_file} (EOF without final newline) ({len(content)} characters)")
        
        # Additional debug info
        print(f"🔍 Parser debug: Found {len(modified_files)} files in response")
        for filename, content in modified_files.items():
            print(f"  📄 {filename}: {len(content)} chars, ends with: {repr(content[-20:]) if content else 'empty'}")
        
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
                
                # Check if this is a .docx file - we can't write those back
                if filename.lower().endswith('.docx'):
                    print(f"⚠️  Cannot write back to .docx format. Saving as {filename}.txt instead")
                    filename = f"{filename}.txt"
                
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


def get_api_key_for_model(model_name: str) -> str:
    """Get the appropriate API key for the specified model"""
    # Mapping of model names to their expected environment variables
    env_var_map = {
        'gemini': 'GOOGLE_API_KEY',
        'claude': 'ANTHROPIC_API_KEY',
        'chatgpt': 'OPENAI_API_KEY',
        'xai': 'XAI_API_KEY',
        'watsonx': 'WATSONX_API_KEY'
    }
    
    env_var = env_var_map.get(model_name)
    if not env_var:
        raise ValueError(f"Unknown model: {model_name}")
    
    api_key = os.getenv(env_var)
    if not api_key:
        print(f"Error: {env_var} not found in ~/.env file")
        print(f"Please add your {model_name} API key to ~/.env as: {env_var}=your_key_here")
        sys.exit(1)
    
    return api_key


def main():
    """Main execution function"""
    # Load environment variables from multiple locations
    env_paths = [
        os.path.expanduser("~/.env"),  # User home directory
        Path.cwd() / ".env",           # Current working directory
        SCRIPT_DIR / ".env"            # Script directory
    ]
    
    for env_path in env_paths:
        if Path(env_path).exists():
            load_dotenv(env_path)
            print(f"🔧 Loaded environment from: {env_path}")
            break
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Process files with various LLM providers")
    parser.add_argument("-r", "--recursive", action="store_true", 
                       help="Process files recursively through subdirectories")
    parser.add_argument("-x", "--extensions", type=str, default="py",
                       help="Comma-separated list of file extensions (default: py). Example: 'py,json,md,docx'")
    parser.add_argument("-y", "--yes", action="store_true",
                       help="Automatically confirm file modifications (skip confirmation prompt)")
    parser.add_argument("-m", "--model", type=str, default="gemini",
                       choices=list(MODEL_REGISTRY.keys()),
                       help=f"Model to use (default: gemini). Options: {', '.join(MODEL_REGISTRY.keys())}")
    parser.add_argument("-f", "--files", type=str,
                        help="Comma-separated list of files to process instead of searching the directory tree."
    )

    args = parser.parse_args()

    file_list = []
    if args.files:
        file_list = [f.strip() for f in args.files.split(",") if f.strip()]

    # Parse extensions
    extensions = parse_extensions(args.extensions)
    
    # Get API key for selected model
    api_key = get_api_key_for_model(args.model)
    
    # Get additional config for WatsonX
    additional_config = {}
    if args.model == 'watsonx':
        project_id = os.getenv('WATSONX_PROJECT_ID')
        if not project_id:
            print("Error: WATSONX_PROJECT_ID not found in ~/.env file")
            print("Please add your WatsonX project ID to ~/.env as: WATSONX_PROJECT_ID=your_project_id")
            sys.exit(1)
        additional_config['project_id'] = project_id
    
    print("🚀 Commander.py - Multi-Language File Processor")
    print("=" * 50)
    print(f"📂 Script directory: {SCRIPT_DIR}")
    print(f"📂 Working directory: {Path.cwd()}")
    print(f"🤖 Using model: {args.model}")
    print(f"📋 Target extensions: {', '.join(extensions)}")
    print(f"💡 Tip: Place '.skip-commander' file in directories to skip them")
    
    # Check if docx files are being processed and warn about mammoth dependency
    if 'docx' in extensions:
        print(f"📄 Note: .docx files require 'mammoth' library. Install with: pip install mammoth")
    
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
    
    # Step 4: Initialize LLM processor
    print(f"\n🤖 Initializing {args.model} LLM processor...")
    try:
        llm_class = get_llm_class(args.model)
        llm_processor = llm_class(api_key, **additional_config)
        print(f"✅ {llm_processor.model_name} processor initialized")
    except Exception as e:
        print(f"❌ Error initializing {args.model} processor: {e}")
        sys.exit(1)
    
    # Step 5: Process with LLM
    print(f"\n🤖 Processing files with {llm_processor.model_name}...")
    response = llm_processor.process_files(instructions, files_data)
    
    if not response:
        print("No response from LLM!")
        sys.exit(1)
    
    print(f"Received response: {len(response)} characters")
 
    # Write LLM response to commander.log (in current working directory)
    log_file_path = Path.cwd() / "commander.log"
    try:
        with open(log_file_path, "w", encoding="utf-8") as log_file:
            log_file.write(response)
        print(f"✅ LLM response saved to {log_file_path} ({len(response)} characters)")
    except Exception as e:
        print(f"❌ Failed to write {log_file_path}: {e}")

    # Step 6: Parse response and update files
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

    # Write pretty-printed JSON metadata to commander.json (in current working directory)
    # MOVED HERE - after modified_files is defined
    json_file_path = Path.cwd() / "commander.json"
    try:
        import json
        from datetime import datetime
    
        # Create metadata about the processing session
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "script_directory": str(SCRIPT_DIR),
            "working_directory": str(Path.cwd()),
            "model": args.model,
            "model_name": llm_processor.model_name,
            "files_processed": list(files_data.keys()),
            "file_count": len(files_data),
            "extensions": extensions,
            "recursive": args.recursive,
            "instructions_length": len(instructions),
            "response_length": len(response),
            "modified_files": list(modified_files.keys()),  # Now this works correctly
            "modified_files_count": len(modified_files),    # Added count for easier reference
            "settings": {
                "auto_confirm": args.yes,
                "files_parameter": args.files if args.files else None
            }
        }
    
        with open(json_file_path, "w", encoding="utf-8") as json_file:
            json.dump(metadata, json_file, indent=2, ensure_ascii=False)
        print(f"✅ Processing metadata saved to {json_file_path}")
    
    except Exception as e:
        print(f"❌ Failed to write {json_file_path}: {e}")
            
    if not modified_files:
        print("No files were modified by LLM.")
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
    print(f"📄 Log files saved to: {Path.cwd()}")
    
    if file_processor.skipped_directories:
        print(f"\n📁 Note: {len(file_processor.skipped_directories)} directories were skipped due to .skip-commander files")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
docx_to_markdown.py - Convert .docx files to Markdown format

This tool converts Microsoft Word .docx files to Markdown format with support for:
- Headings (H1-H6)
- Bold and italic text
- Lists (ordered and unordered)
- Links
- Images (with extraction)
- Tables
- Code blocks
- Paragraphs

Usage:
    python docx_to_markdown.py input.docx [output.md]
    python docx_to_markdown.py -d directory/  # Convert all .docx files in directory
    python docx_to_markdown.py -r directory/  # Convert recursively
    
Options:
    -d, --directory    Convert all .docx files in specified directory
    -r, --recursive    Process directories recursively
    -i, --images       Extract and save images (creates images/ folder)
    -o, --output       Output directory (default: same as input)
    -v, --verbose      Show detailed processing information
    -h, --help         Show this help message
"""

import os
import sys
import argparse
import re
from pathlib import Path
from typing import List, Optional, Dict, Any
import zipfile
import xml.etree.ElementTree as ET

# Check for required dependencies
try:
    import mammoth
    MAMMOTH_AVAILABLE = True
except ImportError:
    MAMMOTH_AVAILABLE = False

try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False


class DocxToMarkdownConverter:
    """Converts .docx files to Markdown format"""
    
    def __init__(self, extract_images: bool = False, verbose: bool = False):
        self.extract_images = extract_images
        self.verbose = verbose
        self.images_extracted = 0
        
        if not MAMMOTH_AVAILABLE:
            print("❌ Error: mammoth library is required")
            print("Install with: pip install mammoth")
            sys.exit(1)
    
    def log(self, message: str) -> None:
        """Log message if verbose mode is enabled"""
        if self.verbose:
            print(f"📝 {message}")
    
    def extract_images_from_docx(self, docx_path: str, output_dir: str) -> Dict[str, str]:
        """Extract images from .docx file and return mapping of old->new paths"""
        images_dir = Path(output_dir) / "images"
        images_dir.mkdir(exist_ok=True)
        
        image_mapping = {}
        
        try:
            with zipfile.ZipFile(docx_path, 'r') as zip_ref:
                # Find all image files in the docx
                image_files = [f for f in zip_ref.namelist() if f.startswith('word/media/')]
                
                for img_file in image_files:
                    # Extract the image
                    img_data = zip_ref.read(img_file)
                    
                    # Get the original filename
                    img_name = Path(img_file).name
                    
                    # Save to images directory
                    img_path = images_dir / img_name
                    with open(img_path, 'wb') as f:
                        f.write(img_data)
                    
                    # Create mapping for markdown links
                    image_mapping[img_file] = f"images/{img_name}"
                    self.images_extracted += 1
                    self.log(f"Extracted image: {img_name}")
        
        except Exception as e:
            self.log(f"Warning: Could not extract images: {e}")
        
        return image_mapping
    
    def clean_markdown(self, markdown_text: str) -> str:
        """Clean up and improve the markdown output"""
        # Remove extra whitespace
        markdown_text = re.sub(r'\n\s*\n\s*\n', '\n\n', markdown_text)
        
        # Fix heading spacing
        markdown_text = re.sub(r'^(#{1,6})\s*(.+)$', r'\1 \2', markdown_text, flags=re.MULTILINE)
        
        # Fix list formatting
        markdown_text = re.sub(r'^(\s*[\*\-\+])\s*(.+)$', r'\1 \2', markdown_text, flags=re.MULTILINE)
        markdown_text = re.sub(r'^(\s*\d+\.)\s*(.+)$', r'\1 \2', markdown_text, flags=re.MULTILINE)
        
        # Fix bold/italic formatting
        markdown_text = re.sub(r'\*\*\s+(.+?)\s+\*\*', r'**\1**', markdown_text)
        markdown_text = re.sub(r'\*\s+(.+?)\s+\*', r'*\1*', markdown_text)
        
        # Remove trailing whitespace
        lines = [line.rstrip() for line in markdown_text.split('\n')]
        markdown_text = '\n'.join(lines)
        
        # Ensure single trailing newline
        markdown_text = markdown_text.rstrip() + '\n'
        
        return markdown_text
    
    def convert_file(self, input_path: str, output_path: Optional[str] = None) -> str:
        """Convert a single .docx file to markdown"""
        input_path = Path(input_path)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        if input_path.suffix.lower() != '.docx':
            raise ValueError(f"Input file must be .docx format: {input_path}")
        
        # Determine output path
        if output_path is None:
            output_path = input_path.with_suffix('.md')
        else:
            output_path = Path(output_path)
        
        # Create output directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.log(f"Converting: {input_path} -> {output_path}")
        
        # Extract images if requested
        image_mapping = {}
        if self.extract_images:
            image_mapping = self.extract_images_from_docx(str(input_path), str(output_path.parent))
        
        try:
            # Configure mammoth for better markdown conversion
            style_map = """
                p[style-name='Heading 1'] => h1
                p[style-name='Heading 2'] => h2
                p[style-name='Heading 3'] => h3
                p[style-name='Heading 4'] => h4
                p[style-name='Heading 5'] => h5
                p[style-name='Heading 6'] => h6
                p[style-name='Code'] => pre
                p[style-name='Quote'] => blockquote
                r[style-name='Code Char'] => code
            """
            
            # Convert to markdown
            with open(input_path, 'rb') as docx_file:
                result = mammoth.convert_to_markdown(
                    docx_file,
                    style_map=style_map,
                    convert_image=mammoth.images.img_element(self._image_converter) if self.extract_images else None
                )
                
                markdown_content = result.value
                
                # Log any warnings
                if result.messages:
                    for message in result.messages:
                        self.log(f"Warning: {message}")
        
        except Exception as e:
            raise RuntimeError(f"Failed to convert {input_path}: {e}")
        
        # Clean up the markdown
        markdown_content = self.clean_markdown(markdown_content)
        
        # Write the output
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            self.log(f"✅ Successfully converted: {output_path}")
            return str(output_path)
            
        except Exception as e:
            raise RuntimeError(f"Failed to write output file {output_path}: {e}")
    
    def _image_converter(self, image):
        """Convert images for mammoth"""
        # This is a placeholder - mammoth handles image conversion
        # when extract_images is True
        return {}
    
    def convert_directory(self, directory: str, recursive: bool = False, output_dir: Optional[str] = None) -> List[str]:
        """Convert all .docx files in a directory"""
        directory = Path(directory)
        
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        if not directory.is_dir():
            raise ValueError(f"Path is not a directory: {directory}")
        
        # Find all .docx files
        if recursive:
            docx_files = list(directory.rglob("*.docx"))
        else:
            docx_files = list(directory.glob("*.docx"))
        
        if not docx_files:
            print(f"No .docx files found in {directory}")
            return []
        
        print(f"Found {len(docx_files)} .docx file(s) to convert")
        
        converted_files = []
        
        for docx_file in docx_files:
            try:
                # Determine output path
                if output_dir:
                    output_path = Path(output_dir) / docx_file.with_suffix('.md').name
                else:
                    output_path = docx_file.with_suffix('.md')
                
                # Convert the file
                result = self.convert_file(str(docx_file), str(output_path))
                converted_files.append(result)
                
            except Exception as e:
                print(f"❌ Error converting {docx_file}: {e}")
                continue
        
        return converted_files


def show_requirements():
    """Show required dependencies and installation instructions"""
    print("📦 Required Dependencies:")
    print("=" * 40)
    
    if not MAMMOTH_AVAILABLE:
        print("❌ mammoth - REQUIRED for .docx conversion")
        print("   Install with: pip install mammoth")
    else:
        print("✅ mammoth - Available")
    
    if not PILLOW_AVAILABLE:
        print("⚠️  Pillow - Optional for image processing")
        print("   Install with: pip install Pillow")
    else:
        print("✅ Pillow - Available")
    
    print("\nFull installation command:")
    print("pip install mammoth Pillow")


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description="Convert .docx files to Markdown format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python docx_to_markdown.py document.docx
    python docx_to_markdown.py document.docx output.md
    python docx_to_markdown.py -d documents/
    python docx_to_markdown.py -r -i projects/
    python docx_to_markdown.py -v document.docx
        """
    )
    
    parser.add_argument('input', nargs='?', help='Input .docx file or directory')
    parser.add_argument('output', nargs='?', help='Output .md file (optional)')
    parser.add_argument('-d', '--directory', action='store_true',
                       help='Convert all .docx files in specified directory')
    parser.add_argument('-r', '--recursive', action='store_true',
                       help='Process directories recursively')
    parser.add_argument('-i', '--images', action='store_true',
                       help='Extract and save images')
    parser.add_argument('-o', '--output-dir', type=str,
                       help='Output directory (default: same as input)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Show detailed processing information')
    parser.add_argument('--requirements', action='store_true',
                       help='Show required dependencies')
    
    args = parser.parse_args()
    
    # Show requirements if requested
    if args.requirements:
        show_requirements()
        return
    
    # Check if input is provided
    if not args.input:
        parser.print_help()
        print("\n" + "="*50)
        show_requirements()
        return
    
    # Initialize converter
    converter = DocxToMarkdownConverter(
        extract_images=args.images,
        verbose=args.verbose
    )
    
    try:
        if args.directory:
            # Convert directory
            converted_files = converter.convert_directory(
                args.input,
                recursive=args.recursive,
                output_dir=args.output_dir
            )
            
            print(f"\n✨ Conversion complete!")
            print(f"📄 Converted {len(converted_files)} files")
            if converter.images_extracted > 0:
                print(f"🖼️  Extracted {converter.images_extracted} images")
        
        else:
            # Convert single file
            result = converter.convert_file(args.input, args.output)
            
            print(f"\n✨ Conversion complete!")
            print(f"📄 Output: {result}")
            if converter.images_extracted > 0:
                print(f"🖼️  Extracted {converter.images_extracted} images")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

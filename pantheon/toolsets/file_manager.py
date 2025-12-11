import os
from pathlib import Path
import tempfile
import shutil
import base64
import io
import itertools
from datetime import datetime

from PIL import Image


from ..toolset import ToolSet, tool
from ..utils.log import logger


def _replace_in_content(
    content: str,
    old_string: str,
    new_string: str,
    replace_all: bool = False,
    start_line: int | None = None,
    end_line: int | None = None,
) -> tuple[str | None, int, str | None]:
    """Perform string replacement in content with optional line range.
    
    Args:
        content: The full file content.
        old_string: The exact string to find.
        new_string: The replacement string.
        replace_all: If True, replace all occurrences.
        start_line: Optional start line (1-indexed, inclusive).
        end_line: Optional end line (1-indexed, inclusive).
    
    Returns:
        Tuple of (new_content, replacement_count, error_message).
        On success: (new_content, count, None)
        On failure: (None, 0, error_message)
    """
    def do_replace(text: str, old: str, new: str, count: int) -> tuple[str, int]:
        """Perform replacement, returns (new_text, actual_count)."""
        if count == 0:  # replace all
            n = text.count(old)
            return text.replace(old, new), n
        else:
            return text.replace(old, new, count), min(count, text.count(old))
    
    # Handle line range restriction
    if start_line is not None or end_line is not None:
        lines = content.splitlines(keepends=True)
        start_idx = (start_line - 1) if start_line else 0
        end_idx = end_line if end_line else len(lines)
        
        # Validate bounds
        if start_idx < 0 or start_idx >= len(lines):
            return None, 0, f"start_line {start_line} is out of range (file has {len(lines)} lines)"
        if end_idx > len(lines):
            return None, 0, f"end_line {end_line} is out of range (file has {len(lines)} lines)"
        if start_idx >= end_idx:
            return None, 0, "start_line must be less than end_line"
        
        before = "".join(lines[:start_idx])
        section = "".join(lines[start_idx:end_idx])
        after = "".join(lines[end_idx:])
        
        match_count = section.count(old_string)
        
        if match_count == 0:
            return None, 0, f"old_string not found in lines {start_line}-{end_line}"
        
        if match_count > 1 and not replace_all:
            return None, 0, f"old_string found {match_count} times in lines {start_line}-{end_line}. Set replace_all=True or narrow the line range."
        
        new_section, replaced = do_replace(
            section, old_string, new_string, 0 if replace_all else 1
        )
        return before + new_section + after, replaced, None
    else:
        # Full content replacement
        match_count = content.count(old_string)
        
        if match_count == 0:
            return None, 0, "old_string not found in file"
        
        if match_count > 1 and not replace_all:
            return None, 0, f"old_string found {match_count} times. Set replace_all=True or use start_line/end_line to target specific occurrence."
        
        new_content, replaced = do_replace(
            content, old_string, new_string, 0 if replace_all else 1
        )
        return new_content, replaced, None


class FileManagerToolSetBase(ToolSet):
    """Base class for file manager toolsets.
    Supplies fundamental workspace operations such as:
        - `get_cwd` / `list_files`: inspect the current root and list directory contents.
        - `create_directory`: create one or multiple directories (recursively when needed).
        - `delete_path`: remove files or directories, optionally with recursive deletion.
        - `move_file`: relocate files within the managed workspace.

    Args:
        name: The name of the toolset.
        path: The root directory to manage (defaults to cwd).
        black_list: Names to hide from listing APIs.
        **kwargs: Additional keyword arguments.
    """

    def __init__(
        self,
        name: str,
        path: str | Path | None = None,
        black_list: list[str] | None = None,
        **kwargs,
    ):
        super().__init__(name, **kwargs)
        if path is None:
            path = Path.cwd()
        self.path = Path(path)
        self.black_list = black_list or []

    @tool
    async def get_cwd(self) -> dict:
        """Get current working directory."""
        return {"success": True, "cwd": str(self.path)}

    @tool
    async def list_files(
        self,
        sub_dir: str | None = None,
        recursive: bool = False,
        max_depth: int = 5,
    ) -> dict:
        """List files and directories in the workspace.

        Use this tool to browse directory contents. For searching, use shell:
        - Find files by name: `fd` or `find`
        - Find text in files: `rg` or `grep`

        Args:
            sub_dir: Subdirectory to list (relative to workspace root).
                     If not provided, lists the workspace root.
            recursive: If True, list all files recursively as a tree structure.
            max_depth: Maximum depth to recurse (only used when recursive=True).
                       0 means only the target directory, 1 includes immediate children, etc.
                       Default is 5.

        Returns:
            dict: {success: bool, files: list} with name, type, size, last_modified.
        """
        # Determine target directory - support absolute paths
        if sub_dir is not None and os.path.isabs(sub_dir):
            target_path = Path(sub_dir)
        elif sub_dir:
            target_path = self.path / sub_dir
        else:
            target_path = self.path

        if not target_path.exists():
            return {"success": False, "error": "Directory does not exist"}

        if not recursive:
            files = list(target_path.glob("*"))
            return {
                "success": True,
                "files": [
                    {
                        "name": file.name,
                        "size": file.stat().st_size if file.is_file() else 0,
                        "type": "file" if file.is_file() else "directory",
                        "last_modified": datetime.fromtimestamp(
                            file.stat().st_mtime
                        ).strftime("%Y-%m-%d %H:%M:%S"),
                    }
                    for file in files
                    if file.name not in self.black_list
                ],
            }
        else:
            def _list_tree(path: Path, current_depth: int = 0) -> dict:
                """Helper function to recursively build the tree structure."""
                result = {
                    "name": path.name,
                    "type": "directory" if path.is_dir() else "file",
                    "size": path.stat().st_size if path.is_file() else 0,
                }
                if path.is_dir():
                    # Check depth limit before recursing
                    if max_depth is not None and current_depth >= max_depth:
                        result["children"] = []  # Empty children at max depth
                    else:
                        result["children"] = []
                        for item in sorted(path.iterdir()):
                            result["children"].append(_list_tree(item, current_depth + 1))
                return result

            if not target_path.exists():
                return {"success": False, "error": "Target directory does not exist"}

            return {"success": True, "tree": _list_tree(target_path, 0)}


    @tool
    async def create_directory(self, sub_dir: str | list[str]) -> dict:
        """Create one or more directories.

        Args:
            sub_dir: Directory path or list of directory paths to create.

        Returns:
            dict: Success status. For batch operations, includes results for each path.
        """
        if isinstance(sub_dir, str):
            new_dir = self.path / sub_dir
            new_dir.mkdir(parents=True, exist_ok=True)
            return {"success": True}

        # Batch operation
        results = []
        for path in sub_dir:
            try:
                new_dir = self.path / path
                new_dir.mkdir(parents=True, exist_ok=True)
                results.append({"path": path, "success": True})
            except Exception as exc:
                results.append({"path": path, "success": False, "error": str(exc)})

        all_success = all(r["success"] for r in results)
        return {"success": all_success, "results": results}

    @tool
    async def delete_path(
        self,
        path: str | list[str],
        recursive: bool = False,
    ) -> dict:
        """Delete files or directories with optional recursion.

        Args:
            path: Single path or list of paths relative to the workspace root.
            recursive: When True, directories are deleted recursively using rmtree.
        """
        def _delete_single_path(relative_path: str) -> dict:
            target_path = self.path / relative_path
            if not target_path.exists():
                return {
                    "path": relative_path,
                    "success": False,
                    "error": "Path does not exist",
                }
            try:
                if target_path.is_dir():
                    if recursive:
                        shutil.rmtree(target_path)
                    else:
                        target_path.rmdir()
                else:
                    target_path.unlink()
                return {"path": relative_path, "success": True}
            except Exception as exc:
                return {
                    "path": relative_path,
                    "success": False,
                    "error": str(exc),
                }

        if isinstance(path, str):
            return _delete_single_path(path)

        results = [_delete_single_path(p) for p in path]
        all_success = all(r["success"] for r in results)
        return {"success": all_success, "results": results}

    @tool
    async def move_file(self, old_path: str, new_path: str):
        """Move or rename a file.

        Args:
            old_path: Current path of the file (relative to workspace root).
            new_path: New path for the file (relative to workspace root).

        Returns:
            dict: {success: bool} or {success: False, error: str}
        """
        old_path = self.path / old_path
        if not old_path.exists():
            return {"success": False, "error": "Old path does not exist"}
        new_path = self.path / new_path
        shutil.move(old_path, new_path)
        return {"success": True}


def path_to_image_url(path: str) -> str:
    img = Image.open(path)
    with io.BytesIO() as buffer:
        img.save(buffer, format="PNG")
        buffer.seek(0)
        return f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"


class FileManagerToolSet(FileManagerToolSetBase):
    """Extended file manager toolset.
    Builds on the base class with higher-level helpers:
        - `read_file` / `write_file` / `update_file`: text read/write/structured replace operations.
        - `observe_images` / `observe_pdf_screenshots`: LLM-assisted visual inspection.
        - `read_pdf`: PDF-to-text extraction for downstream consumption.
        - `fetch_image_base64`: encode images for frontend display pipelines.

    Args:
        name: The name of the toolset.
        path: The path to the directory to manage.
        black_list: The list of files to ignore.
        **kwargs: Additional keyword arguments.
    """

    @tool
    async def read_file(
        self,
        file_path: str,
        start_line: int | None = None,
        end_line: int | None = None,
    ) -> dict:
        """Read the contents of a text file.

        Usage:
        - Lines are 1-indexed (first line is line 1).
        - start_line and end_line are inclusive.
        - To read the entire file, do not pass start_line or end_line.
        - To read a specific range, pass both start_line and end_line.

        Args:
            file_path: Path to the file to read (relative to workspace root).
            start_line: Optional. First line to read (1-indexed, inclusive).
            end_line: Optional. Last line to read (1-indexed, inclusive).

        Returns:
            dict: {success: bool, content: str, total_lines: int, format: str}
        """
        # Support both absolute and relative paths
        if os.path.isabs(file_path):
            target_path = Path(file_path)
        else:
            target_path = self.path / file_path
        if not target_path.exists():
            return {"success": False, "error": "File does not exist"}
        if not target_path.is_file():
            return {"success": False, "error": "Path is not a file"}
        
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            total_lines = len(lines)
            
            # Handle line range
            if start_line is not None or end_line is not None:
                # Convert to 0-indexed
                start_idx = (start_line - 1) if start_line else 0
                end_idx = end_line if end_line else total_lines
                
                # Validate bounds
                if start_idx < 0:
                    return {"success": False, "error": "start_line must be >= 1"}
                if start_idx >= total_lines:
                    return {"success": False, "error": f"start_line {start_line} is out of range (file has {total_lines} lines)"}
                if end_idx > total_lines:
                    end_idx = total_lines  # Clamp to file end
                if start_idx >= end_idx:
                    return {"success": False, "error": "start_line must be less than or equal to end_line"}
                
                content = "".join(lines[start_idx:end_idx])
            else:
                content = "".join(lines)
            
            return {
                "success": True,
                "content": content,
                "total_lines": total_lines,
                "format": target_path.suffix.lower(),
            }
        except UnicodeDecodeError:
            return {"success": False, "error": "File is not a valid text file (binary or encoding issue)"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @tool
    async def write_file(
        self,
        file_path: str,
        content: str = "",
        overwrite: bool = True,
    ) -> dict:
        """Use this tool to CREATE NEW files.

        This tool writes content to a file, automatically creating parent
        directories if they do not exist.

        IMPORTANT: For EDITING existing files, use `update_file` instead.
        Using write_file to rewrite entire files when only small changes
        are needed is wasteful and error-prone.

        Use this tool when:
        - Creating a brand new file
        - Completely rewriting a file from scratch (rare)

        DO NOT use this tool when:
        - Making partial modifications to an existing file
        - Changing a few lines in a large file
        - For these cases, use `update_file` instead

        Args:
            file_path: The path to the file to write.
            content: The content to write to the file.
            overwrite: When False, abort if the target file already exists.
                       Default is True, but consider using update_file for edits.

        Returns:
            dict: Success status or error message.
        """

        target_path = self.path / file_path
        if not overwrite and target_path.exists():
            return {
                "success": False,
                "error": "File already exists",
                "reason": "overwrite_disabled",
            }

        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(content)
            return {"success": True, "overwritten": overwrite}
        except Exception as exc:
            logger.error(f"write_file failed for {file_path}: {exc}")
            return {"success": False, "error": str(exc)}

    @tool
    async def update_file(
        self,
        file_path: str,
        old_string: str,
        new_string: str,
        replace_all: bool = False,
        start_line: int | None = None,
        end_line: int | None = None,
    ) -> dict:
        """Use this tool to edit an existing file. Follow these rules:

        1. Use this tool ONLY when making a SINGLE edit to a file. If you need to make
           MULTIPLE different edits to the same file, use `batch_update_file` instead.
        2. The old_string must EXACTLY MATCH the text in the file, including whitespace
           and indentation. Copy the exact text you want to replace.
        3. When old_string appears multiple times in the file, use start_line and end_line
           to limit the search scope, OR set replace_all=True to replace all occurrences.
        4. DO NOT use `write_file` to rewrite entire files when you only need small changes.
           This tool is more efficient and safer.

        Args:
            file_path: Path to the file to update (relative to workspace root).
            old_string: The exact string to find and replace.
            new_string: The string to replace old_string with.
            replace_all: If True, replace all occurrences. Default False (safer).
            start_line: Optional. Limit search from this line (1-indexed, inclusive).
            end_line: Optional. Limit search to this line (1-indexed, inclusive).

        Returns:
            dict: {success: bool, replacements: int} or {success: False, error: str}
        """
        target_path = self.path / file_path
        if not target_path.exists():
            return {"success": False, "error": "File does not exist"}
        if not target_path.is_file():
            return {"success": False, "error": "Path is not a file"}

        try:
            with open(target_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            new_content, replacements, error = _replace_in_content(
                content, old_string, new_string,
                replace_all=replace_all,
                start_line=start_line,
                end_line=end_line,
            )
            
            if error:
                return {"success": False, "error": error}

            with open(target_path, "w", encoding="utf-8") as f:
                f.write(new_content)

            return {"success": True, "replacements": replacements}

        except UnicodeDecodeError:
            return {"success": False, "error": "File is not a valid text file"}
        except Exception as e:
            logger.error(f"update_file failed for {file_path}: {e}")
            return {"success": False, "error": str(e)}

    @tool
    async def batch_update_file(
        self,
        file_path: str,
        replacements: list[dict],
    ) -> dict:
        """Use this tool to make multiple edits to an existing file. Follow these rules:

        1. Use this tool ONLY when making MULTIPLE, NON-CONTIGUOUS edits to the same file.
           If you are making a single edit, use `update_file` instead.
        2. Do NOT make multiple parallel calls to `update_file` for the same file.
           Use this tool to batch all edits into one call.
        3. Each replacement in the list is applied sequentially. Later replacements
           operate on the result of earlier ones.
        4. For each replacement, old_string must EXACTLY MATCH the text in the file.

        Args:
            file_path: Path to the file to update (relative to workspace root).
            replacements: List of replacement dicts, each containing:
                - old_string (required): Exact string to find
                - new_string (required): Replacement string
                - start_line (optional): Limit search from this line (1-indexed)
                - end_line (optional): Limit search to this line (1-indexed)
                - replace_all (optional): Replace all occurrences (default: False)

        Returns:
            dict: {success: bool, results: list, total_replacements: int}

        Example:
            replacements = [
                {"old_string": "import foo", "new_string": "import bar"},
                {"old_string": "foo()", "new_string": "bar()", "replace_all": True},
            ]
        """
        target_path = self.path / file_path
        if not target_path.exists():
            return {"success": False, "error": "File does not exist"}
        if not target_path.is_file():
            return {"success": False, "error": "Path is not a file"}
        
        if not replacements:
            return {"success": False, "error": "replacements list is empty"}

        try:
            with open(target_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            results = []
            current_content = content
            
            for i, repl in enumerate(replacements):
                old_string = repl.get("old_string")
                new_string = repl.get("new_string")
                
                if not old_string or new_string is None:
                    results.append({
                        "index": i,
                        "success": False,
                        "error": "old_string and new_string are required",
                    })
                    continue
                
                try:
                    new_content, replaced_count, error = _replace_in_content(
                        current_content,
                        old_string,
                        new_string,
                        replace_all=repl.get("replace_all", False),
                        start_line=repl.get("start_line"),
                        end_line=repl.get("end_line"),
                    )
                    
                    if error:
                        results.append({"index": i, "success": False, "error": error})
                    else:
                        current_content = new_content
                        results.append({
                            "index": i,
                            "success": True,
                            "replacements": replaced_count,
                        })
                except Exception as e:
                    results.append({
                        "index": i,
                        "success": False,
                        "error": str(e),
                    })
            
            # Check if any replacement succeeded
            any_success = any(r["success"] for r in results)
            
            if any_success:
                with open(target_path, "w", encoding="utf-8") as f:
                    f.write(current_content)
            
            all_success = all(r["success"] for r in results)
            return {
                "success": all_success,
                "partial_success": any_success and not all_success,
                "results": results,
                "total_replacements": sum(r.get("replacements", 0) for r in results),
            }

        except UnicodeDecodeError:
            return {"success": False, "error": "File is not a valid text file"}
        except Exception as e:
            logger.error(f"batch_update_file failed for {file_path}: {e}")
            return {"success": False, "error": str(e)}

    @tool
    async def observe_images(self, question: str, image_paths: list[str]) -> dict:
        """Observe images and answer a question about them.

        Args:
            question: The question to answer.
            image_paths: The paths to the images to view."""
        context = self.get_context()
        if context is None:
            return {"success": False, "error": "ExecutionContext not available"}

        # Build messages with question
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": question,
                    },
                ],
            }
        ]

        # Add images to the message
        for img_path in image_paths:
            ipath = self.path / img_path

            # Validate image path
            if not ipath.exists():
                return {
                    "success": False,
                    "error": f"Image file does not exist: {img_path}",
                }
            if not ipath.is_file():
                return {"success": False, "error": f"Path is not a file: {img_path}"}

            # Convert image to base64 URI and add to message
            base64_uri = path_to_image_url(str(ipath))
            messages[0]["content"].append(
                {
                    "type": "image_url",
                    "image_url": {"url": base64_uri},
                }
            )

        # Call LLM to analyze images
        try:
            response = await context.call_agent(messages=messages, use_memory=True)
            return {"success": True, "content": response}
        except Exception as e:
            logger.error(
                f"Error calling agent for image observation: {e}", exc_info=True
            )
            return {"success": False, "error": str(e)}

    @tool
    async def observe_pdf_screenshots(
        self,
        question: str,
        pdf_path: str,
        page_numbers: list[int] | None = None,
        dpi: int = 300,
    ) -> dict:
        """Observe the screenshots of the PDF file and answer a question about them.

        Args:
            question: The question to answer.
            pdf_path: The path to the PDF file to observe.
            page_numbers: The numbers of the pages to observe. If not provided, all pages will be observed.
            dpi: The DPI of the screenshots. If not provided, the default value is 300.
        """
        file_path = self.path / pdf_path
        if not file_path.exists():
            return {"success": False, "error": "PDF file does not exist"}
        if not file_path.is_file():
            return {"success": False, "error": "Path is not a file"}
        if file_path.suffix.lower() != ".pdf":
            return {"success": False, "error": "File is not a PDF (wrong extension)"}
        try:
            import pymupdf
            with tempfile.TemporaryDirectory() as tmp_dir:
                image_paths = []
                with pymupdf.open(str(file_path)) as doc:
                    page_count = len(doc)
                    if page_numbers is not None:
                        page_numbers = [p for p in page_numbers if p <= page_count]
                    else:
                        page_numbers = list(range(page_count))
                    for page_number in page_numbers:
                        page = doc.load_page(page_number)
                        image = page.get_pixmap(dpi=dpi)
                        path = os.path.join(tmp_dir, f"page_{page_number}.png")
                        image.save(path)
                        image_paths.append(path)
                    resp = await self.observe_images(question, image_paths)
                    return resp
        except ImportError:
            return {
                "success": False,
                "error": "pymupdf library not installed. Install with: pip install pymupdf",
            }
        except Exception as e:
            return {"success": False, "error": f"Unexpected error: {str(e)}"}

    @tool
    async def read_pdf(self, pdf_path: str) -> dict:
        """Read a PDF file and return the text inside it.

        Args:
            pdf_path: The path to the PDF file to read.

        Returns:
            dict: Success status, content, and metadata about the PDF.
        """
        file_path = self.path / pdf_path

        # Check if file exists
        if not file_path.exists():
            return {"success": False, "error": "PDF file does not exist"}

        # Check if it's actually a file
        if not file_path.is_file():
            return {"success": False, "error": "Path is not a file"}

        # Check if it has a PDF extension
        if file_path.suffix.lower() != ".pdf":
            return {"success": False, "error": "File is not a PDF (wrong extension)"}

        try:
            # Try to import pymupdf
            import pymupdf
        except ImportError:
            return {
                "success": False,
                "error": "pymupdf library not installed. Install with: pip install pymupdf",
            }

        try:
            # Open and read the PDF
            texts = []
            page_count = 0

            with pymupdf.open(str(file_path)) as doc:
                page_count = len(doc)

                # Check if PDF is password protected
                if doc.needs_pass:
                    return {
                        "success": False,
                        "error": "PDF is password protected and cannot be read",
                    }

                # Extract text from each page
                for page_num, page in enumerate(doc):
                    try:
                        page_text = page.get_text()
                        if page_text.strip():  # Only add non-empty pages
                            texts.append(f"--- Page {page_num + 1} ---\n{page_text}")
                    except Exception as e:
                        texts.append(
                            f"--- Page {page_num + 1} (Error reading) ---\nError: {str(e)}"
                        )

            # Combine all text
            full_text = "\n\n".join(texts)

            return {
                "success": True,
                "content": full_text,
                "format": ".pdf",
                "metadata": {
                    "total_pages": page_count,
                    "file_size": file_path.stat().st_size,
                    "pages_with_text": len(
                        [
                            t
                            for t in texts
                            if not t.startswith("--- Page") or "Error" not in t
                        ]
                    ),
                },
            }

        except pymupdf.FileDataError:
            return {"success": False, "error": "Invalid or corrupted PDF file"}
        except pymupdf.FitzError as e:
            return {"success": False, "error": f"PDF processing error: {str(e)}"}
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error reading PDF: {str(e)}",
            }

    @tool(exclude=True)
    async def fetch_image_base64(self, image_path: str) -> dict:
        """Fetch an image and return the base64 encoded image. for frontend display

        Args:
            image_path: Path to the image file (relative to workspace)

        Returns:
            Dict with success status and either data_uri or error message

        Raises:
            Returns error dict for invalid paths, unsupported formats, or file issues
        """
        # Security: Maximum image size (10MB)
        MAX_IMAGE_SIZE = 10 * 1024 * 1024

        try:
            i_path = self.path / image_path

            # Security: Check if path is within allowed workspace
            try:
                resolved_path = i_path.resolve()
                allowed_path = self.path.resolve()
                if not str(resolved_path).startswith(str(allowed_path)):
                    return {"success": False, "error": "Path outside allowed workspace"}
            except Exception:
                return {"success": False, "error": "Invalid path"}

            # Security: Reject symbolic links
            if resolved_path.is_symlink():
                return {"success": False, "error": "Symbolic links are not allowed"}

            # Check file existence
            if not resolved_path.exists():
                return {"success": False, "error": "Image does not exist"}

            # Check if it's a file (not directory)
            if not resolved_path.is_file():
                return {"success": False, "error": "Path is not a file"}

            # Validate format
            format = resolved_path.suffix.lower()
            if format not in [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg"]:
                return {
                    "success": False,
                    "error": "Image format must be jpg, jpeg, png, gif, webp, bmp, or svg",
                }

            # Check file size
            try:
                file_size = resolved_path.stat().st_size
                if file_size == 0:
                    return {"success": False, "error": "Image file is empty"}
                if file_size > MAX_IMAGE_SIZE:
                    return {
                        "success": False,
                        "error": f"Image size ({file_size / 1024 / 1024:.1f}MB) exceeds maximum ({MAX_IMAGE_SIZE / 1024 / 1024:.0f}MB)",
                    }
            except OSError as e:
                return {"success": False, "error": f"Cannot access file: {str(e)}"}

            # Encode image to base64
            try:
                with open(resolved_path, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode("utf-8")
            except PermissionError:
                return {"success": False, "error": "Permission denied reading image"}
            except IOError as e:
                return {"success": False, "error": f"IO error reading image: {str(e)}"}

            # Map format to MIME type
            mime_format = format.lstrip(".")
            if mime_format == "jpg":
                mime_format = "jpeg"

            data_uri = f"data:image/{mime_format};base64,{b64}"
            return {
                "success": True,
                "image_path": image_path,
                "data_uri": data_uri,
            }

        except Exception as e:
            logger.error(f"Error fetching image base64 for {image_path}: {str(e)}")
            return {"success": False, "error": f"Unexpected error: {str(e)}"}


__all__ = ["FileManagerToolSet"]

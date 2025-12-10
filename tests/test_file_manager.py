import pytest
from tempfile import TemporaryDirectory
from pantheon.toolsets.file_manager import FileManagerToolSet

@pytest.fixture
def temp_toolset():
    """Create a FileManagerToolSet with a temporary directory."""
    with TemporaryDirectory() as temp_dir:
        yield FileManagerToolSet("file_manager", temp_dir)

async def test_filemanager_comprehensive(temp_toolset):
    """
    Test comprehensive file manager operations in a single flow.
    Includes edge case parameters and additional APIs like batch_update_file.
    
    Covers:
    - create_directory
    - write_file (and overwrite behavior)
    - list_files (root and subdirectory)
    - read_file (full and partial/line-range)
    - update_file (single, multiple/replace_all, line-limited)
    - batch_update_file (mixed scenarios)
    - move_file
    - delete_path
    """
    
    # 1. Start with directory structure
    assert (await temp_toolset.create_directory("src"))["success"]
    assert (await temp_toolset.create_directory("src/utils"))["success"]
    
    # 2. Write file with multiple lines
    content = "import os\nimport sys\n\ndef func():\n    pass\n    return 0\n"
    res = await temp_toolset.write_file("src/main.py", content)
    assert res["success"]
    
    # Test overwrite protection (default is overwrite=False but tool interface usually defaults to user intent, 
    # checking impl: write_file defaults to overwrite=False in some versions, let's verify)
    # Actually most LLM tool implementations of write_file default to overwriting or failing. 
    # Current pantheon implementation signature is: write_file(file_path, content) -> likely overwrites or fails.
    # Let's test overwrite explicit just in case.
    res = await temp_toolset.write_file("src/main.py", "OVERWRITTEN", overwrite=True)
    assert res["success"]
    assert (await temp_toolset.read_file("src/main.py"))["content"] == "OVERWRITTEN"
    
    # Restore content
    await temp_toolset.write_file("src/main.py", content, overwrite=True)
    
    # 3. List files in subdirectory
    res = await temp_toolset.list_files("src")
    assert res["success"]
    names = [f["name"] for f in res["files"]]
    assert "main.py" in names
    assert "utils" in names

    # 4. Read file with line range
    # Content:
    # 1: import os
    # 2: import sys
    # 3: 
    # 4: def func():
    # 5:     pass
    # 6:     return 0
    
    # Read lines 4-6
    res = await temp_toolset.read_file("src/main.py", start_line=4, end_line=6)
    assert res["success"]
    part = res["content"]
    assert "def func():" in part
    assert "return 0" in part
    assert "import os" not in part
    
    # 5. Update file with advanced params
    
    # A. Scope limit (only replace 'pass' inside function if we knew lines, 
    # but here just testing line limit works)
    res = await temp_toolset.update_file(
        "src/main.py",
        old_string="pass",
        new_string="print('hello')",
        start_line=5,
        end_line=5
    )
    assert res["success"]
    assert "print('hello')" in (await temp_toolset.read_file("src/main.py"))["content"]
    
    # Prepare file for replace_all test
    # 1: import os
    # 2: import sys
    # ...
    # Let's add multiple same lines
    multi_content = "foo\nbar\nfoo\nbaz\nfoo"
    await temp_toolset.write_file("src/multi.txt", multi_content)
    
    # B. Replace All
    res = await temp_toolset.update_file(
        "src/multi.txt",
        old_string="foo",
        new_string="replaced",
        replace_all=True
    )
    assert res["success"]
    assert res["replacements"] == 3
    new_multi = (await temp_toolset.read_file("src/multi.txt"))["content"]
    assert new_multi.count("replaced") == 3
    assert "foo" not in new_multi
    
    # 6. Batch Update File
    # Create a complex file
    code = """
    def process(x):
        res = x + 1
        print(res)
        return res
    """
    await temp_toolset.write_file("src/calc.py", code)
    
    res = await temp_toolset.batch_update_file(
        "src/calc.py",
        replacements=[
            # 1. Rename variable
            {"old_string": "x + 1", "new_string": "x * 2"},
            # 2. Change print to logging
            {"old_string": "print(res)", "new_string": "logger.info(res)"}
        ]
    )
    assert res["success"]
    assert res["total_replacements"] == 2
    
    final_code = (await temp_toolset.read_file("src/calc.py"))["content"]
    assert "x * 2" in final_code
    assert "logger.info(res)" in final_code
    
    # 7. Move and Delete
    # Move directory
    res = await temp_toolset.move_file("src/utils", "src/tools")
    assert res["success"]
    assert (temp_toolset.path / "src/tools").exists()
    assert not (temp_toolset.path / "src/utils").exists()
    
    # Delete file
    res = await temp_toolset.delete_path("src/calc.py")
    assert res["success"]
    assert not (temp_toolset.path / "src/calc.py").exists()

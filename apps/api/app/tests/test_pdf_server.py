import json
import os

from app.mcp_servers.pdf_server import (
    _get_output_dir,
    create_pdf,
    inspect_pdf,
    merge_pdfs,
)


def test_create_pdf_basic():
    """Verify that create_pdf produces a valid PDF file with standard headers and returns valid JSON."""
    result_raw = create_pdf(
        title="Test Document",
        content="This is a simple paragraph.",
        author="Agent",
    )
    res = json.loads(result_raw)
    assert res["status"] == "success"
    filename = res["filename"]
    file_path = os.path.join(_get_output_dir(), filename)
    assert os.path.exists(file_path)
    assert res["page_count"] == 1
    assert res["file_size_bytes"] > 0
    assert "file_path" not in res

    with open(file_path, "rb") as f:
        header = f.read(5)
        assert header == b"%PDF-"

    # Clean up test artifact
    if os.path.exists(file_path):
        os.remove(file_path)


def test_create_pdf_with_markdown_and_custom_filename():
    """Verify that create_pdf parses markdown formatting and respects custom filenames and author metadata."""
    content = (
        "# Main Heading\n\n"
        "## Sub Heading\n\n"
        "### Section Header\n\n"
        "- First bullet point\n"
        "- Second bullet point with **bold**\n\n"
        "Plain closing paragraph."
    )
    result_raw = create_pdf(
        title="Markdown Doc",
        content=content,
        filename="custom_markdown_report.pdf",
        author="Unit Tester",
    )
    res = json.loads(result_raw)
    assert res["status"] == "success"
    assert "custom_markdown_report" in res["filename"]
    assert res["filename"].endswith(".pdf")
    filename = res["filename"]
    file_path = os.path.join(_get_output_dir(), filename)

    # Inspect the generated file using filename (not absolute file_path)
    insp_raw = inspect_pdf(filename)
    insp = json.loads(insp_raw)
    assert insp["status"] == "success"
    assert insp["page_count"] == 1
    assert "Main Heading" in insp["preview"]
    assert insp["metadata"].get("Title") == "Markdown Doc"
    assert insp["metadata"].get("Author") == "Unit Tester"

    if os.path.exists(file_path):
        os.remove(file_path)


def test_create_pdf_with_html_content():
    """Verify that create_pdf renders HTML tags if detected in content."""
    html_content = (
        "<h1>HTML Title</h1>"
        "<p>This is a paragraph with <b>bold</b> and <i>italic</i> styling.</p>"
        "<ul><li>Item A</li><li>Item B</li></ul>"
    )
    result_raw = create_pdf(
        title="HTML Report",
        content=html_content,
        filename="html_report.pdf",
    )
    res = json.loads(result_raw)
    assert res["status"] == "success"
    filename = res["filename"]
    file_path = os.path.join(_get_output_dir(), filename)
    assert os.path.exists(file_path)

    insp = json.loads(inspect_pdf(filename))
    assert insp["status"] == "success"
    assert "HTML Title" in insp["preview"]

    if os.path.exists(file_path):
        os.remove(file_path)


def test_merge_pdfs_success():
    """Verify that merge_pdfs combines multiple PDF files into one with the correct page count."""
    doc1 = json.loads(create_pdf("Doc 1", "Content 1", filename="doc1.pdf"))
    doc2 = json.loads(create_pdf("Doc 2", "Content 2", filename="doc2.pdf"))

    merged_raw = merge_pdfs(
        [doc1["filename"], doc2["filename"]],
        output_filename="merged_output.pdf",
    )
    merged = json.loads(merged_raw)
    assert merged["status"] == "success"
    assert merged["total_pages"] == 2
    assert merged["source_files_count"] == 2
    assert "merged_file_path" not in merged
    out_dir = _get_output_dir()
    merged_path = os.path.join(out_dir, merged["filename"])
    assert os.path.exists(merged_path)

    # Clean up
    for fname in [doc1["filename"], doc2["filename"], merged["filename"]]:
        p = os.path.join(out_dir, fname)
        if os.path.exists(p):
            os.remove(p)


def test_merge_pdfs_errors():
    """Verify that merge_pdfs handles empty lists and nonexistent files safely."""
    res_empty = json.loads(merge_pdfs([]))
    assert res_empty["status"] == "error"
    assert "cannot be empty" in res_empty["error"]

    res_missing = json.loads(merge_pdfs(["nonexistent_sample_12345.pdf"]))
    assert res_missing["status"] == "error"
    assert res_missing["error"] == "PDF not found."


def test_inspect_pdf_nonexistent():
    """Verify that inspect_pdf returns an error on missing files."""
    res = json.loads(inspect_pdf("nonexistent_sample_99999.pdf"))
    assert res["status"] == "error"
    assert res["error"] == "PDF not found."


def test_inspect_pdf_traversal_and_absolute_paths_rejected():
    """Verify inspect_pdf rejects absolute paths and traversal without revealing existence."""
    for bad_path in ["/etc/passwd", "../../x.pdf"]:
        res = json.loads(inspect_pdf(bad_path))
        assert res["status"] == "error"
        assert res["error"] == "PDF not found."
        assert bad_path not in res["error"]


def test_merge_pdfs_outside_path_rejected():
    """Verify merge_pdfs rejects paths outside the output directory."""
    res = json.loads(merge_pdfs(["/tmp/outside.pdf"]))
    assert res["status"] == "error"
    assert res["error"] == "PDF not found."
    assert "/tmp/outside.pdf" not in res["error"]


def test_create_pdf_different_files_same_filename():
    """Verify two create_pdf calls with the same filename produce two distinct files."""
    res1 = json.loads(
        create_pdf(title="Doc 1", content="Content 1", filename="report.pdf")
    )
    res2 = json.loads(
        create_pdf(title="Doc 2", content="Content 2", filename="report.pdf")
    )
    assert res1["status"] == "success"
    assert res2["status"] == "success"
    assert res1["filename"] != res2["filename"]
    assert "report" in res1["filename"]
    assert "report" in res2["filename"]
    out_dir = _get_output_dir()
    for f in [res1["filename"], res2["filename"]]:
        p = os.path.join(out_dir, f)
        if os.path.exists(p):
            os.remove(p)

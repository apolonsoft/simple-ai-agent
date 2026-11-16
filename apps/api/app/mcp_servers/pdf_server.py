import json
import logging
import os
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from dotenv import load_dotenv
from fpdf import FPDF
from mcp.server.mcpserver import MCPServer
from pypdf import PdfReader, PdfWriter

# Load environment variables (.env at project root or apps/api/.env)
load_dotenv()

logger = logging.getLogger(__name__)

# Initialize FastMCP Server
mcp = MCPServer("custom-pdf-tools")


def _get_output_dir() -> str:
    """Return the resolved absolute directory for storing generated PDFs."""
    base_dir = os.getenv("MCP_PDF_DIR", "outputs/pdfs")
    if not os.path.isabs(base_dir):
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        api_root = os.path.abspath(os.path.join(current_file_dir, "..", ".."))
        base_dir = os.path.join(api_root, base_dir)
    os.makedirs(base_dir, exist_ok=True)
    return base_dir


def _sanitize_filename(name: str | None, prefix: str = "doc") -> str:
    """Sanitize or generate a safe .pdf filename without directory traversal."""
    if name:
        base = os.path.basename(name).strip()
        base = re.sub(r"[^\w\-\.]", "_", base)
        if not base.lower().endswith(".pdf"):
            base += ".pdf"
        return base
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    rand_suffix = uuid.uuid4().hex[:6]
    return f"{prefix}_{timestamp}_{rand_suffix}.pdf"


class DocumentPDF(FPDF):
    """Custom FPDF document class with consistent headers and footers."""

    def __init__(self, title: str = "", author: str = ""):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.doc_title = title
        self.doc_author = author
        if author:
            self.set_author(author)
        if title:
            self.set_title(title)

    def header(self):
        if self.doc_title and self.page_no() > 1:
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(128, 128, 128)
            self.cell(0, 8, self.doc_title, align="R", new_x="LMARGIN", new_y="NEXT")
            self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")


@mcp.tool()
def create_pdf(
    title: str,
    content: str,
    filename: str | None = None,
    author: str | None = None,
) -> str:
    """
    Create a styled PDF document from text or Markdown content.

    Args:
        title: Title of the document
        content: Body content (supports Markdown headers, lists, bold, italics, or basic HTML)
        filename: Optional custom filename (e.g. 'quarterly_report.pdf')
        author: Optional author name embedded in PDF metadata

    Returns:
        JSON string with creation status, file_path, page_count, and file_size_bytes
    """
    try:
        output_dir = _get_output_dir()
        safe_filename = _sanitize_filename(filename, prefix="document")
        target_path = os.path.join(output_dir, safe_filename)

        pdf = DocumentPDF(title=title, author=author or "")
        pdf.add_page()

        # Render Title Block
        if title:
            pdf.set_font("Helvetica", "B", 18)
            pdf.set_text_color(25, 30, 36)
            pdf.multi_cell(0, 10, text=title, align="L", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)
            # Divider line
            pdf.set_draw_color(210, 215, 220)
            pdf.set_line_width(0.4)
            pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
            pdf.ln(6)
            pdf.set_x(pdf.l_margin)

        # Check for HTML content
        is_html = any(
            tag in content
            for tag in ["<p>", "<h1>", "<h2>", "<h3>", "<table>", "<br>", "<ul>"]
        )
        if is_html:
            pdf.set_font("Helvetica", size=10)
            pdf.set_text_color(40, 44, 52)
            pdf.write_html(content)
        else:
            # Markdown / plain-text rendering
            lines = content.split("\n")
            for line in lines:
                pdf.set_x(pdf.l_margin)
                stripped = line.strip()
                if not stripped:
                    pdf.ln(3)
                    continue

                if stripped.startswith("### "):
                    pdf.ln(2)
                    pdf.set_font("Helvetica", "B", 12)
                    pdf.set_text_color(50, 55, 65)
                    pdf.multi_cell(
                        0,
                        7,
                        text=stripped[4:],
                        markdown=True,
                        new_x="LMARGIN",
                        new_y="NEXT",
                    )
                    pdf.set_font("Helvetica", size=10)
                    pdf.set_text_color(40, 44, 52)
                elif stripped.startswith("## "):
                    pdf.ln(3)
                    pdf.set_font("Helvetica", "B", 14)
                    pdf.set_text_color(35, 40, 50)
                    pdf.multi_cell(
                        0,
                        8,
                        text=stripped[3:],
                        markdown=True,
                        new_x="LMARGIN",
                        new_y="NEXT",
                    )
                    pdf.set_font("Helvetica", size=10)
                    pdf.set_text_color(40, 44, 52)
                elif stripped.startswith("# "):
                    pdf.ln(4)
                    pdf.set_font("Helvetica", "B", 16)
                    pdf.set_text_color(20, 25, 35)
                    pdf.multi_cell(
                        0,
                        9,
                        text=stripped[2:],
                        markdown=True,
                        new_x="LMARGIN",
                        new_y="NEXT",
                    )
                    pdf.set_font("Helvetica", size=10)
                    pdf.set_text_color(40, 44, 52)
                elif stripped.startswith("- ") or stripped.startswith("* "):
                    pdf.set_font("Helvetica", size=10)
                    pdf.set_text_color(40, 44, 52)
                    pdf.multi_cell(
                        0,
                        6,
                        text=f"  - {stripped[2:]}",
                        markdown=True,
                        new_x="LMARGIN",
                        new_y="NEXT",
                    )
                else:
                    pdf.set_font("Helvetica", size=10)
                    pdf.set_text_color(40, 44, 52)
                    pdf.multi_cell(
                        0,
                        6,
                        text=stripped,
                        markdown=True,
                        new_x="LMARGIN",
                        new_y="NEXT",
                    )

        pdf.output(target_path)
        page_count = pdf.page_no()
        file_size = os.path.getsize(target_path)

        result: dict[str, Any] = {
            "status": "success",
            "file_path": target_path,
            "filename": safe_filename,
            "download_url": f"/api/v1/chats/files/pdf/{safe_filename}",
            "page_count": page_count,
            "file_size_bytes": file_size,
        }
        return json.dumps(result)
    except Exception as exc:
        logger.exception("Failed to create PDF")
        return json.dumps({"status": "error", "error": f"Failed to create PDF: {exc}"})


@mcp.tool()
def merge_pdfs(
    file_paths: list[str],
    output_filename: str | None = None,
) -> str:
    """
    Merge multiple existing PDF files into a single unified document.

    Args:
        file_paths: List of absolute or relative paths to PDF files to merge
        output_filename: Optional name for the merged output file

    Returns:
        JSON string with status, merged_file_path, total_pages, and source_files_count
    """
    if not file_paths:
        return json.dumps(
            {"status": "error", "error": "file_paths list cannot be empty."}
        )

    try:
        writer = PdfWriter()
        valid_count = 0

        for path in file_paths:
            if not os.path.exists(path):
                return json.dumps(
                    {
                        "status": "error",
                        "error": f"Input PDF file does not exist: {path}",
                    }
                )
            writer.append(path)
            valid_count += 1

        output_dir = _get_output_dir()
        safe_filename = _sanitize_filename(output_filename, prefix="merged")
        target_path = os.path.join(output_dir, safe_filename)

        with open(target_path, "wb") as f_out:
            writer.write(f_out)
        writer.close()

        total_pages = len(PdfReader(target_path).pages)
        file_size = os.path.getsize(target_path)

        result: dict[str, Any] = {
            "status": "success",
            "merged_file_path": target_path,
            "filename": safe_filename,
            "download_url": f"/api/v1/chats/files/pdf/{safe_filename}",
            "total_pages": total_pages,
            "source_files_count": valid_count,
            "file_size_bytes": file_size,
        }
        return json.dumps(result)
    except Exception as exc:
        logger.exception("Failed to merge PDFs")
        return json.dumps({"status": "error", "error": f"Failed to merge PDFs: {exc}"})


@mcp.tool()
def inspect_pdf(file_path: str) -> str:
    """
    Inspect an existing PDF to inspect metadata, page count, and text preview.

    Args:
        file_path: Absolute or relative path to the PDF file

    Returns:
        JSON string with status, file_path, page_count, metadata, and preview
    """
    if not os.path.exists(file_path):
        return json.dumps(
            {
                "status": "error",
                "error": f"Target PDF file does not exist: {file_path}",
            }
        )

    try:
        reader = PdfReader(file_path)
        page_count = len(reader.pages)
        metadata = {}
        if reader.metadata:
            for k, v in reader.metadata.items():
                metadata[str(k).lstrip("/")] = str(v)

        preview = ""
        if page_count > 0:
            extracted = reader.pages[0].extract_text() or ""
            preview = extracted[:400].strip()

        result: dict[str, Any] = {
            "status": "success",
            "file_path": file_path,
            "page_count": page_count,
            "metadata": metadata,
            "preview": preview,
            "file_size_bytes": os.path.getsize(file_path),
        }
        return json.dumps(result)
    except Exception as exc:
        logger.exception("Failed to inspect PDF")
        return json.dumps({"status": "error", "error": f"Failed to inspect PDF: {exc}"})


if __name__ == "__main__":
    port = int(os.getenv("MCP_PDF_PORT", "8002"))
    host = os.getenv("MCP_PDF_HOST", "127.0.0.1")
    print(f"Starting PDF MCP Server on http://{host}:{port}/sse ...")
    mcp.run(transport="sse", host=host, port=port)

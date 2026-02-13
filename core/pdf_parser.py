"""PDF parsing module for PaperGuide.

Extracts text, sections, images, and captions from academic papers.
"""
import re
from pathlib import Path
from dataclasses import dataclass, field
import fitz  # PyMuPDF


# Common section patterns in academic papers
SECTION_PATTERNS = [
    r"^\s*(?:I{1,3}|IV|V|VI{0,3}|IX|X)?\s*\.?\s*(Abstract)\s*$",
    r"^\s*(?:\d+\.?)?\s*(Introduction)\s*$",
    r"^\s*(?:\d+\.?)?\s*(Related\s+Work)\s*$",
    r"^\s*(?:\d+\.?)?\s*(Background)\s*$",
    r"^\s*(?:\d+\.?)?\s*(Method(?:ology|s)?)\s*$",
    r"^\s*(?:\d+\.?)?\s*(Approach)\s*$",
    r"^\s*(?:\d+\.?)?\s*(Experiment(?:s|al)?(?:\s+Results?)?)\s*$",
    r"^\s*(?:\d+\.?)?\s*(Results?)\s*$",
    r"^\s*(?:\d+\.?)?\s*(Discussion)\s*$",
    r"^\s*(?:\d+\.?)?\s*(Conclusion(?:s)?)\s*$",
    r"^\s*(?:\d+\.?)?\s*(References?)\s*$",
    r"^\s*(?:\d+\.?)?\s*(Appendix)\s*$",
]

FIGURE_CAPTION_PATTERN = re.compile(
    r"(Figure|Fig\.?)\s*(\d+)[:\.]?\s*(.+?)(?=\n\n|$)",
    re.IGNORECASE | re.DOTALL
)


@dataclass
class Section:
    """A section of the paper."""
    title: str
    content: str
    page_start: int
    page_end: int


@dataclass
class FigureInfo:
    """Information about a figure."""
    number: str
    caption: str
    page: int
    image_path: str | None = None


@dataclass
class ParsedPaper:
    """Parsed paper data."""
    title: str
    full_text: str
    sections: list[Section] = field(default_factory=list)
    figures: list[FigureInfo] = field(default_factory=list)
    page_count: int = 0


def extract_text(pdf_path: str | Path) -> str:
    """Extract full text from PDF."""
    doc = fitz.open(pdf_path)
    text_parts = []
    for page in doc:
        text_parts.append(page.get_text())
    doc.close()
    return "\n".join(text_parts)


def extract_title(doc: fitz.Document) -> str:
    """Extract paper title (usually largest font on first page)."""
    if len(doc) == 0:
        return "Unknown Title"
    first_page = doc[0]
    blocks = first_page.get_text("dict")["blocks"]
    # Find text with largest font size in top portion of page
    candidates = []
    for block in blocks:
        if "lines" not in block:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                if span["bbox"][1] < 200:  # Top portion
                    candidates.append((span["size"], span["text"].strip()))
    if candidates:
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]
    return "Unknown Title"


def identify_sections(text: str) -> list[tuple[str, int]]:
    """Identify section headers and their positions."""
    sections = []
    lines = text.split("\n")
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        for pattern in SECTION_PATTERNS:
            match = re.match(pattern, line_stripped, re.IGNORECASE)
            if match:
                section_name = match.group(1)
                sections.append((section_name, i))
                break
    return sections


def extract_figure_captions(text: str) -> list[tuple[str, str]]:
    """Extract figure numbers and captions."""
    matches = FIGURE_CAPTION_PATTERN.findall(text)
    return [(m[1], m[2].strip()) for m in matches]


def extract_images(pdf_path: str | Path, output_dir: Path) -> list[str]:
    """Extract images from PDF and save to output directory."""
    output_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_path)
    saved_images = []

    for page_num, page in enumerate(doc):
        images = page.get_images(full=True)
        for img_idx, img in enumerate(images):
            xref = img[0]
            pix = fitz.Pixmap(doc, xref)
            if pix.n - pix.alpha > 3:  # CMYK
                pix = fitz.Pixmap(fitz.csRGB, pix)
            img_name = f"page{page_num+1}_img{img_idx+1}.png"
            img_path = output_dir / img_name
            pix.save(str(img_path))
            saved_images.append(str(img_path))
            pix = None
    doc.close()
    return saved_images


def parse_pdf(pdf_path: str | Path, images_dir: Path | None = None) -> ParsedPaper:
    """Parse a PDF file and extract all relevant information."""
    doc = fitz.open(pdf_path)
    title = extract_title(doc)

    # Extract text
    full_text = ""
    page_texts = []
    for page in doc:
        page_text = page.get_text()
        page_texts.append(page_text)
        full_text += page_text + "\n"

    # Identify sections
    section_markers = identify_sections(full_text)
    sections = []
    lines = full_text.split("\n")
    for i, (name, start_line) in enumerate(section_markers):
        end_line = section_markers[i+1][1] if i+1 < len(section_markers) else len(lines)
        content = "\n".join(lines[start_line:end_line])
        sections.append(Section(title=name, content=content, page_start=0, page_end=0))

    # Extract figures
    caption_matches = extract_figure_captions(full_text)
    figures = [FigureInfo(number=num, caption=cap, page=0) for num, cap in caption_matches]

    # Extract images if directory provided
    if images_dir:
        extract_images(pdf_path, images_dir)

    doc.close()
    return ParsedPaper(
        title=title,
        full_text=full_text,
        sections=sections,
        figures=figures,
        page_count=len(page_texts)
    )

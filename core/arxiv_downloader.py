"""arXiv paper downloader for PaperGuide.

Downloads PDF and metadata from arXiv.
"""
import re
from pathlib import Path
from dataclasses import dataclass
import requests


# arXiv URL patterns
ARXIV_PATTERNS = [
    r"arxiv\.org/abs/([\d.]+)",
    r"arxiv\.org/pdf/([\d.]+)",
    r"^([\d]{4}\.[\d]{4,5})$",  # Just the ID
]


@dataclass
class ArxivPaper:
    """arXiv paper metadata."""
    arxiv_id: str
    title: str
    authors: list[str]
    abstract: str
    pdf_path: Path | None = None


def extract_arxiv_id(url_or_id: str) -> str | None:
    """Extract arXiv ID from URL or direct ID."""
    url_or_id = url_or_id.strip()
    for pattern in ARXIV_PATTERNS:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    return None


def fetch_metadata(arxiv_id: str) -> dict:
    """Fetch paper metadata from arXiv API."""
    api_url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
    response = requests.get(api_url, timeout=30)
    response.raise_for_status()

    # Parse XML response (simple extraction)
    content = response.text
    title_match = re.search(r"<title>(.+?)</title>", content, re.DOTALL)
    title = title_match.group(1).strip() if title_match else "Unknown"
    # Skip the "arXiv Query:" title
    if "arXiv Query" in title:
        titles = re.findall(r"<title>(.+?)</title>", content, re.DOTALL)
        title = titles[1].strip() if len(titles) > 1 else "Unknown"

    # Extract authors
    authors = re.findall(r"<name>(.+?)</name>", content)

    # Extract abstract
    summary_match = re.search(r"<summary>(.+?)</summary>", content, re.DOTALL)
    abstract = summary_match.group(1).strip() if summary_match else ""

    return {"title": title, "authors": authors, "abstract": abstract}


def download_pdf(arxiv_id: str, output_dir: Path) -> Path:
    """Download PDF from arXiv."""
    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    pdf_path = output_dir / f"{arxiv_id.replace('.', '_')}.pdf"

    response = requests.get(pdf_url, timeout=60, stream=True)
    response.raise_for_status()

    with open(pdf_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    return pdf_path


def download_arxiv_paper(url_or_id: str, output_dir: Path) -> ArxivPaper | None:
    """Download arXiv paper and return metadata."""
    arxiv_id = extract_arxiv_id(url_or_id)
    if not arxiv_id:
        return None

    # Fetch metadata
    metadata = fetch_metadata(arxiv_id)

    # Download PDF
    pdf_path = download_pdf(arxiv_id, output_dir)

    return ArxivPaper(
        arxiv_id=arxiv_id,
        title=metadata["title"],
        authors=metadata["authors"],
        abstract=metadata["abstract"],
        pdf_path=pdf_path
    )

"""Task 1: Download public RMIT Vietnam policy documents."""
from pathlib import Path
import requests

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"
LEGAL_DOCUMENTS = {
    "student-fees-and-charges-guide-rmit-2026.pdf": "https://www.rmit.edu.vn/assets/vn/en/assets-for-production/documents/pdfs/study-at-rmit/tuition-fees/student-fees-and-charges-guide-06-2026.pdf",
    "scholarship-terms-and-conditions-rmit.pdf": "https://www.rmit.edu.vn/content/dam/rmit/vn/en/assets-for-production/documents/pdfs/study-at-rmit/scholarships/english-pdf/rmit-university-vietnam-scholarship-terms-and-conditions.pdf",
    "international-student-predeparture-guide-rmit.pdf": "https://www.rmit.edu.vn/content/dam/rmit/vn/en/assets-for-production/documents/pdfs/study-at-rmit/international-students/pre-departure-guide-for-study-abroad-students.pdf",
}

def setup_directory():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

def download_file(url, filename):
    response = requests.get(url, timeout=60, headers={"User-Agent": "Mozilla/5.0 (educational RAG lab)"})
    response.raise_for_status()
    if not response.content.startswith(b"%PDF") or len(response.content) <= 1024:
        raise ValueError(f"Invalid PDF response from {url}")
    path = DATA_DIR / filename
    path.write_bytes(response.content)
    return path

def collect_all():
    setup_directory()
    return [download_file(url, name) for name, url in LEGAL_DOCUMENTS.items()]

if __name__ == "__main__":
    collect_all()

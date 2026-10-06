import io

from docx import Document
from pypdf import PdfReader


def _docx_text(data: bytes) -> str:
    """Paragraphs AND tables, in document order (many resumes are laid out in tables)."""
    doc = Document(io.BytesIO(data))
    lines = []
    for child in doc.element.body.iterchildren():
        tag = child.tag.rsplit("}", 1)[-1]
        if tag == "p":
            lines.append("".join(t.text or "" for t in child.iter() if t.tag.endswith("}t")))
        elif tag == "tbl":
            for row in child.iter():
                if row.tag.endswith("}tc"):
                    cell = "\n".join("".join(t.text or "" for t in p.iter() if t.tag.endswith("}t"))
                                     for p in row if p.tag.endswith("}p"))
                    lines.append(cell)
    return "\n".join(lines)


def extract_text(uploaded_file):
    name = uploaded_file.name.lower()
    data = uploaded_file.getvalue()
    if name.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(data))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if name.endswith(".docx"):
        return _docx_text(data)
    if name.endswith(".txt"):
        return data.decode("utf-8", errors="ignore")
    raise ValueError("Unsupported file type.")

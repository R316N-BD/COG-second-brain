"""Explicit local text extraction into an inbox note. Optional office/PDF dependencies."""
import hashlib
import io
from pathlib import Path
from .paths import note_path, private_path

MAX=16*1024*1024
MAX_TEXT=128*1024

def extract(path, raw=None):
    path=Path(path)
    if raw is None:
        with path.open("rb") as handle:
            raw=handle.read(MAX+1)
    if len(raw)>MAX:
        raise ValueError("File exceeds 16 MiB.")
    suffix=path.suffix.lower()
    if suffix in {".txt",".md",".csv"}:
        text=raw.decode("utf-8-sig")
    elif suffix==".pdf":
        from pypdf import PdfReader
        reader=PdfReader(io.BytesIO(raw))
        if reader.is_encrypted or len(reader.pages)>100:
            raise ValueError("Encrypted or oversized PDF.")
        text="\n".join((page.extract_text() or "") for page in reader.pages)
    elif suffix in {".docx",".xlsx"}:
        import zipfile
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            if len(z.infolist())>5000 or sum(e.file_size for e in z.infolist())>64*1024*1024:
                raise ValueError("Office archive exceeds extraction budget.")
        if suffix==".docx":
            from docx import Document
            doc=Document(io.BytesIO(raw))
            text="\n".join(p.text for p in doc.paragraphs)
        else:
            from openpyxl import load_workbook
            book=load_workbook(io.BytesIO(raw),read_only=True,data_only=True,keep_links=False)
            try:
                lines=[]
                for sheet in book.worksheets[:10]:
                    lines.append("Sheet: "+sheet.title)
                    for row in sheet.iter_rows(max_row=200,max_col=30,values_only=True):
                        lines.append(" | ".join(str(v) if v is not None else "" for v in row))
                text="\n".join(lines)
            finally:
                book.close()
    else:
        raise ValueError("Supported: TXT, MD, CSV, PDF, DOCX, XLSX. Image OCR is not implemented.")
    if not text.strip():
        raise ValueError("No extracted text; scanned images need OCR.")
    if len(text.encode("utf-8"))>MAX_TEXT:
        raise ValueError("Extracted text exceeds 128 KiB.")
    return text

def ingest(data,path):
    root=private_path(data)
    path=Path(path)
    with path.open("rb") as handle:
        raw=handle.read(MAX+1)
    if len(raw)>MAX:
        raise ValueError("Source changed or exceeds limit.")
    text=extract(path,raw)
    digest=hashlib.sha256(raw).hexdigest()
    relative="00-inbox/import-"+digest+".md"
    destination=note_path(root,relative)
    with destination.open("x",encoding="utf-8") as handle:
        handle.write("# Imported document\n\nSource SHA-256: "+digest+"\n\nUntrusted extracted content; review before use.\n\n"+text+"\n")
    return {"path":relative,"source_sha256":digest,"notice":"Review sensitive content before indexing. This note is not automatically indexed."}

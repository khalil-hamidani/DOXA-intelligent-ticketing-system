import os
import json
import re
from mistralai import Mistral
from dotenv import load_dotenv

# =====================================================
# Simple Markdown splitter (no langchain dependency)
# =====================================================
class MarkdownHeaderTextSplitter:
    def __init__(self, headers=None, chunk_size=500, chunk_overlap=50):
        self.headers = headers or ["#", "##", "###"]
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text(self, text: str):
        pattern = r'(?m)^(#{1,6}\s.*)$'
        segments = []

        # No headers → fallback fixed chunks
        if not re.search(pattern, text):
            step = max(1, self.chunk_size - self.chunk_overlap)
            for i in range(0, len(text), step):
                segments.append(text[i:i + self.chunk_size])
            return segments

        parts = re.split(pattern, text)

        for i in range(1, len(parts), 2):
            heading = parts[i].strip()
            body = parts[i + 1].strip() if i + 1 < len(parts) else ""
            block = heading + "\n" + body

            step = max(1, self.chunk_size - self.chunk_overlap)
            for j in range(0, len(block), step):
                segments.append(block[j:j + self.chunk_size])

        return segments


# =====================================================
# Paths & ENV
# =====================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PDF_DIR = os.path.join(BASE_DIR, "pdfs")
TEXT_DIR = os.path.join(BASE_DIR, "texts")
INDEX_PATH = os.path.join(BASE_DIR, "index.json")

os.makedirs(TEXT_DIR, exist_ok=True)

load_dotenv(os.path.join(BASE_DIR, ".env"))

API_KEY = os.getenv("MISTRAL_API_KEY")
if not API_KEY:
    raise RuntimeError("❌ MISTRAL_API_KEY not found in ai/kb/.env")

# =====================================================
# Mistral client
# =====================================================
client = Mistral(api_key=API_KEY)

# =====================================================
# OCR + text extraction
# =====================================================
documents = []

for pdf_file in os.listdir(PDF_DIR):
    if not pdf_file.lower().endswith(".pdf"):
        continue

    pdf_path = os.path.join(PDF_DIR, pdf_file)
    print(f"📄 OCR processing: {pdf_file}")

    # Upload PDF using the SDK FileTypedDict (file handle + metadata)
    with open(pdf_path, "rb") as fh:
        file_payload = {
            "file_name": pdf_file,
            "content": fh,
            "content_type": "application/pdf",
        }
        uploaded = client.files.upload(
            file=file_payload,
            purpose="ocr",
        )

    # OCR
    ocr = client.ocr.process(
        model="mistral-ocr-latest",
        document={
            "type": "file",
            "file_id": uploaded.id,
        },
        table_format="markdown",
        include_image_base64=False,
    )

    # Extract markdown text
    pages_text = []
    for page in ocr.pages:
        if hasattr(page, "markdown") and page.markdown:
            pages_text.append(page.markdown)

    full_text = "\n\n".join(pages_text)

    # Save raw text
    txt_path = os.path.join(TEXT_DIR, pdf_file.replace(".pdf", ".txt"))
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(full_text)

    documents.append({
        "source": pdf_file,
        "content": full_text,
    })

print("✅ OCR completed for all PDFs")

# =====================================================
# Split documents into chunks
# =====================================================
splitter = MarkdownHeaderTextSplitter(
    headers=["#", "##", "###"],
    chunk_size=500, ## 500 characters
    chunk_overlap=50,
)

indexed_chunks = []

for doc in documents:
    chunks = splitter.split_text(doc["content"])
    print(f"✂️ {doc['source']} → {len(chunks)} chunks")

    for i, chunk in enumerate(chunks):
        indexed_chunks.append({
            "content": chunk,
            "meta": {
                "source": doc["source"],
                "chunk_id": i,
            },
        })

# =====================================================
# Save local index (JSON)
# =====================================================
with open(INDEX_PATH, "w", encoding="utf-8") as f:
    json.dump(indexed_chunks, f, ensure_ascii=False, indent=2)

print(f"📦 Knowledge base indexed → {INDEX_PATH}")
print("🎉 ingest_kb.py finished successfully")

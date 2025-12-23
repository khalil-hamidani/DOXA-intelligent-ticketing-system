# KB & RAG Pipeline Status

## ✅ Completed

1. **PDF Ingestion (`ingest_kb.py`)**
   - ✅ Reads PDFs from `ai/kb/pdfs/`
   - ✅ Uses Mistral OCR API to extract text
   - ✅ Splits text into 359 chunks
   - ✅ Saves chunks to `ai/kb/index.json`

2. **ChromaDB Indexing**
   - ✅ Ingests 359 chunks from `index.json` into ChromaDB
   - ✅ Uses SentenceTransformer embeddings (all-MiniLM-L6-v2)
   - ✅ Persists to `ai/kb/chroma_db/`
   - Script: `ingest_to_chroma.py`

3. **Document Retrieval**
   - ✅ ChromaDB retriever (`retriever.py`) retrieves documents with semantic search
   - ✅ Test: `test_context.py` successfully retrieves 5 relevant documents
   - ✅ Simple JSON retriever (`simple_retriever.py`) also available as fallback

4. **RAG Pipeline with Mistral**
   - ✅ Retrieves documents from ChromaDB
   - ✅ Builds context from retrieved chunks
   - ✅ Calls `mistralai.Mistral.chat.complete()` to generate response
   - ✅ Test: `test_rag_pipeline_mistral.py` working (may be slow due to embedding init)
   - ✅ Lightweight version (`rag_pipeline_lightweight.py`) uses JSON retrieval (faster)

## 🔧 How to Use

### 1. Ingest PDFs to JSON Index
```bash
cd ai/kb
python ingest_kb.py
```

### 2. Ingest Index to ChromaDB
```bash
python ingest_to_chroma.py
```

### 3. Test Retrieval
```bash
python test_context.py
```

### 4. Test RAG Pipeline (with ChromaDB)
```bash
python test_rag_pipeline_mistral.py
```

### 5. Test Lightweight RAG Pipeline (with JSON)
```bash
python rag_pipeline_lightweight.py
```

## ⚙️ Configuration

Set in `ai/kb/.env`:
```env
MISTRAL_API_KEY=your_key_here
MISTRAL_MODEL=mistral-large-latest  # optional
```

## 📊 Statistics

- **Total chunks indexed**: 359
- **ChromaDB collections**: kb_chunks (with 359 documents)
- **PDF sources**: 7 files
  - Doxa Conditions générales.pdf
  - FAQ_Doxa.pdf
  - Guide_Onboarding.pdf
  - Guide_Securite.pdf
  - Guide_Utilisateur_Doxa.pdf
  - Tarification_Offres.pdf
  - Troubleshooting_Support.pdf

## 🐛 Known Issues

- ChromaDB embedding function initialization can be slow on first run (downloads model)
- For faster queries, use `rag_pipeline_lightweight.py` which uses JSON-based retrieval
- Both pipelines require `MISTRAL_API_KEY` environment variable

## 📚 Files Created/Updated

- `ingest_kb.py` - PDF OCR ingest (from Mistral PDF files)
- `ingest_to_chroma.py` - ChromaDB batch ingest (NEW)
- `retriever.py` - ChromaDB retriever (FIXED: now uses get_collection first)
- `simple_retriever.py` - JSON-based retriever (NEW)
- `rag_pipeline_mistral.py` - RAG pipeline (UPDATED: uses retriever.py)
- `rag_pipeline_lightweight.py` - Fast RAG pipeline (NEW)
- `test_context.py` - Retrieval test (FIXED: absolute paths)
- `test_rag_pipeline_mistral.py` - RAG test (FIXED: absolute paths)
- `check_chroma.py` - ChromaDB diagnostics (NEW)

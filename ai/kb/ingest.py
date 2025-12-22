"""
PDF Ingestion with Mistral OCR and Markdown Extraction

Handles PDF document processing with OCR, clean Markdown extraction,
hierarchical organization by titles (## headers), and semantic chunking.
"""

from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, asdict
import logging

try:
    from mistralai.client import MistralClient
    from mistralai.models.chat_message import ChatMessage
except ImportError:
    MistralClient = None

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    RecursiveCharacterTextSplitter = None

logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    """Represents a document chunk with metadata."""
    content: str
    chunk_id: str
    source_file: str
    title: Optional[str] = None
    section: Optional[str] = None
    page_number: Optional[int] = None
    chunk_index: int = 0
    total_chunks: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class MistralOCRProcessor:
    """Handles PDF processing with Mistral OCR."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Mistral OCR processor.
        
        Args:
            api_key: Mistral API key (uses env variable if not provided)
        """
        if MistralClient is None:
            raise ImportError("mistralai package required. Install: pip install mistralai")
        
        self.client = MistralClient(api_key=api_key)
    
    def extract_pdf_to_markdown(self, pdf_path: Path) -> str:
        """
        Extract PDF content to clean Markdown using Mistral OCR.
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            Clean Markdown string
        """
        try:
            # Read PDF binary
            with open(pdf_path, "rb") as f:
                pdf_data = f.read()
            
            logger.info(f"Processing PDF with Mistral OCR: {pdf_path}")
            
            # Use Mistral's vision capabilities to process PDF
            message = ChatMessage(
                role="user",
                content=[
                    {
                        "type": "text",
                        "text": "Extract all text from this PDF and format as clean Markdown with proper hierarchy using ## for section headers. Preserve the document structure."
                    },
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_data
                        }
                    }
                ]
            )
            
            response = self.client.chat(
                messages=[message],
                model="pixtral-12b-2409",
                max_tokens=4096
            )
            
            markdown_content = response.choices[0].message.content
            logger.info(f"Extracted {len(markdown_content)} characters from {pdf_path}")
            
            return markdown_content
        
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {e}")
            raise


class PDFIngestor:
    """Handles PDF document ingestion with OCR and chunking."""
    
    def __init__(self, config: 'KBConfig'):
        """
        Initialize PDF ingestor.
        
        Args:
            config: KBConfig instance
        """
        self.config = config
        self.ocr_processor = None
        
        if config.enable_mistral_ocr:
            self.ocr_processor = MistralOCRProcessor(api_key=config.mistral_api_key)
    
    def extract_markdown(self, pdf_path: Path) -> str:
        """
        Extract PDF to clean Markdown.
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            Clean Markdown string
        """
        if not self.ocr_processor:
            raise RuntimeError("OCR not enabled. Set enable_mistral_ocr=True")
        
        return self.ocr_processor.extract_pdf_to_markdown(pdf_path)
    
    def parse_hierarchical_structure(self, markdown_content: str) -> List[Tuple[Optional[str], str]]:
        """
        Parse Markdown content into hierarchical sections using ## headers.
        
        Args:
            markdown_content: Raw Markdown content
        
        Returns:
            List of (title, section_content) tuples
        """
        lines = markdown_content.split('\n')
        sections = []
        current_title = None
        section_content = []
        
        for line in lines:
            # Match ## headers (main section titles)
            if line.startswith('## '):
                # Save previous section
                if section_content:
                    content = '\n'.join(section_content).strip()
                    if content:
                        sections.append((current_title, content))
                    section_content = []
                
                # Start new section
                current_title = line[3:].strip()
            else:
                section_content.append(line)
        
        # Add last section
        if section_content:
            content = '\n'.join(section_content).strip()
            if content:
                sections.append((current_title, content))
        
        return sections if sections else [(None, markdown_content)]
    
    def split_by_semantic_chunks(self, text: str, title: Optional[str] = None) -> List[str]:
        """
        Split text into semantic chunks using LangChain TextSplitter.
        
        Args:
            text: Text to split
            title: Optional section title for context
        
        Returns:
            List of text chunks
        """
        if RecursiveCharacterTextSplitter is None:
            raise ImportError("langchain-text-splitters required. Install: pip install langchain-text-splitters")
        
        try:
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.config.chunk_size,
                chunk_overlap=self.config.chunk_overlap,
                separators=["\n\n", "\n", ". ", " ", ""],
                length_function=len,
            )
            
            chunks = splitter.split_text(text)
            logger.debug(f"Split text into {len(chunks)} chunks (title: {title})")
            
            return chunks
        
        except Exception as e:
            logger.warning(f"TextSplitter error: {e}, using fallback")
            return self._split_text_simple(text)
    
    def _split_text_simple(self, text: str, chunk_size: Optional[int] = None) -> List[str]:
        """Simple fallback text splitting."""
        chunk_size = chunk_size or self.config.chunk_size
        overlap = self.config.chunk_overlap
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            start = end - overlap
        
        return chunks
    
    def ingest_pdf(
        self,
        pdf_path: Path,
        doc_id: Optional[str] = None,
    ) -> List[DocumentChunk]:
        """
        Complete PDF ingestion pipeline.
        
        Args:
            pdf_path: Path to PDF file
            doc_id: Optional document ID (uses filename if not provided)
        
        Returns:
            List of DocumentChunk objects
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        doc_id = doc_id or pdf_path.stem
        logger.info(f"Ingesting PDF: {pdf_path}")
        
        # Step 1: Extract markdown with OCR
        markdown_content = self.extract_markdown(pdf_path)
        
        # Step 2: Parse hierarchical structure (by ## headers)
        if self.config.use_title_splits:
            sections = self.parse_hierarchical_structure(markdown_content)
        else:
            sections = [(None, markdown_content)]
        
        # Step 3: Create chunks with metadata
        all_chunks = []
        chunk_counter = 0
        
        for section_title, section_text in sections:
            # Split section into semantic chunks
            text_chunks = self.split_by_semantic_chunks(section_text, section_title)
            
            for chunk_idx, chunk_text in enumerate(text_chunks):
                chunk_id = f"{doc_id}_section_{len(all_chunks)}_chunk_{chunk_idx}"
                
                chunk = DocumentChunk(
                    content=chunk_text,
                    chunk_id=chunk_id,
                    source_file=str(pdf_path),
                    title=section_title,
                    section=section_title,
                    chunk_index=chunk_idx,
                    total_chunks=len(text_chunks),
                )
                
                all_chunks.append(chunk)
                chunk_counter += 1
        
        logger.info(f"Ingested {pdf_path}: {len(all_chunks)} chunks from {len(sections)} sections")
        
        return all_chunks
    
    def ingest_directory(self, directory: Optional[Path] = None) -> List[DocumentChunk]:
        """
        Ingest all PDFs in directory.
        
        Args:
            directory: Directory containing PDFs (uses config.pdf_input_path if not provided)
        
        Returns:
            Combined list of chunks from all documents
        """
        directory = directory or self.config.pdf_input_path
        directory = Path(directory)
        
        if not directory.exists():
            logger.warning(f"Directory does not exist: {directory}")
            return []
        
        all_chunks = []
        pdf_files = list(directory.glob("*.pdf"))
        
        if not pdf_files:
            logger.warning(f"No PDF files found in {directory}")
            return []
        
        logger.info(f"Found {len(pdf_files)} PDF files in {directory}")
        
        for pdf_path in pdf_files:
            try:
                chunks = self.ingest_pdf(pdf_path)
                all_chunks.extend(chunks)
            except Exception as e:
                logger.error(f"Error ingesting {pdf_path}: {e}")
        
        logger.info(f"Total chunks from directory: {len(all_chunks)}")
        
        return all_chunks

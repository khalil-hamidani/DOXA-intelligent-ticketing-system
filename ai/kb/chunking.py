"""
Document Chunking Module: Split documents into retrieval units

Handles semantic chunking with:
1. Header-based splitting (respects document structure)
2. Configurable chunk size with overlap
3. Parent-child relationships for context recovery
4. Metadata preservation
5. Small chunk merging

Follows Haystack document processing patterns.
"""

import logging
import re
from typing import List, Optional, Dict, Tuple, Any
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    """Single chunk of a document ready for embedding."""
    
    chunk_id: str              # Unique ID: "doc_source_chunk_0"
    text: str                  # The actual chunk content
    source_doc_id: str         # Original document ID
    chunk_index: int           # Position within document (0-indexed)
    section_title: Optional[str] = None  # Chapter/section name if known
    
    # Parent-child relationship for context recovery
    parent_chunk_id: Optional[str] = None
    child_chunk_ids: List[str] = field(default_factory=list)
    
    # Metadata
    doc_source: str = "unknown"  # Filename or URL
    doc_title: str = "Untitled"  # Document title
    page_number: Optional[int] = None  # For PDFs
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def summary(self) -> str:
        """First 100 chars as summary."""
        return self.text[:100].replace("\n", " ") + "..."
    
    def to_dict(self) -> Dict:
        """Convert to dict for storage."""
        return {
            "chunk_id": self.chunk_id,
            "text": self.text,
            "source_doc_id": self.source_doc_id,
            "chunk_index": self.chunk_index,
            "section_title": self.section_title,
            "parent_chunk_id": self.parent_chunk_id,
            "doc_source": self.doc_source,
            "doc_title": self.doc_title,
            "page_number": self.page_number,
            "metadata": self.metadata
        }


def chunk_document(
    text: str,
    doc_source: str,
    doc_title: str,
    chunk_size: int = 512,
    chunk_overlap: int = 50,
    split_by_headers: bool = True,
    merge_short_chunks: bool = True,
    min_chunk_size: int = 100,
    page_number: Optional[int] = None
) -> List[DocumentChunk]:
    """
    Chunk a document into retrieval units.
    
    Strategy:
    1. If split_by_headers=True: Split by markdown headers first
    2. Then split each section by chunk_size (with overlap)
    3. Merge very small chunks with neighbors
    4. Create parent-child relationships
    
    Args:
        text: Document text to chunk
        doc_source: Source file/URL for tracking
        doc_title: Document title
        chunk_size: Target chunk size in characters (not tokens!)
        chunk_overlap: Overlap between consecutive chunks
        split_by_headers: Split by markdown headers first?
        merge_short_chunks: Merge chunks smaller than min_chunk_size?
        min_chunk_size: Minimum chunk size in characters
        page_number: For PDF chunks (optional)
    
    Returns:
        List of DocumentChunk objects ready for embedding
    
    Example:
        text = "# Installation\n\nTo install...\n\n## Prerequisites\n\nYou need..."
        chunks = chunk_document(
            text,
            doc_source="install_guide.md",
            doc_title="Installation Guide",
            chunk_size=512,
            chunk_overlap=50
        )
        # Returns: [
        #   DocumentChunk(chunk_id="install_guide_0", text="# Installation\n\nTo install...", ...),
        #   DocumentChunk(chunk_id="install_guide_1", text="## Prerequisites\n\nYou need...", ...),
        #   ...
        # ]
    """
    
    if not text or not text.strip():
        logger.warning(f"Empty text for document: {doc_source}")
        return []
    
    # Normalize whitespace
    text = normalize_text(text)
    
    chunks = []
    chunk_counter = 0
    
    try:
        # Step 1: Split by headers if requested
        sections = []
        if split_by_headers:
            sections = _split_by_headers(text)
        else:
            sections = [(None, text)]  # Single section with no header
        
        # Step 2: Chunk each section
        section_chunks = []
        for section_title, section_text in sections:
            section_chunk_list = _chunk_text(
                section_text,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            
            for chunk_index, chunk_text in enumerate(section_chunk_list):
                chunk_id = f"{doc_source.replace('.', '_')}_{chunk_counter}"
                
                chunk = DocumentChunk(
                    chunk_id=chunk_id,
                    text=chunk_text,
                    source_doc_id=doc_source,
                    chunk_index=chunk_counter,
                    section_title=section_title,
                    doc_source=doc_source,
                    doc_title=doc_title,
                    page_number=page_number,
                    metadata={
                        "section": section_title or "main",
                        "source": doc_source,
                        "title": doc_title,
                        "chunk_length": len(chunk_text)
                    }
                )
                
                section_chunks.append(chunk)
                chunk_counter += 1
        
        chunks = section_chunks
        
        # Step 3: Merge small chunks
        if merge_short_chunks:
            chunks = _merge_small_chunks(chunks, min_chunk_size)
            # Re-index after merge
            for idx, chunk in enumerate(chunks):
                chunk.chunk_index = idx
        
        # Step 4: Create parent-child relationships
        chunks = _create_parent_child_relationships(chunks)
        
        logger.info(
            f"Chunked document '{doc_title}' ({doc_source}): "
            f"text_len={len(text)}, chunks={len(chunks)}, "
            f"avg_chunk_size={len(text) / max(1, len(chunks)):.0f}"
        )
        
        return chunks
    
    except Exception as e:
        logger.error(f"Error chunking document {doc_source}: {e}")
        return []


def _split_by_headers(text: str) -> List[Tuple[Optional[str], str]]:
    """
    Split text by markdown headers.
    
    Returns: List of (header, section_text) tuples
    """
    
    # Markdown header pattern: # or ## or ### etc
    header_pattern = r'^(#{1,6})\s+(.+)$'
    
    lines = text.split('\n')
    sections = []
    current_header = None
    current_section = []
    
    for line in lines:
        match = re.match(header_pattern, line)
        
        if match:
            # Save previous section
            if current_section:
                section_text = '\n'.join(current_section).strip()
                if section_text:
                    sections.append((current_header, section_text))
            
            # Start new section
            level = len(match.group(1))
            current_header = match.group(2)
            current_section = [line]
        
        else:
            current_section.append(line)
    
    # Add final section
    if current_section:
        section_text = '\n'.join(current_section).strip()
        if section_text:
            sections.append((current_header, section_text))
    
    if not sections:
        sections = [(None, text)]
    
    logger.debug(f"Split into {len(sections)} sections by headers")
    return sections


def _chunk_text(
    text: str,
    chunk_size: int = 512,
    chunk_overlap: int = 50
) -> List[str]:
    """
    Split text into chunks with overlap.
    
    Uses character-based splitting (not token-based).
    """
    
    chunks = []
    
    if len(text) <= chunk_size:
        return [text]
    
    # Split by sentences first for better boundaries
    sentences = _split_sentences(text)
    
    current_chunk = []
    current_length = 0
    
    for sentence in sentences:
        sentence_len = len(sentence)
        
        # Check if adding this sentence exceeds chunk_size
        if current_length + sentence_len > chunk_size and current_chunk:
            # Save current chunk
            chunk_text = ' '.join(current_chunk).strip()
            chunks.append(chunk_text)
            
            # Start new chunk with overlap
            current_chunk = _get_overlap_text(chunks[-1], chunk_overlap)
            current_length = len(' '.join(current_chunk))
        
        current_chunk.append(sentence)
        current_length += sentence_len
    
    # Add final chunk
    if current_chunk:
        chunk_text = ' '.join(current_chunk).strip()
        chunks.append(chunk_text)
    
    logger.debug(f"Split text ({len(text)} chars) into {len(chunks)} chunks")
    return chunks


def _split_sentences(text: str) -> List[str]:
    """Split text by sentence boundaries."""
    
    # Simple sentence splitter
    sentence_endings = r'([.!?])\s+'
    sentences = re.split(sentence_endings, text)
    
    # Reconstruct sentences with punctuation
    result = []
    for i in range(0, len(sentences), 2):
        if i + 1 < len(sentences):
            result.append(sentences[i] + sentences[i + 1])
        elif sentences[i]:
            result.append(sentences[i])
    
    return result


def _get_overlap_text(chunk: str, overlap_size: int) -> List[str]:
    """Get last overlap_size characters from chunk as list of words."""
    
    if len(chunk) <= overlap_size:
        return chunk.split()
    
    overlap_text = chunk[-overlap_size:]
    return overlap_text.split()


def _merge_small_chunks(
    chunks: List[DocumentChunk],
    min_size: int
) -> List[DocumentChunk]:
    """Merge chunks smaller than min_size with neighbors."""
    
    if not chunks:
        return chunks
    
    merged = []
    current_chunk = None
    
    for chunk in chunks:
        if current_chunk is None:
            current_chunk = chunk
        elif len(chunk.text) < min_size:
            # Merge with current
            current_chunk.text += " " + chunk.text
            current_chunk.metadata["merged"] = True
        else:
            # Save current, start new
            merged.append(current_chunk)
            current_chunk = chunk
    
    if current_chunk:
        merged.append(current_chunk)
    
    logger.debug(f"Merged small chunks: {len(chunks)} → {len(merged)}")
    return merged


def _create_parent_child_relationships(
    chunks: List[DocumentChunk]
) -> List[DocumentChunk]:
    """
    Create parent-child relationships for context recovery.
    
    Large chunks can be children of smaller summary chunks.
    """
    
    # For now, skip this (future enhancement)
    # Could create parent chunks that summarize 3-5 children
    
    return chunks


def normalize_text(text: str) -> str:
    """Normalize text: remove extra whitespace, fix encoding."""
    
    # Remove multiple newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove leading/trailing whitespace from lines
    lines = [line.rstrip() for line in text.split('\n')]
    text = '\n'.join(lines)
    
    # Remove non-breaking spaces and other unicode whitespace
    text = text.replace('\xa0', ' ')
    text = text.replace('\u200b', '')  # Zero-width space
    
    return text


def chunk_directory(
    directory: Path,
    file_pattern: str = "*.txt",
    chunk_size: int = 512,
    chunk_overlap: int = 50
) -> List[DocumentChunk]:
    """
    Chunk all matching files in a directory.
    
    Args:
        directory: Path to directory
        file_pattern: Glob pattern for files (e.g., "*.md", "*.pdf")
        chunk_size: Target chunk size
        chunk_overlap: Overlap between chunks
    
    Returns:
        List of chunks from all files
    """
    
    all_chunks = []
    
    try:
        directory = Path(directory)
        files = list(directory.glob(file_pattern))
        
        logger.info(f"Processing {len(files)} files from {directory}")
        
        for file_path in files:
            try:
                text = file_path.read_text(encoding='utf-8')
                
                chunks = chunk_document(
                    text=text,
                    doc_source=file_path.name,
                    doc_title=file_path.stem,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap
                )
                
                all_chunks.extend(chunks)
                logger.info(f"Processed {file_path.name}: {len(chunks)} chunks")
            
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
        
        logger.info(f"Total chunks from directory: {len(all_chunks)}")
        return all_chunks
    
    except Exception as e:
        logger.error(f"Error processing directory {directory}: {e}")
        return []

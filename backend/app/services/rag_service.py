"""Retrieval-Augmented Generation (RAG) Service for Exam Prep Agent.

Provides semantic document chunking, hybrid keyword/BM25 retrieval,
source citation formatting, and context injection for AI Tutor and Question Generator.
"""
import re
import math
import hashlib
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("service.rag")


class TextChunk(BaseModel):
    chunk_id: str
    user_id: int
    source_document: str # e.g. "CS_Syllabus.pdf"
    subject_name: Optional[str] = None
    topic_name: Optional[str] = None
    text: str
    char_start: int
    char_end: int
    keywords: List[str] = Field(default_factory=list)


class RetrievedChunk(BaseModel):
    chunk_id: str
    source_document: str
    subject_name: Optional[str] = None
    topic_name: Optional[str] = None
    text: str
    score: float # 0.0 to 1.0 relevance score
    citation: str # formatted citation e.g. "[Source: CS_Syllabus.pdf | Topic: Graph Theory]"


class RAGIndex:
    """In-memory hybrid retrieval index with persistence to database/memory."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RAGIndex, cls).__new__(cls)
            cls._instance.chunks_by_user: Dict[int, List[TextChunk]] = {}
        return cls._instance

    def chunk_document(
        self,
        text: str,
        source_document: str,
        user_id: int,
        subject_name: Optional[str] = None,
        topic_name: Optional[str] = None,
        chunk_size: int = 500,
        chunk_overlap: int = 100,
    ) -> List[TextChunk]:
        """Splits document text into overlapping semantic chunks with metadata."""
        if not text:
            return []

        # Clean text
        cleaned_text = re.sub(r"\s+", " ", text).strip()
        chunks: List[TextChunk] = []
        start = 0
        total_len = len(cleaned_text)

        while start < total_len:
            end = min(start + chunk_size, total_len)
            
            # Try not to break words in the middle
            if end < total_len:
                last_space = cleaned_text.rfind(" ", start, end)
                if last_space > start + (chunk_size // 2):
                    end = last_space

            chunk_text = cleaned_text[start:end].strip()
            if len(chunk_text) >= 40:
                # Extract salient keywords for fast lexical scoring
                words = re.findall(r"\b[A-Za-z0-9_\-]{3,}\b", chunk_text.lower())
                stopwords = {
                    "the", "and", "for", "with", "that", "this", "from", "are", "was",
                    "were", "will", "have", "has", "had", "can", "could", "should", "not"
                }
                keywords = list(set(w for w in words if w not in stopwords))

                chunk_id = f"chk_{hashlib.md5(f'{source_document}_{start}_{chunk_text[:30]}'.encode()).hexdigest()[:10]}"
                chunk = TextChunk(
                    chunk_id=chunk_id,
                    user_id=user_id,
                    source_document=source_document,
                    subject_name=subject_name,
                    topic_name=topic_name,
                    text=chunk_text,
                    char_start=start,
                    char_end=end,
                    keywords=keywords,
                )
                chunks.append(chunk)

            start += (chunk_size - chunk_overlap)

        # Store in user index
        user_chunks = self.chunks_by_user.setdefault(user_id, [])
        # Replace existing chunks from same document to avoid duplicates
        self.chunks_by_user[user_id] = [c for c in user_chunks if c.source_document != source_document] + chunks

        logger.info("Indexed %d chunks for user %d from document %s", len(chunks), user_id, source_document)
        return chunks

    def retrieve(
        self,
        query: str,
        user_id: int,
        top_k: int = 3,
        subject_filter: Optional[str] = None,
    ) -> List[RetrievedChunk]:
        """Retrieves top-k relevant chunks using BM25-inspired lexical + term-frequency matching."""
        user_chunks = self.chunks_by_user.get(user_id, [])
        if not user_chunks:
            # Check if there are demo chunks or global chunks
            user_chunks = self.chunks_by_user.get(0, [])
            if not user_chunks:
                return []

        query_tokens = [w.lower() for w in re.findall(r"\b[A-Za-z0-9_\-]{3,}\b", query.lower())]
        if not query_tokens:
            return []

        scored_chunks = []

        for chunk in user_chunks:
            if subject_filter and chunk.subject_name and subject_filter.lower() not in chunk.subject_name.lower():
                continue

            chunk_keywords_set = set(chunk.keywords)
            chunk_text_lower = chunk.text.lower()

            # 1. Exact phrase boost
            phrase_score = 0.0
            if query.lower() in chunk_text_lower:
                phrase_score += 0.40

            # 2. Token overlap and frequency
            matched_tokens = 0
            for token in query_tokens:
                if token in chunk_keywords_set:
                    matched_tokens += 1
                elif token in chunk_text_lower:
                    matched_tokens += 0.5

            token_score = (matched_tokens / len(query_tokens)) * 0.60
            final_score = min(1.0, round(phrase_score + token_score, 3))

            if final_score > 0.15:
                citation_label = chunk.source_document
                if chunk.topic_name:
                    citation_label += f" § {chunk.topic_name}"
                elif chunk.subject_name:
                    citation_label += f" ({chunk.subject_name})"

                scored_chunks.append(RetrievedChunk(
                    chunk_id=chunk.chunk_id,
                    source_document=chunk.source_document,
                    subject_name=chunk.subject_name,
                    topic_name=chunk.topic_name,
                    text=chunk.text,
                    score=final_score,
                    citation=f"[Source: {citation_label}]",
                ))

        # Sort descending by relevance score
        scored_chunks.sort(key=lambda x: x.score, reverse=True)
        return scored_chunks[:top_k]

    def format_context_for_prompt(self, chunks: List[RetrievedChunk]) -> str:
        """Formats retrieved chunks into a prompt-ready context block with citations."""
        if not chunks:
            return ""

        context_lines = [
            "--- RETRIEVED SYLLABUS & CURRICULUM CONTEXT (RAG Grounding) ---"
        ]
        for idx, chk in enumerate(chunks, 1):
            context_lines.append(f"Passage {idx} {chk.citation}:")
            context_lines.append(f'"{chk.text}"')
            context_lines.append("")
        context_lines.append("--- END OF RETRIEVED CONTEXT ---")
        context_lines.append("Instructions: Ground your explanation directly in the retrieved syllabus context above. Cite the source where appropriate.")
        return "\n".join(context_lines)


# Global RAG index singleton
rag_index = RAGIndex()


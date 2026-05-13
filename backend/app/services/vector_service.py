# backend/app/services/vector_service.py

from sentence_transformers import SentenceTransformer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.models.document import Document
from typing import Optional
import numpy as np


class VectorService:
    _model: Optional[SentenceTransformer] = None

    EMBEDDING_DIM = 384
    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 50

    @classmethod
    def get_model(cls) -> SentenceTransformer:
        """
        Lazy load embedding model.
        """

        if cls._model is None:
            print("⏳ Loading embedding model...")

            cls._model = SentenceTransformer(
                "all-MiniLM-L6-v2"
            )

            print("✅ Embedding model loaded")

        return cls._model

    @classmethod
    def embed_text(cls, text: str) -> list[float]:
        """
        Convert text into vector embedding.
        """

        model = cls.get_model()

        embedding = model.encode(
            text,
            normalize_embeddings=True
        )

        return embedding.tolist()

    @classmethod
    def chunk_text(cls, text: str) -> list[str]:
        """
        Split text into overlapping chunks.
        """

        chunks = []
        start = 0

        while start < len(text):
            end = start + cls.CHUNK_SIZE

            # Try to split at sentence boundary
            if end < len(text):
                last_period = text.rfind(".", start, end)
                last_newline = text.rfind("\n", start, end)

                boundary = max(
                    last_period,
                    last_newline
                )

                if boundary > start + 100:
                    end = boundary + 1

            chunk = text[start:end].strip()

            if chunk:
                chunks.append(chunk)

            start = end - cls.CHUNK_OVERLAP

        return chunks

    @classmethod
    async def store_embeddings(
        cls,
        db: AsyncSession,
        document: Document
    ) -> bool:
        """
        Generate and store embedding for document.
        """

        if not document.extracted_text:
            return False

        try:
            text_to_embed = document.extracted_text[:2000]

            embedding = cls.embed_text(text_to_embed)

            # Pad embedding to match pgvector size
            padded = embedding + [0.0] * (
                1536 - len(embedding)
            )

            # Correct vector string format
            embedding_str = (
                "[" + ",".join(map(str, padded)) + "]"
            )

            await db.execute(
                text(
                    """
                    UPDATE documents
                    SET embedding = CAST(:embedding AS vector)
                    WHERE id = CAST(:id AS uuid)
                    """
                ),
                {
                    "embedding": embedding_str,
                    "id": str(document.id)
                }
            )

            await db.commit()

            print(
                f"✅ Embedding stored for document {document.id}"
            )

            return True

        except Exception as e:
            print(f"❌ Error storing embedding: {e}")

            return False

    @classmethod
    async def search_similar(
        cls,
        db: AsyncSession,
        query: str,
        limit: int = 5
    ) -> list[dict]:
        """
        Find documents most similar to query.
        """

        try:
            query_embedding = cls.embed_text(query)

            # Pad to 1536 dimensions
            padded = query_embedding + [0.0] * (
                1536 - len(query_embedding)
            )

            # Convert to pgvector string format
            embedding_str = (
                "[" + ",".join(map(str, padded)) + "]"
            )

            result = await db.execute(
                text(
                    """
                    SELECT
                        id,
                        original_name,
                        file_type,
                        extracted_text,
                        1 - (
                            embedding <=> CAST(:embedding AS vector)
                        ) AS similarity
                    FROM documents
                    WHERE embedding IS NOT NULL
                    ORDER BY embedding <=> CAST(:embedding AS vector)
                    LIMIT :limit
                    """
                ),
                {
                    "embedding": embedding_str,
                    "limit": limit
                }
            )

            rows = result.fetchall()

            return [
                {
                    "document_id": str(row.id),
                    "filename": row.original_name,
                    "file_type": row.file_type,
                    "similarity": round(
                        float(row.similarity),
                        4
                    ),
                    "excerpt": (
                        row.extracted_text[:300]
                        if row.extracted_text
                        else ""
                    )
                }
                for row in rows
            ]

        except Exception as e:
            print(f"❌ Vector search error: {e}")

            return []

    @classmethod
    def find_relevant_chunks(
        cls,
        query: str,
        text: str,
        top_k: int = 3
    ) -> list[str]:
        """
        Find most relevant chunks for query.
        """

        chunks = cls.chunk_text(text)

        if not chunks:
            return []

        model = cls.get_model()

        query_embedding = model.encode(
            query,
            normalize_embeddings=True
        )

        chunk_embeddings = model.encode(
            chunks,
            normalize_embeddings=True
        )

        similarities = np.dot(
            chunk_embeddings,
            query_embedding
        )

        top_indices = np.argsort(
            similarities
        )[::-1][:top_k]

        return [chunks[i] for i in top_indices]
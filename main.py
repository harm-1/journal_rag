#!/usr/bin/env python3.12
"""
Journal RAG System using Ollama
A local RAG system for querying personal journal files organized by day
"""

import argparse
import os
import re
import sqlite3
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import requests
from sentence_transformers import SentenceTransformer


def extract_date(filename: str, content: str) -> str:
    """Extract date from filename or content"""
    # Try filename patterns: YYYY-MM-DD, YYYYMMDD, etc.
    date_patterns = [
        r"(\d{4}-\d{2}-\d{2})",
        r"(\d{4}\d{2}\d{2})",
        r"(\d{2}-\d{2}-\d{4})",
        r"(\d{2}/\d{2}/\d{4})",
    ]

    for pattern in date_patterns:
        match = re.search(pattern, filename)
        if match:
            return match.group(1)

    # Try to find date in content
    for pattern in date_patterns:
        match = re.search(pattern, content[:200])  # Check first 200 chars
        if match:
            return match.group(1)

    return "Unknown"


def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split text into overlapping chunks"""
    words = text.split()
    chunks = []

    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i : i + chunk_size])
        chunks.append(chunk)

        if i + chunk_size >= len(words):
            break

    return chunks


class JournalRAG:
    def __init__(
        self,
        journal_dir: str,
        db_path: str = "diary_embeddings.db",
        embedding_model: str = "all-MiniLM-L6-v2",
        ollama_model: str = "llama2",
    ):
        """
        Initialize the Journal RAG system

        Args:
            journal_dir: Directory containing diary files
            db_path: Path to SQLite database for embeddings
            embedding_model: SentenceTransformer model for embeddings
            ollama_model: Ollama model name for generation
        """
        self.journal_dir = Path(journal_dir)
        self.db_path = db_path
        self.embedding_model = SentenceTransformer(embedding_model)
        self.ollama_model = ollama_model
        self.ollama_url = "http://localhost:11434/api/generate"

    def init_database(self):
        """Initialize SQLite database for storing embeddings"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS journal_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT,
                date TEXT,
                content TEXT,
                embedding BLOB,
                chunk_index INTEGER
            )
        """
        )

        conn.commit()
        conn.close()

    def _parse_journal_files(self) -> List[Dict]:
        """
        Collects and parses journal entries from text files.

        Extracts date information from filenames or content and returns a list of
        dictionaries, each containing the filename, date, content, and file path
        of a journal entry.
        """
        entries = []

        for file_path in self.journal_dir.glob("*.txt"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Try to extract date from filename or content
                date = extract_date(file_path.name, content)

                entries.append(
                    {
                        "filename": file_path.name,
                        "date": date,
                        "content": content,
                        "file_path": str(file_path),
                    }
                )

            except Exception as e:
                print(f"Error reading {file_path}: {e}")

        return entries

    def build_index(self, force_rebuild: bool = False):
        """Build or rebuild the embedding index"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if force_rebuild:
            cursor.execute("DELETE FROM journal_entries")
            conn.commit()

        # Check if we already have entries
        cursor.execute("SELECT COUNT(*) FROM journal_entries")
        existing_count = cursor.fetchone()[0]

        if existing_count > 0 and not force_rebuild:
            print(
                f"Index already exists with {existing_count} entries. Use force_rebuild=True to rebuild."
            )
            conn.close()
            return

        print("Building embedding index...")
        entries = self._parse_journal_files()

        for entry in entries:
            print(f"Processing {entry['filename']}...")

            # Chunk the content
            chunks = chunk_text(entry["content"])

            for i, chunk in enumerate(chunks):
                # Generate embedding
                embedding = self.embedding_model.encode(chunk)
                embedding_blob = embedding.tobytes()

                # Store in database
                cursor.execute(
                    """
                    INSERT INTO journal_entries (filename, date, content, embedding, chunk_index)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (entry["filename"], entry["date"], chunk, embedding_blob, i),
                )

        conn.commit()
        conn.close()
        print(f"Index built successfully with {len(entries)} journal entries!")

    def _similarity_search(
        self, query: str, top_k: int = 5
    ) -> List[Tuple[str, str, str, float]]:
        """Perform similarity search to find relevant journal chunks"""
        query_embedding = self.embedding_model.encode(query)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT filename, date, content, embedding FROM journal_entries")
        results = []

        for row in cursor.fetchall():
            filename, date, content, embedding_blob = row

            # Convert blob back to numpy array
            stored_embedding = np.frombuffer(embedding_blob, dtype=np.float32)

            # Calculate cosine similarity
            similarity = np.dot(query_embedding, stored_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(stored_embedding)
            )

            results.append((filename, date, content, similarity))

        conn.close()

        # Sort by similarity and return top_k
        results.sort(key=lambda x: x[3], reverse=True)
        return results[:top_k]

    def _query_ollama(self, prompt: str) -> str:
        """Send query to Ollama and get response"""
        payload = {"model": self.ollama_model, "prompt": prompt, "stream": False}

        try:
            response = requests.post(self.ollama_url, json=payload)
            response.raise_for_status()
            return response.json()["response"]
        except requests.exceptions.RequestException as e:
            return f"Error querying Ollama: {e}"

    def query(self, question: str, top_k: int = 5) -> str:
        """Query the journal RAG system"""
        print("Searching for relevant journal entries...")

        # Find relevant journal chunks
        relevant_chunks = self._similarity_search(question, top_k)

        if not relevant_chunks:
            return "No relevant journal entries found."

        # Build context from relevant chunks
        context = "Based on these journal entries:\n\n"
        for i, (filename, date, content, similarity) in enumerate(relevant_chunks):
            context += f"Entry {i + 1} (from {filename}, {date}, similarity: {similarity:.3f}):\n"
            context += f"{content}\n\n"

        # Create prompt for Ollama
        prompt = f"""Context from journal entries:
{context}

Question: {question}

Please answer the question based on the journal entries provided above.
Be specific and reference the relevant diary entries when possible.
If the diary entries don't contain enough information to answer the question, please say so.

Answer:"""

        print("Generating response with Ollama...")
        response = self._query_ollama(prompt)

        return response

    def list_entries(self) -> List[Dict]:
        """List all journal entries in the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT DISTINCT filename, date 
            FROM journal_entries
            ORDER BY date DESC
        """
        )

        entries = [{"filename": row[0], "date": row[1]} for row in cursor.fetchall()]
        conn.close()
        return entries


def main():
    parser = argparse.ArgumentParser(description="Journal RAG System")
    parser.add_argument("journal_dir", help="Directory containing diary files")
    parser.add_argument(
        "--build", action="store_true", help="Build the embedding index"
    )
    parser.add_argument(
        "--rebuild", action="store_true", help="Force rebuild the embedding index"
    )
    parser.add_argument("--query", type=str, help="Query the journal system")
    parser.add_argument("--list", action="store_true", help="List all journal entries")
    parser.add_argument("--model", default="llama2", help="Ollama model to use")
    parser.add_argument(
        "--init-db", action="store_true", help="Initialize database tables"
    )

    args = parser.parse_args()

    if not os.path.exists(args.journal_dir):
        print(f"Error: Directory {args.journal_dir} does not exist")
        return

    # Initialize RAG system
    rag = JournalRAG(args.journal_dir, ollama_model=args.model)

    if args.init_db:
        rag.init_database()
        print("Database initialized successfully")
        return

    if args.build or args.rebuild:
        rag.build_index(force_rebuild=args.rebuild)

    if args.list:
        entries = rag.list_entries()
        print(f"\nFound {len(entries)} journal entries:")
        for entry in entries:
            print(f"  {entry['date']}: {entry['filename']}")

    if args.query:
        response = rag.query(args.query)
        print(f"\nQuestion: {args.query}")
        print(f"\nAnswer:\n{response}")

    # Interactive mode if no specific action
    if not any([args.build, args.rebuild, args.query, args.list]):
        print("Interactive mode - type 'quit' to exit")
        while True:
            query = input("\nEnter your question: ").strip()
            if query.lower() in ["quit", "exit", "q"]:
                break
            if query:
                response = rag.query(query)
                print(f"\nAnswer:\n{response}")


if __name__ == "__main__":
    main()

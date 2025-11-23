import os
import shutil
import uuid
from typing import List
from langchain_community.document_loaders import (
    PyMuPDFLoader, TextLoader, UnstructuredMarkdownLoader, BSHTMLLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from app.core.config import settings
from langchain_openai import OpenAIEmbeddings
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger("ingestion_service")

class IngestionService:
    def __init__(self):
        if not settings.OPENAI_API_KEY:
             raise ValueError("OPENAI_API_KEY is missing in .env config")
             
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=settings.OPENAI_API_KEY
        )
        self.vector_store = Chroma(
            persist_directory=settings.VECTOR_DB_PATH,
            embedding_function=self.embeddings
        )

    def _get_loader(self, file_path: str):
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf": return PyMuPDFLoader(file_path)
        if ext == ".md": return UnstructuredMarkdownLoader(file_path)
        if ext == ".html": return BSHTMLLoader(file_path)
        if ext in [".txt", ".json"]: return TextLoader(file_path, encoding="utf-8")
        raise ValueError(f"Unsupported file type: {ext}")

    def process_documents(self, session_id: str, file_paths: List[str]):
        raw_documents = []
        
        for path in file_paths:
            try:
                loader = self._get_loader(path)
                raw_documents.extend(loader.load())
            except Exception as e:
                logger.error(f"Failed to load {path}: {e}")

        if not raw_documents:
            return {"status": "error", "message": "No valid documents parsed."}

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_documents(raw_documents)

        try:
            vector_store = Chroma(
                collection_name=f"session_{session_id}",
                persist_directory=settings.VECTOR_DB_PATH,
                embedding_function=self.embeddings
            )
            vector_store.add_documents(documents=chunks)
            
            logger.info(f"Session {session_id}: Ingested {len(chunks)} chunks.")
            return {"status": "success", "chunks": len(chunks), "message": "Knowledge Base Built."}
            
        except Exception as e:
            logger.error(f"Vector DB Error: {e}")
            return {"status": "error", "message": str(e)}

    def delete_session_data(self, session_id: str):
        try:
            vector_store = Chroma(
                collection_name=f"session_{session_id}",
                persist_directory=settings.VECTOR_DB_PATH,
                embedding_function=self.embeddings
            )
            vector_store.delete_collection()
            logger.info(f"Cleaned up session {session_id}")
            return True
        except Exception as e:
            logger.warning(f"Cleanup failed for {session_id}: {e}")
            return False
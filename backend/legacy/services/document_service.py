import os
from typing import List, Dict, Optional
from pypdf import PdfReader
from docx import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
import uuid

class DocumentService:
    @staticmethod
    def extract_text_from_pdf(file_path: str) -> str:
        text = ""
        reader = PdfReader(file_path)
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    
    @staticmethod
    def extract_text_from_docx(file_path: str) -> str:
        doc = Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    
    @staticmethod
    def extract_text_from_txt(file_path: str) -> str:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    
    @staticmethod
    def extract_text(file_path: str, file_extension: str) -> Optional[str]:
        try:
            if file_extension.lower() == ".pdf":
                return DocumentService.extract_text_from_pdf(file_path)
            elif file_extension.lower() == ".docx":
                return DocumentService.extract_text_from_docx(file_path)
            elif file_extension.lower() in [".txt", ".md"]:
                return DocumentService.extract_text_from_txt(file_path)
            return None
        except Exception as e:
            print(f"Error extracting text: {e}")
            return None
    
    @staticmethod
    def split_text_into_chunks(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[Dict]:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        chunks = text_splitter.split_text(text)
        return [
            {
                "chunk_id": str(uuid.uuid4()),
                "text": chunk,
                "index": i
            }
            for i, chunk in enumerate(chunks)
        ]

import os
from typing import Optional
import uuid
from fastapi import UploadFile

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class StorageService:
    @staticmethod
    async def save_file(file: UploadFile) -> dict:
        file_id = str(uuid.uuid4())
        original_filename = file.filename
        file_extension = os.path.splitext(original_filename)[1]
        saved_filename = f"{file_id}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, saved_filename)
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
            
        return {
            "file_id": file_id,
            "filename": original_filename,
            "saved_filename": saved_filename,
            "file_path": file_path,
            "file_size": os.path.getsize(file_path),
            "file_type": file_extension
        }
    
    @staticmethod
    def get_file_path(saved_filename: str) -> Optional[str]:
        file_path = os.path.join(UPLOAD_DIR, saved_filename)
        if os.path.exists(file_path):
            return file_path
        return None
    
    @staticmethod
    def delete_file(saved_filename: str) -> bool:
        file_path = os.path.join(UPLOAD_DIR, saved_filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False

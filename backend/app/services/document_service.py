import os
import uuid
from typing import Dict, Any, Tuple
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.models.models import Document, AuditLog, User
from app.processors.pdf_processor import PDFProcessor
from app.processors.docx_processor import DOCXProcessor
from app.processors.txt_processor import TXTProcessor


class DocumentService:
    @staticmethod
    def validate_file(file: UploadFile) -> Tuple[str, str]:
        """
        Validates file extension and filename.
        Returns: (sanitized_filename, extension)
        """
        filename = file.filename or "unknown_file"
        _, ext = os.path.splitext(filename)
        ext = ext.lower()

        if ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format '{ext}'. Allowed formats: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )

        return filename, ext

    @staticmethod
    async def save_and_extract(
        file: UploadFile,
        project_id: int,
        user: User,
        db: Session
    ) -> Document:
        filename, ext = DocumentService.validate_file(file)

        # Generate unique storage filename
        unique_name = f"{uuid.uuid4().hex}_{filename}"
        file_path = os.path.join(settings.UPLOAD_DIR, unique_name)

        # Read contents and enforce file size
        contents = await file.read()
        file_size = len(contents)

        if file_size > settings.MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=400,
                detail=f"File exceeds maximum size of {settings.MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB"
            )

        # Write file to disk
        with open(file_path, "wb") as f:
            f.write(contents)

        # Create Document record
        doc_record = Document(
            project_id=project_id,
            uploaded_by_id=user.id,
            filename=filename,
            file_path=file_path,
            file_type=ext.replace(".", ""),
            file_size=file_size,
            processing_status="PROCESSING"
        )
        db.add(doc_record)
        db.commit()
        db.refresh(doc_record)

        # Process text extraction
        try:
            if ext == ".pdf":
                extracted = PDFProcessor.extract_text(file_path)
            elif ext == ".docx":
                extracted = DOCXProcessor.extract_text(file_path)
            elif ext == ".txt":
                extracted = TXTProcessor.extract_text(file_path)
            else:
                raise ValueError(f"No processor available for {ext}")

            doc_record.raw_text = extracted.get("full_text", "")
            doc_record.page_count = extracted.get("page_count", 1)
            doc_record.processing_status = "PROCESSED"
            db.commit()

            audit = AuditLog(
                project_id=project_id,
                user_id=user.id,
                action="DOCUMENT_PROCESSED",
                entity_type="document",
                entity_id=doc_record.id,
                details=f"Extracted {len(doc_record.raw_text)} characters from {doc_record.filename}"
            )
            db.add(audit)
            db.commit()

        except Exception as e:
            doc_record.processing_status = "FAILED"
            doc_record.error_message = str(e)
            db.commit()
            raise HTTPException(status_code=500, detail=f"Text extraction failed: {str(e)}")

        return doc_record

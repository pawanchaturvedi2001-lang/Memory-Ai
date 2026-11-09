import os
from typing import Dict, Any, List
import docx


class DOCXProcessor:
    @staticmethod
    def extract_text(file_path: str) -> Dict[str, Any]:
        """
        Extracts structured text from a Word document (.docx).
        Includes paragraphs, headings, and table cells.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"DOCX file not found at {file_path}")

        doc = docx.Document(file_path)
        content_lines: List[str] = []

        # Extract paragraphs and headings
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                content_lines.append(text)

        # Extract table contents
        for table in doc.tables:
            for row in table.rows:
                row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if row_cells:
                    content_lines.append(" | ".join(row_cells))

        full_text = "\n\n".join(content_lines)

        # Approximate pages based on line/word count (typical page is ~300 words)
        words = full_text.split()
        estimated_pages = max(1, len(words) // 300)

        pages = [{
            "page_number": 1,
            "text": full_text
        }]

        return {
            "full_text": full_text,
            "pages": pages,
            "page_count": estimated_pages
        }

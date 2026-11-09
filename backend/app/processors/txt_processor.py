import os
from typing import Dict, Any, List


class TXTProcessor:
    @staticmethod
    def extract_text(file_path: str) -> Dict[str, Any]:
        """
        Extracts plain text with robust encoding handling (UTF-8, Latin-1, CP1252).
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Text file not found at {file_path}")

        encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
        content = ""
        for enc in encodings:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    content = f.read()
                break
            except (UnicodeDecodeError, Exception):
                continue

        # Approximate pages based on line/word count (every ~300 words is a page)
        words = content.split()
        estimated_pages = max(1, len(words) // 300)

        pages = [{
            "page_number": 1,
            "text": content
        }]

        return {
            "full_text": content,
            "pages": pages,
            "page_count": estimated_pages
        }

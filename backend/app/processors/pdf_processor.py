from typing import List, Dict, Any
import os


class PDFProcessor:
    @staticmethod
    def extract_text(file_path: str) -> Dict[str, Any]:
        """
        Extracts structured text from a PDF file.
        Returns:
            {
                "full_text": str,
                "pages": [{"page_number": int, "text": str}],
                "page_count": int
            }
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found at {file_path}")

        pages: List[Dict[str, Any]] = []

        # First attempt: PyMuPDF (fitz)
        try:
            import fitz  # pymupdf
            doc = fitz.open(file_path)
            page_count = len(doc)
            for page_num in range(page_count):
                page = doc.load_page(page_num)
                page_text = page.get_text("text").strip()
                pages.append({
                    "page_number": page_num + 1,
                    "text": page_text
                })
            doc.close()
        except (ImportError, Exception):
            # Second attempt: pypdfium2
            import pypdfium2 as pdfium
            pdf = pdfium.PdfDocument(file_path)
            page_count = len(pdf)
            for page_num in range(page_count):
                page = pdf[page_num]
                textpage = page.get_textpage()
                page_text = textpage.get_text_range().strip()
                pages.append({
                    "page_number": page_num + 1,
                    "text": page_text
                })
                textpage.close()
                page.close()
            pdf.close()

        full_text = "\n\n--- Page Break ---\n\n".join(
            [f"[Page {p['page_number']}]\n{p['text']}" for p in pages if p['text']]
        )

        return {
            "full_text": full_text,
            "pages": pages,
            "page_count": len(pages)
        }

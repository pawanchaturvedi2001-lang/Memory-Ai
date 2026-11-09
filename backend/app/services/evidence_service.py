import re
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.models import Document, Evidence, KnowledgeItem, KnowledgeStatus


class EvidenceService:
    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalizes whitespace and lowercase for comparison."""
        if not text:
            return ""
        return " ".join(text.lower().split())

    @classmethod
    def verify_excerpt_in_document(
        cls,
        excerpt: str,
        document_text: str
    ) -> Tuple[bool, float, Optional[str]]:
        """
        Validates whether a supporting text excerpt actually exists in the source text.
        Returns: (is_verified, match_confidence, verification_note)
        """
        if not excerpt or not document_text:
            return False, 0.0, "Missing excerpt or document content"

        clean_excerpt = excerpt.strip()
        clean_doc = document_text.strip()

        # 1. Exact string match
        if clean_excerpt in clean_doc:
            return True, 1.0, "Exact match verified in source document"

        # 2. Normalized whitespace match
        norm_excerpt = cls.normalize_text(clean_excerpt)
        norm_doc = cls.normalize_text(clean_doc)

        if norm_excerpt in norm_doc:
            return True, 0.98, "Verified via normalized whitespace match"

        # 3. Fuzzy partial substring matching
        # Look for the majority of the excerpt's words in sequence
        words = norm_excerpt.split()
        if len(words) >= 5:
            # Check 5-gram windows
            matches = 0
            total_windows = max(1, len(words) - 4)
            for i in range(total_windows):
                window = " ".join(words[i:i+5])
                if window in norm_doc:
                    matches += 1
            ratio = matches / total_windows
            if ratio >= 0.75:
                return True, round(0.80 + (ratio * 0.15), 2), f"Verified with {int(ratio*100)}% partial text match"
            elif ratio >= 0.40:
                return False, round(ratio * 0.7, 2), f"Weak correlation ({int(ratio*100)}% phrase match); needs human review"

        return False, 0.0, "Excerpt text could NOT be located in the source document"

    @classmethod
    def locate_page_number(
        cls,
        excerpt: str,
        document_text: str
    ) -> int:
        """
        Finds the page number where the excerpt appears based on [Page X] tags.
        """
        if not excerpt or not document_text:
            return 1

        norm_excerpt = cls.normalize_text(excerpt[:60])
        pages = re.split(r'\[Page\s+(\d+)\]', document_text)

        # pages alternating: [pre-text, page_num1, page_text1, page_num2, page_text2...]
        if len(pages) > 1:
            for i in range(1, len(pages), 2):
                page_num = int(pages[i])
                page_content = pages[i+1] if i+1 < len(pages) else ""
                if norm_excerpt in cls.normalize_text(page_content):
                    return page_num

        return 1

    @classmethod
    def create_evidence_record(
        cls,
        db: Session,
        knowledge_item_id: int,
        document: Document,
        exact_quote: str,
        page_number: Optional[int] = None,
        source_location: Optional[str] = None
    ) -> Evidence:
        """
        Creates and validates an Evidence record linked to a KnowledgeItem and Document.
        """
        is_verified, confidence, note = cls.verify_excerpt_in_document(
            exact_quote,
            document.raw_text or ""
        )

        detected_page = page_number or cls.locate_page_number(exact_quote, document.raw_text or "")

        evidence = Evidence(
            knowledge_item_id=knowledge_item_id,
            document_id=document.id,
            page_number=detected_page,
            source_location=source_location or f"Page {detected_page}",
            exact_quote=exact_quote,
            match_confidence=confidence,
            is_verified=is_verified,
            verification_notes=note
        )
        db.add(evidence)
        db.commit()
        db.refresh(evidence)
        return evidence

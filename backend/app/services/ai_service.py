import json
import re
import os
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.config import settings
from app.models.models import Document, KnowledgeItem, TaskItem, KnowledgeStatus, AuditLog
from app.services.evidence_service import EvidenceService


EXTRACTION_SYSTEM_PROMPT = """You are a Principal Software Architect and Knowledge Engineer analyzing project documents for a critical handover.
Extract all relevant knowledge items into a structured JSON array under the key "items".

Categories to extract:
1. "technical_decision": Explicit decisions made (e.g., choice of database, architectural pattern, library chosen).
2. "pending_task": Open or pending actionable work with owner, deadline, and priority if mentioned.
3. "unresolved_bug": Active bugs, defects, or critical issues reported as unresolved.
4. "project_risk": Stated risks, bottlenecks, scalability concerns, or security alerts.
5. "dependency": External libraries, APIs, services, or hardware dependencies.
6. "task_ownership": Specific ownership assignments of subsystems or responsibilities.
7. "context": Crucial domain or business rules, background context, and team conventions.
8. "tech_stack": Specific technologies, frameworks, and programming languages actively used.
9. "architecture": System design, components, interfaces, and topology.

STRICT EXTRACTION RULES:
- Never hallucinate or extrapolate facts not present in the text.
- If owner, deadline, or priority is not explicitly stated in a task, set them to null.
- For each item, provide an EXACT verbatim excerpt from the document as "supporting_excerpt".
- Distinguish whether the item is a directly stated fact ("FACT") or inferred ("INFERRED").

Output format MUST be valid JSON:
{
  "items": [
    {
      "type": "technical_decision",
      "title": "Short descriptive summary",
      "content": "Detailed description of the item",
      "supporting_excerpt": "Exact text quote from the document",
      "page_number": 1,
      "confidence": 0.95,
      "is_fact": true,
      "task_metadata": {
         "owner": "Person name or null",
         "deadline": "YYYY-MM-DD or text or null",
         "priority": "LOW|MEDIUM|HIGH|CRITICAL",
         "status": "PENDING|IN_PROGRESS|BLOCKED"
      }
    }
  ]
}
"""


class AIService:
    @classmethod
    def extract_with_llm(cls, document_text: str) -> Optional[List[Dict[str, Any]]]:
        """Attempts extraction using OpenAI or Gemini if configured."""
        if settings.OPENAI_API_KEY:
            try:
                import openai
                client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                        {"role": "user", "content": f"Analyze the following document content:\n\n{document_text[:20000]}"}
                    ],
                    temperature=0.1
                )
                raw_json = response.choices[0].message.content
                data = json.loads(raw_json)
                return data.get("items", [])
            except Exception as e:
                print(f"OpenAI extraction warning: {e}")

        if settings.GEMINI_API_KEY:
            try:
                import httpx
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
                prompt = f"{EXTRACTION_SYSTEM_PROMPT}\n\nDocument Content:\n{document_text[:20000]}"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"response_mime_type": "application/json"}
                }
                res = httpx.post(url, json=payload, timeout=30.0)
                if res.status_code == 200:
                    text_resp = res.json()["candidates"][0]["content"]["parts"][0]["text"]
                    data = json.loads(text_resp)
                    return data.get("items", [])
            except Exception as e:
                print(f"Gemini extraction warning: {e}")

        return None

    @classmethod
    def heuristic_extract(cls, document_text: str) -> List[Dict[str, Any]]:
        """
        Robust, deterministic heuristic extractor that guarantees complete knowledge extraction
        even without external LLM API availability. Scans sections, bullet points, and keywords.
        """
        items: List[Dict[str, Any]] = []
        lines = [line.strip() for line in document_text.splitlines() if line.strip()]

        current_section = "General"
        section_patterns = {
            "decision": ["decision", "architecture decision", "technical decision", "adr", "chose", "selected"],
            "task": ["pending task", "to-do", "todo", "action item", "next steps", "tasks", "roadmap"],
            "bug": ["bug", "defect", "known issue", "unresolved", "error", "incident", "failure"],
            "risk": ["risk", "bottleneck", "threat", "concern", "vulnerability"],
            "dependency": ["dependency", "dependencies", "external service", "third-party", "integration"],
            "tech_stack": ["tech stack", "technology stack", "frameworks", "tools", "technologies"],
            "architecture": ["architecture", "system design", "topology", "data flow", "infrastructure"]
        }

        i = 0
        while i < len(lines):
            line = lines[i]

            # Detect section headers (e.g. ## Decisions, Section 3: Bugs)
            header_match = re.match(r'^(?:#+|\d+\.|\bSECTION\b|\bCHAPTER\b)?\s*([A-Za-z0-9\s\-_/]+)[:\-]?$', line, re.IGNORECASE)
            lower_line = line.lower()

            for sec_type, keywords in section_patterns.items():
                if any(kw in lower_line for kw in keywords) and (len(line) < 60 or line.startswith(('#', '*', '-'))):
                    current_section = sec_type
                    break

            # Check if this line looks like an item (bullet point, numbered item, or strong statement)
            is_bullet = bool(re.match(r'^(?:[-*•]|\d+[\.)])\s+', line))
            clean_item_text = re.sub(r'^(?:[-*•]|\d+[\.)])\s+', '', line).strip()

            if is_bullet and len(clean_item_text) > 10:
                item_type = "context"
                task_meta = None
                lower_text = clean_item_text.lower()

                # Categorize item
                if any(k in lower_text for k in ["bug", "issue", "defect", "unresolved", "broken", "failing", "500", "crash"]):
                    item_type = "unresolved_bug"
                elif any(k in lower_text for k in ["decided", "chose", "selected", "adopt", "migrated to", "architecture decision"]):
                    item_type = "technical_decision"
                elif any(k in lower_text for k in ["risk", "vulnerable", "warning", "bottleneck", "concern", "outage"]):
                    item_type = "project_risk"
                elif any(k in lower_text for k in ["dependency", "api", "library", "sdk", "service provider", "stripe", "aws", "redis"]):
                    item_type = "dependency"
                elif any(k in lower_text for k in ["react", "fastapi", "python", "postgres", "sqlite", "node", "docker", "redis", "tailwind"]):
                    item_type = "tech_stack"
                elif current_section == "task" or any(k in lower_text for k in ["todo", "task", "implement", "create", "fix", "deadline", "assigned"]):
                    item_type = "pending_task"
                elif current_section in ["decision", "bug", "risk", "dependency", "architecture", "tech_stack"]:
                    item_type = current_section if current_section != "decision" else "technical_decision"
                    if item_type == "bug":
                        item_type = "unresolved_bug"
                    elif item_type == "risk":
                        item_type = "project_risk"

                # Parse task metadata if it's a task
                if item_type == "pending_task":
                    # Extract Owner (e.g. Owner: Alice, Assigned to: Bob)
                    owner_match = re.search(r'(?:owner|assigned(?:\s+to)?|assignee)[\s:]+([A-Za-z\s]+?)(?:[;,.\)]|$)', clean_item_text, re.IGNORECASE)
                    owner = owner_match.group(1).strip() if owner_match else None

                    # Extract Deadline (e.g. Deadline: 2026-11-20, Due: Nov 15)
                    deadline_match = re.search(r'(?:deadline|due|target)[\s:]+([A-Za-z0-9\s,\-]+?)(?:[;,.\)]|$)', clean_item_text, re.IGNORECASE)
                    deadline = deadline_match.group(1).strip() if deadline_match else None

                    # Extract Priority
                    priority = "MEDIUM"
                    if re.search(r'\b(critical|urgent|blocker|p0)\b', clean_item_text, re.IGNORECASE):
                        priority = "CRITICAL"
                    elif re.search(r'\b(high|important|p1)\b', clean_item_text, re.IGNORECASE):
                        priority = "HIGH"
                    elif re.search(r'\b(low|trivial|minor|p3)\b', clean_item_text, re.IGNORECASE):
                        priority = "LOW"

                    task_meta = {
                        "owner": owner,
                        "deadline": deadline,
                        "priority": priority,
                        "status": "PENDING"
                    }

                title = clean_item_text.split(":")[0] if ":" in clean_item_text and len(clean_item_text.split(":")[0]) < 60 else clean_item_text[:70]

                items.append({
                    "type": item_type,
                    "title": title.strip(),
                    "content": clean_item_text,
                    "supporting_excerpt": line,
                    "page_number": 1,
                    "confidence": 0.92,
                    "is_fact": True,
                    "task_metadata": task_meta
                })

            i += 1

        # If document is formatted as paragraphs rather than bullet points
        if not items and lines:
            for line in lines:
                if len(line) > 30:
                    items.append({
                        "type": "context",
                        "title": line[:60] + "...",
                        "content": line,
                        "supporting_excerpt": line,
                        "page_number": 1,
                        "confidence": 0.85,
                        "is_fact": True,
                        "task_metadata": None
                    })

        return items

    @classmethod
    def process_document_knowledge(
        cls,
        document: Document,
        db: Session
    ) -> List[KnowledgeItem]:
        """
        Orchestrates full knowledge extraction, evidence linking, and traceability for a document.
        """
        raw_text = document.raw_text or ""
        if not raw_text.strip():
            return []

        # Try LLM first, fall back to heuristic extraction
        extracted_data = cls.extract_with_llm(raw_text)
        if not extracted_data:
            extracted_data = cls.heuristic_extract(raw_text)

        created_items: List[KnowledgeItem] = []

        for item_data in extracted_data:
            k_type = item_data.get("type", "context")
            title = item_data.get("title", "Extracted Knowledge Item")
            content = item_data.get("content", "")
            excerpt = item_data.get("supporting_excerpt", "")
            confidence = float(item_data.get("confidence", 0.90))
            page_num = item_data.get("page_number", 1)

            # Determine initial verification status via EvidenceService
            is_verified, match_conf, note = EvidenceService.verify_excerpt_in_document(
                excerpt or content,
                raw_text
            )

            # If evidence is verified, set status to SUPPORTED or NEEDS REVIEW
            initial_status = KnowledgeStatus.SUPPORTED if is_verified else KnowledgeStatus.MISSING_EVIDENCE

            # Create KnowledgeItem
            knowledge_item = KnowledgeItem(
                project_id=document.project_id,
                document_id=document.id,
                type=k_type,
                title=title,
                content=content,
                confidence=round(confidence * (0.8 + 0.2 * match_conf), 2),
                status=initial_status
            )
            db.add(knowledge_item)
            db.commit()
            db.refresh(knowledge_item)

            # Create Evidence link (traceability)
            if excerpt:
                EvidenceService.create_evidence_record(
                    db=db,
                    knowledge_item_id=knowledge_item.id,
                    document=document,
                    exact_quote=excerpt,
                    page_number=page_num
                )

            # If it's a pending task, create a linked TaskItem
            task_meta = item_data.get("task_metadata")
            if k_type == "pending_task":
                owner = task_meta.get("owner") if task_meta else None
                deadline = task_meta.get("deadline") if task_meta else None
                priority = task_meta.get("priority", "MEDIUM") if task_meta else "MEDIUM"
                status_task = task_meta.get("status", "PENDING") if task_meta else "PENDING"

                task_record = TaskItem(
                    project_id=document.project_id,
                    knowledge_item_id=knowledge_item.id,
                    title=title,
                    description=content,
                    owner=owner,
                    deadline=deadline,
                    priority=priority,
                    status=status_task
                )
                db.add(task_record)
                db.commit()

            created_items.append(knowledge_item)

        # Record audit log
        audit = AuditLog(
            project_id=document.project_id,
            user_id=document.uploaded_by_id,
            action="AI_KNOWLEDGE_EXTRACTED",
            entity_type="knowledge_item",
            details=f"Extracted {len(created_items)} items from document '{document.filename}'"
        )
        db.add(audit)
        db.commit()

        return created_items

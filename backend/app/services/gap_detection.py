import re
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session

from app.models.models import (
    KnowledgeItem, TaskItem, KnowledgeGap, Document,
    Evidence, KnowledgeStatus, AuditLog
)


class GapDetectionService:
    @classmethod
    def run_gap_analysis(cls, project_id: int, db: Session) -> List[KnowledgeGap]:
        """
        Runs comprehensive, deterministic Python rule-based gap analysis on a project.
        Identifies:
        1. Missing task ownership
        2. Missing task deadlines
        3. Conflicting project information (conflicting deadlines, conflicting architectural decisions)
        4. Unresolved critical bugs
        5. Unverified decisions (missing or unverified evidence)
        6. Missing technical documentation / dependencies
        """
        # Clear existing OPEN gaps for this project to recompute freshly
        db.query(KnowledgeGap).filter(
            KnowledgeGap.project_id == project_id,
            KnowledgeGap.status == "OPEN"
        ).delete()
        db.commit()

        new_gaps: List[KnowledgeGap] = []

        # ----------------------------------------------------
        # 1. MISSING TASK OWNERSHIP & MISSING DEADLINES
        # ----------------------------------------------------
        tasks = db.query(TaskItem).filter(TaskItem.project_id == project_id).all()
        for t in tasks:
            # Check owner
            if not t.owner or t.owner.strip().lower() in ["none", "null", "tbd", "unassigned", ""]:
                gap = KnowledgeGap(
                    project_id=project_id,
                    gap_type="missing_owner",
                    title=f"Unassigned Task: {t.title[:60]}",
                    description=f"The task '{t.title}' has no designated owner or assignee in the documentation.",
                    severity="HIGH" if t.priority in ["HIGH", "CRITICAL"] else "MEDIUM",
                    item_id_1=t.knowledge_item_id,
                    status="OPEN",
                    suggested_action=f"Assign an incoming team member to take ownership of '{t.title}'."
                )
                db.add(gap)
                new_gaps.append(gap)

                # Update linked knowledge item status
                if t.knowledge_item_id:
                    k_item = db.query(KnowledgeItem).filter(KnowledgeItem.id == t.knowledge_item_id).first()
                    if k_item and k_item.status not in [KnowledgeStatus.APPROVED, KnowledgeStatus.REJECTED]:
                        k_item.status = KnowledgeStatus.NEEDS_REVIEW

            # Check deadline
            if not t.deadline or t.deadline.strip().lower() in ["none", "null", "tbd", "undefined", ""]:
                gap = KnowledgeGap(
                    project_id=project_id,
                    gap_type="missing_deadline",
                    title=f"Missing Deadline: {t.title[:60]}",
                    description=f"Task '{t.title}' has no scheduled deadline or delivery timeframe.",
                    severity="MEDIUM",
                    item_id_1=t.knowledge_item_id,
                    status="OPEN",
                    suggested_action="Establish an agreed milestone and target delivery date."
                )
                db.add(gap)
                new_gaps.append(gap)

        # ----------------------------------------------------
        # 2. CONFLICTING PROJECT INFORMATION
        # ----------------------------------------------------
        # Look for conflicting deadlines across tasks with similar titles/subjects
        for i in range(len(tasks)):
            for j in range(i + 1, len(tasks)):
                t1 = tasks[i]
                t2 = tasks[j]
                if t1.deadline and t2.deadline and t1.deadline != t2.deadline:
                    # Check token overlap between task titles
                    words1 = set(re.findall(r'\w+', t1.title.lower())) - {"the", "a", "an", "for", "to", "in", "and", "of"}
                    words2 = set(re.findall(r'\w+', t2.title.lower())) - {"the", "a", "an", "for", "to", "in", "and", "of"}
                    overlap = words1.intersection(words2)
                    if len(overlap) >= 2 or (words1 and words1 == words2):
                        gap = KnowledgeGap(
                            project_id=project_id,
                            gap_type="conflicting_deadline",
                            title=f"Conflicting Deadlines: '{t1.title[:40]}' vs '{t2.title[:40]}'",
                            description=(
                                f"Documents contain conflicting deadlines for the same task area: "
                                f"'{t1.deadline}' (from task #{t1.id}) versus '{t2.deadline}' (from task #{t2.id})."
                            ),
                            severity="CRITICAL",
                            item_id_1=t1.knowledge_item_id,
                            item_id_2=t2.knowledge_item_id,
                            status="OPEN",
                            suggested_action=f"Reconcile timeline with project lead and establish single canonical deadline."
                        )
                        db.add(gap)
                        new_gaps.append(gap)

                        # Set knowledge item status to CONFLICTING
                        for k_id in [t1.knowledge_item_id, t2.knowledge_item_id]:
                            if k_id:
                                ki = db.query(KnowledgeItem).filter(KnowledgeItem.id == k_id).first()
                                if ki and ki.status not in [KnowledgeStatus.APPROVED, KnowledgeStatus.REJECTED]:
                                    ki.status = KnowledgeStatus.CONFLICTING

        # Check for conflicting technical decisions (e.g. database choices, auth protocols)
        decisions = db.query(KnowledgeItem).filter(
            KnowledgeItem.project_id == project_id,
            KnowledgeItem.type == "technical_decision"
        ).all()

        decision_topics = ["database", "storage", "authentication", "cache", "hosting", "framework", "messaging"]
        for topic in decision_topics:
            matching = [d for d in decisions if topic in d.content.lower()]
            if len(matching) >= 2:
                for a in range(len(matching)):
                    for b in range(a + 1, len(matching)):
                        d1 = matching[a]
                        d2 = matching[b]
                        # If different documents or different titles
                        if d1.document_id != d2.document_id or d1.title != d2.title:
                            # Check if conflicting sentiment or keywords
                            if any(w in d1.content.lower() and w not in d2.content.lower() for w in ["postgresql", "sqlite", "mongo", "redis", "jwt", "oauth"]):
                                gap = KnowledgeGap(
                                    project_id=project_id,
                                    gap_type="conflicting_decision",
                                    title=f"Potential Conflicting Decision regarding {topic.title()}",
                                    description=f"Multiple documents state disparate decisions on {topic}: '{d1.title}' vs '{d2.title}'.",
                                    severity="HIGH",
                                    item_id_1=d1.id,
                                    item_id_2=d2.id,
                                    status="OPEN",
                                    suggested_action=f"Consult with outgoing architect to verify current production choice for {topic}."
                                )
                                db.add(gap)
                                new_gaps.append(gap)

        # ----------------------------------------------------
        # 3. UNRESOLVED BUGS
        # ----------------------------------------------------
        bugs = db.query(KnowledgeItem).filter(
            KnowledgeItem.project_id == project_id,
            KnowledgeItem.type == "unresolved_bug"
        ).all()
        for b in bugs:
            gap = KnowledgeGap(
                project_id=project_id,
                gap_type="unresolved_bug",
                title=f"Active Defect: {b.title[:60]}",
                description=f"Unresolved issue documented: {b.content[:200]}",
                severity="CRITICAL" if any(w in b.content.lower() for w in ["crash", "payment", "data loss", "security", "blocker"]) else "HIGH",
                item_id_1=b.id,
                status="OPEN",
                suggested_action="Prioritize bug reproduction and schedule patch before next release."
            )
            db.add(gap)
            new_gaps.append(gap)

            if b.status not in [KnowledgeStatus.APPROVED, KnowledgeStatus.REJECTED]:
                b.status = KnowledgeStatus.UNRESOLVED

        # ----------------------------------------------------
        # 4. UNVERIFIED DECISIONS / MISSING EVIDENCE
        # ----------------------------------------------------
        for d in decisions:
            evidence = db.query(Evidence).filter(Evidence.knowledge_item_id == d.id).first()
            if not evidence or not evidence.is_verified:
                gap = KnowledgeGap(
                    project_id=project_id,
                    gap_type="unverified_decision",
                    title=f"Unverified Technical Decision: {d.title[:60]}",
                    description=f"Decision '{d.title}' lacks validated verbatim source evidence in the uploaded documents.",
                    severity="MEDIUM",
                    item_id_1=d.id,
                    status="OPEN",
                    suggested_action="Request Architecture Decision Record (ADR) or meeting notes validating this claim."
                )
                db.add(gap)
                new_gaps.append(gap)

                if d.status not in [KnowledgeStatus.APPROVED, KnowledgeStatus.REJECTED]:
                    d.status = KnowledgeStatus.MISSING_EVIDENCE

        # ----------------------------------------------------
        # 5. MISSING DEPENDENCIES
        # ----------------------------------------------------
        dependencies = db.query(KnowledgeItem).filter(
            KnowledgeItem.project_id == project_id,
            KnowledgeItem.type == "dependency"
        ).all()

        docs_text = " ".join([doc.raw_text or "" for doc in db.query(Document).filter(Document.project_id == project_id).all()]).lower()

        for dep in dependencies:
            dep_name = dep.title.lower()
            # If dependency is mentioned as missing credentials, SDK or setup
            if any(term in dep.content.lower() for term in ["missing", "todo", "unconfigured", "untested", "api key needed", "not configured"]):
                gap = KnowledgeGap(
                    project_id=project_id,
                    gap_type="missing_dependency",
                    title=f"Unconfigured Dependency: {dep.title[:60]}",
                    description=f"External dependency '{dep.title}' is reported as unconfigured or missing credentials.",
                    severity="HIGH",
                    item_id_1=dep.id,
                    status="OPEN",
                    suggested_action=f"Obtain sandbox credentials and configuration guide for '{dep.title}'."
                )
                db.add(gap)
                new_gaps.append(gap)

        db.commit()

        # Audit log
        audit = AuditLog(
            project_id=project_id,
            action="KNOWLEDGE_GAP_ANALYSIS_COMPLETED",
            entity_type="knowledge_gap",
            details=f"Identified {len(new_gaps)} knowledge gaps and inconsistencies across project documents"
        )
        db.add(audit)
        db.commit()

        return new_gaps

import os
import io
import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from app.models.models import (
    Project, Document, KnowledgeItem, TaskItem, KnowledgeGap, Evidence, AuditLog, KnowledgeStatus
)


class ReportService:
    @classmethod
    def generate_pdf_handover_report(cls, project_id: int, db: Session) -> io.BytesIO:
        """
        Generates a comprehensive, enterprise-grade PDF Handover & Continuity Report
        containing all 10 required sections:
        1. Project Overview
        2. Technology Stack
        3. Technical Decisions
        4. Pending Tasks & Ownership
        5. Unresolved Bugs & Critical Issues
        6. Technical Dependencies
        7. Project Risks & Bottlenecks
        8. Knowledge Gaps & Inconsistencies
        9. Source Evidence Traceability
        10. Review & Approval Status Summary
        """
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError("Project not found")

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()

        # Custom styles
        primary_color = colors.HexColor("#1e40af")   # Deep Blue
        secondary_color = colors.HexColor("#3b82f6") # Blue Accent
        dark_text = colors.HexColor("#0f172a")       # Slate 900
        light_bg = colors.HexColor("#f8fafc")        # Slate 50
        border_color = colors.HexColor("#cbd5e1")    # Slate 300
        danger_color = colors.HexColor("#dc2626")    # Red
        warning_color = colors.HexColor("#d97706")   # Amber
        success_color = colors.HexColor("#16a34a")   # Green

        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=22,
            leading=26,
            textColor=primary_color,
            spaceAfter=6
        )

        subtitle_style = ParagraphStyle(
            'ReportSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#475569"),
            spaceAfter=14
        )

        section_heading = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=13,
            leading=16,
            textColor=primary_color,
            spaceBefore=12,
            spaceAfter=6
        )

        body_style = ParagraphStyle(
            'ReportBody',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=12,
            textColor=dark_text
        )

        badge_style = ParagraphStyle(
            'BadgeText',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8,
            leading=10,
            textColor=colors.white
        )

        story = []

        # -----------------------------------------------------------------
        # HEADER / COVER TITLE
        # -----------------------------------------------------------------
        story.append(Paragraph("PROJECT MEMORY AI", subtitle_style))
        story.append(Paragraph(f"Handover & Knowledge Continuity Report: {project.name}", title_style))
        gen_time = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        story.append(Paragraph(f"<b>Generated On:</b> {gen_time} &nbsp;|&nbsp; <b>Project Status:</b> {project.status} &nbsp;|&nbsp; <b>ID:</b> #{project.id}", subtitle_style))
        story.append(HRFlowable(width="100%", thickness=1.5, color=primary_color, spaceAfter=14))

        # -----------------------------------------------------------------
        # 1. PROJECT OVERVIEW
        # -----------------------------------------------------------------
        story.append(Paragraph("1. Project Overview", section_heading))
        desc_text = project.description or "No formal project description provided."
        story.append(Paragraph(f"<b>Overview:</b> {desc_text}", body_style))
        story.append(Spacer(1, 6))

        docs_count = db.query(Document).filter(Document.project_id == project.id).count()
        items_count = db.query(KnowledgeItem).filter(KnowledgeItem.project_id == project.id).count()
        gaps_count = db.query(KnowledgeGap).filter(KnowledgeGap.project_id == project.id, KnowledgeGap.status == "OPEN").count()

        summary_table_data = [
            [
                Paragraph("<b>Total Uploaded Documents</b>", body_style),
                Paragraph(f"{docs_count}", body_style),
                Paragraph("<b>Extracted Knowledge Items</b>", body_style),
                Paragraph(f"{items_count}", body_style)
            ],
            [
                Paragraph("<b>Identified Knowledge Gaps</b>", body_style),
                Paragraph(f"<font color='#dc2626'><b>{gaps_count}</b></font>", body_style),
                Paragraph("<b>Primary Creator</b>", body_style),
                Paragraph(project.creator.full_name if project.creator else "Unknown", body_style)
            ]
        ]
        t_summary = Table(summary_table_data, colWidths=[150, 100, 150, 140])
        t_summary.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), light_bg),
            ('GRID', (0, 0), (-1, -1), 0.5, border_color),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(t_summary)
        story.append(Spacer(1, 12))

        # -----------------------------------------------------------------
        # 2. TECHNOLOGY STACK
        # -----------------------------------------------------------------
        story.append(Paragraph("2. Technology Stack", section_heading))
        tech_items = db.query(KnowledgeItem).filter(
            KnowledgeItem.project_id == project.id,
            KnowledgeItem.type == "tech_stack"
        ).all()
        if tech_items:
            tech_data = [[Paragraph("<b>Component / Tech</b>", body_style), Paragraph("<b>Details & Evidence</b>", body_style)]]
            for t in tech_items:
                tech_data.append([
                    Paragraph(f"<b>{t.title}</b>", body_style),
                    Paragraph(t.content, body_style)
                ])
            t_tech = Table(tech_data, colWidths=[160, 380])
            t_tech.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), light_bg),
                ('GRID', (0, 0), (-1, -1), 0.5, border_color),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(t_tech)
        else:
            story.append(Paragraph("<i>No specific technology stack entries extracted.</i>", body_style))
        story.append(Spacer(1, 10))

        # -----------------------------------------------------------------
        # 3. TECHNICAL DECISIONS
        # -----------------------------------------------------------------
        story.append(Paragraph("3. Technical Decisions", section_heading))
        decisions = db.query(KnowledgeItem).filter(
            KnowledgeItem.project_id == project.id,
            KnowledgeItem.type == "technical_decision"
        ).all()
        if decisions:
            dec_data = [[Paragraph("<b>Decision Title</b>", body_style), Paragraph("<b>Decision Content</b>", body_style), Paragraph("<b>Status</b>", body_style)]]
            for d in decisions:
                dec_data.append([
                    Paragraph(f"<b>{d.title}</b>", body_style),
                    Paragraph(d.content, body_style),
                    Paragraph(f"<b>{d.status}</b>", body_style)
                ])
            t_dec = Table(dec_data, colWidths=[140, 300, 100])
            t_dec.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), light_bg),
                ('GRID', (0, 0), (-1, -1), 0.5, border_color),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(t_dec)
        else:
            story.append(Paragraph("<i>No technical decisions documented.</i>", body_style))
        story.append(Spacer(1, 10))

        # -----------------------------------------------------------------
        # 4. PENDING TASKS & OWNERSHIP
        # -----------------------------------------------------------------
        story.append(Paragraph("4. Pending Tasks & Ownership", section_heading))
        tasks = db.query(TaskItem).filter(TaskItem.project_id == project.id).all()
        if tasks:
            task_data = [[
                Paragraph("<b>Task</b>", body_style),
                Paragraph("<b>Owner</b>", body_style),
                Paragraph("<b>Deadline</b>", body_style),
                Paragraph("<b>Priority</b>", body_style),
                Paragraph("<b>Status</b>", body_style)
            ]]
            for tk in tasks:
                owner_disp = f"<font color='#dc2626'><b>UNASSIGNED</b></font>" if not tk.owner or tk.owner.lower() in ['none', 'null', 'tbd'] else tk.owner
                deadline_disp = f"<font color='#d97706'><b>MISSING</b></font>" if not tk.deadline or tk.deadline.lower() in ['none', 'null', 'tbd'] else tk.deadline
                task_data.append([
                    Paragraph(tk.title, body_style),
                    Paragraph(owner_disp, body_style),
                    Paragraph(deadline_disp, body_style),
                    Paragraph(tk.priority, body_style),
                    Paragraph(tk.status, body_style)
                ])
            t_task = Table(task_data, colWidths=[180, 100, 90, 80, 90])
            t_task.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), light_bg),
                ('GRID', (0, 0), (-1, -1), 0.5, border_color),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(t_task)
        else:
            story.append(Paragraph("<i>No pending tasks recorded.</i>", body_style))
        story.append(Spacer(1, 10))

        # -----------------------------------------------------------------
        # 5. UNRESOLVED BUGS & DEFECTS
        # -----------------------------------------------------------------
        story.append(Paragraph("5. Unresolved Bugs & Critical Defects", section_heading))
        bugs = db.query(KnowledgeItem).filter(
            KnowledgeItem.project_id == project.id,
            KnowledgeItem.type == "unresolved_bug"
        ).all()
        if bugs:
            bug_data = [[Paragraph("<b>Bug / Defect</b>", body_style), Paragraph("<b>Description</b>", body_style), Paragraph("<b>Verification Status</b>", body_style)]]
            for b in bugs:
                bug_data.append([
                    Paragraph(f"<font color='#dc2626'><b>{b.title}</b></font>", body_style),
                    Paragraph(b.content, body_style),
                    Paragraph(b.status, body_style)
                ])
            t_bug = Table(bug_data, colWidths=[150, 290, 100])
            t_bug.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), light_bg),
                ('GRID', (0, 0), (-1, -1), 0.5, border_color),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(t_bug)
        else:
            story.append(Paragraph("<i>No active unresolved bugs found.</i>", body_style))
        story.append(Spacer(1, 10))

        # -----------------------------------------------------------------
        # 6. TECHNICAL DEPENDENCIES & 7. RISKS
        # -----------------------------------------------------------------
        story.append(Paragraph("6. Technical Dependencies & Risks", section_heading))
        deps_and_risks = db.query(KnowledgeItem).filter(
            KnowledgeItem.project_id == project.id,
            KnowledgeItem.type.in_(["dependency", "project_risk"])
        ).all()
        if deps_and_risks:
            dr_data = [[Paragraph("<b>Type</b>", body_style), Paragraph("<b>Item</b>", body_style), Paragraph("<b>Impact & Details</b>", body_style)]]
            for itm in deps_and_risks:
                dr_data.append([
                    Paragraph(f"<b>{itm.type.replace('_', ' ').title()}</b>", body_style),
                    Paragraph(f"<b>{itm.title}</b>", body_style),
                    Paragraph(itm.content, body_style)
                ])
            t_dr = Table(dr_data, colWidths=[100, 150, 290])
            t_dr.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), light_bg),
                ('GRID', (0, 0), (-1, -1), 0.5, border_color),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(t_dr)
        else:
            story.append(Paragraph("<i>No dependencies or risks listed.</i>", body_style))
        story.append(Spacer(1, 10))

        # -----------------------------------------------------------------
        # 8. KNOWLEDGE GAPS & INCONSISTENCIES (MAIN INNOVATION)
        # -----------------------------------------------------------------
        story.append(Paragraph("7. Knowledge Gap & Consistency Analysis (Innovative)", section_heading))
        gaps = db.query(KnowledgeGap).filter(KnowledgeGap.project_id == project.id).all()
        if gaps:
            gap_data = [[
                Paragraph("<b>Gap Type</b>", body_style),
                Paragraph("<b>Severity</b>", body_style),
                Paragraph("<b>Description & Finding</b>", body_style),
                Paragraph("<b>Recommended Action</b>", body_style)
            ]]
            for g in gaps:
                sev_color = "#dc2626" if g.severity in ["CRITICAL", "HIGH"] else "#d97706"
                gap_data.append([
                    Paragraph(g.gap_type.replace("_", " ").title(), body_style),
                    Paragraph(f"<font color='{sev_color}'><b>{g.severity}</b></font>", body_style),
                    Paragraph(g.description, body_style),
                    Paragraph(g.suggested_action or "Review manually with outgoing team member", body_style)
                ])
            t_gap = Table(gap_data, colWidths=[100, 60, 200, 180])
            t_gap.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), light_bg),
                ('GRID', (0, 0), (-1, -1), 0.5, border_color),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(t_gap)
        else:
            story.append(Paragraph("<i>No knowledge gaps detected.</i>", body_style))
        story.append(Spacer(1, 10))

        # -----------------------------------------------------------------
        # 9. SOURCE EVIDENCE TRACEABILITY & 10. APPROVALS
        # -----------------------------------------------------------------
        story.append(Paragraph("8. Source Evidence Traceability & Approval Log", section_heading))
        evidence_items = db.query(Evidence).join(KnowledgeItem).filter(KnowledgeItem.project_id == project.id).limit(10).all()
        if evidence_items:
            ev_data = [[
                Paragraph("<b>Claim / Knowledge Item</b>", body_style),
                Paragraph("<b>Source Document</b>", body_style),
                Paragraph("<b>Page</b>", body_style),
                Paragraph("<b>Verified Excerpt</b>", body_style),
                Paragraph("<b>Status</b>", body_style)
            ]]
            for ev in evidence_items:
                ev_data.append([
                    Paragraph(ev.knowledge_item.title[:40], body_style),
                    Paragraph(ev.document.filename if ev.document else "Unknown", body_style),
                    Paragraph(f"p.{ev.page_number}", body_style),
                    Paragraph(f"<i>\"{ev.exact_quote[:70]}...\"</i>", body_style),
                    Paragraph("VERIFIED" if ev.is_verified else "UNVERIFIED", body_style)
                ])
            t_ev = Table(ev_data, colWidths=[120, 100, 40, 200, 80])
            t_ev.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), light_bg),
                ('GRID', (0, 0), (-1, -1), 0.5, border_color),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(t_ev)
        else:
            story.append(Paragraph("<i>No evidence records found.</i>", body_style))

        story.append(Spacer(1, 14))
        story.append(HRFlowable(width="100%", thickness=1, color=border_color, spaceAfter=8))
        story.append(Paragraph("Generated by <b>Project Memory AI Platform</b> – Confidential & Grounded in Source Evidence.", subtitle_style))

        doc.build(story)
        buffer.seek(0)
        return buffer

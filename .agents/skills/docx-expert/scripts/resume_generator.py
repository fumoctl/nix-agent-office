"""
ATS-Optimized Resume Generator
Usage: python resume_generator.py config.json output.docx

Single-page, ATS-friendly, professional resume.
No images, no tables for layout (tab stops instead), no headers/footers.
"""

import json
import sys

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


PRIMARY = RGBColor(0x1a, 0x36, 0x5d)
MUTED   = RGBColor(0x64, 0x74, 0x8b)
TEXT    = RGBColor(0x1f, 0x29, 0x37)


def _add_divider(doc):
    """Thin horizontal line as a section divider."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after  = Pt(4)
    pPr = p._p.get_or_add_pPr()
    pBdr = pPr.makeelement(qn('w:pBdr'), {})
    bottom = pBdr.makeelement(qn('w:bottom'), {
        qn('w:val'): 'single', qn('w:sz'): '4',
        qn('w:space'): '1', qn('w:color'): '1A365D'})
    pBdr.append(bottom)
    pPr.append(pBdr)


def _section_heading(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after  = Pt(0)
    r = p.add_run(text.upper())
    r.bold = True
    r.font.size = Pt(11)
    r.font.color.rgb = PRIMARY
    r.font.name = 'Calibri'
    _add_divider(doc)


def _right_aligned_line(doc, left_text, right_text, left_bold=False, right_bold=False,
                         left_color=None, right_color=None, left_size=10.5, right_size=10):
    """Tab-based right-aligned layout for job title ↔ dates, school ↔ year."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after  = Pt(0)
    pf = p.paragraph_format
    pf.tab_stops.add_tab_stop(Inches(6.5), WD_TAB_ALIGNMENT.RIGHT)

    r = p.add_run(left_text)
    r.bold = left_bold
    r.font.size = Pt(left_size)
    r.font.name = 'Calibri'
    if left_color:
        r.font.color.rgb = left_color

    p.add_run('\t')

    r2 = p.add_run(right_text)
    r2.bold = right_bold
    r2.font.size = Pt(right_size)
    r2.font.name = 'Calibri'
    if right_color:
        r2.font.color.rgb = right_color


def generate_resume(cfg: dict, output_path: str):
    doc = Document()

    # Page: tight margins to fit on one page
    sec = doc.sections[0]
    sec.page_width    = Inches(8.5)
    sec.page_height   = Inches(11)
    sec.top_margin    = Inches(0.6)
    sec.bottom_margin = Inches(0.6)
    sec.left_margin   = Inches(0.75)
    sec.right_margin  = Inches(0.75)

    doc.styles['Normal'].font.name = 'Calibri'
    doc.styles['Normal'].font.size = Pt(10.5)
    doc.styles['Normal'].font.color.rgb = TEXT

    # ── Name ────────────────────────────────────────────────────────────────
    name_p = doc.add_paragraph()
    name_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    name_p.paragraph_format.space_after = Pt(2)
    nr = name_p.add_run(cfg['name'])
    nr.font.size = Pt(24)
    nr.font.bold = True
    nr.font.color.rgb = PRIMARY
    nr.font.name = 'Calibri'

    # ── Contact line ────────────────────────────────────────────────────────
    contact = cfg.get('contact', {})
    parts = [v for v in [contact.get('email'), contact.get('phone'),
                          contact.get('location'), contact.get('linkedin'),
                          contact.get('github')] if v]
    cp = doc.add_paragraph(' | '.join(parts))
    cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cp.paragraph_format.space_after = Pt(4)
    for r in cp.runs:
        r.font.size = Pt(9.5)
        r.font.color.rgb = MUTED

    # ── Summary ─────────────────────────────────────────────────────────────
    if cfg.get('summary'):
        _section_heading(doc, 'Professional Summary')
        sp = doc.add_paragraph(cfg['summary'])
        sp.paragraph_format.space_before = Pt(4)
        sp.paragraph_format.space_after  = Pt(0)
        for r in sp.runs:
            r.font.size = Pt(10.5)

    # ── Experience ──────────────────────────────────────────────────────────
    if cfg.get('experience'):
        _section_heading(doc, 'Experience')
        for job in cfg['experience']:
            _right_aligned_line(doc,
                left_text=job['title'], right_text=job['dates'],
                left_bold=True, left_size=11, right_size=9.5, right_color=MUTED)

            comp_p = doc.add_paragraph()
            comp_p.paragraph_format.space_before = Pt(0)
            comp_p.paragraph_format.space_after  = Pt(2)
            cr = comp_p.add_run(job['company'])
            cr.font.size = Pt(10)
            cr.font.italic = True
            cr.font.color.rgb = MUTED

            for bullet in job.get('bullets', []):
                bp = doc.add_paragraph(bullet, style='List Bullet')
                bp.paragraph_format.space_before = Pt(0)
                bp.paragraph_format.space_after  = Pt(1)
                bp.paragraph_format.left_indent  = Inches(0.2)
                for r in bp.runs:
                    r.font.size = Pt(10.5)

    # ── Education ───────────────────────────────────────────────────────────
    if cfg.get('education'):
        _section_heading(doc, 'Education')
        for edu in cfg['education']:
            _right_aligned_line(doc,
                left_text=edu.get('degree', ''), right_text=edu.get('year', ''),
                left_bold=True, left_size=11)
            sp = doc.add_paragraph(
                f"{edu.get('school', '')}"
                + (f" | GPA: {edu['gpa']}" if edu.get('gpa') else '')
                + (f" | {edu['honors']}" if edu.get('honors') else ''))
            sp.paragraph_format.space_before = Pt(0)
            sp.paragraph_format.space_after  = Pt(0)
            for r in sp.runs:
                r.font.size = Pt(10)
                r.font.color.rgb = MUTED

    # ── Skills ──────────────────────────────────────────────────────────────
    if cfg.get('skills'):
        _section_heading(doc, 'Skills')
        for category, items in cfg['skills'].items():
            sp = doc.add_paragraph()
            sp.paragraph_format.space_before = Pt(3)
            sp.paragraph_format.space_after  = Pt(0)
            r = sp.add_run(f'{category}: ')
            r.bold = True
            r.font.size = Pt(10.5)
            r2 = sp.add_run(', '.join(items))
            r2.font.size = Pt(10.5)

    # ── Certifications ──────────────────────────────────────────────────────
    if cfg.get('certifications'):
        _section_heading(doc, 'Certifications')
        for cert in cfg['certifications']:
            _right_aligned_line(doc,
                left_text=cert['name'], right_text=cert.get('year', ''),
                left_size=10.5, right_size=10, right_color=MUTED)

    # ── Projects (optional) ─────────────────────────────────────────────────
    if cfg.get('projects'):
        _section_heading(doc, 'Projects')
        for proj in cfg['projects']:
            pp = doc.add_paragraph()
            pp.paragraph_format.space_before = Pt(4)
            pp.paragraph_format.space_after  = Pt(1)
            r = pp.add_run(proj['name'] + ': ')
            r.bold = True
            r.font.size = Pt(10.5)
            r2 = pp.add_run(proj['description'])
            r2.font.size = Pt(10.5)

    ppr_seq = ['pStyle', 'keepNext', 'keepLines', 'pageBreakBefore', 'framePr', 'widowControl',
               'numPr', 'suppressLineNumbers', 'pBdr', 'shd', 'tabs', 'suppressAutoHyphens',
               'kinsoku', 'wordWrap', 'overflowPunct', 'topLinePunct', 'autoSpaceDE',
               'autoSpaceDN', 'bidi', 'adjustRightInd', 'snapToGrid', 'spacing',
               'ind', 'contextualSpacing', 'mirrorIndents', 'suppressOverlap', 'jc', 'textDirection',
               'textAlignment', 'textboxTightWrap', 'outlineLvl', 'divId', 'cnfStyle', 'rPr',
               'sectPr', 'pPrChange']
    idx = {qn(f'w:{n}'): i for i, n in enumerate(ppr_seq)}
    for pr in doc.element.iter(qn('w:pPr')):
        kids = list(pr)
        srt = sorted(kids, key=lambda k: idx.get(k.tag, 999))
        if srt != kids:
            for k in kids:
                pr.remove(k)
            for k in srt:
                pr.append(k)
    for z in doc.settings.element.findall(qn('w:zoom')):
        z.set(qn('w:percent'), '100')
    doc.save(output_path)
    print(f'Resume saved: {output_path}')


EXAMPLE_CONFIG = {
    "name": "Jordan Lee",
    "contact": {
        "email": "jordan@email.com",
        "phone": "(415) 555-0199",
        "location": "San Francisco, CA",
        "linkedin": "linkedin.com/in/jordanlee",
        "github": "github.com/jordanlee"
    },
    "summary": "Senior software engineer with 7 years building scalable backend systems and data platforms. Proven track record leading cross-functional teams and reducing infrastructure costs by 40%.",
    "experience": [
        {
            "title": "Senior Software Engineer",
            "company": "Stripe · San Francisco, CA",
            "dates": "2022 – Present",
            "bullets": [
                "Led migration of payment processing pipeline to Kafka, handling 2M+ events/day with 99.99% uptime",
                "Designed multi-region database architecture reducing P99 latency from 180ms to 42ms",
                "Mentored 6 junior engineers; established quarterly tech talks and RFC review process"
            ]
        },
        {
            "title": "Software Engineer",
            "company": "Airbnb · San Francisco, CA",
            "dates": "2019 – 2022",
            "bullets": [
                "Built pricing optimization service using gradient boosting, improving host revenue by 12%",
                "Implemented CI/CD pipeline reducing deploy frequency from weekly to 20× per day",
                "Led API redesign reducing average response time by 35% across 50+ endpoints"
            ]
        }
    ],
    "education": [
        {
            "degree": "B.S. Computer Science",
            "school": "UC Berkeley",
            "year": "2019",
            "gpa": "3.87",
            "honors": "Summa Cum Laude"
        }
    ],
    "skills": {
        "Languages": ["Python", "Go", "TypeScript", "SQL", "Rust"],
        "Infrastructure": ["AWS", "Kubernetes", "Docker", "Terraform", "Kafka"],
        "Databases": ["PostgreSQL", "Redis", "DynamoDB", "Snowflake"],
        "Frameworks": ["FastAPI", "NestJS", "React", "dbt"]
    },
    "certifications": [
        {"name": "AWS Solutions Architect – Professional", "year": "2023"},
        {"name": "Certified Kubernetes Administrator (CKA)", "year": "2022"}
    ]
}

if __name__ == '__main__':
    if len(sys.argv) >= 3:
        with open(sys.argv[1]) as f:
            cfg = json.load(f)
        generate_resume(cfg, sys.argv[2])
    else:
        generate_resume(EXAMPLE_CONFIG, 'resume_demo.docx')
        print('Demo: resume_demo.docx')

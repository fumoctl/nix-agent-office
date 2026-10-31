# Resume Template — Document Structure

## Layout

```
+----------------------------------------------------------+
|                      FULL NAME                            |
|    email@example.com | (555) 123-4567 | City, State      |
|    linkedin.com/in/name | github.com/name                |
|  -----------------------------------------------         |
|                                                           |
|  PROFESSIONAL SUMMARY                                     |
|  Results-driven [role] with X+ years of experience in     |
|  [domain]. Proven track record of [achievement].          |
|                                                           |
|  EXPERIENCE                                               |
|  -----------------------------------------------         |
|  Senior Software Engineer                    2022-Present |
|  Company Name, City, State                                |
|  • Led migration of monolithic app to microservices,      |
|    reducing deploy time by 75%                            |
|  • Designed and implemented real-time data pipeline       |
|    processing 10M+ events/day                             |
|  • Mentored team of 5 junior engineers                    |
|                                                           |
|  Software Engineer                            2019-2022   |
|  Previous Company, City, State                            |
|  • Built REST API serving 50K requests/minute             |
|  • Implemented CI/CD pipeline reducing bug rate by 40%    |
|                                                           |
|  EDUCATION                                                |
|  -----------------------------------------------         |
|  B.S. Computer Science                              2019  |
|  University Name, City, State | GPA: 3.8                  |
|                                                           |
|  SKILLS                                                   |
|  Languages: Python, TypeScript, Go, SQL                   |
|  Frameworks: React, FastAPI, Django, NestJS               |
|  Tools: AWS, Docker, Kubernetes, PostgreSQL, Redis        |
|                                                           |
|  CERTIFICATIONS                                           |
|  AWS Solutions Architect Associate            2023        |
+----------------------------------------------------------+
```

## Implementation Notes

1. **Margins**: 0.6 inches all sides (maximize space)
2. **Name**: Calibri 24pt Bold, centered
3. **Contact line**: Calibri 10pt, centered, muted color, pipe-separated
4. **Section headings**: Calibri 12pt Bold, UPPERCASE, bottom border (thin line)
5. **Job title + dates**: Use invisible table — title left-aligned, dates right-aligned
6. **Bullets**: Use List Bullet style, Calibri 10.5pt
7. **Skills**: Comma-separated on single lines by category
8. **Total**: Fit on ONE PAGE. Reduce spacing if needed.
9. **Fonts**: Calibri (safe, ATS-friendly). Alternatives: Garamond, Arial.
10. **No images/graphics**: ATS systems can't parse them.

## ATS Optimization Rules

- Use standard section headings (Experience, Education, Skills)
- No headers/footers (ATS may not read them)
- No tables for layout (use tab stops instead for date alignment)
- No text boxes or floating elements
- Standard fonts only (Calibri, Arial, Times New Roman, Garamond)
- Save as .docx (not .pdf) for ATS submission

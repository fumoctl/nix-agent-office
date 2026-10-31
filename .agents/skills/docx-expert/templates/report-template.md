# Report Template — Document Structure

## Layout

```
Page 1: Cover Page
+----------------------------------------------------------+
|                                                           |
|                      [Company Logo]                       |
|                                                           |
|                                                           |
|                    REPORT TITLE HERE                      |
|                 Subtitle or Description                   |
|                                                           |
|                                                           |
|                                                           |
|                     Prepared by: Name                     |
|                     Date: Month DD, YYYY                  |
|                     Version: 1.0                          |
|                                                           |
|                     CONFIDENTIAL                          |
+----------------------------------------------------------+

Page 2: Table of Contents
+----------------------------------------------------------+
|  TABLE OF CONTENTS                                       |
|                                                           |
|  1. Executive Summary ............................ 3      |
|  2. Introduction ................................. 4      |
|  3. Methodology .................................. 5      |
|  4. Findings ..................................... 7      |
|     4.1 Key Finding One ......................... 7       |
|     4.2 Key Finding Two ......................... 9       |
|  5. Recommendations .............................. 11     |
|  6. Appendix ..................................... 13     |
+----------------------------------------------------------+

Page 3+: Content
+----------------------------------------------------------+
|  Company Name                                  Page X     |
|  -----------------------------------------------         |
|                                                           |
|  1. EXECUTIVE SUMMARY                                     |
|                                                           |
|  Brief overview paragraph covering key findings           |
|  and recommendations in 3-5 sentences.                    |
|                                                           |
|  KEY METRICS:                                             |
|  +--------+--------+--------+--------+                    |
|  | Metric | Q1     | Q2     | Change |                    |
|  +--------+--------+--------+--------+                    |
|  | Rev    | $1.2M  | $1.5M  | +25%   |                    |
|  +--------+--------+--------+--------+                    |
|                                                           |
|  [Chart Image]                                            |
|  Figure 1: Revenue Growth                                 |
|                                                           |
+----------------------------------------------------------+
```

## Implementation Notes

1. Cover page: use `add_cover_page()` helper
2. TOC: use Word field code `TOC \o "1-3" \h \z \u`
3. Headers: company name left, page number right
4. Use Heading 1 for chapters, Heading 2 for sections
5. Data tables: styled header row, zebra striping
6. Charts: generate with matplotlib, embed as PNG
7. Consistent 1-inch margins throughout
8. Professional font: Calibri 11pt body, Calibri Bold for headings

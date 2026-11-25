# Report templates

The report is generated from a single document model (`backend/app/reports/builder.py`) and rendered to PDF, DOCX and HTML (`render.py`).
Its theoretical text is taken directly from the editable Markdown sources in `research/`:

| Report section | Source |
|---|---|
| Literature review, references | `research/Literature_Review.md` |
| Theoretical framework | `research/Theoretical_Framework.md` |
| Research questions and hypotheses | `research/Research_Question_and_Hypotheses.md` |
| Cognitive task design | `research/Experimental_Design.md` §5–6, `research/Lecture_Concept_Mapping.md` |
| Appendices | `research/Participant_Instructions.md`, `research/Informed_Consent.md`, `research/Statistical_Analysis_Plan.md`, `experiment/documentation/Pilot_Testing_Protocol.md` |
| Title page, apparatus, recruitment, pilot observations, deviations | Dashboard → Settings |
| Results, discussion, conclusion | Latest analysis run (generated; pending when no eligible data) |

Edit those sources (never the generated files) and regenerate from the dashboard (Reports → Generate Research Report) or with `scripts/generate_preliminary_deliverables.py`.

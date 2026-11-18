# TFPMDS final academic verification

Prepared for Gloria Beneth Mbilinyi, Dar es Salaam Institute of Technology, Bachelor of Engineering in Computer Engineering. This report records corrections to the original 45-page technical proposal at published baseline `ddc2e8aacc48ece0dfad27b19e5f26317f56cd58`.

## Delivered documents and content boundaries

| Word file | Original PDF content | Verified Word pages | Editable source blocks | Native tables | Size |
| --- | --- | --- | --- | --- | --- |
| TFPMDS_Technical_Proposal_Part_1.docx | Pages 1-10 | 20 | 42 | 3 | 0.95 MiB |
| TFPMDS_Technical_Proposal_Part_2.docx | Pages 11-20 | 37 | 15 | 0 | 3.05 MiB |
| TFPMDS_Technical_Proposal_Part_3.docx | Pages 21-45 | 47 | 79 | 4 | 3.02 MiB |

The complete updated PDF contains **103 A4 pages**. Page counts increased because poster diagrams were replaced by A4 views and the text was enlarged. Word pagination differs from the complete PDF. No original body block was omitted or duplicated: all **136 blocks**, **27 numbered sections**, **18 source figures** and **61 traceability records** remain represented. The corrected cover and updated contents are navigation/front matter, rather than additional implementation claims.

The first split is immediately before sequence process 4 (original page 11); the second is immediately before section 13 (original page 21). These boundaries do not cut an ordinary paragraph or table. Section 10 continues in Part 2 with Figure 10.4. Part 2 has no original tables; all seven original tables are native editable Word tables in Parts 1 and 3.

## Academic corrections

- Added the DIT institution, programme and student name. Registration number, course/module name, lecturer/supervisor and submission date remain explicit placeholders.
- Used A4 portrait text and landscape figures/tables, standard margins, 12-point Times New Roman body text, 1.5 spacing, native heading styles, page-number fields and updated local contents tables. Constrained tables, captions and code use smaller text where practical.
- Added section-based figure numbers and continuation captions. Full state/package overviews precede their overlapping detail sheets, so relationships can be followed across the enlarged views.
- Replaced the outdated blanket statement about unpublished history with the distinction between Codex's local development and the owner's subsequent GitHub push of the original 26 commits.
- Retained all original technical explanations, tests, references and limitations. Seven prose blocks were corrected; the remaining original body text is unchanged. Word references retain native hyperlinks. The Pydantic documentation link was checked against the official site and its redirect.

## Word and PDF verification

Each final Word part was opened independently in the user's installed Microsoft Word, its table of contents updated, saved, and exported to PDF through Word. The verified page counts above come from those native exports. OOXML checks confirm editable text, seven native tables, native heading styles, A4 sections, internal image relationships, page fields, and no OLE objects or whole-page PDF screenshots.

LibreOffice is not installed. The packaged `render_docx.py` initially reported that missing renderer. The final QA instead used actual Microsoft Word exports with the packaged rasterizer and bundled Poppler. Page images/contact sheets and selected full pages were inspected for broken images, overflow, orphaned captions, page numbering and table layout. The early PDF caption spill and a default-template title border/font issue were corrected before final verification. All current PDF figure-source captions share their page with the corresponding image.

Machine-readable evidence: `evidence/academic-verification.json` and `evidence/pdf-validation.json`. The complete PDF has 27 outline entries, 62 link annotations, 69 publication image panels/overviews, only A4 media boxes, and no unexpected blank pages. The original page-size error is addressed by removing every A1/A2/A3 PDF sheet.

## Editable UML verification

| Canonical source | Primary shapes | Primary connectors | Editable pages in final file |
| --- | --- | --- | --- |
| sequence.drawio | 179 | 104 | 17 |
| communication.drawio | 128 | 44 | 17 |
| purchase-order-state.drawio | 48 | 24 | 1 |
| shipment-state.drawio | 37 | 22 | 1 |
| package-overview.drawio | 28 | 26 | 1 |
| classes-identity-produce.drawio | 41 | 10 | 1 |
| classes-orders-payments.drawio | 33 | 7 | 1 |
| classes-logistics-notifications.drawio | 38 | 9 | 1 |

All eight primary models opened in the draw.io web editor as native shapes/connectors. The corrected local sequence and communication files were also loaded through encoded source links; their 16 additional A4 pages appeared in the editor. A sequence excerpt displayed 19 shapes/11 connectors, and communication page `A4 process 3 excerpt 2` displayed 14 shapes/4 connectors, including `3.6.1` and the grouped `3.10, 3.11, 3.12` link labels. The shared catalogue still contains all 84 matching messages and all 15 participants. Every canonical primary diagram is structurally identical to the published baseline; new pages are publication views, not extra business processes or replacement models.

The files use genuine draw.io/mxGraph XML. The original agent generated this native XML programmatically; it did not claim manual mouse drawing. Draw.io itself was used for the final opening/editability checks. The supplied PNGs are exports of the same authored geometry. The canonical combined fragments retain their guards, the two state machines retain their transitions, and the package diagrams retain their class relationships. `scripts/validate_uml.py` checks identifiers, endpoints, messages, required guards/states, the shipment graph and package dependency cycles. Editable sources remain in `uml/` and the submission package.

## Implementation evidence retained

The academic corrections do not change application behavior. The prior verified baseline remains **28 backend tests and 5 frontend tests passed**, the production build passed, functional acceptance remains **61/61**, and the recorded browser journey has 14 verified steps. Those results are preserved from the genuine development evidence; they are not invented new test runs. Current corrections were checked with the document/UML validators and the read-only release snapshot verification.

Payments and SMS remain simulations. No real mobile money, SMS network, production deployment, field study, PostgreSQL integration test or penetration test is claimed. The Playwright harness remains typechecked; its previously blocked normal browser run is not relabelled as executed.

## Git history and submission handoff

GitHub's read-only listing confirmed the owner's 26 published commits through `ddc2e8a`. The existing history and official owner/remote were preserved. Before the correction commit, the local identity was checked as `gloria-mbilinyi <gloriambilinyi5@gmail.com>`, associated with the owner; no Git identity setting was changed. Academic correction implementation commit: `125617398614c10f342260b779c6bf2db34143a6` (`docs: correct academic report and add editable Word parts`). The subsequent verification/handoff commit contains this report and the completed ledger; its exact hash is in the delivery manifest. All hashes are recorded in `AGENT_DEVELOPMENT_LOG.md`, `LOCAL_COMMIT_HISTORY.md` and that manifest. Codex has not pushed the academic corrections.

From the project directory, the owner can publish the additional commits later:

```powershell
git status
git remote -v
git log --oneline origin/main..HEAD
git fetch origin
git push -u origin main
```

## Remaining items

Complete the four academic placeholders before submission. The three Word parts contain editable text and tables; UML images are edited through the supplied draw.io sources. No unresolved content omission, broken image or page-size defect was found in the completed checks. The student's institution determines any final submission-specific formatting requirements.

# School dashboard and APA tools

School retains the existing Study database, documents directory, launcher path and workspace ID. The visible shell/menu names change to School without moving or deleting course files. Course, assignment and notes workflows remain available.

The overview reads assignments across all courses and shows open, complete, overdue and undated counts plus the earliest outstanding dated assignment. Due dates use `YYYY-MM-DD` and the machine's local date. Existing informal due strings remain stored and appear in the undated count instead of being guessed. Assignment table cells are read-only; the existing status controls persist changes.

The APA Paper action opens one form for title, author, institution, course, instructor and due date, plus optional supplied paper text and references. It exports a DOCX with US Letter pages, one-inch margins, 12-point Times New Roman, double spacing, a centered title page, page-number header, half-inch body paragraph indents and hanging reference indents. The builder preserves supplied writing and reference entries; it does not invent sources, sort references, validate citations or verify a rubric. Review the paper against instructor requirements before submission.

Export writes a complete temporary document before publishing it. Existing files are protected unless the user explicitly confirms replacement. Missing `python3-docx` produces a dependency message while the rest of School remains usable. Future image dependencies and source CI include this package.

The mySNHU button opens the official portal in the user's browser. Authentication remains in the browser; School stores no portal credentials and does not scrape assignments or grades.

## Verified in the source test environment

- [x] All-course dashboard with completion and overdue counts.
- [x] Existing Study database and notes survive reopening.
- [x] APA form and supplied-content DOCX export.
- [x] Existing-file protection and failed-save recovery.
- [x] Three-page sample rendered and visually inspected: title, body, references.
- [x] Shell, desktop menu and CI integration.

Installed-PC deployment, live SNHU sign-in, grade tracking, rubric/source libraries and instructor-specific formatting checks remain pending.

References: [APA student paper guide](https://www.apa.org/ed/precollege/psn/2020/09/apa-style-student-papers) and [official mySNHU portal](https://my.snhu.edu/).

Companion repository scope: this stages the School source, launcher, menu file and tests. The authoritative native repository owns the qualified image payload wiring; no companion boot/build scaffolding is replaced.

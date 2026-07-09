# Course production template

The repeatable recipe for one Cambium Academy course per week. Copy this checklist into the new course folder and work top to bottom.

## Folder layout

```
courses/course-NN-short-name/
  README.md            syllabus: outcomes, modules, time, links to everything
  slides/              the .pptx lecture deck (30 to 40 slides)
  script/
    VIDEO_SCRIPT.md    per-slide narration, recording notes, YouTube description
  web/
    index.html         course landing page (video embed + links)
    slides.html        browser slide deck, keyboard and touch friendly
    quiz.html          20 questions, instant grading, pass at 70%
    certificate.html   name entry, printable certificate with unique ID
  resources.md         hand-verified free videos, courses, and guides
  PUBLISHING.md        exact steps to publish this course
```

## Weekly production checklist

- [ ] 1. Pick the topic from the roadmap in courses/README.md and write 5 learning outcomes
- [ ] 2. Research: dispatch scouts for current facts, dispatch the librarian to verify every external link. Nothing enters the course unsourced.
- [ ] 3. Outline 5 to 6 modules, roughly 5 slides each
- [ ] 4. Build the deck (30 to 40 slides, one idea per slide, big type, visual on every slide)
- [ ] 5. Write the narration script: 2 to 4 spoken sentences per slide, plain English
- [ ] 6. Build the web version: landing page, HTML slides, quiz, certificate
- [ ] 7. Write the 20-question quiz. Every answer must be findable in the slides. Pass mark 70%.
- [ ] 8. Verification pass: every link fetched live, every dated fact re-checked, deck opens, quiz key correct
- [ ] 9. Director gate: review and approve
- [ ] 10. Publish per PUBLISHING.md, then update the catalog row in courses/README.md to Ready

## Quality bar

Write like a person talking to a smart friend. Short sentences. No jargon without a one-line explanation. No hype. Never use the em dash. Every model name, price, and stat carries a date and a source. If a fact could not be verified, it does not ship.

## Certificate rules

Pass mark 70% (14 of 20). Certificate carries: learner name, course title, completion date, and a certificate ID in the form CAMB-CNN-XXXXXX. IDs are generated in the browser and not stored anywhere; the certificate is honor-based, like most free course certificates.

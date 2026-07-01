---
name: ui-ux-design
description: Design and review interfaces that are accessible, usable, and consistent, not just pretty. Use when the user wants to design a UI or UX, set up a design system or design tokens, choose colors, type, and spacing, check accessibility or contrast, lay out a responsive page, improve a form, or get a usability review of an existing screen. Trigger on "UI", "UX", "design system", "design tokens", "accessibility", "WCAG", "contrast", "responsive design", "usability", "wireframe", "improve this UI", "review this screen". Pairs with web-development (which builds it) and brand-guidelines (which supplies a house look). Honest: this advises and flags against real standards; the human designer decides and signs off. Names its sources.
---

# UI/UX design: accessible and usable first, decorative last

A good interface is one a person can actually operate, including with a keyboard or a screen reader, on a
small screen, under stress. Beauty that fails those is a bug. Design against standards, not taste alone, and
hand the build to the web-development skill.

For component libraries, icon sets, and curated design-resource lists, see the proven, most-starred
repositories in `docs/web_ui_toolbelt.md`. Prefer accessible primitives (for example Radix under shadcn/ui)
so the keyboard and focus behavior is correct before you style it.

## Accessibility is the floor, not a feature (WCAG 2.2 AA)

Organize thinking with POUR: Perceivable, Operable, Understandable, Robust. The concrete checks:

- Contrast: normal text at least 4.5:1, large text at least 3:1, and UI components and focus indicators at least 3:1.
- Keyboard: every interactive element is reachable and operable by keyboard, in a logical order, with no traps.
- Focus: a visible focus indicator with at least 3:1 contrast and a 2 px perimeter (WCAG 2.2, 2.4.11). Never remove :focus-visible without a stronger replacement.
- Prefer native HTML elements. No ARIA is better than bad ARIA: wrong ARIA breaks screen readers more than it helps.
- Do not signal state with color alone. Pair it with text, an icon, or a shape.

## Design tokens: three tiers, so theming does not touch components

Build the visual language as tokens, not scattered values:

- Primitive: raw values, for example color-blue-500, space-4.
- Semantic: role names that map to primitives, for example color-interactive-primary, color-danger, space-inset-md.
- Component: the values a component reads, for example button-padding-x. Components read semantic and component tokens only, so a theme swap never edits component code.

Scales, not free choice: a type scale on a modular ratio (1.25 or 1.333) in rem, and a spacing scale on a
4 px base. Color as a primitive palette plus semantic role assignment, so branding is decoupled from components.

Store the tokens in the Design Tokens Community Group (DTCG) format, a tool-agnostic JSON standard with
`$value`, `$type`, and `$description` fields. It is portable across Figma, Style Dictionary, and code, so
the same tokens drive design and build without hand-copying. See designtokens.org.

Do not start the design system from a blank page. Adopt an open, battle-tested one as the preset baseline,
then override only the brand layer: Material 3, IBM Carbon, Adobe Spectrum, Shopify Polaris, GitHub Primer,
or the GOV.UK Design System. Keeping a few named presets you can switch between is faster and more
consistent than inventing tokens per project.

## Layout: mobile-first and responsive

Write base styles for the smallest viewport, then add breakpoints upward. Use CSS Grid for two-dimensional
layout and Flexbox for one-dimensional alignment; both are baseline-supported. Common patterns (sidebar and
content, card grid, sticky header, holy grail) need no JavaScript.

## Every interactive element needs all its states

Design and specify: default, hover, focus-visible, active, disabled, error, and loading. Missing states are
one of the most common usability and accessibility gaps. Wrap all motion in prefers-reduced-motion, because
users with vestibular or cognitive conditions depend on it.

## Forms, where most usability is won or lost

- A visible label on every input. A placeholder is not a label.
- Inline, specific error messages next to the field they concern, not a summary far away.
- Never color-alone for the error state; include text.

## Review with Nielsen's 10 heuristics

Use them as a checklist when auditing a screen: visibility of system status, match to the real world, user
control and freedom, consistency and standards, error prevention, recognition over recall, flexibility and
efficiency, aesthetic and minimalist design, help users recover from errors, and help and documentation.
They are qualitative and rater-dependent, so treat findings as prompts, not scores.

## Red flags to catch in a review

Text under the contrast minimum, focus that disappears on tab, click targets under about 24 px, color as the
only signal, placeholder-as-label, motion with no reduced-motion fallback, and a "design system" that is
really hard-coded values scattered across components.

## Attribution and sources

Standards and durable guidance, cited not invented: WCAG 2.2 (w3.org/TR/WCAG22), contrast and focus
(w3.org/WAI/WCAG22/Understanding), using ARIA (w3.org/TR/using-aria), design tokens (Adobe Spectrum,
Material 3), spacing and type scales (Material 3, Tailwind), responsive layout and prefers-reduced-motion
(MDN, developer.mozilla.org), forms (w3.org/WAI/tutorials/forms), and Nielsen's 10 heuristics
(nngroup.com/articles/ten-usability-heuristics).

Ideas adopted from two open UI/UX skill projects, with credit and no code copied: the DTCG-token and
design-system-preset approach from ux-ui-agent-skills (github.com/plugin87/ux-ui-agent-skills), and the
design-vocabulary and tested-prompt review approach from LibreUIUX-Claude-Code
(github.com/HermeticOrmus/LibreUIUX-Claude-Code). The related ui-ux-pro-max skill
(github.com/nextlevelbuilder/ui-ux-pro-max-skill) and the official Anthropic frontend-design skill are worth
consulting for a wider style vocabulary. Verify each project's license before adopting any of its files.

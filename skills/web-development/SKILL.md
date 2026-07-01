---
name: web-development
description: Build real websites and web apps well, and choose the right stack instead of defaulting to a framework. Use when the user wants to build or review a website, web app, dashboard, landing page, or component; pick between React, Next.js, SvelteKit, Astro, or plain HTML; set up styling, components, testing, or a performance budget. Trigger on "build a website", "web app", "frontend", "React", "Next.js", "Svelte", "Astro", "Tailwind", "shadcn", "component", "responsive", "landing page", "Core Web Vitals", "make this site". Pairs with ui-ux-design (which owns accessibility and visual design) and, for a cinematic 3D scene only, cinematic-frontend. Honest: ships tested, accessible, performance-budgeted code, and judges the result in a real browser, not from a screenshot.
---

# Web development, the right tool for the job

Most "make a website" work goes wrong at the first decision: reaching for a heavy framework when the job
needs almost none. Start from the content and the interactivity, then pick the lightest stack that does it.
Accessibility and a performance budget are part of the definition of done, not a later pass. For anything
visual or usability-related, work with the ui-ux-design skill.

The proven, most-starred repositories for each choice below (frameworks, styling, component libraries,
icons, and the learning and reference lists) are curated in `docs/web_ui_toolbelt.md`. Popularity is a
signal, not a reason: pick the lightest option that does the job and install it into the specific project,
never as a Cambium dependency.

## Choose the stack first (do not default to React)

| The job | Reach for | Why |
|---|---|---|
| A landing page, prototype, or email | Plain HTML and CSS | No build step, no dependency surface. Reach here first when JS adds nothing. |
| A content site: docs, blog, marketing | Astro | Ships zero JS by default, best Core Web Vitals baseline, framework islands where needed. |
| An app with real state and many interactions | React, or Next.js when you need SSR, SSG, image optimization, or API routes | The ecosystem and hiring pool are largest; Next adds server rendering in one package. |
| Performance-sensitive, small team | SvelteKit | Compiler ships less runtime JS. Pin minor versions, it moves fast. |

If you cannot name the state the framework is managing, you probably do not need the framework.

## Styling and components

Use design tokens as the base layer (CSS custom properties), then a system on top. Tailwind CSS is the
default utility layer, with dead-CSS elimination and a built-in token scale. Own your components rather
than renting them: shadcn/ui gives you copy-in components built on Radix UI, so you keep the code and the
accessibility that Radix handles (ARIA, keyboard, focus) with no runtime lock-in. All three are MIT.

Get the token scale and the color and contrast decisions from the ui-ux-design skill before you style.

## Ship against a performance budget (Core Web Vitals)

Treat these as pass or fail, measured on a mid-tier phone, not a hope:

- LCP (largest contentful paint) under 2.5 s. Levers: preload the hero image, serve WebP or AVIF, use responsive images.
- INP (interaction to next paint, replaced FID in 2024) under 200 ms. Levers: break long tasks, defer JS, yield to the scheduler.
- CLS (cumulative layout shift) under 0.1. Lever: set explicit width and height on images and embeds.

## Test it, do not eyeball it

- Vitest for unit and integration (Vite-native, Jest-compatible API).
- Playwright for cross-browser end-to-end.
- axe-core in CI for automated accessibility checks. It catches roughly a third of issues, so it is a floor, not a pass. The rest is manual keyboard and screen-reader review (see ui-ux-design).
- Vite as the dev server and bundler for anything that is not Next.js. pnpm for monorepos.

## Honest guardrails

- Judge the result in a real browser. A screenshot does not tell you about focus order, keyboard traps, or jank.
- Inside a Cowork or claude.ai artifact, do not use localStorage or sessionStorage (unsupported there); keep state in memory. A real project on the user's machine can use them.
- Do not ship without the accessibility pass and the Core Web Vitals check. "Looks fine" is not the bar.
- Fast-moving areas to hedge and version-pin: Tailwind v4 migration, SvelteKit minor churn, shadcn/ui component additions.

## Attribution and sources

This skill encodes public best practice; it invents nothing. React (react.dev), Next.js (nextjs.org),
SvelteKit (kit.svelte.dev), Astro (docs.astro.build), Tailwind (tailwindcss.com), shadcn/ui (ui.shadcn.com),
Radix (radix-ui.com), Core Web Vitals (web.dev/articles/lcp, /inp, /cls), Vitest (vitest.dev),
Playwright (playwright.dev), axe-core (github.com/dequelabs/axe-core), Vite (vitejs.dev), MDN (developer.mozilla.org).

# Web and UI/UX toolbelt: the proven, most-starred repositories

A curated shortlist the `web-development` and `ui-ux-design` skills consult. These are references, not
Cambium dependencies. Cambium stays stdlib-first; you install any of these into a specific web project when
that project needs them. Star counts are approximate and change over time; treat them as "widely proven",
not exact. Every entry is open source under its own license. We name each source; none of this is ours.

## Frameworks and core (build the app)

| Repo | Stars (approx) | Use it when |
|---|---|---|
| facebook/react | 235k+ | Stateful, component-driven apps and a large ecosystem or team. |
| vuejs/core (Vue) | 50k+ core, 200k+ legacy | A gentler learning curve, single-file components. |
| sveltejs/svelte | 85k+ | You want less runtime JS; compiler-based. Moves fast, pin versions. |
| vercel/next.js | 130k+ | React plus SSR, SSG, image optimization, and API routes in one package. |
| withastro/astro | 50k+ | Content sites (docs, blogs, marketing); ships zero JS by default, best Core Web Vitals baseline. |
| microsoft/TypeScript | 100k+ | Types on any non-trivial codebase. The default, not an add-on. |
| vitejs/vite | 80k+ | Dev server and bundler for anything that is not Next.js. |
| nodejs/node | 110k+ | The runtime under most of this. |

## Styling

| Repo | Stars (approx) | Use it when |
|---|---|---|
| tailwindlabs/tailwindcss | 85k+ | Utility-first styling with a built-in token scale. The default utility layer. |
| twbs/bootstrap | 170k+ | Fastest path to a conventional, responsive layout; the most-starred CSS framework. |
| (native) CSS custom properties | n/a | The token layer under any system; zero dependencies. |

## UI component libraries

| Repo | Stars (approx) | Use it when |
|---|---|---|
| ant-design/ant-design | 94k+ | Enterprise React apps that want a complete, batteries-included set. |
| mui/material-ui | 93k+ | The safe, huge-adoption choice; Material Design. |
| shadcn-ui/ui | 75k+ | You want to own the component code (copy-in), Tailwind plus Radix. Default for new Next.js and Tailwind projects. |
| radix-ui/primitives | 16k+ | Headless, accessible primitives (ARIA, keyboard, focus) under your own styling. |
| chakra-ui/chakra-ui | 38k+ | Accessible, themeable components with a friendly API. |
| mantinedev/mantine | 38k+ | A large hooks-and-components set with good defaults. |

## Icons, animation, assets

| Repo | Stars (approx) | Use it when |
|---|---|---|
| FortAwesome/Font-Awesome | 74k+ | The most common icon set. |
| lucide-icons/lucide | 13k+ | Clean, MIT icon set; the default in shadcn/ui. |
| google/material-design-icons | 51k+ | Google's open glyphs. |
| juliangarnier/anime | 50k+ | Lightweight JS animation; respect prefers-reduced-motion. |
| animate-css/animate.css | 80k+ | Drop-in CSS animations for simple cases. |

## Learn, reference, and audit (the most-starred repos overall)

These are not installed; they are where to learn and what to check work against.

| Repo | Stars (approx) | What it is |
|---|---|---|
| freeCodeCamp/freeCodeCamp | 400k+ | The most-starred repo on GitHub; a full free curriculum. |
| kamranahmedse/developer-roadmap | 300k+ | Role-based learning paths for web and beyond. |
| codecrafters-io/build-your-own-x | 350k+ | Rebuild real technologies from scratch to understand them. |
| donnemartin/system-design-primer | 290k+ | How to design large systems, with flashcards. |
| sindresorhus/awesome | 350k+ | The index of curated "awesome" lists. |
| EbookFoundation/free-programming-books | 360k+ | Free books and courses across languages. |
| public-apis/public-apis | 340k+ | Free APIs to build against. |
| gztchan/awesome-design | 34k+ | Curated UI/UX design resources. |
| goabstract/Awesome-Design-Tools | 35k+ | The best design tools and plugins. |

## UI/UX design skills to learn from (agent skills, not libraries)

These are Claude/agent skills for design. Cambium borrows their durable, open ideas (see ATTRIBUTION.md);
it does not vendor them. Verify each license before copying any file.

| Repo | Stars (approx) | What to borrow |
|---|---|---|
| nextlevelbuilder/ui-ux-pro-max-skill | 24k+ | A large searchable design-knowledge base: styles, color palettes, font pairings, product types. |
| plugin87/ux-ui-agent-skills | 400+ | DTCG design tokens, WCAG 2.2, design-system presets, any-framework output. |
| HermeticOrmus/LibreUIUX-Claude-Code | smaller | A suite of specialized design agents, a shared design vocabulary, and tested prompts. |
| anthropics frontend-design (in anthropics/skills) | official | Creative direction: opinionated, non-templated palette, type, and layout choices. |

## Design token standard and open design systems

- Design Tokens Community Group (DTCG) format, designtokens.org: the portable JSON token standard (`$value`, `$type`), so the same tokens drive Figma and code.
- Open design systems to adopt as a preset baseline, then override the brand layer: Material 3 (m3.material.io), IBM Carbon (carbondesignsystem.com), Adobe Spectrum (spectrum.adobe.com), Shopify Polaris (polaris.shopify.com), GitHub Primer (primer.style), GOV.UK Design System (design-system.service.gov.uk).

## How Cambium uses this

The two skills point here so a web or design task reaches for a proven tool instead of reinventing one. The
rule of adoption is unchanged: pick the lightest option that does the job, install it into the specific
project (never as a Cambium dependency), keep the accessibility and Core Web Vitals checks, and credit the
source. Popularity is a signal, not a reason; a 300k-star framework is still the wrong choice for a static
page that needs no JavaScript.

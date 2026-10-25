# SentinelFlux Brand & Marketing Standard

Extends the app design system (`sentinelflux-vigilqa/docs/design-system/`). The app system governs product UI;
this document governs the website, product landing pages and marketing material. Tokens live in
[`tokens.css`](tokens.css). When the two disagree, the app design system wins for in-app UI and this file wins
for marketing.

## 1. Typography
- **Sans: Inter** (400, 500, 600, 700, 800) for all headings, body and UI. Load from Google Fonts.
- **Mono: JetBrains Mono** for code, IDs, URLs, model names and terminal-style visuals.
- Marketing headings use `font-extrabold` (H1) / `font-bold` (H2, H3); body is `text-slate-500`–`700`.
  In-app UI keeps the app rule (`font-medium`/`font-semibold`, avoid bold).
- Product dashboards should adopt Inter + JetBrains Mono too (AgentPulse and TalentDesk already do;
  VigilQA, DocForge and SpecVault still use the system stack — migrate on the next UI pass).

## 2. Color
| Role | Value | Use |
|---|---|---|
| Brand | indigo `#4f46e5` (600), hover `#4338ca` (700) | Primary buttons, links, active states, logo tile |
| Accent | violet `#7c3aed` | Gradient end, secondary highlights |
| Ink / body / muted | slate `#0f172a` / `#334155` / `#64748b` | Text |
| Surface / border | slate `#f8fafc` / `#e2e8f0` | Section backgrounds, dividers |
| Dark band | `slate-950` | Footer, CTA bands |
| Success / warning / danger | emerald / amber / red | **Status only** — never a brand or product hue |

**Gradient:** indigo → violet (`--sf-gradient`), used for headline highlight text only. No pink, no other hues.

### Product accents
Marketing follows what the product app actually ships:
- **Default = indigo** — VigilQA, AgentPulse, DocForge and any new product.
- **Exceptions** (app already themed): SpecVault = violet, TalentDesk = teal.
- Emerald and amber are reserved for success/warning and must not be a product's brand color.
- Product identity comes from name, icon and copy, not from re-coloring the whole page.
- A new exception needs a hue from the approved list in the app `theming.md` and an app that ships it.

## 3. Shape and layout (marketing)
- Buttons: `rounded-xl`, `font-semibold`, primary = brand fill + white text.
- Cards: `rounded-2xl` (feature) / `rounded-3xl` (hero or product cards), `border-slate-200`, `shadow-sm`.
- Inputs: `rounded-xl`, brand focus ring (`focus:ring-4 focus:ring-indigo-100`).
- Max content width `max-w-6xl` (marketing) / `max-w-3xl` (long-form). Section padding `py-20`–`py-24`.
- One shared nav and footer across all company pages (copy from `about.html`; footer from `index.html`).

## 4. Logo and assets
- Mark: white shield-check on an indigo `rounded-lg` tile, followed by the word "SentinelFlux" in Inter bold.
  Product pages add a "By SentinelFlux" pill. Do not recolor the tile per product.
- Favicon `/favicon.svg`; social preview `/og-image.png` (1200×630, dark indigo gradient, wordmark + tagline).
- Every public page needs: title, description, canonical, OG + Twitter tags with `og-image.png`.

## 5. Voice
Plain, specific, confident. Lead with the outcome for the team. Avoid hard numbers for growing counts
(use "20+ agents", "11+ modules"). No unverified compliance or customer claims.

## 6. Checklist for new pages
Inter + JetBrains Mono · tokens only (no new hex) · indigo primary · shared nav and footer · OG/canonical tags ·
mobile menu script · © 2026 SentinelFlux.

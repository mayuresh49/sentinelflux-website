# SentinelFlux Website — AI Context Resume

**Last updated:** 2026-05-27

## Project Overview

Static marketing website for SentinelFlux (sentinelflux.in) — an AI-powered test automation platform. Pure HTML/Tailwind CSS, no build step, hosted via GitHub Pages.

**Repo:** github.com/mayuresh49/sentinelflux  
**Stack:** HTML5, Tailwind CSS (CDN), vanilla JS  
**Pages:** index, about, blog, changelog, status, privacy, terms, security + feature/module/blog subpages

---

## What Was Just Done (2026-05-27)

### Chat Widget — AI Assistant (scripted, no API key)
- Added floating chat widget to `website/index.html`
- Pure frontend JS, zero backend/API dependency
- **100 Q&A topics** covering all product areas
- **5 on-demand agent simulations** with animated log streams: CoverageGap, FlakyDetector, RegressionGuard, ResultAnalyzer, LocatorHealer
- Quick-action chips for common questions
- Smart fallback (`smartHint`) for unrecognised questions — topic-cluster detection + always surfaces `engage@sentinelflux.in`

**Fixes applied in session:**
- Pricing response corrected: Starter=Free, Pro=$49/seat/mo, Enterprise=Custom
- CI keyword bug fixed: bare `'ci'` substring was matching inside "pricing" → replaced with specific keys
- All `sentinelflux <command>` CLI references removed from Q&A per product decision (not exposing CLI publicly)
- Export scripts Q&A added ("can I export generated test scripts?")

---

## Previous Work

### Mobile responsiveness pass (31a0357)
Full mobile responsiveness across all pages.

### Email addresses (84b327f)
Replaced placeholder emails with official `sentinelflux.in` addresses.

### Blog posts (a69faae)
Added 10 blog posts + updated listing page.

### Missing pages (c9856ab)
Added Privacy, Terms, About, Security, Changelog, Blog, Status pages.

### Pricing fix (0f722dd)
Updated Starter tier details.

---

## Key Constraints / Decisions

- **No CLI references in Q&A** — don't expose `sentinelflux run` or other commands publicly
- **No API keys on marketing site** — chat widget must be pure scripted JS
- **No backend** — entirely static; any dynamic features must be client-side
- **Tailwind CDN** — classes available globally including in JS-generated HTML
- YAML config examples (non-command) are OK to show in Q&A

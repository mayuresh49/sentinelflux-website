# SentinelFlux Website — AI Context Resume

**Last updated:** 2026-05-27

## Project Overview

Static marketing website for SentinelFlux (sentinelflux.in) — an AI-powered test automation platform. Pure HTML/Tailwind CSS, no build step, hosted via GitHub Pages.

**Repo:** github.com/mayuresh49/sentinelflux  
**Stack:** HTML5, Tailwind CSS (CDN), vanilla JS  
**Pages:** index, about, blog, changelog, status, privacy, terms, security + feature/module/blog subpages

---

## What Was Just Done (2026-05-27) — b40465c

### Pricing: Starter free tier → 14-day free trial
- Removed "Starter — Free — Self-hosted — forever free" tier entirely
- **Reason:** self-hosting would expose codebase; all plans are now cloud-hosted
- Replaced with **Free Trial card**: 14 days, full Pro access, no credit card required
- Updated 10 spots: pricing card HTML, Q&A pricing/open-source/run-locally/multiple-users/run-history/data-storage/GDPR/downgrade responses, and smart hint fallback

---

## Previous Work

### Chat Widget — 100 Q&A topics (00107a9)
- Pure frontend JS AI assistant, zero backend/API dependency
- 100 Q&A topics covering all product areas
- 5 on-demand agent simulations (CoverageGap, FlakyDetector, RegressionGuard, ResultAnalyzer, LocatorHealer)
- Fixes: CI keyword bug, pricing accuracy, CLI refs removed, smart fallback

### Mobile responsiveness pass (31a0357)
Full mobile responsiveness across all pages.

### Email addresses (84b327f)
Replaced placeholder emails with official `sentinelflux.in` addresses.

### Blog posts + missing pages (a69faae, c9856ab)
10 blog posts + Privacy, Terms, About, Security, Changelog, Blog, Status pages.

---

## Key Constraints / Decisions

- **No self-hosting** — all plans cloud-hosted; no Starter free tier to avoid code exposure
- **No CLI references in Q&A** — don't expose `sentinelflux run` or other commands publicly
- **No API keys on marketing site** — chat widget must be pure scripted JS
- **No backend** — entirely static; any dynamic features must be client-side
- **Tailwind CDN** — classes available globally including in JS-generated HTML
- YAML config examples (non-command) are OK to show in Q&A

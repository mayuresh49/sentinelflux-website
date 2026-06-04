# SentinelFlux Website — AI Context Resume

**Last updated:** 2026-06-05

## Project Overview

sentinelflux.in is now a **company homepage** for SentinelFlux, with products on their own pages. Pure HTML/Tailwind CSS, no build step, hosted via GitHub Pages.

**Repo:** github.com/mayuresh49/sentinelflux-website  
**Stack:** HTML5, Tailwind CSS (CDN), vanilla JS  
**Structure:**
- `/` — SentinelFlux company homepage (hero, product cards, mission)
- `/vigilqa/` — VigilQA product landing page (with "By SentinelFlux" breadcrumb)
- `/vigilqa/blog.html` + `/vigilqa/blog/` — VigilQA blog (14 posts, VigilQA branding)
- `/vigilqa/docs/` — VigilQA docs (moved from docs-site/, 41 pages)
- `/specvault/` — SpecVault product landing page
- `/blog.html` — company-level blog stub (links to product blogs)
- Supporting pages: about, changelog, status, privacy, terms, security, features/, modules/

---

## What Was Just Done (2026-06-05) — 961afd6

### Complete SentinelFlux → VigilQA rename across docs and blog
- `docs.js`: sidebar logo "SentinelFlux" → "VigilQA", back link → /vigilqa/, breadcrumb href fixed
- All 41 docs pages: titles "SentinelFlux Docs" → "VigilQA Docs", body product references, nav
- `docs/index.html`: meta description, back link → /vigilqa/, content text
- `vigilqa/blog/why-we-built-sentinelflux.html`: product body refs, CTA "Try VigilQA free", footer logo

---

## Previous Work (2026-06-05) — 48b3e9d + 350b459

### Restructure as company site with per-product pages
- `website/index.html` → new SentinelFlux company homepage (hero, product cards for VigilQA + SpecVault, mission section, CTA)
- `website/vigilqa/index.html` → VigilQA product page (moved from root); nav updated: logo → /vigilqa/, "By SentinelFlux" breadcrumb → /
- `website/vigilqa/blog.html` + `blog/` → VigilQA blog index + 14 posts; branding updated SentinelFlux → VigilQA throughout; company-name exceptions preserved
- `website/vigilqa/docs/` → docs moved from docs-site/; all internal links updated to /vigilqa/docs/ prefix; stale CNAME removed
- `website/blog.html` → company-level stub linking to product blogs
- All 35+ supporting pages updated: `/#modules` → `/vigilqa/#modules`, blog → `/vigilqa/blog`, docs → `/vigilqa/docs/`

---

## Previous Work (2026-06-04) — 01d18e2

### Remove all SpecVault GitHub links — repo made private
- `specvault/index.html`: nav GitHub → Contact mailto; hero "View on GitHub" → "Request Access" mailto; CTA "GitHub — MIT" → "Request Access"; footer GitHub → Contact; "Open Source" feature card → "Self-Hostable"; MIT stack tag → "Self-hostable"
- `portfolio.html`: removed GitHub button from SpecVault card; "MIT Open Source" tag → "Self-hostable"
- `index.html`: ecosystem section GitHub link removed, just "Learn more →" remains

---

## Previous Work (2026-06-04) — c0e3977

### SpecVault product landing page + portfolio update
- `website/specvault/index.html` — standalone product landing page: hero, 3-step how-it-works, 6-card feature grid (version history, breaking change detection, email alerts, CI/CD integration, API tokens, open source), stack section, CTA, footer; links to `specvault.sentinelflux.in` and GitHub
- `portfolio.html` — SentinelFlux + SpecVault now side-by-side featured cards (not col-span-2 SentinelFlux alone); SentinelFlux description: 9 modules, correct stack tags (FastAPI/Alpine.js/HTMX, not React/TypeScript); hero bio updated to mention both products; SpecVault card links to product page + live app + GitHub
- `index.html` — ecosystem section SpecVault card "Learn more →" now links to `/specvault/`; GitHub link kept separately

---

## Previous Work (2026-06-04) — 55e4de0

### Add SpecVault ecosystem section
- New "The SentinelFlux Ecosystem" section above the footer
- Two cards side-by-side: SentinelFlux (current, indigo) + SpecVault (companion, violet)
- SpecVault card links to github.com/mayuresh49/sentinelflux-specvault
- Establishes cross-product narrative on the marketing site

---

## Previous Work (2026-06-03) — 8127f4b

### Add compliance-reports.html module doc page
- New `website/modules/compliance-reports.html` — teal colour scheme, animated demo
- Demo: framework config panel, run aggregation metrics, section-by-section PDF build animation, SOC 2 control coverage table, "ready" state with download button
- Homepage module card `<div>` → `<a>` with correct href wired
- Follows exact structure/pattern of bug-tracker.html

---

## Previous Work (2026-06-03) — c82b8bc

### Add Compliance Reports as module #9
- Module card grid: added 9th card (teal/shield icon, "Pro" badge) for Compliance Reports
- Metrics bar: 8 → 9 testing modules counter
- Modules subtitle: "Eight" → "Nine testing modules"
- Pricing: Trial ("All 9"), Pro ("Compliance Reports — SOC 2, ISO 27001, GDPR, 3/month"), Enterprise ("Unlimited + branded PDF")
- Chatbot: updated module count + added entry #9 to the modules list response
- OG meta description: 8 → 9 modules

---

## Previous Work (2026-06-02) — b73d29c

### Minor portfolio copy + hook fix
- Contact CTA: removed "senior/staff" — profile is VP/Director level
- Post-push hook updated to skip firing on `chore(context):` commits (breaks the loop)

---

## Previous Work (2026-06-02) — 90140d3

### Minor portfolio copy fix
- Texnovate Solutions: final bullet wording — "Built web applications in .NET and jQuery; authored complex MS SQL stored procedures for an advertising product; managed deployments."

---

## Previous Work (2026-06-02) — ef5c75d + cert fixes

### Portfolio major update from resume PDF + cert number fix
- Hero: stronger executive tagline (14+ yrs), resume PDF download button added
- peopleHum: AWS→Hetzner migration, 35% regression reduction, Quantic Panelist, Kafka/Redis/ES, iOS/Kotlin/Ionic
- IBM: richer role-split bullets (Principal QA vs Sr QA MaaS360)
- Skills: Spring Boot, Kotlin, Swift, Kafka, Redis, Elasticsearch, Ionic, OWASP ZAP, SOC2, Serenity BDD, IaC
- Awards section: new dedicated section with 3 linked cards
- Certifications: added PMP Training, Agentic AI Workflows, OWASP ZAP, Serenity BDD
- University: full name Punyashlok Ahilyadevi Holkar Solapur University
- ISO 9001:2015 cert number updated: C-2026-XXXXX → C-2026-58593

---

## Previous Work (2026-06-02) — ab4a756

### Portfolio certifications upgraded with verified PDF data
- Replaced flat tag-style certs with card grid (issuer + date + cert number)
- ISTQB CTFL: #ITB-CTFL-0092941, Sep 2018, Indian Testing Board
- Lean Six Sigma Black Belt: #C-2024-57597, Apr 2024, IMC / CPD UK / CSSC USA
- ISO 9001:2015 Lead Auditor: #C-2026-XXXXX, May 2026, IMC / CPD UK (A038236)

---

## Previous Work (2026-06-02) — b6cfc79

### Portfolio page — website/portfolio.html
- New standalone portfolio page at sentinelflux.in/portfolio for job applications
- Profile photo (mayuresh-photo.png) added to website root
- Sections: Hero (photo, name, tagline, contact links), Experience timeline, Featured Projects, Skills grid, Education & Certifications, Contact CTA
- Experience covers full 13+ year career: SentinelFlux (Apr 2026–Present), peopleHum (2020–2026, 5-step promotion ladder), IBM (2015–2020), AFour Technologies (2012–2015), Texnovate Solutions (2011–2012)
- peopleHum card includes linked award badge (Excellence in QE Transformation HRTech, Digital QA Show 2026) and linked speaker badge ("Quality at Scale", Mar 2026)
- Certifications: ISTQB CTFL, Lean Six Sigma Black Belt (ICBB), ISO 9001:2015 Lead Auditor, ML Foundations, Playwright certs, Git
- Education: IIIT Bangalore PG Applied AI & Agentic AI (Dec 2026), Solapur University BE CS (2007–2011)
- All role title arrows consistently junior → senior

---

## Previous Work

### Docs served at sentinelflux.in/docs/ (420f58f + 2606adc, 2026-05-28)
- GitHub Pages can only serve one domain per repo — subdomain would require a separate repo
- Deploy workflow now merges `website/` (root) + `docs-site/` (`_build/docs/`) before publishing to gh-pages
- All docs paths updated: NAV hrefs, script src, mobile header links, docs landing page card links
- All marketing site links updated from `https://docs.sentinelflux.in` to `/docs/` (nav, mobile nav, footer, chat widget Q&A)
- Workflow triggers on changes to `website/**` OR `docs-site/**`
- No GoDaddy DNS change needed — docs live at `sentinelflux.in/docs/`

---

## Older Previous Work

### Complete docs site + CLI ref removal + Impact section (f7847d1)
- 38 static HTML pages under `docs-site/` covering Getting Started, Core Concepts, Modules, Agents, Platform, CI/CD Integration, Configuration, Troubleshooting
- Removed all CLI references from marketing site (code block, walkthrough slides, FAQ, JS TITLES)
- Added Impact section: 4 stat cards + before/after comparison

### Pricing: Starter free tier → 14-day free trial (b40465c)
- Removed Starter (self-hosted, forever free) tier — codebase exposure risk
- Replaced with Free Trial card: 14 days, full Pro access, no CC required

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

### Pricing: Starter free tier → 14-day free trial (b40465c)
- Removed Starter (self-hosted, forever free) tier — codebase exposure risk
- Replaced with Free Trial card: 14 days, full Pro access, no CC required

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

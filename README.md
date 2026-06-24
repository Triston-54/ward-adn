# The Ward — ADN Nursing Study Suite

A professional, teaching-first nursing education web application built for the Associate Degree Nursing (ADN) program at **New River Community and Technical College**.

## Philosophy

- **Teaching-first** — Every calculation and concept shows the "why" and derivation
- **Verified & sourced** — Traceable references with visible "Verify Source" on key facts
- **Interactive** — Word builders, step-by-step calculators, flashcards, NCLEX-style practice
- **Static-first** — Deploy once, share a link; students need only a browser
- **Long-term companion** — Modular design that grows through NURS 145–245 and beyond

## Quick Start — Static Site (Recommended)

The Ward is a **fully static** ADN study site. Students open a URL in any browser — **no Python, no install, no server.**

### Share with students (primary path)

1. Deploy to **Vercel** or **Netlify** (see [Deployment](#deployment) below).
2. Copy your live URL (e.g. `https://ward-adn.vercel.app`).
3. Send the link — students bookmark it and study from phone, tablet, or laptop.

All module content loads from `/data/content/*.json` in the browser. Progress is stored in **localStorage** on each device.

New students should start with **[How to Use The Ward](/how-to-use.html)** for a recommended study workflow and NCLEX strategy.

---

## Deployment

The Ward deploys as a **static site** from the project root. A build step renders HTML from Jinja templates; no Node.js or database is required.

### Prerequisites

- GitHub (or GitLab) repository containing this project
- Python **3.10+** on the build host (Vercel and Netlify provide this automatically)
- Build dependency: **Jinja2** only (`requirements-build.txt`)

### Deploy to Vercel

1. Push this repository to GitHub.
2. Go to [vercel.com/new](https://vercel.com/new) and **Import** your repository.
3. Vercel reads `vercel.json` automatically:
   - **Install command:** `pip install -r requirements-build.txt`
   - **Build command:** `python scripts/build_static_html.py`
   - **Output directory:** `.` (project root)
4. Click **Deploy**.
5. After deploy, verify these URLs on your live domain:

| URL | Expected |
|-----|----------|
| `/` | Dashboard |
| `/how-to-use` | Student guide (clean URL rewrite) |
| `/modules/terminology` | Medical Terminology module |
| `/nclex-prep` | NCLEX Prep Center |
| `/data/content/terminology.json` | JSON content (200, `application/json`) |

**Optional:** Add a custom domain under Project Settings → Domains.

### Deploy to Netlify

1. Push this repository to GitHub.
2. Go to [app.netlify.com/start](https://app.netlify.com/start) and **Import** your repository.
3. Netlify reads `netlify.toml` automatically:
   - **Build command:** `python scripts/build_static_html.py`
   - **Publish directory:** `.`
   - **Python version:** 3.11 (set in `[build.environment]`)
4. Click **Deploy site**.
5. Run the same verification URLs as Vercel (Netlify redirects extensionless paths via `netlify.toml`).

### Local preview (instructors / developers)

```bash
pip install -r requirements-build.txt   # first time only
python scripts/build_static_html.py     # rebuild HTML from templates
python -m http.server 8000
```

Open **http://127.0.0.1:8000** — same experience as the live site.

### End-to-end smoke test

With the local server running on port 8777:

```bash
python -m http.server 8777
python scripts/test_static_e2e.py
```

Expect **OVERALL: PASS** with all HTML pages, JSON content, and deploy configs validated.

### Install as App (PWA)

On the deployed site, open in Chrome or Edge → click the install icon in the address bar. Cached pages work offline via `sw.js`.

---

## Legacy Python Server (optional — development only)

The FastAPI backend (`run.py`) remains for API development and content auditing. **Not required** for the static study site or for sharing with students.

```bash
pip install -r requirements.txt   # full server deps
python run.py                     # http://127.0.0.1:8000
```

<details>
<summary>Windows desktop shortcut (local install — not needed for deployed link)</summary>

For offline/local use without deploying:

1. Install [Python 3.10+](https://www.python.org/downloads/) with **Add Python to PATH**.
2. Run **`create_desktop_shortcut.bat`** in the project folder.
3. Launch via the **The Ward** desktop icon (`launch_ward.bat` also works).

| Problem | Fix |
|---------|-----|
| "Python was not found" | Reinstall Python with **Add Python to PATH** |
| Port already in use | Close other copies of The Ward or restart |
</details>

## Modules

| Module | Status | Features |
|--------|--------|----------|
| **Dashboard** | ✅ Ready | Curriculum map, module launcher, NCLEX hub, How to Use guide |
| **Medical Terminology** | ✅ Full MVP | Word builder, searchable database, flashcards, NCLEX practice |
| **Microbiology** | ✅ Starter | Infection chain, concepts, Gram stain, flashcards, practice |
| **NURS 145 Dosage** | ✅ Starter | SymPy calculators, IV drip, pediatric/geriatric, practice |
| **NURS 146 Health Assessment** | ✅ Full MVP | Head-to-toe, SOAP/SBAR, flashcards, red flag drill |
| **NURS 147 Mental Health** | ✅ Phase 1 | Therapeutic communication, safety screening, suicide risk drill |
| **Pathophysiology** | ✅ New | Disease cascades, compare/contrast, scenarios, flashcards, NCLEX practice |
| **NURS 148 Maternal-Child** | ✅ New | Antepartum through peds, complications drill, safety red flags, NCLEX practice |
| **Medical-Surgical Nursing** | ✅ New | Adult health concepts, disease processes, NCLEX practice |
| **Maternal-Newborn Nursing** | ✅ New | Antepartum through newborn care, complications drill |
| **Pediatric Nursing** | ✅ New | Growth milestones, immunizations, pediatric safety |
| **NCLEX Prep** | ✅ New | Cross-module practice, rationales, clinical judgment drills |

## Key Features

- **Verify Source** — Every fact links to nursing textbooks, NCLEX plan, CDC, Open RN
- **Progress Tracking** — Flashcard ratings and NCLEX missed-question review stored in browser localStorage
- **Export** — Download flashcards as Markdown study guides
- **Command Palette** — Press `Ctrl+K` (or `Cmd+K`) for quick navigation
- **Mobile-first** — Responsive design optimized for phone, tablet, and desktop

## Project Structure

```
WARD/
├── index.html               # Built dashboard (deploy root)
├── how-to-use.html          # Student study guide
├── modules/*.html           # Built module pages
├── nclex-prep.html          # NCLEX prep hub
├── sw.js                    # PWA service worker (root scope)
├── vercel.json / netlify.toml
├── scripts/
│   ├── build_static_html.py # Jinja2 → static HTML (build step)
│   └── test_static_e2e.py   # Deployment smoke tests
├── static/                  # CSS, JS, images, manifest.json
├── data/content/            # Verified JSON (served at /data/content/)
├── app/                     # Jinja templates (source) + legacy FastAPI
├── requirements-build.txt   # Build only: jinja2
├── requirements.txt         # Full server deps (optional)
└── run.py                   # Legacy local server launcher
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+K` / `Cmd+K` | Command palette |
| `Escape` | Close modals |

## Content Sources

All content is verified against:

- New River CTC ADN curriculum outcomes
- NCLEX-RN Test Plan (NCSBN, 2023)
- Open RN Nursing OER textbooks
- CDC Infection Control Guidelines
- Standard nursing references (Ehrlich & Schroeder, Ogden & Fluharty)

## Development

```bash
# Rebuild static HTML after template or content changes
python scripts/build_static_html.py

# Content quality pass (rationales, pediatrics expansion)
python scripts/content_quality_pass.py
python scripts/final_production_pass.py

# Local preview
python -m http.server 8000
```

## License

Built for personal educational use. Content references are cited to their original sources.
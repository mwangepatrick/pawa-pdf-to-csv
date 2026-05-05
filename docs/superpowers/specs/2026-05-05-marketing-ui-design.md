# DataDrop — Marketing UI Design Spec

**Date:** 2026-05-05  
**Status:** Approved  
**Scope:** Add a marketing landing page to the existing PDF-to-CSV tool, rebrand as DataDrop

---

## 1. Overview

The current app is a purely functional PDF-to-CSV converter with no branding or marketing presence. This spec defines a marketing-oriented UI enhancement that adds a landing page before the existing tool, introduces the DataDrop brand identity, and makes the overall experience more compelling for both cold visitors and returning users.

The existing tool flow (upload → processing → result → email) is preserved intact. The landing page wraps around it.

---

## 2. Brand Identity

**Product name:** DataDrop  
**Tagline:** "Drop your PDF. Get your data."  
**Secondary tagline:** "PDF tables to CSV. In seconds."  
**Color accent:** Purple (`#a78bfa` / `#7c3aed`)  
**Domain aesthetic:** Modern, clean, no-nonsense — minimal UI chrome, maximum focus on the tool  

### Logo treatment
- Wordmark only: `Data` in body color + `Drop` in purple accent (`#a78bfa`)  
- Font weight: 900, letter-spacing: -2px  
- No icon required at this stage  
- Size: `clamp(42px, 8vw, 72px)` in the hero  

---

## 3. Theme System

The app must support both dark and light themes:

- **Default:** Detect system preference via `window.matchMedia('(prefers-color-scheme: dark)')`
- **Toggle:** A floating pill button (`☀ Light` / `☾ Dark`) fixed at `top: 20px; right: 24px`
- **Implementation:** CSS custom properties on `:root` and `[data-theme="light"]`, toggled via `document.documentElement.setAttribute('data-theme', ...)`
- **Transition:** `transition: background 0.3s, color 0.3s` on `body` for smooth switching

### Dark theme palette
| Token | Value |
|-------|-------|
| `--bg` | `#08101f` |
| `--bg2` | `#0f1a2e` |
| `--text` | `#f1f5f9` |
| `--text2` | `#94a3b8` |
| `--accent` | `#a78bfa` |
| `--accent2` | `#7c3aed` |
| `--glow` | `rgba(167,139,250,0.18)` |

### Light theme palette
| Token | Value |
|-------|-------|
| `--bg` | `#f8fafc` |
| `--bg2` | `#f1f5f9` |
| `--text` | `#0f172a` |
| `--text2` | `#475569` |
| `--accent` | `#a78bfa` (same) |
| `--accent2` | `#7c3aed` (same) |
| `--glow` | `rgba(167,139,250,0.12)` |

---

## 4. Page Structure

The page is a single scrolling document. Sections in order:

```
[Theme toggle — fixed, top-right]
[1. Hero]
[2. How It Works]
[3. M-PESA Callout]
[4. Upload Tool]  ← existing React app embeds here
[5. Footer]
```

---

## 5. Section Designs

### 5.1 Hero

- **Full viewport height** (`min-height: 100vh`), flex-centered
- **Background:** `--bg` with two radial purple glow overlays (top-center and bottom-left) via `::before` / `::after` pseudo-elements — no image, pure CSS
- **Content (centered, stacked vertically):**
  1. Brand wordmark — `Data` + `Drop` (purple)
  2. Purple gradient divider bar (56px × 3px)
  3. Tagline: "Drop your PDF. Get your data." (`clamp(20px, 3.5vw, 28px)`, weight 700)
  4. Sub-copy: "Instant table extraction from any PDF — cleaned, formatted, and delivered as CSV to your inbox." (`16px`, `--text2`)
  5. CTA button: "Start converting ↓" — gradient pill (`#a78bfa` → `#7c3aed`), `14px 36px` padding, `border-radius: 32px`, `box-shadow: 0 0 28px rgba(167,139,250,0.35)`. Smooth-scrolls to `#tool` section on click.
  6. Trust badges row: "No account needed · Free to use · M-PESA ready · Max 20MB" — small dots + `--text3` text

### 5.2 How It Works

- **Background:** `--how-bg` (slightly different from hero for visual separation), top and bottom border in `--footer-border`
- **Padding:** `80px 24px`
- **Section label:** "HOW IT WORKS" — uppercase, `12px`, `2px` letter-spacing, accent color
- **Section title:** "Three steps. That's it." — `clamp(22px, 4vw, 30px)`, weight 800
- **Three step cards** in a CSS grid (3 columns on desktop, 1 on mobile ≤640px):
  - Numbered circle (gradient `#a78bfa → #7c3aed`, `44px`, weight 800)
  - Emoji icon
  - Step title (weight 700)
  - Step description (`13px`, `--text2`)
- **Steps:**
  1. Upload your PDF — "Drag & drop or browse. Any PDF with tables — bank statements, reports, invoices."
  2. We extract & clean — "Tables are pulled out, junk rows removed, and data formatted into clean CSV."
  3. CSV to your inbox — "Enter your email and receive the file instantly — ready for Excel or Google Sheets."
- Subtle gradient line connecting the step numbers (desktop only, `::before` on `.steps`)

### 5.3 M-PESA Callout

- **Background:** `--mpesa-bg` (dark green tint in dark mode, `#f0fdf4` in light), bordered top and bottom in green
- **Padding:** `72px 24px`
- **Layout:** 2-column grid on desktop (copy left, visual right), single column on mobile
- **Left — copy:**
  - Badge pill: "🇰🇪 M-PESA" — green tint background, green border, uppercase
  - Title: "Built for M-PESA Statements" — `clamp(20px, 3.5vw, 26px)`, weight 800
  - Description: explains the problem (messy PDFs) and the solution (automatic cleaning)
  - Feature list (4 items with green ✓ circles):
    - Removes summary & balance rows automatically
    - Strips unnecessary noise columns
    - Outputs clean transaction rows only
    - Ready for reconciliation in seconds
- **Right — live data preview:**
  - Dark card with monospace font
  - Mini table showing sample M-PESA rows
  - Struck-through rows = removed (Opening Balance, Transaction Charges, Closing Balance)
  - Green rows = kept (actual transactions)
  - Caption: "Strikethrough rows removed automatically"

### 5.4 Upload Tool

- **Background:** `--bg` (same as hero — anchors the tool in the main brand space)
- **Padding:** `80px 24px`
- **Section label + title:** "GET STARTED / Convert your PDF now"
- **Upload zone:** Dashed border (`--upload-border`), `border-radius: 20px`, `48px 32px` padding, hover state darkens background and changes border to solid accent
- **Content:** PDF emoji icon, "Drag & drop your PDF here", sub-copy with constraints, "Choose File" button (gradient)
- **This section has the anchor `id="tool"`** — the CTA in the hero scrolls here
- **The existing React app** replaces the static upload zone mock at build time — the landing page shell wraps the React root

### 5.5 Footer

- Top border in `--footer-border`, `28px` padding
- Centered DataDrop wordmark (smaller, `18px`)
- Sub-copy: "Free PDF table extractor · No account required · © 2026"

---

## 6. Architecture & Integration

### Option A — Landing page as a new HTML shell (recommended)

Replace `frontend/index.html` with the new marketing page. The tool section contains `<div id="root"></div>` — React still mounts to `#root` as today, but `#root` is now nested inside the `#tool` section (a `<section>` with `id="tool"`) rather than directly in `<body>`. The `#tool` anchor is what the hero CTA scrolls to; `#root` is what React mounts into.

**Changes required:**
- `frontend/index.html` — replace with full marketing page HTML (hero, how-it-works, M-PESA section, tool section containing `<div id="root"></div>`, footer)
- `frontend/src/index.css` — add CSS custom properties for both themes, theme toggle styles, and all landing page section styles
- `frontend/src/main.tsx` — no change (still mounts to `#root`)
- `frontend/src/App.tsx` — no change (existing tool logic unchanged)
- Theme toggle script — small inline `<script>` in `index.html` (runs before React hydration to avoid flash of wrong theme)

**Why this approach:** Zero changes to the React component tree. The marketing content is pure HTML/CSS in the shell, which is static and fast. The React app only handles the interactive tool section it already owns.

### Theme toggle timing
The theme detection script must run **synchronously in `<head>`** (before `<body>` renders) to prevent flash of wrong theme (FOUT):

```html
<script>
  const d = window.matchMedia('(prefers-color-scheme: dark)').matches;
  document.documentElement.setAttribute('data-theme', d ? 'dark' : 'light');
</script>
```

The toggle button and interactive script can load normally at end of body.

---

## 7. Responsive Behaviour

| Breakpoint | Changes |
|-----------|---------|
| > 960px | Full 3-column steps grid, 2-column M-PESA layout |
| 640px–960px | Steps grid: 1 column, M-PESA: 1 column, hero font scales via clamp |
| < 640px | Everything single column, hero padding reduced, trust badges wrap |

---

## 8. What Does NOT Change

- All React components (`UploadZone`, `Progress`, `Result`, `TurnstileWidget`) — untouched
- All API logic and polling behaviour — untouched  
- Backend — untouched
- Turnstile CAPTCHA integration — untouched
- M-PESA statement cleaning logic — untouched (already in backend)
- Build config (`vite.config.ts`) — untouched

---

## 9. Out of Scope

- SEO / meta tags / Open Graph — not in this spec
- Analytics / tracking — not in this spec
- Multiple pages / routing — still a single-page app
- Animations beyond existing CSS transitions and hover states
- A custom domain or deployment changes

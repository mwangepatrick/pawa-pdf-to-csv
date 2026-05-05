# DataDrop Marketing UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a marketing landing page (hero → how-it-works → M-PESA callout → tool) wrapping the existing React PDF-to-CSV tool, and introduce the DataDrop brand with a system-aware dark/light theme toggle.

**Architecture:** The marketing page lives in `frontend/index.html` as a static HTML shell with inline CSS and a tiny theme-detection script in `<head>`. React mounts into `#root` inside the tool section — no routing changes, no new components. `App.tsx` is simplified to remove its own hero panel (now redundant since the landing page owns branding). Theme CSS variables defined in `index.html` are global and cascade into React components.

**Tech Stack:** React 19, TypeScript, Vite 8, custom CSS (no framework), Vitest + React Testing Library.

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `frontend/index.html` | Replace | Marketing shell: hero, how-it-works, M-PESA, tool section with `#root`, footer, all landing CSS, theme toggle |
| `frontend/src/index.css` | Modify | Remove conflicting gradient background; add `var(--text)` fallback for React components |
| `frontend/src/App.tsx` | Modify | Remove redundant `.hero-panel`; render `.workspace-panel` directly |
| `frontend/src/App.css` | Modify | Remove two-column grid; make workspace a single centered panel |
| `frontend/src/App.test.tsx` | Create | Assert hero-panel is gone, workspace-panel is rendered |

---

## Task 1: Establish a green baseline

**Files:**
- Read: `frontend/src/index.css`
- Read: `frontend/src/App.tsx`
- Read: `frontend/index.html`

- [ ] **Step 1: Run the full test suite**

```bash
cd frontend && npm test -- --run
```

Expected: all tests pass. Note the count — every subsequent task must preserve it. If any test is already failing, fix it before proceeding.

---

## Task 2: Update index.css — remove conflicting background

The current `:root` sets a radial-gradient background on the `html` element and hardcodes `color-scheme: dark`. These conflict with the landing page's own section backgrounds and theme system. Strip them out and add a `var(--text)` fallback so React components inherit the theme colour once it's defined by the landing page.

**Files:**
- Modify: `frontend/src/index.css`

- [ ] **Step 1: Replace the entire content of `frontend/src/index.css`**

```css
:root {
  font-family: "Segoe UI Variable", "Segoe UI", "Helvetica Neue", Arial, sans-serif;
  color: var(--text, #e2e8f0);
}

* {
  box-sizing: border-box;
}

html {
  min-height: 100%;
}

body {
  min-height: 100vh;
  margin: 0;
  background: transparent;
}

button,
input {
  font: inherit;
}

button {
  cursor: pointer;
}
```

Changes from current: removed `color-scheme: dark`, removed the `radial-gradient` / `linear-gradient` background on `:root`, changed `color` to `var(--text, #e2e8f0)` so it inherits from the landing page's CSS custom properties once loaded (falling back to the existing dark colour until then).

- [ ] **Step 2: Run tests**

```bash
cd frontend && npm test -- --run
```

Expected: same count, all pass.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/index.css
git commit -m "refactor: remove hardcoded background from index.css, use CSS var for text color"
```

---

## Task 3: Update App.tsx — remove redundant hero panel

The current `App.tsx` renders a two-column layout: a `.hero-panel` (branding + steps) on the left and `.workspace-panel` (the tool) on the right. The landing page now owns all branding and how-it-works content, making the `.hero-panel` redundant. Reduce App to render the `.workspace-panel` directly.

**Files:**
- Modify: `frontend/src/App.tsx`
- Create: `frontend/src/App.test.tsx`

- [ ] **Step 1: Create the failing test**

Create `frontend/src/App.test.tsx`:

```tsx
import { render } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import App from './App';

vi.mock('./api/client', () => ({
  uploadPdf: vi.fn(),
  pollStatus: vi.fn(),
  sendEmail: vi.fn(),
}));

vi.mock('./components/TurnstileWidget', () => ({
  default: () => <div data-testid="turnstile-mock" />,
}));

describe('App layout', () => {
  it('does not render a hero-panel', () => {
    render(<App />);
    expect(document.querySelector('.hero-panel')).toBeNull();
  });

  it('renders the workspace-panel', () => {
    render(<App />);
    expect(document.querySelector('.workspace-panel')).not.toBeNull();
  });
});
```

- [ ] **Step 2: Run the new test to confirm it fails**

```bash
cd frontend && npm test -- --run src/App.test.tsx
```

Expected: FAIL — `.hero-panel` is present in the current render.

- [ ] **Step 3: Replace the return block in App.tsx**

The return block starts at line 111 (`return (`). Replace everything from `return (` to the closing `);` with:

```tsx
  return (
    <section className="workspace-panel" aria-live="polite">
      {state.step === "upload" && (
        <UploadZone onFileSelected={handleFileSelected} />
      )}

      {state.step === "processing" && (
        <Progress
          filename={state.filename}
          pagesProcessed={state.status?.pages_processed ?? null}
          totalPages={state.status?.total_pages ?? null}
        />
      )}

      {state.step === "result" && (
        <Result
          filename={state.data.filename}
          rowCount={state.data.row_count ?? 0}
          totalPages={state.data.total_pages ?? 0}
          jobId={state.jobId}
          emailState={state.emailState}
          onReset={handleReset}
          onSendEmail={handleSendEmail}
        />
      )}

      {state.step === "error" && (
        <div className="error-panel">
          <div className="error-badge">Conversion stopped</div>
          <h2>{state.message}</h2>
          <p>
            Try another PDF or rerun the same file with text extraction if the document is text-heavy.
          </p>
          {state.message.includes("No tables found") && state.file && (
            <button
              type="button"
              className="secondary-button"
              onClick={() => startUpload(state.file!, true)}
            >
              Try text extraction instead
            </button>
          )}
          <button type="button" className="primary-button" onClick={handleReset}>
            Upload a different file
          </button>
        </div>
      )}
    </section>
  );
```

Everything above `return (` (all the state, hooks, and handlers) stays identical.

- [ ] **Step 4: Run all tests**

```bash
cd frontend && npm test -- --run
```

Expected: all pass, including the new App.test.tsx.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/App.tsx frontend/src/App.test.tsx
git commit -m "refactor: remove redundant hero-panel from App, landing page owns branding"
```

---

## Task 4: Update App.css — single centered workspace

With `.hero-panel` gone, the two-column `.app-layout` grid is unused. Replace the top of `App.css` with a single centered workspace style. The rest of the file (upload zone, progress, result, error panel styles) is unchanged.

**Files:**
- Modify: `frontend/src/App.css`

- [ ] **Step 1: Replace lines 1–45 of App.css**

These are the `.app-shell`, `.app-layout`, `.hero-panel`, `.workspace-panel`, and their `::before` blocks. Replace them with:

```css
.workspace-panel {
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(148, 163, 184, 0.18);
  background: rgba(8, 15, 30, 0.72);
  backdrop-filter: blur(18px);
  box-shadow: 0 24px 80px rgba(2, 6, 23, 0.38);
  border-radius: 28px;
  padding: 28px;
  width: min(560px, calc(100vw - 32px));
  margin: 0 auto;
}

.workspace-panel::before {
  content: "";
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at top left, rgba(59, 130, 246, 0.22), transparent 34%),
    radial-gradient(circle at bottom right, rgba(14, 165, 233, 0.12), transparent 32%);
  pointer-events: none;
}
```

Then delete the `.hero-kicker`, `.hero-title`, `.hero-copy`, `.hero-step-grid`, `.hero-step`, `.hero-step-index`, `.hero-step-title`, `.hero-step-copy`, `.hero-note` rule blocks that follow (they are dead code — those elements are no longer rendered). Keep everything from `.upload-zone` onwards untouched.

- [ ] **Step 2: Run tests**

```bash
cd frontend && npm test -- --run
```

Expected: all pass. CSS changes don't affect Vitest component tests.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/App.css
git commit -m "refactor: simplify App.css to single centered workspace panel"
```

---

## Task 5: Replace index.html with the full marketing landing page

The core task. The new `index.html` is the complete marketing shell. Note that `<script type="module" src="/src/main.tsx"></script>` must remain — Vite uses it to bundle the React app.

**Files:**
- Replace: `frontend/index.html`

- [ ] **Step 1: Replace the entire content of `frontend/index.html`**

```html
<!doctype html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="UTF-8" />
  <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>DataDrop — PDF tables to CSV</title>

  <!-- Theme detection: runs synchronously to prevent flash of wrong theme -->
  <script>
    (function () {
      var prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      document.documentElement.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
    })();
  </script>

  <style>
    /* ── CSS Custom Properties ── */
    :root,
    [data-theme="dark"] {
      --bg: #08101f;
      --how-bg: #0b1525;
      --text: #f1f5f9;
      --text2: #94a3b8;
      --text3: #475569;
      --accent: #a78bfa;
      --accent2: #7c3aed;
      --glow: rgba(167, 139, 250, 0.18);
      --section-border: rgba(255, 255, 255, 0.06);
      --toggle-bg: rgba(255, 255, 255, 0.06);
      --toggle-border: rgba(255, 255, 255, 0.1);
      --toggle-text: #94a3b8;
      --mpesa-bg: #071a0f;
      --mpesa-border: rgba(74, 222, 128, 0.2);
      --mpesa-text: #4ade80;
      --mpesa-sub: #86efac;
      --mpesa-card: rgba(0, 0, 0, 0.25);
      --step-bg: #0f1a2e;
      --step-border: rgba(167, 139, 250, 0.12);
    }

    [data-theme="light"] {
      --bg: #f8fafc;
      --how-bg: #f1f5f9;
      --text: #0f172a;
      --text2: #475569;
      --text3: #94a3b8;
      --glow: rgba(167, 139, 250, 0.12);
      --section-border: rgba(0, 0, 0, 0.06);
      --toggle-bg: rgba(0, 0, 0, 0.04);
      --toggle-border: rgba(0, 0, 0, 0.1);
      --toggle-text: #64748b;
      --mpesa-bg: #f0fdf4;
      --mpesa-border: rgba(22, 163, 74, 0.2);
      --mpesa-text: #15803d;
      --mpesa-sub: #166534;
      --mpesa-card: rgba(0, 0, 0, 0.04);
      --step-bg: #ffffff;
      --step-border: rgba(124, 58, 237, 0.1);
    }

    /* ── Reset & Base ── */
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    html { min-height: 100%; scroll-behavior: smooth; }
    body {
      font-family: "Segoe UI Variable", "Segoe UI", "Helvetica Neue", Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
      transition: background 0.3s, color 0.3s;
      min-height: 100vh;
    }

    /* ── Theme Toggle ── */
    .theme-toggle {
      position: fixed;
      top: 20px;
      right: 24px;
      z-index: 200;
      background: var(--toggle-bg);
      border: 1px solid var(--toggle-border);
      color: var(--toggle-text);
      font-size: 13px;
      font-family: inherit;
      padding: 6px 14px;
      border-radius: 20px;
      cursor: pointer;
      backdrop-filter: blur(8px);
      transition: opacity 0.15s;
    }
    .theme-toggle:hover { opacity: 0.75; }

    /* ── Hero ── */
    .hero {
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      text-align: center;
      padding: 80px 24px 60px;
      position: relative;
      overflow: hidden;
    }
    .hero::before {
      content: '';
      position: absolute;
      top: -120px; left: 50%; transform: translateX(-50%);
      width: 700px; height: 700px;
      background: radial-gradient(circle, var(--glow) 0%, transparent 65%);
      pointer-events: none;
    }
    .hero::after {
      content: '';
      position: absolute;
      bottom: -80px; left: 20%;
      width: 350px; height: 350px;
      background: radial-gradient(circle, rgba(124, 58, 237, 0.08) 0%, transparent 65%);
      pointer-events: none;
    }
    .brand {
      font-size: clamp(42px, 8vw, 72px);
      font-weight: 900;
      letter-spacing: -2px;
      line-height: 1;
      color: var(--text);
      position: relative;
      z-index: 1;
    }
    .brand-accent { color: var(--accent); }
    .brand-divider {
      width: 56px;
      height: 3px;
      background: linear-gradient(90deg, var(--accent), var(--accent2));
      border-radius: 3px;
      margin: 20px auto;
      position: relative;
      z-index: 1;
    }
    .hero-tagline {
      font-size: clamp(20px, 3.5vw, 28px);
      font-weight: 700;
      color: var(--text);
      line-height: 1.35;
      position: relative;
      z-index: 1;
    }
    .hero-sub {
      font-size: 16px;
      color: var(--text2);
      margin-top: 12px;
      max-width: 420px;
      line-height: 1.6;
      position: relative;
      z-index: 1;
    }
    .hero-cta {
      margin-top: 32px;
      display: inline-block;
      background: linear-gradient(135deg, var(--accent), var(--accent2));
      color: #fff;
      font-size: 16px;
      font-weight: 700;
      padding: 14px 36px;
      border-radius: 32px;
      border: none;
      font-family: inherit;
      cursor: pointer;
      box-shadow: 0 0 28px rgba(167, 139, 250, 0.35);
      transition: transform 0.15s, box-shadow 0.15s;
      position: relative;
      z-index: 1;
    }
    .hero-cta:hover {
      transform: translateY(-2px);
      box-shadow: 0 0 36px rgba(167, 139, 250, 0.5);
    }
    .trust-badges {
      display: flex;
      gap: 20px;
      margin-top: 28px;
      justify-content: center;
      flex-wrap: wrap;
      position: relative;
      z-index: 1;
    }
    .trust-badge {
      font-size: 13px;
      color: var(--text3);
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .trust-badge::before {
      content: '';
      display: inline-block;
      width: 5px;
      height: 5px;
      border-radius: 50%;
      background: var(--accent);
      opacity: 0.6;
    }

    /* ── Section shared ── */
    .section-label {
      text-align: center;
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 2px;
      text-transform: uppercase;
      color: var(--accent);
      margin-bottom: 12px;
    }
    .section-title {
      text-align: center;
      font-size: clamp(22px, 4vw, 30px);
      font-weight: 800;
      color: var(--text);
      margin-bottom: 48px;
      letter-spacing: -0.5px;
    }

    /* ── How It Works ── */
    .how {
      background: var(--how-bg);
      padding: 80px 24px;
      border-top: 1px solid var(--section-border);
      border-bottom: 1px solid var(--section-border);
    }
    .steps {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 20px;
      max-width: 840px;
      margin: 0 auto;
    }
    .step {
      background: var(--step-bg);
      border: 1px solid var(--step-border);
      border-radius: 16px;
      padding: 28px 20px;
      text-align: center;
    }
    .step-num {
      width: 44px;
      height: 44px;
      border-radius: 50%;
      background: linear-gradient(135deg, var(--accent), var(--accent2));
      color: #fff;
      font-size: 16px;
      font-weight: 800;
      display: flex;
      align-items: center;
      justify-content: center;
      margin: 0 auto 14px;
      box-shadow: 0 0 14px var(--glow);
    }
    .step-icon { font-size: 24px; margin-bottom: 10px; }
    .step-title { font-size: 15px; font-weight: 700; color: var(--text); margin-bottom: 6px; }
    .step-desc { font-size: 13px; color: var(--text2); line-height: 1.5; }

    /* ── M-PESA Callout ── */
    .mpesa {
      background: var(--mpesa-bg);
      border-top: 1px solid var(--mpesa-border);
      border-bottom: 1px solid var(--mpesa-border);
      padding: 72px 24px;
    }
    .mpesa-inner {
      max-width: 840px;
      margin: 0 auto;
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 48px;
      align-items: center;
    }
    .mpesa-badge {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: rgba(74, 222, 128, 0.1);
      border: 1px solid rgba(74, 222, 128, 0.25);
      color: var(--mpesa-text);
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 1.5px;
      text-transform: uppercase;
      padding: 5px 12px;
      border-radius: 20px;
      margin-bottom: 16px;
    }
    .mpesa-title {
      font-size: clamp(20px, 3.5vw, 26px);
      font-weight: 800;
      color: var(--text);
      line-height: 1.3;
      letter-spacing: -0.5px;
      margin-bottom: 14px;
    }
    .mpesa-desc {
      font-size: 15px;
      color: var(--text2);
      line-height: 1.65;
      margin-bottom: 20px;
    }
    .mpesa-features { list-style: none; display: flex; flex-direction: column; gap: 10px; }
    .mpesa-features li {
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 14px;
      color: var(--mpesa-sub);
    }
    .mpesa-features li::before {
      content: '✓';
      color: var(--mpesa-text);
      font-weight: 700;
      font-size: 12px;
      min-width: 20px;
      height: 20px;
      background: rgba(74, 222, 128, 0.12);
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }
    .mpesa-visual {
      background: var(--mpesa-card);
      border: 1px solid var(--mpesa-border);
      border-radius: 14px;
      padding: 18px;
      font-family: 'Courier New', monospace;
      font-size: 11px;
      overflow: hidden;
    }
    .mpesa-visual-label {
      font-size: 10px;
      font-weight: 700;
      letter-spacing: 1px;
      text-transform: uppercase;
      color: var(--mpesa-text);
      margin-bottom: 12px;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .mpesa-visual-label::before {
      content: '';
      display: inline-block;
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: var(--mpesa-text);
      flex-shrink: 0;
    }
    .mpesa-table { width: 100%; border-collapse: collapse; }
    .mpesa-table th {
      font-size: 9px;
      color: var(--mpesa-text);
      text-align: left;
      padding: 4px 6px;
      border-bottom: 1px solid var(--mpesa-border);
      letter-spacing: 0.5px;
      text-transform: uppercase;
    }
    .mpesa-table td {
      font-size: 9px;
      color: var(--mpesa-sub);
      padding: 5px 6px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.03);
    }
    .mpesa-table tr.removed td { text-decoration: line-through; opacity: 0.3; }
    .mpesa-caption { margin-top: 10px; font-size: 9px; color: var(--mpesa-text); opacity: 0.6; }

    /* ── Tool Section ── */
    .tool-section { padding: 80px 24px; text-align: center; }

    /* ── Footer ── */
    footer {
      border-top: 1px solid var(--section-border);
      padding: 28px 24px;
      text-align: center;
    }
    .footer-brand { font-size: 18px; font-weight: 800; color: var(--text); letter-spacing: -0.5px; }
    .footer-copy { font-size: 12px; color: var(--text3); margin-top: 6px; }

    /* ── Responsive ── */
    @media (max-width: 640px) {
      .steps { grid-template-columns: 1fr; }
      .mpesa-inner { grid-template-columns: 1fr; gap: 28px; }
      .hero { padding: 100px 20px 48px; }
      .trust-badges { gap: 12px; }
    }
  </style>
</head>
<body>

  <button class="theme-toggle" id="themeToggle">☀ Light</button>

  <!-- HERO -->
  <section class="hero">
    <div class="brand">Data<span class="brand-accent">Drop</span></div>
    <div class="brand-divider"></div>
    <div class="hero-tagline">Drop your PDF.<br>Get your data.</div>
    <p class="hero-sub">Instant table extraction from any PDF — cleaned, formatted, and delivered as CSV to your inbox.</p>
    <button class="hero-cta" onclick="document.getElementById('tool').scrollIntoView({behavior:'smooth'})">Start converting ↓</button>
    <div class="trust-badges">
      <span class="trust-badge">No account needed</span>
      <span class="trust-badge">Free to use</span>
      <span class="trust-badge">M-PESA ready</span>
      <span class="trust-badge">Max 20MB</span>
    </div>
  </section>

  <!-- HOW IT WORKS -->
  <section class="how">
    <div class="section-label">How it works</div>
    <div class="section-title">Three steps. That's it.</div>
    <div class="steps">
      <div class="step">
        <div class="step-num">1</div>
        <div class="step-icon">📄</div>
        <div class="step-title">Upload your PDF</div>
        <p class="step-desc">Drag &amp; drop or browse. Any PDF with tables — bank statements, reports, invoices.</p>
      </div>
      <div class="step">
        <div class="step-num">2</div>
        <div class="step-icon">⚡</div>
        <div class="step-title">We extract &amp; clean</div>
        <p class="step-desc">Tables are pulled out, junk rows removed, and data formatted into clean CSV.</p>
      </div>
      <div class="step">
        <div class="step-num">3</div>
        <div class="step-icon">📧</div>
        <div class="step-title">CSV to your inbox</div>
        <p class="step-desc">Enter your email and receive the file instantly — ready for Excel or Google Sheets.</p>
      </div>
    </div>
  </section>

  <!-- M-PESA CALLOUT -->
  <section class="mpesa">
    <div class="mpesa-inner">
      <div>
        <div class="mpesa-badge">🇰🇪 M-PESA</div>
        <div class="mpesa-title">Built for<br>M-PESA Statements</div>
        <p class="mpesa-desc">M-PESA statement PDFs are notoriously messy — summary rows, transaction noise, and columns you never asked for. DataDrop knows the format and cleans it automatically.</p>
        <ul class="mpesa-features">
          <li>Removes summary &amp; balance rows automatically</li>
          <li>Strips unnecessary noise columns</li>
          <li>Outputs clean transaction rows only</li>
          <li>Ready for reconciliation in seconds</li>
        </ul>
      </div>
      <div class="mpesa-visual">
        <div class="mpesa-visual-label">Cleaned output preview</div>
        <table class="mpesa-table">
          <thead>
            <tr><th>Date</th><th>Details</th><th>Amount</th></tr>
          </thead>
          <tbody>
            <tr class="removed"><td>—</td><td>Opening Balance</td><td>—</td></tr>
            <tr><td>01/05</td><td>Sent to John M.</td><td>-1,200</td></tr>
            <tr><td>02/05</td><td>Received from Wanjiku</td><td>+5,000</td></tr>
            <tr class="removed"><td>—</td><td>Transaction Charges</td><td>—</td></tr>
            <tr><td>03/05</td><td>Buy Goods - Naivas</td><td>-890</td></tr>
            <tr class="removed"><td>—</td><td>Closing Balance</td><td>—</td></tr>
          </tbody>
        </table>
        <div class="mpesa-caption">Strikethrough rows removed automatically</div>
      </div>
    </div>
  </section>

  <!-- TOOL SECTION — React mounts into #root here -->
  <section class="tool-section" id="tool">
    <div class="section-label">Get started</div>
    <div class="section-title">Convert your PDF now</div>
    <div id="root"></div>
  </section>

  <!-- FOOTER -->
  <footer>
    <div class="footer-brand">Data<span class="brand-accent">Drop</span></div>
    <p class="footer-copy">Free PDF table extractor · No account required · © 2026</p>
  </footer>

  <script type="module" src="/src/main.tsx"></script>

  <script>
    // Theme toggle — syncs label with the theme set by the inline <head> script
    var toggle = document.getElementById('themeToggle');

    function getTheme() {
      return document.documentElement.getAttribute('data-theme');
    }
    function setTheme(theme) {
      document.documentElement.setAttribute('data-theme', theme);
      toggle.textContent = theme === 'dark' ? '☀ Light' : '☾ Dark';
    }

    setTheme(getTheme()); // sync label on load

    toggle.addEventListener('click', function () {
      setTheme(getTheme() === 'dark' ? 'light' : 'dark');
    });
  </script>

</body>
</html>
```

- [ ] **Step 2: Run all tests**

```bash
cd frontend && npm test -- --run
```

Expected: all pass. JSDOM does not render `index.html`, so existing component tests are unaffected.

- [ ] **Step 3: Start the dev server and visually verify**

```bash
cd frontend && npm run dev
```

Open `http://localhost:5173` and check each item:

- [ ] Hero visible: large DataDrop wordmark, purple accent on "Drop", divider, tagline, sub-copy, CTA button, trust badges
- [ ] Theme toggle (top-right): clicking switches between dark and light correctly
- [ ] System preference honoured on first load (no flash of wrong theme)
- [ ] "Start converting ↓" button smooth-scrolls to the upload zone
- [ ] How It Works: 3 step cards with purple numbered circles
- [ ] M-PESA section: green badge, copy, feature list, data preview table with struck-through rows
- [ ] Tool section: React upload zone renders below the section title
- [ ] Upload a test PDF: processing → result → email flow works end-to-end
- [ ] Footer: DataDrop wordmark + copy
- [ ] On mobile width (< 640px): steps stack to 1 column, M-PESA stacks to 1 column

- [ ] **Step 4: Commit**

```bash
git add frontend/index.html
git commit -m "feat: add DataDrop marketing landing page with hero, how-it-works, and M-PESA callout"
```

---

## Task 6: Final verification

- [ ] **Step 1: Run full test suite**

```bash
cd frontend && npm test -- --run
```

Expected: all tests pass, count matches Task 1 baseline plus the 2 new App.test.tsx tests.

- [ ] **Step 2: Type-check and build**

```bash
cd frontend && npm run build
```

Expected: build succeeds, no TypeScript errors, output in `frontend/dist/`.

---

## Spec Coverage

| Spec requirement | Task |
|-----------------|------|
| Brand: DataDrop, purple accent, wordmark logo | Task 5 |
| Hero: centered logo above tagline, no navbar | Task 5 |
| CTA: smooth-scrolls to `#tool` | Task 5 |
| Trust badges row | Task 5 |
| Theme: system preference default (FOUT-safe) | Task 5 (inline `<head>` script) |
| Theme: manual toggle | Task 5 (toggle button + end-of-body script) |
| How It Works: 3 step cards | Task 5 |
| M-PESA: dedicated callout section | Task 5 |
| M-PESA: data preview table with struck-through rows | Task 5 |
| Upload tool: `#root` inside `#tool` section | Task 5 |
| Footer | Task 5 |
| App.tsx hero-panel removed | Task 3 |
| App.css: single centered workspace | Task 4 |
| index.css: conflicting gradient removed | Task 2 |
| React components (UploadZone, Progress, Result, TurnstileWidget) untouched | Tasks 2–5 |
| Backend untouched | Out of scope — correct |
| Responsive ≤ 640px | Task 5 (CSS media query) |

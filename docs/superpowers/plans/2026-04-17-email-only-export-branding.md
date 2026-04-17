# Email-Only Export And Branding Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove direct CSV download from the browser UI, deliver exports only by email, add Cloudflare Turnstile to the email-send action, and refresh the landing page with a stronger branded experience without interrupting upload or conversion.

**Architecture:** Keep the current FastAPI + React + Vite split, but change the contract so the browser never receives or renders a direct download token. The backend remains responsible for conversion, emailing, and download-link generation, while the frontend becomes a single-page branded flow that shows upload progress, completion state, and an email-only delivery prompt protected by Turnstile. Add lightweight server-side abuse controls so email delivery is not reliant on Turnstile alone.

**Tech Stack:** Python 3.12, FastAPI, aiosqlite, pdfplumber, pandas, httpx, python-dotenv, React, TypeScript, Vite, Cloudflare Turnstile, Nginx, Docker Compose, pytest, pytest-asyncio

---

## File Map

### Backend

| File | Responsibility |
|------|-----------------|
| `backend/app/config.py` | Load env vars, including Turnstile keys and email throttling settings |
| `backend/app/db.py` | Persist jobs and any new email-attempt metadata used for cooldowns/throttling |
| `backend/app/main.py` | API routes, response shaping, Turnstile enforcement, email send orchestration |
| `backend/app/email_service.py` | Provider-specific email delivery for Brevo/Mailjet |
| `backend/requirements.txt` | Python dependency list |
| `backend/tests/test_api.py` | Integration tests for upload/status/email/download behavior |
| `backend/tests/test_email_service.py` | Email provider tests |
| `backend/tests/test_config.py` | dotenv/config loading tests |
| `backend/tests/test_turnstile.py` | New tests for Turnstile verification and email gating |

### Frontend

| File | Responsibility |
|------|-----------------|
| `frontend/src/App.tsx` | Branded landing page plus upload/progress/result state orchestration |
| `frontend/src/App.css` | Layout, typography, and branded visual system |
| `frontend/src/index.css` | Global base theme and background styling |
| `frontend/src/api/client.ts` | API client shape, including email token submission |
| `frontend/src/components/UploadZone.tsx` | Upload interaction, validation, and helper copy |
| `frontend/src/components/Progress.tsx` | Conversion progress UI |
| `frontend/src/components/Result.tsx` | Completion UI, email form, Turnstile widget, resend/error state |
| `frontend/src/components/TurnstileWidget.tsx` | Dedicated wrapper for Cloudflare Turnstile script/widget lifecycle |
| `frontend/vite.config.ts` | Dev proxy and any required environment passthrough |
| `frontend/vitest.config.ts` | Frontend test runner config |
| `frontend/src/test/setup.ts` | Test setup for DOM assertions |
| `frontend/src/App.test.tsx` | Landing-page branding smoke test |
| `frontend/src/components/Result.test.tsx` | Email-only result state smoke test |
| `frontend/package.json` | Test script and dev dependencies |

### Infrastructure and Docs

| File | Responsibility |
|------|-----------------|
| `nginx/nginx.conf` | Reverse proxy, static serving, and optional CSP headers for Turnstile |
| `.env.example` | Required config template for local and Docker runs |
| `README.md` | Developer instructions and email-only flow notes |
| `docs/superpowers/specs/2026-04-17-email-only-export-branding-design.md` | Approved product/spec baseline |

---

## Task 1: Add Turnstile and abuse-control config to the backend

**Files:**
- Modify: `backend/app/config.py`
- Modify: `backend/requirements.txt`
- Modify: `.env.example`
- Modify: `README.md`

- [ ] **Step 1: Write a config test that proves `.env` loading and new keys exist**

Add to `backend/tests/test_config.py`:

```python
def test_config_exposes_turnstile_and_throttle_settings():
    import app.config as config

    assert hasattr(config, "TURNSTILE_SECRET_KEY")
    assert hasattr(config, "TURNSTILE_VERIFY_URL")
    assert hasattr(config, "EMAIL_SEND_COOLDOWN_SECONDS")
    assert hasattr(config, "EMAIL_SEND_MAX_ATTEMPTS")
```

- [ ] **Step 2: Run the test and verify it fails**

Run:

```bash
cd backend
python -m pytest tests/test_config.py -q
```

Expected: fail because the new config symbols do not exist yet.

- [ ] **Step 3: Implement the config keys and dependency**

Update `backend/app/config.py`:

```python
TURNSTILE_SITE_KEY = os.getenv("TURNSTILE_SITE_KEY", "")
TURNSTILE_SECRET_KEY = os.getenv("TURNSTILE_SECRET_KEY", "")
TURNSTILE_VERIFY_URL = os.getenv("TURNSTILE_VERIFY_URL", "https://challenges.cloudflare.com/turnstile/v0/siteverify")
EMAIL_SEND_COOLDOWN_SECONDS = int(os.getenv("EMAIL_SEND_COOLDOWN_SECONDS", "60"))
EMAIL_SEND_MAX_ATTEMPTS = int(os.getenv("EMAIL_SEND_MAX_ATTEMPTS", "5"))
```

Update `backend/requirements.txt`:

```text
python-dotenv==1.0.1
```

Update `.env.example`:

```env
TURNSTILE_SITE_KEY=your-turnstile-site-key
TURNSTILE_SECRET_KEY=your-turnstile-secret-key
EMAIL_SEND_COOLDOWN_SECONDS=60
EMAIL_SEND_MAX_ATTEMPTS=5
```

- [ ] **Step 4: Run the config tests and verify they pass**

Run:

```bash
cd backend
python -m pytest tests/test_config.py -q
```

Expected: PASS.

- [ ] **Step 5: Update developer docs**

Add a short note in `README.md` that:

- `.env` is auto-loaded from the repo root
- `TURNSTILE_SITE_KEY` is public and used only by the frontend
- `TURNSTILE_SECRET_KEY` must never be exposed to the browser
- email sending should fail closed if Turnstile is unavailable

- [ ] **Step 6: Commit**

```bash
git add backend/app/config.py backend/requirements.txt .env.example README.md backend/tests/test_config.py
git commit -m "feat: add Turnstile and email throttle config"
```

---

## Task 2: Enforce email-only delivery in the backend

**Files:**
- Modify: `backend/app/main.py`
- Modify: `backend/app/db.py`
- Modify: `backend/app/email_service.py`
- Create: `backend/tests/test_turnstile.py`
- Modify: `backend/tests/test_api.py`

- [ ] **Step 1: Write failing tests for email gating and no-token exposure**

Create `backend/tests/test_turnstile.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_email_rejects_missing_turnstile_token(client):
    response = await client.post("/api/email", json={"job_id": "job-1", "email": "user@example.com"})
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_email_rejects_invalid_turnstile_token(client):
    with patch("app.main.verify_turnstile", AsyncMock(return_value=False)):
        response = await client.post(
            "/api/email",
            json={"job_id": "job-1", "email": "user@example.com", "turnstile_token": "bad"},
        )
    assert response.status_code == 400
    assert response.json()["detail"] == "Turnstile verification failed."
```

Add to `backend/tests/test_api.py` a check that the completed status response no longer contains `download_token`.

```python
assert "download_token" not in data
```

- [ ] **Step 2: Run the tests and verify they fail**

Run:

```bash
cd backend
python -m pytest tests/test_turnstile.py tests/test_api.py -q
```

Expected: fail until the new route contract and verification helper exist.

- [ ] **Step 3: Implement Turnstile verification and throttled email sending**

In `backend/app/main.py`, extend the request model:

```python
class EmailRequest(BaseModel):
    job_id: str
    email: str
    turnstile_token: str
```

Add a small verification helper:

```python
async def verify_turnstile(token: str, remote_ip: str | None = None) -> bool:
    if not config.TURNSTILE_SECRET_KEY:
        return False

    async with httpx.AsyncClient() as client:
        response = await client.post(
            config.TURNSTILE_VERIFY_URL,
            data={
                "secret": config.TURNSTILE_SECRET_KEY,
                "response": token,
                "remoteip": remote_ip or "",
            },
            timeout=10,
        )
    payload = response.json()
    return bool(payload.get("success"))
```

Change `/api/email` to:

- verify Turnstile before any provider call
- reject missing/invalid tokens with `400`
- enforce a per-job or per-email cooldown before sending
- keep the job context intact on failures

Update the status endpoint so it no longer returns `download_token` to the browser:

```python
if job["status"] == "completed":
    result["row_count"] = job["row_count"]
```

Keep `/api/download/{token}` intact for emailed links.

If you need a per-job resend throttle, store the last successful email attempt in the jobs table or a tiny side table in `backend/app/db.py`. Prefer the smallest schema change that supports a 60-second cooldown and a finite attempt count.

- [ ] **Step 4: Run the tests and verify they pass**

Run:

```bash
cd backend
python -m pytest tests/test_turnstile.py tests/test_api.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/main.py backend/app/db.py backend/app/email_service.py backend/tests/test_turnstile.py backend/tests/test_api.py
git commit -m "feat: gate email delivery with Turnstile"
```

---

## Task 3: Replace the browser result flow with email-only completion UX

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/components/Result.tsx`
- Create: `frontend/src/components/TurnstileWidget.tsx`
- Modify: `frontend/src/components/UploadZone.tsx`
- Modify: `frontend/src/components/Progress.tsx`
- Modify: `frontend/package.json`
- Create: `frontend/vitest.config.ts`
- Create: `frontend/src/test/setup.ts`
- Create: `frontend/src/App.test.tsx`
- Create: `frontend/src/components/Result.test.tsx`

- [ ] **Step 1: Add the frontend test harness and write failing smoke tests**

Update `frontend/package.json`:

```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "test": "vitest run"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^6.6.3",
    "@testing-library/react": "^16.1.0",
    "@types/jsdom": "^21.1.7",
    "jsdom": "^25.0.1",
    "vitest": "^2.1.8"
  }
}
```

Create `frontend/vitest.config.ts`:

```ts
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    setupFiles: "./src/test/setup.ts",
  },
});
```

Create `frontend/src/test/setup.ts`:

```ts
import "@testing-library/jest-dom";
```

Create `frontend/src/App.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import App from "./App";

test("renders branded landing copy", () => {
  render(<App />);
  expect(screen.getByRole("heading", { name: /pdf to csv/i })).toBeInTheDocument();
  expect(screen.getByText(/delivered by email/i)).toBeInTheDocument();
});
```

Create `frontend/src/components/Result.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import Result from "./Result";

test("does not render a direct download link", () => {
  render(
    <Result
      filename="invoice.pdf"
      rowCount={12}
      totalPages={3}
      jobId="job-1"
      onReset={() => {}}
      emailState="idle"
      onSendEmail={async () => {}}
    />
  );

  expect(screen.queryByRole("link", { name: /download/i })).toBeNull();
  expect(screen.queryByRole("button", { name: /download/i })).toBeNull();
});
```

- [ ] **Step 2: Run the tests and verify they fail**

Run:

```bash
cd frontend
npm run test
```

Expected: fail because the current `Result.tsx` still renders a direct download link and the harness is not configured yet.

- [ ] **Step 3: Implement the new flow and Turnstile widget**

Change `frontend/src/api/client.ts`:

```ts
export interface StatusResponse {
  job_id: string;
  status: "processing" | "completed" | "failed";
  filename: string;
  total_pages: number | null;
  pages_processed: number | null;
  row_count?: number;
  error?: string;
}

export async function sendEmail(jobId: string, email: string, turnstileToken: string): Promise<EmailResponse> {
  const res = await fetch(`${API_BASE}/email`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ job_id: jobId, email, turnstile_token: turnstileToken }),
  });
  ...
}
```

Replace `frontend/src/components/Result.tsx` so it:

- shows row count and page count
- shows email delivery status
- contains the email input
- renders the Turnstile widget
- does not render any download link
- resets the Turnstile widget on error

Suggested email-state shape:

```ts
type EmailState = "idle" | "sending" | "sent" | "error";
```

Create `frontend/src/components/TurnstileWidget.tsx` as a thin wrapper around the Cloudflare script with:

- site key from `VITE_TURNSTILE_SITE_KEY`
- callback for token changes
- explicit reset support after failures

Update `frontend/src/App.tsx`:

- keep upload/progress/result/error states
- remove any dependency on `download_token`
- keep the flow on one page
- make the result screen an email-delivery completion view

Improve `frontend/src/App.tsx` hero copy and layout so the upload screen feels branded and intentional:

- product title
- concise promise line
- upload CTA
- “delivered by email” reassurance
- short three-step explanation

Adjust `frontend/src/UploadZone.tsx` and `Progress.tsx` only as needed to match the new visual language. Do not add disruptive navigation or modal steps.

- [ ] **Step 4: Build and verify the frontend passes with no direct download UI**

Run:

```bash
cd frontend
npm run test
npm run build
```

Expected: PASS, and the result UI no longer contains a download link.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/App.tsx frontend/src/api/client.ts frontend/src/components/Result.tsx frontend/src/components/TurnstileWidget.tsx frontend/src/components/UploadZone.tsx frontend/src/components/Progress.tsx
git commit -m "feat: make result flow email-only with Turnstile"
```

---

## Task 4: Add the branded landing page and visual system

**Files:**
- Modify: `frontend/src/App.css`
- Modify: `frontend/src/index.css`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/UploadZone.tsx`
- Modify: `frontend/src/components/Progress.tsx`
- Modify: `frontend/src/components/Result.tsx`

- [ ] **Step 1: Add a landing-page branding smoke test**

Create `frontend/src/App.test.tsx` assertions that verify the hero copy and trust line render:

```tsx
expect(screen.getByText(/convert pdfs/i)).toBeInTheDocument();
expect(screen.getByText(/deliver csv securely by email/i)).toBeInTheDocument();
```

- [ ] **Step 2: Run the check and verify it fails if branding is absent**

Run:

```bash
cd frontend
npm run test
```

Expected: fail until the branded copy and layout are implemented.

- [ ] **Step 3: Implement the branded design**

Use a clear, premium-looking system:

- dark layered background with subtle gradients
- one accent color for primary actions
- display typography for the hero
- tighter card spacing
- a more deliberate upload panel
- a compact trust strip or “how it works” block

`frontend/src/App.css` should own the page layout and hero styling.
`frontend/src/index.css` should own the global page background, font stack, and reset.

Keep the upload interaction simple:

- drag and drop
- file picker
- immediate validation
- no extra screens

Keep the conversion result visually integrated with the landing page:

- same card language
- same accent color
- same spacing and typography scale

- [ ] **Step 4: Build and inspect the UI**

Run:

```bash
cd frontend
npm run build
npm run dev
```

Then inspect `http://localhost:5173` and confirm:

- landing page looks branded
- upload still works
- progress still shows
- result feels like a completion view, not a generic form

- [ ] **Step 5: Commit**

```bash
git add frontend/src/App.css frontend/src/index.css frontend/src/App.tsx frontend/src/components/UploadZone.tsx frontend/src/components/Progress.tsx frontend/src/components/Result.tsx
git commit -m "feat: add branded landing page and completion UI"
```

---

## Task 5: Harden the deployment surface and developer docs

**Files:**
- Modify: `nginx/nginx.conf`
- Modify: `README.md`
- Modify: `.env.example`
- Modify: `docker-compose.yml`

- [ ] **Step 1: Add a deployment check for Turnstile script loading and email-only copy**

Review that the docs mention:

- Turnstile is only used on `/api/email`
- the frontend should fail closed if Turnstile is unavailable
- the direct download link is not rendered in the browser

- [ ] **Step 2: Add or update CSP/proxy settings**

If the app is served behind Nginx, allow the Turnstile script and frames in a way that does not weaken the rest of the app. Prefer the narrowest possible CSP needed for Cloudflare Turnstile.

Example idea for `nginx/nginx.conf`:

```nginx
add_header Content-Security-Policy "default-src 'self'; script-src 'self' https://challenges.cloudflare.com; frame-src https://challenges.cloudflare.com; connect-src 'self' https://challenges.cloudflare.com;" always;
```

Only add this if it does not conflict with the existing app shell.

- [ ] **Step 3: Update docs and environment template**

`README.md` should explain:

- how to set `TURNSTILE_SITE_KEY` and `TURNSTILE_SECRET_KEY`
- that the email send is Turnstile-protected
- that users receive the CSV only through email
- that the UI does not expose a direct download action

`.env.example` should include:

```env
TURNSTILE_SITE_KEY=
TURNSTILE_SECRET_KEY=
EMAIL_SEND_COOLDOWN_SECONDS=60
EMAIL_SEND_MAX_ATTEMPTS=5
```

- [ ] **Step 4: Verify Docker and local startup**

Run:

```bash
cp .env.example .env
docker compose build
```

Expected: images build with the new env vars and dependencies.

- [ ] **Step 5: Commit**

```bash
git add nginx/nginx.conf README.md .env.example docker-compose.yml
git commit -m "docs: add Turnstile and email-only deployment notes"
```

---

## Task 6: Full verification pass

**Files:** none

- [ ] **Step 1: Run the backend test suite**

```bash
cd backend
python -m pytest -v
```

Expected: all tests pass, including the new Turnstile and no-token checks.

- [ ] **Step 2: Run the frontend build**

```bash
cd frontend
npm run build
```

Expected: build passes and the bundle contains no download CTA.

- [ ] **Step 3: Manually test the full flow**

Start both services:

```bash
cd backend
uvicorn app.main:app --reload --port 8000

cd frontend
npm run dev
```

Then verify in the browser:

1. Branded landing page renders correctly.
2. Upload still starts immediately.
3. Progress remains visible.
4. Result screen shows summary only.
5. No direct download link appears anywhere.
6. Turnstile gates email submission only.
7. Email delivery succeeds once Turnstile is solved.
8. Failure states remain inline and recoverable.

- [ ] **Step 4: Final commit if any fixes were needed**

```bash
git add -A
git commit -m "fix: complete email-only export and branding rollout"
```

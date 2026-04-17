# Email-Only Export And Branding Design

## Goal

Turn the current PDF-to-CSV web app into an email-delivery-first experience:

- Users can upload a PDF, watch conversion progress, and see completion status.
- The CSV export must not be directly downloadable from the frontend UI.
- The only user-visible delivery path for the CSV is via email.
- The landing page should feel polished, branded, and trustworthy without adding friction to the conversion flow.

This is a product and UX change first, with a supporting backend enforcement change to ensure the UI cannot expose a direct download link.

## Scope

### In scope

- Remove direct download affordances from the frontend.
- Keep progress and result states visible after upload.
- Preserve the existing email-send flow, but make it the only delivery path surfaced to users.
- Add a branded landing page with stronger visual identity and clearer messaging.
- Update backend responses so the frontend never needs the download token.
- Keep the experience uninterrupted: upload, progress, result, email confirmation.

### Out of scope

- Public authentication, login, or accounts.
- Paid plans, subscriptions, or gating by membership.
- A redesign of the CLI converter.
- Major changes to the PDF conversion logic.
- Rewriting the email providers beyond what is needed to support the current flow.

## Product Principles

1. The app should feel immediate. Upload should start conversion quickly and progress should be visible.
2. The app should feel secure. No CSV download link should appear in the browser UI.
3. The app should feel simple. The flow should stay on one page and not force navigation.
4. The app should feel branded. The first screen should look intentionally designed, not generic.
5. The app should feel resilient. If email sending fails, the user should see a recoverable state instead of losing their job.

## User Experience

### Landing page

The landing page should combine branding and task entry in one primary view:

- Prominent product name and short value proposition.
- One clear upload call to action.
- Supporting line that explains the CSV is delivered by email.
- Optional email field near the upload action so users can provide the delivery address before or during the conversion flow.
- A compact trust section that explains:
  - CSV delivery happens by email.
  - Files expire automatically.
  - The app does not show a direct download button.

### Conversion flow

The flow must remain uninterrupted:

1. User uploads a PDF.
2. UI switches to a progress state.
3. Backend converts the file.
4. UI switches to a result state.
5. Result state confirms the file is ready and that delivery is by email only.
6. If an email address is already available, the app sends the message automatically.
7. If not, the result state prompts for an email address without requiring the user to restart the upload.

### Result state

The result state should show:

- File name
- Rows extracted
- Pages processed
- Email delivery status
- Retry / resend controls if email fails

The result state should not show:

- A download button
- A raw download URL
- A visible token
- A clickable link that points at the CSV download endpoint

## Branding Direction

The visual direction should be a clean, modern utility with a confident identity.

### Brand personality

- Calm
- Precise
- Secure
- Modern
- A little premium, but not flashy

### Suggested tone of voice

- “Convert PDFs. Deliver CSV securely by email.”
- “Upload once, receive your CSV by email.”
- “No direct download link exposed in the browser.”

### Visual style

- Dark base with a subtle gradient or layered background.
- Strong single accent color for primary actions and status.
- Rounded cards with restrained shadows.
- Clean typography with a more intentional display font for headings and a practical sans-serif for body copy.
- Small, high-contrast status chips for upload, processing, and complete states.

### Landing page sections

1. Hero section with title, subtitle, upload CTA, and supporting copy.
2. Small “how it works” strip with three steps.
3. Security and privacy reassurance block.
4. Conversion result area that reuses the same visual language as the hero.

## Technical Design

### Frontend state model

The frontend should keep the existing app structure but change the result contract:

- `upload` state
- `processing` state
- `result` state
- `error` state

The `result` state should hold only the information needed for display and email actions:

- filename
- row count
- total pages
- email status
- any email error

It should not depend on a download token.

### API contract changes

The backend should continue to process the file and produce the CSV, but the browser-facing API should be adjusted so the frontend does not receive the direct download token.

Expected behavior:

- `/api/upload` still returns job metadata and processing state.
- `/api/status/{job_id}` returns progress and completion details, but not a direct download token.
- `/api/email` remains the mechanism that sends the download link to the user.
- `/api/download/{token}` remains available for emailed links, but the token must not be surfaced in the UI.

### Enforcement rule

The frontend must never render a download link or token. This should be enforced in two places:

- The frontend result UI should not include a download control.
- The backend status response should not provide the download token to the browser.

This ensures the download path is only available through email and not through the normal UI flow.

### Email delivery behavior

If the user supplies an email address early, the app should send the CSV link when the conversion completes.
If the user does not supply an email address upfront, the result view should ask for it without forcing the user to re-upload.

The email form should feel like part of the completion state, not a separate interruption.

## Accessibility And UX Quality

- Preserve keyboard navigation for upload and email fields.
- Maintain strong color contrast for action buttons and status text.
- Keep copy concise and explicit about what happens to the CSV.
- Do not add modal dialogs unless absolutely necessary.
- Make status changes obvious without requiring page navigation.

## Error Handling

The UI should handle these cases inline:

- Invalid file upload
- Conversion failure
- Email send failure
- Missing email address at completion time

Error states should keep the job context visible so the user can retry without starting over.

## Testing Strategy

### Backend tests

- Verify status responses do not expose the download token to the frontend.
- Verify the email route still sends a usable download link.
- Verify the download route remains functional for emailed tokens only.

### Frontend tests

- Verify the landing page renders the branded hero and upload CTA.
- Verify the result screen does not render any direct download link.
- Verify the result screen can send or resend the email.
- Verify the progress state still renders while conversion is in flight.

### Manual checks

- Upload a PDF and confirm the app stays on one page.
- Confirm the result state shows completion and email confirmation.
- Confirm there is no visible download button or token anywhere in the UI.
- Confirm the email contains the only user-facing download path.

## Acceptance Criteria

- Users can upload a PDF and see progress without interruption.
- Users can see the result summary after conversion.
- The frontend does not expose a direct CSV download link.
- The CSV is available to the user only through email delivery.
- The landing page looks intentionally branded and polished.
- The flow still works if the user enters email after conversion completes.
- The backend and frontend tests cover the no-direct-download behavior.

## Rollout Notes

- This should be delivered as a contained UI + API change, not a rewrite.
- The direct download route may remain in the backend for emailed access, but it must not be exposed in the normal UI flow.
- If there is any mismatch between the UI and backend contract, the backend contract wins for security.

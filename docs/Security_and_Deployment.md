# Security, Privacy and Deployment

## Default (recommended): local only

SMIT is designed to run on **one testing computer** with the server bound to `127.0.0.1`. Nothing is sent to third-party services, there is no telemetry, and all data live in `data/smit.db` (SQLite) and `data/outputs/`.

## Protections implemented

| Area | Protection |
|---|---|
| Identifying data | Emails stored only in `participant_contacts`; never in exports, analysis, reports, figures or the audit log. Duplicate emails detected through a peppered HMAC hash. |
| Pseudonymisation | Participants are identified by generated IDs (`P001`, `PILOT-001`). |
| Researcher access | Password login (`SMIT_ADMIN_PASSWORD`) → HMAC-signed bearer token (`SMIT_SECRET_KEY`), 12 h expiry, stored in `sessionStorage` (cleared when the tab closes). Failed logins are slowed. |
| Participant sessions | Random session token; server stores only its SHA-256 hash; trials can be written only with the token and only for trials in the server's own plan. |
| Contact access | Viewing or exporting contacts is audit-logged. |
| SQL injection | SQLAlchemy with bound parameters only. |
| Uploads | ≤ 15 MB; `.xlsx/.csv/.json` only; ZIP magic-byte check; macro-enabled workbooks rejected; XML parsed with `defusedxml`; formulas never evaluated and reported as errors; text starting with `= + - @` rejected in identifiers; synthetic data refused. |
| Exports | Leading formula characters neutralised (CSV/Excel injection). |
| Web | `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, `Cache-Control: no-store` for API; CORS limited to the local dev origin; React escapes all rendered text. |
| Withdrawal / deletion | Participants can stop and withdraw in-app; researchers can mark withdrawn/excluded (with reason) or permanently delete a participant and all their data (audit-logged without personal data). |

## Before real data collection

1. Copy `.env.example` to `.env`; set `SMIT_ADMIN_PASSWORD`, a random `SMIT_SECRET_KEY` and a random `SMIT_EMAIL_PEPPER`.
2. Use a computer account that only the research team can access; enable full-disk encryption (FileVault/BitLocker/LUKS).
3. Back up `data/smit.db` after each testing day with `scripts/backup_database.sh` to an encrypted drive.

## Data retention

Set the retention dates in *Settings* (shown in the consent form). At the end of the retention period: export the de-identified dataset needed for assessment, delete contacts (Participants → Delete or delete `data/smit.db`), and delete backups.

## Quick online access: Cloudflare quick tunnel (implemented)

`scripts/start_online.sh` keeps the app bound to `127.0.0.1` and publishes it through a free Cloudflare quick tunnel (`cloudflared`), giving a random `https://….trycloudflare.com` link. It refuses to start with default secrets, warns about short passwords, keeps the Mac awake, and stops the server when the window is closed. Data stay on the Mac; traffic is HTTPS and passes through Cloudflare. Researcher login locks for 15 minutes after 10 failed attempts. The link changes on every start, and quick tunnels have no uptime guarantee — suitable for a short student study, not for long-term hosting.

## If online testing is required

Online testing reduces timing control (different devices/browsers) and adds security obligations. Only do so with your institution's approval.

- Deploy behind HTTPS (reverse proxy such as Caddy or nginx with a valid certificate). Never expose port 8000 directly.
- Keep the researcher dashboard restricted (VPN, IP allow-list or HTTP basic auth at the proxy) in addition to the app password.
- Use PostgreSQL (`SMIT_DATABASE_URL`) with encrypted storage and automated encrypted backups.
- Set `SMIT_CORS_ORIGINS` to your exact origin.
- Update the consent text (data storage location, hosting provider) — participants must be told where data are stored.
- Record device and browser variability as a limitation; consider restricting to desktop browsers.

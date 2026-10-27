# AI-POS on Namecheap cPanel

Target: `aipos.sitndo.online`, in a **separate document root**. The root domain `sitndo.online` and its existing application/data must remain untouched.

## Verified repository state
`web/` is a static holding page plus a PHP 8-compatible **503 fail-closed placeholder** at `/api/`. It is **not** a functioning AI-POS backend. No production deployment, DNS changes, accounts, databases, or API keys are provisioned.

## Operator preflight (read-only)
In Namecheap cPanel, inspect **Domains → Create A New Domain** / **Subdomains**, **MultiPHP Manager** or **Select PHP Version**, **MySQL Databases**, **SSL/TLS Status**, and **Cron Jobs**. Names vary by cPanel version. Confirm PHP 8.1+ and PDO MySQL support; verify that a separate document root and HTTPS are available. Do not create/overwrite any existing root-domain files or database.

## Proposed architecture
- PHP request/response backend suitable for shared hosting (no resident Node.js/Python worker assumption).
- MariaDB/MySQL using separate database and restricted DB user.
- Server-side sessions, CSRF protection, passwordless/SSO identity integration only after callback and credential custody are designed.
- Role orchestration as **queued tasks**, dispatched by a bounded cron runner with explicit timeout, quotas, audit trails, and idempotency. Do not store ChatGPT account credentials or attempt to automate interactive ChatGPT accounts.
- Secrets stored outside public document root. Founder signing key **stays on Fedora**, never uploaded to cPanel.
- No automated deployment until independent acceptance and exact-SHA Founder approval; initial release remains blocked.

## Required before production
Confirm hosting features, create separate subdomain and DB with operator authorization, build and test real API/auth/queue/roles, verify six-role end-to-end acceptance, add backup/restore, audit and deployment rollback, then review the final candidate.

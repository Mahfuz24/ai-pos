# Domain deployment — aipos.sitndo.online

Founder-selected destination: `aipos.sitndo.online`. **No DNS, cPanel, live website, production database, or release configuration has been changed.**

## Scope
The `web/` folder is a static, no-JavaScript, no-login holding page. It is **not** the AI-POS application and must not be represented as a six-role product.

## Safe prerequisites
1. Verify domain ownership and hosting type through the operator's Namecheap/cPanel account without sharing passwords.
2. Create a dedicated subdomain document root, separate from `sitndo.online` and existing lead databases. Enforce HTTPS and check DNS propagation.
3. Confirm PHP/Node/Python runtime availability, database options, resource limits, cron/background worker support, and outbound HTTPS. Shared cPanel hosting may not support long-running workers.
4. Select and validate a compatible application architecture, user identity provider, server-side role execution, session protection, database migrations, backups and secrets custody.
5. Implement six-role end-to-end acceptance, threat-model checks, and independent release authorization before any real production deployment.

## Fail-closed rules
No automatic deployment workflow or credentials are included. Never place the local Founder key in cPanel, GitHub, or web root. Do not modify existing root-domain content. No production release until explicit approval for the exact candidate SHA and independent gate evidence.

# Reuni Project Security Rules

All future development on the Reuni platform MUST adhere strictly to the following security guidelines to prevent regressions and maintain a highly secure circular economy application.

---

## 1. Access Control & Authorization (Anti-IDOR)
- **Always Verify Ownership**: Never fetch or mutate objects from the database by ID alone without verifying ownership.
  - *Bad*: `item = Item.query.get(id)`
  - *Good*: `item = Item.query.filter_by(id=id, seller_id=current_user.id).first()`
- **Guarded Routes**: Ensure routes modifying or accessing sensitive resources (e.g., claiming items, sending messages, changing credentials) are protected with `@login_required` or `@verified_required` decorators.
- **Double-Sided Verification**: Verify both buyer and seller status before granting access to transaction-specific resources like chat threads or PIN verification.

---

## 2. Content Security Policy (CSP) & Script Sandboxing
- **Zero Inline JavaScript**: Do NOT write `<script>` blocks inside HTML templates. All JS must be modularized under `app/static/js/` (e.g., `common.js`, `auth.js`, `chat.js`).
- **No Inline Event Handlers**: Avoid `onclick=""`, `onchange=""`, etc. in HTML markup. Bind events using `addEventListener` in external JS files.
- **Strict script-src**: The CSP header enforces `script-src 'self'`. Inline scripts will fail to execute.
- **Nonce-secured inline styles**: Inline styles should be avoided; if absolutely necessary, they must utilize style nonces: `<style nonce="{{ csp_nonce }}">`.
- **Safe data injection**: Pass backend data to JS using secure HTML data attributes (e.g., `data-item-id="{{ item.id }}"`) or JSON script blocks (e.g., `<script type="application/json" id="category-weights">{{ category_weights | tojson | safe }}</script>`).

---

## 3. GDPR Compliance & Privacy (No PII in Logs)
- **Log Hashing**: Never write raw emails, names, or other Personally Identifiable Information (PII) to log files. 
- **SHA-256 Email Hashing**: For login attempts and audit logs, hash the email address using SHA-256:
  `hashed_email = hashlib.sha256(email.strip().lower().encode('utf-8')).hexdigest()[:16]`
- **Log by Database ID**: Identify users, listings, claims, and other entities in logs strictly by their database auto-increment IDs.
- **PII-Free Reprs**: Database model representations (`__repr__`) must never serialize sensitive properties like `email`, `name`, `phone`, or `title`.

---

## 4. Authentication, Session & Password Hardening
- **Generic Error Messages**: Login, password reset, register, and lock-out responses must return generic status messages (e.g., "Invalid email or password" or "Verification code sent") to prevent email/user enumeration.
- **Bcrypt DoS Prevention**: Limit password length to a maximum of 128 characters on all registration and reset forms.
- **Timing-Safe Verifications**: Use `secrets.compare_digest()` for string comparisons of security codes, PINs, or verification tokens to prevent side-channel timing attacks.
- **Session Regeneration**: Always clear the session (`session.clear()`) before authenticating a user to mitigate session fixation vulnerabilities.

---

## 5. General Security & API Quality
- **ORM-Only Database Queries**: Never construct raw SQL strings or concatenate variables in queries. Utilize SQLAlchemy parameterization.
- **Path/URL Escaping**: Always validate external redirects to prevent Open Redirects. Avoid concatenating raw query strings; use standard routing tools.
- **Host Header Hardening**: Use Gunicorn/ProxyFix configuration with environment-driven `BASE_URL` configs for absolute link generation (e.g. password resets).
- **Subresource Integrity (SRI)**: Any externally loaded CDN assets must include valid `integrity` hashes and `crossorigin="anonymous"` properties.

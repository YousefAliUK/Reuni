# Reuni Platform — Future Product Roadmap

This document serves as the project backlog for the Reuni circular economy platform. It tracks planned features, security hardening targets, and user experience enhancements.

---

## Upcoming Features Backlog

### 🏆 Campus & Global Leaderboards

A gamification layer to encourage carbon footprint reduction and waste diversion.

- **Campus Hall of Fame:** Displays top users ranked by carbon saved (`kg_saved_total`) at the local university level (e.g. Brookes or Oxford).
- **Grand Hall of Fame:** A global leaderboard ranking the top-performing students/partners across all campuses in the network.
- **Milestone Badges:** Award digital badges for milestones (e.g. "10kg Saved", "First Handshake").

#### Phase 2 — Leaderboard Enhancements (Post-Launch)

- **Achievement & Badge System:** Store a `badges` JSON column on `User`, populated during weekly/seasonal snapshot archival. Display earned badges on user profiles and send in-app + email notifications for new awards. Badge tiers to consider: weekly podium finishes (3rd, 2nd, 1st), seasonal champion, consecutive-week winner streak.
- **Cross-University Leaderboard Tab:** Aggregate `kg_saved` by `university_domain` to produce a university-vs-university ranking (no individual names — GDPR-safe). Controlled by `FEATURE_MULTI_UNIVERSITY` env flag.
- **Lazy Hall of Fame Snapshot Materialisation:** Currently, weekly snapshots are created by a cron job at 00:10 UTC (~10 minutes past midnight). For international universities in later timezones (e.g. UAE, UTC+4), this introduces up to a 4-hour display gap where the Hall of Fame does not yet show the just-completed week. The fix is a `maybe_archive_previous_week(university_domain, university_timezone)` utility function called at the top of the Hall of Fame route before rendering. If the previous week ended and no snapshot exists, it creates the snapshot inline (no emails — notifications remain cron-only to avoid race conditions on email sending). Unique constraint `(university_domain, week_start, rank)` acts as a natural mutex for concurrent requests; wrap in `try/except IntegrityError` in the route handler.
- **Leaderboard Opt-In Consent Flow:** A modal or settings toggle for students who want additional prominence (e.g. public profile link from leaderboard entry). Separate from the default opt-out toggle.
- **Profile Display Name Control:** Allow students to set a custom display name / alias for leaderboard appearances (distinct from their real account name), subject to moderation.
- **Content Moderation for Display Names:** Automated profanity/inappropriate name detection on account creation and name changes to ensure leaderboard entries are appropriate.

### 📊 ESG Report Exports (CSV/PDF)

Allows sustainability partners to download certified reports for official reporting.

- **CSV Export:** Download waste diversion statistics, kg saved, and CO₂e avoided per category.
- **Branded PDF Export:** A styled dashboard printout suitable for board meetings and ESG submissions.

### 🔒 Subject Access Request (GDPR Data Portability)

Allows users to download a copy of all personal data stored in compliance with UK GDPR.

- **Self-Service Export:** A button in User Settings generating a secure JSON file containing profile info, item histories, chat messages, and carbon statistics.

### ✉️ Notification Engine

Email alerts to close the loop on marketplace interactions.

- **New Message Alerts:** Notification emails when a user receives a new message in a chat thread.
- **PIN Handshake Updates:** Alerting both buyer and seller upon the initiation and completion of a physical exchange.

---

## Security & Operational Hardening

- [ ] Implement rate limiting on general API endpoints.
- [ ] Add session expiry checks and audit trails for admin events.

---

## Role Hierarchy Expansion — Partner Lead (University Admin)

### Background

The current role model (`admin`, `partner`, `student`) requires the Reuni admin to personally
invite every individual sustainability team member at every university. At scale across multiple
universities this is unworkable.

### Target Role Hierarchy

```
Reuni Admin (platform owner)
├── Onboards universities (creates UniversityConfig records)
├── Promotes one partner → Partner Lead per university
├── Emergency account actions (deactivate a Partner Lead who leaves)
├── Platform-wide feature flag control and maintenance mode
└── Cross-university visibility — the only role that sees all universities' data

Partner Lead (Head of Sustainability at each university)
├── Invites additional partners scoped to their own university email domain
├── Sets and edits Season dates (term start/end) for their university
├── Views their university's aggregated ESG stats and leaderboard data
└── Cannot read or modify any other university's data (enforced at query level)

Partner (sustainability team member)
└── Views partner dashboard, manages items, downloads reports

Student
└── Trades items, appears on leaderboard (if opted in)
```

### Implementation Approach

**Do not create a new `role` value.** Instead, add a boolean flag to `User`:

```python
is_university_manager = db.Column(db.Boolean, default=False, nullable=False)
```

A `partner` with `is_university_manager=True` IS the Partner Lead. This avoids adding a
fourth role string and scattering new role checks across every `current_user.role == ...`
guard in the codebase.

A new `@partner_lead_required` decorator would combine the existing `@partner_required`
check with `current_user.is_university_manager == True`.

### Partner Invite Scoping

When a Partner Lead generates an invite token, the token must be scoped to their own
`university_domain` (already stored on the User model). The invite registration route
validates that the registering email matches the token's domain. This prevents a Partner
Lead from Brookes from inviting someone from Oxford.

The existing `generate_partner_invite_token()` in `app/utils/tokens.py` already includes
`university_domain` in the payload — the change is gating token generation behind
`is_university_manager` rather than `role == 'admin'`.

### What the Reuni Admin Retains

- Only the Reuni admin can create `UniversityConfig` records (onboard new universities)
- Only the Reuni admin can promote a partner to Partner Lead (`is_university_manager=True`)
- Only the Reuni admin has cross-university query access (no `university_domain` filter)
- Only the Reuni admin can deactivate a Partner Lead

### When to Implement

Not needed until the platform expands to a second university with its own sustainability
team. For single-university operation (Brookes), the current `admin` + `partner` model is
sufficient — the admin invites partners directly. This item is relevant when a second
university is onboarded and their sustainability lead needs to self-manage their team.

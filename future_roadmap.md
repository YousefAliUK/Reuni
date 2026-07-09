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

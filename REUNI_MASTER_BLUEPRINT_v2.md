# REUNI — Master Design Blueprint v2.0
### Canonical specification. Supersedes all previous blueprint documents.
### Source: product_specification.md v1.3 · 13 June 2026
### For: Antigravity 2.0 / Google Stitch / any execution agent

---

## SECTION 0 — SKILL STACK & DESIGN RATIONALE

### Active Skills (layered in priority order)

| Layer | Skill | Why |
|---|---|---|
| Foundation | **`stitch-skill`** | Reuni is fundamentally a dashboard product — ESG partner portal, student dashboard, PIN state machine, admin panel. Modular component stitching is the dominant design challenge. |
| Execution | **`impeccable-skill`** | Two audiences (18–25 students + institutional sustainability officers) sharing one codebase demands pixel-perfect execution at every breakpoint. No slop tolerance. |
| Enforcement | **`brandkit`** | Token names, palette, and icon library are **committed decisions in the live codebase** — identity preservation wins over reinvention. |

### Design Atmosphere Calibration

| Dial | Student surfaces | Partner/Admin surfaces |
|---|---|---|
| **Density** | 5 / 10 — approachable, open | 7 / 10 — data-forward, institutional |
| **Variance** | 6 / 10 — asymmetric enough to feel human | 4 / 10 — restrained authority |
| **Motion** | 5 / 10 — purposeful on key moments | 3 / 10 — almost static |

### Physical Scene (design decisions are anchored here)
- **Student claiming an item:** Standing outside a campus building, one-handed, possibly nervous, comparing phones with a stranger. Needs: huge tap targets, minimal cognitive load, PIN digits legible in daylight.
- **Sustainability officer reading the ESG dashboard:** At a desk, on a laptop, preparing a quarterly report. Needs: precise numbers, printable layout, data they can copy-paste directly into Word.

### The Central Tension — Resolved
Reuni is pitched B2B (sustainability offices) but used B2C (students). Both audiences share one visual language. Register differences are expressed through **layout density and information hierarchy** — never through different colour palettes or components.

---

## SECTION 1 — DESIGN TOKEN MASTER MAP

> **Critical naming rule:** All tokens use `--color-*` prefix in the stylesheet. Never `--primary` alone — always `--color-primary`. This matches the live codebase convention.

```css
/* ============================================================
   REUNI DESIGN SYSTEM — CANONICAL TOKEN MAP v2.0
   Naming convention: --color-* for colour, --radius-* for shape
   Source: product_specification.md §2.3
   ============================================================ */

/* ─── Color Palette — Light Mode ─── */
--color-bg:               #F8FAFC;   /* Slate-50 — page canvas */
--color-surface:          #FFFFFF;   /* Cards, modals, sidebars */
--color-surface-raised:   #F1F5F9;   /* Slate-100 — nested surfaces, input fills, table alternates */
--color-border:           rgba(226, 232, 240, 0.7); /* 1px structural lines */

--color-ink-primary:      #0F172A;   /* Slate-900 — headlines, labels. Never pure #000000 */
--color-ink-secondary:    #475569;   /* Slate-600 — body text, descriptions */
--color-ink-tertiary:     #94A3B8;   /* Slate-400 — timestamps, metadata, placeholders */

--color-primary:          #0D9488;   /* Teal-600 — CTAs, links, kg_saved badges, primary actions */
--color-primary-hover:    #0F766E;   /* Teal-700 — hover/active state */
--color-primary-muted:    #CCFBF1;   /* Teal-100 — chip backgrounds, tag fills */

--color-accent:           #F97316;   /* Orange-500 — Claim buttons, urgency states, notifications */
--color-accent-hover:     #EA6C0A;   /* Orange-600 — hover state */
--color-accent-muted:     #FFF7ED;   /* Orange-50 — soft accent fills */

--color-danger:           #EF4444;   /* Red-500 — Delete, errors, late cancellation */
--color-danger-muted:     #FEF2F2;   /* Red-50 */

--color-success:          #22C55E;   /* Green-500 — completed transactions, verified badges */
--color-success-muted:    #F0FDF4;   /* Green-50 */

--color-warning:          #F59E0B;   /* Amber-500 — PIN expiry warnings, pending states */
--color-warning-muted:    #FFFBEB;   /* Amber-50 */

/* ─── Dark Mode Overrides ─── */
[data-theme="dark"] {
  --color-bg:              #0F172A;
  --color-surface:         #1E293B;
  --color-surface-raised:  #334155;
  --color-border:          rgba(51, 65, 85, 0.8);
  --color-ink-primary:     #F1F5F9;
  --color-ink-secondary:   #94A3B8;
  --color-ink-tertiary:    #475569;
  --color-primary:         #70B8AE;   /* Teal-300 — lightened for dark bg */
  --color-accent:          #FB923C;   /* Orange-400 */
  --color-danger:          #F87171;
  --color-success:         #4ADE80;
  --color-warning:         #FBBF24;
  --color-primary-muted:   rgba(13, 148, 136, 0.15);
  --color-accent-muted:    rgba(249, 115, 22, 0.12);
}

/* ─── Typography ─── */
--font-sans: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif;
--font-mono: 'JetBrains Mono', 'Fira Code', monospace;
/* Mono used exclusively for: kg values, PIN codes, timestamps, prices, counts */
/* Google Fonts load: Plus Jakarta Sans (wght@400;500;600;700;800) + JetBrains Mono (wght@400;500;600;700;800) */

--type-display:  clamp(1.875rem, 4vw, 2.625rem);  /* Page titles */
--type-title:    clamp(1.25rem, 2.5vw, 1.625rem);  /* Section headers */
--type-body-lg:  1.0625rem;   /* Lead body */
--type-body:     0.9375rem;   /* Default body — never below this */
--type-small:    0.8125rem;   /* Labels, metadata */
--type-micro:    0.6875rem;   /* Tags, timestamps — hard floor */

--track-display:  -0.025em;   /* Headlines — floor is -0.04em, never tighter */
--track-tight:    -0.015em;
--track-normal:   0em;
--track-wide:     0.05em;     /* ALL-CAPS labels only */

--lead-display:  1.15;
--lead-title:    1.3;
--lead-body:     1.65;        /* 65ch max line length on prose */

/* ─── Spatial Scale (8px base grid) ─── */
--space-1:   0.25rem;   /*  4px */
--space-2:   0.5rem;    /*  8px */
--space-3:   0.75rem;   /* 12px */
--space-4:   1rem;      /* 16px */
--space-5:   1.25rem;   /* 20px */
--space-6:   1.5rem;    /* 24px */
--space-8:   2rem;      /* 32px */
--space-10:  2.5rem;    /* 40px */
--space-12:  3rem;      /* 48px */
--space-16:  4rem;      /* 64px */

/* ─── Radius Scale ─── */
--radius-sm:   6px;     /* Tags, chips, status badges */
--radius-md:   10px;    /* Inputs, buttons — confirmed from spec */
--radius-lg:   12px;    /* Cards — confirmed from spec */
--radius-xl:   16px;    /* Modals, drawers — confirmed from spec */
--radius-full: 9999px;  /* Pills, avatars, toggle switches */

/* ─── Elevation ─── */
--shadow-card:   0 1px 3px rgba(0,0,0,0.06), 0 4px 16px rgba(0,0,0,0.04);
--shadow-raised: 0 4px 12px rgba(0,0,0,0.08), 0 12px 40px rgba(0,0,0,0.06);
--shadow-modal:  0 20px 60px rgba(0,0,0,0.15);

/* ─── Layout ─── */
--container-max:    1320px;
--container-pad:    clamp(1rem, 4vw, 2.5rem);
--sidebar-width:    240px;
--content-max-ch:   65ch;

/* ─── Touch Targets ─── */
--tap-min: 44px;   /* WCAG AA absolute minimum */

/* ─── Motion ─── */
--ease-out-expo:  cubic-bezier(0.16, 1, 0.3, 1);
--ease-spring:    cubic-bezier(0.34, 1.56, 0.64, 1);  /* Claims, confirmations, badge unlocks */
--dur-fast:       150ms;
--dur-normal:     250ms;
--dur-slow:       400ms;

/* ─── Z-Index Scale ─── */
/* base: 0 | sticky: 100 | dropdown: 200 | drawer: 300 | backdrop: 400 | modal: 500 | toast: 600 | tooltip: 700 */

/* ─── Icon Library ─── */
/* Google Material Symbols (outlined style) */
/* Import: https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined */
/* All decorative icons: aria-hidden="true" */
/* All interactive icons: descriptive aria-label on parent button */
/* Syntax: <span class="material-symbols-outlined" aria-hidden="true">search</span> */
```

---

## SECTION 2 — NAVIGATION SYSTEM

### Breakpoint Architecture
> **Single breakpoint: 1024px.** Below = mobile layout. At and above = desktop layout.
> Per spec §2.4a: "Mobile-first rule: breakpoint is 1024px, not 768px."

```
VIEWPORT < 1024px — MOBILE LAYOUT:
  - Fixed top bar (56px + safe-area-inset-top)
  - Fixed bottom tab bar (60px + safe-area-inset-bottom)  ← 4 tabs
  - Hamburger (☰) in top bar opens slide-in drawer (mirrors sidebar links)
  - NO left sidebar

VIEWPORT ≥ 1024px — DESKTOP LAYOUT:
  - Sticky top navbar (64px)
  - Fixed left sidebar (240px, authenticated users only)
  - NO bottom tab bar
```

---

### Desktop — Top Navbar

```
HEIGHT: 64px, sticky, z-index: 100
BACKGROUND: var(--color-surface)
BORDER: border-bottom 1px var(--color-border)

LAYOUT: flex, space-between, align-center

LEFT:
  Reuni logo mark (teal leaf/cycle SVG, 28px) + wordmark "Reuni" (Plus Jakarta Sans 700, 18px)
  No tagline. Logo links to /

RIGHT (unauthenticated):
  [Log in] ghost outline button → /auth/login
  [Register] var(--color-primary) fill button → /auth/register
  Gap: 8px. Both: 40px height, --radius-md

RIGHT (authenticated):
  Dark mode toggle: Material Symbol "light_mode"/"dark_mode", 20px icon, 36px button, ghost
  Notification bell:
    Material Symbol "notifications", 20px
    IF unread_count > 0:
      Badge: var(--color-accent) dot 16px diameter, --font-mono 10px 700 white
      Content: count (1–9) or "9+" if more
      Badge position: absolute, top-right of icon, -4px offset
      Pulse animation: scale(1) → scale(1.15) → scale(1), 2s infinite ease-in-out
    IF unread_count = 0: icon at --color-ink-tertiary, no badge
    On click: navigate to /notifications
  User avatar: initials circle 36px, var(--color-primary-muted) bg, var(--color-primary) text
    Opens dropdown on click

AVATAR DROPDOWN:
  var(--color-surface), var(--shadow-raised), --radius-lg, 200px wide
  Mount: scale(0.95) → scale(1) + opacity 0 → 1, 150ms, var(--ease-out-expo)
  Transform origin: top right
  Items (44px each, 16px padding):
    My Dashboard → /dashboard
    My Profile → /profile
    Settings → /settings
    [divider]
    ESG Dashboard → /partner/dashboard  [only if role=partner or role=admin]
    Admin Panel → /admin              [only if role=admin]
    [divider]
    Sign Out (var(--color-danger) text)
```

---

### Desktop — Left Sidebar (authenticated, ≥1024px)

```
WIDTH: 240px, fixed left, full height
BACKGROUND: var(--color-surface)
BORDER: border-right 1px var(--color-border)
PADDING: 24px 16px
TOP OFFSET: 64px (below navbar)

LINK ORDER (exact per spec §2.4a):
  My Dashboard      → /dashboard
  Browse Items      → /
  List an Item      → /items/new
  My Profile        → /profile
  [divider]
  ESG Dashboard     → /partner/dashboard   [partner + admin only]
  Admin Panel       → /admin/partners      [admin only]
  [divider]
  Settings          → /settings
  Sign Out

LINK STYLE:
  Each: 40px height, 12px 14px padding, --radius-md
  Icon: Material Symbol 20px, --color-ink-tertiary, left of label, 10px gap
  Label: 14px 500, --color-ink-secondary
  Active: var(--color-primary-muted) bg, --color-primary text + icon
  Hover: var(--color-surface-raised) bg
  Transition: background 150ms, color 150ms

SIDEBAR FOOTER (bottom of sidebar):
  kg_saved global counter: [leaf icon] "{campus_kg}kg saved at Brookes"
  13px, --color-ink-tertiary, --font-mono for number
  Links to /partner/dashboard if partner, otherwise decorative
```

---

### Mobile — Top Bar

```
HEIGHT: 56px + env(safe-area-inset-top)
BACKGROUND: var(--color-surface)
BORDER: border-bottom 1px var(--color-border)
Position: fixed, top: 0, z-index: 100

LAYOUT: 3-column: [left] [center] [right]

LEFT:
  Hamburger ☰ button (44px touch target) → opens right drawer
  OR [← Back] arrow (Material Symbol "arrow_back") on non-root pages

CENTER:
  Page-aware title (not always "Reuni"):
    /              → "Marketplace"
    /dashboard     → "My Dashboard"
    /items/new     → "New listing"
    /items/<id>    → item title (max 28ch, ellipsis)
    /items/<id>/pin → "PIN Handshake"
    /profile       → "My Profile"
    /settings      → "Settings"
    /partner/dashboard → "ESG Dashboard"
    /admin/*       → "Admin Panel"
    Auth pages     → "Reuni" wordmark (logo)
  Font: 16px 600, --color-ink-primary

RIGHT:
  Notification bell (same spec as desktop — badge + count)
  OR on auth pages: dark mode toggle
```

---

### Mobile — Bottom Tab Bar (4 tabs, authenticated only)

```
HEIGHT: 60px + env(safe-area-inset-bottom)
BACKGROUND: var(--color-surface)
BORDER: border-top 1px var(--color-border)
Position: fixed, bottom: 0, z-index: 100

4 tabs, each 25% width:

[Home]          Material Symbol "home"         → /
[Search]        Material Symbol "search"       → opens full-screen search overlay
[  ➕ Sell  ]   Material Symbol "add"           → /items/new  (or /auth/login if unauth)
[Profile]       User initials circle 24px      → /profile  (or /auth/login if unauth)

HOME: standard icon, 12px label below
SEARCH: standard icon, 12px label below
  On tap: full-screen overlay (NOT a new page):
    White bg, full-screen, search input auto-focused
    Recent searches below
    Dismiss: back button or swipe down or tap backdrop
SELL (center):
  ELEVATED treatment: var(--color-primary) circle bg, 52px diameter
  White "add" icon 24px inside
  translateY(-8px) above tab bar baseline — floats above the bar
  No label (action is obvious)
PROFILE:
  User initials circle 24px, --color-primary-muted bg, --color-primary text
  12px label "Profile" below
  Active: border 2px var(--color-primary) on circle
  If unauth: person icon placeholder

ACTIVE STATE (non-Sell tabs):
  Icon + label: var(--color-primary)
INACTIVE:
  Icon + label: var(--color-ink-tertiary)

BODY PADDING (mobile, authenticated):
  padding-top: calc(56px + env(safe-area-inset-top))
  padding-bottom: calc(60px + env(safe-area-inset-bottom))
```

---

### Mobile — Hamburger Drawer (authenticated)

```
TRIGGER: ☰ in top bar left
WIDTH: 280px
SIDE: slides in from RIGHT
BACKGROUND: var(--color-surface)
BACKDROP: rgba(0,0,0,0.4) behind drawer

ANIMATION:
  Open: translateX(100%) → translateX(0), 280ms, var(--ease-out-expo)
  Close: reverse, 220ms
  Backdrop: opacity 0 → 0.4, 200ms

DRAWER HEADER:
  Logo + "Reuni" wordmark, 20px — top of drawer, 20px 16px padding

LINKS (mirrors sidebar exactly, same order):
  My Dashboard / Browse Items / List an Item / My Profile
  [divider]
  ESG Dashboard / Admin Panel (role-gated)
  [divider]
  Settings
  
  Each: 48px touch target, 16px 20px padding, 15px text

DRAWER FOOTER:
  [Sign out] — --color-danger text, 48px, full-width
  kg_saved counter: same as desktop sidebar
```

---

## SECTION 3 — PAGE BLUEPRINTS

### PAGE 1: `index.html` — Marketplace
**Route:** `GET /` · **Auth:** Public

```
LAYOUT (≥1024px): 2-column grid [260px sidebar | 1fr listings]
LAYOUT (<1024px): single column

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HERO STRIP — CONTEXT-AWARE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Unauthenticated:
    Full-width, var(--color-primary) bg, 80px height (auto on mobile)
    LEFT: "Campus items. Real kg saved." (18px 600, white)
          "Student-to-student. In person. No fees." (14px, white opacity 0.75)
    RIGHT: [Register free →] white fill, --color-primary text, 40px, --radius-md
    No scroll arrows, no bounce, no animations — content pulls users in

  Authenticated:
    Full-width, var(--color-surface), border-bottom 1px var(--color-border), 60px
    3 stat chips left-aligned (12px 16px padding, --radius-full):
      [leaf icon] "{user.kg_saved}kg saved" — weight 700, --font-mono, --color-primary text
      [package icon] "{n} listed"
      [shopping_bag icon] "{n} purchased"
    Each chip: var(--color-surface-raised) bg, 13px

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SEARCH BAR (full-width, 64px zone):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Input: full-width, 48px, --radius-md, border 1px var(--color-border)
  Left icon: Material Symbol "search", 18px, --color-ink-tertiary
  Right: [Search] button, var(--color-primary) fill, 40px — attached inside border
  Placeholder: "Search listings — textbooks, furniture, electronics…"
  Focus: border-color → var(--color-primary), box-shadow 0 0 0 3px var(--color-primary-muted)
  Form GET → ?q= on enter or button click

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FILTER SIDEBAR (desktop, sticky):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Width: 260px, sticky top: calc(64px + 16px)
  No card shadow — avoids nested card anti-pattern

  [Group 1] Price Type
    Label: "PRICE" — 11px, var(--track-wide), ALL-CAPS, --color-ink-tertiary
    Custom radio group: ○ All items  ○ Free only  ○ Paid only
    Active radio: var(--color-primary) fill

  [Group 2] Category + kg hint
    Label: "CATEGORY"
    8 checkboxes with category name + kg weight:
      □ Furniture (12.0 kg)    □ Kitchenware (4.0 kg)
      □ Electronics (3.0 kg)  □ Sports (2.5 kg)
      □ Clothing (1.5 kg)     □ Books (0.8 kg)
      □ Stationery (0.3 kg)   □ Other (1.0 kg)
    kg: 12px, --color-ink-tertiary — communicates impact at a glance
    Checked: --color-primary border/fill

  [Group 3] Price Range (visible when "All" or "Paid" active)
    Label: "PRICE RANGE"
    Min [£] / Max [£] — 48% each, 40px, --radius-md

  [Apply Filters] — full-width, 44px, var(--color-primary) fill
  [Clear all] — centered text link, 13px, --color-ink-tertiary

  MOBILE FILTER ALTERNATIVE:
    Horizontal scroll chip strip below search bar
    [All] [Free] [Paid] [Furniture] [Electronics]... + [filter_list Filters] chip at end
    [Filters] chip opens full-screen overlay:
      Top: [← Back] "Filters" [Clear all]
      Same groups as desktop sidebar
      Bottom sticky: [Apply — {n} results] var(--color-primary) fill, 56px, full-width
      Result count updates live as filters change

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LISTINGS GRID:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Grid: repeat(auto-fill, minmax(280px, 1fr)), gap 20px
  Mobile: repeat(auto-fill, minmax(160px, 1fr)), gap 12px

  ITEM CARD ANATOMY:
  ┌────────────────────────────┐
  │ IMAGE — 16:10, object-cover│
  │ --radius-lg top corners    │
  │ [Claimed] badge top-right  │   var(--color-warning) bg, 10px, pill
  │ [Free] badge top-left      │   var(--color-success) bg, white text
  │ [⚡ Featured] badge tl     │   var(--color-accent) bg — boosted (Phase 2)
  ├────────────────────────────┤
  │ BODY — padding 12px (mob)  │
  │        padding 16px (desk) │
  │                            │
  │ [Category chip] [Condition]│   10px, --radius-sm, --color-surface-raised
  │                            │
  │ Title — 14px 600 (mob)     │
  │         15px 600 (desk)    │   2 lines max, text-overflow ellipsis
  │                            │
  │ Price [$]  [leaf] {kg}kg   │   Price: --font-mono 16px 700
  │            right-aligned   │   kg: --font-mono 12px, --color-primary
  │                            │
  │ SELLER ROW (Phase 2 only): │
  │ [avatar 20px] Name         │   Shows Grove/Ecosystem badge if earned
  │   [🌲 Top Seller]          │   Grove badge: 10px label, --color-primary muted bg
  │   [♻️ Ecosystem]           │   Ecosystem: subtle animated gradient border on card
  │                            │
  │ [CTA button — full-width]  │   See states below
  └────────────────────────────┘

  CTA STATES ON CARD:
    Available + auth'd:     [Claim] — var(--color-accent) fill, 40px (desk) / 36px (mob)
    Available + unauth'd:   [Log in to claim] — ghost, --color-primary
    Claimed:                [Claimed] — disabled, --color-surface-raised
    Sold:                   [Sold ✓] — --color-success-muted bg, --color-success text
    Owner:                  No CTA on card — see detail page

  CARD HOVER (desktop only):
    transform: translateY(-2px)
    shadow: var(--shadow-raised)
    Transition: 200ms var(--ease-out-expo)
    Animate the CARD, never the image directly

  CARD MOUNT ANIMATION:
    Stagger: opacity 0 + translateY(12px) → opacity 1 + translateY(0)
    Delay: calc(index * 60ms), max 10 items staggered
    Duration: 300ms, var(--ease-out-expo)
    @media (prefers-reduced-motion): instant, no stagger

  RESULTS HEADER:
    "Showing 24 of 87 items" — 13px, --color-ink-tertiary, left-aligned
    Right: [Sort: Newest] dropdown, ghost style, 13px

  EMPTY STATE (no results):
    Material Symbol "search_off" 48px, --color-ink-tertiary
    "Nothing here" — 18px 600, --color-ink-primary
    "Try adjusting your search or filters." — 14px, --color-ink-secondary
    [Clear filters] — --color-primary text link
    No illustrations

  PAGINATION:
    Page number chips: 36px square, --radius-md
    Active: var(--color-primary) fill, white
    Other: var(--color-surface-raised), --color-ink-secondary
    Mobile: [← Prev] [Next →] only (no page chips)
```

---

### PAGE 2: `items/detail.html` — Item Detail
**Route:** `GET /items/<id>` · **Auth:** Public

```
LAYOUT (≥1024px): 2-column [image 55% | details 45%], max-width 960px centered
LAYOUT (<1024px): single column, edge-to-edge image

BREADCRUMB (desktop): Browse → {Category} → {Title}
  12px, --color-ink-tertiary, Material Symbol "chevron_right" between segments

IMAGE (desktop): 100% column width, max 480px height, object-cover, --radius-lg
IMAGE (mobile): full-width, 16:9 ratio, no border-radius (edge-to-edge is more native)
CLAIMED OVERLAY: semi-dark + "CLAIMED" centered, 700 weight, white, when claimed

DETAILS COLUMN (vertical stack, 24px gap):

  ROW 1: [Category chip] [Condition chip] — 10px, --radius-sm
  
  ROW 2: Title — 24px 700, --color-ink-primary, line-height 1.2, text-wrap: balance
  
  ROW 3: Price + kg
    Price: --font-mono 28px 700, --color-ink-primary
    If free: "Free" in --color-success 24px 700
    kg block (full-width):
      var(--color-primary-muted) bg, --radius-md, 12px 16px padding
      Material Symbol "eco" 16px + "This item saves ~{kg} kg from landfill"
      14px, --color-primary 500
      Below: "Based on WRAP UK material weight data" — 11px, --color-ink-tertiary
  
  ROW 4: Description (if set) — 15px, --color-ink-secondary, leading 1.65, max 65ch
  
  ROW 5: Seller info
    Avatar: initials circle 36px, --color-primary-muted bg, --color-primary text
    Name: 14px 500, --color-ink-primary
    Listed: "Listed 3 days ago" — 12px, --color-ink-tertiary
    Phase 2 seller tier badge inline with name: "🌲 Top Seller" / "♻️ Ecosystem"
  
  Divider: 1px var(--color-border)
  
  ROW 6: CTA BLOCK (desktop inline / mobile sticky footer)
  
    STATE A — Available, authenticated, not owner:
      [Claim This Item] — var(--color-accent) fill, white, full-width, 48px, --radius-md
      Below: "You'll get the seller's contact + a pickup PIN." — 12px, --color-ink-tertiary
    
    STATE B — Available, unauthenticated:
      [Log in to claim] — var(--color-accent) fill, full-width, 48px
      Below: "Oxford Brookes email required." — 12px, --color-ink-tertiary
    
    STATE C — Owner, available:
      Row: [Edit listing] (outline, --radius-md) | [Delete listing] (--color-danger outline)
      Both: 48px, equal width
    
    STATE D — Owner, item claimed by someone:
      Status chip: "Claimed" (--color-warning bg, pill)
      [View PIN handshake →] — var(--color-accent) fill, full-width, 48px
    
    STATE E — Current user is buyer:
      Status chip: "You've claimed this"
      [View PIN handshake →] — var(--color-accent) fill
      [Cancel claim] — 14px text link, --color-danger, centered below
    
    STATE F — Previously cancelled this item (anti-griefing):
      [Claimed before — unavailable to you] — disabled, --color-surface-raised bg
      Material Symbol "block" icon left
      "You cancelled a previous claim on this item." — 12px, --color-ink-tertiary
    
    STATE G — Sold:
      [Sold ✓] — disabled, --color-success-muted bg, --color-success text, full-width 48px
      "This item found a new home." — 14px, --color-ink-secondary centered

  ROW 7: Report link (authenticated, not owner):
    Material Symbol "flag" 14px + "Report this listing" — 13px, --color-ink-tertiary
    On hover: --color-danger
    On click: opens report modal overlay (Phase 2 — see Part 4)

MOBILE — STICKY CTA FOOTER:
  Fixed bottom, above tab bar
  Height: 72px + env(safe-area-inset-bottom)
  var(--color-surface), border-top 1px var(--color-border)
  Padding: 12px 16px
  Renders the appropriate CTA state button at 52px height, full-width
  The in-page CTA buttons are REMOVED on mobile — sticky footer is the only CTA
```

---

### PAGE 3: `items/list_item.html` — Create Listing
**Route:** `GET|POST /items/new` · **Auth:** `@login_required @verified_required`

```
LAYOUT: Single column, max-width 680px, centered
MOBILE: Photo field moves to top (see below)

PAGE HEADER:
  "List an item" — var(--type-display), --color-ink-primary
  "60 seconds. Campus pickup only. No fees." — 14px, --color-ink-secondary

FORM CARD: var(--color-surface), var(--shadow-card), --radius-xl, 32px 36px padding

FIELD ORDER (DESKTOP):
  [1] Title — text, 48px, maxlength 80, live char counter "0/80", --radius-md
      Placeholder: "e.g. IKEA desk lamp, Nikon DSLR, Chemistry textbook…"

  [2] Category — custom-styled select, 48px, --radius-md
      After selection: KG PREVIEW appears:
        var(--color-primary-muted) bg, --radius-md, 10px 14px
        Material Symbol "eco" + "Furniture ≈ 12.0 kg prevented from landfill" — 13px, --color-primary
        kg weight fetched from /items/api/category-weights on change

  [3] Condition — segmented control (NOT a select)
      [New] [Like New] [Good] [Fair] [Poor] — 5 equal segments
      Selected: var(--color-primary) bg, white text
      Unselected: var(--color-surface-raised), --color-ink-secondary
      Height: 40px. Outer edges rounded --radius-md, inner edges flat.

  [4] Price — toggle first, then conditional field
      Toggle: [Free ✓] [Set Price] — pill segments, 48px full-width
      If "Set Price":
        £ prefix inside input, 48px, type number, --radius-md
        "12px, --color-ink-tertiary: Payment at handoff — cash or bank transfer."

  [5] Description (optional) — textarea
      Min-height: 160px, resize: vertical only
      maxlength: 2000 (NOT 500 — corrected)
      Live char counter below right: "0/2000"
      Placeholder: "Any details: size, age, minor wear, accessories included…"

  [6] Photo (required)
      Upload zone: dashed 2px var(--color-border), --radius-lg, 180px min-height
      Center: Material Symbol "photo_camera" 32px, --color-ink-tertiary
      "Click to upload or drag here" — 14px, --color-ink-secondary
      "JPG, PNG, WebP · max 5MB" — 12px, --color-ink-tertiary
      After select: image preview fills zone, [✕ Remove] chip top-right

MOBILE FIELD ORDER (REORDERED — camera is fastest mobile input):
  Photo FIRST → Category → Title → Condition → Price → Description
  Photo zone: "Tap to take a photo or upload" — no drag-and-drop on mobile
  All fields: 48px height, native selects (triggers OS picker)
  Submit: sticky footer button

FORM FOOTER:
  [List this item] — var(--color-primary) fill, white, full-width, 48px, --radius-md
  Loading: "Listing…" + 3-dot pulse loader (not a spinner)
  Below: [Discard] text link, centered, 13px, --color-ink-tertiary

MOBILE — STICKY SUBMIT:
  Fixed bottom, above tab bar
  [List this item] — var(--color-primary) fill, 52px, full-width

TRUST SIGNAL:
  Below form (or below sticky button on mobile):
  Material Symbol "lock" 14px + "Your contact details are only shared after a claim."
  12px, --color-ink-tertiary, centered
```

---

### PAGE 4: `items/pin.html` — PIN Handshake
**Route:** `GET /items/<id>/pin` · **Auth:** `@login_required` (buyer or seller)

> Physical context: user is standing outside on campus in front of a stranger. One hand. Possible wind, rain, social pressure. Every design decision here prioritises speed and legibility over aesthetics.

```
LAYOUT: Single column, max-width 480px centered
TOP PADDING: 40px (desktop) / 20px (mobile)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WHATSAPP CONTACT BLOCK
(buyer-side only, shown before PIN display)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  var(--color-surface), --radius-lg, border 1px var(--color-border)
  Padding: 16px 20px, margin-bottom 20px

  Label: "SELLER CONTACT" — 11px, ALL-CAPS, --track-wide, --color-ink-tertiary
  [Avatar 32px] {Seller name} — 14px 500, --color-ink-primary
  Phone: +44 7xxx xxxxxx — --font-mono 15px, --color-ink-secondary

  [open_in_new  Open WhatsApp]
  Background: #25D366 (WhatsApp brand green, hardcoded — not a token)
  White text + Material Symbol "open_in_new" icon left
  Full-width, 44px, --radius-md
  href: "https://wa.me/{e164_number}?text={prefilled_message}"
  Message: "Hey, I just claimed your {item_title} on Reuni. When can we meet for the PIN handshake?"

  [content_copy  Copy message] — ghost link, 13px, --color-primary, below button
  On click: copies prefilled text to clipboard
  After click: text changes to "Copied ✓" for 1s, then reverts

  Privacy note: Material Symbol "lock" 12px + "Contact details are only visible after claiming."
  11px, --color-ink-tertiary

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ROLE HEADER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  PIN HOLDER (seller on free item / buyer on paid):
    Material Symbol "verified_user" 40px (desktop) / 40px (mobile), --color-primary
    Title: "Your pickup PIN" — 22px 700
    Subtitle (role-aware):
      Seller free item: "Share this PIN with the buyer when they confirm collection."
      Buyer paid item: "Share this PIN with the seller AFTER inspecting and paying."

  PIN ENTERER (buyer on free / seller on paid):
    Material Symbol "input" 40px, --color-accent
    Title: "Enter the PIN" — 22px 700
    Subtitle (role-aware):
      Buyer free item: "The seller will tell you the 4 digits when you collect."
      Seller paid item: "Enter the PIN the buyer gives you after you confirm payment."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PIN DISPLAY CARD (holder view)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  var(--color-surface), var(--shadow-raised), --radius-xl, 32px padding
  var(--color-primary-muted) inner zone for the digits

  PIN: "3 · 7 · 4 · 1"
    Font: --font-mono
    Desktop: 52px 800, letter-spacing 0.25em
    Mobile: 56px 900, letter-spacing 0.3em — LARGER outdoors
    Color: var(--color-primary)
    Dots: --color-ink-tertiary 30px, centered between digits
    Inner zone bg: var(--color-primary-muted), --radius-lg, padding 20px 32px

  Expiry countdown:
    "Expires in 71:43:22" — --font-mono 14px, --color-ink-secondary
    < 4 hours: → --color-warning
    < 1 hour: → --color-danger + subtle text pulse animation

  ACTIONS:
    [mail  Resend PIN to email] — ghost outline, 40px, --radius-md, full-width
    Rate limit note: "3 per hour" — 11px, --color-ink-tertiary

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PIN ENTRY CARD (enterer view)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  4 individual single-character inputs
  Desktop: 64×64px each, 12px gap, --font-mono 28px 700
  Mobile: 68×72px each, 10px gap, --font-mono 32px 700 — LARGER for thumbs
  Border: 2px solid var(--color-border)
  Focus: border → --color-primary, box-shadow 0 0 0 3px var(--color-primary-muted)
  Filled: border → --color-success
  Error: all 4 → --color-danger border (simultaneous)

  inputmode="numeric" — triggers number keypad on iOS/Android, NOT QWERTY

  Auto-advance: focus moves to next input on character entry
  Auto-submit: fires when 4th digit entered

  KEYBOARD HANDLING (critical):
    Problem: software keyboard pushes layout up, covers inputs
    Solution:
      window.visualViewport.addEventListener('resize', scrollHandler)
      [NOT window.innerHeight — wrong on mobile]
      On resize: scroll inputs to remain 100px from visible top
      PIN boxes never fall below 50% of visible viewport height

  Attempt counter:
    "2 of 3 attempts remaining" — 13px, --color-warning, Material Symbol "timer" left
    1 attempt: → --color-danger, 600 weight

  [Confirm Exchange] — var(--color-accent) fill, white, full-width, 48px (desk) / 56px (mob)
  Disabled (opacity 0.4, pointer-events none) until all 4 digits entered
  Loading: "Confirming…" + 3-dot pulse

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SAFE EXCHANGE GUIDE
(below PIN display/entry card, both parties)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  var(--color-surface-raised), border 1px var(--color-border), --radius-lg
  Padding: 16px 20px

  DESKTOP: always expanded
  MOBILE: collapsible accordion (default collapsed after first visit)
    Header: "handshake  Safe exchange guide" tappable, chevron_right/expand_more icon
    First visit: auto-expanded (localStorage flag "pin_guide_seen")

  Content:
    "handshake  Safe Exchange Guide" — 13px 600, --color-ink-primary
    5 numbered steps:
      1. Meet in a public space on campus (library, SU, café)
      2. Buyer: inspect the item first
      3. Seller: confirm you've received payment (check your app)
      4. Both phones out — PIN holder shows PIN, other party types it in
      5. Both confirm the on-screen ✅ Complete before walking away

    Steps: 13px, --color-ink-secondary, leading 1.5, 8px gap between
    Step numbers: 12px 700, --color-primary, --font-mono

  HIGH-VALUE ADVISORY (only when item.price ≥ 100):
    Appears directly below the guide
    var(--color-warning-muted) bg, border 1px rgba(245,158,11,0.4), --radius-md, 14px 16px
    Material Symbol "warning" 16px, --color-warning
    "For items over £100, we recommend meeting at the SU reception desk
     and completing the exchange with both phones visible."
    13px, --color-ink-primary

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CANCELLATION COUNTDOWN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  STATE A — within 24h of claim:
    var(--color-success-muted) bg, --radius-md, 12px 14px
    Material Symbol "check_circle" 14px, --color-success
    "Free cancellation — {18h 32m} left to cancel without penalty"
    Countdown in --font-mono, 13px
    Color transition: STATE A → STATE B auto-triggers in JS at 24h mark

  STATE B — after 24h:
    var(--color-warning-muted) bg, --radius-md
    Material Symbol "warning" 14px, --color-warning
    "Late cancellation — cancelling now will result in a small trust adjustment"
    13px, --color-ink-secondary

  Countdown timer: updates live via setInterval every 60s
  Format: "{n}d {h}h {m}m" if >24h, "{h}h {m}m" if <24h, "{m}m" if <1h (→ --color-danger)

  [Cancel this claim] BUTTON (NOT a text link):
    Outline border var(--color-danger), --color-danger text
    Full-width, 44px (desk) / 52px (mob), --radius-md
    Inline confirmation on click:
      "Are you sure?" [Yes, cancel] [Never mind]
      Both: 44px, equal width, side by side
      [Yes, cancel]: var(--color-danger) fill white
      [Never mind]: ghost outline

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SUCCESS STATE (after correct PIN)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Replaces card content in-place (no page navigation)

  Material Symbol "check_circle" 64px, var(--color-success)
  Animation: scale(0) → scale(1.2) → scale(1), 500ms, var(--ease-spring)
  "Exchange complete!" — 24px 700, --color-ink-primary

  KG SAVED BLOCK:
    var(--color-success-muted) bg, --radius-xl, 24px padding, full-width
    Large number: "{kg}" — --font-mono 48px 800, --color-success
    ANIMATION: count up from 0.0 to {kg} over 1000ms, easeOutExpo, one decimal
    "kg saved from landfill" — 14px, --color-success
    "Your total: {user.total}kg" — 12px, --color-ink-secondary, --font-mono

  BADGE UNLOCK (Phase 2 — if kg push crosses threshold):
    After count-up animation:
    Badge icon scales in: scale(0) → scale(1.2) → scale(1), 500ms, var(--ease-spring)
    "{Badge Name} Badge Unlocked!" — 16px 700, --color-primary
    12 small teal/orange squares scatter from icon: pure CSS, transform + opacity
    Auto-clear after 2s
    This is the ONLY moment in the product where particle effects are justified.

  [Back to marketplace →] — --color-primary text link, 48px touch target
```

---

### PAGE 5: `dashboard.html` — Student Dashboard
**Route:** `GET /dashboard` · **Auth:** `@login_required`

```
LAYOUT: Full authenticated shell (sidebar + main), 32px content padding

PAGE HEADER ROW:
  Left: "My Dashboard" — var(--type-title), 700, --color-ink-primary
  Right: [add  List an Item] — var(--color-primary) fill, white, 40px, --radius-md

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ACTIVE CLAIM ALERT (conditional, priority — appears first)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Only shown if user has a pending claim or their item is claimed.
  var(--color-warning-muted) bg, --radius-lg, 16px 20px, border 1px var(--color-warning)
  Material Symbol "timer" 20px, --color-warning

  AS BUYER: "You've claimed {item.title} — awaiting pickup"
  AS SELLER: "{buyer.name} has claimed your {item.title}"
  
  Right: [View PIN handshake →] — var(--color-accent) fill, white, 36px, --radius-md
  Below text: "PIN expires in {n}h {m}m" — --font-mono 12px, --color-warning

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 1: IMPACT CARDS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Grid: 3 columns (desktop), 2 columns (tablet), 1 column (mobile)
  ASYMMETRIC — not equal identical cards (banned pattern)

  CARD A — kg Saved (DOMINANT):
    Background: var(--color-primary) — the only filled-primary card on this page
    Number: --font-mono 42px 800, WHITE
    Label: "kg saved from landfill" — 14px, white opacity 0.85
    Subline: "Oxford Brookes total: {campus_total}kg" — 12px, white opacity 0.6
    Mount animation: number counts up 0 → {kg_saved} over 800ms, easeOutExpo
    This card takes the full visual emphasis of the row

  CARD B — Items Listed:
    var(--color-surface), var(--shadow-card)
    Number: --font-mono 28px 700, --color-ink-primary
    Label: "items listed" — 13px, --color-ink-secondary
    Sub: "{n} active · {n} sold" — 12px, --color-ink-tertiary

  CARD C — Items Purchased:
    var(--color-surface), var(--shadow-card)
    Number: --font-mono 28px 700, --color-ink-primary
    Label: "items purchased" — 13px, --color-ink-secondary

  All cards: --radius-lg, padding 20px 24px

  BADGE PROGRESS BAR (Phase 2 — shown below Card A or inline within it):
    Full-width within card
    "████████████░░  8.3 / 10 kg — 1.7 kg to Tree 🌳"
    Bar: --color-primary fill on white track, --radius-full, transition 600ms on mount
    Text: 13px, --font-mono for numbers
    IF max badge: "♻️ Ecosystem — Maximum badge reached" (no bar)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 2: TABBED ITEM LISTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Tabs: [My Listings ({n})] [My Purchases ({n})]
  Style: underline tabs — 2px --color-primary underline active, no pill/box
  Active: --color-ink-primary, 500 weight
  Inactive: --color-ink-tertiary

  LIST VIEW (not grid — more info density needed here):
  Each row (72px height, border-bottom 1px var(--color-border)):
  
    [IMG 52×52px, --radius-md, object-cover]
    [Title 14px 500 | Category chip | Condition chip]
    [£Price --font-mono 14px 700 | leaf icon {kg}kg --font-mono 11px --color-primary]
    [Status badge — right]
    [Action buttons — far right]

  STATUS BADGES:
    Available: --color-success-muted bg, --color-success text, pill
    Claimed: --color-warning-muted bg, --color-warning text
    Sold: --color-surface-raised bg, --color-ink-tertiary — dimmed (archived feel)

  ACTION BUTTONS (My Listings):
    Available: [edit  Edit] ghost 32px | [delete  Delete] --color-danger text link
    Claimed: [View PIN →] -- --color-accent fill, 32px
    Sold: no actions (complete)

  BOOST BUTTON (Phase 2, My Listings, Available items):
    [rocket_launch  Boost] — --color-accent outline, 32px, 13px
    Only shown if user has boost_tokens > 0

  EMPTY STATE:
    My Listings: Material Symbol "sell" 48px | "No listings yet" | [List your first item] CTA
    My Purchases: Material Symbol "shopping_bag" 48px | "No purchases yet" | [Browse marketplace] link
```

---

### PAGE 6: `profile.html` — User Profile
**Route:** `GET /profile` · **Auth:** `@login_required`

```
LAYOUT: Single column, max-width 720px, centered. Padding top 40px.

PROFILE HEADER:
  Avatar: 80px circle, initials, var(--color-primary-muted) bg, --color-primary text 32px 700
  
  Phase 2 badge treatment:
    Tree: subtle teal glow on avatar border (box-shadow 0 0 0 3px var(--color-primary-muted))
    Forest: permanent teal border (border 3px solid var(--color-primary))
    Ecosystem: animated gradient border on avatar (CSS @keyframes hue-rotate, 3s infinite)
  
  Name: 24px 700, --color-ink-primary
  University: "Oxford Brookes University" — 14px, --color-ink-secondary
  Member since: "Member since October 2024" — 12px, --color-ink-tertiary
  Verified badge: [check_circle  Verified Student] — --color-success fill, white, 11px, pill

  KG HEADLINE BLOCK:
    var(--color-primary-muted) bg, --radius-lg, padding 20px 24px, margin 16px 0
    Number: --font-mono 40px 800, --color-primary — the identity statement
    "kg saved from landfill" — 14px, --color-primary opacity 0.75
    Subline: "Top {percentile}% at Brookes" — 12px, --color-ink-tertiary (if calculable)
    Phase 2 badge label below: "🌲 Grove · 🌳 Tree · ♻️ Ecosystem" etc.

  STATS ROW (borderless, text-only):
    Items listed: {n} | Items sold: {n} | Items purchased: {n}
    Dividers: 1px var(--color-border) vertical between blocks
    Number: --font-mono 22px 700, --color-ink-primary
    Label: 12px, --color-ink-tertiary

  [Edit profile] → /settings — 13px, --color-primary, Material Symbol "settings" icon

ACTIVE LISTINGS SECTION:
  "Active listings" — 16px 600
  Grid: repeat(auto-fill, minmax(240px, 1fr)) — same item cards as marketplace
  Empty: "Nothing listed right now." — --color-ink-tertiary
```

---

### PAGE 7: `settings.html` — Account Settings
**Route:** `GET/POST /settings` · **Auth:** `@login_required`

```
LAYOUT: Single column, max-width 640px, centered. Padding top 40px.
PAGE TITLE: "Settings" — var(--type-title)

Settings cards (vertical stack, 24px gap):
Each section: var(--color-surface), var(--shadow-card), --radius-lg, 24px padding
Section label: 12px ALL-CAPS --track-wide --color-ink-tertiary — top of each card

SECTION 1 — Account Info (read-only):
  Email: {user.email} + Verified chip (--color-success) or Unverified (--color-warning)
  Role: Student / Partner / Admin
  Note: Email is immutable — no edit

SECTION 2 — Phone Number:
  Current: {phone} or "Not set"
  Inline mini-form:
    Input: 48px, type tel, +44 prefix, --radius-md
    [Save] button same row (desktop) / below (mobile), 40px, var(--color-primary) fill
  "12px hint: Used for WhatsApp coordination after a claim."

SECTION 3 — Change Password:
  3 inputs (stacked, 14px gap):
    Current / New / Confirm — all 48px, type password, show/hide toggle (Material Symbol "visibility"/"visibility_off")
  Password strength bar below New field:
    3-segment pill bar, --radius-full
    Weak: --color-danger fill | Medium: --color-warning fill | Strong: --color-success fill
    Updates live via JS on keyup
  [Update password] — var(--color-primary) fill, full-width, 44px

SECTION 4 — Danger Zone:
  Background: var(--color-danger-muted) — different from other sections
  Border: 1px solid rgba(239,68,68,0.3)
  Label: "DANGER ZONE" in --color-danger
  
  Explainer: 14px, --color-ink-secondary, max 65ch:
    "Deleting your account cancels all active claims and removes your listings.
     ESG transaction data is retained (anonymised). You have a 30-day cooling-off period."
  
  Confirmation form:
    Label: 'Type "DELETE" to confirm'
    Input: 48px, 200px wide, text type
    [Delete My Account] — var(--color-danger) fill, white, 44px
    ONLY enabled when input value === "DELETE" exactly (JS check)
    Rate limited: 3/hour (enforced server-side)
  
  Admin/partner accounts: section shows "Account deletion requires contacting support." — no form
```

---

### PAGE 8: Auth Pages

#### `auth/login.html`
```
LAYOUT: 2-column split (50/50) ≥1024px, single column <1024px

LEFT COLUMN (form):
  Padding: 48px, max 400px form
  [Reuni logo + wordmark] at top

  "Welcome back" — 26px 700
  "Sign in to your Brookes account" — 14px, --color-ink-secondary

  Fields (16px gap):
    Email: 48px, type email, Material Symbol "mail" inside left
    Password: 48px, type password, Material Symbol "visibility" toggle right

  Lockout warning (5 failed attempts):
    var(--color-warning-muted) bg, --color-warning left-border 3px (functional alert), 13px
    "Account temporarily locked. Try again in {time}."
    This IS a functional status stripe — not a decorative ban violation ✓

  [Sign in] — var(--color-primary) fill, white, full-width, 48px, --radius-md

  Below (14px, --color-ink-tertiary):
    Left: "New here? [Register]"
    Right: "[Forgot password?]"

RIGHT COLUMN (brand):
  var(--color-primary) fill
  Centered content, vertical middle:
  "{campus_total_kg}kg" — --font-mono 56px 800, white
  "saved by {n} Brookes students" — 18px, white opacity 0.8
  "Every item exchanged is one less in landfill." — 14px, white opacity 0.6
  Abstract teal geometric pattern (CSS SVG — NOT hand-drawn)

MOBILE: Right column collapses.
  Thin teal strip at top (8px height, --color-primary) replaces it.
```

#### `auth/register.html`
```
Same split layout as login.

"Join Reuni" — 26px 700
"Oxford Brookes students only. Always free." — 14px, --color-ink-secondary

Fields:
  Full Name — 48px, Material Symbol "person"
  University Email — 48px, Material Symbol "mail"
    Real-time validation after blur:
    Valid .ac.uk → [check_circle] "Brookes email detected" — --color-success, 12px below
    Invalid → [cancel] "Must be a .ac.uk email" — --color-danger, 12px
  Phone Number — 48px, Material Symbol "phone", +44 prefix inside
    "12px: For WhatsApp coordination. Not shown publicly."
  Password — 48px, show/hide toggle
    Strength bar (same as settings)
    "Min 8 chars, mixed case, and a digit required."

Privacy: "By registering you agree to our [Privacy Policy]." — 12px, --color-ink-tertiary

[Create account] — var(--color-primary) fill, full-width, 48px

"Already have an account? [Sign in]" — 14px
```

#### `auth/verify_email.html`
```
LAYOUT: Centered single column, max 480px, vertical centered

Material Symbol "mail" 48px, --color-primary, centered
"Check your email" — 24px 700
"We sent a 6-digit code to {email}. Expires in 15 minutes." — 14px, --color-ink-secondary

OTP INPUT — 6 individual boxes:
  Desktop: 56×64px each, 8px gap
  Mobile: 44×52px each, 8px gap (smaller — 6 boxes must fit 375px)
  --font-mono 24px 700, centered text
  Border 2px var(--color-border)
  Focus → --color-primary border + ring
  Filled → --color-success border
  inputmode="numeric" — numpad on mobile
  Auto-advance on entry. Auto-submit on 6th digit.
  Error: all 6 → --color-danger + "Code incorrect or expired." below

[Verify email] — var(--color-primary) fill, full-width, 48px

[Resend code] — --color-primary text link, centered, 14px
"3 per hour limit" — 11px, --color-ink-tertiary below
```

#### `auth/forgot_password.html` + `auth/reset_password.html`
```
LAYOUT: Centered card, max 440px

FORGOT:
  Material Symbol "lock_reset" 48px, --color-primary
  "Reset your password" — 24px 700
  Single email field + [Send reset link] — var(--color-primary) fill, full-width, 48px
  Rate limit: 3/hour
  Success state: replace form with:
    "Check {email} for a reset link valid for 1 hour."
    [Back to login] link

RESET:
  "Set new password" — 24px 700
  New / Confirm password fields + strength bar
  [Set password] — var(--color-primary) fill, full-width, 48px
  On success: flash success → redirect /auth/login
```

---

### PAGE 9: `partner/dashboard.html` — ESG Dashboard
**Route:** `GET /partner/dashboard` · **Auth:** `@partner_required or @admin_required`

> Register: institutional, data-forward. Density 7/10. Every number is --font-mono. No warmth — precision and trust.

```
LAYOUT: Full-width, max-width 1320px, 32px padding
MOBILE: Functional but desktop-primary (sustainability officer desk usage)

DASHBOARD HEADER:
  Left: [University logo 32px, Google Favicon API] + "Oxford Brookes University" 18px 600
        "Sustainability Dashboard · Powered by Reuni" — 13px, --color-ink-tertiary
  Admin global view: Reuni logo + "All Universities" instead
  Right: [download  Download report] ghost outline, 40px
         "Last updated: {datetime}" — --font-mono 12px, --color-ink-tertiary

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ROW 1: HERO KPI CARDS (4-column, asymmetric)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  CARD A — Total kg Saved (DOMINANT, 2fr):
    var(--color-primary) fill — only filled card in dashboard
    Number: --font-mono 52px 800, WHITE
    Label: "kg saved from landfill" — 16px, white opacity 0.85
    Subline: "Since {launch_date}" — 12px, white opacity 0.6
    Material Symbol "eco" 40px, white opacity 0.2 — bottom-right decorative

  CARD B — Items Exchanged (1fr):
    var(--color-surface), var(--shadow-card)
    Number: --font-mono 32px 700
    Label: "items exchanged" — 13px, --color-ink-secondary
    Trend: "↑ +{n} this month" — 12px, --color-success (or --color-danger ↓)

  CARD C — Verified Students (1fr):
    Same structure as B
    Label: "verified students"

  CARD D — Avg kg/Exchange (1fr):
    Same structure
    Label: "avg kg per exchange"
    Sub: "vs benchmark" — 12px, --color-ink-tertiary

  Grid: 4-column with A at 2fr, B-D at 1fr each (desktop)
  Mobile: stack all, A first

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ROW 2: CATEGORY BREAKDOWN (2fr | 1fr asymmetric)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  LEFT (2fr) — Category Table:
    "Exchanges by Category" — 16px 600
    Table: Category | Exchanges | kg Saved | % of Total
    All number cols: --font-mono
    Row hover: --color-surface-raised
    Sorted by kg_saved DESC
    Background bar: 4px teal stripe behind row, width = % of max (opacity 0.12)
    This avoids a separate chart while showing dominance visually
    Total row: 600 weight, border-top 1px --color-border
    No outer table borders — row separators only

  RIGHT (1fr) — Distribution Visual:
    "Distribution" — 16px 600
    Simple percentage list (no external chart library — pure CSS):
      Each category: [label] [bar] [%]
      Bar: --color-primary fill, proportional width, 8px height, --radius-full
      %: --font-mono 12px, right-aligned
      Saves: no Chart.js CSP issues

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ROW 3: LIVE CIRCULATION LOG (full-width)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  5 most recent exchanges (from spec §2.2 partner dashboard)
  "Recent Exchanges" — 16px 600
  Table rows: Item image (40px circle) + Title | Category | kg Saved | Date
  kg: --font-mono --color-primary 14px 600
  Date: relative timestamp, --font-mono 13px, --color-ink-tertiary

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ROW 4: ESG COPY BLOCK (full-width)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  var(--color-surface-raised) bg, border 1px dashed var(--color-border), --radius-lg
  Padding: 24px 28px
  "FOR YOUR ESG REPORT" — 11px ALL-CAPS, --track-wide, --color-ink-tertiary

  Pre-written copy (italic, 14px, --color-ink-secondary):
  "{university_name} students exchanged {total_items} items via Reuni in {period},
  diverting an estimated {total_kg} kg of goods from landfill in line with UN SDG 12
  — Responsible Consumption and Production."

  [content_copy  Copy text] — ghost button, 36px, --radius-md, right-aligned
  This block is a key differentiator: saves the sustainability officer 10 minutes.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 2 ADDITION — TREND CHART ROW:
(Insert between Row 2 and Row 3 when Phase 2 ships)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  "Monthly Exchange Trend" header + academic year selector dropdown
  12-bar column chart (Sep → Aug), pure SVG (no Chart.js — CSP safe)
  Bars: --color-primary fill, --radius-sm top corners
  Hover tooltip: "{month}: {kg}kg saved, {n} exchanges"
  Year-on-year ghost bars: --color-ink-tertiary opacity 0.25 (when 2+ years of data)
  Academic year total below chart: "{total_kg}kg" --font-mono 24px 700 --color-primary
```

---

### PAGE 10: `admin/partners.html` — Admin Panel
**Route:** `GET /admin/partners` · **Auth:** `@admin_required`

```
LAYOUT: Full-width, max-width 1100px
PAGE TITLE: "Partner Management" — var(--type-title)
RIGHT: [add  Invite partner university] — var(--color-primary) fill, 40px

INVITE FORM (expandable, collapsed by default):
  Expands below header on button click
  var(--color-surface), var(--shadow-card), --radius-lg, 24px

  "UNIVERSITY DOMAIN" label
  Input: 48px, placeholder "brookes.ac.uk"
  [Generate invite link] — var(--color-primary) fill, 44px

  On success: URL in --font-mono code block
    var(--color-surface-raised) bg, --radius-md, 12px 16px
    [content_copy  Copy link] icon, right-aligned
    "Expires in 48 hours" — 11px, --color-ink-tertiary

PARTNERS TABLE:
  Columns: University · Partner Email · Status · Created · Actions
  Row: 56px height, border-bottom 1px --color-border
  Hover: --color-surface-raised
  University: [favicon 20px] domain name 14px 500
  Email: --font-mono 13px, --color-ink-secondary
  Status: pill — Active (--color-success) / Deactivated (--color-surface-raised, --color-ink-tertiary)
  Created: --font-mono 13px, relative timestamp
  Actions:
    [Deactivate] — 13px, --color-danger text button
    Inline confirmation (replaces button, no modal):
      "Confirm deactivate?" [Yes] [Cancel] — within same row height
  Empty: Material Symbol "business" 48px | "No partners yet." | [Invite first university] link
```

---

### PAGE 11: `privacy.html` — Privacy Policy

```
LAYOUT: Max 720px, centered, 48px top, 80px bottom

[arrow_back  Back to Reuni] — --color-primary, 14px, top of page
"Last updated: {date}" — --font-mono 13px, --color-ink-tertiary

Typography (prose document):
  h1: var(--type-display), --color-ink-primary
  h2: 20px 600, margin-top 40px
  h3: 16px 600, margin-top 24px
  p: 15px, --color-ink-secondary, leading 1.7, max 65ch
  a: --color-primary, underline on hover

Sections: What we collect / How we use it / Retention / GDPR rights (erasure) / Contact / WRAP attribution
Pure typographic — no cards, no boxes, no icons
```

---

### PAGE 12: Error Pages

```
404:
  min-height: 100dvh, flex centering
  "404" — --font-mono 72px 800, var(--color-primary-muted) — large but muted
  "Page not found" — 24px 700, --color-ink-primary
  "This page doesn't exist or may have been removed." — 14px, --color-ink-secondary
  [Back to marketplace] — var(--color-primary) fill, 44px
  No illustrations.

500:
  Same layout
  "500" — var(--color-danger-muted) version
  "Something went wrong" — 24px 700
  "We've logged this error. Try refreshing or return to the marketplace." — 14px
  [Back to marketplace] — var(--color-primary) fill, 44px
```

---

### PAGE 13: `base.html` — Flash Messages

```
Per spec §2.3: "Inline alert banners rendered below the navbar, category-coloured.
Not toast-style — no slide animations."

POSITION: Full-width, directly below fixed navbar (not overlapping)
Z-INDEX: 90 (below navbar 100)
NO ANIMATION: appear/disappear with display toggle, no slide, no fade

VARIANTS:
  Success: var(--color-success-muted) bg, 3px left border --color-success (functional status indicator ✓)
  Error/Danger: var(--color-danger-muted) bg, 3px left border --color-danger
  Warning: var(--color-warning-muted) bg, 3px left border --color-warning
  Info: var(--color-primary-muted) bg, 3px left border --color-primary

Content row: [status icon 16px] [message text] [close ✕ button] right-aligned
Padding: 12px var(--container-pad)
Font: 14px, matching ink colour, 500 weight

NOTE ON LEFT-BORDER: The impeccable-skill bans decorative side stripes.
These flash banners ARE functional status communication, not decoration — the ban does not apply.
```

---

## SECTION 4 — PHASE 2+ UI BANK

*Features not yet built. Fully specced and ready for the next phase.*

---

### B1. Notification Feed — `/notifications`
```
LAYOUT: Max 680px, centered
HEADER: "Notifications" left | [Mark all read] right (--color-primary, only if unread > 0)

LIST (no cards — dividers only):
  Each row: 64px min-height, 12px 0 padding, border-bottom 1px --color-border

  UNREAD: 3px left border --color-primary + --color-primary-muted bg (1% opacity) + 600 weight
  READ: no border, transparent bg, 400 weight

  [Icon 40px circle] Message 14px | Relative timestamp --font-mono 12px --color-ink-tertiary

  NOTIFICATION TYPE → ICON + BEHAVIOUR:
  pin_generated → Material Symbol "key" (--color-accent bg) → tap: /items/{id}/pin
  claim_confirmed → "shopping_bag" (--color-primary bg) → tap: /items/{id}/pin
  exchange_complete → "check_circle" (--color-success bg) → tap: /dashboard
  claim_cancelled → "cancel" (--color-danger bg) → tap: /items/{id}
  trust_change → "shield" (--color-warning bg) → no link (shadow governance — no target to contest)
  boost_awarded → "rocket_launch" (--color-accent bg) → tap: /dashboard
  jury_summons → "gavel" (--color-primary bg) → tap: /jury/{report_id}
  badge_unlocked → [tier SVG icon] → tap: /profile
    Special: badge_unlocked gets a full card treatment (not just a row)
    Large badge icon + tier name + kg milestone reached
    Spring scale-in entrance animation

  MARK AS READ: tap row → optimistic JS update (instant visual, then POST)
  EMPTY: Material Symbol "notifications_none" 48px | "No notifications yet" | 14px --color-ink-secondary
```

---

### B2. Leaderboard — `/leaderboard`
```
LAYOUT: Max 680px, centered
TABS: [My University] [All Universities]

ACTIVE SEASON (Sep 1 – Jun 30):
  Season label + days remaining (--color-warning if <30 days)

  PODIUM (top 3):
    3-column: [2nd] [1st elevated] [3rd]
    1st: 48px avatar, gold podium (--color-warning fill), crown "workspace_premium" icon
    2nd/3rd: 40px avatars
    Below each: Name 13px | kg --font-mono 14px --color-primary
    Podium heights: 1st 80px | 2nd 60px | 3rd 50px

  POSITIONS 4–10:
    Row: [Rank --font-mono 13px --color-ink-tertiary] [Avatar 32px] [Name 14px] [kg --font-mono 14px --color-primary right]
    Height: 52px, border-bottom 1px --color-border

  CURRENT USER (if outside top 10):
    Sticky bottom of list, "— Your position —" separator
    Actual rank shown (e.g. "#47"), --color-primary-muted highlight

  ALL UNIVERSITIES TAB:
    Same row pattern with favicon instead of avatar
    Current user's university highlighted

OFF-SEASON (Jul 1 – Aug 31):
  Champions banner: --color-primary fill, podium with previous season's top 3
  "New season starts {Sep 1 date}" — 13px white
  Hall of Fame section: previous seasons collapsible list (permanent, never removed)
```

---

### B3. Badge System — Profile & Dashboard Integrations
```
BADGE TIERS:
  🌱 Seedling: 1 kg | 🌿 Sapling: 5 kg (+1 boost token)
  🌳 Tree: 10 kg (profile glow) | 🌲 Grove: 25 kg (+2 tokens + "Top Seller" on listings)
  🏔️ Forest: 50 kg (permanent teal border + early jury eligibility)
  🌍 Ecosystem: 100 kg (animated frame + "♻️ Ecosystem" title on ALL listings)

ON PROFILE: Badge icon 32px circle next to avatar, tier color bg
ON ITEM CARDS: Seller badge shown next to seller name (Grove+)
  Ecosystem items: subtle animated gradient card border
ON DASHBOARD: Progress bar below kg card (see Section 3, Page 5)
UNLOCK ANIMATION: On PIN success screen — spring scale-in, confetti (ONLY here)
```

---

### B4. Boost Token UI
```
DASHBOARD chip (if tokens > 0):
  [rocket_launch {n} boost tokens] — --color-accent fill, pill, right of stat chips

MY LISTINGS — per-item boost button (if tokens > 0, item available):
  [rocket_launch Boost] — --color-accent outline, 32px
  Inline confirmation: "Boost 30 days? ({n} token left)" [Use token] [Cancel]

BOOSTED IN FEED: [⚡ Featured] chip top-left of card image
  No other visual difference — organic feel preserved

EXPIRED BOOST: [rocket_launch Boosted · Expires {date}] — muted, no cancel
```

---

### B5. Report Flow
```
ENTRY: "flag  Report this listing" text link on detail page (authenticated, not owner)
MODAL:
  Two sections — Listing Reports (→ jury) | Transaction Reports (→ pattern-based)
  Radio options per section
  Role notes explaining resolution path
  [Submit report] --color-danger fill | [Cancel] text link
  POST-SUBMIT: success state in modal (no page nav)

JURY PAGE — /jury/{report_id}:
  Item preview (anonymised seller: "Anonymous Seller")
  Report shown: what was reported
  [check_circle Clear] / [cancel Guilty] — both 56px, outline style
  Inline confirmation on each vote
  POST-VOTE: "Vote submitted. +2 trust if you voted with majority."
```

---

### B6. Trust Score Indirect UI
```
SHADOW STATE (trust < 50):
  One non-dismissible notification:
  "Your listings are receiving less visibility due to community feedback.
   Continue making successful transactions to improve."
  Recovery: 3-segment progress bar, fills per clean exchange
  "Progress: {n}/3 clean exchanges completed." --font-mono --color-primary
  
WHAT IS NEVER SHOWN:
  - The number 50
  - "Shadow ban" / "trust score" / "banned"
  - Any appeal mechanism
  The ghost never knows they're a ghost.
```

---

### B7. PWA (Phase 2 — not current)
```
STATUS: Not yet implemented. No manifest.json or service worker exists. (spec §2.4a)

WHEN SHIPPED:
  manifest.json:
    "theme_color": "#0D9488"    (var(--color-primary))
    "background_color": "#F8FAFC" (var(--color-bg))
    "display": "standalone"
    "orientation": "portrait"
    "start_url": "/"

  iOS meta tags in base.html:
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="default">
    <meta name="apple-mobile-web-app-title" content="Reuni">
    <meta name="theme-color" content="#0D9488">

  Camera capture (also Phase 2 per spec):
    Add capture="camera" to list_item photo input
    CURRENTLY: accept="image/*" only (no capture attribute)
```

---

## SECTION 5 — ANTI-PATTERNS & GLOBAL BANS

```
BANNED — match and refuse, always rewrite:

ICONS:
  ✗ Phosphor icons anywhere (library changed to Google Material Symbols)
  ✗ Font Awesome, Heroicons, or any other icon library

TOKENS:
  ✗ --primary (correct: --color-primary)
  ✗ --accent (correct: --color-accent)
  ✗ --bg (correct: --color-bg)
  Any token without --color-* prefix for colour values

LAYOUT:
  ✗ 3 identical equal-width cards in a row as a feature layout
  ✗ Nested shadow cards (card inside a card with shadow)
  ✗ height: 100vh anywhere (use min-height: 100dvh)
  ✗ Horizontal overflow on mobile (critical failure)

TYPOGRAPHY:
  ✗ Inter font (banned — use Plus Jakarta Sans)
  ✗ Letter-spacing tighter than -0.04em on display text
  ✗ Font size below 11px (hard floor — --type-micro)
  ✗ Eyebrow text (small ALL-CAPS + wide tracking) above EVERY section
    One deliberate eyebrow in a UI is voice; an eyebrow on every section is AI grammar
  ✗ Numbered section markers (01 / 02 / 03) as decorative scaffolding

COLOR:
  ✗ Pure black #000000 (use --color-ink-primary #0F172A)
  ✗ Gradient text (background-clip: text with gradient)
  ✗ Neon outer glows or high-saturation box-shadow color
  ✗ Glassmorphism as default decorative treatment

MOTION:
  ✗ Rotating circle spinner (use 3-dot pulse or skeleton shimmer)
  ✗ Animating top / left / width / height properties
  ✗ Infinite floating/pulsing on non-status elements
  ✗ Hover animation on images (hover card bg/shadow instead)
  ✗ Scroll-hijacking or parallax
  ✗ Missing @media (prefers-reduced-motion: reduce) fallback

INTERACTION:
  ✗ Touch targets below 44px height on any interactive element
  ✗ Using window.innerHeight for keyboard detection on mobile (use visualViewport)
  ✗ Hover-only states on mobile (use :active for touch)
  ✗ Missing touch-action: manipulation on buttons (removes 300ms tap delay)
  ✗ Font-size below 16px on form inputs (causes iOS auto-zoom)

COPY:
  ✗ AI clichés: "Elevate", "Seamless", "Unleash", "Next-Gen", "Revolutionary"
  ✗ "Scroll to explore" / scroll arrows / bouncing chevrons
  ✗ Generic placeholder names: "John Doe", "Acme Corp", "Item Name"
  ✗ Round fake numbers: "99.9% uptime", "50% faster"

STRUCTURE:
  ✗ Hand-drawn SVG illustrations anywhere
  ✗ Skeleton elements that don't match actual content dimensions
  ✗ Empty states without a clear action or next step
  ✗ Form errors not shown inline (must appear below the offending field)
  ✗ Phase 2 features rendering in Phase 1 templates (Phase 2 UI is additive)
```

---

## CORRECTION LOG
*Records every discrepancy found between previous blueprints and the confirmed product_specification.md v1.3*

| # | What was wrong | Corrected to |
|---|---|---|
| 1 | Icon library: Phosphor | Google Material Symbols (outlined), aria-hidden="true" |
| 2 | Token prefix: `--primary` | `--color-primary` (all tokens use `--color-*`) |
| 3 | Button radius: 8px | 10px (--radius-md, confirmed in spec) |
| 4 | Mobile breakpoint: 768px | 1024px (spec explicit: "breakpoint is 1024px, not 768px") |
| 5 | Bottom tab bar: 5 tabs | 4 tabs: Home / Search / ➕ Sell / Profile |
| 6 | Notifications: tab bar slot | Top navbar bell icon only (no notifications tab) |
| 7 | PWA: treated as current | Phase 2 planned — no manifest.json exists yet |
| 8 | Camera capture: current | Phase 2 planned — currently accept="image/*" only |
| 9 | Description: 500 chars | 2000 chars (confirmed in spec §2.2) |
| 10 | Flash messages: no border | 3px left border IS correct — functional status, not decorative |
| 11 | Sidebar: vague spec | Exact link order from spec: Dashboard → Browse → List → Profile → ESG → Admin → Settings → Sign Out |
| 12 | Item cards: no seller tier | Phase 2 seller tier badge slot designed (Grove "Top Seller", Ecosystem "♻️ Ecosystem") |
| 13 | Mobile drawer: vague | Mirrors sidebar links exactly, right-slide |

---

*Blueprint v2.0 — canonical, supersedes REUNI_DESIGN_BLUEPRINT.md + REUNI_MOBILE_SPEC.md + REUNI_BLUEPRINT_AMENDMENT.md*
*Three documents → one. Source of truth: product_specification.md v1.3 · 13 June 2026*

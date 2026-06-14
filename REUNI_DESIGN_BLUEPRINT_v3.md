# REUNI — Elite Design Blueprint v3.0 (Unified)
### Master Design Specification & Phase 2+ Future UI Bank
### Source: product_specification.md v1.3 & Addendum v1.0 · June 2026
### For Antigravity 2.0 · Authored by Elite Design Architect

---

## PART 0 — STRATEGIC ANALYSIS & SYSTEM ACTIVATION

### Systems Activated (Multi-Layer Stack)

**PRIMARY: `stitch-skill` (Dashboard Composition Engine)**
Reuni is not a simple consumer marketplace — it is a B2B sustainability data platform where the marketplace is the data-generation mechanism. The entire shell, metric dashboards, circulation logs, and admin panels require a dense, modular component-stitching approach where every piece fits together seamlessly. `stitch-skill` governs all dashboard and data-heavy surfaces.

**SECONDARY: `soft-skill` (Consumer-Facing Warmth Layer)**
The student-facing marketplace must feel native to the Depop/Vinted world — fluid, card-first, tactile micro-interactions, and haptic depth on mobile. `soft-skill` governs all marketplace pages (index, item detail, listing form, PIN handshake) where the target demographic is 18–25-year-old students.

**TERTIARY: `impeccable-skill` (Pixel-Perfect Execution Enforcer)**
Applied globally as the quality gate. Contrast verification, typography rules, z-index discipline, and the elimination of all AI design tells are enforced at every surface.

**MOTION INJECTION: `emil-kowalski-skill` logic**
Spring physics on card reveals, staggered cascade on dashboard metrics, magnetic hover on primary CTAs, and tactile press states on the PIN numeric input — applied specifically on the PIN handshake page and the ESG dashboard.

### Atmosphere Profile

```
Density:  5/10 — "Daily App Balanced" (not clinical, not sparse)
Variance: 6/10 — "Offset Asymmetric" (cards vary in weight, grids break symmetry)
Motion:   6/10 — "Fluid CSS" (spring physics on key surfaces, not cinematic)
Register: Product (design SERVES the platform, never decorates it)
```

### Activation Rationale by Audience

| User Type | Design Register | Dominant Skill |
|-----------|----------------|----------------|
| Students (18–25, Depop/Vinted natives) | Warm, fast, tactile, mobile-first | `soft-skill` |
| Partner/Admin (sustainability officers, university staff) | Data-dense, trustworthy, precise | `stitch-skill` |
| Auth pages (all users) | Minimal, trustworthy, frictionless | `impeccable-skill` |

### Sidebar Removal Decision — STRATEGIC

**The sidebar is removed.** This is not purely cosmetic — it is a strategic experience decision:

> Admin, partner, and student users must feel they share the **same platform**. A sidebar present only for some roles would create a visual schism that signals "B2B tool" vs "student app." Instead, the marketplace IS the front page for every role. The ESG Dashboard and Admin Panel are accessed via the **top navbar profile dropdown** — appearing only for the authenticated roles that hold them. The bottom mobile tab bar is universal. This enforces the "campus circular economy infrastructure" framing: the sustainability data layer is embedded in the same experience, not separated into a corporate portal.

---

## PART 1 — DESIGN TOKEN SYSTEM (MASTER SPECIFICATION)

### 1.1 Color Palette (Strict — Do Not Deviate)

All colors must be declared as CSS custom properties on `:root` and `[data-theme="dark"]`. These are the exact committed brand tokens. No new colors may be introduced without explicit justification.

```css
/* ——— LIGHT MODE (Default) ——— */
:root {
  /* Backgrounds */
  --color-bg:              #FAF7F2;  /* Warm Canvas — paper-like background */
  --color-surface:         #FFFFFF;  /* Cards, navbar, modal fills */
  --color-surface-raised:  #F4F0E8;  /* Warm Stone-100 — inputs, nested panels */

  /* Borders */
  --color-border:          rgba(28, 25, 23, 0.12); /* Warm Stone-based whisper lines */

  /* Ink */
  --color-ink-primary:     #1C1917;  /* Warm Ink (Stone-950) — headlines, active labels */
  --color-ink-secondary:   #44403C;  /* Stone-700 — body copy, secondary labels */
  --color-ink-tertiary:    #706A64;  /* Stone-600 — timestamps, placeholders (passes 4.5:1 on canvas) */

  /* Brand — Teal (Sustainability) */
  --color-primary:         #0F766E;  /* Deep Teal (Teal-700) — brand, active state, kg_saved */
  --color-primary-hover:   #115E59;  /* Teal-800 — hover state */
  --color-primary-muted:   #CCFBF1;  /* Teal-100 — chip fills, success zones */

  /* Brand — Orange (Urgency/Action - CTAs ONLY) */
  --color-accent:          #B44018;  /* Burnt Terracotta — claim and buy CTAs only (76% saturation, passes AAA contrast on white text) */
  --color-accent-hover:    #8E3213;  /* Deeper terracotta — hover state */
  --color-accent-muted:    #FFF7ED;  /* Orange-50 — urgency panel fills */

  /* Semantic */
  --color-danger:          #C81E1E;  /* Red-700 — errors, destructive, delete (passes 4.5:1 on canvas) */
  --color-danger-muted:    #FEF2F2;  /* Red-50 — error background fills */
  --color-success:         #15803D;  /* Green-700 — sold, verified, free */
  --color-success-muted:   #F0FDF4;  /* Green-50 — success tag fills */
  --color-warning:         #B45309;  /* Amber-700 — PIN expiry, late cancel (passes 4.5:1 on canvas) */
  --color-warning-muted:   #FFFBEB;  /* Amber-50 — warning banner fills */
}

/* ——— DARK MODE ——— */
[data-theme="dark"] {
  --color-bg:              #1C1917;  /* Stone-950 */
  --color-surface:         #292524;  /* Stone-900 */
  --color-surface-raised:  #44403C;  /* Stone-700 */
  --color-border:          rgba(120, 113, 108, 0.2);
  --color-ink-primary:     #F5F5F4;  /* Stone-100 */
  --color-ink-secondary:   #D6D3D1;  /* Stone-300 — readable on surface-raised (passes 4.5:1) */
  --color-ink-tertiary:    #87807B;  /* Stone-500 — timestamps, placeholders (readable on dark surfaces) */
  --color-primary:         #2DD4BF;  /* Teal-400 — lightened for contrast. NOTE: NEVER use with white text (use dark text #1C1917 instead) */
  --color-primary-hover:   inherit;
  --color-primary-muted:   rgba(13, 148, 136, 0.15);
  --color-accent:          #F97316;  /* Orange-500 */
  --color-accent-hover:    inherit;
  --color-accent-muted:    rgba(234, 88, 12, 0.12);
  --color-danger:          #F87171;  /* Red-400 */
  --color-danger-muted:    rgba(239, 68, 68, 0.15);
  --color-success:         #4ADE80;  /* Green-400 */
  --color-success-muted:   rgba(21, 128, 61, 0.15);
  --color-warning:         #FBBF24;  /* Amber-400 */
  --color-warning-muted:   rgba(217, 119, 6, 0.15);
}
```

**Banned color patterns:**
- NO pure `#000000` black — use `--color-ink-primary`
- NO neon outer glows or purple gradients
- NO warm/cool grey oscillation — Slate family only, always
- NO additional accent colors without strategic justification

---

### 1.2 Typography System

```css
/* Font Families */
--font-sans: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif;
--font-mono: 'JetBrains Mono', 'Fira Code', monospace;

/* Type Scale */
--type-display: clamp(1.875rem, 4vw, 2.625rem);   /* Page titles, hero heads */
--type-title:   clamp(1.25rem, 2.5vw, 1.625rem);  /* Section heads, modal heads */
--type-body-lg: 1.0625rem;                          /* Featured body intros */
--type-body:    0.9375rem;                          /* Base body, descriptions */
--type-small:   0.8125rem;                          /* Form labels, metadata */
--type-micro:   0.6875rem;                          /* Card timestamps, categories */

/* Line Heights */
--leading-display: 1.15;
--leading-title:   1.3;
--leading-body:    1.65;

/* Letter Spacing — CRITICAL FLOORS */
/* display: min -0.03em (NEVER below -0.04em — letters touch = cramped) */
/* title: -0.01em to -0.02em */
/* body: 0em (normal) */

/* Font Weights */
/* Headings: 700–800 */
/* Labels/badges: 500–600 */
/* Body: 400 */
/* Mono (kg values, PINs): 600–800 */
```

**Typography Rules (Non-Negotiable):**
- `--font-mono` is MANDATORY for: all `kg_saved` values, PIN digits, countdown timers, price tags (large format), timestamps
- Body text max-width: `65ch` (reading comfort)
- Use `text-wrap: balance` on `h1–h3`
- Display headings: letter-spacing floor is `−0.03em`, hard floor is `−0.04em`
- Inter, Roboto, Arial: BANNED

---

### 1.3 Spacing System

```css
/* 4px base grid */
--space-1:  4px;
--space-2:  8px;
--space-3:  12px;
--space-4:  16px;
--space-5:  20px;
--space-6:  24px;
--space-8:  32px;
--space-10: 40px;
--space-12: 48px;
--space-16: 64px;
--space-20: 80px;
```

**Padding Constraints by Surface Type:**

| Surface | Internal Padding | Notes |
|---------|-----------------|-------|
| Marketplace cards | `--space-3` (12px) | Compact, information-dense |
| Form containers | `--space-8` (32px) side, `--space-10` (40px) top/bottom | Breathing room |
| Dashboard metric panels | `--space-6` (24px) | Balanced density |
| Modal / drawer | `--space-6` (24px) top/bottom, `--space-8` (32px) sides | Premium feel |
| Page body (desktop) | `--space-8` (32px) side padding, `--space-10` (40px) top | Content breathing |
| Navbar inner | `--space-4` (16px) top/bottom, `--space-6` (24px) sides | Tight but not cramped |

---

### 1.4 Border Radius Scale

```css
--radius-sm:   6px;    /* Mini tags, category chips, filter pills */
--radius-md:   10px;   /* Form inputs, action buttons, alert boxes */
--radius-lg:   12px;   /* Standard cards — ENFORCED STRICTLY */
--radius-xl:   16px;   /* Modals, mobile drawer, search overlay */
--radius-full: 9999px; /* Pill toggles, user avatar initials */
```

---

### 1.5 Elevation System

```css
--shadow-card:  0 1px 3px rgba(0,0,0,0.06), 0 4px 16px rgba(0,0,0,0.04);
--shadow-raised: 0 4px 12px rgba(0,0,0,0.08), 0 12px 40px rgba(0,0,0,0.06);
--shadow-modal: 0 20px 60px rgba(0,0,0,0.15);
```

---

### 1.6 Motion System

```css
/* Custom easing — NO linear, NO ease-in-out */
--ease-out:     cubic-bezier(0.16, 1, 0.3, 1);       /* Primary reveals */
--ease-spring:  cubic-bezier(0.34, 1.56, 0.64, 1);   /* Spring elements, badges */
--ease-smooth:  cubic-bezier(0.32, 0.72, 0, 1);       /* Navigation, overlays */

/* Duration Scale */
--duration-fast:   150ms;  /* Hover color, border states */
--duration-mid:    250ms;  /* Button state changes */
--duration-slow:   350ms;  /* Card reveals, drawer slides */
--duration-xslow:  500ms;  /* Page transitions, modal entrance */
```

**Motion Rules:**
- Animate ONLY via `transform` and `opacity` (never `top`, `left`, `width`, `height`)
- `backdrop-filter: blur()` — ONLY on fixed/sticky elements (navbar, modal backdrop)
- `will-change: transform` — sparingly, only on actively animating elements
- `@media (prefers-reduced-motion: reduce)` — required on every animation block; substitute crossfade or instant transition
- Staggered list reveals: `animation-delay: calc(var(--index) * 0.05s)` pattern only

---

### 1.7 Z-Index Scale

```css
--z-base:    1;
--z-raised:  10;    /* Sticky filter bars, banners */
--z-dropdown: 100;  /* Profile dropdown, category dropdown */
--z-sticky:  200;   /* Navbar (desktop), bottom tab bar (mobile) */
--z-drawer:  500;   /* Mobile slide drawer */
--z-modal:   700;   /* Dialog modals, search overlay */
--z-toast:   900;   /* Flash messages */
--z-tooltip: 1000;  /* Tooltips */
```

**No arbitrary values. Never `z-index: 999` or `z-index: 9999`.**

---

### 1.8 Icon System

- **Library:** Google Material Symbols, `outlined` style
- **All decorative icons:** `aria-hidden="true"`
- **All interactive icon buttons:** must have `aria-label` text
- **Size standard:** `20px` inline, `24px` standalone/button-embedded
- Banned: Thick-stroked Lucide defaults, FontAwesome solid variants

---

## PART 2 — SHELL ARCHITECTURE (NO SIDEBAR)

### 2.1 Desktop Top Navigation Bar (`.navbar`)

**Geometry:**
- Position: `sticky; top: 0; z-index: var(--z-sticky)`
- Height: `56px`
- Background: `var(--color-surface)` with `backdrop-filter: blur(20px)` and `background-opacity: 0.92`
- Top Accent Line: `position: absolute; top: 0; left: 0; right: 0; height: 3px; background: linear-gradient(90deg, #0D9488, #059669, #0ea5e9, #0F766E)`
- Border bottom: `1px solid var(--color-border)`
- Shadow: `var(--shadow-card)`

**3-Zone Layout (CSS Grid: `auto 1fr auto`):**

**Zone 1 — Left: Brand Logo**
- Recycling icon (Material Symbols `recycling`) in `--color-primary`, `20px`
- Wordmark "Reuni" — `--font-sans`, `18px`, `font-weight: 600`, `--color-ink-primary`
- Gap between icon and text: `--space-2`
- Clicking navigates to `/` (marketplace)

**Zone 2 — Center: Search Bar**
- Width: `320px`, height: `38px`, `border-radius: var(--radius-md)`
- Background: `var(--color-surface-raised)`
- Border: `1.5px solid var(--color-border)`
- Focus state: border becomes `1.5px solid var(--color-primary)` with `box-shadow: 0 0 0 3px var(--color-primary-muted)`
- Left icon: `search` (Material Symbol), `16px`, `--color-ink-tertiary`
- Placeholder: "Search items..." `--type-small`, `--color-ink-tertiary`
- On focus: opens search overlay (full-screen) — the input itself does NOT expand on desktop to avoid layout shift. Autofocuses input inside overlay.

**Zone 3 — Right: Controls**

*Always Visible:*
- Theme Toggle: Ghost button `36px × 36px`, `border-radius: var(--radius-md)`. Shows `light_mode` sun icon (light) or `dark_mode` moon icon (dark). Transition: `transform: rotate(20deg)` + opacity on toggle.

*Authenticated:*
- Avatar Button: `36px × 36px` circle (`border-radius: var(--radius-full)`). Background: `var(--color-primary-muted)`. Letter: user's first initial, `--font-sans`, `14px`, `font-weight: 700`, `--color-primary`. Opens profile dropdown on click.

*Unauthenticated:*
- "Log in" — ghost button, `--radius-md`, `--color-ink-secondary`
- "Sign up" — filled button, `background: var(--color-primary)`, white text

**Profile Dropdown (`.navbar__dropdown`):**
- Position: `absolute; right: 0; top: calc(100% + 8px)`, width: `220px`
- Background: `var(--color-surface)`, `border-radius: var(--radius-xl)`, `box-shadow: var(--shadow-raised)`
- Border: `1px solid var(--color-border)`
- Entrance animation: `transform: translateY(-4px) scale(0.98) → translateY(0) scale(1)`, `opacity: 0 → 1`, `--duration-mid`, `--ease-out`
- Contains:
  - **Header block:** User name (bold), email (`--type-small`, `--color-ink-tertiary`)
  - **Divider:** `1px solid var(--color-border)`
  - **Navigation Links** (each `40px` tall, `border-radius: var(--radius-md)`, hover: `background: var(--color-surface-raised)`):
    - My Dashboard → `/dashboard`
    - My Profile → `/profile`
    - Settings → `/settings`
  - **Conditional Links (role-gated, above divider):**
    - ESG Dashboard (if `role == partner` OR `role == admin`) → `/partner/dashboard`
    - Admin Panel (if `role == admin`) → `/admin/partners`
  - **Divider**
  - **Sign Out** → `/auth/logout`, text `--color-danger`

---

### 2.2 Mobile Top Bar (`.mobile-top-bar`)

- Position: `fixed; top: 0; left: 0; right: 0; z-index: var(--z-sticky)`
- Height: `56px`
- Background: `var(--color-surface)` with `backdrop-filter: blur(20px)`
- Border bottom: `1px solid var(--color-border)`
- Top Accent Line: same 3px gradient as desktop

**3-Zone Layout (flex, space-between):**
- **Left:** Hamburger button (`menu` icon, `24px`) — opens slide drawer from the left.
- **Center:** Wordmark "Reuni" — `--font-sans`, `18px`, `font-weight: 700`
- **Right:** Theme toggle icon button (`36px × 36px`)

---

### 2.3 Mobile Navigation Drawer (`.mobile-drawer`)

- Position: `fixed; top: 0; left: 0; bottom: 0; z-index: var(--z-drawer)`
- Width: `280px`
- Background: `var(--color-surface)`
- `border-radius: 0 var(--radius-xl) var(--radius-xl) 0`
- Shadow: `var(--shadow-modal)`
- Entrance: `transform: translateX(-100%) → translateX(0)`, `--duration-slow`, `--ease-out`
- Backdrop: `position: fixed; inset: 0; background: rgba(0,0,0,0.4); backdrop-filter: blur(4px); z-index: calc(var(--z-drawer) - 1)`

**Drawer Contents:**
- **Header (72px tall):** User avatar initial (large, `48px` circle) + name + email
- **Nav links list:** each link `44px` tall, `border-radius: var(--radius-md)`, `--space-4` horizontal padding, icon (left, `20px`) + label text
  - Home, Browse, Sell, My Dashboard, My Profile
  - ESG Dashboard (partner/admin only)
  - Admin Panel (admin only)
  - Settings
- **Footer:** Sign Out link in danger color + app version `--type-micro`
- **Close button:** `position: absolute; top: --space-4; right: --space-4`, `close` icon

---

### 2.4 Mobile Bottom Tab Bar (`.mobile-tabs`)

- Position: `fixed; bottom: 0; left: 0; right: 0; z-index: var(--z-sticky)`
- Height: `60px` + `env(safe-area-inset-bottom)` for iPhone home bar
- Background: `var(--color-surface)` with `backdrop-filter: blur(20px)`
- Border top: `1px solid var(--color-border)`

**4-Tab Layout (flex, space-around):**

| Tab | Icon | Label | Route |
|-----|------|-------|-------|
| Home | `home` | Home | `/` |
| Search | `search` | Search | Opens full-screen overlay |
| Sell | `add` (in `--color-primary` circle, elevated) | — | `/items/new` |
| Profile | User initial avatar | Profile | `/profile` or `/auth/login` |

**Sell Tab — Elevated Pill:**
- `width: 48px`, `height: 48px`, `border-radius: var(--radius-full)`
- Background: `--color-primary`, icon: `add` in `#FFFFFF`, `24px`
- `box-shadow: 0 4px 12px rgba(13, 148, 136, 0.35)` (tinted teal glow — ONLY acceptable glow in the system)
- Position: `margin-top: -12px` (floats above the tab bar)

**Active State:** Icon + label in `--color-primary`. Inactive: `--color-ink-tertiary`.
**Label text:** `10px`, `font-weight: 500`, below icon, `4px` gap.

---

### 2.5 Flash Message System (`.flash-messages`)

- Position: Below the sticky navbar, before page content; NOT toast
- Each message: `border-radius: var(--radius-md)`, `--space-3` padding vertical, `--space-4` padding horizontal
- Left border: `4px solid [semantic color]`
- Background: `[semantic-muted color]`
- Icon: left-aligned Material Symbol (`check_circle`, `error`, `warning`, `info`)
- Dismiss `×` button: right-aligned, ghost
- **NO slide animations** — appears instantly in DOM flow

| Type | Border | Background |
|------|--------|------------|
| Success | `--color-success` | `--color-success-muted` |
| Danger | `--color-danger` | `--color-danger-muted` |
| Warning | `--color-warning` | `--color-warning-muted` |
| Info | `--color-primary` | `--color-primary-muted` |

---

### 2.6 Full-Screen Search Overlay (`.search-overlay`)

- Position: `fixed; inset: 0; z-index: var(--z-modal)`
- Background: `var(--color-bg)`
- Entrance: `opacity: 0 → 1`, `--duration-mid`, `--ease-out`

**Structure (top → down):**
1. **Search Header Bar** (`56px`, background: `var(--color-surface)`, border-bottom: `1px solid var(--color-border)`):
   - Search input (full-width, `44px` height, `--radius-md`)
   - `search` icon left, `close` icon button right
   - Auto-focus on open
2. **Content Area:**
   - Label: "Recent Searches" (`--type-small`, `--color-ink-tertiary`)
   - Horizontal scrolling chips (`.filter-chip` pattern) of past queries
   - Trash icon button to clear all history
   - On typed query: live results preview (if wired server-side)

---

### 2.7 Global Campus Impact Counter (Footer Widget)

**Strategic intent:** Visible proof of campus-wide sustainability momentum. Reinforces the B2B value proposition at the page bottom for every visitor. The single number that makes Reuni's ESG claim tangible.

**Location:** Footer block, present on ALL pages (via `base.html` shell).

**Desktop Layout:**
- Footer container: `background: var(--color-surface); border-top: 1px solid var(--color-border); padding: var(--space-8) var(--space-8);`
- Impact widget (left-aligned): `display: inline-flex; align-items: center; gap: var(--space-3);`
  - `eco` icon: 20px, `--color-success`
  - Text string: `[campus_total_kg] kg saved at Brookes`
    - `[campus_total_kg]` — `--font-mono`, `font-weight: 700`, `font-size: 17px`, `--color-primary`
    - `" kg saved at Brookes"` — `--font-sans`, `--type-body`, `font-weight: 400`, `--color-ink-secondary`
- Footer secondary content (right-aligned): Links: *Privacy Policy · © 2026 Reuni* (`--type-small`, `--color-ink-tertiary`, hover: `--color-ink-secondary`, separated by a center dot).

**Mobile Layout:**
- Same widget, centered rather than left-aligned. Padding reduced to `var(--space-6)`.

**Data binding:**
- `campus_total_kg` = sum of all `kg_saved` across all `items` where `status = 'sold'` and `university_domain = current_university`. Calculated server-side (Jinja2) to 1 decimal place.

---

## PART 3 — PAGE BLUEPRINTS

---

### PAGE 1 — MARKETPLACE INDEX (`/` · `index.html`)

**Page Role:** Universal entry point — students browse, buy, or discover. The platform's face for all roles.

**Desktop Layout (`≥1024px`):**
- **Eliminated sidebar** — content area is now full-width inside the page container.
- Page container: `max-width: 1280px`, `margin: 0 auto`, `padding: 0 var(--space-8)`
- Three-tier top section:
  1. **Marketplace Hero Strip** (Context-aware registration/impact strip)
  2. **Category filter strip** (horizontal scrollable chips)
  3. **Filter/sort control bar** (condition, price, price range)

**Mobile Layout (`<1024px`):**
- Category filter strip edge-to-edge (no horizontal padding, overflow-x scroll, `overscroll-behavior-x: contain`)
- Filter bar collapses into a single "Filters" button that opens a bottom sheet.

---

**Component: Marketplace Hero Strip**

**Height:** `80px` (desktop and mobile)

*Unauthenticated State:*
- Background: `var(--color-primary)`
- Layout: flex, align-items: center, justify-content: space-between
- Padding: `0 var(--space-8)` (desktop) / `0 var(--space-4)` (mobile)
- **Left block:**
  - Line 1: *"Campus items. Real kg saved."* (`18px`, `font-weight: 600`, white, `--font-sans`)
  - Line 2: *"Student-to-student. In person. No fees."* (`14px`, `font-weight: 400`, white opacity 0.75, margin-top: `--space-1`)
  - *Mobile behavior:* Show only Line 1 (or stack vertically if space permits).
- **Right block:**
  - CTA Button: *"Register free →"* (background: white, text: `var(--color-primary)`, `--radius-md`, 40px height, `--type-small` semibold, hover transition). Mobile: text scales to *"Join free →"*.

*Authenticated State:*
- Background: `var(--color-surface)`, `border-bottom: 1px solid var(--color-border)`
- Layout: flex, align-items: center, gap: `var(--space-3)` (12px), horizontal overflow-x auto (mobile)
- **Three horizontal stat chips (`.hero-stat-chip`):**
  - Card style: `background: var(--color-surface-raised); border-radius: var(--radius-full); padding: 12px 16px; display: inline-flex; align-items: center; gap: var(--space-2);`
  - Chip 1: `eco` icon (16px, `--color-success`) + `user.kg_saved_total` (`--font-mono` 700, `--color-primary`) + *"saved"* text (`--type-micro`).
  - Chip 2: `inventory_2` icon + listing count (`--font-mono` 700, `--color-ink-primary`) + *"listed"* text.
  - Chip 3: `shopping_bag` icon + purchase count (`--font-mono` 700, `--color-ink-primary`) + *"purchased"* text.
  - *Mobile:* scrollable horizontally, chips never wrap, scrollbars hidden.

---

**Component: Category Filter Strip (`.category-strip`)**

- Height: `52px`, `overflow-x: auto`, horizontal padding `var(--space-4)` on first/last chip (visual margin)
- Chips: `display: inline-flex`, `align-items: center`, `height: 36px`, `border-radius: var(--radius-full)`, `padding: 0 var(--space-4)`, `--type-small` semibold.

| State | Background | Text | Border |
|-------|-----------|------|--------|
| Default | `--color-surface-raised` | `--color-ink-secondary` | `1px solid var(--color-border)` |
| Active | `--color-primary` | `#FFFFFF` | none |
| Hover | `--color-primary-muted` | `--color-primary` | `1px solid var(--color-primary)` |
| Focus | Default + `3px solid var(--color-primary)` outline offset `2px` | — | — |

**Categories List (8 chips):** All · Furniture · Kitchenware · Electronics · Sports · Clothing · Books · Stationery · Other

---

**Component: Filter/Sort Control Bar (`.filter-bar`)**

Desktop — single row, flex, `align-items: center`, `gap: var(--space-3)`:
- Condition select: "Any Condition" dropdown (`--radius-md`, `40px` height)
- Price type toggle: ghost buttons "All · Free · Paid"
- Min/Max price inputs: side-by-side `80px` inputs with `£` prefix, appear only when "Paid" selected
- Sort dropdown: "Newest first / Price: low-high / Price: high-low / Most eco-friendly"
- Result count: `--type-small`, `--color-ink-tertiary`, pushed right

---

**Component: Listings Grid (`.listings-grid`)**

```
Desktop: grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: var(--space-5)
Mobile: grid-template-columns: repeat(2, 1fr); gap: var(--space-3)
```

**Card Stagger Animation:**
```css
@keyframes scaleIn {
  from { transform: scale(0.96) translateY(8px); opacity: 0; }
  to   { transform: scale(1) translateY(0); opacity: 1; }
}
.listing-card { animation: scaleIn 0.3s var(--ease-out) forwards; animation-delay: calc(var(--card-index) * 0.05s); }
@media (prefers-reduced-motion: reduce) { .listing-card { animation: none; opacity: 1; } }
```

---

**Component: Item Card (`.listing-card`)**

Structure (outer shell → inner):
- Outer: `background: var(--color-surface)`, `border-radius: var(--radius-lg)`, `box-shadow: var(--shadow-card)`, `overflow: hidden`
- Hover: `transform: translateY(-2px)`, `box-shadow: var(--shadow-raised)`, `transition: var(--duration-mid) var(--ease-out)`

**Image Block (top 60% of card):**
- Aspect ratio: `4:3`, `object-fit: cover`
- Fallback: `var(--color-surface-raised)` + `image` icon centered in `--color-ink-tertiary`
- Overlay tags (absolute positioned):
  - Top-left: Category chip — `background: rgba(255,255,255,0.9)` (light) or `rgba(30,41,59,0.9)` (dark), `border-radius: var(--radius-sm)`, `--font-mono`, `--type-micro`, `font-weight: 600`, `padding: 3px 8px`
  - Top-right: Condition tag — pill shape, semantic color fill:
    - "Like New" → `--color-success-muted` / `--color-success` text
    - "Good" → `--color-primary-muted` / `--color-primary` text
    - "Fair" → `--color-warning-muted` / `--color-warning` text

**Content Block (bottom 40%):**
- Padding: `var(--space-3)`
- Title: `--font-sans`, `--type-body`, `font-weight: 600`, `--color-ink-primary`, `line-clamp: 2`
- Row 2 (flex, justify-between, align-center):
  - **Eco badge** (left): `border-radius: var(--radius-full)`, `background: var(--color-success-muted)`, `padding: 3px 8px`, `eco` icon (`14px`, `--color-success`) + kg value in `--font-mono`, `--type-micro`, `font-weight: 600`, `--color-success`
  - **Price** (right): `--font-mono`, `--type-body`, `font-weight: 700` — if paid: `--color-accent`; if free: `--color-success`
- Timestamp: `--type-micro`, `--color-ink-tertiary`, `margin-top: var(--space-1)`

---

**Component: Pagination**
- Centered, `margin-top: var(--space-10)`
- "Previous" / page numbers / "Next" — ghost buttons, active page filled with `--color-primary`
- `--radius-md`, `40px × 40px` minimum tap target

**Empty State (no listings):**
- Centered composition, `margin-top: var(--space-20)`
- Large icon: `shopping_bag` or `recycling`, `48px`, `--color-ink-tertiary`
- Heading: "Nothing here yet" — `--type-title`, `font-weight: 700`
- Subtext: "Be the first to list something on campus." — `--type-body`, `--color-ink-secondary`
- CTA: "List an item" filled teal button → `/items/new`

---

### PAGE 2 — ITEM DETAIL (`/items/<id>` · `items/detail.html`)

**Page Role:** Converts browse intent into claim action. The most conversion-critical page.

**Desktop Layout (`≥1024px`):**
- Two-column grid: 55% image | 45% info panel. Max-width: 1100px centered. Gap: `var(--space-12)`. Padding: `var(--space-8)` horizontal.

**Mobile Layout (`<1024px`):**
- Single column: image full-width at top, content below. Image aspect ratio: 4:3.

---

**Component: Item Photo (`.detail-photo`)**
- Desktop: `border-radius: var(--radius-lg)`, `box-shadow: var(--shadow-card)`
- Mobile: no border-radius, edge-to-edge (full bleed)
- Status overlay ribbon (if claimed): `position: absolute; top: 0; right: 0`, `background: var(--color-warning)`, white text "Claimed", angled via CSS triangle ribbon technique.

---

**Component: Info Panel (`.detail-info`)**

Vertical stack, `gap: var(--space-5)`:
1. **Header Row:**
   - Category chip (teal pill) + Condition tag (semantic pill)
   - Title: `--type-display`, `font-weight: 800`, `--color-ink-primary`, `text-wrap: balance`
   - Listed by: `--type-small`, `--color-ink-tertiary` → link to seller's profile
2. **Price Row:**
   - If paid: `--font-mono`, `clamp(1.5rem, 3vw, 2rem)`, `font-weight: 800`, `--color-accent`
   - If free: "Free" in same size, `--color-success`
3. **Eco Impact Block (`.eco-block`):**
   - Background: `var(--color-primary-muted)`, `border-radius: var(--radius-md)`, `padding: var(--space-4)`
   - `eco` icon (24px, `--color-primary`) + "Saving X.X kg from landfill" text (`--font-mono` for the number)
   - Sub-label: "Based on WRAP UK material weight data" — `--type-micro`, `--color-ink-tertiary`
4. **Description:**
   - `--type-body`, `--color-ink-secondary`, `leading-body`
   - Max visible: 150 words, "Show more" toggle
5. **Meta row:**
   - Listed: relative timestamp (`--type-small`, `--color-ink-tertiary`)
6. **CTA Button Block — State Machine:**

| State | Appearance | Trigger Condition |
|-------|-----------|------------------|
| **Available** | Full-width filled orange: "Claim this item" / "Pay and Claim" | `item.status == 'available'` AND `not anti-griefed` |
| **Anti-griefed** | Full-width, disabled, grey background, `opacity: 0.4`, `pointer-events: none`; label: "Unavailable (Previous claim cancelled)" | User previously cancelled claim on this item |
| **Claimed by self** | Teal filled: "View PIN Handshake" → `/items/<id>/pin` | User is current buyer |
| **Own listing** | Two ghost buttons: "Edit listing" + "Delete listing" | User is the seller |
| **Claimed by other** | Grey disabled: "Currently claimed" | Item has buyer, viewer is different user |
| **Sold** | Grey disabled: "Sold" | `item.status == 'sold'` |

**Mobile Sticky CTA:**
```css
@media (max-width: 1023px) {
  .cta-sticky {
    position: fixed;
    bottom: calc(60px + env(safe-area-inset-bottom));
    left: 0; right: 0;
    padding: var(--space-3) var(--space-4);
    background: var(--color-surface);
    border-top: 1px solid var(--color-border);
    z-index: var(--z-raised);
  }
}
```
The sticky CTA sits ABOVE the bottom tab bar (60px + safe area offset).

---

### PAGE 3 — PIN HANDSHAKE (`/items/<id>/pin` · `items/pin.html`)

**Page Role:** The physical transaction bridge. The most UX-critical page in the entire system. Must inspire trust and clarity.

**Layout:** Max-width `640px` centered. Padding: `var(--space-8)` horizontal, `var(--space-10)` vertical. Vertical stack with `gap: var(--space-6)`.

---

**Component: Item Context Header**
- Small image thumbnail (`64px × 64px`, `border-radius: var(--radius-md)`) + item title + price
- "Transaction in progress" eyebrow badge: pill, `--color-warning-muted`, `--color-warning`, `--type-micro`, uppercase, tracking `0.1em`

---

**Component: WhatsApp Coordination Block (buyer only) (`.whatsapp-block`)**
- Border: `1px solid var(--color-border)`, `border-radius: var(--radius-lg)`, padding: `var(--space-5)`
- Header: `chat` icon + "Contact the seller" label (`--type-small`, `font-weight: 600`)
- **WhatsApp button:** `background: #25D366`, `color: #FFFFFF`, width: `100%`, `border-radius: var(--radius-md)`, `height: 48px`; `chat` icon left + "Open WhatsApp" label
- **Deep link message formatting:** The WhatsApp link must pre-fill the seller's number and this exact encoded message body:
  `https://wa.me/[seller_phone_e164]?text=Hey%2C+I+just+claimed+your+[ENCODED_TITLE]+on+Reuni.+When+can+we+meet+for+the+PIN+handshake%3F`
- **Copy message button:** ghost text link below; on click, copy the pre-filled text, change label to `"Copied ✓"` in `--color-success` for `1000ms`, then revert.

---

**Component: PIN Display Card — Holder Role (`.pin-display-card`)**
- Background: `var(--color-surface)`, `border-radius: var(--radius-xl)`, `box-shadow: var(--shadow-raised)`, padding: `var(--space-8)`
- Header: "Your PIN Code" (`--type-title`, `font-weight: 700`) + **Role-Aware PIN Instruction Headers**:
  - *Seller free item:* `"Share this PIN with the buyer when they confirm collection."`
  - *Buyer paid item:* `"Share this PIN with the seller after inspecting the item and sending payment."`
  - *Buyer free item:* `"The seller will tell you the 4 digits when you collect."`
  - *Seller paid item:* `"Enter the PIN the buyer gives you after you confirm payment."`

**PIN Digit Display (`.pin-display-wrapper`):**
```
Flex row, centered. Background: var(--color-primary-muted); border-radius: var(--radius-lg); padding: 20px 32px; gap: 0.25em (desktop) / 0.3em (mobile)
```
Each digit: `--font-mono`, size `52px` (desktop) / `56px` (mobile), weight `800` (desktop) / `900` (mobile), `--color-primary`. Separator dots: `.` size `30px`, `--color-ink-tertiary`.

**Countdown Timer (`#expiry-countdown`):**
Default: `--color-ink-tertiary`. `< 2 hours` remaining: `--color-warning`. `< 30 minutes` remaining: `--color-danger` + `warning-pulse` animation. Resend PIN link below.

---

**Component: PIN Input Grid — Enterer Role (`.pin-entry-card`)**
- Same card shell as display card.
- **4-Box OTP Input:**
  - 4 × `input.otp-input` (Desktop: `56px × 64px` / Mobile: `68px × 72px` for touch targets).
  - Background: `var(--color-surface-raised)`, Border: 1.5px solid `var(--color-border)`.
  - Focus: border `var(--color-primary)`, box-shadow 3px `var(--color-primary-muted)`.
  - Error: border `var(--color-danger)`, box-shadow 3px `var(--color-danger-muted)`.
  - `inputmode="numeric"`, `maxlength="1"`, `pattern="[0-9]"`, `autocomplete="off"`.
- **Input Behavior & Keyboard Handling:**
  - Auto-advances focus on valid digit, auto-submits on 4th digit (triggers AJAX validation).
  - Uses `visualViewport` resize listener rather than `window.innerHeight` to prevent mobile keyboard layout overlap. container scrolls smoothly to remain `100px` below visible top.
  - Error state after incorrect PIN: shake animation (`shake` keyframes) + error message below.

---

**Component: High-Value Advisory Block (≥£100)**
- Background: `var(--color-warning-muted)`, `border: 1px solid var(--color-warning)`, padding: `var(--space-4)`, visible only when `item.price >= 100`.
- Material Symbol `warning` + *"For items over £100, we recommend meeting at the SU reception desk..."*

---

**Component: Safe Exchange Guide Accordion**
- `<details id="safe-exchange-details">` native element.
- Summary: `"🤝 Safe Exchange Guide"`
- Desktop: always open. Mobile: open on first visit (localStorage check), collapsed subsequently.
- Content: 5-step numbered list.

---

**Component: Cancellation Block (`.cancellation-block`)**
- Within 24h: success-muted bg, success border, schedule icon + *"Free cancellation — Xh Ym left..."*
- After 24h: warning-muted bg, warning border, warning icon + *"Late cancellation — cancels trigger penalty"*
- Cancel CTA: ghost danger button. On click: hides, showing inline confirmation: `Yes, cancel` (filled danger) and `Never mind` (ghost outline). Stacked on mobile, side-by-side on desktop.

---

**Component: Success State (after correct PIN)**
- Replaces card in-place (no page navigation).
- `check_circle` icon (64px, `--color-success`, spring entrance animation).
- **KG Saved Block:** success-muted bg, large number `[kg]` (`--font-mono` 48px, counts up from 0 to actual over 1000ms), text: *"kg saved from landfill"*.
- Back to marketplace link.

---

### PAGE 4 — LISTING FORM (`/items/new` · `list_item.html`) & EDIT FORM (`/items/<id>/edit` · `edit_item.html`)

**Layout:** Max-width `720px` centered. Vertical stack of sections with `gap: var(--space-8)`.

---

**Component: Photo Upload Zone (`#photo-upload-zone`)**
- Height: `200px` desktop / `160px` mobile. `border: 2px dashed var(--color-border)`, background: `var(--color-surface-raised)`.
- Center: `upload` icon (32px) + *"Drag & drop or tap to upload"* + format rules (JPG, PNG, WebP up to 5MB).
- Drag-over: border `var(--color-primary)`, bg `var(--color-primary-muted)`.
- After upload: object-fit cover preview fills container + absolute top-right *"Remove"* dark badge.

---

**Component: Form Inputs (global standard)**
```
Label: --type-small, font-weight: 600, --color-ink-primary, margin-bottom: var(--space-2)
Input/Textarea:
  border: 1.5px solid var(--color-border); border-radius: var(--radius-md)
  background: var(--color-surface-raised); padding: var(--space-3) var(--space-4)
  --type-body, --color-ink-primary; min-height: 44px
  Focus: border-color: var(--color-primary); box-shadow: 0 0 0 3px var(--color-primary-muted)
  Error: border-color: var(--color-danger); box-shadow: 0 0 0 3px var(--color-danger-muted)
Helper text below: --type-micro, --color-ink-tertiary
```

- **Title Field:** text input, `maxlength="80"`, live character counter (`X/80` turns warning at 60, danger at 75).
- **Description Textarea:** `min-height: 140px`, vertical resize, `maxlength="2000"`, counter (`X/2000`).
- **Category Select:** Native `<select>` styled. On selection: environmental preview banner height transition (`height: 0 -> auto`) + opacity (`0 -> 1`): `eco` icon + *"Selecting [Category] saves ~X.X kg from landfill"*.
- **Condition Segmented Selector:** Custom button row (`.condition-btns-container`). Flex layout, button wrap. Active: primary fill. Hover: primary-muted. Segment options: New · Like New · Good · Fair · For Parts.
- **Price Toggle + Price Input:** Segmented pill toggle ("Free" / "Set Price"). Active: filled primary, white text. Price field input (prefix `£`, type `number`, `min: 0.01`, step `0.01`) hidden by default, slides open on "Set Price" (`max-height: 0 -> 80px`).

---

**Component: Client-Side Validation**
Validation checks on submit: title, category, condition, price, photo. Appends `<p class="custom-error-msg">` below fields, applies error border, and scrolls smoothly: `window.scrollTo({ top: firstErrorField.offsetTop - 80, behavior: 'smooth' })`.

---

### PAGE 5 — USER DASHBOARD (`/dashboard` · `dashboard.html`)

**Page Role:** Personal activity center. Shows active claims, my listings, purchase history.

**Layout:** Max-width `1100px`, centered. Two-column sidebar-free layout on desktop (tabs organize sections).

---

**Component: Personal kg_saved Total Banner**
- Pinned at top of page, above tabs.
- Card: `background: var(--color-primary-muted); border-radius: var(--radius-xl); padding: var(--space-5) var(--space-6)`
- `eco` icon (24px) + *"You've saved X.X kg from landfill"* (`--font-mono` 800 bold, size `clamp(1.25rem, 2vw, 1.75rem)`, primary color) + sub-label *"Across N completed transactions"*.

---

**Component: Dashboard Tabs (`.dashboard-tabs`)**
- Horizontal pill-segmented tab row: "Active Claims" · "My Listings" · "Purchases"
- Count badge on "Active Claims" if active: orange fill badge.

---

**Component: Active Claim Card (`.claim-card`)**
- Left accent border (`4px solid var(--color-accent)`), thumbnail (48px), title, price.
- Role badge: "Buyer" (orange pill) or "Seller" (teal pill).
- Status: "Awaiting PIN exchange" + countdown timer + "View PIN" CTA link.

---

**Component: My Listings Tab**
- Marketplace listing card grid.
- Hover overlay (desktop) or card bottom (mobile) exposes "Edit" and "Delete" ghost danger options.

---

**Component: Purchases Tab**
- List view: thumbnail, title, seller, date, `kg_saved` contribution (`--font-mono`).
- Completed badge: *"Exchanged ✓"* (green filled).

---

### PAGE 6 — PARTNER & ADMIN ESG DASHBOARD (`/partner/dashboard`)

**Page Role:** B2B sustainability reporting interface for partners and admins. Data density level: 7/10.

**Layout:** Max-width `1200px`, centered. Heading block: university logo (Google Favicon API, `48px`, rounded), university name, sub-label. Admin-only domain scope dropdown selector.

---

**Component: KPI Metric Cards (`.metric-grid`)**
4 cards in a grid: grid-template-columns repeat auto-fit minmax 220px. 
Metric items:
1.  **Items Exchanged:** `recycling` icon, `--font-mono` display size, weight 800.
2.  **Kilograms Saved (Dominant):** `eco` icon, `--font-mono` clamp display size, weight 800, color: `--color-success`.
3.  **Verified Students:** `school` icon, weight 800.
4.  **CO₂ Prevented:** `co2` icon, weight 800.
Metric animation: staggered scale-in on mount.

---

**Component: Category Distribution Panel (`.category-distribution`)**
- Card layout, title. Vertical progress bar distribution list (no pie charts).
- Rows: Category icon (Material Symbol) + Category name, center progress bar (teal fill, width animated on mount), right count + kg label.

---

**Component: Live Circulation Log (`.circulation-log`)**
- Shows 5 most recent completed transactions.
- Header: "Recent Exchanges" + Live pulsing green dot badge.
- Rows: `recycling` icon + *"Category item exchanged"*, `kg_saved` value (`--font-mono` 600 success color), relative timestamp.

---

**Component: ESG Copy Block**
- Dashed border card. Eyebrow *"FOR YOUR ESG REPORT"*.
- Copy: *"[University] students exchanged [items] via Reuni, diverting an estimated [kg] kg from landfill..."*
- Right-aligned *"Copy text"* button.

---

### PAGE 7 — ADMIN PARTNER PANEL (`/admin/partners`)

**Page Role:** System admin control panel for partner management. Clean and functional layout.

**Layout:** Max-width `960px` centered. Title + "Admin Panel" badge (teal pill).

---

**Component: Invite Partner Section**
- Card. Heading: *"Invite a New University Partner"*.
- Form row (horizontal flex on desktop, vertical on mobile): .ac.uk domain input + "Generate Invite" primary button.
- On success: success-muted banner showing URL (monospace, truncated, copy button), expiry note, and sustainability officer instructions.

---

**Component: Active Partners Table**
- Table with headers: University (logo + domain), Partner Name, Joined, Status (Active green pill / Inactive grey), Actions (Deactivate ghost danger).
- Deactivate action replaces button inline with confirmation: *"Are you sure?"* + *"Yes"* + *"Cancel"*. Collapses to vertical cards on mobile.

---

### PAGE 8 — PROFILE PAGE (`/profile/<id>` · `profile.html`)

**Layout:** Max-width `720px` centered. Single column.

- **Profile Hero:** Avatar initials circle (`80px`, primary-muted bg, `32px` text), display name, member since, university domain pill.
- **Stats Row:** items listed / total kg saved (monospace, primary color) / completed sales. Separated by vertical border dividers.
- **Listed Items Grid:** Listing cards, 2-3 columns. Shows `status: available` items.

---

### PAGE 9 — SETTINGS PAGE (`/settings` · `settings.html`)

**Layout:** Max-width `680px` centered. Sections separated by `var(--space-12)` vertical gap.

- **Section: Phone Number:** Card layout, current E.164 number, inline edit form (+44 input + update button).
- **Section: Change Password:** Card layout, Current / New / Confirm fields, password strength indicator bar (Weak/Fair/Strong in danger/warning/success colors), update button.
- **Section: Account Deletion (Danger Zone):** Card with red border, danger-muted bg. Explains GDPR erasure, cooling-off period. Delete button triggers confirmation modal requiring typing "DELETE" to confirm.

---

### PAGE 10 — AUTHENTICATION PAGES (`/auth/*`)

**Universal Auth Layout:** card fills screen with `border-radius: 0` on mobile. Card centered `max-width: 440px` on desktop. Background: `var(--color-bg)` with top 4px primary-muted gradient bar.
**Auth Card:** Modal-style card. Brand logo, title, sub-label.

- **Login Page:** Email, Password (show/hide toggle), Forgot password link, Log in button, divider with "or", link to register.
- **Register Page:** Display name, email (.ac.uk validation), phone number (+44, coordination warning), password (+ strength bar), terms checkbox, Create account button.
- **OTP Verification Page:** Title, code details, 6-box OTP input grid (`44px × 52px` each), auto-submit, resend timer link.
- **Forgot/Reset Password:** Single email input form, success state message banner. Reset page has New/Confirm inputs + strength bar.

---

### PAGE 11 — ERROR PAGES (`404.html` / `500.html`)

**Layout:** Vertically centered, full height, max-width `560px`.

- **404:** `search_off` icon (64px, tertiary color), *"Page not found"* title, body text, *"Back to marketplace"* primary button.
- **500:** `error_outline` icon, *"Something went wrong"* title, body text, *"Back to marketplace"* primary button + *"Try again"* ghost button.

---

### PAGE 12 — PRIVACY POLICY PAGE (`/privacy` · `privacy.html`)

**Page Role:** Legal document. Trust-building surface. Typography and readability are the entire product here. This is NOT a card layout, NOT a dashboard — it is a long-form prose document.

**Layout Constraints:**
- Max-width: `720px`, centered. Padding top: `48px`; padding bottom: `80px`. Horizontal padding: `var(--space-8)` (32px) on mobile; `0` on desktop (let max-width do the work).
- Background: `var(--color-bg)` — no surface cards wrapping content.
- Zero card layouts on this page — BANNED here specifically.

**Back Navigation (top of page, before all content):**
- Element: `<a href="/">`
- Icon: `arrow_back` (Material Symbol, 20px, `--color-ink-secondary`)
- Text: `"Back to Reuni"` (`--type-small`, font-weight: 500, `--color-ink-secondary`)
- Layout: inline-flex, align-items: center, gap: `var(--space-2)`. Hover: `--color-primary`, transition: color `var(--duration-fast)` `var(--ease-out)`. Margin-bottom: `var(--space-10)` (40px).

**Page Header:**
- Heading: `"Privacy Policy"` (`--font-sans`, `--type-display`, `font-weight: 800`, `--color-ink-primary`, `text-wrap: balance`, margin-bottom: `var(--space-3)`).
- Last updated timestamp: `"Last updated: [Month DD, YYYY]"` (`--font-mono`, `--type-small`, `--color-ink-tertiary`, `display: block`, margin-bottom: `var(--space-10)`).
- Divider: 1px solid `var(--color-border)`, margin-bottom: `var(--space-10)`.

**Typography Scale (prose document):**

| Element | Font | Size | Weight | Color | Line Height |
|---------|------|------|--------|-------|-------------|
| `h2` section headers | `--font-sans` | `20px` (1.25rem) | `700` | `--color-ink-primary` | `1.3` |
| `h3` sub-headers | `--font-sans` | `16px` (1rem) | `600` | `--color-ink-primary` | `1.3` |
| `p` body text | `--font-sans` | `15px` (0.9375rem) | `400` | `--color-ink-secondary` | `1.7` |
| `a` inline links | `--font-sans` | inherit | `500` | `--color-primary` | inherit |
| `strong` emphasis | `--font-sans` | inherit | `600` | `--color-ink-primary` | inherit |

**Spacing between prose elements:**
- `h2` → paragraph gap: `var(--space-3)` (12px). `h3` → paragraph gap: `var(--space-2)` (8px). Paragraph → paragraph: `var(--space-4)` (16px). Section → section gap: `var(--space-10)` (40px). `h2` top margin: `var(--space-8)` (32px) from previous block.
- Internal anchor links (table of contents — optional): simple ordered list above first `h2` (`--type-small`, `--color-primary`, underline on hover, margin-bottom: `var(--space-8)`).

**STRICTLY BANNED on this page:** Card containers wrapping text blocks, icon decorations beside headings, color backgrounds on sections, bold numbers as metric stats, and any marketplace components.

---

## PART 4 — PHASE 2+ FUTURE UI BANK

---

### B.1 — LEADERBOARD PAGE (`/leaderboard`)

**Phase:** 2 (Gamification & Growth)
**Route:** `/leaderboard` | **Template:** `leaderboard.html`

**Page Role:** Campus-wide sustainability competition surface. Creates social proof and repeat engagement.

**Layout:** Max-width: `800px`, centered. Padding: `var(--space-8)` horizontal.

---

**Component: Tab Selector (`.leaderboard-tabs`)**
- Two tabs: "My University" (active by default) and "All Universities" (Phase 3).
- Tab selector pill pattern (dashboard tabs style). Active: primary fill, white text. Inactive: ghost.

---

**Component: Season Badge (above podium)**
- Pill: background `var(--color-primary-muted)`, `border-radius: var(--radius-full)`, padding: `var(--space-2) var(--space-4)`.
- Icon: `event` (16px, `--color-primary`) + text *"Season 1 — Spring 2026"* (`--type-small` semibold, `--color-primary`) + subtext *"Ends in X days"* (`--type-micro`, `--color-ink-tertiary`). Centered above podium, margin-bottom: `var(--space-6)`.

---

**Component: Top 3 Podium Block (`.podium`)**
- Layout: 3-column flex, `align-items: flex-end`, `justify-content: center`, gap: `var(--space-4)`.

**Podium column structure (each):**
- Flex column, align-items: center.
- Avatar circle: 2nd and 3rd: `48px` / 1st: `56px` (elevated prominence), `border-radius: var(--radius-full)`, `background: var(--color-primary-muted)`.
- Crown icon for 1st: `workspace_premium` icon (24px, `#F59E0B` amber/gold) position absolute, top: -12px centered above avatar.
- Display name: `--type-small` semibold, `--color-ink-primary`.
- kg_saved value: `--font-mono` 700 semibold, `--type-small`, `--color-success`.
- Rank number below name: `--type-micro`, `--color-ink-tertiary` (e.g. `"#1"`, `"#2"`, `"#3"`).

**Podium platform heights (physical step blocks):**
- 2nd place: column height `60px`, background: `var(--color-surface-raised)`.
- 1st place: column height `80px`, background: `var(--color-primary-muted)`, border-top: 2px solid `var(--color-primary)`.
- 3rd place: column height `50px`, background: `var(--color-surface-raised)`.
- Platform width: `80px` each, top corners rounded (`--radius-md var(--radius-md) 0 0`).
- *Asymmetric layout rule:* columns are NEVER equal height. 1st is always visually dominant.

---

**Component: Rankings List (Positions 4–10) (`.leaderboard-list`)**
- Background: `var(--color-surface)`, `--radius-xl`, `--shadow-card`, overflow hidden.
- Rows: height `56px`, padding: `0 var(--space-5)`, border-bottom: 1px solid `var(--color-border)` (last: none), hover: `var(--color-surface-raised)`, flex layout, gap `var(--space-4)`.
  - Left: Rank number (`--font-mono` `--type-small` 700, `--color-ink-tertiary`, width 28px).
  - Avatar: 32px circle, Name (`--type-body` 500, `--color-ink-primary`, flex: 1), kg_saved (`--font-mono` `--type-small` 700, `--color-success`, right-aligned).
- Stagger entrance animation:
  ```css
  .leaderboard-list .leaderboard-row {
    animation: scaleIn 0.25s var(--ease-out) both;
    animation-delay: calc(var(--row-index) * 0.04s);
  }
  @media (prefers-reduced-motion: reduce) {
    .leaderboard-row { animation: none; opacity: 1; }
  }
  ```

---

**Component: Current User Sticky Row (`.my-rank-bar`)**
- Position: `sticky`, bottom: `calc(60px + env(safe-area-inset-bottom))` (above mobile tab bar) or bottom: 0 on desktop.
- Background: `var(--color-primary-muted)`, `border-top: 2px solid var(--color-primary)`, height: `52px`, padding: `0 var(--space-5)`, flex layout, gap `var(--space-4)`, shadow, z-index: `var(--z-raised)`.
- Left: `"You"` label (`--type-micro` semibold, `--color-primary`, uppercase, tracking `0.06em`) + Rank number (`--font-mono` `--type-body` 800, `--color-primary`), Name, kg_saved.
- If user is in top 10 (already visible), hide this sticky bar.

---

### B.2 — JURY VOTING DASHBOARD (`/jury/<report_id>`)

**Phase:** 2 (Anti-Fraud & Moderation — Jury System)
**Route:** `/jury/<report_id>` | **Template:** `jury/vote.html`
**Access:** Trust score ≥ 120 only (enforced server-side)

**Page Role:** Community moderation tool. The jury sees a reported item anonymized, makes a verdict, and gets trust points if they vote with the majority. Must feel weighty and deliberate.

**Layout:** Max-width: `640px` centered. Padding: `var(--space-10)` horizontal, `var(--space-8)` vertical.

---

**Component: Jury Context Header**
- Eyebrow badge: `"Jury Review"` (warning-muted bg, warning text, `--radius-full`, `--type-micro` 600 uppercase, tracking `0.08em`, padding `var(--space-1) var(--space-3)`, margin-bottom `var(--space-4)`).
- Heading: `"Review Reported Item"` (`--type-display` 800), subtext: *"Your vote is anonymous. You earn +2 trust if you vote with the majority."*

---

**Component: Reported Item Display Card**
- Background: `var(--color-surface)`, `--radius-xl`, `--shadow-card`, overflow hidden, margin `var(--space-8) 0`.
- Layout: two columns (desktop) / stacked (mobile):
  - Left: photo block (width 160px on desktop / 100% on mobile, 4:3, cover, fallback raised surface).
  - Right: details (padding `var(--space-5)`, gavel icon + *"Anonymous Seller"* label, item title, item description, category chip, price).

---

**Component: Violation Report Panel**
- Background: `var(--color-warning-muted)`, `border: 1px solid var(--color-warning)`, padding `var(--space-4)`, margin `var(--space-5) 0`, flex layout, gap `var(--space-3)`.
- Icon: `flag` (20px, `--color-warning`). Content: Label: *"Reported for:"* (semibold, warning color) + reason text. Reason options: *Category fraud / Misleading description / Misrepresented condition / Ghost listing*.

---

**Component: Verdict Action Buttons**
- Desktop: grid-template-columns 1fr 1fr, gap `var(--space-4)`.
- **"Clear" button:** height 56px, `--radius-md`, border 2px solid `var(--color-success)`, background transparent, text color `--color-success`, icon `check_circle`, label `"Clear"` (`--font-sans` `--type-body` 600, hover success-muted bg, active scale transition).
- **"Guilty" button:** same dimensions, border 2px solid `var(--color-danger)`, background transparent, color `--color-danger`, icon `cancel`, label `"Guilty"`, hover danger-muted bg.

---

**Component: Inline Confirmation Step**
After clicking either verdict button, button grid hides and inline confirmation appears (no modal):
- Container: border, `--radius-lg`, padding `var(--space-5)`.
- Text: *"You're voting to [Clear / find Guilty]. This cannot be changed."*
- Confirm button (full-width): *"Confirm — [Clear / Guilty]"* (Clear: green bg, Guilty: red bg, height 48px).
- Cancel link below: *"← Go back"* (hover primary).

---

**Component: Post-Vote Success Card**
Replaces entire verdict section on submit:
- Background: `var(--color-primary-muted)`, `--radius-xl`, padding `var(--space-8)`, center aligned.
- Icon: `check_circle` (48px, `--color-success`, spring entrance).
- Heading: `"Vote submitted."` (`--type-title` 700), body: `"+2 trust if you voted with the majority."`
- CTA: *"Back to marketplace"* ghost button.
- Entrance animation: `.vote-success-card` animation `successReveal` 0.35s `var(--ease-spring)` forwards.

---

### B.3 — BADGE SYSTEM VISUAL STATES (User Avatars — Phase 2)

**Phase:** 2
**Applied on:** Item cards (seller avatar), Profile page (profile hero avatar), Dashboard, Leaderboard

Badges are applied as CSS classes on avatar elements. The underlying avatar component structure does not change — these are visual-only overrides.

**Standard avatar (no badge):**
```css
.avatar {
  width: var(--size); height: var(--size);
  border-radius: var(--radius-full);
  background: var(--color-primary-muted);
  display: flex; align-items: center; justify-content: center;
  font-family: var(--font-sans); font-weight: 800;
  color: var(--color-primary); flex-shrink: 0;
}
```

---

**Tree Milestone (10 kg saved) — `.avatar--tree`**
- outer soft glow border: `box-shadow: 0 0 0 3px var(--color-primary-muted);`
- Tooltip on hover (desktop only): `"🌱 10 kg milestone"`

---

**Forest Milestone (50 kg saved) — `.avatar--forest`**
- solid brand teal border: `border: 3px solid var(--color-primary);`
- Tooltip on hover: `"🌳 50 kg milestone"`

---

**Ecosystem Milestone (100 kg saved) — `.avatar--ecosystem`**
- transparent border, padding-box background clip, plus dynamic animation gradient:
```css
.avatar--ecosystem {
  position: relative; border: 2px solid transparent; background-clip: padding-box;
}
.avatar--ecosystem::before {
  content: ''; position: absolute; inset: -3px; border-radius: var(--radius-full);
  background: linear-gradient(135deg, var(--color-primary), var(--color-success), #0ea5e9, var(--color-primary));
  background-size: 300% 300%; animation: ecosystemGradient 3s ease infinite; z-index: -1;
}
@keyframes ecosystemGradient {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}
@media (prefers-reduced-motion: reduce) {
  .avatar--ecosystem::before { animation: none; background-position: 0% 50%; }
}
```

**Ecosystem text badge (on item cards, beside seller name):**
- Element: `<span class="ecosystem-badge">`
- Content: `"Ecosystem"`, icon: `recycling` (Material Symbol, 12px, `--color-primary`), background `var(--color-primary-muted)`, `--radius-full`, padding `2px 8px`, `--type-micro` 600, inline-flex, gap 4px, margin-left `var(--space-2)`. (No emojis in badge).

---

### B.4 — BOOST TOKEN UI (Phase 2)

**Phase:** 2
**Appears on:** User Dashboard, Item Listings (feed), Listing Form

---

#### B.4.1 — Dashboard Boost Token Counter
- Location: Top of dashboard, beside or below the kg_saved personal total chip.
- Element: `.boost-token-badge` (background: `var(--color-accent-muted)`, `--radius-full`, padding `var(--space-2) var(--space-4)`, inline-flex, gap `var(--space-2)`).
- Icon: `rocket_launch` (16px, `--color-accent`) + text: `[N] boost tokens available` (`[N]` bold, `--font-mono`, `--color-accent`, label: `--type-small`, `--color-ink-secondary`).
- If N == 0: Icon `rocket_launch` (16px, `--color-ink-tertiary`), text: *"No boost tokens — earn more via transactions"*.

---

#### B.4.2 — "Boost" Button on Listings (My Dashboard · My Listings Tab)
- Appears beside each unsold listing the user owns, when they have ≥ 1 boost token.
- **Button:** label `"Boost"`, icon `bolt` (14px, left), style: ghost, border 1px solid `var(--color-accent)`, color `var(--color-accent)`, `--radius-md`, height 36px, padding `0 var(--space-4)`, `--type-small` 600, hover accent-muted bg.
- **Inline Confirmation Dialog (replaces button on click):**
  - Container: border, accent-muted bg, `--radius-md`, padding `var(--space-4)`. Height/opacity transition (`--duration-mid` `--ease-out`).
  - Text: *"Boost for 30 days? (1 token will be used)"* (`--type-small`), remaining tokens hint (`--type-micro`, `--color-ink-tertiary`).
  - Buttons: `"Use token"` (filled accent, white text, height 36px, `--radius-md`) and `"Cancel"` (ghost).

---

#### B.4.3 — "Featured" Tag on Boosted Listings (Feed)
- Shown on item cards when `item.is_boosted == True`.
- Element: `.boost-featured-tag` (position: absolute top-left corners, background `var(--color-accent)`, white text, `--radius-sm`, padding `2px 8px`, inline-flex, gap 4px, icon `bolt`, label `"Featured"` `--font-mono` 11px 600).
- *Layout rule:* This tag occupies the same space as the Category chip. On boosted items, the Category chip moves below the image into the card content block.

---

### B.5 — SHADOW-BAN WARNING BANNER (Phase 2 — Sub-50 Trust Score)

**Phase:** 2
**Location:** Top of user dashboard, visible only to users with `trust_score < 50`.
**Critical copy rules (non-negotiable):**
- MUST include: *"Your listings are receiving less visibility due to community feedback. Continue making successful transactions to improve."*
- MUST NEVER use the words: "Trust Score", "Shadow-ban", or "Muted".

---

**Component: (`.shadow-warning-banner`)**
- Background: `var(--color-warning-muted)`, `border: 1px solid var(--color-warning)`, `--radius-md`, padding `var(--space-4) var(--space-5)`, margin-bottom `var(--space-6)`.
- **Content layout:** flex, `align-items: flex-start`, gap `var(--space-3)`.
  - Icon: `visibility_off` (20px, `--color-warning`).
  - Right block:
    - Heading: `"Reduced Visibility"` (`--type-small` 700).
    - Body text: *"Your listings are receiving less visibility due to community feedback. Continue making successful transactions to improve."*
    - Progress tracker: *"Progress: [n]/3 clean exchanges completed"* (`[n]` `--font-mono` 700 bold, primary color).
    - Progress bar below: height 6px, raised surface bg, `--radius-full`, width 200px. Fill: primary color, width `calc([n] / 3 * 100%)` transition width 0.5s `--ease-out`.
- *Disappearance:* Banner is removed server-side once `trust_score >= 50` on the next page load.

---

### B.6 — IN-APP NOTIFICATION FEED (Phase 2)

**Phase:** 2 | **Route:** `/notifications` | **Template:** `notifications.html`
**Page Role:** Central inbox for system events. Replaces email-only notifications with an in-app layer.
**Layout:** Max-width `680px`, centered.

---

**Navbar notification indicator (Phase 2 navbar addition):**
- Positioned on avatar button (top-right badge): unread count badge (position absolute top/right offset, `16px × 16px`, background `var(--color-accent)`, `--radius-full`, border 2px solid `var(--color-surface)`, `--font-mono` 10px 700 white, line-height 12px). Displayed if `unread_count > 0`.

---

**Notification List:**
- List rows: height auto (min 64px), padding `var(--space-4) var(--space-5)`, border-bottom, hover raised surface bg, cursor pointer (if linked), flex layout, gap `var(--space-4)`.
  - Left indicator dot (`.notif-dot`): width 8px, height 8px, `--radius-full`, background primary (unread) or transparent (read), border (read only), margin-top 6px.
  - Right content: Notification text (`--type-body`, primary color (unread), secondary color (read)), timestamp (`--type-micro`, tertiary color, margin-top `--space-1`).
- **Notification type → icon mapping:**

| Event | Icon | Color |
|-------|------|-------|
| Item claimed | `shopping_bag` | `--color-accent` |
| PIN exchange complete | `check_circle` | `--color-success` |
| Claim cancelled | `cancel` | `--color-danger` |
| Jury call (high trust users) | `gavel` | `--color-warning` |
| Trust milestone | `eco` | `--color-success` |
| System message | `info` | `--color-primary` |

- **Mark all read:** ghost button top-right of page header. Click transitions all filled dots to empty.

---

### B.7 — ITEM REPORT FLOW (Phase 2 — "Report this listing")

**Phase:** 2 | **Entry point:** Item detail page — text link below item description.
- **Entry link:** text `"Report this listing"` (`--type-small`, tertiary color, hover danger color, cursor pointer).

**Report Modal:**
- Max-width `480px`, background `var(--color-surface)`, `--radius-xl`, `--shadow-modal`, padding `var(--space-8)`, backdrop blur. Z-index: `var(--z-modal)`.
- **Report form structure:**
  - Heading: `"Report Listing"` (`--type-title` 700) + subtext: *"Your report is anonymous."*
  - Radio group: *"Select a reason"* label. Options (44px min height, border, `--radius-md`, padding):
    - Category fraud — item listed in the wrong category
    - Misleading description
    - Item no longer available
    - Item condition misrepresented
  - Selected option: border primary color, background primary-muted. Radio dot color: primary.
  - Submit button: *"Submit report"* (filled primary, full-width, height 48px). Cancel link below.
- **Post-submit state (replaces form):**
  - Icon `check_circle` (40px, `--color-success`).
  - Text: *"Report submitted. Our community jury will review this."* centered.
  - CTA: *"Back to marketplace"* ghost button.

---

### B.8 — QR CODE HANDSHAKE (Phase 2 — Alternative to PIN)

**Phase:** 2
**Page role:** An alternative confirmation method on the PIN page — the PIN holder can display a QR code encoding the PIN instead of reading digits aloud.

**UI Addition to PIN page (`items/pin.html`):**
Below the PIN digit display, add a toggle link: `"Show QR code instead"` (`--type-small` primary color, cursor pointer).
- **Expanded state (QR panel):**
  - Background `var(--color-surface)`, `--radius-lg`, padding `var(--space-6)`, center-aligned.
  - QR code image: `200px × 200px`, `--radius-md`, border. Generated server-side encoding the PIN value. Alt text: *"QR code for PIN verification"*.
  - Instruction: *"The other person scans this to confirm"* (`--type-small` secondary color).
  - Collapse link: *"← Back to PIN digits"* (`--type-small` tertiary color).
- *Note:* The QR code does not replace the PIN — it encodes the same 4-digit PIN. The scan simply fills the digits into the OTP fields automatically.

---

## PART 5 — ANTI-PATTERNS (BANNED — ENFORCED GLOBALLY)

The following patterns are EXPLICITLY FORBIDDEN. Any generated output containing these constitutes a quality failure:

```
TYPOGRAPHY
❌ Inter, Roboto, Arial, Helvetica, Open Sans (any of these)
❌ Generic serif fonts (Times New Roman, Georgia, Garamond)
❌ Display letter-spacing below −0.04em
❌ Body text on near-white backgrounds without 4.5:1 contrast verification

COLOR
❌ Pure black #000000
❌ Neon outer glows on buttons
❌ Purple gradients or blue neon aesthetic
❌ Warm/cool grey oscillation (no mixing Slate and Zinc grays)
❌ Saturated accents above 80% saturation

LAYOUT
❌ 3 equal-width columns side by side (generic feature row)
❌ Persistent left sidebar present for any user role
❌ Nested cards (card inside a card)
❌ Overlapping elements stacked without z-index discipline
❌ Horizontal scroll on mobile (critical failure)
❌ h-screen (use min-h-[100dvh] — iOS Safari viewport bug)
❌ calc() percentage hacks instead of Grid

MOTION
❌ linear or ease-in-out transitions
❌ Instant state changes with zero interpolation
❌ backdrop-blur on scrolling containers
❌ Animating top, left, width, height properties
❌ window.addEventListener('scroll') for reveal animations
❌ Bounce or elastic easing

COPY & UX
❌ Emojis anywhere in interface (except within badges as milestones)
❌ AI copywriting: "Elevate", "Seamless", "Unleash", "Next-Gen", "Revolutionary"
❌ "Scroll to explore", bouncing chevrons, scroll arrows
❌ Generic placeholder names ("John Doe", "Admin User", "Acme Corp")
❌ Fake round numbers (99.9%, 100%, exactly 1,000 users)

ICONS
❌ Thick-stroked generic Lucide defaults
❌ FontAwesome solid variants
❌ Missing aria-hidden on decorative icons
❌ Missing aria-label on icon-only interactive buttons
```

---

## PART 6 — COMPONENT ACCESSIBILITY RULES

Every component must pass:

| Requirement | Target |
|------------|--------|
| Color contrast (body text) | ≥ 4.5:1 |
| Color contrast (large text/bold 14px+) | ≥ 3:1 |
| Touch target minimum | 44 × 44px |
| Focus ring | 3px `--color-primary-muted` outline on all interactive elements |
| All form inputs | `<label for="...">` associations |
| All images | `alt=""` if decorative, descriptive if informational |
| All decorative icons | `aria-hidden="true"` |
| All icon-only buttons | `aria-label="..."` |
| Keyboard navigation | All interactive elements reachable and operable via keyboard |
| Screen reader skip link | `<a href="#main-content" class="skip-link">Skip to main content</a>` as first element in `<body>` |

---

## PART 7 — RESPONSIVE BREAKPOINTS

```css
/* Mobile-first. ONE breakpoint, clearly defined. */

/* Default: mobile (<1024px)
   - Single column layouts
   - Bottom tab navigation
   - No sidebar
   - Full-bleed cards and images
   - Compact padding: var(--space-4) horizontal
*/

@media (min-width: 1024px) {
  /* Desktop
   - Multi-column layouts enabled
   - Sidebar replaced by top navbar dropdown
   - Padding: var(--space-8) horizontal
   - Search bar visible in navbar center
  */
}
```

**Mobile-specific rules:**
- Claim CTA button on detail page: `position: fixed; bottom: calc(60px + env(safe-area-inset-bottom))`
- Category filter strip: `padding: 0 var(--space-4)`, `overflow-x: auto`, `-webkit-overflow-scrolling: touch`
- Dashboard metrics: 2-column grid (not 4)
- Admin partner table: collapses to card list
- Auth card: `border-radius: 0`, full bleed (`padding: var(--space-6)`)

---

## PART 8 — EXECUTION ORDER FOR ANTIGRAVITY 2.0

When executing this blueprint, process pages in this order:

```
1. Establish CSS custom properties (Part 1 — all tokens)
2. Build base.html shell:
   a. Desktop navbar (2.1)
   b. Mobile top bar (2.2) + drawer (2.3) + bottom tabs (2.4)
   c. Flash message system (2.5)
   d. Search overlay (2.6)
   e. Global Campus Impact Counter Footer widget (2.7)
3. Build auth pages (Page 10) — unblocks testing
4. Build Privacy Policy (Page 12) — legal base
5. Build Marketplace Index (Page 1) — highest traffic surface (incorporate Hero Strip)
6. Build Item Detail (Page 2) — conversion surface
7. Build Listing Form (Page 4) — supply creation
8. Build PIN Handshake (Page 3) — transaction completion (incorporate VisualViewport, role-aware copy)
9. Build User Dashboard (Page 5) — activity management
10. Build ESG Partner Dashboard (Page 6) — B2B value proof
11. Build Admin Panel (Page 7) — operator tooling
12. Build Profile (Page 8) + Settings (Page 9) — account management
13. Build Error Pages (Page 11) — defensive completeness
```

---

*Blueprint finalized by Elite Design Architect · Version 3.0 · For Antigravity 2.0 execution · June 2026*
*This document supersedes REUNI_UI_IMPLEMENTATION_MAP.md and REUNI_DESIGN_BLUEPRINT_ADDENDUM.md for all design decisions.*

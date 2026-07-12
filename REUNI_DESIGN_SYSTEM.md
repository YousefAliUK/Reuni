# REUNI — Unified Design System
### Master Specification · Supersedes: REUNI_DESIGN_BLUEPRINT_v3.md, REUNI_DESIGN_BLUEPRINT_ADDENDUM.md, REUNI_DESIGN_SYSTEM.md v1.0
### Version 1.0 · July 2026

> **This is the single source of truth for all Reuni design decisions.** On any conflict between this document and any prior blueprint or addendum, this document wins.

---

## PART 0 — STRATEGIC DESIGN READ

### The Core Tension Reuni Must Resolve

The same product must feel like a native Vinted/Depop app to an 18-year-old student *and* feel like credible ESG infrastructure to a sustainability officer writing a board report. Generic SaaS would alienate students. Generic marketplace loses the institutional pitch.

**The resolution:** Make sustainability the *aesthetic*, not a badge on top of it. Teal is not a brand color — it is the ideology of the platform made visible. Every surface reads as "circular economy data infrastructure" regardless of whether it is showing a £5 lamp or a kg_saved trend chart.

### Design Read (Formal)

```
"Reading this as: dual-audience platform (student marketplace + B2B sustainability
infrastructure), with Editorial Luxury warmth on consumer surfaces and data-dense
precision on institutional surfaces — unified by a single token system and one visual DNA.
Aesthetic family: Premium Consumer × Vertical SaaS."
```

### Atmosphere Profile (Global)

```
Variance:  6 / 10  — Offset Asymmetric (grids break symmetry intentionally; not chaos)
Motion:    6 / 10  — Fluid CSS, spring physics on ceremony moments, mobile-safe
Density:   5 / 10  — Daily App Balanced (not clinical, not sparse)
Register:  PRODUCT (design serves the platform, never decorates it)
```

### Multi-Skill Activation

| Skill | Where Activated | Purpose |
|-------|----------------|---------|
| `soft-skill` | Landing page, Marketplace, Item Detail, PIN Handshake | Consumer warmth, tactile cards, fluid physics |
| `stitch-skill` | User Dashboard, ESG Partner Dashboard, Admin Panel | Data density, modular composition |
| `impeccable-skill` | Auth pages, all surfaces (quality gate) | Pixel-perfect execution, contrast enforcement |
| `emil-kowalski-skill` | PIN Handshake digit input, ESG metric count-ups, CTA hover states | Spring physics, ceremony moments |

### Per-Surface Override Table

| Surface | Variance | Motion | Density | Dominant Skill |
|---------|----------|--------|---------|----------------|
| Landing Page | 8 | 7 | 3 | `soft-skill` + `impeccable-skill` |
| Marketplace Index | 6 | 5 | 5 | `soft-skill` |
| Item Detail | 5 | 5 | 5 | `soft-skill` |
| PIN Handshake | 3 | 7 | 4 | `impeccable-skill` + motion injection |
| Listing Form | 4 | 3 | 5 | `impeccable-skill` |
| User Dashboard | 5 | 5 | 6 | `stitch-skill` |
| ESG Partner Dashboard | 4 | 4 | 8 | `stitch-skill` |
| Admin Panel | 3 | 3 | 9 | `stitch-skill` |
| Auth Pages | 3 | 4 | 3 | `impeccable-skill` |

---

## PART 1 — DESIGN TOKEN SYSTEM

### 1.1 Color Palette

All colors declared as CSS custom properties on `:root` and `[data-theme="dark"]`. No hardcoded color values anywhere in component CSS — always reference variables.

```css
/* ════════════════════════════════════
   LIGHT MODE (Default)
════════════════════════════════════ */
:root {
  /* Backgrounds */
  --color-bg:              #FAF7F2;  /* Warm Canvas — paper-like, tactile */
  --color-surface:         #FFFFFF;  /* Cards, navbar, modal fills */
  --color-surface-raised:  #F4F0E8;  /* Warm Stone-100 — inputs, nested panels */

  /* Borders */
  --color-border:          rgba(28, 25, 23, 0.12);

  /* Ink */
  --color-ink-primary:     #1C1917;  /* Stone-950 — headlines, active labels */
  --color-ink-secondary:   #44403C;  /* Stone-700 — body copy */
  --color-ink-tertiary:    #706A64;  /* Stone-600 — timestamps, placeholders (4.5:1 on canvas) */

  /* Brand — Teal (Sustainability Identity) */
  --color-primary:         #0F766E;  /* Teal-700 — brand, active, kg_saved */
  --color-primary-hover:   #115E59;  /* Teal-800 */
  --color-primary-muted:   #CCFBF1;  /* Teal-100 — chips, success zones */

  /* Brand — Terracotta (Action/Urgency — CTAs only) */
  --color-accent:          #B44018;  /* Burnt Terracotta — claim/buy CTAs only */
  --color-accent-hover:    #8E3213;
  --color-accent-muted:    #FFF7ED;  /* Orange-50 — urgency panel fills */

  /* Semantic */
  --color-danger:          #C81E1E;  /* Red-700 — errors, destructive (4.5:1) */
  --color-danger-muted:    #FEF2F2;
  --color-success:         #15803D;  /* Green-700 — sold, verified, free */
  --color-success-muted:   #F0FDF4;
  --color-warning:         #B45309;  /* Amber-700 — PIN expiry, late cancel (4.5:1) */
  --color-warning-muted:   #FFFBEB;
}

/* ════════════════════════════════════
   DARK MODE
════════════════════════════════════ */
[data-theme="dark"] {
  --color-bg:              #1C1917;  /* Stone-950 */
  --color-surface:         #292524;  /* Stone-900 */
  --color-surface-raised:  #44403C;  /* Stone-700 */
  --color-border:          rgba(120, 113, 108, 0.2);

  --color-ink-primary:     #F5F5F4;  /* Stone-100 */
  --color-ink-secondary:   #D6D3D1;  /* Stone-300 (4.5:1 on surface-raised) */
  --color-ink-tertiary:    #87807B;  /* Stone-500 */

  /* NOTE: Teal-400 in dark. NEVER pair with white text — use dark ink (#1C1917) */
  --color-primary:         #2DD4BF;  /* Teal-400 */
  --color-primary-hover:   #2DD4BF;
  --color-primary-muted:   rgba(13, 148, 136, 0.15);

  --color-accent:          #F97316;  /* Orange-500 */
  --color-accent-hover:    #F97316;
  --color-accent-muted:    rgba(234, 88, 12, 0.12);

  --color-danger:          #F87171;  /* Red-400 */
  --color-danger-muted:    rgba(239, 68, 68, 0.15);
  --color-success:         #4ADE80;  /* Green-400 */
  --color-success-muted:   rgba(21, 128, 61, 0.15);
  --color-warning:         #FBBF24;  /* Amber-400 */
  --color-warning-muted:   rgba(217, 119, 6, 0.15);
}
```

### Color Rationale (Designer Notes)

**Why Teal-700 (`#0F766E`)?** Deep teal sits at the intersection of sustainability (green spectrum) and institutional trust (cool precision). Dark enough for white text (AAA). Rare enough in the student app space to be ownable. Lighter teals (Teal-400/500) feel generic SaaS. Teal-700 feels institutional — which the B2B pitch demands.

**Why Burnt Terracotta (`#B44018`) for CTAs?** Teal appears everywhere (brand, footer, chips). If the primary CTA is also teal, it disappears into the brand. Terracotta creates the one moment of urgency-action. Warm (humanising a transaction) without aggressive (no neon). Survives both modes.

**Why Warm Canvas (`#FAF7F2`)?** Pure white feels clinical. Warm canvas reads as "paper" — tactile, campus notice board. Positions the platform as part of campus life, not a cold digital tool dropped onto campus.

**Why Stone family, never Slate?** Stone grays have warmth baked in (slight yellow undertone). Slate grays are cold (slight blue undertone). Mixing Stone and Slate creates an imperceptible but real visual dissonance. All neutrals resolve to Stone family only.

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

/* Letter Spacing Rules */
/* Display: -0.02em to -0.03em. HARD FLOOR: -0.04em (letters touch below this) */
/* Title: -0.01em to -0.02em */
/* Body: 0em (normal) */

/* Font Weights */
/* Display headings: 700-800 */
/* Labels/badges: 500-600 */
/* Body: 400 */
/* Mono (kg values, PINs, prices): 600-800 */
```

**Non-negotiable typography rules:**
- `--font-mono` is mandatory for: all `kg_saved` values, PIN digits, countdown timers, price tags (large format), timestamps
- Body text max-width: `65ch`
- `text-wrap: balance` on all h1–h3
- Display headings: letter-spacing floor is `−0.03em`, hard floor `−0.04em`
- Banned fonts: Inter, Roboto, Arial, Helvetica, Open Sans
- Banned serifs as defaults: Fraunces, Instrument_Serif (LLM tells)

**Why Plus Jakarta Sans?** Humanist grotesque — geometric precision with slightly warm, human terminals. Distinguishable from Inter to design-literate eyes. Variable font range (300–800) gives full hierarchy control. Works at display scale and form labels without a second family.

**Why JetBrains Mono?** Monospace for `kg_saved` signals "this is a real number from a verified system" — not marketing copy. Fixed character width prevents layout reflow when numbers update.

### 1.3 Spacing System (4px base grid)

```css
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
--space-24: 96px;
```

### 1.4 Border Radius Scale

```css
--radius-sm:   4px;
--radius-md:   8px;
--radius-lg:   12px;
--radius-xl:   16px;
--radius-2xl:  20px;
--radius-full: 9999px;
```

### 1.5 Shadow System

```css
--shadow-card:  0 1px 3px rgba(28, 25, 23, 0.06), 0 4px 12px rgba(28, 25, 23, 0.06);
--shadow-modal: 0 8px 32px rgba(28, 25, 23, 0.14), 0 2px 8px rgba(28, 25, 23, 0.08);
--shadow-nav:   0 2px 16px rgba(28, 25, 23, 0.08);
--shadow-lift:  0 4px 24px rgba(28, 25, 23, 0.10), 0 1px 4px rgba(28, 25, 23, 0.06);
```

Dark mode: replace `rgba(28, 25, 23, X)` with `rgba(0, 0, 0, X * 1.4)` — darker shadows on dark surfaces.

### 1.6 Motion Tokens

```css
--duration-instant: 80ms;
--duration-fast:    150ms;
--duration-base:    250ms;
--duration-slow:    400ms;
--duration-enter:   600ms;

/* Spring curves — no linear, no ease-in-out */
--ease-out:    cubic-bezier(0.16, 1, 0.3, 1);     /* Standard exit/enter */
--ease-spring: cubic-bezier(0.32, 0.72, 0, 1);    /* CTA hover, card press */
--ease-expo:   cubic-bezier(0.19, 1, 0.22, 1);    /* Count-up, page transitions */
```

### 1.7 Z-Index Scale

```css
--z-base:    0;
--z-raised:  10;
--z-dropdown: 100;
--z-sticky:  200;
--z-modal-backdrop: 300;
--z-modal:   400;
--z-toast:   500;
--z-tooltip: 600;
```

No arbitrary `z-50` or `z-[9999]`. Always reference the scale.

---

## PART 2 — NAVIGATION ARCHITECTURE

### 2.1 Strategic Decision: No Sidebar

**The sidebar is permanently removed from all user roles.** This is a strategic experience decision, not cosmetic:

Admin, partner, and student users must feel they share the same platform. A sidebar for some roles creates a visual schism ("B2B tool" vs "student app"). The marketplace is the front page for every role. The ESG Dashboard and Admin Panel are accessed via the navbar avatar dropdown — appearing only for authenticated roles that hold them. The bottom mobile tab bar is universal.

This enforces the "campus circular economy infrastructure" framing: the sustainability data layer is embedded in the same experience, not separated into a corporate portal.

### 2.2 Desktop Navbar

```
Shell:
  Position: fixed, top: 0, left: 0, right: 0
  Background: var(--color-surface)
  Border-bottom: 1px solid var(--color-border)
  Height: 60px
  Z-index: var(--z-sticky)
  Display: flex, align-items: center
  Padding: 0 var(--space-8)
  backdrop-filter: blur(12px) [if using transparent variant]

Three zones (flex, space-between):

LEFT — Brand + University Context
  Reuni wordmark: --font-sans, 17px, font-weight: 800, --color-ink-primary
  University badge (when on subdomain): pill chip next to wordmark
    Background: var(--color-primary-muted)
    Color: var(--color-primary)
    Text: university short name (e.g. "Brookes") — --type-micro, font-weight: 600
    Border-radius: var(--radius-full)
    Padding: 3px 8px

CENTER — Search
  Search input: full rounded pill, background: var(--color-surface-raised)
  Width: min(480px, 40vw)
  Height: 36px
  Placeholder: "Search items at Brookes..."
  Icon: search (Material Symbols, 16px, left inside input)

RIGHT — Actions
  [if unauthenticated]
    "Log in" — ghost text, --type-small, font-weight: 500, --color-ink-secondary
    "Register" — filled pill, var(--color-accent), height: 36px, --type-small, font-weight: 600
    
  [if authenticated]
    Theme toggle button: 36×36px, icon-only, aria-label="Toggle theme"
      sun/dark_mode icon, --color-ink-secondary
      Hover: background: var(--color-surface-raised), border-radius: var(--radius-md)
    
    "Sell" button: ghost pill with add icon
    
    Avatar button: 36×36px circle
      Background: var(--color-primary-muted)
      Initials: --font-sans, 13px, font-weight: 700, --color-primary
      Notification badge (if unread): absolute top-right, 8px × 8px
        Background: var(--color-accent)
        Border: 2px solid var(--color-surface)
        Border-radius: var(--radius-full)
      Dropdown (on click):
        Background: var(--color-surface)
        Border: 1px solid var(--color-border)
        Border-radius: var(--radius-lg)
        Box-shadow: var(--shadow-modal)
        Min-width: 200px
        Items: My listings · Activity · Profile · Settings
               [if partner role]: ESG Dashboard (teal dot indicator)
               [if admin role]: Admin Panel (orange dot indicator)
               Divider
               Log out
```

### 2.3 Mobile Top Bar

```
Height: 52px
Background: var(--color-surface)
Border-bottom: 1px solid var(--color-border)
Z-index: var(--z-sticky)
Display: flex, align-items: center
Padding: 0 var(--space-4)
justify-content: space-between

Left: Reuni wordmark + university badge (same as desktop)
Right: Search icon button (opens search overlay) + Avatar button
```

### 2.4 Mobile Drawer

```
Triggered by: avatar button tap OR hamburger (if applicable)
Position: fixed, inset: 0, z-index: var(--z-modal)
Backdrop: rgba(28, 25, 23, 0.4), backdrop-filter: blur(4px)

Drawer panel:
  Position: right: 0, top: 0, bottom: 0
  Width: min(320px, 88vw)
  Background: var(--color-surface)
  Transform: translateX(0) ↔ translateX(100%) — spring animation
  overscroll-behavior: contain
  
Contents:
  Header: avatar + name + university email (truncated)
  Nav items: same as desktop dropdown
  Bottom: theme toggle (full-width row with label "Dark mode" + toggle switch)
```

### 2.5 Mobile Bottom Tab Bar

```
Position: fixed, bottom: 0, left: 0, right: 0
Height: calc(56px + env(safe-area-inset-bottom))
Padding-bottom: env(safe-area-inset-bottom)
Background: var(--color-surface)
Border-top: 1px solid var(--color-border)
Z-index: var(--z-sticky)
Display: grid, grid-template-columns: repeat(4, 1fr)

Tabs (all authenticated users):
  [house] Home (marketplace)
  [add_circle] Sell
  [notifications] Activity  
  [person] Profile

Tab item:
  Display: flex, flex-direction: column, align-items: center
  Padding: var(--space-2) 0 var(--space-3)
  Icon: 22px Material Symbol
  Label: --type-micro, font-weight: 500
  Active: icon + label both var(--color-primary)
  Inactive: --color-ink-tertiary
  touch-action: manipulation
```

### 2.6 Search Overlay

```
Position: fixed, inset: 0
Z-index: var(--z-modal)
Background: rgba(28, 25, 23, 0.4) [desktop] / var(--color-bg) [mobile full-screen]
Backdrop-filter: blur(8px) [desktop only — never on scrolling containers]

Search panel (desktop):
  Position: top: 80px, centered
  Width: min(600px, 90vw)
  Background: var(--color-surface)
  Border-radius: var(--radius-xl)
  Box-shadow: var(--shadow-modal)
  
Input row: 36px height, full-width, no border
  Icon: search 18px left
  Clear button right (appears when value present)

Results (max 8, virtualized if more): 
  60px per row, icon left, title + category right, price far right
```

### 2.7 Flash Message System

```
Position: fixed, top: calc(60px + var(--space-3)), left: 50%, transform: translateX(-50%)
Z-index: var(--z-toast)
Min-width: 320px, max-width: min(480px, 90vw)
Display: flex, align-items: center, gap: var(--space-3)
Background: var(--color-surface)
Border: 1px solid var(--color-border)
Border-left: 3px solid [semantic color]
Border-radius: var(--radius-lg)
Box-shadow: var(--shadow-modal)
Padding: var(--space-3) var(--space-4)

Left border colors by type:
  success: var(--color-success)
  error: var(--color-danger)
  warning: var(--color-warning)
  info: var(--color-primary)

Auto-dismiss: 4 seconds. Dismiss on click.
Animation enter: translateY(-8px) opacity:0 → translateY(0) opacity:1, 250ms var(--ease-out)
Animation exit: translateY(-4px) opacity:1 → opacity:0, 200ms var(--ease-out)
aria-live="polite" on the flash container
```

---

## PART 3 — COMPONENT LIBRARY

### 3.1 Button System

```css
/* Base — all buttons */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  border: none;
  cursor: pointer;
  font-family: var(--font-sans);
  font-weight: 600;
  text-decoration: none;
  border-radius: var(--radius-md);
  height: 40px;
  padding: 0 var(--space-5);
  font-size: var(--type-body);
  transition: transform var(--duration-fast) var(--ease-spring),
              background-color var(--duration-fast) var(--ease-out),
              box-shadow var(--duration-fast) var(--ease-out),
              color var(--duration-fast) var(--ease-out);
  touch-action: manipulation; /* prevents double-tap zoom */
  -webkit-tap-highlight-color: transparent;
  white-space: nowrap;
  min-width: 44px; /* WCAG touch target */
  min-height: 44px;
}
.btn:active { transform: scale(0.97); }
.btn:focus-visible {
  outline: 3px solid var(--color-primary-muted);
  outline-offset: 2px;
}

/* Primary — filled teal */
.btn-primary {
  background: var(--color-primary);
  color: #FFFFFF;
}
.btn-primary:hover { background: var(--color-primary-hover); transform: translateY(-1px); }

/* Accent — filled terracotta (CTAs: claim, buy) */
.btn-accent {
  background: var(--color-accent);
  color: #FFFFFF;
}
.btn-accent:hover { background: var(--color-accent-hover); transform: translateY(-1px); }

/* Ghost — outline */
.btn-ghost {
  background: transparent;
  border: 1px solid var(--color-border);
  color: var(--color-ink-secondary);
}
.btn-ghost:hover { border-color: var(--color-ink-tertiary); color: var(--color-ink-primary); }

/* Danger */
.btn-danger { background: var(--color-danger); color: #FFFFFF; }

/* Sizes */
.btn-sm { height: 32px; padding: 0 var(--space-4); font-size: var(--type-small); border-radius: var(--radius-md); }
.btn-lg { height: 52px; padding: 0 var(--space-8); font-size: 1rem; border-radius: var(--radius-lg); }
.btn-pill { border-radius: var(--radius-full); }

/* Loading state */
.btn[disabled], .btn.loading {
  opacity: 0.55;
  cursor: not-allowed;
  transform: none;
}
/* Show spinner during loading — keep original label visible */
```

### 3.2 Item Card

```
Shell: 
  Background: var(--color-surface)
  Border: 1px solid var(--color-border)
  Border-radius: var(--radius-xl)
  Overflow: hidden
  Transition: transform var(--duration-fast) var(--ease-spring),
              box-shadow var(--duration-fast) var(--ease-out)

Desktop hover: 
  transform: translateY(-2px)
  box-shadow: var(--shadow-lift)

Mobile press: transform: scale(0.98) — touch-action: manipulation

Image:
  Aspect-ratio: 4/3
  Object-fit: cover
  Background: var(--color-surface-raised)
  Width: 100%
  Loading: lazy (below fold), fetchpriority="high" (above fold, first 4 cards)

Content area: padding: var(--space-3) var(--space-4) var(--space-4)

Top row:
  Category chip: var(--color-surface-raised), --type-micro, font-weight: 500
  Border-radius: var(--radius-full), padding: 2px 8px, margin-bottom: var(--space-2)

Title: --type-body, font-weight: 600, --color-ink-primary
  line-clamp: 2, text-overflow: ellipsis

Bottom row (flex, space-between, align: center):
  Price: --font-mono, 16px, font-weight: 700, --color-ink-primary
    "Free": var(--color-success), font-weight: 700
    
  kg chip:
    Display: inline-flex, align-items: center, gap: 4px
    Icon: eco (14px, --color-success, aria-hidden)
    Value: --font-mono, 11px, font-weight: 700, --color-primary
    "X.X kg"
    
Condition badge (top-right of image, absolute):
  Background: rgba(28, 25, 23, 0.75)
  Color: #FFFFFF, --type-micro, font-weight: 600
  Border-radius: var(--radius-sm), padding: 2px 6px
  Values: New · Good · Fair · Well-used
```

### 3.3 Form Input System

```css
/* Text input base */
.input {
  width: 100%;
  height: 44px; /* WCAG touch target */
  padding: 0 var(--space-4);
  background: var(--color-surface-raised);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-family: var(--font-sans);
  font-size: var(--type-body);
  color: var(--color-ink-primary);
  transition: border-color var(--duration-fast) var(--ease-out),
              box-shadow var(--duration-fast) var(--ease-out);
  autocomplete: on; /* must match semantic field */
}
.input:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-muted);
  outline: none;
}
.input.error { border-color: var(--color-danger); }
.input::placeholder { color: var(--color-ink-tertiary); }
/* Never block paste on any input */

/* Textarea */
.textarea {
  min-height: 120px;
  padding: var(--space-3) var(--space-4);
  resize: vertical;
  /* Cmd/Ctrl+Enter submits; Enter inserts newline */
}

/* Form group */
.form-group { display: flex; flex-direction: column; gap: var(--space-2); }
.form-label {
  font-size: var(--type-small);
  font-weight: 600;
  color: var(--color-ink-secondary);
}
/* Every input must have an associated <label> via for/id or wrapping */

.form-error {
  font-size: var(--type-small);
  color: var(--color-danger);
  margin-top: var(--space-1);
}
```

### 3.4 PIN Digit Input

The PIN handshake is a ceremony, not a form. Design must reflect this.

```
Container:
  Display: flex, gap: var(--space-3), justify-content: center
  
Each digit input:
  Width: 56px, height: 72px
  Background: var(--color-surface-raised)
  Border: 2px solid var(--color-border)
  Border-radius: var(--radius-lg)
  Font: --font-mono, 32px, font-weight: 800, --color-ink-primary
  Text-align: center
  Caret: none (custom visual)
  
  Focus: border-color: var(--color-primary), box-shadow: 0 0 0 3px var(--color-primary-muted)
  Filled: border-color: var(--color-primary), background: var(--color-primary-muted)
  Error: border-color: var(--color-danger), shake animation
  
  Spring press physics (emil-kowalski):
    :active → transform: scale(0.94)
    Release → spring back: stiffness: 400, damping: 30
    
  Mobile:
    Use visualViewport resize listener to re-center card when soft keyboard opens
    touch-action: manipulation (no double-tap zoom)
    
Shake animation (on wrong PIN):
  keyframes: translateX(-6px 0 6px 0 -4px 0 4px 0) — 400ms
  NOT bounce/elastic — controlled horizontal oscillation only
```

### 3.5 Chip / Badge System

```
Base chip: inline-flex, align-items: center, gap: 4px
  Border-radius: var(--radius-full)
  Padding: 4px 10px
  Font: --type-micro, font-weight: 600

Teal chip (category, active): background: var(--color-primary-muted), color: var(--color-primary)
Success chip (free, sold): background: var(--color-success-muted), color: var(--color-success)
Warning chip (expiring, late): background: var(--color-warning-muted), color: var(--color-warning)
Danger chip (cancelled): background: var(--color-danger-muted), color: var(--color-danger)
Neutral chip (condition, filter): background: var(--color-surface-raised), color: var(--color-ink-secondary), border: 1px solid var(--color-border)
```

### 3.6 Modal System

```
Backdrop:
  Position: fixed, inset: 0
  Background: rgba(28, 25, 23, 0.5)
  Backdrop-filter: blur(4px)
  Z-index: var(--z-modal-backdrop)

Modal panel:
  Position: fixed, top: 50%, left: 50%, transform: translate(-50%, -50%)
  Background: var(--color-surface)
  Border-radius: var(--radius-xl) [desktop] / --radius-xl top only [mobile sheet]
  Box-shadow: var(--shadow-modal)
  Max-width: 480px, width: calc(100% - var(--space-8))
  Max-height: 90dvh
  Overflow-y: auto
  Z-index: var(--z-modal)
  overscroll-behavior: contain
  Padding: var(--space-8)
  
Mobile: bottom sheet — fixed bottom: 0, width: 100%, border-radius: 20px 20px 0 0
  Transform: translateY(100%) → translateY(0), spring animation
  
Enter animation: scale(0.96) opacity(0) → scale(1) opacity(1), 250ms var(--ease-out)
Exit animation: scale(0.97) → opacity(0), 200ms var(--ease-out)

Close button: top-right, 32×32px, aria-label="Close"
  Icon: close (Material Symbols, 18px)
  Background: var(--color-surface-raised) on hover
  Border-radius: var(--radius-full)
  
Focus trap: mandatory. Escape key dismisses.
```

---

## PART 4 — PAGE SPECIFICATIONS

### 4.1 Marketplace Index (Page 1)

**Role:** Highest-traffic student surface. Must load fast, feel native, convert to listings.

```
Layout: max-width: 1200px, margin: 0 auto
Padding: var(--space-4) [mobile] / var(--space-8) [desktop]

Hero Strip (context-aware, 80px height):
  [Unauthenticated]
    Background: var(--color-primary)
    Left: "Campus items. Real kg saved." (18px, 600, white) + "Student-to-student. In person. No fees." (14px, 400, rgba white 0.75)
    Right: "Register free →" pill (white background, primary color text)
    
  [Authenticated]
    Background: var(--color-surface)
    Border-bottom: 1px solid var(--color-border)
    Three stat chips (horizontally scrollable on mobile):
      [eco icon] X.X kg saved — --font-mono 700 --color-primary
      [inventory icon] N listed — --font-mono 700
      [bag icon] N purchased — --font-mono 700
    Mobile: overflow-x: auto, scrollbar-width: none, flex-shrink: 0 on chips

Filter Strip:
  Position: sticky, top: 60px, z-index: var(--z-raised)
  Background: var(--color-bg)
  Border-bottom: 1px solid var(--color-border)
  Padding: var(--space-3) var(--space-4)
  Overflow-x: auto, -webkit-overflow-scrolling: touch, scrollbar-width: none
  
  Category filter pills: horizontal scroll
  Price toggle: "All | Free | Paid"
  Sort dropdown: "Latest | Price ↑ | Price ↓"

Listing Grid:
  Desktop: grid-template-columns: repeat(auto-fill, minmax(260px, 1fr))
  Mobile: grid-template-columns: repeat(2, 1fr)
  Gap: var(--space-4)
  
  Pagination: page-based, 12 items per page
  
  Empty state:
    Icon: inventory_2 (48px, --color-ink-tertiary)
    Heading: "Nothing here yet"
    Body: "Be the first to list something at [university]."
    CTA: "List an item →" (filled primary)
```

### 4.2 Item Detail (Page 2)

```
Max-width: 1100px desktop, full-width mobile

Two-column layout (desktop): 
  Left: image gallery (60% width)
  Right: item info (40% width)
Mobile: stacked

Image gallery:
  Main image: aspect 4/3, object-fit: cover, --radius-xl
  Thumbnails (if multiple): 48px × 48px row below, gap: var(--space-2)
  
Item info:
  Category chip + Condition badge (row)
  Title: --type-display, font-weight: 800, --color-ink-primary, margin: var(--space-3) 0
  Price: --font-mono, 28px, font-weight: 800
    Free: --color-success + "Free to take"
    Paid: --color-ink-primary + "£X.XX"
  
  kg chip: [eco icon] "X.X kg saved if this item is rehomed"
    Background: var(--color-success-muted), padding: var(--space-2) var(--space-3)
    Border-radius: var(--radius-md), display: inline-flex
    --type-small, --color-success
  
  Divider: 1px solid var(--color-border)
  
  Description: --type-body, --color-ink-secondary, line-height: 1.7, max-width: 65ch
  
  Seller row:
    Avatar (36px circle) + username + "Listed X days ago"
    --type-small, --color-ink-tertiary
  
  "Report this listing" text link below description (--type-small, --color-ink-tertiary, hover: --color-danger)
  
  Claim CTA:
    Desktop: full-width btn-accent btn-lg below seller info
    Mobile: position: fixed, bottom: calc(60px + env(safe-area-inset-bottom) + var(--space-3))
      left: var(--space-4), right: var(--space-4)
      height: 52px, border-radius: var(--radius-full), btn-accent
```

### 4.3 PIN Handshake (Page 3)

**Design philosophy:** This is a ceremony, not a form. Every element should communicate "this is a significant, verified moment." Friction here is the trust architecture.

```
Layout: single centered card
  Max-width: 420px, margin: var(--space-12) auto
  
Role-aware header:
  Icon: lock (32px, --color-primary, inside 56px circle with --color-primary-muted bg)
  
  [Free item seller] "Share your PIN" (--type-title, 700)
  [Free item buyer] "Enter the seller's PIN" (--type-title, 700)
  [Paid item buyer] "Share your PIN" (--type-title, 700)
  [Paid item seller] "Enter the buyer's PIN" (--type-title, 700)
  
  Item summary row: image thumbnail (40px) + item title + price
  
  Instruction text: --type-body, --color-ink-secondary (role-specific guidance)
  
PIN display (for PIN holder):
  4 × digit boxes (see 3.4)
  Each digit revealed with scale-in spring animation
  
  Expiry countdown: --font-mono, --color-warning
  Resend link: --type-small, --color-primary (rate-limited: 3/hr)
  
PIN input (for non-holder):
  4 × OTP input boxes (see 3.4)
  Auto-advance on fill
  Submit triggers on 4th digit complete
  
  Failed attempt: shake animation + red border + attempt counter "X of 3 attempts"
  3rd fail: auto-cancel, redirect to marketplace with flash error
  
Chat thread (below PIN section):
  Background: var(--color-surface-raised)
  Border-radius: var(--radius-xl)
  Padding: var(--space-4)
  Max-height: 300px, overflow-y: auto
  
  Bubble alignment: buyer right (--color-primary-muted), seller left (var(--color-surface))
  Timestamp: --type-micro, --color-ink-tertiary, centered between time gaps
  
  Input: sticky bottom of chat box, 40px height
  
QR Code toggle (Phase 2):
  "Show QR code instead" link below PIN display (--type-small, --color-primary)
  Expanded: 200×200px QR image, centered, --radius-md border
  
WhatsApp bypass: "Contact via WhatsApp instead →" ghost link at bottom of card
  
Mobile visualViewport:
  Listen for visualViewport resize events
  On keyboard open: re-center the PIN card in the remaining visible area
  Remove any fixed-bottom elements (Claim CTA not present on this page)
```

### 4.4 Listing Form (Page 4)

```
Max-width: 600px, centered
Padding: var(--space-8) var(--space-4)

Form sections (stacked, no tabs):
  1. Photos — drag-drop zone + upload button
     Accepts: JPG, PNG, WebP. Max: 5MB each.
     Shows thumbnail grid on upload (up to 5 images)
     
  2. Item details — title, description (2000 char limit + counter), category, condition
  
  3. Pricing — "Free" toggle OR price input (£ prefix, --font-mono)
     Price must be > 0 for paid items (enforced client + server)
     
  4. Location — auto-filled from university domain (read-only display)

Submit: btn-primary btn-lg, full-width
  Disabled until: title, category, condition, price (or free) filled
  Loading state: spinner + "Listing your item…"

Each form group has:
  <label for="..."> (required, no exceptions)
  Error: inline below the field, --color-danger, --type-small
  Focus: border + ring (see 3.3)
```

### 4.5 User Dashboard (Page 5)

```
Max-width: 900px, centered

Tabs: "My Listings" | "Activity" | "Impact"
  Tab strip: border-bottom: 1px solid var(--color-border)
  Active tab: border-bottom: 2px solid var(--color-primary), color: --color-primary
  Transition: border-color, color — var(--duration-fast)

My Listings tab:
  Item list (not grid): each row is a listing card with status badge
  Status badges: Available · Claimed · Sold · Cancelled
  Actions: Edit (if available) · Delete (if available)
  Empty: "You haven't listed anything yet" + CTA

Activity tab:
  Timeline of transactions (buyer and seller)
  Each row: item thumbnail + title + kg saved + date + status

Impact tab:
  3 metric cards (2-col mobile, 3-col desktop):
    Total kg saved (--font-mono, large, --color-primary)
    Items circulated (--font-mono)
    Reputation score (--font-mono, 1–5 stars visual)
  
  kg_saved timeline chart: simple SVG line chart
  Category breakdown: horizontal bar chart
```

### 4.6 ESG Partner Dashboard (Page 6)

**Register:** Partner/sustainability officer only (via navbar dropdown → "ESG Dashboard").

```
Max-width: 1100px

Header: 
  University name + academic year
  Export button: "Download report" (ghost btn) → CSV/PDF

Metric strip (4 cards, 2-col on mobile):
  Total kg saved (YTD) — --font-mono, large, --color-primary, count-up on load
  Active students (this semester) — --font-mono
  Items circulated (YTD) — --font-mono  
  CO2e equivalent (kg × 0.6 conversion) — --font-mono

kg_saved trend chart:
  Weekly bars, 12-week default view
  Bar color: var(--color-primary), 40% opacity
  Active week: full opacity
  Y-axis: --font-mono, --type-micro, --color-ink-tertiary
  X-axis: date labels, --type-micro

Category breakdown:
  Horizontal bars per category
  % of total kg, item count
  
Student engagement:
  Active users / total registered (simple ratio)
  Peak activity days (heatmap: 7-day × 52-week grid, like GitHub contributions)

All charts: no chartjs defaults. Use custom SVG or the Reuni palette only.
```

### 4.7 Admin Panel (Page 7)

```
Max-width: 1200px

Sections:
  Partner management table: name · university · status · ACV · actions
    Columns collapse to card list on mobile
    Actions: Activate · Deactivate · Edit
    
  Student listings: search/filter + list view (not card grid)
  
  Trust score management: user search + manual delta + reason log
  
  Ghost mode log: read-only, sorted by date (admin-only context)
  
  Platform metrics: total users, total kg, total transactions, active universities
```

### 4.8 Auth Pages (Page 10)

```
Auth pages do NOT extend base.html. Standalone layout:
  Background: var(--color-bg)
  Center-aligned vertically and horizontally
  
Desktop:
  Card: max-width 420px, background: var(--color-surface), --shadow-modal, --radius-xl, padding: var(--space-8)
  
Mobile:
  NO card — full-bleed, border-radius: 0
  Padding: var(--space-6)
  
Reuni wordmark at top of every auth page (centered)
University badge if university context is known (from subdomain)

Form fields: see 3.3
Error placement: inline below field, focus first error on submit
Submit button: btn-primary btn-lg, full-width, loading state while request in flight
Footer links: "Already have an account? Log in" — --type-small

Cloudflare Turnstile CAPTCHA: register, login, forgot-password endpoints
```

### 4.9 Error Pages (Page 11)

```
404: "This item might have been sold."
  Icon: search_off (64px, --color-ink-tertiary)
  CTA: "Back to marketplace"

500: "Something went wrong on our end."
  Icon: error (64px, --color-ink-tertiary)
  No technical error details exposed to users.

Both: centered, max-width 400px, clean typography
```

### 4.10 Privacy Policy (Page 12)

```
Max-width: 720px, centered
No card containers — raw prose on canvas background
Padding: var(--space-12) var(--space-8)

Back nav: "← Back to Reuni" — --type-small, font-weight: 500, --color-ink-secondary, hover: --color-primary

Heading: "Privacy Policy" — --type-display, font-weight: 800
Last updated: --font-mono, --type-small, --color-ink-tertiary
Divider: 1px solid var(--color-border), margin: var(--space-8) 0

Prose typography:
  h2: 20px, 700, --color-ink-primary, leading: 1.3
  h3: 16px, 600, --color-ink-primary
  p: 15px, 400, --color-ink-secondary, leading: 1.7
  a: --color-primary, 500, no underline default, hover: underline
  strong: 600, --color-ink-primary

Section gap: var(--space-10)
Zero card components, zero icons, zero metric stats on this page.
```

---

## PART 5 — PHASE 2+ FUTURE UI BANK

### 5.1 Leaderboard & Hall of Fame (Phase 2)

**Access:** All authenticated users. Navbar dropdown + mobile drawer.

**Note:** Neither page is on the landing page. These are in-app gamification features, not public marketing elements. Showing inter-university competition or empty archives publicly would look thin during early stages and distract from the core conversion goal.

**Full specification superseded to a dedicated companion document:** see `REUNI_LEADERBOARD_HALLOFFAME_DESIGN.md` for the complete spec covering the Leaderboard page (weekly / seasonal / inter-university sections) and the Hall of Fame page (seasonal / weekly archives), including the podium component, rank row component, university row component, champion card component, empty and low-population states, motion, dark mode, mobile layout, and accessibility requirements. That document is the source of truth for this feature; the summary below is retained only as a pointer.

### 5.2 Notifications (Phase 2)

```
Navbar avatar badge: 8px dot (accent color) when unread count > 0

Notification page: max-width 680px, centered

Each row: 64px min height
  Left: 8px dot (primary = unread, transparent = read)
  Icon by type (see addendum B.6)
  Text: --type-body, primary (unread) / secondary (read)
  Timestamp: --type-micro, --color-ink-tertiary

Mark all read: ghost button top-right
```

### 5.3 Boost Management (Phase 2)

Access from Dashboard → My Listings tab.

```
Boost tokens counter: "You have N boost tokens"
  N capped at 3, displayed in --font-mono

Per-listing boost action: "Boost this listing" btn (ghost) 
  On boost: listing rises to top of marketplace, boost_expires_at shown
  Duration: 48 hours
  
Post-boost badge on listing card: small "Boosted" chip (warning-muted)
```

### 5.4 Jury Voting (Phase 2)

Access via notification link only. Never in persistent navigation.

```
Triggered when trust_score >= 120

Report review card:
  Item details (image, title, category, description)
  Report reason (from reporter)
  
Vote buttons: "Keep listing" (ghost) | "Remove listing" (danger)
  Requires: majority verdict from assigned jury pool
  
Result notification: sent to both reporter and reporter
```

### 5.5 Item Report Flow (Phase 2)

```
Entry: "Report this listing" text link on item detail page
  Hover: --color-danger

Modal: 480px max-width (see 3.6 modal system)
  Header: "Report Listing" + "Your report is anonymous."
  
  Radio group (4 options, 44px min height each):
    Category fraud · Misleading description · No longer available · Condition misrepresented
    Selected: border: --color-primary, background: --color-primary-muted
    
  Submit: "Submit report" btn-primary full-width 48px height
  
Post-submit (replaces form):
  check_circle icon (40px, --color-success) centered
  "Report submitted. Our community jury will review this."
  "Back to marketplace" ghost button
```

### 5.6 QR Code Handshake (Phase 2)

```
Deferred from Phase 1. Addition to PIN page only.

Toggle link below PIN display: "Show QR code instead" (--type-small, --color-primary)

Expanded state:
  QR image: 200×200px, --radius-md, 1px border
  Server-side generated (encodes the PIN value)
  Alt: "QR code for PIN verification"
  "The other person scans this to confirm" (--type-small, --color-ink-secondary)
  
  Collapse: "← Back to PIN digits" (--type-small, --color-ink-tertiary)

Note: QR encodes the same 4-digit PIN. Scanning auto-fills the OTP input. PIN is not bypassed.
```

---

## PART 6 — GLOBAL FOOTER

```
Background: var(--color-surface)
Border-top: 1px solid var(--color-border)
Padding: var(--space-8)

Desktop layout (flex, space-between):
  Left: Campus Impact Widget
    [eco icon 20px, --color-success]
    "[campus_total_kg] kg saved" — [campus_total_kg] in --font-mono, 700, 17px, --color-primary
    " kg saved at [University]" — --type-body, 400, --color-ink-secondary
    Data: sum of kg_saved across all sold items for current university domain
    Precision: 1 decimal place (e.g. "245.8 kg")
    Server-side rendered by Jinja2 — not client-side JS
    
  Right: Links
    "Privacy Policy" · "© 2026 Reuni"
    --type-small, --color-ink-tertiary
    Hover: --color-ink-secondary
    Divider: " · "

Mobile: centered stack, padding: var(--space-6)

Landing page ONLY: aggregates kg_saved across ALL universities for the global counter.
App pages (subdomain): shows per-university counter only.
```

---

## PART 7 — MULTI-UNIVERSITY ARCHITECTURE (DESIGN IMPLICATIONS)

### 7.1 Subdomain Model

- `reuni.uk` / `www.reuni.uk` → Landing page (multi-university overview)
- `brookes.reuni.uk` → Oxford Brookes marketplace
- `oxford.reuni.uk` → University of Oxford marketplace

**Cookie preference:** When a user navigates to `reuni.uk`, if a `preferred_university` cookie exists, redirect immediately to `[slug].reuni.uk`. This prevents students seeing the landing page on repeated visits. Cookie is set when a student registers or explicitly selects a university.

### 7.2 University Context in UI

When on a university subdomain, all UI must reflect that university:
- Navbar university badge: shows short name (e.g. "Brookes", "Oxford")
- Hero strip: "Search [University] items…" placeholder
- Footer counter: per-university kg total only
- Auth pages: "Register with your [University] email" + domain hint
- Empty states: "Be the first to list at [University]"

When on `reuni.uk` (landing page):
- University picker is the primary conversion flow (see landing page spec)
- kg counter shows global total across all universities

### 7.3 Low Population States (Seed Data Phase)

With only 2 universities and limited seed data, all empty-facing states must be designed for small numbers without looking broken:

- Leaderboard < 5 users: show "Rankings unlock when more students list." — not an empty table
- Marketplace < 12 items: first page fills without pagination (no "showing 0–0 of 0" UI)
- kg counter with small value (e.g., "47.2 kg"): honest and credible. Never inflate.
- Leaderboard NOT shown on landing page for this reason.

### 7.4 International Markets (UAE, Egypt, etc.)

The design system is regionally neutral — no language targeting, no cultural assumptions baked into tokens. However, strategic note for B2B expansion:

**UAE:** Sustainability + community balance. ESG dashboard pitch remains valid. Landing page copy can emphasise both.

**Egypt:** Community-primary. The ESG data pitch has lower institutional pull if universities don't report Scope 3. In this case, the B2B wedge is weaker — Reuni competes more directly with WhatsApp groups and Facebook Marketplace. The design does not need to change, but the product pitch (and which sections the landing emphasises) would shift. This is a product/marketing strategy decision, not a design system decision.

**Design implication:** The landing page hero copy must not mention "Scope 3" or assume sustainability mandates. Frame kg_saved as community impact, not exclusively as ESG compliance data. This makes it regionally universal.

---

## PART 8 — THEME SYSTEM (LIGHT / DARK)

### 8.1 Theme Toggle

Theme toggle button present in:
- Desktop navbar (right side, icon-only, sun/dark_mode icon, aria-label="Toggle theme")
- Mobile drawer (full-width row with "Dark mode" label + toggle switch)
- Landing page floating navbar (desktop only)

Theme is stored in `localStorage` as `"reuni-theme": "light" | "dark"`. On page load, apply class to `<html>` before render to prevent flash. Fallback: `prefers-color-scheme`.

### 8.2 Implementation

```javascript
// In <head>, before any CSS paint:
const theme = localStorage.getItem('reuni-theme') 
  || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
document.documentElement.setAttribute('data-theme', theme);
```

```css
/* Set color-scheme on html for dark mode */
[data-theme="dark"] { color-scheme: dark; }
/* <meta name="theme-color"> must update dynamically to match --color-bg */
```

### 8.3 Landing Page with Themes

The landing page must work in both light and dark modes. The dark ESG dashboard preview card in Section 5 uses `--color-ink-primary` as its background — in dark mode this resolves to `#F5F5F4` (near white), which would break the "dark card" effect. Fix: use a hardcoded dark value for this specific card only, scoped as a local CSS variable:

```css
.esg-preview-card {
  --esg-card-bg: #1E2B2A; /* fixed dark teal, not a theme variable */
}
```

---

## PART 9 — MOTION SYSTEM

### 9.1 Philosophy

Motion is motivated, not decorative. Before any animation: "What does this communicate?" Valid: hierarchy, storytelling, feedback, state transition. Invalid: "it looks cool."

**Animation frequency rule (from Emil Kowalski):**

| Frequency | Decision |
|-----------|----------|
| 100+ times/day (keyboard shortcuts, search) | No animation |
| Tens of times/day (hover, list nav) | Reduce drastically |
| Occasional (modals, drawers, toasts) | Standard animation |
| Rare/first-time (onboarding, PIN ceremony) | Can add delight |

### 9.2 Spring Curves (Only These)

```css
/* Enter — instant start, smooth land */
cubic-bezier(0.16, 1, 0.3, 1)      /* --ease-out, use for most entries */
/* CTA hover — physical press feel */
cubic-bezier(0.32, 0.72, 0, 1)     /* --ease-spring */
/* Count-up numbers, page transitions */
cubic-bezier(0.19, 1, 0.22, 1)     /* --ease-expo */
```

### 9.3 Scroll Reveals

Use `IntersectionObserver` (not `window.addEventListener('scroll')`). Alternatively, Motion's `whileInView`. Elements start visible for safety — CSS class transitions, not visibility gates.

```javascript
// Safe pattern — element is visible by default, transition enhances it
const observer = new IntersectionObserver((entries) => {
  entries.forEach(el => el.isIntersecting && el.target.classList.add('revealed'));
}, { threshold: 0.15, rootMargin: '0px 0px -40px 0px' });
```

```css
.reveal { opacity: 0; transform: translateY(20px); transition: opacity 600ms var(--ease-out), transform 600ms var(--ease-out); }
.reveal.revealed { opacity: 1; transform: translateY(0); }
@media (prefers-reduced-motion: reduce) { .reveal, .reveal.revealed { opacity: 1; transform: none; transition: none; } }
```

### 9.4 `prefers-reduced-motion` (Non-Optional)

Every animation must have a `@media (prefers-reduced-motion: reduce)` override:
- Crossfade (opacity only, no transform) or instant state change
- Count-up animation: show final value immediately
- Card hover: color/border change only, no translateY
- PIN digit spring: none (instant fill)

This is both WCAG compliance and respect for users who set this preference.

### 9.5 Banned Animation Patterns

```
❌ window.addEventListener('scroll', ...) — use IntersectionObserver or Motion useScroll
❌ linear / ease-in-out transitions — use cubic-bezier spring curves
❌ Animating: top, left, width, height — only transform + opacity (compositor-friendly)
❌ Bounce / elastic easing — this is a trusted institutional platform, not a game
❌ backdrop-blur on scrolling containers — only on fixed/sticky elements
❌ Stagger delays > 120ms between siblings — feels slow, not premium
❌ Loop animations on informational content — if the user will see it often, stop it
❌ will-change: transform on more than 3 elements simultaneously
```

---

## PART 10 — ACCESSIBILITY REQUIREMENTS (GLOBAL)

Applies to every page, every component. Non-negotiable.

| Requirement | Target | Method |
|------------|--------|--------|
| Color contrast (body) | ≥ 4.5:1 | Verify against background, not token assumption |
| Color contrast (large text ≥ 18px) | ≥ 3:1 | Include bold 14px+ |
| Touch target minimum | 44 × 44px | All interactive elements |
| Focus ring | 3px `--color-primary-muted` outline, 2px offset | All interactive, use `:focus-visible` not `:focus` |
| Form labels | `<label for="...">` or wrapping | No exception, no aria-label substitute without label |
| Images | Descriptive `alt` or `alt=""` if decorative | Every `<img>` |
| Decorative icons | `aria-hidden="true"` | All icon spans/svgs not conveying information |
| Icon-only buttons | `aria-label="..."` | Every button with no visible text |
| Skip link | `<a href="#main-content" class="skip-link">Skip to main content</a>` | First element in every page `<body>` |
| `<button>` vs `<a>` | `<button>` for actions, `<a>` for navigation | Never `<div onClick>` |
| Native semantics first | `<button>`, `<a>`, `<label>`, `<table>` before ARIA | Semantics over ARIA |
| `aria-live` | On async update zones (flash messages, validation) | `aria-live="polite"` |
| `scroll-margin-top` | On all heading anchors | Prevents anchor scroll behind sticky nav |
| Keyboard navigation | All interactive elements reachable and operable | Tab order, Enter/Space activation |
| `color-scheme: dark` | On `<html>` for dark theme | Fixes native controls (scrollbars, inputs) |
| Non-breaking spaces | `10&nbsp;kg`, `£&nbsp;8`, brand names | Prevents awkward line breaks |
| `font-variant-numeric: tabular-nums` | On all number columns/comparisons | Prevents reflow on count-up |
| `touch-action: manipulation` | On all interactive elements | Prevents double-tap zoom delay |
| `-webkit-tap-highlight-color` | Set intentionally (usually transparent) | Consistent on mobile |

---

## PART 11 — GLOBAL ANTI-PATTERNS (ABSOLUTE BANS)

```
TYPOGRAPHY
❌ Inter, Roboto, Arial, Helvetica, Open Sans (any of these) — use Plus Jakarta Sans
❌ Fraunces, Instrument_Serif as default displays — LLM tells
❌ Display letter-spacing below −0.04em — letters touch
❌ Mixed font families in one headline (serif + sans emphasis)
❌ Body text without 4.5:1 contrast verification

COLOR
❌ Pure #000000 black — use --color-ink-primary
❌ Purple gradients / blue neon aesthetic
❌ Warm/cool gray oscillation — Stone family only, always
❌ Saturated accents above 80% saturation
❌ Additional accent colors without explicit justification
❌ Hardcoded color values in component CSS (always use variables)

LAYOUT
❌ Sidebar for any user role (strategic decision — see Part 2)
❌ 3 equal-width feature columns side by side
❌ Nested cards (card inside a card)
❌ Eyebrows on more than 1 of every 3 sections
❌ Section-layout repetition (same layout family used twice in sequence)
❌ h-screen — always min-h-[100dvh] (iOS Safari viewport jump)
❌ Horizontal scroll on mobile (critical failure)
❌ calc() percentage hacks instead of CSS Grid
❌ <div onClick> or <span onClick> — use <button> or <a>

MOTION
❌ linear or ease-in-out transitions
❌ Bounce or elastic easing
❌ Animating top, left, width, height properties
❌ backdrop-blur on scrolling containers
❌ window.addEventListener('scroll') for reveal animations
❌ No prefers-reduced-motion fallback
❌ transition: all (list properties explicitly)

COPY & UX
❌ Emoji in UI (except within achievement badges in leaderboard milestones)
❌ "Seamless", "Elevate", "Unleash", "Next-Gen", "Revolutionary" — AI copy tells
❌ Fake round numbers — kg_saved must be precise: "245.8 kg" not "~250 kg"
❌ Fabricated testimonials — only real quotes with real attribution
❌ "John Doe" / "Admin User" placeholder names in UI
❌ "Scroll to explore" / bouncing chevrons / scroll indicators

ICONS
❌ Thick-stroked generic Lucide defaults
❌ FontAwesome solid variants
❌ Mixed icon families on the same page
❌ Missing aria-hidden on decorative icons
❌ Missing aria-label on icon-only buttons
❌ Hand-rolled SVG icon paths (use library)
```

---

## PART 12 — RESPONSIVE BREAKPOINTS

```css
/* Mobile-first. Single breakpoint. */

/* Default (mobile, < 1024px):
   - Single column layouts
   - Bottom tab navigation
   - Full-bleed cards and images
   - Compact padding: var(--space-4) horizontal
   - No backdrop-blur on page-level elements
*/

@media (min-width: 1024px) {
  /* Desktop:
   - Multi-column layouts enabled
   - Top navbar (no bottom tab bar)
   - Search bar visible in navbar center
   - Hover states active
   - Padding: var(--space-8) horizontal
  */
}

/* Mobile-specific overrides */
.auth-card { border-radius: 0; } /* Mobile auth is full-bleed, not a card */
.claim-cta { position: fixed; bottom: calc(60px + env(safe-area-inset-bottom) + 12px); }
.category-filter-strip { overflow-x: auto; -webkit-overflow-scrolling: touch; scrollbar-width: none; }
.dashboard-metrics { grid-template-columns: 1fr 1fr; } /* 2-col not 4 on mobile */
```

---

## PART 13 — TOKEN EXTENSION PROTOCOL (FUTURE PHASES)

When Phase 3+ introduces new surfaces:

1. **Exhaust existing tokens first.** Never introduce a new color variable if an existing semantic token covers the intent.
2. **If a new token is required:** Add to `:root` with comment `/* Phase X addition */` and provide both light and dark values.
3. **No value hardcoded in component CSS** — always reference variables.
4. **No new font family** — system is `--font-sans` + `--font-mono` only.
5. **New components must:** reuse at least one Phase 1 atom, follow the existing border-radius scale, include `prefers-reduced-motion` override, pass WCAG AA contrast.

---

## PART 14 — PAGE NAVIGATION MATRIX

| Page | Who Sees | Entry Point |
|------|----------|-------------|
| Marketplace Index | All users | Root of subdomain, Home tab |
| Item Detail | All users | Click item card |
| PIN Handshake | Buyer + seller in active transaction | Transaction notification, activity feed |
| Listing Form | Authenticated students | "Sell" button (nav + tab bar) |
| User Dashboard | Authenticated | Profile tab (mobile), avatar dropdown (desktop) |
| ESG Partner Dashboard | Partner role | Avatar dropdown → "ESG Dashboard" |
| Admin Panel | Admin role | Avatar dropdown → "Admin Panel" |
| Profile | Authenticated | Mobile tab bar → Profile |
| Settings | Authenticated | Avatar dropdown → Settings |
| Auth pages | Unauthenticated | Register / Login links |
| Privacy Policy | All users | Footer link |
| Error pages | Triggered by 404/500 | Automatic |
| Leaderboard (P2) | All authenticated | Navbar dropdown + mobile drawer |
| Notifications (P2) | All authenticated | Navbar badge → dropdown link |
| Jury Voting (P2) | High-trust (≥120) | Notification link only |

---

*Unified Design System v1.0 · Reuni · July 2026*
*Supersedes: REUNI_DESIGN_BLUEPRINT_v3.md, REUNI_DESIGN_BLUEPRINT_ADDENDUM.md, REUNI_DESIGN_SYSTEM.md v1.0*
*This document does not include the landing page specification — see REUNI_LANDING_PAGE_DESIGN.md*

# REUNI — Design Blueprint Addendum v1.0
### Gap-Fill + Phase 2+ Future UI Bank · For Antigravity 2.0
### Extends: REUNI_DESIGN_BLUEPRINT.md v2.0 · June 2026

> This document patches every gap Antigravity 2.0 identified in the v2.0 blueprint, and extends the system with a complete Phase 2+ Future UI Bank. It is to be read **alongside** the v2.0 blueprint, not instead of it. All token references (`--color-*`, `--space-*`, etc.) resolve to the master token system defined in v2.0 Part 1.

---

## SECTION A — CORE GAPS (Phase 1 Missing Specs)

---

### A.1 — PRIVACY POLICY PAGE (`/privacy` · `privacy.html`)

**Page Role:** Legal document. Trust-building surface. Typography and readability are the entire product here. This is NOT a card layout, NOT a dashboard — it is a long-form prose document.

**Layout Constraints:**
- Max-width: `720px`, centered
- Padding top: `48px`; padding bottom: `80px`
- Horizontal padding: `var(--space-8)` (32px) on mobile; `0` on desktop (let max-width do the work)
- Background: `var(--color-bg)` — no surface cards wrapping content
- Zero card layouts on this page — BANNED here specifically

**Back Navigation (top of page, before all content):**
```
Element: <a href="/">
Icon: arrow_back (Material Symbol, 20px, --color-ink-secondary)
Text: "Back to Reuni" (--type-small, font-weight: 500, --color-ink-secondary)
Layout: inline-flex, align-items: center, gap: var(--space-2)
Hover: --color-primary, transition: color var(--duration-fast) var(--ease-out)
Margin-bottom: var(--space-10) (40px) — visual separation before title
```

**Page Header:**
```
Heading: "Privacy Policy"
  font: --font-sans, --type-display, font-weight: 800, --color-ink-primary
  text-wrap: balance
  margin-bottom: var(--space-3)

Last updated timestamp:
  format: "Last updated: [Month DD, YYYY]"
  font: --font-mono, --type-small, --color-ink-tertiary
  display: block
  margin-bottom: var(--space-10)

Divider: 1px solid var(--color-border), margin-bottom: var(--space-10)
```

**Typography Scale (prose document):**

| Element | Font | Size | Weight | Color | Line Height |
|---------|------|------|--------|-------|-------------|
| `h2` section headers | `--font-sans` | `20px` (1.25rem) | `700` | `--color-ink-primary` | `1.3` |
| `h3` sub-headers | `--font-sans` | `16px` (1rem) | `600` | `--color-ink-primary` | `1.3` |
| `p` body text | `--font-sans` | `15px` (0.9375rem) | `400` | `--color-ink-secondary` | `1.7` |
| `a` inline links | `--font-sans` | inherit | `500` | `--color-primary` | inherit |
| `strong` emphasis | `--font-sans` | inherit | `600` | `--color-ink-primary` | inherit |

**Spacing between prose elements:**
```
h2 → paragraph gap:   var(--space-3) (12px)
h3 → paragraph gap:   var(--space-2) (8px)
paragraph → paragraph: var(--space-4) (16px)
section → section gap: var(--space-10) (40px) — visual breath between major sections
h2 top margin:         var(--space-8) (32px) from previous block
```

**Internal anchor links (table of contents — optional):**
- If present, render as a simple ordered list above the first `h2`
- `--type-small`, `--color-primary`, no underline (underline on hover only)
- Margin-bottom: `var(--space-8)` before first section

**STRICTLY BANNED on this page:**
- Card containers wrapping text blocks
- Icon decorations beside headings
- Color backgrounds on sections
- Bold numbers presented as metric stats
- Any component from the marketplace system

---

### A.2 — MARKETPLACE HERO STRIP (Homepage Index, above listings grid)

**Strategic intent:** Context-aware strip that converts unauthenticated visitors into registrants, and rewards authenticated users with a live personal impact snapshot. Replaces generic "welcome" messaging with role-aware content.

**Height:** `80px` (desktop and mobile)

---

#### A.2.1 — Unauthenticated State

```
Background: var(--color-primary)
Layout: flex, align-items: center, justify-content: space-between
Padding: 0 var(--space-8) (desktop) / 0 var(--space-4) (mobile)
```

**Left block:**
```
Line 1: "Campus items. Real kg saved."
  font-size: 18px
  font-weight: 600
  color: #FFFFFF
  font-family: --font-sans

Line 2: "Student-to-student. In person. No fees."
  font-size: 14px
  font-weight: 400
  color: rgba(255, 255, 255, 0.75)
  margin-top: var(--space-1)
```

**Right block:**
```
CTA Button: "Register free →"
  background: #FFFFFF
  color: var(--color-primary)
  border-radius: var(--radius-md)
  height: 40px
  padding: 0 var(--space-5)
  font-size: --type-small
  font-weight: 600
  hover: background: rgba(255,255,255,0.9), transform: translateY(-1px)
  transition: var(--duration-fast) var(--ease-out)
  href: /auth/register
```

**Mobile (< 1024px) behavior:**
- Left block: show only Line 1 (truncate Line 2 at mobile width)
- OR: stack vertically if width permits (both lines visible)
- Right CTA: shrinks to `"Join free →"` if space is tight

---

#### A.2.2 — Authenticated State

```
Background: var(--color-surface)
Border-bottom: 1px solid var(--color-border)
Layout: flex, align-items: center
Padding: 0 var(--space-8) (desktop) / 0 var(--space-4) (mobile)
Overflow-x: auto (for chip scrolling on mobile)
```

**Three horizontal stat chips (`.hero-stat-chip`):**

Each chip:
```
background: var(--color-surface-raised)
border-radius: var(--radius-full)
padding: 12px 16px
display: inline-flex
align-items: center
gap: var(--space-2)
flex-shrink: 0 (prevents wrapping)
```

| Chip | Icon | Value Format | Color |
|------|------|-------------|-------|
| kg saved | `eco` (16px, `--color-success`) | `user.kg_saved_total` in `--font-mono`, `font-weight: 700`, `--color-primary` | Teal |
| Items listed | `package` or `inventory_2` (16px, `--color-ink-tertiary`) | count in `--font-mono`, `font-weight: 700`, `--color-ink-primary` | Default |
| Items purchased | `shopping_bag` (16px, `--color-ink-tertiary`) | count in `--font-mono`, `font-weight: 700`, `--color-ink-primary` | Default |

Label text beside value: `--type-micro`, `font-weight: 400`, `--color-ink-secondary`
e.g. chip reads: [eco icon] **2.4 kg** saved

**Gap between chips:** `var(--space-3)` (12px)
**Mobile:** strip scrolls horizontally; chips never wrap; no scrollbar visible (`scrollbar-width: none`, `-webkit-overflow-scrolling: touch`)

---

### A.3 — GLOBAL CAMPUS IMPACT COUNTER (Footer Widget)

**Strategic intent:** Visible proof of campus-wide sustainability momentum. Reinforces the B2B value proposition at the page bottom for every visitor. The single number that makes Reuni's ESG claim tangible.

**Location:** Footer block, present on ALL pages (via `base.html`)

**Desktop Layout:**
```
Footer container:
  background: var(--color-surface)
  border-top: 1px solid var(--color-border)
  padding: var(--space-8) var(--space-8)
  
Impact widget (left-aligned):
  display: inline-flex
  align-items: center
  gap: var(--space-3)

  eco icon: 20px, --color-success
  
  Text string: "[campus_total_kg] kg saved at Brookes"
    [campus_total_kg] — --font-mono, font-weight: 700, font-size: 17px, --color-primary
    " kg saved at Brookes" — --font-sans, --type-body, font-weight: 400, --color-ink-secondary
```

**Mobile Layout:**
- Same widget, centered rather than left-aligned
- Padding reduced to `var(--space-6)`

**Data binding:**
- `campus_total_kg` = sum of all `kg_saved` across all `items` where `status = 'sold'` and `university_domain = current_university`
- Rendered server-side by Jinja2 (not client-side JS)
- Formatted to 1 decimal place: `245.8` not `245.82`

**Footer secondary content (right-aligned, desktop):**
```
Links: Privacy Policy · © 2026 Reuni
  --type-small, --color-ink-tertiary
  Hover: --color-ink-secondary
  Divider: " · " separator character
```

---

### A.4 — PIN HANDSHAKE PAGE — MISSING SPECIFICATIONS

These patch the PIN page spec in v2.0 Page 3. All other PIN page specs remain as defined.

#### A.4.1 — WhatsApp Message Copy Template (Exact String)

The WhatsApp deep-link must pre-fill this EXACT message body:

```
"Hey, I just claimed your [item_title] on Reuni. When can we meet for the PIN handshake?"
```

Where `[item_title]` is the URL-encoded item title injected server-side into the Jinja2 template.

**WhatsApp URL format:**
```
https://wa.me/[seller_phone_e164]?text=Hey%2C+I+just+claimed+your+[ENCODED_TITLE]+on+Reuni.+When+can+we+meet+for+the+PIN+handshake%3F
```

**Copy Message button behavior:**
```
Default label:   "Copy message"
  --type-small, --color-primary, no underline, cursor: pointer
  
On click:
  1. Copy the EXACT string above (with resolved item_title) to clipboard
  2. Change label to: "Copied ✓"
     color: --color-success
     transition: color var(--duration-fast) var(--ease-out)
  3. After 1000ms: revert label back to "Copy message"
     transition: same

JavaScript pattern:
  navigator.clipboard.writeText(messageText).then(() => {
    btn.textContent = 'Copied ✓';
    btn.style.color = 'var(--color-success)';
    setTimeout(() => {
      btn.textContent = 'Copy message';
      btn.style.color = '';
    }, 1000);
  });
```

---

#### A.4.2 — Role-Aware PIN Instruction Headers

The instructional text directly above the PIN display or PIN input MUST vary by role combination. Four states:

| User Role | Item Type | Is PIN Holder? | Instruction Text |
|-----------|-----------|---------------|-----------------|
| Seller | Free (£0) | ✅ YES | "Share this PIN with the buyer when they confirm collection." |
| Buyer | Paid (£) | ✅ YES | "Share this PIN with the seller **after** inspecting the item and sending payment." |
| Buyer | Free (£0) | ❌ NO | "The seller will tell you the 4 digits when you collect." |
| Seller | Paid (£) | ❌ NO | "Enter the PIN the buyer gives you after you confirm payment." |

**Jinja2 template logic (pseudocode):**
```jinja2
{% if is_pin_holder %}
  {% if item.price == 0 %}
    {# Seller holds PIN on free item #}
    <p class="pin-instruction">Share this PIN with the buyer when they confirm collection.</p>
  {% else %}
    {# Buyer holds PIN on paid item #}
    <p class="pin-instruction">Share this PIN with the seller <strong>after</strong> inspecting the item and sending payment.</p>
  {% endif %}
{% else %}
  {% if item.price == 0 %}
    {# Buyer enters PIN on free item #}
    <p class="pin-instruction">The seller will tell you the 4 digits when you collect.</p>
  {% else %}
    {# Seller enters PIN on paid item #}
    <p class="pin-instruction">Enter the PIN the buyer gives you after you confirm payment.</p>
  {% endif %}
{% endif %}
```

**Instruction text styling:**
```
Element: <p class="pin-instruction">
font: --font-sans, --type-body, font-weight: 400, --color-ink-secondary
line-height: var(--leading-body)
text-align: center
max-width: 340px
margin: 0 auto var(--space-5)
strong: font-weight: 700, --color-ink-primary
```

---

#### A.4.3 — Mobile Keyboard Handling (Visual Viewport Listener)

**Problem being solved:** On mobile, the software keyboard obscures the lower portion of the screen. Standard `window.innerHeight` does NOT update when the keyboard opens (on iOS). `window.visualViewport.height` does.

**Required JavaScript pattern:**

```javascript
// PIN page only — executes after DOM ready
const handleViewportResize = () => {
  const inputContainer = document.querySelector('.pin-entry-inputs');
  if (!inputContainer) return;

  const viewport = window.visualViewport;
  if (!viewport) return;
  
  const visibleTop = viewport.offsetTop;
  const containerTop = inputContainer.getBoundingClientRect().top + window.scrollY;
  const targetScrollY = containerTop - visibleTop - 100; // 100px below visible top
  
  window.scrollTo({ top: targetScrollY, behavior: 'smooth' });
};

function centerPinInputsAboveKeyboard() {
  const inputContainer = document.querySelector('.pin-entry-inputs');
  if (!inputContainer || !window.visualViewport) return;

  window.visualViewport.addEventListener('resize', handleViewportResize);
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
  if (window.visualViewport) {
    window.visualViewport.removeEventListener('resize', handleViewportResize);
  }
});
```

**CSS support rule:**
```css
/* Ensure PIN inputs are scrollable-to above keyboard */
.pin-entry-card {
  scroll-margin-top: 100px; /* Used by browser scroll-into-view */
}

@supports (height: 100dvh) {
  .pin-entry-wrapper {
    min-height: 100dvh; /* Never use 100vh — iOS Safari catastrophic jump */
  }
}
```

---

## SECTION B — PHASE 2+ FUTURE UI BANK

> **Execution Policy:** These blueprints are design-ready but NOT yet wired to backend routes. When Phase 2 development begins, these specs drop directly into Antigravity without rework. All token references resolve to the same master system. Component patterns reuse Phase 1 atoms — no new design languages introduced.

---

### B.1 — LEADERBOARD PAGE (`/leaderboard`)

**Phase:** 2 (Gamification & Growth)
**Route:** `/leaderboard`
**Template:** `leaderboard.html`

**Page Role:** Campus-wide sustainability competition surface. Creates social proof and repeat engagement. The leaderboard season system makes this a living, recurring feature.

**Layout:**
- Max-width: `800px`, centered
- Padding: `var(--space-8)` horizontal

---

**Component: Tab Selector (`.leaderboard-tabs`)**

Two tabs:
- "My University" (active by default)
- "All Universities" (Phase 3 — may render as disabled with tooltip "Coming soon" until multi-university launch)

Tab pattern: same segmented pill selector as dashboard tabs. Active tab: `--color-primary` fill, white text. Inactive: ghost.

---

**Component: Season Badge (above podium)**

```
Pill: background: var(--color-primary-muted), border-radius: var(--radius-full)
      padding: var(--space-2) var(--space-4)
      
Icon: event (16px, --color-primary)
Text: "Season 1 — Spring 2026" (--type-small, font-weight: 600, --color-primary)
Subtext: "Ends in X days" (--type-micro, --color-ink-tertiary)

Layout: inline-flex, centered above podium, margin-bottom: var(--space-6)
```

---

**Component: Top 3 Podium Block (`.podium`)**

```
Layout: 3-column flex, align-items: flex-end, justify-content: center
Gap: var(--space-4)
```

**Podium column structure (each):**

```
Flex column, align-items: center

Avatar circle:
  2nd and 3rd: 48px × 48px
  1st: 56px × 56px (elevated prominence)
  border-radius: var(--radius-full)
  background: var(--color-primary-muted) (default) or badge border per milestone

Crown icon for 1st:
  workspace_premium icon (24px, #F59E0B amber/gold)
  position: absolute, top: -12px, centered above avatar
  aria-label: "1st place"

Display name: --type-small, font-weight: 600, --color-ink-primary, text-align: center
kg_saved value: --font-mono, font-weight: 700, --type-small, --color-success

Rank number: displayed BELOW name in --type-micro, --color-ink-tertiary
  Format: "#1", "#2", "#3"
```

**Podium platform heights (the physical "step" visual):**
```
2nd place column: platform height 60px, background: var(--color-surface-raised)
1st place column: platform height 80px, background: var(--color-primary-muted), border-top: 2px solid var(--color-primary)
3rd place column: platform height 50px, background: var(--color-surface-raised)
Platform width: 80px each
Platform border-radius: var(--radius-md) var(--radius-md) 0 0 (top corners only)
```

**Asymmetric layout rule:** The 3 columns are NEVER equal height/size. 1st is always visually dominant. This is correct design — do NOT equalize.

---

**Component: Rankings List (Positions 4–10) (`.leaderboard-list`)**

```
Background: var(--color-surface)
Border-radius: var(--radius-xl)
Box-shadow: var(--shadow-card)
Overflow: hidden
```

Each row:
```
Height: 56px
Padding: 0 var(--space-5)
Border-bottom: 1px solid var(--color-border) (last row: none)
Hover: background: var(--color-surface-raised)
Display: flex, align-items: center, gap: var(--space-4)

Left: Rank number — --font-mono, --type-small, font-weight: 700, --color-ink-tertiary, width: 28px, text-align: right
Avatar: 32px × 32px circle, --radius-full
Name: --type-body, font-weight: 500, --color-ink-primary, flex: 1
kg_saved: --font-mono, --type-small, font-weight: 700, --color-success, text-align: right
```

**Stagger entrance animation:**
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

```
Position: sticky, bottom: calc(60px + env(safe-area-inset-bottom)) (above mobile tab bar)
         OR bottom: 0 on desktop

Background: var(--color-primary-muted)
Border-top: 2px solid var(--color-primary)
Height: 52px
Padding: 0 var(--space-5)
Display: flex, align-items: center, gap: var(--space-4)
Box-shadow: 0 -4px 12px rgba(13, 148, 136, 0.1) (tinted upward shadow)
Z-index: var(--z-raised)

Left: "You" label — --type-micro, font-weight: 600, --color-primary, uppercase, letter-spacing: 0.06em
Rank number: --font-mono, --type-body, font-weight: 800, --color-primary (e.g. "#47")
Name: --type-body, font-weight: 500, --color-ink-primary, flex: 1
kg_saved: --font-mono, font-weight: 700, --color-success
```

If user is in top 10 (already visible): hide the sticky bar.

---

### B.2 — JURY VOTING DASHBOARD (`/jury/<report_id>`)

**Phase:** 2 (Anti-Fraud & Moderation — Jury System)
**Route:** `/jury/<report_id>`
**Template:** `jury/vote.html`
**Access:** Trust score ≥ 120 only (enforced server-side via decorator)

**Page Role:** Community moderation tool. The jury sees a reported item anonymized, makes a verdict, and gets trust points if they vote with the majority. Must feel weighty and deliberate — not casual.

**Layout:**
- Max-width: `640px`, centered
- Padding: `var(--space-10)` horizontal, `var(--space-8)` vertical

---

**Component: Jury Context Header**

```
Eyebrow badge: "Jury Review"
  background: var(--color-warning-muted)
  color: var(--color-warning)
  border-radius: var(--radius-full)
  --type-micro, font-weight: 600, uppercase, letter-spacing: 0.08em
  padding: var(--space-1) var(--space-3)
  margin-bottom: var(--space-4)

Heading: "Review Reported Item" — --type-display, font-weight: 800
Subtext: "Your vote is anonymous. You earn +2 trust if you vote with the majority."
  --type-body, --color-ink-secondary, margin-top: var(--space-2)
```

---

**Component: Reported Item Display Card**

```
Background: var(--color-surface)
Border-radius: var(--radius-xl)
Box-shadow: var(--shadow-card)
Overflow: hidden
Margin: var(--space-8) 0
```

Layout — two columns (desktop) / stacked (mobile):

**Left: Item photo (if available)**
```
Width: 160px (fixed, desktop) / 100% (mobile)
Aspect ratio: 4:3
Object-fit: cover
Background fallback: var(--color-surface-raised) + image icon
```

**Right: Item details**
```
Padding: var(--space-5)

Anonymous seller badge:
  gavel icon (16px, --color-ink-tertiary) + "Anonymous Seller"
  --type-small, --color-ink-tertiary, margin-bottom: var(--space-3)

Item title: --type-title, font-weight: 700, --color-ink-primary

Item description: --type-body, --color-ink-secondary, max 4 lines (line-clamp: 4)
  "Show more" toggle if truncated

Category chip: standard pill, --color-primary-muted

Price: --font-mono if paid, or "Free" in --color-success
```

---

**Component: Violation Report Panel**

```
Background: var(--color-warning-muted)
Border: 1px solid var(--color-warning)
Border-radius: var(--radius-md)
Padding: var(--space-4)
Margin: var(--space-5) 0
Display: flex, gap: var(--space-3)

Icon: flag (20px, --color-warning)

Content:
  Label: "Reported for:" — --type-small, font-weight: 600, --color-warning, margin-bottom: var(--space-1)
  Reason text: --type-body, --color-ink-secondary
```

Violation reason options (rendered as text, not interactive):
- "Category fraud — wrong category selected"
- "Misleading description"
- "Item condition misrepresented"
- "Item not available / ghost listing"

---

**Component: Verdict Action Buttons**

Two large buttons, stacked (mobile) or side-by-side (desktop):

```
Layout (desktop): display: grid, grid-template-columns: 1fr 1fr, gap: var(--space-4)
```

**"Clear" button:**
```
Height: 56px
Border-radius: var(--radius-md)
Border: 2px solid var(--color-success)
Background: transparent (ghost style)
Color: --color-success
Icon: check_circle (20px, left of text)
Label: "Clear"
Font: --font-sans, --type-body, font-weight: 600
Hover: background: var(--color-success-muted)
Active: transform: scale(0.98), transition: 100ms
```

**"Guilty" button:**
```
Same dimensions
Border: 2px solid var(--color-danger)
Background: transparent (ghost style)
Color: --color-danger
Icon: cancel (20px, left of text)
Label: "Guilty"
Hover: background: var(--color-danger-muted)
```

---

**Component: Inline Confirmation Step**

After clicking either verdict button, the button grid hides and an inline confirmation appears (NO modal — keeps context):

```
Container: border: 1px solid var(--color-border), border-radius: var(--radius-lg), padding: var(--space-5)

Text: "You're voting to [Clear / find Guilty]. This cannot be changed."
  --type-body, --color-ink-secondary, margin-bottom: var(--space-4)

Confirm button (full-width):
  "Confirm — [Clear / Guilty]"
  For Clear: background: var(--color-success), color: white
  For Guilty: background: var(--color-danger), color: white
  Height: 48px, --radius-md

Cancel link (below):
  "← Go back" — --type-small, --color-ink-secondary, centered
  hover: --color-primary
```

---

**Component: Post-Vote Success Card**

Replaces entire verdict section after submission:

```
Background: var(--color-primary-muted)
Border-radius: var(--radius-xl)
Padding: var(--space-8)
Text-align: center

Icon: check_circle (48px, --color-success) — entrance animation: scale(0.5) → scale(1), spring

Heading: "Vote submitted." — --type-title, font-weight: 700, --color-ink-primary
Body: "+2 trust if you voted with the majority." — --type-body, --color-ink-secondary

CTA: "Back to marketplace" ghost button → /
```

Entrance animation for success card:
```css
@keyframes successReveal {
  from { transform: scale(0.95) translateY(8px); opacity: 0; }
  to   { transform: scale(1) translateY(0); opacity: 1; }
}
.vote-success-card { animation: successReveal 0.35s var(--ease-spring) forwards; }
@media (prefers-reduced-motion: reduce) { .vote-success-card { animation: none; opacity: 1; } }
```

---

### B.3 — BADGE SYSTEM VISUAL STATES (User Avatars — Phase 2)

**Phase:** 2
**Applied on:** Item cards (seller avatar), Profile page (profile hero avatar), Dashboard, Leaderboard

Badges are applied as CSS classes on avatar elements. The underlying avatar component structure does not change — these are visual-only overrides.

**Standard avatar (no badge):**
```
.avatar {
  width: var(--size); /* 32px, 48px, 56px, or 80px depending on context */
  height: var(--size);
  border-radius: var(--radius-full);
  background: var(--color-primary-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-sans);
  font-weight: 800;
  color: var(--color-primary);
  flex-shrink: 0;
}
```

---

**Tree Milestone (10 kg saved) — `.avatar--tree`**
```css
.avatar--tree {
  box-shadow: 0 0 0 3px var(--color-primary-muted);
  /* Soft outer glow — ONLY acceptable glow besides Sell tab, because
     it's tinted to brand color and communicates milestone, not decoration */
}
```

Tooltip on hover (desktop only): "🌱 10 kg milestone"

---

**Forest Milestone (50 kg saved) — `.avatar--forest`**
```css
.avatar--forest {
  border: 3px solid var(--color-primary);
  /* Solid brand teal border — permanent, visible at all avatar sizes */
}
```

Tooltip on hover: "🌳 50 kg milestone"

---

**Ecosystem Milestone (100 kg saved) — `.avatar--ecosystem`**

```css
.avatar--ecosystem {
  position: relative;
  border: 2px solid transparent;
  background-clip: padding-box;
}

.avatar--ecosystem::before {
  content: '';
  position: absolute;
  inset: -3px;
  border-radius: var(--radius-full);
  background: linear-gradient(
    135deg,
    var(--color-primary),
    var(--color-success),
    #0ea5e9,  /* sky-500 — third point of the gradient arc */
    var(--color-primary)
  );
  background-size: 300% 300%;
  animation: ecosystemGradient 3s ease infinite;
  z-index: -1;
}

@keyframes ecosystemGradient {
  0%   { background-position: 0% 50%; }
  50%  { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

@media (prefers-reduced-motion: reduce) {
  .avatar--ecosystem::before {
    animation: none;
    /* Static gradient preserved — milestone identity remains visible */
    background-position: 0% 50%;
  }
}
```

**Ecosystem text badge (on item cards, beside seller name):**
```
Element: <span class="ecosystem-badge">
Content: "Ecosystem" (NO recycling emoji in badge — use text or icon only)
Icon: recycling (Material Symbol, 12px, --color-primary)
background: var(--color-primary-muted)
border-radius: var(--radius-full)
padding: 2px 8px
--type-micro, font-weight: 600, --color-primary
display: inline-flex, align-items: center, gap: 4px
margin-left: var(--space-2)
```

Note on emojis in badges: The system-wide emoji ban applies everywhere EXCEPT this one badge label. The product spec uses ♻️ — replace with the `recycling` Material Symbol instead. No emoji in any badge.

---

### B.4 — BOOST TOKEN UI (Phase 2)

**Phase:** 2
**Appears on:** User Dashboard, Item Listings (feed), Listing Form

---

#### B.4.1 — Dashboard Boost Token Counter

Location: Top of dashboard, beside or below the kg_saved personal total chip.

```
Element: .boost-token-badge
Background: var(--color-accent-muted)
Border-radius: var(--radius-full)
Padding: var(--space-2) var(--space-4)
Display: inline-flex, align-items: center, gap: var(--space-2)

Icon: rocket_launch (16px, --color-accent)
Text: "[N] boost tokens available"
  [N] — --font-mono, font-weight: 700, --color-accent
  " boost tokens available" — --type-small, font-weight: 400, --color-ink-secondary

If N == 0:
  Icon: rocket_launch (16px, --color-ink-tertiary)
  Text color: --color-ink-tertiary
  Text: "No boost tokens — earn more via transactions"
```

---

#### B.4.2 — "Boost" Button on Listings (My Dashboard · My Listings Tab)

Appears beside each unsold listing the user owns, when they have ≥ 1 boost token.

**Button:**
```
Label: "Boost"
Icon: bolt (14px, left of label)
Style: ghost, border: 1px solid var(--color-accent), color: var(--color-accent)
Border-radius: var(--radius-md)
Height: 36px, padding: 0 var(--space-4)
--type-small, font-weight: 600
Hover: background: var(--color-accent-muted)
```

**Inline Confirmation Dialog (replaces button on click — no modal):**
```
Container: border: 1px solid var(--color-accent), background: var(--color-accent-muted),
           border-radius: var(--radius-md), padding: var(--space-4)
           Entrance: height: 0 → auto + opacity: 0 → 1, --duration-mid, --ease-out

Text: "Boost for 30 days? (1 token will be used)"
  --type-small, --color-ink-secondary, margin-bottom: var(--space-3)

Remaining tokens hint: "You have [N] tokens left after this."
  --type-micro, --color-ink-tertiary

Two buttons (side-by-side):
  "Use token" — filled accent (background: var(--color-accent), white text, height: 36px, --radius-md)
  "Cancel" — ghost, --color-ink-secondary, same dimensions
```

---

#### B.4.3 — "Featured" Tag on Boosted Listings (Feed)

Shown on item cards in the marketplace when `item.is_boosted == True` and `item.boost_expires_at > now`.

```
Element: .boost-featured-tag
Position: absolute, top: var(--space-2), left: var(--space-2)

Background: var(--color-accent)
Color: #FFFFFF
Border-radius: var(--radius-sm)
Padding: 2px 8px
Display: inline-flex, align-items: center, gap: 4px

Icon: bolt (12px, #FFFFFF)
Label: "Featured"
Font: --font-mono, font-size: 11px, font-weight: 600

Note: This tag occupies the SAME position as the Category chip. On boosted items,
the Category chip moves BELOW the image into the content block.
The featured tag is the absolute-position replacement at top-left.
```

---

### B.5 — SHADOW-BAN WARNING BANNER (Phase 2 — Sub-50 Trust Score)

**Phase:** 2
**Location:** Top of user dashboard, visible only to users with `trust_score < 50`

**Critical copy rules (from product spec — non-negotiable):**
- MUST include: "Your listings are receiving less visibility due to community feedback. Continue making successful transactions to improve."
- MUST NEVER use the words: "Trust Score", "Shadow-ban", or "Muted"

---

**Component: (`.shadow-warning-banner`)**

```
Background: var(--color-warning-muted)
Border: 1px solid var(--color-warning)
Border-radius: var(--radius-md)
Padding: var(--space-4) var(--space-5)
Margin-bottom: var(--space-6)
```

**Content layout:**
```
Display: flex, align-items: flex-start, gap: var(--space-3)

Icon: visibility_off (20px, --color-warning, flex-shrink: 0, margin-top: 2px)

Right block:
  Heading: "Reduced Visibility" — --type-small, font-weight: 700, --color-ink-primary, margin-bottom: var(--space-1)
  
  Body text: "Your listings are receiving less visibility due to community feedback. Continue making successful transactions to improve."
    --type-body, --color-ink-secondary, line-height: 1.6
    margin-bottom: var(--space-3)

  Progress tracker: "Progress: [n]/3 clean exchanges completed"
    
    [n] — --font-mono, font-weight: 700, --color-primary (the number)
    "/3 clean exchanges completed" — --type-small, font-weight: 400, --color-ink-secondary
    
    Progress bar below text:
      height: 6px
      background: var(--color-surface-raised)
      border-radius: var(--radius-full)
      width: 200px
      
      Fill: background: var(--color-primary), border-radius: var(--radius-full)
            width: calc([n] / 3 * 100%) — animated on mount
            transition: width 0.5s var(--ease-out)
```

**Disappearance:** Banner is removed server-side once `trust_score >= 50`. It does NOT animate out — it simply does not render on the next page load. No need for client-side removal animation.

---

### B.6 — IN-APP NOTIFICATION FEED (Phase 2)

**Phase:** 2 (requires `notifications` table from future schema)
**Route:** `/notifications`
**Template:** `notifications.html`

**Page Role:** Central inbox for system events. Replaces email-only notifications with an in-app layer.

**Layout:** Max-width `680px`, centered

---

**Navbar notification indicator (Phase 2 addition to navbar):**
```
Position: on the avatar button (top-right badge)
Unread count badge:
  position: absolute, top: -2px, right: -2px
  width: 16px, height: 16px
  background: var(--color-accent)
  border-radius: var(--radius-full)
  border: 2px solid var(--color-surface) (visible against navbar)
  font: --font-mono, 10px, font-weight: 700, color: #FFFFFF
  text-align: center, line-height: 12px
  Display only if unread_count > 0
```

---

**Notification List:**

Each notification row:
```
Height: auto (min 64px)
Padding: var(--space-4) var(--space-5)
Border-bottom: 1px solid var(--color-border)
Hover: background: var(--color-surface-raised)
Cursor: pointer (if notification has a link)
Display: flex, align-items: flex-start, gap: var(--space-4)
```

**Left indicator dot (`.notif-dot`):**
```
width: 8px, height: 8px
border-radius: var(--radius-full)
background: var(--color-primary) (unread) or transparent (read)
border: 1px solid var(--color-border) (read only)
flex-shrink: 0, margin-top: 6px
```

**Right content:**
```
Notification text: --type-body, --color-ink-primary (unread), --color-ink-secondary (read)
Timestamp: --type-micro, --color-ink-tertiary, margin-top: var(--space-1)
```

**Notification type → icon mapping:**

| Event | Icon | Color |
|-------|------|-------|
| Item claimed | `shopping_bag` | `--color-accent` |
| PIN exchange complete | `check_circle` | `--color-success` |
| Claim cancelled | `cancel` | `--color-danger` |
| Jury call (high trust users) | `gavel` | `--color-warning` |
| Trust milestone | `eco` | `--color-success` |
| System message | `info` | `--color-primary` |

**Mark all read:** ghost button top-right of page header. Clicking transitions all dot indicators from filled to empty simultaneously.

---

### B.7 — ITEM REPORT FLOW (Phase 2 — "Report this listing")

**Phase:** 2 (requires `reports` table)
**Entry point:** Item detail page — small text link below the item description

**Entry link:**
```
Text: "Report this listing"
--type-small, --color-ink-tertiary
Hover: --color-danger
cursor: pointer
Position: below description, above seller info block
```

**Report Modal:**
```
Max-width: 480px
Background: var(--color-surface)
Border-radius: var(--radius-xl)
Box-shadow: var(--shadow-modal)
Padding: var(--space-8)
Backdrop: rgba(0,0,0,0.5), backdrop-filter: blur(4px)
Z-index: var(--z-modal)
```

**Report form structure:**
```
Heading: "Report Listing" — --type-title, font-weight: 700
Subtext: "Your report is anonymous." — --type-small, --color-ink-tertiary
Margin-bottom: var(--space-6)

Radio group: "Select a reason" label (--type-small, font-weight: 600)
Options (each 44px min height, border: 1px solid var(--color-border), --radius-md, padding: var(--space-3) var(--space-4)):
  ○ Category fraud — item listed in the wrong category
  ○ Misleading description
  ○ Item no longer available
  ○ Item condition misrepresented

Selected radio: border-color: var(--color-primary), background: var(--color-primary-muted)
Active radio dot: var(--color-primary) via accent-color CSS

Submit button: "Submit report" — filled primary, full-width, height: 48px
Cancel: "Cancel" ghost button below, --color-ink-secondary
```

**Post-submit state (replaces form):**
```
Icon: check_circle (40px, --color-success)
Text: "Report submitted. Our community jury will review this." — --type-body, centered
CTA: "Back to marketplace" — ghost button
```

---

### B.8 — QR CODE HANDSHAKE (Phase 2 — Alternative to PIN)

**Phase:** 2 (deferred from product spec)
**Page role:** An alternative confirmation method on the PIN page — the PIN holder can display a QR code encoding the PIN instead of reading digits aloud.

**UI Addition to PIN page (`items/pin.html`):**

Below the PIN digit display, add a toggle:

```
Toggle link: "Show QR code instead"
--type-small, --color-primary, cursor: pointer

Expanded state (QR panel):
  Background: var(--color-surface)
  Border-radius: var(--radius-lg)
  Padding: var(--space-6)
  text-align: center
  
  QR code image:
    Width: 200px × 200px
    Border-radius: var(--radius-md)
    Border: 1px solid var(--color-border)
    Generated server-side using a QR library; encodes the PIN value
    Alt text: "QR code for PIN verification"
  
  Instruction: "The other person scans this to confirm" — --type-small, --color-ink-secondary
  
  Collapse link: "← Back to PIN digits" — --type-small, --color-ink-tertiary
```

**Note:** The QR code DOES NOT replace the PIN — it encodes the same 4-digit PIN. The receiving party still enters the PIN. The QR is a scan-to-fill convenience for the PIN entry fields.

---

## SECTION C — DESIGN EVOLUTION PRINCIPLES (For Future Phases)

These rules govern how new features must be introduced into the Reuni design system without breaking the established visual language.

---

### C.1 — Token Extension Protocol

When Phase 3+ introduces new surfaces (e.g., payment integration UI, multi-university network map):

1. **Exhaust existing tokens first.** Never introduce a new color variable if an existing semantic token covers the intent.
2. **If a new token is required:** Add it to the master `:root` declaration with a comment `/* Phase X addition */` and provide both light and dark mode values.
3. **No token value may be hardcoded** in component CSS. Always reference the variable.
4. **No new font family** may be introduced. The system is `--font-sans` + `--font-mono` only.

---

### C.2 — Component Addition Protocol

Every new Phase 2+ component must:
1. Be documented in this Future UI Bank before implementation
2. Reuse at least one existing Phase 1 atom (button, chip, card shell, form input)
3. Follow the same border-radius scale (`--radius-sm/md/lg/xl/full`) — no new values
4. Include a `prefers-reduced-motion` override if it contains any animation
5. Pass the same WCAG AA contrast requirements (4.5:1 body, 3:1 large text)

---

### C.3 — New Page Execution Checklist

For every new page template added in Phase 2+:

```
□ Extends base.html (inherits navbar, flash messages, footer)
□ Sets correct <title> and meta description
□ Mobile breakpoint handled at 1024px (not 768px)
□ Bottom sticky CTA (if applicable) clears: calc(60px + env(safe-area-inset-bottom))
□ Empty state defined (no "loading..." dead ends)
□ All interactive elements ≥ 44px × 44px touch target
□ Focus rings present on all interactive elements
□ No new colors introduced (unless Token Extension Protocol followed)
□ No emojis in UI (Material Symbols only)
□ Page appears in navbar profile dropdown if role-gated (admin/partner)
   OR in mobile drawer if universally accessible
```

---

### C.4 — Page Addition to Navigation

When a new route becomes active in Phase 2+:

| New Page | Who Sees It | Where It Appears |
|----------|------------|-----------------|
| Leaderboard | All authenticated users | Navbar dropdown + mobile drawer |
| Jury voting | High-trust users (120+) | Notification link only (no persistent nav entry) |
| Notifications | All authenticated users | Navbar avatar badge → dropdown link |
| Boost management | All authenticated users | Dashboard → My Listings tab |
| Report flow | All authenticated users | Item detail page only (contextual) |

---

*Addendum v1.0 — June 2026*
*Gap-fill + Phase 2+ Future UI Bank*
*All Phase 1 token references resolve to REUNI_DESIGN_BLUEPRINT.md v2.0 Part 1*
*Read both documents together. This addendum never contradicts the base blueprint — it extends it.*

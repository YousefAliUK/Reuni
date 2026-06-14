# Reuni Frontend Design System & UI Specification Map

This document serves as the absolute visual and architectural reference for the Reuni user interface. It describes every design token, style rule, responsive layout change, component state, and client-side script behavior in detail.

---

## 1. Design System & Global Style Tokens

### 1.1 Color Palettes
Reuni implements a clean, slate-based color scheme with highly legible accent colors designed to meet WCAG AA contrast standards. Colors automatically switch using the `data-theme="dark"` attribute on the `<html>` element.

| Color Variable Name | Light Mode Value (HEX) | Dark Mode Value (HEX) | Role / Usage |
| :--- | :--- | :--- | :--- |
| `--color-bg` | `#F8FAFC` (Slate-50) | `#0F172A` (Slate-900) | Core page background |
| `--color-surface` | `#FFFFFF` | `#1E293B` (Slate-800) | Cards, dropdowns, sidebars, header panels |
| `--color-surface-raised`| `#F1F5F9` (Slate-100) | `#334155` (Slate-700) | Nested surfaces, input fills, table rows |
| `--color-border` | `rgba(226, 232, 240, 0.7)` | `rgba(51, 65, 85, 0.8)` | Whisper borders (1px structural lines) |
| `--color-ink-primary` | `#0F172A` (Slate-900) | `#F1F5F9` (Slate-100) | Headlines, active labels, primary text |
| `--color-ink-secondary` | `#475569` (Slate-600) | `#94A3B8` (Slate-400) | Body copy, descriptions, secondary text |
| `--color-ink-tertiary` | `#94A3B8` (Slate-400) | `#475569` (Slate-600) | Timestamps, placeholders, metadata labels |
| `--color-primary` | `#0D9488` (Teal-600) | `#70B8AE` (Teal-300) | Primary CTAs, active indicators, offset badges |
| `--color-primary-hover` | `#0F766E` (Teal-700) | — (inherited/opacity) | Hover state for primary actions |
| `--color-primary-muted` | `#CCFBF1` (Teal-100) | `rgba(13, 148, 136, 0.15)`| Soft background highlights, success zones |
| `--color-accent` | `#F97316` (Orange-500) | `#FB923C` (Orange-400) | Claim actions, pricing highlights, urgency |
| `--color-accent-hover` | `#EA6C0A` (Orange-600) | — | Hover state for accent actions |
| `--color-accent-muted` | `#FFF7ED` (Orange-50) | `rgba(249, 115, 22, 0.12)` | Urgency panels, warning highlights |
| `--color-danger` | `#EF4444` (Red-500) | `#F87171` (Red-400) | Destructive actions, validation errors, penalty labels |
| `--color-danger-muted` | `#FEF2F2` (Red-50) | `rgba(239, 68, 68, 0.15)` | Error box background fills |
| `--color-success` | `#22C55E` (Green-500) | `#4ADE80` (Green-400) | Done states, verified badges, free indicators |
| `--color-success-muted` | `#F0FDF4` (Green-50) | `rgba(34, 197, 94, 0.15)` | Success tags, green banner fills |
| `--color-warning` | `#F59E0B` (Amber-500) | `#FBBF24` (Amber-400) | Expiry timers, high-value alerts |
| `--color-warning-muted` | `#FFFBEB` (Amber-50) | `rgba(245, 158, 11, 0.15)` | Warning banner backgrounds |

### 1.2 Typography
* **Primary Sans-Serif Font Family**: `'Plus Jakarta Sans', system-ui, -apple-system, sans-serif` (`--font-sans`). Used for body text, headings, buttons, and form labels.
* **Monospace Font Family**: `'JetBrains Mono', 'Fira Code', monospace` (`--font-mono`). Used for carbon values (e.g. `2.5 kg`), PIN codes, timers, and timestamps.
* **Sizing Scale**:
  * `--type-display` (`clamp(1.875rem, 4vw, 2.625rem)`): Page titles.
  * `--type-title` (`clamp(1.25rem, 2.5vw, 1.625rem)`): Section headers, modal headings.
  * `--type-body-lg` (`1.0625rem`): Prominent body introductions.
  * `--type-body` (`0.9375rem`): Base body copy, description text.
  * `--type-small` (`0.8125rem`): Form labels, secondary meta details, inputs.
  * `--type-micro` (`0.6875rem`): Tiny cards metadata, categories, timestamps.
* **Line Heights**: Display: `1.15`, Title: `1.3`, Body: `1.65`.

### 1.3 Layout & Spacing
* **Base Spatial Grid**: 4px/8px incremental scale:
  * `--space-1` (4px), `--space-2` (8px), `--space-3` (12px), `--space-4` (16px), `--space-5` (20px), `--space-6` (24px), `--space-8` (32px), `--space-10` (40px), `--space-12` (48px), `--space-16` (64px), `--space-20` (80px).
* **Corner Radii Scale**:
  * `--radius-sm` (6px): Mini tags, categories, filter chips.
  * `--radius-md` (10px): Form inputs, action buttons, alert boxes.
  * `--radius-lg` (12px): Standard cards (enforced strictly).
  * `--radius-xl` (16px): Dialog modals, mobile sliding navigation drawer.
  * `--radius-full` (9999px): Pill toggle segment, user initial profile avatars.
* **Elevation Shadows**:
  * Card Shadow (`--shadow-card`): `0 1px 3px rgba(0,0,0,0.06), 0 4px 16px rgba(0,0,0,0.04)`.
  * Raised Shadow (`--shadow-raised`): `0 4px 12px rgba(0,0,0,0.08), 0 12px 40px rgba(0,0,0,0.06)`. Used for sticky banners, overlays, active popups.
  * Modal Shadow (`--shadow-modal`): `0 20px 60px rgba(0,0,0,0.15)`.

---

## 2. Desktop Shell Layout (`>= 1024px`)

### 2.1 Sticky Top Navigation Header Bar (`.navbar`)
* **Height & Backdrop**: Sticky height of `56px`. Blurs under-elements using `backdrop-filter: blur(20px)`.
* **Top Accent Line**: A visual 3px gradient line (`#0D9488` -> `#059669` -> `#0ea5e9` -> `#0F766E`) runs across the absolute top border.
* **Content Placement**:
  * **Left Area**: Brand logo, comprising a green recycling icon and the title "Reuni" (semi-bold, 18px).
  * **Center Area**: Search bar (`.navbar__search`). A centered input field (width: 320px, height: 38px, border-radius: 8px) with a search icon on the left.
  * **Right Area**: Theme toggle button and user profile initials. Tapping the profile circle displays a dropdown menu container containing profile settings and log out links.

### 2.2 Sticky Left Sidebar Navigation (`.sidebar-nav`)
* **Layout**: Stickily anchored layout (`position: sticky; top: 64px; align-self: start; min-height: calc(100vh - 64px)`), width: `240px`.
* **Navigation Links**:
  * Structure: Vertical list of items, each with `height: 40px`, rounded corners (`--radius-md`), displaying an icon and text label.
  * Active state: Styled with `--color-primary-muted` background and `--color-primary` text/icon color.
  * Hover state: Inactive links transition text and icon to `--color-primary` on hover.
  * Role Gating: ESG Dashboard and Admin Panel links are programmatically included for authorized roles.
* **Cumulative Impact Widget**:
  * Positioned at the bottom of the sidebar.
  * Styled as a light-green chip (`--color-success-muted` background) showing an eco leaf icon (`eco`) next to the campus-wide cumulative CO2 offset in monospace (e.g. `245.8 kg saved`).

---

## 3. Mobile Shell Layout (`< 1024px`)

### 3.1 Mobile Top Bar (`.mobile-top-bar`)
* **Structure**: Flex container, height: `56px`, fixed to top.
* **Controls**:
  * Left: Hamburger menu toggle button (`menu` icon) that slides out the navigation drawer.
  * Center: Logo text "Reuni" (18px, bold).
  * Right: Theme toggle icon button. Syncs with system preferences or updates local storage on click, updating the icon from a sun (`light_mode`) to a moon (`dark_mode`).

### 3.2 Sliding Navigation Drawer (`.mobile-drawer`)
* **Appearance**: Slides from left to right (`width: 280px`, `z-index: 1000`), backed by a dark semi-transparent overlay (`.mobile-drawer-backdrop`).
* **Content**: Replicates the sidebar navigation links in a full vertical list (Dashboard, Browse, List, Profile, ESG Dashboard, Admin Panel, Settings, Logout). Close button (`close` icon) in top right.

### 3.3 Bottom Navigation Tab Bar (`.mobile-tabs`)
* **Appearance**: Sticky bar at the bottom (`position: fixed; bottom: 0; left: 0; right: 0; height: 60px`), styled with `--color-surface` and top border line.
* **4-Tab Navigation Layout**:
  1. **Home**: `home` icon with "Home" text label underneath (font size: 10px).
  2. **Search**: `search` icon with "Search" text. Clicking this triggers the full-screen search overlay.
  3. **Sell Button**: Positioned in the middle of the tab bar. Elevated circle button (`width: 48px`, `height: 48px`, background: `--color-primary`) containing a white plus sign (`add`), floating slightly above the bar.
  4. **Profile**: User initials displayed inside a circular border avatar with "Profile" text underneath.
* **Active tab state**: Uses active color highlight (`--color-primary`) for icon and label.

### 3.4 Full-Screen Search Overlay
* **Visuals**: Full screen modal (`position: fixed; inset: 0; background: var(--color-bg)`).
* **Search Input Header**: Top header contains a search input field stretching full width, a search button, and a close icon (`close`).
* **Recent Queries List**: Below the search bar, displays "Recent Searches" label, followed by a list of horizontal, rounded tags representing past query strings.
  * Clicking a tag runs that search immediately.
  * Includes a trash/ghost button to clear search history.

---

## 4. Marketplace Index Page (`index.html`)

### 4.1 Horizontal Category Filter Strip (Mobile view)
* **Visuals**: Edge-to-edge category navigation strip (`.mobile-filters-trigger-strip`) with `overflow-x: auto` and `-webkit-overflow-scrolling: touch` for swipe gesture support.
* **Filter Chips (`.filter-chip`)**:
  * Default: Rounded capsule (`border-radius: var(--radius-full)`), height: `36px`, background: `--color-surface-raised`, text: `--color-ink-secondary`.
  * Active: background: `--color-primary`, text: `#ffffff`.
  * Focus: 3px outer border highlight.
  * Dark mode compatibility: Background defaults to dark slate (`#334155`) with lighter text to maintain readable contrast.

### 4.2 Card Grid & Stagger Animations
* **Grid Layout (`.listings-grid-blueprint`)**:
  * Desktop: Multi-column responsive layout.
  * Mobile: 2-column layout (`grid-template-columns: repeat(auto-fill, minmax(160px, 1fr))`) with compact spacing (`gap: var(--space-3)`).
* **Staggered Animation**: Cards slide up and fade in on page load.
  * CSS Animation: `@keyframes scaleIn { 0% { transform: scale(0.96) translateY(8px); opacity: 0; } 100% { transform: scale(1) translateY(0); opacity: 1; } }`
  * Applied to `.listing-card-blueprint` with stagger offset via dynamic inline variable: `animation: scaleIn 0.3s var(--ease-out) forwards; animation-delay: calc(var(--card-index) * 0.05s)`.

### 4.3 Marketplace Item Cards (`.listing-card-blueprint`)
* **Image**: Top part is the item image with rounded corners (`10px`). Uses a fallback grey box with a picture icon if no image is present.
* **Metadata Overlay/Tags**:
  * Top-Left: Category name displayed in monospace characters inside a white background capsule.
  * Top-Right: Condition tag (e.g. "Like New", "Good") with soft fill styling.
* **Content Details**:
  * Title: Bold text, truncated if exceeding two lines.
  * Carbon Saving Badge: Left-aligned green chip (`--color-success-muted` background) showing a green leaf icon and saving value in monospace (e.g. `1.8 kg saved`).
  * Price: Large orange text on the right (e.g., `£15`), or green text **"Free"** if the item is listed as free.
  * Bottom Meta: Tiny grey text showing post time (e.g., `3h ago`).

---

## 5. Item Details Page (`items/detail.html`)

### 5.1 Responsive Column Grid
* **Desktop**: 2-column layout. Left column holds the large item photo. Right column displays the info panel, including title, category tags, description, carbon offsets, and buttons.
* **Mobile**: Single vertical column. The photo occupies the absolute top, and the detail content spans below it.

### 5.2 Environmental Savings Block
* **Appearance**: Soft teal highlighted banner (`--color-primary-muted` background) displaying an eco icon (`eco`) and saving value in bold monospace (e.g., `5.6 kg`).
* **Source attribution**: Includes the footnote label: *"Based on WRAP UK material weight data"*.

### 5.3 Anti-Griefing Claim CTA Button (State Machine F)
* **States**:
  * **Claimable (Default)**: Bright orange CTA button (`background: var(--color-accent)`) labeled "Claim this item" or "Pay and Claim". Tapping redirects to the PIN Handshake page.
  * **Unavailable (Anti-griefing blocking)**: If a user claims an item, cancels it, and attempts to claim it again, the button is **disabled** (`opacity: 0.4; pointer-events: none; background: var(--color-ink-tertiary); color: var(--color-ink-secondary)`) and displays the warning text **"Unavailable (Previous claim cancelled)"**.
* **Mobile Sticky Button**: On viewport sizes below 1024px, the claim CTA button sticks to the bottom edge of the screen (`position: fixed; bottom: 0; left: 0; right: 0; z-index: 100`) as a full-width block to facilitate one-handed thumb interaction.

---

## 6. PIN Handshake Page (`items/pin.html`)

### 6.1 WhatsApp Seller Coordination Block
* **Access**: Shown only on the buyer's screen.
* **Structure**: Rounded border panel (`--radius-lg`, background: `--color-surface`).
* **WhatsApp Button**: Bright brand green button (`background: #25D366`, white text) showing a `chat` icon and reading "Open WhatsApp". Opens WhatsApp with a prefilled message.
* **Copy Button**: A secondary text link. Clicking copies the prefilled message text to clipboard, updating the label to "Copied ✓" for 1 second.

### 6.2 PIN Code Display Card (Holder Role)
* **digits Wrapper (`.pin-display-wrapper`)**: Flex container (`display: flex; flex-direction: row; flex-wrap: nowrap; justify-content: center; align-items: center; background: var(--color-primary-muted); border-radius: var(--radius-lg); padding: 20px 32px;`).
  * **PIN Digits (`.pin-digit`)**: Large monospace characters (`font-family: var(--font-mono); font-size: 52px; font-weight: 800; color: var(--color-primary);`). Mobile overrides increase font-size to `56px` and font-weight to `900`.
  * **Separators (`.pin-dot`)**: Centered dots (`&middot;`, font-size: `30px`, color: `--color-ink-tertiary`).
  * **Spacing**: Separated using dynamic font-size relative gap values (`gap: 0.25em` desktop, `gap: 0.3em` mobile).
* **Countdown Timer (`#expiry-countdown`)**: Updates in real-time.
  * Default: Grey text.
  * `< 2 Hours`: Amber text (`--color-warning`).
  * `< 30 Minutes`: Red text (`--color-danger`) with a text pulse animation (`warning-pulse`).

### 6.3 PIN Numeric Input Grid (Enterer Role)
* **Inputs**: 4 distinct box inputs (`.otp-input`, size: 56x64px on desktop, 68x72px on mobile) lined horizontally with a gap.
  * Input constraints: `maxlength="1"`, `pattern="[0-9]"`, `inputmode="numeric"`.
  * Interactive behaviors: Advancing focus forward to the next field occurs on typing, and shifts focus backwards on backspace. Typing the fourth digit fires the AJAX validation immediately.
  * Soft Keyboard Handling: Adjusts coordinates using `visualViewport` resize listener to center the inputs and prevent them from being hidden behind the keyboard.

### 6.4 Safe Exchange Guide Accordion
* Accordion element (`details#safe-exchange-details`).
* **Desktop**: Forces accordion to stay expanded. Intercepts click events to prevent collapse.
* **Mobile**: Automatically expands on the user's first visit to this page (using `localStorage.getItem('pin_guide_seen')`). Subsequent visits collapse the accordion by default to preserve screen real estate.

### 6.5 High-Value Advisory Warning
* Triggered when the transaction value is `>= £100`.
* Styled as an warning block with an amber warning icon and dark text: *"For items over £100, we recommend meeting at the SU reception desk..."*

### 6.6 Claim Cancellation Block
* **cancellation Banner (`#cancellation-banner`)**:
  * State A (Within 24h of claiming): Green border box (`background: var(--color-success-muted); border-color: var(--color-success); color: var(--color-success)`) displaying: "Free cancellation — Xh Ym left to cancel without penalty".
  * State B (After 24h of claiming): Amber border box (`background: var(--color-warning-muted); border-color: var(--color-warning); color: var(--color-warning)`) displaying: "Late cancellation — cancelling now will result in a small trust adjustment".
* **Trigger Controls**: Tapping "Cancel this claim" hides the main button and displays inline confirmation elements.
  * **Yes, cancel**: Red button that posts cancellation form to backend.
  * **Never mind**: Ghost button that cancels confirmation and returns to default state.
  * Script is corrected to run for both buyer and seller roles.

---

## 7. listing & Editing Forms (`list_item.html` / `edit_item.html`)

### 7.1 Input Formatting & Counters
* **Title**: Text field constrained to max 80 characters.
* **Description**: Textarea field. The description character limit is set to `2000` (counter shows `X/2000` dynamically).
* **Category**: Dropdown selector. Shows live environmental preview on selection (e.g. "Selecting 'Electronics' = ~12.0 kg CO2e prevented").
* **Condition Segmented Buttons**:
  * Raw `<select id="condition">` is hidden but kept focusable (`position: absolute; opacity: 0; width: 1px; height: 1px; pointer-events: none`).
  * Custom buttons: Horizontal list container (`.condition-btns-container`). Tapping a button assigns its value to the hidden select and highlights the active button in brand teal (`--color-primary`, white text).
* **Price Segmented Toggle**:
  * Raw checkbox is hidden. Toggle buttons select "Free" or "Set Price".
  * Selecting "Set Price" dynamically slides open a numerical price input box with prefix symbol.
* **Photo Upload**:
  * Raw `<input type="file">` is hidden but focusable.
  * Custom zone: Drag-and-drop zone (`#photo-upload-zone`). Shows preview image once file selected, along with a "Remove" button.

### 7.2 custom client-side validation
* Validates title, category selection, condition selection, price, and photo on submission.
* **Error States**: If validation fails:
  * Prevents default form submit event (prevents buttons from locking into "Listing..." disabled states).
  * Highlights failing fields with red border (`var(--color-danger)`).
  * Appends a descriptive error label (`.custom-error-msg` in red) under the invalid inputs.
  * Automatically performs smooth scroll directly to the first invalid field.

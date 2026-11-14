# Perplexity AI — Style Reference
> Warm research terminal. A cream-toned search bar floats on aged-paper canvas, surrounded by quiet monochrome controls — the calm of a library reading desk distilled into a single input field.

**Theme:** light  
**Application Target:** Simple AI Agent (Full-Stack Monorepo — Angular 22 & FastAPI)

Source measurements are normalized; roles and recommendations are interpreted. Font summary lists are independent, not paired by position. HTML examples are reconstructions, not source components.

Perplexity's interface operates like a quiet research terminal: a warm off-white canvas (`#faf8f5`) that reads more like aged paper than sterile app-white, a single monochrome typographic voice, and one restrained teal accent (`#016a71`) that appears only as functional punctuation. The entire visual system compresses to a search bar as the hero — every surrounding control (sidebar, top nav, model selector, voice button) is a subordinate satellite. Density is compact but not cramped: 8px is the workhorse gap, 12–16px the padding standard, with 9999px pill rounding on all interactive controls. There is almost no elevation — the design is deliberately flat, using a barely-there 1px border at `#d1d1cd` and a single whisper-soft shadow to separate the card layer from the canvas. Typography is custom (pplxSans) at exactly two weights (400, 500) and three sizes (12, 14, 16) — the scale is intentionally narrow, making the interface feel like a document rather than a dashboard.

---

## Tokens — Colors

| Name | Value | Token | Role |
|------|-------|-------|------|
| Aged Paper | `#faf8f5` | `--color-aged-paper` | Page canvas and card surfaces — warm off-white replaces sterile pure white, giving the interface a document-like, paper-textured quality |
| Ink Black | `#000000` | `--color-ink-black` | Primary text, icon strokes, and the dominant fill across navigation and body copy |
| Charcoal | `#27251e` | `--color-charcoal` | Primary action button background and high-emphasis text — warm near-black that pairs with the cream canvas for a softer than pure-black contrast |
| Ash Gray | `#72706b` | `--color-ash-gray` | Secondary text, muted icons, and inactive nav fills — carries the warm tint of the palette |
| Stone | `#92918b` | `--color-stone` | Tertiary/placeholder text and low-emphasis labels |
| Pebble | `#d1d1cd` | `--color-pebble` | Hairline borders on cards and input containers — warm gray that recedes against the cream canvas |
| Deep Teal | `#016a71` | `--color-deep-teal` | Sole chromatic accent — active nav indicator and selected state fill, provides the only color punctuation in the interface |
| Pure White | `#ffffff` | `--color-surface-card` | Surface fill for elevated input boxes, tool cards, and modal dialogs |
| Subtle Fill | `#e8e6e1` | `--color-subtle-fill` | Active sidebar nav item background, subtle hover states |
| Shimmer Fill | `#f0eeea` | `--color-shimmer-fill` | Skeleton placeholder loading bars and pulse backgrounds |

---

## Tokens — Typography

### pplxSans — All interface text — the deliberately narrow scale (3 sizes, 2 weights) makes the system feel document-like. Weight 400 handles body, labels, and input text; weight 500 is reserved for active/selected states and emphasis. The custom typeface is geometric and humanist, tighter and more distinctive than a system sans like Inter. Normal letter-spacing throughout. · `--font-pplxsans`
- **Substitute:** Inter (system fallback) — closest in geometric proportions; alternatively DM Sans for similar warmth
- **Weights:** 400, 500
- **Sizes:** 12px, 14px, 16px
- **Line height:** 1.25, 1.33, 1.43, 1.50, 2.00
- **Role:** All interface text — the deliberately narrow scale (3 sizes, 2 weights) makes the system feel document-like. Weight 400 handles body, labels, and input text; weight 500 is reserved for active/selected states and emphasis. The custom typeface is geometric and humanist, tighter and more distinctive than a system sans like Inter. Normal letter-spacing throughout.

### Type Scale

| Role | Family | Weight | Size | Line Height | Letter Spacing | Token |
|------|--------|--------|------|-------------|----------------|-------|
| caption | pplxSans, Inter, sans-serif | 400 / 500 | 12px | 1.43 | normal | `--text-caption` |
| body-sm | pplxSans, Inter, sans-serif | 400 / 500 | 14px | 1.43 | normal | `--text-body-sm` |
| body | pplxSans, Inter, sans-serif | 400 / 500 | 16px | 1.43 | normal | `--text-body` |

---

## Tokens — Spacing & Shapes

**Base unit:** 8px  
**Density:** compact

### Spacing Scale

| Name | Value | Token | Tailwind Utility |
|------|-------|-------|------------------|
| 4 | 4px | `--spacing-4` | `gap-1`, `p-1`, `m-1` |
| 8 | 8px | `--spacing-8` | `gap-2`, `p-2`, `m-2` |
| 10 | 10px | `--spacing-10` | `gap-2.5`, `p-2.5` |
| 12 | 12px | `--spacing-12` | `gap-3`, `p-3`, `m-3` |
| 16 | 16px | `--spacing-16` | `gap-4`, `p-4`, `m-4` |
| 32 | 32px | `--spacing-32` | `gap-8`, `p-8`, `m-8` |

### Border Radius

| Element | Value | Token | Tailwind Utility |
|---------|-------|-------|------------------|
| tags | 9999px | `--radius-tags` | `rounded-full` |
| cards | 16px | `--radius-cards` | `rounded-2xl` |
| input | 12px | `--radius-input` | `rounded-xl` |
| buttons | 9999px | `--radius-buttons` | `rounded-full` |
| nav-items | 9999px | `--radius-nav-items` | `rounded-full` |
| chips | 6px | `--radius-chips` | `rounded-md` |

### Shadows

| Name | Value | Token |
|------|-------|-------|
| subtle | `rgba(0, 0, 0, 0.08) 0px 1px 2px 0px` | `--shadow-subtle` |

### Layout

- **Page max-width:** 640px (centered research column)
- **Section gap:** 32px
- **Card padding:** 12px
- **Element gap:** 8px
- **Sidebar width:** 220px
- **Header height:** 56px

---

## Components

### 1. Search & Prompt Input
**Role:** Central input field — the primary action surface of the product.  
- **Container:** Full-width within 640px max-width container. Pure white (`#ffffff`) background with 1px hairline border in `#d1d1cd`, 12px border-radius (`rounded-xl`).
- **Input Text:** 16px pplxSans weight 400 placeholder text in `#92918b`. 16px vertical padding.
- **Satellite Controls:** Inline '+' icon (`#27251e`), capability mode toggle chip (`#faf8f5` pill), AI Model Selector dropdown, optional microphone/attachment icon, and dark circular submit button (`#27251e`, 9999px radius, white up-arrow icon).

### 2. Primary Submit Button
**Role:** Prompt submission — the only filled dark button in the interface.  
- **Dimensions:** 28×28px circle.
- **Style:** `#27251e` background, 9999px radius (`rounded-full`), white (`#ffffff`) up-arrow icon at 14px.
- **Positioning:** Sits inline at the right edge of the prompt container.

### 3. Sidebar Nav Item (Sessions & Navigation)
**Role:** Left rail navigation links and chat session history items.  
- **Dimensions:** 36px height, 8px horizontal padding, 9999px radius (`rounded-full`).
- **Typography:** pplxSans 14px weight 400 in `#27251e`.
- **Active State:** `#e8e6e1` background fill with weight 500 label.
- **Leading Icon:** 16px in `#27251e` or `#72706b`.
- **Session Thread Truncation:** Single-line text overflow ellipsis, full-width within 220px left rail.

### 4. Top Nav Link / Header Bar
**Role:** Horizontal navigation and capability tabs in the header.  
- **Typography:** Inline 14px pplxSans weight 400 in `#27251e`.
- **States:** No background by default. Active/category indicator uses `#016a71` Deep Teal fill as an underline bar (2px height, 8px width) or pill background.

### 5. Mode Toggle Chip (Tools & Capabilities)
**Role:** Inline capability selector within the search input (e.g., Web Search, Calculator, Code Execution).  
- **Style:** Compact pill with 6px radius (`rounded-md`), 4px vertical / 8px horizontal padding.
- **Colors:** `#faf8f5` background, 12px pplxSans weight 500 label in `#27251e`.
- **Prefix & Suffix:** Leading capability icon, trailing '+' icon for adding tools.

### 6. Status Card & Human-in-the-Loop Tool Approval Card
**Role:** System notifications, agent execution status, and tool call approval requests.  
- **Container:** Full-width 640px, pure white (`#ffffff`) background, 16px radius (`rounded-2xl`), 1px `#d1d1cd` border, 12px padding, subtle shadow (`rgba(0, 0, 0, 0.08) 0px 1px 2px 0px`).
- **Header:** 14px pplxSans weight 500 label in `#27251e` with status icon.
- **Action Buttons:** Compact pill buttons (9999px radius) for **Approve & Run** (`#27251e` fill, white text) and **Reject** (1px `#d1d1cd` border, `#72706b` text).
- **Tool Body:** 12px monospace argument preview inside `#faf8f5` inner container with 1px `#d1d1cd` border.

### 7. Skeleton Placeholder & Streaming Indicator
**Role:** Loading state for content cards, token stream buffering, and session lists.  
- **Style:** Rounded 9999px bar, 8px height, `#f0eeea` fill.
- **Animation:** Subtle linear shimmer pulse.
- **Arrangement:** Arranged in rows with 8px gap.

### 8. Sign In / Profile Button
**Role:** Authentication entry at sidebar bottom and user profile status.  
- **Dimensions:** 28px height, 8px horizontal / 12px vertical padding, 9999px radius (`rounded-full`).
- **Typography:** pplxSans 14px weight 500 in `#27251e`.
- **Prefix:** Circular avatar or user outline icon.

### 9. Model Selector
**Role:** Dropdown trigger for AI provider/model selection (e.g. Gemini 2.5 Flash, Ollama Llama 3).  
- **Style:** Inline text button, 14px pplxSans weight 400 in `#27251e`.
- **Adornment:** Trailing chevron-down icon at 12px. No border or background. Active selection indicated in `#016a71`.

### 10. Code Block & Markdown Streaming Surface
**Role:** Rendering agent reasoning, markdown documents, and syntax-highlighted code.  
- **Typography:** pplxSans 14px/16px for prose; JetBrains Mono / SFMono for code snippets.
- **Code Container:** `#ffffff` surface or subtle `#27251e` dark terminal card, 1px `#d1d1cd` border, 12px radius (`rounded-xl`).
- **Copy Button:** Compact pill (`rounded-full`, 12px text, 1px `#d1d1cd` border) with subtle `#e8e6e1` hover.

---

## Do's and Don'ts

### Do
- Use 9999px border-radius (`rounded-full`) for all interactive controls (buttons, nav items, toggle chips, tags).
- Maintain the narrow type scale: 12px caption, 14px body-sm, 16px body — do not introduce sizes outside this set.
- Set all card and input backgrounds to `#ffffff` on the `#faf8f5` canvas to create the paper-on-paper layering effect.
- Use 1px `#d1d1cd` borders for all container separation — avoid shadows except the single whisper-soft card shadow.
- Use `#016a71` Deep Teal only for active/selected state indicators — it should appear on fewer than 5% of elements.
- Keep the main content column at 640px max-width centered — the search/chat input is the focal point, not an unbounded canvas.
- Use pplxSans weight 500 exclusively for emphasis and active states; weight 400 for all default and body text.
- Left-align all message copy, descriptions, and input text.

### Don't
- Do not introduce new colors — the palette is deliberately minimal: cream, black, warm grays, and one teal.
- Do not use bold weights (600+) — the system maxes strictly at weight 500.
- Do not use 0px or 4px border-radius on interactive elements — always pill (9999px) or 12px minimum.
- Do not apply heavy shadows or multiple shadow layers — the design is intentionally flat.
- Do not use pure white (`#ffffff`) as a page background — the warm `#faf8f5` canvas is a signature choice.
- Do not center-align body text — left-align all labels, descriptions, and input text.
- Do not use the teal accent decoratively — it signals a functional state (active, selected, live).

---

## Surfaces

| Level | Name | Value | Purpose |
|-------|------|-------|---------|
| 0 | Canvas | `#faf8f5` | Page background — warm off-white that reads as paper or aged cream |
| 1 | Card | `#ffffff` | Elevated container surfaces — input fields, status cards, tool approval blocks |
| 2 | Subtle Fill | `#e8e6e1` | Active nav item backgrounds, hover states — a barely-visible warm gray |

---

## Elevation

- **Status Card / Tool Card:** `rgba(0, 0, 0, 0.08) 0px 1px 2px 0px`
- **Canvas & Default Elements:** Flat (0px elevation, 1px `#d1d1cd` hairline border).

---

## Imagery

No photography, illustration, or decorative graphics. The visual language is pure UI — typography, whitespace, and a single teal accent do all the work. Icons are minimal line-style at 16–20px, rendered in `#27251e` or `#72706b`. The brand wordmark 'simple-agent' or 'perplexity' is the only typographic identity element. There are no product screenshots, hero images, or marketing visuals on the primary search interface.

---

## Layout

Centered single-column layout at 640px max-width. Left sidebar (220px) contains primary navigation (New Chat, Tools, Spaces, History) with a Sign In / Profile button pinned at the bottom. Top header bar (56px) holds category links or model status right-aligned. The main content area is dominated by the centered wordmark and the query input — the hero is literally a search/chat bar, not a visual. Below the input, status cards, active tool approvals, and skeleton placeholders extend the column. The layout is deliberately minimal: no multi-column grids, no hero imagery, no card carousels on the primary screen. Navigation is a compact sidebar + thin top bar. Section rhythm is defined by generous vertical breathing room (32px+) rather than visual dividers.

---

## Agent Prompt Guide

### Quick Color Reference
- **canvas:** `#faf8f5`
- **card/surface:** `#ffffff`
- **text primary:** `#000000`
- **text secondary:** `#72706b`
- **text placeholder:** `#92918b`
- **border:** `#d1d1cd`
- **active fill:** `#e8e6e1`
- **accent (selected/active only):** `#016a71`
- **primary action:** `#27251e`

### Example Component Prompts

1. **Search Input with Submit**: Create a 640px-wide search bar on `#faf8f5` canvas. Input: white (`#ffffff`) background, 1px `#d1d1cd` border, 12px radius, 16px padding. Placeholder 'Ask anything…' in 16px pplxSans weight 400, `#92918b`. Inside: a '+' icon (`#27251e`), a mode chip ('Computer') with `#faf8f5` background, 6px radius, 12px pplxSans weight 500, and a dark submit circle (28px, `#27251e` fill, 9999px radius, white arrow icon).
2. **Sidebar Nav Item**: 36px tall, 8px horizontal padding, 9999px radius. 14px pplxSans weight 400, `#27251e` text. 16px leading icon in `#27251e`. Active state: `#e8e6e1` background fill. Full width within a 220px left sidebar with `#faf8f5` background.
3. **Status / Tool Approval Notification Card**: 640px wide, white (`#ffffff`) background, 16px radius, 1px `#d1d1cd` border, 12px padding, subtle shadow (`rgba(0,0,0,0.08) 0px 1px 2px`). 14px pplxSans weight 500 label in `#27251e` with a 12px status icon. Below: 3-4 skeleton bars (9999px radius, `#f0eeea` fill, 8px height) with 8px gap.
4. **Teal Active Nav Indicator**: Horizontal 14px pplxSans weight 500 text in `#27251e` with a `#016a71` teal underline bar (2px height, 8px width) or teal pill background. This is the only place teal should appear in the interface.
5. **Top Header Category Link**: Inline 14px pplxSans weight 400, `#27251e`, no background. Spacing: 16px gap between links, right-aligned in a 56px-tall header bar on `#faf8f5` background.

---

## Similar Brands

- **Notion AI** — Same warm off-white canvas, monochrome text system, and single accent color approach — both feel like documents rather than dashboards
- **Phind** — Developer-focused search interface with centered input hero, minimal chrome, and teal/dark dual-tone palette
- **You.com** — Search-first AI interface with compact sidebar nav, centered query input as the page hero, and restrained accent usage
- **Linear** — Same flat elevation philosophy, hairline borders instead of shadows, narrow type scale, and pill-shaped interactive controls

---

## Quick Start

### CSS Custom Properties

```css
:root {
  /* Colors */
  --color-aged-paper: #faf8f5;
  --color-ink-black: #000000;
  --color-charcoal: #27251e;
  --color-ash-gray: #72706b;
  --color-stone: #92918b;
  --color-pebble: #d1d1cd;
  --color-deep-teal: #016a71;

  /* Typography — Font Families */
  --font-pplxsans: 'pplxSans', Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;

  /* Typography — Scale */
  --text-caption: 12px;
  --leading-caption: 1.43;
  --text-body-sm: 14px;
  --leading-body-sm: 1.43;
  --text-body: 16px;
  --leading-body: 1.43;

  /* Typography — Weights */
  --font-weight-regular: 400;
  --font-weight-medium: 500;

  /* Spacing */
  --spacing-unit: 8px;
  --spacing-4: 4px;
  --spacing-8: 8px;
  --spacing-10: 10px;
  --spacing-12: 12px;
  --spacing-16: 16px;
  --spacing-32: 32px;

  /* Layout */
  --page-max-width: 640px;
  --section-gap: 32px;
  --card-padding: 12px;
  --element-gap: 8px;

  /* Border Radius */
  --radius-md: 6px;
  --radius-xl: 12px;
  --radius-2xl: 16px;
  --radius-full: 9999px;

  /* Named Radii */
  --radius-tags: 9999px;
  --radius-cards: 16px;
  --radius-input: 12px;
  --radius-buttons: 9999px;
  --radius-nav-items: 9999px;

  /* Shadows */
  --shadow-subtle: rgba(0, 0, 0, 0.08) 0px 1px 2px 0px;

  /* Surfaces */
  --surface-canvas: #faf8f5;
  --surface-card: #ffffff;
  --surface-subtle-fill: #e8e6e1;
}
```

### Tailwind v4 `@theme` Configuration

```css
@theme {
  /* Colors */
  --color-aged-paper: #faf8f5;
  --color-ink-black: #000000;
  --color-charcoal: #27251e;
  --color-ash-gray: #72706b;
  --color-stone: #92918b;
  --color-pebble: #d1d1cd;
  --color-deep-teal: #016a71;

  /* Surfaces */
  --color-canvas: #faf8f5;
  --color-card: #ffffff;
  --color-subtle-fill: #e8e6e1;
  --color-shimmer: #f0eeea;

  /* Typography */
  --font-pplxsans: 'pplxSans', Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;

  /* Typography — Scale */
  --text-caption: 12px;
  --leading-caption: 1.43;
  --text-body-sm: 14px;
  --leading-body-sm: 1.43;
  --text-body: 16px;
  --leading-body: 1.43;

  /* Spacing */
  --spacing-4: 4px;
  --spacing-8: 8px;
  --spacing-10: 10px;
  --spacing-12: 12px;
  --spacing-16: 16px;
  --spacing-32: 32px;

  /* Border Radius */
  --radius-md: 6px;
  --radius-xl: 12px;
  --radius-2xl: 16px;
  --radius-full: 9999px;

  /* Shadows */
  --shadow-subtle: rgba(0, 0, 0, 0.08) 0px 1px 2px 0px;
}
```

---

## Tailwind CSS Project Implementation Guide

### 1. App Root & Canvas
```html
<div class="h-screen w-screen overflow-hidden bg-[#faf8f5] text-[#000000] font-['pplxSans',Inter,sans-serif] flex">
  <!-- Sidebar Navigation: 220px width -->
  <aside class="w-[220px] h-full bg-[#faf8f5] border-r border-[#d1d1cd] p-3 flex flex-col justify-between shrink-0">
    ...
  </aside>

  <!-- Main Research Terminal Content Area -->
  <main class="flex-1 h-full flex flex-col items-center justify-between p-4 overflow-y-auto">
    <header class="w-full max-w-[640px] h-14 flex items-center justify-between">
      <span class="text-sm font-medium text-[#27251e] tracking-tight">Simple AI Agent</span>
      <div class="flex items-center gap-4 text-sm text-[#72706b]">
        <button class="hover:text-[#27251e] text-[#016a71] font-medium border-b-2 border-[#016a71] pb-0.5">Chat</button>
        <button class="hover:text-[#27251e] transition-colors">Tools</button>
      </div>
    </header>

    <!-- Message Stream Viewport: Centered 640px -->
    <div class="w-full max-w-[640px] flex-1 flex flex-col gap-4 py-8 overflow-y-auto">
      ...
    </div>

    <!-- Centered Query Box Hero: Max Width 640px -->
    <div class="w-full max-w-[640px] bg-white border border-[#d1d1cd] rounded-xl p-3 shadow-[0_1px_2px_rgba(0,0,0,0.08)] flex flex-col gap-2">
      <textarea
        placeholder="Ask anything..."
        class="w-full resize-none border-none bg-transparent text-base text-[#000000] placeholder-[#92918b] focus:outline-none"
      ></textarea>
      
      <div class="flex items-center justify-between pt-1">
        <!-- Capability Chips -->
        <div class="flex items-center gap-2">
          <span class="px-2 py-1 bg-[#faf8f5] text-[#27251e] text-xs font-medium rounded-md flex items-center gap-1 border border-[#d1d1cd]">
            <span>⚡</span> Search & Tools
          </span>
          <span class="text-xs text-[#72706b] hover:text-[#27251e] cursor-pointer">Gemini 2.5 Flash ▾</span>
        </div>

        <!-- Submit Button Circle -->
        <button class="w-7 h-7 rounded-full bg-[#27251e] text-white flex items-center justify-center hover:opacity-90 transition-opacity">
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 10l7-7m0 0l7 7m-7-7v18"/>
          </svg>
        </button>
      </div>
    </div>
  </main>
</div>
```

### 2. Sidebar Nav Items & Session History
```html
<div class="flex flex-col gap-1 w-full">
  <!-- New Chat Pill Button -->
  <button class="h-9 px-3 w-full rounded-full bg-[#27251e] text-white text-sm font-medium flex items-center gap-2 hover:opacity-95 transition-opacity">
    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
    <span>New Thread</span>
  </button>

  <!-- Session List -->
  <nav class="flex flex-col gap-0.5 mt-4">
    <a href="#" class="h-9 px-3 rounded-full bg-[#e8e6e1] text-[#27251e] text-sm font-medium flex items-center justify-between">
      <span class="truncate">Financial Search Analysis</span>
    </a>
    <a href="#" class="h-9 px-3 rounded-full hover:bg-[#e8e6e1]/60 text-[#72706b] hover:text-[#27251e] text-sm flex items-center justify-between transition-colors">
      <span class="truncate">Redis Caching Architecture</span>
    </a>
  </nav>
</div>
```

### 3. Human-in-the-Loop Tool Approval Card
```html
<div class="w-full max-w-[640px] bg-white border border-[#d1d1cd] rounded-2xl p-3 shadow-[0_1px_2px_rgba(0,0,0,0.08)] flex flex-col gap-2">
  <div class="flex items-center justify-between">
    <div class="flex items-center gap-2">
      <span class="w-2 h-2 rounded-full bg-[#016a71]"></span>
      <span class="text-sm font-medium text-[#27251e]">Tool Approval Required: search_web</span>
    </div>
    <span class="text-xs text-[#72706b]">Tavily Engine</span>
  </div>

  <div class="bg-[#faf8f5] border border-[#d1d1cd] rounded-md p-2 text-xs font-mono text-[#27251e]">
    {"query": "Latest Nvidia earnings report 2026"}
  </div>

  <div class="flex items-center justify-end gap-2 pt-1">
    <button class="h-7 px-3 rounded-full border border-[#d1d1cd] text-xs text-[#72706b] hover:bg-[#e8e6e1] transition-colors">
      Reject
    </button>
    <button class="h-7 px-3 rounded-full bg-[#27251e] text-xs font-medium text-white hover:opacity-90 transition-opacity">
      Approve & Run
    </button>
  </div>
</div>
```

# UI Style Guide

## 1. Purpose

This file defines the shared visual language for the Energy Consumption Reporting Tool.

It exists to prevent mixed styles across the same screen or report.
All future UI updates must follow this guide unless the user explicitly requests an exception.

This guide applies to:
- HTML report view
- PDF report layout
- section partial templates
- reusable UI blocks
- future dashboard-style extensions

---

## 2. Core Design Goals

The UI must feel:
- professional
- consistent
- data-dense
- readable
- modern but restrained
- suitable for engineering and management review

The visual direction is:
- enterprise reporting
- clean card-based layout
- soft modern spacing
- low-noise styling
- clear emphasis on numbers and comparison

Avoid:
- flashy gradients
- overly rounded consumer-style UI
- heavy shadows
- excessive animation
- decorative elements without business meaning

---

## 3. Design Principles

### 3.1 Consistency First
All components of the same type must share the same style.

Examples:
- all area summary cards must use one card style and highlight total/plant card
- all section titles must use one heading style
- all data tables must use one table system
- all KPI emphasis values must use one number style

Do not introduce a new visual style for the same object type inside the same screen.

### 3.2 Business First
The UI is a reporting surface, not a marketing page.

Priority order:
1. clarity
2. comparability
3. density
4. aesthetics

### 3.3 Structure Before Decoration
Use spacing, grouping, borders, and typography before adding color.

### 3.4 Explicit State
Missing, partial, warning, and complete states must be visually distinguishable.

### 3.5 Reuse Before Inventing
Before creating a new component style, reuse one of the existing patterns in this document.

---

## 4. Global Visual Language

### 4.1 Color Philosophy
Use a restrained neutral base with a few semantic accent colors.

#### Neutral Base
- Page background: very light neutral
- Card background: white
- Primary text: near-black / dark slate
- Secondary text: muted gray
- Border: light gray
- Table stripe: subtle neutral tint

#### Semantic Colors
Use color only for meaning:
- positive / improved: green family
- negative / worsened: red family
- warning / partial / coverage issue: amber family
- informational / emphasis / section identity: blue family

Do not use many unrelated accent colors in the same page.

### 4.2 Color Usage Rules
- section titles may use a single controlled accent
- cards should remain mostly neutral
- numeric deltas may use semantic color only when meaningful
- large background fills should remain subtle
- avoid saturated full-card backgrounds except for rare highlight cases

### 4.3 Typography
Typography must be calm and functional.

#### Hierarchy
- Page title: strong and clear
- Section title: medium-large and bold
- Card title: medium weight
- Label text: smaller, muted
- Primary value: large and bold
- Table body: compact and highly readable
- Notes / metadata: small and muted

#### Typography Rules
- avoid more than 3 visual text levels inside one component
- do not mix many font weights in one row
- emphasize numbers more than labels
- keep units smaller and less visually dominant than the value

### 4.4 Radius and Shape
- cards: soft radius, not overly round
- buttons: medium radius
- table container: soft radius if wrapped in card
- charts: no decorative framing beyond the shared card container

### 4.5 Shadow and Border
- prefer light borders over strong shadows
- use subtle shadow only to separate cards from page background
- do not stack multiple shadow systems in one layout

---

## 5. Layout System

### 5.1 Page Layout
Use a clean vertical flow:
1. page header
2. section blocks
3. subsection blocks
4. detail tables / charts
5. notes / footer

### 5.2 Spacing Scale
Use a consistent spacing rhythm.
Recommended mental scale:
- extra small: tight inner spacing for labels and chips
- small: table cell / inline spacing
- medium: card padding and block gaps
- large: gap between major sections
- extra large: page-level separation only

Do not mix random spacing values.
Use repeated spacing tokens or repeated CSS values.

### 5.3 Grid Behavior
For responsive view:
- summary cards should align to a predictable grid
- avoid uneven card heights when possible
- related blocks should stay visually grouped

For PDF:
- prioritize stable stacking over aggressive multi-column layouts
- avoid overly complex responsive behavior

---

## 6. Section Style Rules

## 6.1 Header Section
The report header should look structured and executive.

Should include:
- report title
- workshop / scope info
- reporting period
- generation timestamp
- optional compact summary strip

Style rules:
- strong title, muted metadata
- no oversized decorative banner
- summary strip should be compact and aligned
- keep header visually clean and balanced

## 6.2 Section Container
Each main section must use the same section pattern:
- section heading
- optional subtitle / note
- summary area first
- comparison next
- detail tables / charts after that

Section heading style must be consistent across:
- Electricity
- Utility
- KPI

## 6.3 Subsection Blocks
Subsections should not visually overpower section headers.
Use:
- smaller title
- optional divider or spacing separation
- shared card/table styling

---

## 7. Card System

### 7.1 Shared Card Pattern
All metric cards must use one shared style family.

Card structure:
- title / label
- primary value
- optional unit
- optional secondary values
- optional delta / comparison row
- optional note / coverage badge

### 7.2 Card Types
#### A. Summary Card
Used for plant totals, official totals, top-level KPIs.

Visual behavior:
- clean neutral background
- large value
- compact label
- optional semantic delta

#### B. Comparison Card
Used when current vs previous is central.

Should show:
- current
- previous
- delta
- delta %

Do not make comparison cards visually louder than primary summary cards.

#### C. Status Card
Used for notes like coverage, missing data, warnings.

Use semantic accent lightly.
Do not turn every note into a colorful banner.

### 7.3 Card Rules
- same padding for all cards in the same page
- same title position
- same value alignment logic
- same unit style
- same delta badge style

### 7.4 Numeric Emphasis
Primary numbers should be the visual focus.

Rules:
- value first
- label second
- unit third
- supporting comparison below or beside depending on width

---

## 8. KPI-Specific UI Rules

### 8.1 KPI Priority
KPI must feel important but not visually disconnected from other sections.

### 8.2 KPI Presentation
Preferred pattern:
- primary KPI total card
- compact comparison cards by area
- clear production context nearby
- dense daily detail table below

### 8.3 KPI State Display
Coverage is critical and must be visible.

Visual states:
- complete: calm success treatment
- partial: warning treatment
- missing: muted or warning-neutral treatment

Coverage note must never compete visually with the KPI value itself.

### 8.4 KPI Numbers
- KPI value should be large
- unit `kWh/Ton` should be smaller
- plant total should be visually stronger than area values
- delta and delta % should be compact and aligned consistently

---

## 9. Table System

### 9.1 Shared Table Style
All tables must follow one common table system.

Use:
- consistent header background
- consistent border style
- dense readable rows
- right alignment for numeric values
- left alignment for labels and names
- centered alignment only for short status indicators when appropriate

### 9.2 Header Style
Table headers should be:
- clear
- compact
- slightly emphasized
- not too dark or visually heavy

### 9.3 Row Rules
- use subtle zebra striping only if it improves readability
- hover effect for HTML view may be subtle
- PDF must not rely on hover
- avoid excessive row separators

### 9.4 Cell Content Rules
- numbers: right aligned
- status: badge or short semantic text
- missing values: display `-`
- units: do not repeat excessively if already defined by column header

### 9.5 Table Density
This project is data-dense.
Tables should be compact but not cramped.

Avoid:
- oversized row height
- excessive padding
- giant headers

### 9.6 Wide Tables
For HTML view:
- use horizontal scroll wrappers when necessary
- preserve column readability

For PDF:
- prefer print-safe sizing
- avoid layout breakage
- prioritize completeness and legibility

---

## 10. Utility Section Rules

### 10.1 Utility Summary
Utility summary should visually align with electricity and KPI styles.
Do not invent a separate visual language.

### 10.2 Sensor Monitoring
Sensor monitoring belongs inside Utility and must look like a related subsection.

Preferred structure:
- subsection title
- compact note if needed
- daily table
- future chart blocks in the same visual system

### 10.3 Avg / Max Presentation
Average and maximum values should be clearly distinguished but still belong to the same table family.

Use:
- column grouping
- consistent muted subheaders
- not separate competing color systems

---

## 11. Chart Style Rules

### 11.1 Shared Chart Behavior
Charts must look like part of the same report system.

Use:
- chart inside shared card container
- consistent title style
- consistent legend placement logic
- clean gridlines
- restrained axis styling

### 11.2 Chart Color Rules
- use limited semantic palette
- keep series count visually manageable
- do not use random colors per chart
- the same metric should prefer the same color family across related charts

### 11.3 Chart Density
Charts should support reading, not decoration.

Avoid:
- 3D effects
- heavy shadows
- glossy visual styles
- unnecessary animation

### 11.4 PDF Rules
For PDF mode:
- prioritize stability
- disable or minimize animation when needed
- prefer sizing consistency over flashy behavior
- charts must remain readable in A4 output

---

## 12. Status and Semantic UI

### 12.1 Positive / Negative
Use semantic colors consistently:
- positive delta / improved metric
- negative delta / worsened metric

The interpretation of positive vs negative must match business meaning.
For metrics where lower is better, do not blindly color positive deltas as good.

### 12.2 Missing Data
Missing values must be visible but not overly alarming.
Use:
- `-`
- muted tone
- optional note if important

### 12.3 Partial Coverage
Partial coverage must be more visible than missing numeric data but less aggressive than an error state.

### 12.4 Error / Warning Notes
Reserve stronger visual emphasis only for important warnings.
Do not style every note as an alert banner.

---

## 13. HTML View vs PDF Rules

### 13.1 Shared Rule
Both view and PDF should look like the same product.
They may differ in layout constraints, but not in design identity.

### 13.2 HTML View
Can include:
- hover states
- responsive card layout
- interactive chart behavior

But must remain consistent with the PDF visual language.

### 13.3 PDF View
Must prioritize:
- print safety
- stable spacing
- clean table breaks
- consistent chart sizing

Do not introduce a separate visual style just because it is PDF.

---

## 14. Reusable Component Patterns

The following reusable patterns should be preferred.

### 14.1 Metric Card Pattern
Used for:
- plant total
- area total
- KPI total
- production total

### 14.2 Comparison Strip Pattern
Used for:
- current vs previous
- delta
- delta %

### 14.3 Dense Data Table Pattern
Used for:
- daily detail
- utility detail
- KPI detail
- sensor monitoring

### 14.4 Section Note Pattern
Used for:
- coverage notes
- assumptions
- missing-data remarks

### 14.5 Chart Card Pattern
Used for:
- line chart
- bar chart
- future utility charts

All of the above patterns must reuse the same spacing, border, and typography logic.

---

## 15. Do / Do Not Rules

### 15.1 Do
- keep one shared card system
- keep one shared table system
- keep one heading hierarchy
- keep semantic color usage disciplined
- keep PDF and HTML visually aligned
- prefer reuse over invention

### 15.2 Do Not
- do not mix multiple button/card/table styles in one report
- do not use different border radius values randomly
- do not use multiple unrelated shadows
- do not introduce new accent colors casually
- do not create a special style for one object unless business meaning requires it
- do not let templates drift apart visually over time

---

## 16. Implementation Guidance for AI / OpenClaw

When changing UI, always follow this order:
1. reuse an existing component style
2. apply this guide consistently across the touched files
3. avoid local one-off styling
4. explain any exception before implementing

When asked to modify a UI block, OpenClaw should:
- check whether the same object type already exists elsewhere
- match the existing shared style
- avoid introducing a second visual language
- keep CSS reusable and centralized where possible

If a request is ambiguous, prefer:
- consistency with this style guide
- minimal visual change
- reuse of existing structure

---

## 17. Suggested CSS Token Direction

The implementation may define reusable CSS variables or equivalent tokens for:
- page background
- card background
- primary text
- secondary text
- border color
- success color
- danger color
- warning color
- info/accent color
- radius size
- shadow level
- spacing scale

Do not hardcode random colors throughout templates.
Centralize tokens whenever practical.

---

## 18. Future Extension Rule

If a new section or widget is added later, it must inherit from this style system.

New UI work must answer:
- which existing component pattern does it match?
- which shared style does it reuse?
- does it preserve report-wide consistency?

If not, redesign before implementation.

---

## 19. Short Instruction Snippet

Use this when prompting AI:

"Follow `docs/ui_style.md` strictly. Reuse the existing shared card, table, spacing, heading, and semantic color system. Do not introduce a new visual style for the same object type. Keep HTML view and PDF visually aligned."

---

## 20. Project-Specific Priority

For this project, the most important consistency targets are:
1. summary cards
2. comparison rows
3. KPI cards
4. dense tables
5. sensor monitoring tables
6. chart containers
7. section heading hierarchy

If there is a conflict between novelty and consistency, choose consistency.

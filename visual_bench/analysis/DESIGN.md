# Propagation inspection design

## 1. Product and journey

Researchers inspect one verification run and its ACT domain, follow propagation,
then select a layer and a neuron without losing recorded pass/version identity.
ACT owns bounds and verdicts. Missing records remain missing, never synthesized.

## 2. Color

Reuse `styles.css` semantic roles in both themes: `--panel`, `--panel2`, `--well`,
`--text`, `--muted`, `--line`, `--accent`, `--good`, `--warn`, `--violet`.
Neuron active = good, inactive = violet, unstable = warn, unknown = muted.
Labels and counts accompany color. Selected rows use a tonal surface, not a stripe.

## 3. Type

Preserve the workbench system font and 14px body. Inspection heading is 18px;
secondary text 12px; numeric values use tabular numerals. No new font dependency.

## 4. Spacing and layout

Local tokens: space 4/8/12/16/24px; radius 6px; control height 32px desktop and
44px touch; diagram coordinates describe data geometry rather than UI spacing.

Layout: list-detail (StyleGallery `patterns/split-sidebar/list-detail.md`);
network 28%, neuron map 72%; scroll owner `.center`, supplemental inspector
`.tabbody`; at <900px Network > Layer > Neuron shows one level at a time and
document scrolls. No additional vertical scroller in the propagation region.
Preserve source/focus order. Avoid fixed canvas widths forcing page overflow.

## 5. Components and brief

Use project `.secondary`, `.primary`, `.error`, `Empty`, `Pixels`, native labeled
select/input controls, and the existing SVG DAG conventions. Canvas maps have
an equivalent labeled neuron selector and keyboard arrows.

- Primary action: select a neuron to inspect its recorded bounds.
- Priorities: domain and pass; network progress; selected neuron evidence.
- Required content: block network and edges; per-layer active/inactive/unstable
  share; live layer and revisits; growing per-layer chart; play/pause/scrub;
  normalized/recorded timing; image input lb/ub; dense/conv neuron maps; bin/zoom;
  lane selector; forward/backward labels; pre/post bounds; ReLU relaxation;
  alpha per specification row and optimization state; unavailable/pending/error
  states including the explicit tensor-size limit.
- Left out on purpose: decorative cards, duplicate network when propagation is
  available, cross-domain comparison, sample terminology, arbitrary projected
  hybrid-zonotope polygons.

## 6. Interaction

Live follows committed records; replay uses record IDs, not newly computed
bounds. Pause stops local playback, not ACT. Every control retains its geometry.
No decorative animation. Focus-visible uses the accent outline.

## 7. Surfaces

Flat existing panel surfaces and neutral rules. No blur, shadows, raster UI or
new component framework. Canvas colors resolve CSS variables each render/theme.

## 8. Verification and debt

Baseline captures: `.omo/evidence/propagation/*-before.png`.
The existing shell's density, theme-default policy and broader accessibility
debt are outside this focused feature; do not claim whole-app WCAG conformance.
No scientific equivalence is claimed from synthetic fixture captures.

## 9. Gap ledger

| ID | Gap | Fix | Acceptance |
| --- | --- | --- | --- |
| P1 | Completed-only layer states | SSE-invalidated index plus replay | Live/replay browser checks |
| P2 | Only first 64 values shown | Binned canvas with exact selection | Binning tests and map capture |
| P3 | No pass/lane/spec identity | Explicit selectors and tensor indexing | Pure tensor tests |
| P4 | No neuron inspector | Existing inspector tab and mobile breadcrumb | Desktop/mobile captures |

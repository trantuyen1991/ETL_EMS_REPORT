# UI Cleanup Release Note (2026-05-01)

## Short changelog version
- Normalized report wording across daily and periodic report surfaces.
- Daily wording now consistently uses `Today / Yesterday` for electricity and utility charts.
- Weekly/monthly wording now consistently uses `This Week / Last Week` and `This Month / Last Month` across electricity, utility, and KPI render paths.
- Cleaned remaining residual and fallback wording drift in builder/template paths, including electricity residual subtitles, KPI fallback summary titles, and utility template fallback copy.
- Added regression coverage for electricity, utility, KPI, render pipeline, and PDF export paths.
- Validation status after the final cleanup chain: `24 passed`.

## Slightly fuller release-note version
Today’s UI/report wording cleanup standardized comparison labels across the report stack, with daily views using `Today / Yesterday` and periodic views using `This Week / Last Week` or `This Month / Last Month`. The work covered electricity and utility chart wording, periodic top-10/table phrasing, KPI fallback title alignment, and the last template fallback copy drift. Regression coverage was expanded alongside the cleanup, and the final verification state for the repo ended at `24 passed`.

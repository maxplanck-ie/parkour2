// Shared config for a plain client-side text (substring) header filter.
export function textFilterConfig(tooltip) {
  return {
    headerFilter: "input",
    headerTooltip: tooltip
  };
}

// All dates in this app display as YYYY.MM.DD (see dateUtils.js /
// formatDisplayDate) -- share one tooltip for date columns instead of the
// generic free-text hint.
export const DATE_FILTER_HELP =
  "Filter by date, full or partial, e.g. 2026.09 or 2026";

export function dateFilterConfig() {
  return textFilterConfig(DATE_FILTER_HELP);
}

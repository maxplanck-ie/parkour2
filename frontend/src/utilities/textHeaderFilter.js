// Shared config for a plain client-side text (substring) header filter.
export function textFilterConfig(tooltip, placeholder = "Filter...") {
  return {
    headerFilter: "input",
    headerFilterPlaceholder: placeholder,
    headerTooltip: tooltip
  };
}

// All dates in this app display as DD.MM.YYYY (see dateUtils.js /
// formatApiDate) -- share one placeholder/tooltip pair for date columns
// instead of the generic free-text hint.
export const DATE_FILTER_PLACEHOLDER = "DD.MM.YYYY";
export const DATE_FILTER_HELP =
  "Filter by date, full or partial, e.g. 03.09 or 2026";

export function dateFilterConfig() {
  return textFilterConfig(DATE_FILTER_HELP, DATE_FILTER_PLACEHOLDER);
}

// Parse a comparison expression typed into a numeric header filter.
// Supports: ">100", ">=100", "<50", "<=50", "=0", "100" (exact) and
// "100-200" (inclusive range). Returns null for an empty box (no filter)
// and {op: "invalid"} for a partial/unparsable entry (treated as no
// filter so rows are not all hidden mid-typing).
export function parseNumericExpression(raw) {
  const s = String(raw ?? "").trim();
  if (!s) return null;
  const num = (x) => Number(String(x).replace(",", "."));
  const between = s.match(/^(\d+(?:[.,]\d+)?)\s*-\s*(\d+(?:[.,]\d+)?)$/);
  if (between) {
    return { op: "between", a: num(between[1]), b: num(between[2]) };
  }
  const cmp = s.match(/^(>=|<=|>|<|=)?\s*(-?\d+(?:[.,]\d+)?)$/);
  if (cmp) {
    return { op: cmp[1] || "=", a: num(cmp[2]) };
  }
  return { op: "invalid" };
}

// Build a Tabulator headerFilterFunc that compares each row's numeric value
// (via `extract`) against the parsed comparison expression.
export function numericHeaderFilter(extract) {
  return (headerValue, rowValue) => {
    const expr = parseNumericExpression(headerValue);
    if (!expr || expr.op === "invalid") return true;
    const v = extract(rowValue);
    if (v === null || v === undefined || Number.isNaN(v)) return false;
    switch (expr.op) {
      case ">":
        return v > expr.a;
      case ">=":
        return v >= expr.a;
      case "<":
        return v < expr.a;
      case "<=":
        return v <= expr.a;
      case "=":
        return v === expr.a;
      case "between": {
        const lo = Math.min(expr.a, expr.b);
        const hi = Math.max(expr.a, expr.b);
        return v >= lo && v <= hi;
      }
      default:
        return true;
    }
  };
}

export const NUMERIC_FILTER_PLACEHOLDER = ">100  50-200";
export const NUMERIC_FILTER_HELP =
  "Numeric filter — type a comparison:\n" +
  ">100  above    <50  below\n" +
  ">=100 / <=50   at least / at most\n" +
  "=0  exact      100-200  range";

// Shared config that turns a column's header filter into the numeric
// comparison-expression filter, with one Tabulator tooltip for the header.
// Do not add a native title to the input: it overlaps Tabulator's tooltip.
export function numericFilterConfig(extract) {
  return {
    headerFilter: "input",
    headerFilterPlaceholder: NUMERIC_FILTER_PLACEHOLDER,
    headerFilterFunc: numericHeaderFilter(extract),
    headerTooltip: NUMERIC_FILTER_HELP
  };
}

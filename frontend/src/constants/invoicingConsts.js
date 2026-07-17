function displayValue(value) {
  if (value === null || value === undefined || value === "") return "";
  return value;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function ellipsisContainer(value, align = "left", bold = false) {
  const display = displayValue(value);
  const finalValue =
    display === null || display === undefined || display === "" ? "-" : display;
  const escapedValue = escapeHtml(finalValue);
  const justifyContent = align === "right" ? "flex-end" : "flex-start";
  const weight = bold ? "font-weight: bold;" : "";
  return `
    <div style="padding: 4px 8px; display: flex; align-items: center; justify-content: ${justifyContent};">
      <span title="${escapedValue}" style="${weight} padding: 8px 0px; overflow: hidden; white-space: nowrap; text-overflow: ellipsis;">${escapedValue}</span>
    </div>
  `;
}

function textFormatter(align = "left", bold = false) {
  return (cell) => ellipsisContainer(cell.getValue(), align, bold);
}

function moneyFormatter() {
  return (cell) => {
    const value = cell.getValue();
    if (value === null || value === undefined || value === "") {
      return ellipsisContainer("", "right");
    }
    const number = Number(value);
    const display = Number.isFinite(number)
      ? `${number.toLocaleString("de-DE", {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2
        })} €`
      : value;
    return ellipsisContainer(display, "right");
  };
}

// Parse a comparison expression typed into a numeric header filter.
// Supports: ">100", ">=100", "<50", "<=50", "=0", "100" (exact) and
// "100-200" (inclusive range). Returns null for an empty box (no filter)
// and {op: "invalid"} for a partial/unparsable entry (treated as no
// filter so rows are not all hidden mid-typing).
function parseNumericExpression(raw) {
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
function numericHeaderFilter(extract) {
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

const NUMERIC_FILTER_PLACEHOLDER = ">100  50-200";
const NUMERIC_FILTER_HELP =
  "Numeric filter — type a comparison:\n" +
  ">100  above    <50  below\n" +
  ">=100 / <=50   at least / at most\n" +
  "=0  exact      100-200  range";

// Shared config that turns a column's header filter into the numeric
// comparison-expression filter, with a syntax tooltip on both the header
// title and the filter input.
function numericFilterConfig(extract) {
  return {
    headerFilter: "input",
    headerFilterPlaceholder: NUMERIC_FILTER_PLACEHOLDER,
    headerFilterFunc: numericHeaderFilter(extract),
    headerFilterParams: { elementAttributes: { title: NUMERIC_FILTER_HELP } },
    headerTooltip: NUMERIC_FILTER_HELP
  };
}

export function invoicingColumnDefs() {
  return [
    {
      field: "request",
      title: "Request",
      minWidth: 150,
      frozen: true,
      cssClass: "right-border",
      headerFilter: true,
      headerFilterPlaceholder: "Filter...",
      formatter: textFormatter("left", true)
    },
    {
      field: "cost_unit",
      title: "Cost Unit",
      minWidth: 90,
      headerFilter: true,
      headerFilterPlaceholder: "Filter...",
      formatter: textFormatter("left")
    },
    {
      field: "sequencer",
      title: "Sequencer",
      minWidth: 115,
      headerFilter: true,
      headerFilterPlaceholder: "Filter...",
      formatter: textFormatter("left")
    },
    {
      field: "flowcell_date",
      title: "Date",
      minWidth: 95,
      headerFilter: true,
      headerFilterPlaceholder: "Filter...",
      formatter: textFormatter("left")
    },
    {
      field: "flowcell_id",
      title: "Flowcell ID",
      minWidth: 120,
      headerFilter: true,
      headerFilterPlaceholder: "Filter...",
      formatter: textFormatter("left")
    },
    {
      field: "pool",
      title: "Pool",
      minWidth: 100,
      headerFilter: true,
      headerFilterPlaceholder: "Filter...",
      formatter: textFormatter("left")
    },
    {
      field: "percentage",
      title: "%",
      minWidth: 90,
      headerFilter: true,
      headerFilterPlaceholder: "Filter...",
      formatter: textFormatter("left")
    },
    {
      field: "read_length",
      title: "Read Length",
      minWidth: 105,
      headerFilter: true,
      headerFilterPlaceholder: "Filter...",
      formatter: textFormatter("left")
    },
    {
      field: "num_libraries_samples_show",
      title: "# of Libraries/Samples",
      minWidth: 115,
      ...numericFilterConfig((v) => parseFloat(String(v))),
      formatter: textFormatter("left")
    },
    {
      field: "library_protocol",
      title: "Library Protocol",
      minWidth: 140,
      headerFilter: true,
      headerFilterPlaceholder: "Filter...",
      formatter: textFormatter("left")
    },
    {
      field: "fixed_costs",
      title: "Fixed Costs",
      minWidth: 95,
      hozAlign: "right",
      ...numericFilterConfig((v) => Number(v)),
      formatter: moneyFormatter()
    },
    {
      field: "sequencing_costs",
      title: "Sequencing Costs",
      minWidth: 105,
      hozAlign: "right",
      ...numericFilterConfig((v) => Number(v)),
      formatter: moneyFormatter()
    },
    {
      field: "preparation_costs",
      title: "Preparation Costs",
      minWidth: 105,
      hozAlign: "right",
      ...numericFilterConfig((v) => Number(v)),
      formatter: moneyFormatter()
    },
    {
      field: "variable_costs",
      title: "Variable Costs",
      minWidth: 95,
      hozAlign: "right",
      ...numericFilterConfig((v) => Number(v)),
      formatter: moneyFormatter()
    },
    {
      field: "total_costs",
      title: "Total Costs",
      minWidth: 95,
      hozAlign: "right",
      ...numericFilterConfig((v) => Number(v)),
      formatter: moneyFormatter()
    }
  ];
}

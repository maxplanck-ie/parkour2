import { numericFilterConfig } from "../utilities/numericHeaderFilter";
import { textFilterConfig } from "../utilities/textHeaderFilter";

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

const deEuroFormatter = new Intl.NumberFormat("de-DE", {
  style: "currency",
  currency: "EUR",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2
});

export function formatInvoicingCurrency(value) {
  if (value === null || value === undefined || value === "") return "";
  const number = Number(value);
  if (!Number.isFinite(number)) return String(value);

  return deEuroFormatter.format(number);
}

function moneyFormatter() {
  return (cell) => {
    const value = cell.getValue();
    if (value === null || value === undefined || value === "") {
      return ellipsisContainer("", "right");
    }
    return ellipsisContainer(formatInvoicingCurrency(value), "right");
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
      ...textFilterConfig(),
      formatter: textFormatter("left", true)
    },
    {
      field: "cost_unit",
      title: "Cost Unit",
      minWidth: 90,
      ...textFilterConfig(),
      formatter: textFormatter("left")
    },
    {
      field: "sequencer",
      title: "Sequencer",
      minWidth: 115,
      ...textFilterConfig(),
      formatter: textFormatter("left")
    },
    {
      field: "flowcell_date",
      title: "Date",
      minWidth: 95,
      ...textFilterConfig(),
      formatter: textFormatter("left")
    },
    {
      field: "flowcell_id",
      title: "Flowcell ID",
      minWidth: 120,
      ...textFilterConfig(),
      formatter: textFormatter("left")
    },
    {
      field: "pool",
      title: "Pool",
      minWidth: 100,
      ...textFilterConfig(),
      formatter: textFormatter("left")
    },
    {
      field: "percentage",
      title: "%",
      minWidth: 90,
      ...textFilterConfig(),
      formatter: textFormatter("left")
    },
    {
      field: "read_length",
      title: "Read Length",
      minWidth: 105,
      ...textFilterConfig(),
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
      ...textFilterConfig(),
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

export function invoicingExportColumns() {
  return [
    { header: "Request ID", key: "request", width: 16, excelType: "text" },
    { header: "Cost Unit", key: "cost_unit", width: 16, excelType: "text" },
    { header: "Sequencer", key: "sequencer", width: 22, excelType: "text" },
    { header: "Date", key: "flowcell_date", width: 14, excelType: "text" },
    { header: "Flowcell ID", key: "flowcell_id", width: 18, excelType: "text" },
    { header: "Pool ID", key: "pool", width: 18, excelType: "text" },
    { header: "% of Lanes", key: "percentage", width: 14, excelType: "text" },
    { header: "Read Length", key: "read_length", width: 18, excelType: "text" },
    {
      header: "# of Libraries/Samples",
      key: "num_libraries_samples_show",
      width: 20,
      excelType: "text"
    },
    {
      header: "Library Preparation Protocol",
      key: "library_protocol",
      width: 28,
      excelType: "text"
    },
    {
      header: "Fixed Costs",
      key: "fixed_costs",
      width: 16,
      excelType: "number",
      decimalPlaces: 2
    },
    {
      header: "Sequencing Costs",
      key: "sequencing_costs",
      width: 16,
      excelType: "number",
      decimalPlaces: 2
    },
    {
      header: "Preparation Costs",
      key: "preparation_costs",
      width: 16,
      excelType: "number",
      decimalPlaces: 2
    },
    {
      header: "Variable Costs",
      key: "variable_costs",
      width: 16,
      excelType: "number",
      decimalPlaces: 2
    },
    {
      header: "Total Costs",
      key: "total_costs",
      width: 16,
      excelType: "number",
      decimalPlaces: 2
    }
  ];
}

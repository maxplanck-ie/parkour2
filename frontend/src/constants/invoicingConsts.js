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

export function invoicingColumnDefs() {
  return [
    {
      field: "request",
      title: "Request",
      minWidth: 250,
      frozen: true,
      cssClass: "right-border",
      formatter: textFormatter("left", true)
    },
    {
      field: "cost_unit",
      title: "Cost Unit",
      minWidth: 150,
      formatter: textFormatter("left")
    },
    {
      field: "sequencer",
      title: "Sequencer",
      minWidth: 160,
      formatter: textFormatter("left")
    },
    {
      field: "flowcell",
      title: "Date + Flowcell ID",
      minWidth: 200,
      formatter: textFormatter("left")
    },
    {
      field: "pool",
      title: "Pool",
      minWidth: 150,
      formatter: textFormatter("left")
    },
    {
      field: "percentage",
      title: "%",
      minWidth: 120,
      formatter: textFormatter("left")
    },
    {
      field: "read_length",
      title: "Read Length",
      minWidth: 150,
      formatter: textFormatter("left")
    },
    {
      field: "num_libraries_samples_show",
      title: "# of Libraries/Samples",
      minWidth: 160,
      formatter: textFormatter("left")
    },
    {
      field: "library_protocol",
      title: "Library Protocol",
      minWidth: 200,
      formatter: textFormatter("left")
    },
    {
      field: "fixed_costs",
      title: "Fixed Costs",
      minWidth: 130,
      hozAlign: "right",
      formatter: moneyFormatter()
    },
    {
      field: "sequencing_costs",
      title: "Sequencing Costs",
      minWidth: 140,
      hozAlign: "right",
      formatter: moneyFormatter()
    },
    {
      field: "preparation_costs",
      title: "Preparation Costs",
      minWidth: 140,
      hozAlign: "right",
      formatter: moneyFormatter()
    },
    {
      field: "variable_costs",
      title: "Variable Costs",
      minWidth: 130,
      hozAlign: "right",
      formatter: moneyFormatter()
    },
    {
      field: "total_costs",
      title: "Total Costs",
      minWidth: 130,
      hozAlign: "right",
      formatter: moneyFormatter()
    }
  ];
}

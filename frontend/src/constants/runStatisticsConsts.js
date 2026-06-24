function displayValue(value, digits = null) {
  if (value === null || value === undefined || value === "") return "";
  if (digits === null) return value;
  const number = Number(value);
  return Number.isFinite(number) ? number.toFixed(digits) : value;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function ellipsisContainer(value, align = "left") {
  const finalValue = displayValue(value) || "-";
  const escapedValue = escapeHtml(finalValue);
  const justifyContent = align === "right" ? "flex-end" : "flex-start";
  return `
    <div style="padding: 4px 8px; display: flex; align-items: center; justify-content: ${justifyContent};">
      <span title="${escapedValue}" style="padding: 8px 0px; overflow: hidden; white-space: nowrap; text-overflow: ellipsis;">${escapedValue}</span>
    </div>
  `;
}

function textFormatter(align = "left") {
  return (cell) => ellipsisContainer(cell.getValue(), align);
}

function numberFormatter(digits = null, divisor = 1) {
  return (cell) => {
    const value = cell.getValue();
    if (value === null || value === undefined || value === "") {
      return ellipsisContainer("", "right");
    }
    const number = Number(value);
    const display = Number.isFinite(number)
      ? displayValue(number / divisor, digits)
      : value;
    return ellipsisContainer(display, "right");
  };
}

function withRunStatisticsColumnDefaults(columns) {
  return columns.map((column) => {
    if (!column.field || column.field === "selected") return column;
    const align = column.hozAlign === "right" ? "right" : "left";
    return {
      cssClass: column.frozen ? "right-border" : "regular-column",
      formatter: textFormatter(align),
      ...column
    };
  });
}

export function runStatisticsColumnDefs(onSelectionChanged) {
  return withRunStatisticsColumnDefaults([
    {
      field: "selected",
      title: "",
      width: 30,
      minWidth: 30,
      frozen: true,
      visible: true,
      headerVertical: false,
      headerSort: false,
      resizable: false,
      hozAlign: "center",
      cssClass: "checkbox-column right-border",
      clipboardCopyValue: () => "",
      formatter: (cell) =>
        `<input type="checkbox" title="Select" style="top:-4px" ${
          cell.getValue() ? "checked" : ""
        } />`,
      cellClick: (event, cell) => {
        const checkbox = event.target.closest('input[type="checkbox"]');
        if (!checkbox) return;
        const row = cell.getRow();
        row.update({ selected: checkbox.checked });
        onSelectionChanged?.(row.getData().row_id, checkbox.checked);
      }
    },
    {
      title: "Lane",
      field: "name",
      minWidth: 110,
      visible: true,
      frozen: true,
      headerFilter: true
    },
    {
      title: "Pool",
      field: "pool",
      minWidth: 135,
      visible: true,
      headerFilter: true
    },
    {
      title: "Request",
      field: "request",
      minWidth: 135,
      visible: true,
      headerFilter: true
    },
    {
      title: "Preparation Method",
      field: "library_preparation",
      minWidth: 150,
      visible: true,
      headerFilter: true,
      headerTooltip: "Preparation Method"
    },
    {
      title: "Analysis Type",
      field: "library_type",
      minWidth: 135,
      visible: true,
      headerFilter: true
    },
    {
      title: "Loading Concentration",
      field: "loading_concentration",
      minWidth: 135,
      visible: true,
      headerFilter: true,
      headerTooltip: "Loading Concentration",
      hozAlign: "right"
    },
    {
      title: "Cluster PF (%)",
      field: "cluster_pf",
      minWidth: 125,
      visible: true,
      headerFilter: true,
      hozAlign: "right"
    },
    {
      title: "Reads PF (M)",
      field: "reads_pf",
      minWidth: 125,
      visible: true,
      headerFilter: true,
      formatter: numberFormatter(1, 1000000),
      hozAlign: "right"
    },
    {
      title: "Undetermined Indices (%)",
      field: "undetermined_indices",
      minWidth: 145,
      visible: true,
      headerFilter: true,
      headerTooltip: "Undetermined Indices (%)",
      hozAlign: "right"
    },
    {
      title: "PhiX (%)",
      field: "phix",
      minWidth: 110,
      visible: true,
      headerFilter: true,
      hozAlign: "right"
    },
    {
      title: "Read 1 ≥ Q30 (%)",
      field: "read_1",
      minWidth: 135,
      visible: true,
      headerFilter: true,
      hozAlign: "right"
    },
    {
      title: "Read 2 (I) ≥ Q30 (%)",
      field: "read_2",
      minWidth: 155,
      visible: true,
      headerFilter: true,
      hozAlign: "right"
    }
  ]);
}

export function runStatisticsGroupHeader(value, count, data) {
  const row = data?.[0] || {};
  const date = row.create_time_display || "";
  const readLength = row.read_length ? `, ${row.read_length}` : "";
  return `<strong>${row.flowcell_id || value} (${date}, ${
    row.sequencer || ""
  }${readLength})</strong>`;
}

export function formatRunStatisticsDate(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return new Intl.DateTimeFormat("de-DE").format(date);
}

export function uniqueRunStatisticsValues(rows, field) {
  return [
    ...new Set(
      rows
        .map((row) => row[field])
        .filter((value) => value !== null && value !== undefined && value !== "")
        .map(String)
    )
  ].sort((a, b) => a.localeCompare(b, undefined, { sensitivity: "base" }));
}

export function runStatisticsRowMatchesSearch(row, query) {
  const normalizedQuery = String(query || "")
    .trim()
    .toLowerCase();
  if (!normalizedQuery) return true;
  return Object.values(row).some((value) =>
    (Array.isArray(value) ? value.join(", ") : String(value ?? ""))
      .toLowerCase()
      .includes(normalizedQuery)
  );
}

export function runStatisticsExportColumns() {
  return [
    { header: "Flowcell ID", key: "flowcell_id", width: 18, excelType: "text" },
    { header: "Date", key: "create_time_display", width: 14, excelType: "text" },
    { header: "Sequencer", key: "sequencer", width: 22, excelType: "text" },
    { header: "Read Length", key: "read_length", width: 18, excelType: "text" },
    { header: "Lane", key: "name", width: 14, excelType: "text" },
    { header: "Pool", key: "pool", width: 18, excelType: "text" },
    { header: "Request", key: "request", width: 28, excelType: "text" },
    {
      header: "Preparation Method",
      key: "library_preparation",
      width: 24,
      excelType: "text"
    },
    {
      header: "Analysis Type",
      key: "library_type",
      width: 20,
      excelType: "text"
    },
    {
      header: "Loading Concentration",
      key: "loading_concentration",
      width: 18,
      excelType: "number"
    },
    { header: "Cluster PF (%)", key: "cluster_pf", width: 16, excelType: "number" },
    { header: "Reads PF (M)", key: "reads_pf_m", width: 16, excelType: "number" },
    {
      header: "Undetermined Indices (%)",
      key: "undetermined_indices",
      width: 18,
      excelType: "number"
    },
    { header: "PhiX (%)", key: "phix", width: 14, excelType: "number" },
    { header: "Read 1 ≥ Q30 (%)", key: "read_1", width: 20, excelType: "number" },
    { header: "Read 2 (I) ≥ Q30 (%)", key: "read_2", width: 22, excelType: "number" }
  ];
}

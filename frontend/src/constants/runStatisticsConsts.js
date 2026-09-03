import iconSelectAll from "../assets/icons/action_select_all.svg";
import iconDeselectAll from "../assets/icons/action_deselect_all.svg";

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
  const display = displayValue(value);
  const finalValue =
    display === null || display === undefined || display === "" ? "-" : display;
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
      minWidth: 65,
      visible: true,
      frozen: true,
      headerFilter: true,
      headerFilterPlaceholder: "Filter..."
    },
    {
      title: "Pool",
      field: "pool",
      minWidth: 75,
      visible: true,
      headerFilter: true,
      headerFilterPlaceholder: "Filter..."
    },
    {
      title: "Request",
      field: "request",
      minWidth: 85,
      visible: true,
      headerFilter: true,
      headerFilterPlaceholder: "Filter..."
    },
    {
      title: "Preparation",
      field: "library_preparation",
      minWidth: 95,
      visible: true,
      headerFilter: true,
      headerFilterPlaceholder: "Filter...",
      headerTooltip: "Preparation Method"
    },
    {
      title: "Analysis Type",
      field: "library_type",
      minWidth: 85,
      visible: true,
      headerFilter: true,
      headerFilterPlaceholder: "Filter...",
      headerTooltip: "Analysis Type"
    },
    {
      title: "Loading Conc.",
      field: "loading_concentration",
      minWidth: 82,
      visible: true,
      headerTooltip: "Loading Concentration",
      hozAlign: "right"
    },
    {
      title: "Cluster PF (%)",
      field: "cluster_pf",
      minWidth: 78,
      visible: true,
      headerTooltip: "Cluster PF (%)",
      formatter: numberFormatter(2),
      hozAlign: "right"
    },
    {
      title: "Reads PF (M)",
      field: "reads_pf",
      minWidth: 74,
      visible: true,
      formatter: numberFormatter(1, 1000000),
      hozAlign: "right"
    },
    {
      title: "Undet. Indices (%)", // codespell:ignore undet
      field: "undetermined_indices",
      minWidth: 92,
      visible: true,
      headerTooltip: "Undetermined Indices (%)",
      hozAlign: "right"
    },
    {
      title: "PhiX (%)",
      field: "phix",
      minWidth: 60,
      visible: true,
      hozAlign: "right"
    },
    {
      title: "Aligned to PhiX (%)",
      field: "aligned_spike_in",
      minWidth: 95,
      visible: true,
      headerTooltip: "Aligned to PhiX (%)",
      hozAlign: "right"
    },
    {
      title: "Read 1 ≥ Q30 (%)",
      field: "read_1",
      minWidth: 85,
      visible: true,
      formatter: numberFormatter(2),
      hozAlign: "right"
    },
    {
      title: "Read 2 (I) ≥ Q30 (%)",
      field: "read_2",
      minWidth: 90,
      visible: true,
      headerTooltip: "Read 2 (I) ≥ Q30 (%)",
      formatter: numberFormatter(2),
      hozAlign: "right"
    }
  ]);
}

export function runStatisticsGroupHeader(value, count, data) {
  const row = data?.[0] || {};
  const title = row.flowcell_id || value;
  const metadata = [
    `Date: ${row.create_time_display || "-"}`,
    `Sequencer: ${row.sequencer || "-"}`,
    `Read Length: ${row.read_length || "-"}`
  ].join(", ");

  return `
    <div style="display: flex; justify-content: flex-start; align-items: center; min-width: 0;">
      <div style="display: flex; align-items: center; min-width: 0;">
        <span style="font-weight: bold; font-size: 12px; color: #333;">${title}</span><span style="display: inline-block; font-weight: normal; font-size: 12px; margin-left: 6px; color: black;">(${metadata})</span>
        <div class="group-action-buttons-container" style="position: sticky; gap: 5px;">
          <div title="Select All" class="group-action-button" onclick="handleGroupButtonClick(event, '${value}', 'selectAll')">
            <img src="${iconSelectAll}" alt="Select All" width="24" height="24" />
          </div>
          <div title="Deselect All" class="group-action-button" onclick="handleGroupButtonClick(event, '${value}', 'deselectAll')">
            <img src="${iconDeselectAll}" alt="Deselect All" width="24" height="24" />
          </div>
        </div>
      </div>
    </div>
  `;
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
        .filter(
          (value) => value !== null && value !== undefined && value !== ""
        )
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
    {
      header: "Date",
      key: "create_time_display",
      width: 14,
      excelType: "text"
    },
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
    {
      header: "Cluster PF (%)",
      key: "cluster_pf",
      width: 16,
      excelType: "number",
      decimalPlaces: 2
    },
    {
      header: "Reads PF (M)",
      key: "reads_pf_m",
      width: 16,
      excelType: "number",
      decimalPlaces: 1
    },
    {
      header: "Undetermined Indices (%)",
      key: "undetermined_indices",
      width: 18,
      excelType: "number"
    },
    { header: "PhiX (%)", key: "phix", width: 14, excelType: "number" },
    {
      header: "Aligned to PhiX (%)",
      key: "aligned_spike_in",
      width: 20,
      excelType: "number"
    },
    {
      header: "Read 1 ≥ Q30 (%)",
      key: "read_1",
      width: 20,
      excelType: "number",
      decimalPlaces: 2
    },
    {
      header: "Read 2 (I) ≥ Q30 (%)",
      key: "read_2",
      width: 22,
      excelType: "number",
      decimalPlaces: 2
    }
  ];
}

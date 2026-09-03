import iconSelectAll from "../assets/icons/action_select_all.svg";
import iconDeselectAll from "../assets/icons/action_deselect_all.svg";

function fixedNumber(value, digits = 2) {
  if (value === null || value === undefined || value === "") return "";
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

function ellipsisContainer(value, align = "left", nativeTitle = true) {
  const finalValue =
    value === null || value === undefined || value === "" ? "-" : value;
  const escapedValue = escapeHtml(finalValue);
  const justifyContent = align === "right" ? "flex-end" : "flex-start";
  const titleAttr = nativeTitle ? ` title="${escapedValue}"` : "";
  return `
    <div style="padding: 4px 8px; display: flex; align-items: center; justify-content: ${justifyContent};">
      <span${titleAttr} style="padding: 8px 0px; overflow: hidden; white-space: nowrap; text-overflow: ellipsis;">${escapedValue}</span>
    </div>
  `;
}

function textFormatter(align = "left", nativeTitle = true) {
  return (cell) => ellipsisContainer(cell.getValue(), align, nativeTitle);
}

function fixedFormatter(digits = 2) {
  return (cell) =>
    ellipsisContainer(fixedNumber(cell.getValue(), digits), "right");
}

function withSequencesStatisticsColumnDefaults(columns) {
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

export function sequencesStatisticsColumnDefs(onSelectionChanged) {
  return withSequencesStatisticsColumnDefaults([
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
      title: "Request",
      field: "request",
      minWidth: 75,
      visible: true,
      frozen: true,
      headerFilter: true,
      headerFilterPlaceholder: "Filter..."
    },
    {
      title: "Barcode",
      field: "barcode",
      minWidth: 70,
      visible: true,
      frozen: true,
      headerFilter: true,
      headerFilterPlaceholder: "Filter..."
    },
    {
      title: "Name",
      field: "name",
      minWidth: 80,
      visible: true,
      headerFilter: true,
      headerFilterPlaceholder: "Filter...",
      formatter: textFormatter("left", false),
      tooltip: (event, cell) => cell.getValue() || ""
    },
    {
      title: "Lane",
      field: "lane_display",
      minWidth: 45,
      visible: true,
      headerFilter: true,
      headerFilterPlaceholder: "Filter..."
    },
    {
      title: "Pool",
      field: "pool",
      minWidth: 65,
      visible: true,
      headerFilter: true,
      headerFilterPlaceholder: "Filter..."
    },
    {
      title: "Protocol",
      field: "library_protocol",
      minWidth: 80,
      visible: true,
      headerFilter: true,
      headerFilterPlaceholder: "Filter...",
      headerTooltip: "Library Protocol"
    },
    {
      title: "Analysis",
      field: "library_type",
      minWidth: 70,
      visible: true,
      headerFilter: true,
      headerFilterPlaceholder: "Filter...",
      headerTooltip: "Analysis Type"
    },
    {
      title: "Requested Reads (M)",
      field: "reads_pf_requested",
      minWidth: 95,
      visible: true,
      headerTooltip: "Requested Reads (M)",
      hozAlign: "right"
    },
    {
      title: "Seq. Reads (M)",
      field: "reads_pf_sequenced",
      minWidth: 85,
      visible: true,
      headerTooltip: "Sequenced Reads PF (M)",
      formatter: (cell) => {
        const value = cell.getValue();
        if (value === null || value === undefined || value === "") {
          return ellipsisContainer("", "right");
        }
        return ellipsisContainer(fixedNumber(Number(value) / 1000000), "right");
      },
      hozAlign: "right"
    },
    {
      title: "Reads (%)",
      field: "reads_percent",
      minWidth: 55,
      visible: true,
      formatter: fixedFormatter(),
      hozAlign: "right"
    },
    {
      title: "Conf. Off-species",
      field: "confident_reads",
      minWidth: 95,
      visible: true,
      headerTooltip: "Confident Off-species Reads",
      formatter: fixedFormatter(),
      hozAlign: "right"
    },
    {
      title: "Opt. Dup. (%)",
      field: "optical_duplicates",
      minWidth: 80,
      visible: true,
      headerTooltip: "Optical Duplicates (%)",
      formatter: fixedFormatter(),
      hozAlign: "right"
    },
    {
      title: "Dup. Reads (%)",
      field: "dupped_reads",
      minWidth: 75,
      visible: true,
      headerTooltip: "Duplicated Reads (%)",
      formatter: fixedFormatter(),
      hozAlign: "right"
    },
    {
      title: "Mapped (%)",
      field: "mapped_reads",
      minWidth: 75,
      visible: true,
      headerTooltip: "Mapped Reads (%)",
      formatter: fixedFormatter(),
      hozAlign: "right"
    },
    {
      title: "Insert",
      field: "insert_size",
      minWidth: 55,
      visible: true,
      headerTooltip: "Insert Size",
      hozAlign: "right"
    }
  ]);
}

export function sequencesStatisticsGroupHeader(value, count, data) {
  const row = data?.[0] || {};
  const title = row.flowcell_id || value;
  const metadata = [
    `Date: ${row.create_time_display || "-"}`,
    `Sequencer: ${row.sequencer || "-"}`
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

export function formatSequencesStatisticsDate(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return new Intl.DateTimeFormat("de-DE").format(date);
}

export function uniqueSequencesStatisticsValues(rows, field) {
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

export function sequencesStatisticsRowMatchesSearch(row, query) {
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

export function sequencesStatisticsExportColumns() {
  return [
    { header: "Flowcell ID", key: "flowcell_id", width: 18, excelType: "text" },
    {
      header: "Date",
      key: "create_time_display",
      width: 14,
      excelType: "text"
    },
    { header: "Sequencer", key: "sequencer", width: 22, excelType: "text" },
    { header: "Request", key: "request", width: 28, excelType: "text" },
    { header: "Barcode", key: "barcode", width: 16, excelType: "text" },
    { header: "Name", key: "name", width: 24, excelType: "text" },
    { header: "Lane", key: "lane_display", width: 14, excelType: "text" },
    { header: "Pool", key: "pool", width: 18, excelType: "text" },
    {
      header: "Library Protocol",
      key: "library_protocol",
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
      header: "Requested Reads (M)",
      key: "reads_pf_requested",
      width: 22,
      excelType: "number"
    },
    {
      header: "Sequenced Reads PF (M)",
      key: "reads_pf_sequenced_m",
      width: 22,
      excelType: "number",
      decimalPlaces: 2
    },
    {
      header: "Reads (%)",
      key: "reads_percent",
      width: 14,
      excelType: "number",
      decimalPlaces: 2
    },
    {
      header: "Confident Off-species Reads",
      key: "confident_reads",
      width: 26,
      excelType: "number",
      decimalPlaces: 2
    },
    {
      header: "Optical Duplicates (%)",
      key: "optical_duplicates",
      width: 22,
      excelType: "number",
      decimalPlaces: 2
    },
    {
      header: "Duplicated Reads (%)",
      key: "dupped_reads",
      width: 20,
      excelType: "number",
      decimalPlaces: 2
    },
    {
      header: "Mapped Reads (%)",
      key: "mapped_reads",
      width: 18,
      excelType: "number",
      decimalPlaces: 2
    },
    {
      header: "Insert Size",
      key: "insert_size",
      width: 16,
      excelType: "number"
    }
  ];
}

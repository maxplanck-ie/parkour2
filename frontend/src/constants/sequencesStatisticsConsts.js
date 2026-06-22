function fixedNumber(value, digits = 2) {
  if (value === null || value === undefined || value === "") return "";
  const number = Number(value);
  return Number.isFinite(number) ? number.toFixed(digits) : value;
}

function fixedFormatter(digits = 2) {
  return (cell) => fixedNumber(cell.getValue(), digits);
}

export function sequencesStatisticsColumnDefs(onSelectionChanged) {
  return [
    {
      field: "selected",
      title: "",
      width: 38,
      minWidth: 38,
      maxWidth: 38,
      frozen: true,
      visible: true,
      headerSort: false,
      resizable: false,
      hozAlign: "center",
      formatter: (cell) =>
        `<input type="checkbox" title="Select" ${
          cell.getValue() ? "checked" : ""
        } />`,
      cellClick: (event, cell) => {
        const checkbox = event.target.closest('input[type="checkbox"]');
        if (!checkbox) return;
        cell.getRow().update({ selected: checkbox.checked });
        onSelectionChanged?.();
      }
    },
    {
      title: "Request",
      field: "request",
      minWidth: 135,
      visible: true,
      frozen: true,
      headerFilter: true
    },
    {
      title: "Barcode",
      field: "barcode",
      minWidth: 120,
      visible: true,
      frozen: true,
      headerFilter: true
    },
    {
      title: "Name",
      field: "name",
      minWidth: 135,
      visible: true,
      headerFilter: true
    },
    {
      title: "Lane",
      field: "lane_display",
      minWidth: 100,
      visible: true,
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
      title: "Library Protocol",
      field: "library_protocol",
      minWidth: 150,
      visible: true,
      headerFilter: true
    },
    {
      title: "Analysis Type",
      field: "library_type",
      minWidth: 135,
      visible: true,
      headerFilter: true
    },
    {
      title: "Reads PF (M), requested",
      field: "reads_pf_requested",
      minWidth: 170,
      visible: true,
      headerFilter: true,
      hozAlign: "right"
    },
    {
      title: "Reads PF (M), sequenced",
      field: "reads_pf_sequenced",
      minWidth: 170,
      visible: true,
      headerFilter: true,
      formatter: (cell) => {
        const value = cell.getValue();
        if (value === null || value === undefined || value === "") return "";
        return fixedNumber(Number(value) / 1000000);
      },
      hozAlign: "right"
    },
    {
      title: "% reads",
      field: "reads_percent",
      minWidth: 105,
      visible: true,
      headerFilter: true,
      formatter: fixedFormatter(),
      hozAlign: "right"
    },
    {
      title: "confident off-species reads",
      field: "confident_reads",
      minWidth: 190,
      visible: true,
      headerFilter: true,
      formatter: fixedFormatter(),
      hozAlign: "right"
    },
    {
      title: "% Optical Duplicates",
      field: "optical_duplicates",
      minWidth: 165,
      visible: true,
      headerFilter: true,
      formatter: fixedFormatter(),
      hozAlign: "right"
    },
    {
      title: "% dupped reads",
      field: "dupped_reads",
      minWidth: 135,
      visible: true,
      headerFilter: true,
      formatter: fixedFormatter(),
      hozAlign: "right"
    },
    {
      title: "% mapped reads",
      field: "mapped_reads",
      minWidth: 135,
      visible: true,
      headerFilter: true,
      formatter: fixedFormatter(),
      hozAlign: "right"
    },
    {
      title: "Insert Size",
      field: "insert_size",
      minWidth: 110,
      visible: true,
      headerFilter: true,
      hozAlign: "right"
    }
  ];
}

export function sequencesStatisticsGroupHeader(value, count, data) {
  const row = data?.[0] || {};
  return `<strong>${row.flowcell_id || value} (${
    row.create_time_display || ""
  }, ${row.sequencer || ""})</strong>`;
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
        .filter((value) => value !== null && value !== undefined && value !== "")
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

export function applySequencesStatisticsColumnSettings(
  columns,
  visibilityStorageKey,
  widthsStorageKey
) {
  const visibility = JSON.parse(
    localStorage.getItem(visibilityStorageKey) || "{}"
  );
  const widths = JSON.parse(localStorage.getItem(widthsStorageKey) || "{}");
  return columns.map((column) => {
    const configured = { ...column };
    if (configured.field) {
      if (widths[configured.field]) {
        configured.width = Math.max(
          widths[configured.field],
          configured.minWidth || 0
        );
      }
      configured.visible =
        visibility[configured.field] ?? configured.visible ?? true;
    }
    return configured;
  });
}

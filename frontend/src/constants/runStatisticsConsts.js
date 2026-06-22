function displayValue(value, digits = null) {
  if (value === null || value === undefined || value === "") return "";
  if (digits === null) return value;
  const number = Number(value);
  return Number.isFinite(number) ? number.toFixed(digits) : value;
}

function numberFormatter(digits = null, divisor = 1) {
  return (cell) => {
    const value = cell.getValue();
    if (value === null || value === undefined || value === "") return "";
    const number = Number(value);
    if (!Number.isFinite(number)) return value;
    return displayValue(number / divisor, digits);
  };
}

export function runStatisticsColumnDefs() {
  return [
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
      title: "Prep. Method",
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
      title: "Loading Concentr.",
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
      title: "Undet. Indices (%)",
      field: "undetermined_indices",
      minWidth: 145,
      visible: true,
      headerFilter: true,
      headerTooltip: "Undetermined Indices (%)",
      hozAlign: "right"
    },
    {
      title: "% Spike In",
      field: "phix",
      minWidth: 110,
      visible: true,
      headerFilter: true,
      hozAlign: "right"
    },
    {
      title: "Read 1 % >=Q30",
      field: "read_1",
      minWidth: 135,
      visible: true,
      headerFilter: true,
      hozAlign: "right"
    },
    {
      title: "Read 2 (I) % >=Q30",
      field: "read_2",
      minWidth: 155,
      visible: true,
      headerFilter: true,
      hozAlign: "right"
    }
  ];
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

export function applyRunStatisticsColumnSettings(
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

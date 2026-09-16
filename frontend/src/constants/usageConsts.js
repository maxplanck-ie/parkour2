// Reserved for the Libraries/Samples split -- used by stacked charts and by
// the Records chart's own two bars. Keep the semantics consistent: index 0
// is always "Libraries", index 1 is always "Samples".
export const USAGE_CHART_COLORS = [
  "#5DA5DA",
  "#FAA43A",
  "#60BD68",
  "#F17CB0",
  "#B2912F",
  "#B276B2",
  "#DECF3F",
  "#F15854",
  "#4D4D4D"
];

// Used for per-category coloring in any non-stacked chart other than
// Records, so those charts don't restart at the same blue/orange pair that
// means "Libraries/Samples" elsewhere.
export const USAGE_CHART_COLORS_SECONDARY = [
  "#8DA0CB",
  "#E78AC3",
  "#A6D854",
  "#FFD92F",
  "#E5C494",
  "#B3B3B3",
  "#66C2A5",
  "#FC8D62",
  "#7570B3"
];

const AXIS_LABEL_MAX_CHARS = 22;

function truncateAxisLabel(value) {
  return value.length > AXIS_LABEL_MAX_CHARS
    ? `${value.slice(0, AXIS_LABEL_MAX_CHARS)}…`
    : value;
}

// `stacked: true` charts break each bar down into libraries/samples
// (matching what the API already returns); `stacked: false` charts only
// have a single "data" value per bar. `type: "boxplot"` charts plot a
// [min, q1, median, q3, max] array per bar instead of a single value.
export const USAGE_CHARTS = [
  {
    key: "records",
    title: "Libraries & Samples",
    endpoint: "api/usage/records/",
    stacked: false,
    usesPrimaryPalette: true
  },
  {
    key: "organizations",
    title: "Organizations",
    endpoint: "api/usage/organizations/",
    stacked: false
  },
  {
    key: "principalInvestigators",
    title: "Principal Investigators",
    endpoint: "api/usage/principal_investigators/",
    stacked: true
  },
  {
    key: "analysisTypes",
    title: "Analysis Types",
    endpoint: "api/usage/analysis_types/",
    stacked: true
  },
  {
    key: "turnaroundAnalysisType",
    title: "Turnaround Time by Analysis Type (days)",
    endpoint: "api/usage/turnaround_time/",
    type: "boxplot",
    extraParams: { group_by: "analysis_type" }
  },
  {
    key: "turnaroundPrincipalInvestigator",
    title: "Turnaround Time by PI (days)",
    endpoint: "api/usage/turnaround_time/",
    type: "boxplot",
    extraParams: { group_by: "pi" }
  }
];

// The API always returns one row per known category (e.g. "records"
// always returns both "Libraries" and "Samples"), even when every value in
// range is zero -- so an empty range still yields a non-empty array. Sum
// the actual values instead of checking array length to decide whether
// there's anything to plot.
export function usageChartTotal(chartDef, data) {
  if (chartDef.type === "boxplot") {
    return data.length;
  }
  return data.reduce((sum, row) => {
    return (
      sum +
      (chartDef.stacked
        ? (row.libraries || 0) + (row.samples || 0)
        : row.data || 0)
    );
  }, 0);
}

export function buildUsageChartOption(chartDef, data) {
  const names = data.map((row) => row.name);
  const categoryColors = chartDef.usesPrimaryPalette
    ? USAGE_CHART_COLORS
    : USAGE_CHART_COLORS_SECONDARY;

  let series;
  if (chartDef.type === "boxplot") {
    series = [
      {
        name: chartDef.title,
        type: "boxplot",
        data: data.map((row) => row.data),
        itemStyle: { color: categoryColors[0] }
      }
    ];
  } else if (chartDef.stacked) {
    series = [
      {
        name: "Libraries",
        type: "bar",
        stack: "total",
        data: data.map((row) => row.libraries || 0),
        color: USAGE_CHART_COLORS[0]
      },
      {
        name: "Samples",
        type: "bar",
        stack: "total",
        data: data.map((row) => row.samples || 0),
        color: USAGE_CHART_COLORS[1]
      }
    ];
  } else {
    series = [
      {
        name: chartDef.title,
        type: "bar",
        data: data.map((row) => row.data || 0),
        itemStyle: {
          color: (params) =>
            categoryColors[params.dataIndex % categoryColors.length]
        }
      }
    ];
  }

  return {
    grid: {
      left: 8,
      right: 16,
      top: chartDef.stacked ? 36 : 16,
      bottom: 70,
      containLabel: true
    },
    legend: chartDef.stacked ? { top: 0 } : undefined,
    tooltip: {
      trigger: chartDef.type === "boxplot" ? "item" : "axis",
      axisPointer: { type: "shadow" }
    },
    xAxis: {
      type: "category",
      data: names,
      axisLabel: {
        rotate: 45,
        interval: 0,
        formatter: truncateAxisLabel
      }
    },
    yAxis: {
      type: "value",
      minInterval: chartDef.type === "boxplot" ? undefined : 1
    },
    series
  };
}

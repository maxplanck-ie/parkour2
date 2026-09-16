// Whole Usage page shares this 3-color palette: purple/orange for the
// "Libraries"/"Samples" split on stacked charts, green for boxplot charts.
export const USAGE_CHART_COLORS = ["#8064A2", "#FAA43A", "#60A060"];

const AXIS_LABEL_MAX_CHARS = 18;

function truncateAxisLabel(value) {
  return value.length > AXIS_LABEL_MAX_CHARS
    ? `${value.slice(0, AXIS_LABEL_MAX_CHARS)}…`
    : value;
}

// `stacked: true` charts break each bar down into libraries/samples
// (matching what the API already returns). `type: "boxplot"` charts plot a
// [min, q1, median, q3, max] array per bar instead of a single value.
export const USAGE_CHARTS = [
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
    key: "turnaroundPrincipalInvestigator",
    title: "Turnaround Time by PI (days)",
    endpoint: "api/usage/turnaround_time/",
    type: "boxplot",
    extraParams: { group_by: "pi" }
  },
  {
    key: "turnaroundAnalysisType",
    title: "Turnaround Time by Analysis Type (days)",
    endpoint: "api/usage/turnaround_time/",
    type: "boxplot",
    extraParams: { group_by: "analysis_type" }
  }
];

// The API always returns one row per known category (e.g. a stacked chart
// always returns both "Libraries" and "Samples"), even when every value in
// range is zero -- so an empty range still yields a non-empty array. Sum
// the actual values instead of checking array length to decide whether
// there's anything to plot.
export function usageChartTotal(chartDef, data) {
  if (chartDef.type === "boxplot") {
    return data.length;
  }
  return data.reduce((sum, row) => {
    return sum + (row.libraries || 0) + (row.samples || 0);
  }, 0);
}

export function buildUsageChartOption(chartDef, data) {
  const names = data.map((row) => row.name);

  let series;
  if (chartDef.type === "boxplot") {
    series = [
      {
        name: chartDef.title,
        type: "boxplot",
        data: data.map((row) => row.data),
        itemStyle: { color: USAGE_CHART_COLORS[2] }
      }
    ];
    const outlierPoints = data.flatMap((row, index) =>
      (row.outliers || []).map((value) => [index, value])
    );
    if (outlierPoints.length) {
      series.push({
        name: "Outliers",
        type: "scatter",
        data: outlierPoints,
        symbolSize: 6,
        itemStyle: { color: USAGE_CHART_COLORS[2] }
      });
    }
  } else {
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

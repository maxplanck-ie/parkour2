// Whole Usage page shares this palette: purple/orange for the
// "Libraries"/"Samples" split on stacked charts, lifecycle teal for the
// all-records boxplot charts. Boxplot lines/outliers are always black.
export const USAGE_CHART_COLORS = ["#8064A2", "#FAA43A", "#006c66"];
const BOXPLOT_LINE_COLOR = "#000000";

export const USAGE_RECORD_TYPES = [
  { value: "all", label: "All records" },
  { value: "libraries", label: "Libraries" },
  { value: "samples", label: "Samples" }
];

const BOXPLOT_FILL_BY_RECORD_TYPE = {
  all: USAGE_CHART_COLORS[2],
  libraries: USAGE_CHART_COLORS[0],
  samples: USAGE_CHART_COLORS[1]
};

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
    key: "turnaroundSequencer",
    title: "Turnaround Time by Sequencer (days)",
    endpoint: "api/usage/turnaround_time/",
    type: "boxplot",
    horizontal: true,
    extraParams: { group_by: "sequencer" }
  },
  {
    key: "turnaroundAnalysisType",
    title: "Turnaround Time by Analysis Type (days)",
    endpoint: "api/usage/turnaround_time/",
    type: "boxplot",
    horizontal: true,
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

export function buildUsageChartOption(chartDef, data, recordType = "all") {
  const names = data.map((row) =>
    chartDef.type === "boxplot" && row.count !== undefined
      ? `${row.name} (n=${row.count})`
      : row.name
  );
  const isHorizontalBoxplot =
    chartDef.type === "boxplot" && chartDef.horizontal;

  let series;
  if (chartDef.type === "boxplot") {
    const boxplotFill =
      BOXPLOT_FILL_BY_RECORD_TYPE[recordType] || USAGE_CHART_COLORS[2];
    series = [
      {
        name: chartDef.title,
        type: "boxplot",
        data: data.map((row) => row.data),
        itemStyle: {
          color: boxplotFill,
          borderColor: BOXPLOT_LINE_COLOR,
          borderWidth: 1
        },
        lineStyle: { color: BOXPLOT_LINE_COLOR }
      }
    ];
    const outlierPoints = data.flatMap((row, index) =>
      (row.outliers || []).map((outlierObj) => ({
        value: isHorizontalBoxplot
          ? [outlierObj.value, index]
          : [index, outlierObj.value],
        name: row.name,
        request_id: outlierObj.request_id,
        flowcell_id: outlierObj.flowcell_id,
        turnaround_days: outlierObj.value
      }))
    );
    if (outlierPoints.length) {
      series.push({
        name: "Outliers",
        type: "scatter",
        data: outlierPoints,
        symbolSize: 6,
        itemStyle: { color: BOXPLOT_LINE_COLOR }
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
    ].filter(
      (seriesDef) =>
        recordType === "all" || seriesDef.name.toLowerCase() === recordType
    );
  }

  return {
    grid: {
      left: isHorizontalBoxplot ? 110 : 8,
      right: 16,
      top: chartDef.stacked ? 36 : 16,
      bottom: isHorizontalBoxplot ? 16 : 70,
      containLabel: true
    },
    legend: chartDef.stacked ? { top: 0 } : undefined,
    tooltip: {
      trigger: chartDef.type === "boxplot" ? "item" : "axis",
      axisPointer: { type: "shadow" },
      formatter: (params) => {
        if (chartDef.type === "boxplot") {
          if (params.seriesName === "Outliers") {
            const { name, turnaround_days, request_id, flowcell_id } =
              params.data;
            return `${name}<br/>Days: ${turnaround_days}<br/>Request: ${request_id}<br/>Flowcell: ${flowcell_id}`;
          } else {
            const [min, q1, median, q3, max] = params.data;
            const countMatch = params.name.match(/\(n=(\d+)\)$/);
            const count = countMatch ? countMatch[1] : "?";
            const nameWithoutCount = countMatch
              ? params.name.slice(0, -countMatch[0].length).trim()
              : params.name;
            return `${nameWithoutCount}<br/>Count: ${count}<br/>Min: ${min}<br/>Q1: ${q1}<br/>Median: ${median}<br/>Q3: ${q3}<br/>Max: ${max}`;
          }
        } else {
          let total = 0;
          let lines = [`${params[0].axisValueLabel}<br/>`];
          params.forEach((item) => {
            total += item.value;
            lines.push(`${item.marker} ${item.seriesName}: ${item.value}`);
          });
          lines.push(`<strong>Total: ${total}</strong>`);
          return lines.join("<br/>");
        }
      }
    },
    xAxis: {
      type: isHorizontalBoxplot ? "value" : "category",
      data: isHorizontalBoxplot ? undefined : names,
      name: isHorizontalBoxplot ? "Days" : undefined,
      nameLocation: isHorizontalBoxplot ? "middle" : undefined,
      nameGap: isHorizontalBoxplot ? 30 : undefined,
      axisLabel: isHorizontalBoxplot
        ? { interval: 0 }
        : {
            rotate: 45,
            interval: 0,
            formatter: truncateAxisLabel
          }
    },
    yAxis: {
      type: isHorizontalBoxplot ? "category" : "value",
      data: isHorizontalBoxplot ? names : undefined,
      axisLabel: isHorizontalBoxplot
        ? { interval: 0, formatter: truncateAxisLabel }
        : undefined,
      minInterval: chartDef.type === "boxplot" ? undefined : 1
    },
    series
  };
}

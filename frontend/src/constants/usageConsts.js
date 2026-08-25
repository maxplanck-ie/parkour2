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

// `stacked: true` charts break each bar down into libraries/samples
// (matching what the API already returns); `stacked: false` charts only
// have a single "data" value per bar.
export const USAGE_CHARTS = [
  {
    key: "records",
    title: "Libraries & Samples",
    endpoint: "api/usage/records/",
    stacked: false
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
    key: "libraryTypes",
    title: "Analysis Types",
    endpoint: "api/usage/library_types/",
    stacked: true
  }
];

// The API always returns one row per known category (e.g. "records"
// always returns both "Libraries" and "Samples"), even when every value in
// range is zero -- so an empty range still yields a non-empty array. Sum
// the actual values instead of checking array length to decide whether
// there's anything to plot.
export function usageChartTotal(chartDef, data) {
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

  const series = chartDef.stacked
    ? [
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
      ]
    : [
        {
          name: chartDef.title,
          type: "bar",
          data: data.map((row) => row.data || 0),
          itemStyle: {
            color: (params) =>
              USAGE_CHART_COLORS[params.dataIndex % USAGE_CHART_COLORS.length]
          }
        }
      ];

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
      trigger: "axis",
      axisPointer: { type: "shadow" }
    },
    xAxis: {
      type: "category",
      data: names,
      axisLabel: {
        rotate: 45,
        interval: 0
      }
    },
    yAxis: {
      type: "value",
      minInterval: 1
    },
    series
  };
}

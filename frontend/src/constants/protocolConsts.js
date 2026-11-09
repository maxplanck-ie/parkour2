// Build ECharts option for protocol comparison charts (density + rug)
import { USAGE_CHART_COLORS } from "./usageConsts";

export function buildProtocolChartOption(chartDef, protocolSeries) {
  // protocolSeries = [{ protocol: string, values: number[] }, ...]
  // One protocol: Usage green. Two: Usage purple + orange.
  const PROTOCOL_COLORS =
    protocolSeries.length > 1
      ? [USAGE_CHART_COLORS[0], USAGE_CHART_COLORS[1]]
      : [USAGE_CHART_COLORS[2]];

  const series = protocolSeries
    .map((p, idx) => {
      const values = p.values || [];
      if (values.length === 0) return null;

      // Simple KDE for density
      const min = Math.min(...values);
      const max = Math.max(...values);
      const bandwidth = Math.max(
        (max - min) / 40,
        chartDef.key === "optical_duplicates" ? 0.01 : 1,
      );
      const nSteps = 120;
      const xs = [];
      const ys = [];

      for (let i = 0; i <= nSteps; i++) {
        const x = min + (max - min) * (i / nSteps);
        let y = 0;
        for (const v of values) {
          const u = (x - v) / bandwidth;
          y += Math.exp(-0.5 * u * u) / (bandwidth * Math.sqrt(2 * Math.PI));
        }
        y /= values.length;
        xs.push(x);
        ys.push(y);
      }

      const color = PROTOCOL_COLORS[idx % PROTOCOL_COLORS.length];

      return {
        // density area
        name: p.protocol,
        type: "line",
        smooth: true,
        data: xs.map((x, i) => [x, ys[i]]),
        lineStyle: { width: 2, color },
        areaStyle: {
          color: {
            type: "linear",
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: color + "40" },
              { offset: 1, color: color + "00" },
            ],
          },
        },
        showSymbol: false,
        z: 10,
      };
    })
    .filter(Boolean);

  // Rug marks (y=0 scatter with rectangular symbols)
  const rugSeries = protocolSeries
    .map((p, idx) => {
      const values = p.values || [];
      if (values.length === 0) return null;
      return {
        name: p.protocol,
        type: "scatter",
        data: values.map((v) => [v, 0]),
        symbolSize: 4,
        symbol: "rect",
        itemStyle: { color: PROTOCOL_COLORS[idx % PROTOCOL_COLORS.length] },
        emphasis: { disabled: true },
        z: 5,
        tooltip: {
          formatter: (params) => {
            const label =
              chartDef.key === "optical_duplicates"
                ? params.data[0].toFixed(2) + "%"
                : params.data[0].toFixed(2) + " ng/µl";
            return `${p.protocol}: ${label}`;
          },
        },
      };
    })
    .filter(Boolean);

  const xName =
    chartDef.key === "optical_duplicates"
      ? "Optical Duplicate Rate (%)"
      : "Concentration (ng/µl)";

  return {
    color: PROTOCOL_COLORS,
    tooltip: { trigger: "axis" },
    legend: { data: protocolSeries.map((p) => p.protocol), bottom: 0 },
    grid: { left: 60, right: 40, top: 30, bottom: 50 },
    xAxis: { type: "value", name: xName },
    yAxis: [
      { type: "value", name: "Density", min: 0 },
      { type: "value", show: false, min: 0, max: 1 },
    ],
    series: [...series, ...rugSeries.map((s) => ({ ...s, yAxisIndex: 1 }))],
  };
}

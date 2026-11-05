<template>
  <div class="parent-container">
    <div class="header-bar">
      <h1>
        <font-awesome-icon icon="fa-solid fa-flask-vial" class="header-icon" />
        Protocol Comparison
      </h1>
    </div>

    <div class="filter-row">
      <div class="filter-item protocol-filter-item">
        <label>Protocols</label>
        <select
          v-model="selectedProtocols"
          multiple
          size="4"
          class="protocol-select"
          @change="onProtocolChange"
        >
          <option v-for="p in availableProtocols" :key="p.name" :value="p.name">
            {{ p.name }}
          </option>
        </select>
        <span class="protocol-hint">Select 1–2 protocols (Ctrl/Cmd+click for multiple)</span>
      </div>

      <div class="filter-item date-filter-item">
        <label>Start</label>
        <DateInput v-model="startDateString" :disabled="loading" />
      </div>

      <div class="filter-item date-filter-item">
        <label>End</label>
        <DateInput v-model="endDateString" :disabled="loading" />
      </div>
    </div>

    <div class="charts-grid">
      <div v-if="loading" class="loading-overlay">Loading…</div>

      <template v-else>
        <div class="charts-row">
          <div class="chart-card">
            <div class="chart-title">Library Concentration (ng/µl)</div>
            <div class="chart-canvas" ref="concChartRef"></div>
            <div v-if="!hasConcData" class="chart-empty-text">No concentration data</div>
          </div>

          <div class="chart-card">
            <div class="chart-title">Optical Duplicate Rate (%)</div>
            <div class="chart-canvas" ref="dupChartRef"></div>
            <div v-if="!hasDupData" class="chart-empty-text">No optical duplicate data</div>
          </div>
        </div>

        <div class="charts-row">
          <div class="chart-card" style="grid-column: 1 / -1; max-width: 800px; margin: 0 auto;">
            <div class="chart-title">Protocol Summary</div>
            <div class="protocol-summary">
              <table class="table table-sm table-bordered">
                <thead>
                  <tr>
                    <th>Protocol</th>
                    <th>Libraries (conc.)</th>
                    <th>Libraries (opt. dup.)</th>
                    <th>Median Conc.</th>
                    <th>Median Opt. Dup.</th>
                    <th>Conc. Range</th>
                    <th>Opt. Dup. Range</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="p in protocolStats" :key="p.protocol">
                    <td>{{ p.protocol }}</td>
                    <td>{{ p.n_libraries }}</td>
                    <td>{{ p.n_optical }}</td>
                    <td>{{ p.median_conc !== null ? p.median_conc.toFixed(2) : '—' }}</td>
                    <td>{{ p.median_dup !== null ? (p.median_dup * 100).toFixed(2) : '—' }}</td>
                    <td>{{ p.min_conc !== null ? `${p.min_conc.toFixed(1)} – ${p.max_conc.toFixed(1)}` : '—' }}</td>
                    <td>{{ p.min_dup !== null ? `${(p.min_dup * 100).toFixed(2)} – ${(p.max_dup * 100).toFixed(2)}%` : '—' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useDebounceFn } from "@vueuse/core";
import { use } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { LineChart, ScatterChart } from "echarts/charts";
import {
  GridComponent,
  LegendComponent,
  TooltipComponent,
  TitleComponent,
} from "echarts/components";
import VChart from "vue-echarts";
import DateInput from "../components/DateInput.vue";
import {
  createAxiosObject,
  formatDateForInput,
  handleError,
  isValidDate,
  urlStringStartsWith,
} from "../utilities/utilityFunctions";
import { getProtocolNames } from "../constants/protocolConsts";

use([
  CanvasRenderer,
  LineChart,
  ScatterChart,
  GridComponent,
  LegendComponent,
  TooltipComponent,
  TitleComponent,
]);

const axiosRef = createAxiosObject();
const urlStringStart = urlStringStartsWith();

const PROTOCOL_COLORS = ["#8064A2", "#FAA43A"];

const today = new Date();
const sixMonthsAgo = new Date(today);
sixMonthsAgo.setMonth(today.getMonth() - 6);

const loading = ref(true);
const startDateString = ref(formatDateForInput(sixMonthsAgo));
const endDateString = ref(formatDateForInput(today));
const selectedProtocols = ref<string[]>([]);
const availableProtocols = ref<Array<{ name: string }>>([]);
const chartData = reactive<Record<string, any>>({});
let requestId = 0;

const concChartRef = ref<VChart | null>(null);
const dupChartRef = ref<VChart | null>(null);

const startDateValid = computed(() => isValidDate(startDateString.value));
const endDateValid = computed(() => isValidDate(endDateString.value));

async function loadAvailableProtocols() {
  try {
    const names = await getProtocolNames();
    availableProtocols.value = names.map((n) => ({ name: n }));
    if (names.length >= 2) {
      selectedProtocols.value = names.slice(0, 2);
    } else if (names.length === 1) {
      selectedProtocols.value = [names[0]];
    }
  } catch (e) {
    handleError(e, "Failed to load protocols");
  }
}

function computeStats(protocolName: string, concVals: number[], dupVals: number[]) {
  const sortedConc = [...concVals].sort((a, b) => a - b);
  const sortedDup = [...dupVals].sort((a, b) => a - b);
  const median = (arr: number[]) =>
    arr.length === 0 ? null : arr[Math.floor(arr.length / 2)];
  return {
    protocol: protocolName,
    n_libraries: sortedConc.length,
    n_optical: sortedDup.length,
    median_conc: median(sortedConc),
    median_dup: median(sortedDup),
    min_conc: sortedConc[0] ?? null,
    max_conc: sortedConc[sortedConc.length - 1] ?? null,
    min_dup: sortedDup[0] ?? null,
    max_dup: sortedDup[sortedDup.length - 1] ?? null,
  };
}

const protocolStats = computed(() => {
  const stats = [];
  for (const protocol of selectedProtocols.value) {
    const d = chartData[protocol];
    if (!d) continue;
    const concVals = d.concentration?.map((x: any) => x.value) ?? [];
    const dupVals = d.optical_duplicates?.map((x: any) => x.value) ?? [];
    stats.push(computeStats(protocol, concVals, dupVals));
  }
  return stats;
});

const hasConcData = computed(() => {
  return selectedProtocols.value.some(
    (p) => (chartData[p]?.concentration?.length ?? 0) > 0
  );
});

const hasDupData = computed(() => {
  return selectedProtocols.value.some(
    (p) => (chartData[p]?.optical_duplicates?.length ?? 0) > 0
  );
});

function buildDensityOption(protocolData: any[], color: string) {
  const series = protocolData.map((p, idx) => {
    const values = p.concentration?.map((x: any) => x.value) ?? [];
    if (values.length === 0) return null;
    // Simple kernel density estimation for display
    const min = Math.min(...values);
    const max = Math.max(...values);
    const bandwidth = Math.max(1, (max - min) / 40);
    const xs = [];
    const ys = [];
    const nSteps = 100;
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
    return {
      name: p.protocol,
      type: "line",
      smooth: true,
      data: xs.map((x, i) => [x, ys[i]]),
      lineStyle: { width: 2, color: PROTOCOL_COLORS[idx % PROTOCOL_COLORS.length] },
      areaStyle: {
        color: {
          type: "linear",
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            { offset: 0, color: PROTOCOL_COLORS[idx % PROTOCOL_COLORS.length] + "40" },
            { offset: 1, color: PROTOCOL_COLORS[idx % PROTOCOL_COLORS.length] + "00" },
          ],
        },
      },
      showSymbol: false,
      z: 10,
    };
  }).filter(Boolean);

  // Rug marks
  const rugSeries = protocolData.map((p, idx) => {
    const values = p.concentration?.map((x: any) => x.value) ?? [];
    if (values.length === 0) return null;
    return {
      name: p.protocol + " (rug)",
      type: "scatter",
      data: values.map((v: number) => [v, 0]),
      symbolSize: 4,
      symbol: "rect",
      itemStyle: { color: PROTOCOL_COLORS[idx % PROTOCOL_COLORS.length] },
      emphasis: { disabled: true },
      z: 5,
      tooltip: {
        formatter: (params: any) => `${p.protocol}: ${params.data[0].toFixed(2)} ng/µl`,
      },
    };
  }).filter(Boolean);

  return {
    color: PROTOCOL_COLORS,
    tooltip: { trigger: "axis" },
    legend: { data: protocolData.map((p) => p.protocol), bottom: 0 },
    grid: { left: 60, right: 40, top: 30, bottom: 50 },
    xAxis: { type: "value", name: "Concentration (ng/µl)" },
    yAxis: [
      { type: "value", name: "Density", min: 0, max: "dataMax" },
      { type: "value", show: false, min: 0, max: 1 },
    ],
    series: [...series, ...rugSeries.map((s) => ({ ...s, yAxisIndex: 1 }))],
  };
}

function buildOpticalDupOption(protocolData: any[], color: string) {
  const series = protocolData.map((p, idx) => {
    const values = p.optical_duplicates?.map((x: any) => x.value * 100) ?? []; // percentage
    if (values.length === 0) return null;
    const min = Math.min(...values);
    const max = Math.max(...values);
    const bandwidth = Math.max(0.01, (max - min) / 40);
    const xs = [];
    const ys = [];
    const nSteps = 100;
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
    return {
      name: p.protocol,
      type: "line",
      smooth: true,
      data: xs.map((x, i) => [x, ys[i]]),
      lineStyle: { width: 2, color: PROTOCOL_COLORS[idx % PROTOCOL_COLORS.length] },
      areaStyle: {
        color: {
          type: "linear",
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            { offset: 0, color: PROTOCOL_COLORS[idx % PROTOCOL_COLORS.length] + "40" },
            { offset: 1, color: PROTOCOL_COLORS[idx % PROTOCOL_COLORS.length] + "00" },
          ],
        },
      },
      showSymbol: false,
      z: 10,
    };
  }).filter(Boolean);

  const rugSeries = protocolData.map((p, idx) => {
    const values = p.optical_duplicates?.map((x: any) => x.value * 100) ?? [];
    if (values.length === 0) return null;
    return {
      name: p.protocol + " (rug)",
      type: "scatter",
      data: values.map((v: number) => [v, 0]),
      symbolSize: 4,
      symbol: "rect",
      itemStyle: { color: PROTOCOL_COLORS[idx % PROTOCOL_COLORS.length] },
      emphasis: { disabled: true },
      z: 5,
      tooltip: {
        formatter: (params: any) => `${p.protocol}: ${params.data[0].toFixed(2)}% optical dup.`,
      },
    };
  }).filter(Boolean);

  return {
    color: PROTOCOL_COLORS,
    tooltip: { trigger: "axis" },
    legend: { data: protocolData.map((p) => p.protocol), bottom: 0 },
    grid: { left: 60, right: 40, top: 30, bottom: 50 },
    xAxis: { type: "value", name: "Optical Duplicate Rate (%)" },
    yAxis: [
      { type: "value", name: "Density", min: 0, max: "dataMax" },
      { type: "value", show: false, min: 0, max: 1 },
    ],
    series: [...series, ...rugSeries.map((s) => ({ ...s, yAxisIndex: 1 }))],
  };
}

async function loadData() {
  if (!startDateValid.value || !endDateValid.value || selectedProtocols.value.length === 0) {
    return;
  }
  const thisRequestId = ++requestId;
  loading.value = true;

  const params = {
    protocols: selectedProtocols.value.join(","),
    start: `${startDateString.value}T00:00:00`,
    end: `${endDateString.value}T23:59:59`,
  };

  try {
    const resp = await axiosRef.get(`${urlStringStart}/api/usage/protocol_comparison/`, {
      params,
    });
    if (thisRequestId !== requestId) return;
    const data = resp.data;
    chartData.value = {};
    for (const d of data) {
      chartData[d.protocol] = d;
    }
  } catch (e) {
    if (thisRequestId === requestId) handleError(e, "Failed to load protocol comparison data");
  } finally {
    if (thisRequestId === requestId) loading.value = false;
  }
}

const debouncedLoad = useDebounceFn(loadData, 300);

function onProtocolChange() {
  if (selectedProtocols.value.length > 2) {
    selectedProtocols.value = selectedProtocols.value.slice(0, 2);
  }
  debouncedLoad();
}

watch(
  [startDateString, endDateString],
  () => {
    if (startDateValid.value && endDateValid.value) {
      debouncedLoad();
    }
  },
  { deep: true }
);

onMounted(async () => {
  await loadAvailableProtocols();
  await loadData();
});

onBeforeUnmount(() => {
  // cleanup if needed
});
</script>

<style scoped>
.parent-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 10px;
}

.header-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.header-bar h1 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--bs-body-color);
}

.header-icon {
  font-size: 1.5rem;
  color: var(--bs-primary);
}

.filter-row {
  display: flex;
  gap: 16px;
  align-items: flex-end;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.filter-item.protocol-filter-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 280px;
}

.protocol-select {
  height: 120px;
  font-size: var(--header-control-font-size, 0.875rem);
  border-radius: 6px;
  border: 1px solid #d8d8d8;
  padding: 4px;
  background: white;
}

.protocol-hint {
  font-size: 0.75rem;
  color: #6c757d;
}

.filter-item.date-filter-item {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--bs-body-color);
  white-space: nowrap;
}

.filter-item.date-filter-item label {
  display: inline;
  padding: 0;
  margin: 0;
  border: none;
  background-color: transparent;
  font-weight: normal;
  color: var(--bs-body-color);
}

.filter-item.date-filter-item input,
.filter-item.date-filter-item select {
  height: var(--header-control-height, 36px);
  font-size: var(--header-control-font-size, 0.875rem);
  border-radius: 6px;
  border: 1px solid #d8d8d8;
  padding: 0 8px;
  width: auto;
}

.filter-item.date-filter-item .invalid-date {
  border-color: #dc3545;
}

.charts-grid {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 14px;
  overflow-y: auto;
  position: relative;
}

.charts-row {
  flex: 1;
  display: grid;
  gap: 14px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

@media (max-width: 767px) {
  .charts-row {
    grid-template-columns: 1fr;
  }
}

.chart-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.2);
  padding: 14px;
  display: flex;
  flex-direction: column;
  min-height: 360px;
}

.chart-title {
  font-weight: bold;
  margin-bottom: 8px;
  font-size: 0.95rem;
}

.chart-canvas {
  flex: 1;
  width: 100%;
}

.chart-empty-text {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
  font-size: 18px;
}

.loading-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.8);
  font-size: 1.2rem;
  color: #666;
  z-index: 10;
}

.protocol-summary {
  flex: 1;
  overflow: auto;
}

.protocol-summary table {
  margin-bottom: 0;
  font-size: 0.875rem;
}

.protocol-summary th {
  background-color: #f8f9fa;
  font-weight: 600;
}
</style>
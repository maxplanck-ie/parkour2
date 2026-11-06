<template>
  <div class="parent-container">
    <div v-if="loading" class="loading-overlay">
      <div class="spinner"></div>
      <p>Loading <span style="font-weight: bold">Protocol Comparison</span>...</p>
    </div>

    <div class="header">
      <img :src="iconUsageHeader" alt="Usage" class="statistics-header-icon" />
      <div class="header-title">Protocol Comparison</div>

      <div class="sticky-actions">
        <div class="filter-item protocol-filter-item">
          <label for="pcProtocolA">Protocol A</label>
          <select id="pcProtocolA" v-model="protocolA" @change="scheduleReload">
            <option v-for="name in protocolNames" :key="name" :value="name">
              {{ name }}
            </option>
          </select>
        </div>
        <div class="filter-item protocol-filter-item">
          <label for="pcProtocolB">Protocol B</label>
          <select id="pcProtocolB" v-model="protocolB" @change="scheduleReload">
            <option value="">— none —</option>
            <option v-for="name in protocolNames" :key="name" :value="name">
              {{ name }}
            </option>
          </select>
        </div>
        <div class="filter-item date-filter-item">
          <label for="pcStartDate">From</label>
          <DateInput
            id="pcStartDate"
            v-model="startDateString"
            :class="{ 'invalid-date': !startDateValid }"
            @update:model-value="scheduleReload"
          />
        </div>
        <div class="filter-item date-filter-item">
          <label for="pcEndDate">To</label>
          <DateInput
            id="pcEndDate"
            v-model="endDateString"
            :class="{ 'invalid-date': !endDateValid }"
            @update:model-value="scheduleReload"
          />
        </div>
      </div>
    </div>

    <div class="charts-grid">
      <div
        v-for="chartDef in charts"
        :key="chartDef.key"
        class="chart-card"
      >
        <div class="chart-title">{{ chartDef.title }}</div>
        <p v-if="!chartHasData(chartDef.key)" class="chart-empty-text">
            No Data
        </p>
        <VChart
          v-else
          class="chart-canvas"
          :option="chartOptions[chartDef.key]"
          autoresize
        />
      </div>
    </div>
  </div>
</template>

<script>
import { computed, onMounted, reactive, ref } from "vue";
import { useDebounceFn } from "@vueuse/core";
import { use } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { LineChart, ScatterChart } from "echarts/charts";
import {
  GridComponent,
  LegendComponent,
  TooltipComponent
} from "echarts/components";
import VChart from "vue-echarts";
import DateInput from "../components/DateInput.vue";
import {
  createAxiosObject,
  formatDateForInput,
  handleError,
  isValidDate,
  urlStringStartsWith
} from "../utilities/utilityFunctions";
import { buildProtocolChartOption } from "../constants/protocolConsts";
import iconUsageHeader from "../assets/icons/header_usage.svg";

use([
  CanvasRenderer,
  LineChart,
  ScatterChart,
  GridComponent,
  LegendComponent,
  TooltipComponent
]);

const axiosRef = createAxiosObject();
const urlStringStart = urlStringStartsWith();
const DATE_FILTER_DEBOUNCE_MS = 500;

const today = new Date();
const threeYearsAgo = new Date(today);
threeYearsAgo.setFullYear(today.getFullYear() - 3);

const charts = [
  { key: "concentration", title: "Library Concentration (ng/µl)" },
  { key: "optical_duplicates", title: "Optical Duplicate Rate (%)" }
];

export default {
  name: "ProtocolComparisonView",
  components: {
    VChart,
    DateInput
  },
  setup() {
    const loading = ref(true);
    const startDateString = ref(formatDateForInput(threeYearsAgo));
    const endDateString = ref(formatDateForInput(today));
    const protocolA = ref("");
    const protocolB = ref("");
    const protocolNames = ref([]);
    const chartData = reactive({});
    let requestId = 0;

    const startDateValid = computed(() => isValidDate(startDateString.value));
    const endDateValid = computed(() => isValidDate(endDateString.value));

    const chartOptions = computed(() => {
      const options = {};
      charts.forEach((chartDef) => {
        options[chartDef.key] = buildProtocolChartOption(
          chartDef,
          chartData[chartDef.key] || []
        );
      });
      return options;
    });

    function chartHasData(key) {
      return (chartData[key] || []).some((series) => series.values.length > 0);
    }

    async function fetchProtocolNames() {
      try {
        const response = await axiosRef.get(
          `${urlStringStart}/api/library_protocols/`
        );
        protocolNames.value = response.data
          .map((p) => p.name)
          .sort((a, b) => a.localeCompare(b, undefined, { sensitivity: "base" }));
        if (!protocolA.value && protocolNames.value.length > 0) {
          protocolA.value = protocolNames.value[0];
        }
      } catch (error) {
        handleError(error);
      }
    }

    async function loadComparisonData() {
      if (!startDateValid.value || !endDateValid.value || !protocolA.value) {
        return;
      }
      const thisRequestId = ++requestId;
      loading.value = true;
      const protocols = [protocolA.value];
      if (protocolB.value && protocolB.value !== protocolA.value) {
        protocols.push(protocolB.value);
      }
      const params = {
        protocols: protocols.join(","),
        start: `${startDateString.value}T00:00:00`,
        end: `${endDateString.value}T23:59:59`
      };
      try {
        const response = await axiosRef.get(
          `${urlStringStart}/api/usage/protocol_comparison/`,
          { params }
        );
        if (thisRequestId !== requestId) return;
        charts.forEach((chartDef) => {
          chartData[chartDef.key] = response.data.map((row) => ({
            protocol: row.protocol,
            values: row[chartDef.key] || []
          }));
        });
      } catch (error) {
        if (thisRequestId === requestId) {
          handleError(error);
        }
      } finally {
        if (thisRequestId === requestId) {
          loading.value = false;
        }
      }
    }

    const scheduleReload = useDebounceFn(loadComparisonData, DATE_FILTER_DEBOUNCE_MS);

    onMounted(async () => {
      await fetchProtocolNames();
      await loadComparisonData();
    });

    return {
      loading,
      startDateString,
      endDateString,
      startDateValid,
      endDateValid,
      protocolA,
      protocolB,
      protocolNames,
      charts,
      chartOptions,
      chartHasData,
      scheduleReload,
      iconUsageHeader
    };
  }
};
</script>

<style scoped>
.parent-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 10px;
}

.filter-item.date-filter-item {
  display: flex;
  align-items: center;
  gap: 6px;
  color: white;
  white-space: nowrap;
  margin-bottom: 0;
}

.filter-item.protocol-filter-item {
  display: flex;
  align-items: center;
  gap: 6px;
  color: white;
  white-space: nowrap;
  margin-bottom: 0;
}

.filter-item label {
  display: inline;
  padding: 0;
  margin: 0;
  border: none;
  background-color: transparent;
  font-weight: normal;
  color: white;
}

.filter-item input,
.filter-item select {
  height: var(--header-control-height);
  font-size: var(--header-control-font-size);
  border-radius: 6px;
  border: 1px solid #d8d8d8;
  padding: 0 8px;
  width: auto;
  max-width: 220px;
}

.filter-item .invalid-date {
  border-color: #dc3545;
}

.charts-grid {
  flex: 1;
  display: grid;
  gap: 14px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  overflow-y: auto;
}

@media (max-width: 767px) {
  .charts-grid {
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
</style>

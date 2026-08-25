<template>
  <div class="parent-container">
    <div v-if="loading" class="loading-overlay">
      <div class="spinner"></div>
      <p>Loading <span style="font-weight: bold">Usage</span>...</p>
    </div>

    <div class="header">
      <img :src="iconUsageHeader" alt="Usage" class="statistics-header-icon" />
      <div class="header-title">Usage</div>

      <div class="sticky-actions">
        <div class="filter-item date-filter-item">
          <label for="usageStartDate">From</label>
          <input
            id="usageStartDate"
            v-model="startDateString"
            :class="{ 'invalid-date': !startDateValid }"
            type="date"
            @input="scheduleReload"
          />
        </div>
        <div class="filter-item date-filter-item">
          <label for="usageEndDate">To</label>
          <input
            id="usageEndDate"
            v-model="endDateString"
            :class="{ 'invalid-date': !endDateValid }"
            type="date"
            @input="scheduleReload"
          />
        </div>
      </div>
    </div>

    <div class="charts-grid">
      <div
        v-for="chartDef in usageCharts"
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
import { computed, onBeforeUnmount, onMounted, reactive, ref } from "vue";
import { use } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { BarChart } from "echarts/charts";
import {
  GridComponent,
  LegendComponent,
  TooltipComponent
} from "echarts/components";
import VChart from "vue-echarts";
import {
  createAxiosObject,
  formatDateForInput,
  handleError,
  isValidDate,
  urlStringStartsWith
} from "../utilities/utilityFunctions";
import { USAGE_CHARTS, buildUsageChartOption } from "../constants/usageConsts";
import iconUsageHeader from "../assets/icons/header_usage.svg";

use([
  CanvasRenderer,
  BarChart,
  GridComponent,
  LegendComponent,
  TooltipComponent
]);

const axiosRef = createAxiosObject();
const urlStringStart = urlStringStartsWith();
const DATE_FILTER_DEBOUNCE_MS = 500;

const today = new Date();
const oneYearAgo = new Date(today);
oneYearAgo.setFullYear(today.getFullYear() - 1);

export default {
  name: "UsageView",
  components: {
    VChart
  },
  setup() {
    const loading = ref(true);
    const startDateString = ref(formatDateForInput(oneYearAgo));
    const endDateString = ref(formatDateForInput(today));
    const chartData = reactive({});
    let reloadTimeout = null;
    let requestId = 0;

    const startDateValid = computed(() => isValidDate(startDateString.value));
    const endDateValid = computed(() => isValidDate(endDateString.value));

    const usageCharts = USAGE_CHARTS;

    const chartOptions = computed(() => {
      const options = {};
      usageCharts.forEach((chartDef) => {
        const data = chartData[chartDef.key] || [];
        options[chartDef.key] = buildUsageChartOption(chartDef, data);
      });
      return options;
    });

    function chartHasData(key) {
      return (chartData[key] || []).length > 0;
    }

    async function loadUsageData() {
      if (!startDateValid.value || !endDateValid.value) {
        return;
      }
      const thisRequestId = ++requestId;
      loading.value = true;
      const params = {
        start: `${startDateString.value}T00:00:00`,
        end: `${endDateString.value}T23:59:59`
      };

      try {
        const responses = await Promise.all(
          usageCharts.map((chartDef) =>
            axiosRef.get(`${urlStringStart}/${chartDef.endpoint}`, { params })
          )
        );
        if (thisRequestId !== requestId) return;
        usageCharts.forEach((chartDef, index) => {
          chartData[chartDef.key] = responses[index].data || [];
        });
      } catch (error) {
        if (thisRequestId !== requestId) return;
        handleError(error);
      } finally {
        if (thisRequestId === requestId) {
          loading.value = false;
        }
      }
    }

    function scheduleReload() {
      if (reloadTimeout) {
        clearTimeout(reloadTimeout);
      }
      reloadTimeout = setTimeout(loadUsageData, DATE_FILTER_DEBOUNCE_MS);
    }

    onMounted(loadUsageData);
    onBeforeUnmount(() => {
      if (reloadTimeout) {
        clearTimeout(reloadTimeout);
      }
    });

    return {
      loading,
      startDateString,
      endDateString,
      startDateValid,
      endDateValid,
      usageCharts,
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
}

.filter-item.date-filter-item input {
  height: var(--header-control-height);
  font-size: var(--header-control-font-size);
  border-radius: 6px;
  border: 1px solid #d8d8d8;
  padding: 0 8px;
}

.filter-item.date-filter-item input.invalid-date {
  border-color: #dc3545;
}

.charts-grid {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  overflow-y: auto;
}

@media (max-width: 991px) {
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

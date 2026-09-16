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
          <DateInput
            id="usageStartDate"
            v-model="startDateString"
            :class="{ 'invalid-date': !startDateValid }"
            @update:model-value="scheduleReload"
          />
        </div>
        <div class="filter-item date-filter-item">
          <label for="usageEndDate">To</label>
          <DateInput
            id="usageEndDate"
            v-model="endDateString"
            :class="{ 'invalid-date': !endDateValid }"
            @update:model-value="scheduleReload"
          />
        </div>
      </div>
    </div>

    <div class="charts-grid">
      <div class="charts-row charts-row-top">
        <div
          v-for="chartDef in topRowCharts"
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
      <div class="charts-row charts-row-bottom">
        <div
          v-for="chartDef in bottomRowCharts"
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
  </div>
</template>

<script>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from "vue";
import { useDebounceFn } from "@vueuse/core";
import { use } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { BarChart, BoxplotChart } from "echarts/charts";
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
import {
  USAGE_CHARTS,
  buildUsageChartOption,
  usageChartTotal
} from "../constants/usageConsts";
import iconUsageHeader from "../assets/icons/header_usage.svg";

use([
  CanvasRenderer,
  BarChart,
  BoxplotChart,
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
    VChart,
    DateInput
  },
  setup() {
    const loading = ref(true);
    const startDateString = ref(formatDateForInput(oneYearAgo));
    const endDateString = ref(formatDateForInput(today));
    const chartData = reactive({});
    let requestId = 0;

    const startDateValid = computed(() => isValidDate(startDateString.value));
    const endDateValid = computed(() => isValidDate(endDateString.value));

    const usageCharts = USAGE_CHARTS;
    const topRowCharts = usageCharts.slice(0, 3);
    const bottomRowCharts = usageCharts.slice(3);

    const chartOptions = computed(() => {
      const options = {};
      usageCharts.forEach((chartDef) => {
        const data = chartData[chartDef.key] || [];
        options[chartDef.key] = buildUsageChartOption(chartDef, data);
      });
      return options;
    });

    function chartHasData(key) {
      const chartDef = usageCharts.find((c) => c.key === key);
      return usageChartTotal(chartDef, chartData[key] || []) > 0;
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
          usageCharts.map((chartDef) => {
            const chartParams = chartDef.extraParams
              ? { ...params, ...chartDef.extraParams }
              : params;
            return axiosRef.get(`${urlStringStart}/${chartDef.endpoint}`, {
              params: chartParams
            });
          })
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

    const scheduleReload = useDebounceFn(
      loadUsageData,
      DATE_FILTER_DEBOUNCE_MS
    );

    onMounted(loadUsageData);
    onBeforeUnmount(() => {
      scheduleReload.cancel();
    });

    return {
      loading,
      startDateString,
      endDateString,
      startDateValid,
      endDateValid,
      usageCharts,
      topRowCharts,
      bottomRowCharts,
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

.filter-item.date-filter-item label {
  display: inline;
  padding: 0;
  margin: 0;
  border: none;
  background-color: transparent;
  font-weight: normal;
  color: white;
}

.filter-item.date-filter-item input {
  height: var(--header-control-height);
  font-size: var(--header-control-font-size);
  border-radius: 6px;
  border: 1px solid #d8d8d8;
  padding: 0 8px;
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
}

.charts-row {
  flex: 1;
  display: grid;
  gap: 14px;
}

.charts-row-top {
  grid-template-columns: 1fr 1fr 2fr;
}

.charts-row-bottom {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

@media (max-width: 1199px) {
  .charts-row-top,
  .charts-row-bottom {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 767px) {
  .charts-row-top,
  .charts-row-bottom {
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

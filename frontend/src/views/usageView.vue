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
        <div class="filter-item header-filter-item">
          <label for="usageProtocol">Protocol</label>
          <select
            id="usageProtocol"
            v-model="protocolA"
            @change="scheduleProtocolReload"
          >
            <option v-for="name in protocolNames" :key="name" :value="name">
              {{ name }}
            </option>
          </select>
        </div>
        <div class="button-popup-wrapper">
          <button
            id="toggleUsageFiltersButton"
            class="header-button"
            @click="showFilters = !showFilters"
          >
            <font-awesome-icon icon="fa-solid fa-filter" />
            <span>Filters</span>
          </button>
          <div
            v-if="showFilters"
            id="usageFiltersPopup"
            class="button-popup-container statistics-filters-popup"
          >
            <div class="filter-item date-filter-item">
              <label for="usageProtocolB">2nd Protocol</label>
              <select
                id="usageProtocolB"
                v-model="protocolB"
                @change="scheduleProtocolReload"
              >
                <option value="">None</option>
                <option v-for="name in protocolNames" :key="name" :value="name">
                  {{ name }}
                </option>
              </select>
            </div>
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
            <div class="filter-item date-filter-item">
              <label for="usageRecordType">Show</label>
              <select
                id="usageRecordType"
                v-model="recordType"
                @change="scheduleReload"
              >
                <option
                  v-for="option in recordTypeOptions"
                  :key="option.value"
                  :value="option.value"
                >
                  {{ option.label }}
                </option>
              </select>
            </div>
            <div class="filter-item date-filter-item">
              <label for="usageMinCount">Min. data points</label>
              <input
                id="usageMinCount"
                v-model.number="minCount"
                type="number"
                min="1"
                step="1"
                @input="scheduleReload"
              />
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="charts-grid">
      <div class="charts-row charts-row-protocol">
        <div
          v-for="chartDef in protocolCharts"
          :key="chartDef.key"
          class="chart-card"
        >
          <div class="chart-title">{{ chartDef.title }}</div>
          <p
            v-if="!protocolChartHasData(chartDef.key)"
            class="chart-empty-text"
          >
            No Data
          </p>
          <VChart
            v-else
            class="chart-canvas"
            :option="protocolChartOptions[chartDef.key]"
            autoresize
          />
        </div>
      </div>
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
import { useDebounceFn, useEventListener } from "@vueuse/core";
import { use } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import {
  BarChart,
  BoxplotChart,
  LineChart,
  ScatterChart,
} from "echarts/charts";
import {
  GridComponent,
  LegendComponent,
  TooltipComponent,
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
import {
  USAGE_CHARTS,
  USAGE_RECORD_TYPES,
  buildUsageChartOption,
  usageChartTotal,
} from "../constants/usageConsts";
import { buildProtocolChartOption } from "../constants/protocolConsts";
import iconUsageHeader from "../assets/icons/header_usage.svg";

use([
  CanvasRenderer,
  BarChart,
  BoxplotChart,
  LineChart,
  ScatterChart,
  GridComponent,
  LegendComponent,
  TooltipComponent,
]);

const axiosRef = createAxiosObject();
const urlStringStart = urlStringStartsWith();
const DATE_FILTER_DEBOUNCE_MS = 500;
const DEFAULT_MIN_COUNT = 3;

const today = new Date();
const sixMonthsAgo = new Date(today);
sixMonthsAgo.setMonth(today.getMonth() - 6);

const protocolCharts = [
  { key: "concentration", title: "Library Concentration (ng/µl)" },
  { key: "optical_duplicates", title: "Optical Duplicate Rate (%)" },
];

export default {
  name: "UsageView",
  components: {
    VChart,
    DateInput,
  },
  setup() {
    const usageLoading = ref(true);
    const protocolLoading = ref(false);
    const loading = computed(() => usageLoading.value || protocolLoading.value);
    const startDateString = ref(formatDateForInput(sixMonthsAgo));
    const endDateString = ref(formatDateForInput(today));
    const recordType = ref("all");
    const minCount = ref(DEFAULT_MIN_COUNT);
    const showFilters = ref(false);
    const protocolA = ref("");
    const protocolB = ref("");
    const protocolNames = ref([]);
    const chartData = reactive({});
    const protocolData = reactive({});
    let requestId = 0;
    let protocolRequestId = 0;

    const startDateValid = computed(() => isValidDate(startDateString.value));
    const endDateValid = computed(() => isValidDate(endDateString.value));
    const effectiveMinCount = computed(() =>
      Number.isInteger(minCount.value) && minCount.value >= 1
        ? minCount.value
        : DEFAULT_MIN_COUNT,
    );

    const usageCharts = USAGE_CHARTS;
    const topRowCharts = usageCharts.slice(0, 2);
    const bottomRowCharts = usageCharts.slice(2);

    const chartOptions = computed(() => {
      const options = {};
      usageCharts.forEach((chartDef) => {
        const data = chartData[chartDef.key] || [];
        options[chartDef.key] = buildUsageChartOption(
          chartDef,
          data,
          recordType.value,
        );
      });
      return options;
    });

    const protocolChartOptions = computed(() => {
      const options = {};
      protocolCharts.forEach((chartDef) => {
        options[chartDef.key] = buildProtocolChartOption(
          chartDef,
          (protocolData[chartDef.key] || []).filter(
            (series) => series.values.length > 0,
          ),
        );
      });
      return options;
    });

    function chartHasData(key) {
      const chartDef = usageCharts.find((c) => c.key === key);
      return usageChartTotal(chartDef, chartData[key] || []) > 0;
    }

    function protocolChartHasData(key) {
      return (protocolData[key] || []).some(
        (series) => series.values.length > 0,
      );
    }

    function baseParams() {
      return {
        start: `${startDateString.value}T00:00:00`,
        end: `${endDateString.value}T23:59:59`,
        record_type: recordType.value,
        min_count: effectiveMinCount.value,
      };
    }

    async function fetchProtocolNames() {
      try {
        const response = await axiosRef.get(
          `${urlStringStart}/api/library_protocols/`,
        );
        protocolNames.value = response.data
          .map((p) => p.name)
          .sort((a, b) =>
            a.localeCompare(b, undefined, { sensitivity: "base" }),
          );
      } catch (error) {
        handleError(error);
      }
    }

    async function pickRandomProtocolWithData() {
      const candidates = [...protocolNames.value];
      for (let i = candidates.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [candidates[i], candidates[j]] = [candidates[j], candidates[i]];
      }
      for (const name of candidates) {
        try {
          const response = await axiosRef.get(
            `${urlStringStart}/api/usage/protocol_comparison/`,
            { params: { ...baseParams(), protocols: name } },
          );
          const row = response.data[0];
          if (
            row &&
            row.concentration.length > 0 &&
            row.optical_duplicates.length > 0
          ) {
            protocolA.value = name;
            return;
          }
        } catch (error) {
          handleError(error);
          return;
        }
      }
    }

    async function loadProtocolData() {
      if (!startDateValid.value || !endDateValid.value || !protocolA.value) {
        return;
      }
      const thisRequestId = ++protocolRequestId;
      protocolLoading.value = true;
      const protocols = [protocolA.value];
      if (protocolB.value && protocolB.value !== protocolA.value) {
        protocols.push(protocolB.value);
      }

      try {
        const response = await axiosRef.get(
          `${urlStringStart}/api/usage/protocol_comparison/`,
          { params: { ...baseParams(), protocols: protocols.join(",") } },
        );
        if (thisRequestId !== protocolRequestId) return;
        protocolCharts.forEach((chartDef) => {
          protocolData[chartDef.key] = response.data.map((row) => ({
            protocol: row.protocol,
            values: row[chartDef.key] || [],
          }));
        });
      } catch (error) {
        if (thisRequestId === protocolRequestId) {
          handleError(error);
        }
      } finally {
        if (thisRequestId === protocolRequestId) {
          protocolLoading.value = false;
        }
      }
    }

    async function loadUsageData() {
      if (!startDateValid.value || !endDateValid.value) {
        return;
      }
      const thisRequestId = ++requestId;
      usageLoading.value = true;
      const params = baseParams();

      try {
        const responses = await Promise.all(
          usageCharts.map((chartDef) => {
            const chartParams = chartDef.extraParams
              ? { ...params, ...chartDef.extraParams }
              : params;
            return axiosRef.get(`${urlStringStart}/${chartDef.endpoint}`, {
              params: chartParams,
            });
          }),
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
          usageLoading.value = false;
        }
      }
    }

    const scheduleProtocolReload = useDebounceFn(
      loadProtocolData,
      DATE_FILTER_DEBOUNCE_MS,
    );

    const scheduleReload = useDebounceFn(() => {
      loadUsageData();
      loadProtocolData();
    }, DATE_FILTER_DEBOUNCE_MS);

    useEventListener(document, "click", (event) => {
      const popup = document.getElementById("usageFiltersPopup");
      const button = document.getElementById("toggleUsageFiltersButton");
      if (
        showFilters.value &&
        !popup?.contains(event.target) &&
        !button?.contains(event.target)
      ) {
        showFilters.value = false;
      }
    });

    onMounted(async () => {
      const usagePromise = loadUsageData();
      await fetchProtocolNames();
      await pickRandomProtocolWithData();
      await loadProtocolData();
      await usagePromise;
    });
    onBeforeUnmount(() => {
      scheduleReload.cancel();
      scheduleProtocolReload.cancel();
    });

    return {
      loading,
      startDateString,
      endDateString,
      recordType,
      minCount,
      showFilters,
      protocolA,
      protocolB,
      protocolNames,
      recordTypeOptions: USAGE_RECORD_TYPES,
      startDateValid,
      endDateValid,
      usageCharts,
      topRowCharts,
      bottomRowCharts,
      protocolCharts,
      chartOptions,
      protocolChartOptions,
      chartHasData,
      protocolChartHasData,
      scheduleReload,
      scheduleProtocolReload,
      iconUsageHeader,
    };
  },
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

.filter-item.date-filter-item,
.filter-item.header-filter-item {
  display: flex;
  align-items: center;
  gap: 6px;
  color: white;
  white-space: nowrap;
  margin-bottom: 0;
}

.filter-item.date-filter-item label,
.filter-item.header-filter-item label {
  display: inline;
  padding: 0;
  margin: 0;
  border: none;
  background-color: transparent;
  font-weight: normal;
  color: white;
}

.filter-item.date-filter-item input,
.filter-item.date-filter-item select,
.filter-item.header-filter-item select {
  height: var(--header-control-height);
  font-size: var(--header-control-font-size);
  border-radius: 6px;
  border: 1px solid #d8d8d8;
  padding: 0 8px;
  width: auto;
}

.filter-item.header-filter-item select {
  max-width: 220px;
}

.filter-item.date-filter-item input[type="number"] {
  width: 70px;
}

.filter-item.date-filter-item .invalid-date {
  border-color: #dc3545;
}

.button-popup-container.statistics-filters-popup {
  left: auto;
  right: 0;
  width: 260px;
}

:deep(.date-input-panel) {
  left: auto;
  right: 0;
  width: 190px;
}

.sticky-actions {
  flex-shrink: 0;
}

.button-popup-wrapper {
  flex: 0 0 auto;
  min-width: max-content;
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

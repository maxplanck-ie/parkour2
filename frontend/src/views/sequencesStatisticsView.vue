<template>
  <div class="statistics-page">
    <div v-if="loading || reportLoading" class="loading-overlay">
      <div class="spinner"></div>
      <p>
        {{ reportLoading ? "Preparing report..." : "Loading Sequence Statistics..." }}
      </p>
    </div>

    <div class="header">
      <font-awesome-icon
        icon="fa-solid fa-file-lines"
        class="statistics-header-icon"
      />
      <div class="header-title">Sequence Statistics</div>

      <div class="sticky-actions">
        <div class="search-bar">
          <input v-model="searchQuery" type="text" placeholder="Search" />
          <font-awesome-icon
            icon="fa-solid fa-magnifying-glass"
            style="color: darkgrey"
          />
        </div>

        <div class="button-popup-wrapper">
          <button
            id="toggleSequencesAdvancedFiltersButton"
            class="header-button"
            @click="toggleAdvancedFilters"
          >
            <font-awesome-icon icon="fa-solid fa-filter" />
            <span>Advanced Filters</span>
          </button>
          <div
            v-if="showAdvancedFilters"
            id="sequencesAdvancedFiltersPopup"
            class="button-popup-container statistics-filters-popup"
          >
            <div class="filter-item date-filter-item">
              <label for="sequencesStartDate">From</label>
              <input
                id="sequencesStartDate"
                v-model="startDateString"
                :class="{ 'invalid-date': !startDateValid }"
                type="date"
              />
            </div>
            <div class="filter-item date-filter-item">
              <label for="sequencesEndDate">To</label>
              <input
                id="sequencesEndDate"
                v-model="endDateString"
                :class="{ 'invalid-date': !endDateValid }"
                type="date"
              />
            </div>
            <div class="filter-item">
              <label for="sequencesSequencer">Sequencer</label>
              <select id="sequencesSequencer" v-model="filters.sequencer">
                <option value="">All Sequencers</option>
                <option v-for="value in sequencerOptions" :key="value">
                  {{ value }}
                </option>
              </select>
            </div>
            <div class="filter-item">
              <label for="sequencesProtocol">Library Protocol</label>
              <select id="sequencesProtocol" v-model="filters.protocol">
                <option value="">All Library Protocols</option>
                <option v-for="value in protocolOptions" :key="value">
                  {{ value }}
                </option>
              </select>
            </div>
            <div class="filter-item">
              <label for="sequencesAnalysisType">Analysis Type</label>
              <select id="sequencesAnalysisType" v-model="filters.analysisType">
                <option value="">All Analysis Types</option>
                <option v-for="value in analysisTypeOptions" :key="value">
                  {{ value }}
                </option>
              </select>
            </div>
            <button class="reset-button" @click="resetAdvancedFilters">
              Reset Filters
            </button>
          </div>
        </div>

        <div class="button-popup-wrapper">
          <button
            id="toggleSequencesSelectColumnsButton"
            class="header-button"
            @click="toggleSelectColumns"
          >
            <font-awesome-icon icon="fa-solid fa-columns" />
            <span>Select Columns</span>
          </button>
          <div
            v-if="showSelectColumns"
            id="sequencesSelectColumnsPopup"
            class="button-popup-container statistics-columns-popup"
          >
            <ul>
              <li
                v-for="column in selectableColumns"
                :key="column.field"
              >
                <label>
                  <input
                    type="checkbox"
                    :checked="column.visible !== false"
                    @change="toggleColumnVisibility(column)"
                  />
                  <span>{{ column.title }}</span>
                </label>
              </li>
            </ul>
            <button class="reset-button" @click="resetColumnVisibility">
              Reset Visibility Settings
            </button>
            <button class="reset-button" @click="resetColumnWidths">
              Reset Width Settings
            </button>
          </div>
        </div>

        <button class="header-button" @click="downloadReport">
          <font-awesome-icon icon="fa-solid fa-download" />
          <span>Download Report</span>
        </button>
      </div>
    </div>

    <div class="statistics-table-container">
      <LiteTabulatorTable
        ref="tableRef"
        table-id="sequencesStatisticsTable"
        :row-data="filteredRows"
        :column-defs="columnsList"
        group-by="flowcell_group"
        :group-sort="{ field: 'flowcell_group', order: 'desc' }"
        :group-start-open="false"
        :table-options="tableOptions"
      />
    </div>
  </div>
</template>

<script>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import { saveAs } from "file-saver";
import LiteTabulatorTable from "../components/TabulatorTableLite.vue";
import {
  applySequencesStatisticsColumnSettings,
  formatSequencesStatisticsDate,
  sequencesStatisticsColumnDefs,
  sequencesStatisticsGroupHeader,
  sequencesStatisticsRowMatchesSearch,
  uniqueSequencesStatisticsValues
} from "../constants/sequencesStatisticsConsts";
import {
  createAxiosObject,
  formatDateForInput,
  handleError,
  isValidDate,
  showNotification,
  urlStringStartsWith
} from "../utilities/utilityFunctions";

const VISIBILITY_KEY = "sequencesStatisticsColumnVisibility";
const WIDTHS_KEY = "sequencesStatisticsColumnWidths";
const axiosRef = createAxiosObject();
const urlStringStart = urlStringStartsWith();
const today = new Date();
const tenYearsAgo = new Date(today);
tenYearsAgo.setFullYear(today.getFullYear() - 10);

export default {
  name: "SequencesStatistics",
  components: {
    LiteTabulatorTable
  },
  setup() {
const tableRef = ref(null);
const loading = ref(true);
const reportLoading = ref(false);
const rows = ref([]);
const columnsList = ref([]);
const searchQuery = ref("");
const startDateString = ref(formatDateForInput(tenYearsAgo));
const endDateString = ref(formatDateForInput(today));
const startDateValid = ref(true);
const endDateValid = ref(true);
const showAdvancedFilters = ref(false);
const showSelectColumns = ref(false);
const filters = reactive({
  sequencer: "",
  protocol: "",
  analysisType: ""
});
let dateTimer = null;

const tableOptions = {
  index: "row_id",
  placeholder: "No sequence statistics to show.",
  initialSort: [{ column: "barcode", dir: "asc" }],
  groupHeader: sequencesStatisticsGroupHeader,
  handleColumnResized: (column) => {
    const field = column.getField();
    if (!field) return;
    const widths = JSON.parse(localStorage.getItem(WIDTHS_KEY) || "{}");
    localStorage.setItem(
      WIDTHS_KEY,
      JSON.stringify({ ...widths, [field]: column.getWidth() })
    );
  },
  handleColumnVisibilityChanged: (field, visible) => {
    if (!field) return;
    const visibility = JSON.parse(
      localStorage.getItem(VISIBILITY_KEY) || "{}"
    );
    localStorage.setItem(
      VISIBILITY_KEY,
      JSON.stringify({ ...visibility, [field]: visible })
    );
    const definition = columnsList.value.find((column) => column.field === field);
    if (definition) definition.visible = visible;
  }
};

const selectableColumns = computed(() =>
  columnsList.value.filter((column) => column.field !== "selected")
);
const sequencerOptions = computed(() =>
  uniqueSequencesStatisticsValues(rows.value, "sequencer")
);
const protocolOptions = computed(() =>
  uniqueSequencesStatisticsValues(rows.value, "library_protocol")
);
const analysisTypeOptions = computed(() =>
  uniqueSequencesStatisticsValues(rows.value, "library_type")
);
const filteredRows = computed(() =>
  rows.value.filter(
    (row) =>
      sequencesStatisticsRowMatchesSearch(row, searchQuery.value) &&
      (!filters.sequencer || row.sequencer === filters.sequencer) &&
      (!filters.protocol || row.library_protocol === filters.protocol) &&
      (!filters.analysisType || row.library_type === filters.analysisType)
  )
);

function setColumns() {
  columnsList.value = applySequencesStatisticsColumnSettings(
    sequencesStatisticsColumnDefs(),
    VISIBILITY_KEY,
    WIDTHS_KEY
  );
  const selectionColumn = columnsList.value.find(
    (column) => column.field === "selected"
  );
  if (selectionColumn) selectionColumn.visible = true;
}

async function fetchRows() {
  if (!validateDateRange()) return;
  loading.value = true;
  try {
    const response = await axiosRef.get(
      `${urlStringStart}/api/sequences_statistics/`,
      {
        params: {
          start: `${startDateString.value}T00:00:00`,
          end: `${endDateString.value}T23:59:59`
        }
      }
    );
    rows.value = response.data.map((row, index) => {
      const requested = Number(row.reads_pf_requested);
      const sequenced = Number(row.reads_pf_sequenced);
      const readsPercent =
        Number.isFinite(requested) &&
        requested > 0 &&
        Number.isFinite(sequenced)
          ? (sequenced / 1000000 / requested) * 100
          : "";
      return {
        ...row,
        selected: false,
        row_id: `${row.pk}_${row.barcode || index}`,
        lane_display: Array.isArray(row.lane) ? row.lane.join(", ") : row.lane,
        reads_percent: readsPercent,
        flowcell_group: `${row.pk}_${row.flowcell_id || ""}`,
        create_time_display: formatSequencesStatisticsDate(row.create_time)
      };
    });
    setColumns();
  } catch (error) {
    handleError(error);
    rows.value = [];
  } finally {
    loading.value = false;
  }
}

function validateDateRange() {
  startDateValid.value = isValidDate(startDateString.value);
  endDateValid.value = isValidDate(endDateString.value);
  if (!startDateValid.value || !endDateValid.value) return false;
  if (startDateString.value > endDateString.value) {
    startDateValid.value = false;
    endDateValid.value = false;
    showNotification("Start date must precede end date.", "warning");
    return false;
  }
  return true;
}

function scheduleDateReload() {
  clearTimeout(dateTimer);
  dateTimer = setTimeout(fetchRows, 500);
}

function toggleAdvancedFilters() {
  showAdvancedFilters.value = !showAdvancedFilters.value;
  if (showAdvancedFilters.value) showSelectColumns.value = false;
}

function toggleSelectColumns() {
  showSelectColumns.value = !showSelectColumns.value;
  if (showSelectColumns.value) showAdvancedFilters.value = false;
}

function resetAdvancedFilters() {
  Object.assign(filters, { sequencer: "", protocol: "", analysisType: "" });
}

function toggleColumnVisibility(column) {
  tableRef.value?.getTable()?.toggleColumn(column.field);
}

async function resetColumnVisibility() {
  localStorage.removeItem(VISIBILITY_KEY);
  setColumns();
  await nextTick();
}

async function resetColumnWidths() {
  localStorage.removeItem(WIDTHS_KEY);
  setColumns();
  await nextTick();
}

async function downloadReport() {
  const selectedBarcodes = (tableRef.value?.getTable()?.getData() || [])
    .filter((row) => row.selected && row.barcode)
    .map((row) => row.barcode);
  if (!selectedBarcodes.length) {
    showNotification("You did not select any items.", "warning");
    return;
  }
  reportLoading.value = true;
  try {
    const response = await axiosRef.post(
      `${urlStringStart}/api/sequences_statistics/download_report/`,
      { barcodes: JSON.stringify(selectedBarcodes) },
      { responseType: "blob" }
    );
    saveAs(response.data, "Sequences_Statistics_Report.xls");
  } catch (error) {
    handleError(error);
  } finally {
    reportLoading.value = false;
  }
}

function handleDocumentClick(event) {
  const advancedPopup = document.getElementById(
    "sequencesAdvancedFiltersPopup"
  );
  const advancedButton = document.getElementById(
    "toggleSequencesAdvancedFiltersButton"
  );
  const columnsPopup = document.getElementById("sequencesSelectColumnsPopup");
  const columnsButton = document.getElementById(
    "toggleSequencesSelectColumnsButton"
  );
  if (
    showAdvancedFilters.value &&
    !advancedPopup?.contains(event.target) &&
    !advancedButton?.contains(event.target)
  ) {
    showAdvancedFilters.value = false;
  }
  if (
    showSelectColumns.value &&
    !columnsPopup?.contains(event.target) &&
    !columnsButton?.contains(event.target)
  ) {
    showSelectColumns.value = false;
  }
}

function handleKeyDown(event) {
  if (event.key !== "Escape") return;
  showAdvancedFilters.value = false;
  showSelectColumns.value = false;
}

watch([startDateString, endDateString], scheduleDateReload);

onMounted(() => {
  setColumns();
  fetchRows();
  document.addEventListener("click", handleDocumentClick);
  document.addEventListener("keydown", handleKeyDown);
});

onBeforeUnmount(() => {
  clearTimeout(dateTimer);
  document.removeEventListener("click", handleDocumentClick);
  document.removeEventListener("keydown", handleKeyDown);
});

    return {
      tableRef,
      loading,
      reportLoading,
      columnsList,
      searchQuery,
      startDateString,
      endDateString,
      startDateValid,
      endDateValid,
      showAdvancedFilters,
      showSelectColumns,
      filters,
      tableOptions,
      selectableColumns,
      sequencerOptions,
      protocolOptions,
      analysisTypeOptions,
      filteredRows,
      toggleAdvancedFilters,
      toggleSelectColumns,
      resetAdvancedFilters,
      toggleColumnVisibility,
      resetColumnVisibility,
      resetColumnWidths,
      downloadReport
    };
  }
};
</script>

<style scoped>
.statistics-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  padding: 10px;
  overflow: hidden;
  background-color: #f4f4f4;
}

.statistics-header-icon {
  flex: 0 0 auto;
  width: 34px;
  height: 34px;
  margin-right: 12px;
  color: white;
}

.statistics-table-container {
  flex: 1 1 auto;
  min-height: 0;
}

.statistics-filters-popup {
  left: -80px;
  width: 290px;
  max-height: calc(100vh - 100px);
  overflow-y: auto;
}

.statistics-columns-popup {
  left: -55px;
  width: 270px;
  max-height: calc(100vh - 100px);
  overflow-y: auto;
}

.statistics-columns-popup ul {
  padding: 0;
  margin: 0 0 8px;
}

.statistics-columns-popup li {
  list-style: none;
}

.statistics-columns-popup .reset-button {
  width: 100%;
  margin-bottom: 6px;
}

.date-filter-item input[type="date"] {
  width: 100%;
  height: 34px;
  padding: 4px 8px;
  border: 1px solid #aaa;
  border-radius: 4px;
}

@media (max-width: 1450px) {
  .search-bar {
    width: 320px;
  }

  .header-button span {
    display: none;
  }
}
</style>

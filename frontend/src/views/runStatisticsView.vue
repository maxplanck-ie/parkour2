<template>
  <div class="statistics-page">
    <div v-if="loading" class="loading-overlay">
      <div class="spinner"></div>
      <p>Loading <strong>Run Statistics</strong>...</p>
    </div>

    <div class="header">
      <font-awesome-icon
        icon="fa-solid fa-table-cells"
        class="statistics-header-icon"
      />
      <div class="header-title">Run Statistics</div>

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
            id="toggleAdvancedFiltersButton"
            class="header-button"
            @click="toggleAdvancedFilters"
          >
            <font-awesome-icon icon="fa-solid fa-filter" />
            <span>Advanced Filters</span>
          </button>
          <div
            v-if="showAdvancedFilters"
            id="advancedFiltersPopup"
            class="button-popup-container statistics-filters-popup"
          >
            <div class="filter-item date-filter-item">
              <label for="runsStartDate">From</label>
              <input
                id="runsStartDate"
                v-model="startDateString"
                :class="{ 'invalid-date': !startDateValid }"
                type="date"
              />
            </div>
            <div class="filter-item date-filter-item">
              <label for="runsEndDate">To</label>
              <input
                id="runsEndDate"
                v-model="endDateString"
                :class="{ 'invalid-date': !endDateValid }"
                type="date"
              />
            </div>
            <div class="filter-item">
              <label for="runsSequencer">Sequencer</label>
              <select id="runsSequencer" v-model="filters.sequencer">
                <option value="">All Sequencers</option>
                <option v-for="value in sequencerOptions" :key="value">
                  {{ value }}
                </option>
              </select>
            </div>
            <div class="filter-item">
              <label for="runsReadLength">Read Length</label>
              <select id="runsReadLength" v-model="filters.readLength">
                <option value="">All Read Lengths</option>
                <option v-for="value in readLengthOptions" :key="value">
                  {{ value }}
                </option>
              </select>
            </div>
            <div class="filter-item">
              <label for="runsPreparation">Preparation Method</label>
              <select id="runsPreparation" v-model="filters.preparation">
                <option value="">All Preparation Methods</option>
                <option v-for="value in preparationOptions" :key="value">
                  {{ value }}
                </option>
              </select>
            </div>
            <div class="filter-item">
              <label for="runsAnalysisType">Analysis Type</label>
              <select id="runsAnalysisType" v-model="filters.analysisType">
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
            id="toggleSelectColumnsButton"
            class="header-button"
            @click="toggleSelectColumns"
          >
            <font-awesome-icon icon="fa-solid fa-columns" />
            <span>Select Columns</span>
          </button>
          <div
            v-if="showSelectColumns"
            id="selectColumnsPopup"
            class="button-popup-container statistics-columns-popup"
          >
            <ul>
              <li v-for="column in columnsList" :key="column.field">
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
      </div>
    </div>

    <div class="statistics-table-container">
      <LiteTabulatorTable
        ref="tableRef"
        table-id="runStatisticsTable"
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
import LiteTabulatorTable from "../components/TabulatorTableLite.vue";
import {
  applyRunStatisticsColumnSettings,
  formatRunStatisticsDate,
  runStatisticsColumnDefs,
  runStatisticsGroupHeader,
  runStatisticsRowMatchesSearch,
  uniqueRunStatisticsValues
} from "../constants/runStatisticsConsts";
import {
  createAxiosObject,
  formatDateForInput,
  handleError,
  isValidDate,
  showNotification,
  urlStringStartsWith
} from "../utilities/utilityFunctions";

const VISIBILITY_KEY = "runStatisticsColumnVisibility";
const WIDTHS_KEY = "runStatisticsColumnWidths";
const axiosRef = createAxiosObject();
const urlStringStart = urlStringStartsWith();
const today = new Date();
const tenYearsAgo = new Date(today);
tenYearsAgo.setFullYear(today.getFullYear() - 10);

export default {
  name: "RunStatistics",
  components: {
    LiteTabulatorTable
  },
  setup() {
const tableRef = ref(null);
const loading = ref(true);
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
  readLength: "",
  preparation: "",
  analysisType: ""
});
let dateTimer = null;

const tableOptions = {
  index: "row_id",
  placeholder: "No run statistics to show.",
  initialSort: [{ column: "name", dir: "asc" }],
  groupHeader: runStatisticsGroupHeader,
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

const sequencerOptions = computed(() =>
  uniqueRunStatisticsValues(rows.value, "sequencer")
);
const readLengthOptions = computed(() =>
  uniqueRunStatisticsValues(rows.value, "read_length")
);
const preparationOptions = computed(() =>
  uniqueRunStatisticsValues(rows.value, "library_preparation")
);
const analysisTypeOptions = computed(() =>
  uniqueRunStatisticsValues(rows.value, "library_type")
);

const filteredRows = computed(() =>
  rows.value.filter(
    (row) =>
      runStatisticsRowMatchesSearch(row, searchQuery.value) &&
      (!filters.sequencer || row.sequencer === filters.sequencer) &&
      (!filters.readLength || row.read_length === filters.readLength) &&
      (!filters.preparation ||
        row.library_preparation === filters.preparation) &&
      (!filters.analysisType || row.library_type === filters.analysisType)
  )
);

function setColumns() {
  columnsList.value = applyRunStatisticsColumnSettings(
    runStatisticsColumnDefs(),
    VISIBILITY_KEY,
    WIDTHS_KEY
  );
}

async function fetchRows() {
  if (!validateDateRange()) return;
  loading.value = true;
  try {
    const response = await axiosRef.get(`${urlStringStart}/api/run_statistics/`, {
      params: {
        start: `${startDateString.value}T00:00:00`,
        end: `${endDateString.value}T23:59:59`
      }
    });
    rows.value = response.data.map((row, index) => ({
      ...row,
      row_id: `${row.pk}_${row.name || index}`,
      flowcell_group: `${row.pk}_${row.flowcell_id || ""}`,
      create_time_display: formatRunStatisticsDate(row.create_time)
    }));
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
  Object.assign(filters, {
    sequencer: "",
    readLength: "",
    preparation: "",
    analysisType: ""
  });
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

function handleDocumentClick(event) {
  const advancedPopup = document.getElementById("advancedFiltersPopup");
  const advancedButton = document.getElementById("toggleAdvancedFiltersButton");
  const columnsPopup = document.getElementById("selectColumnsPopup");
  const columnsButton = document.getElementById("toggleSelectColumnsButton");
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
      sequencerOptions,
      readLengthOptions,
      preparationOptions,
      analysisTypeOptions,
      filteredRows,
      toggleAdvancedFilters,
      toggleSelectColumns,
      resetAdvancedFilters,
      toggleColumnVisibility,
      resetColumnVisibility,
      resetColumnWidths
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

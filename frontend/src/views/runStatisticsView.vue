<template>
  <div class="parent-container">
    <div v-if="loading" class="loading-overlay">
      <div class="spinner"></div>
      <p>Loading <strong>Run Statistics</strong>...</p>
    </div>

    <div class="header">
      <img
        :src="iconStatisticsHeader"
        alt="Run Statistics"
        class="statistics-header-icon"
      />
      <div class="header-title">Run Statistics</div>

      <div class="sticky-actions">
        <div class="search-bar">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search"
            @keyup.enter="handleSearchAction"
          />
          <font-awesome-icon
            icon="fa-solid fa-magnifying-glass"
            style="color: darkgrey; cursor: pointer"
            @click="handleSearchAction"
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
                @input="handleDateChange('start', $event.target.value)"
              />
            </div>
            <div class="filter-item date-filter-item">
              <label for="runsEndDate">To</label>
              <input
                id="runsEndDate"
                v-model="endDateString"
                :class="{ 'invalid-date': !endDateValid }"
                type="date"
                @input="handleDateChange('end', $event.target.value)"
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
              <li v-for="column in selectableColumns" :key="column.field">
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

        <button
          class="header-button"
          id="openRunStatisticsExportPopupButton"
          @click="handleExportClick"
        >
          <font-awesome-icon icon="fa-solid fa-file-excel" />
          <span>Export to Excel</span>
        </button>
      </div>
    </div>

    <div class="table-container">
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

    <div
      v-if="showExportPopup"
      class="popup-overlay"
      @dragover.prevent="handleDragOver"
      @drop="handleDrop"
      @dragenter="handleDragEnter"
      @dragleave="handleDragLeave"
      :class="{ 'drag-over': isDragOver }"
    >
      <div class="drag-drop-indicator">
        <div
          style="
            display: flex;
            justify-content: center;
            align-items: center;
            height: 200px;
          "
        >
          <p>
            Drop <span style="font-weight: bold">XLSX or XLSM file</span> here
            to upload as <span style="font-weight: bold">template</span>
          </p>
        </div>
      </div>
      <div
        v-if="!isDragOver"
        class="popup-container statistics-export-popup"
        :style="{ width: '670px', height: '500px' }"
      >
        <div class="popup-header">
          <span class="popup-title">Export Options</span>
          <span
            class="popup-info-button"
            @mouseover="showExportHelpTooltip = true"
            @mouseleave="showExportHelpTooltip = false"
          >
            ?
            <div v-if="showExportHelpTooltip" class="tooltip-box">
              <div class="tooltip-scroll">
                <div class="tooltip-title">Export Guide</div>
                <p class="tooltip-intro">
                  Use export when you want to download the table data to Excel.
                  You can export only the rows you selected, or the full
                  filtered result set for the current page.
                </p>
                <section class="tooltip-section">
                  <div class="tooltip-section-title">Basic export choices</div>
                  <ul class="tooltip-list">
                    <li>
                      <strong>Export selected</strong> downloads only the rows
                      you selected in the table.
                    </li>
                    <li>
                      <strong>Export all</strong> downloads the full result set
                      for the current export view.
                    </li>
                    <li>
                      Use search and filters first if you want to narrow the
                      exported dataset.
                    </li>
                  </ul>
                </section>
                <section class="tooltip-section">
                  <div class="tooltip-section-title">
                    How template files work
                  </div>
                  <ol class="tooltip-list tooltip-steps">
                    <li>
                      Start by exporting with
                      <strong>Export without any additional sheets</strong>.
                      This creates the base Excel file and keeps the original
                      <strong>Parkour</strong> sheet.
                    </li>
                    <li>
                      Open that file in Excel and add your own extra sheets for
                      notes, calculations, or reporting.
                    </li>
                    <li>
                      Upload the edited file here as a reusable template. It
                      will appear in the list of available templates.
                    </li>
                    <li>
                      Later, when you export using that template, Parkour
                      replaces only the <strong>Parkour</strong> sheet with
                      fresh data and keeps your extra sheets unchanged.
                    </li>
                  </ol>
                </section>
                <section class="tooltip-section">
                  <div class="tooltip-section-title">When to use this</div>
                  <ul class="tooltip-list">
                    <li>
                      Download a snapshot of the current data for review or
                      sharing.
                    </li>
                    <li>
                      Reuse a prepared Excel layout with additional custom
                      sheets.
                    </li>
                    <li>
                      Keep Parkour data up to date inside your existing
                      reporting workbook.
                    </li>
                  </ul>
                </section>
              </div>
            </div>
          </span>
          <button class="popup-close-button" @click="closeExportPopup">
            &times;
          </button>
        </div>
        <div class="popup-body">
          <div class="export-section">
            <div style="font-weight: bold; margin-bottom: 8px">
              Export Options:
            </div>
            <div class="export-selection-radio-option">
              <input
                id="run-export-selected"
                v-model="exportSelection"
                type="radio"
                value="selected"
                :disabled="!hasSelectedRows"
              />
              <label
                for="run-export-selected"
                :class="{ disabled: !hasSelectedRows }"
              >
                Export selected run statistics
              </label>
            </div>
            <div class="export-selection-radio-option">
              <input
                id="run-export-all"
                v-model="exportSelection"
                type="radio"
                value="all"
              />
              <label for="run-export-all">Export all run statistics</label>
            </div>
          </div>
          <div class="export-section" style="height: 100%">
            <div style="font-weight: bold; margin-bottom: 8px">
              Upload additional excel sheet templates to append:
            </div>
            <div class="file-list-section">
              <div class="file-item">
                <div class="file-info">
                  <img
                    :src="iconExportTemplateFile"
                    alt="Export without any additional sheets"
                    width="24"
                    height="24"
                    style="display: block"
                  />
                  <span>Export without any additional sheets</span>
                </div>
                <div class="file-actions">
                  <div
                    class="file-actions-radio-button"
                    style="border: none; margin-right: 5px"
                  >
                    <input
                      id="run-without-file"
                      v-model="selectedFile"
                      type="radio"
                      title="Select"
                      value="without-file"
                    />
                  </div>
                </div>
              </div>
              <div
                v-for="(file, index) in uploadedExportTemplates"
                :key="index"
                class="file-item"
              >
                <div class="file-info">
                  <img
                    :src="iconExportTemplateFileLines"
                    :alt="file.name"
                    width="24"
                    height="24"
                    style="display: block"
                  />
                  <span>{{ file.name }}</span>
                </div>
                <div class="file-actions">
                  <button
                    class="download-button"
                    title="Download Original File"
                    @click.stop="downloadExportTemplate(file)"
                  >
                    <img
                      :src="iconExportDownload"
                      alt="Download"
                      width="24"
                      height="24"
                      style="display: block"
                    />
                  </button>
                  <button
                    class="remove-button"
                    title="Remove File"
                    @click.stop="removeExportTemplate(index)"
                  >
                    <img
                      :src="iconExportRemove"
                      alt="Remove"
                      width="24"
                      height="24"
                      style="display: block"
                    />
                  </button>
                  <div class="file-actions-radio-button">
                    <input
                      :id="'run-file-radio-' + index"
                      v-model="selectedFile"
                      type="radio"
                      title="Select File"
                      :value="file"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="popup-footer">
          <div class="file-upload-section">
            <label
              for="run-file-upload"
              class="file-upload-label"
              title="Upload additional sheet to append to the exported sheet."
            >
              <img
                :src="iconExportUpload"
                alt="Upload"
                width="24"
                height="24"
                style="display: block; margin-right: 4px"
              />
              <span>Upload</span>
            </label>
            <input
              id="run-file-upload"
              type="file"
              accept=".xlsx,.xlsm"
              style="display: none"
              @change="uploadExportTemplate"
            />
          </div>
          <button class="popup-button yes-button" @click="handleExport">
            OK
          </button>
          <button class="popup-button" @click="closeExportPopup">
            Cancel
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref } from "vue";
import { saveAs } from "file-saver";
import LiteTabulatorTable from "../components/TabulatorTableLite.vue";
import {
  formatRunStatisticsDate,
  runStatisticsColumnDefs,
  runStatisticsExportColumns,
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
  urlStringStartsWith,
  createExcelExportBlob,
  buildExcelExportFilename,
  buildExcelDownloadFilename,
  isSupportedExcelTemplateFile
} from "../utilities/utilityFunctions";
import iconExportTemplateFile from "../assets/icons/export_template.svg";
import iconExportTemplateFileLines from "../assets/icons/export_template_lines.svg";
import iconExportDownload from "../assets/icons/export_download.svg";
import iconExportRemove from "../assets/icons/export_remove.svg";
import iconExportUpload from "../assets/icons/export_upload.svg";
import iconStatisticsHeader from "../assets/icons/header_statistics.svg";

const VISIBILITY_KEY = "runStatisticsColumnVisibility";
const WIDTHS_KEY = "runStatisticsColumnWidthsV2";
const DATE_FILTER_DEBOUNCE_MS = 500;
const axiosRef = createAxiosObject();
const urlStringStart = urlStringStartsWith();
const TEMPLATE_API_URL = `${urlStringStart}/api/run-statistics-templates`;
const today = new Date();
const twoMonthsAgo = new Date(today);
twoMonthsAgo.setMonth(today.getMonth() - 2);

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
const appliedSearchQuery = ref("");
const showExportPopup = ref(false);
const showExportHelpTooltip = ref(false);
const isDragOver = ref(false);
const uploadedExportTemplates = ref([]);
const selectedFile = ref("without-file");
const exportSelection = ref("selected");
const hasSelectedRows = ref(false);
const startDateString = ref(formatDateForInput(twoMonthsAgo));
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
  groupContextMenu: [
    {
      label: "Select All",
      action: (event, group) => setGroupSelection(group.getKey(), true)
    },
    {
      label: "Unselect All",
      action: (event, group) => setGroupSelection(group.getKey(), false)
    }
  ],
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
const selectableColumns = computed(() =>
  columnsList.value.filter((column) => column.field !== "selected")
);

const filteredRows = computed(() =>
  rows.value.filter(
    (row) =>
      runStatisticsRowMatchesSearch(row, appliedSearchQuery.value) &&
      (!filters.sequencer || row.sequencer === filters.sequencer) &&
      (!filters.readLength || row.read_length === filters.readLength) &&
      (!filters.preparation ||
        row.library_preparation === filters.preparation) &&
      (!filters.analysisType || row.library_type === filters.analysisType)
  )
);

function setColumns() {
  const storedVisibility = JSON.parse(
    localStorage.getItem(VISIBILITY_KEY) || "{}"
  );
  const storedWidths = JSON.parse(localStorage.getItem(WIDTHS_KEY) || "{}");

  const applySettings = (columns) => {
    return columns.map((column) => {
      if (column.field) {
        if (Object.prototype.hasOwnProperty.call(storedWidths, column.field)) {
          column.width = storedWidths[column.field];
          if (column.minWidth && column.width < column.minWidth) {
            column.width = column.minWidth;
          }
        }
        if (
          Object.prototype.hasOwnProperty.call(storedVisibility, column.field)
        ) {
          column.visible = storedVisibility[column.field];
        } else {
          column.visible = column.visible ?? true;
        }
      }
      return column;
    });
  };

  columnsList.value = applySettings(runStatisticsColumnDefs(updateSourceSelection));
  const selectionColumn = columnsList.value.find(
    (column) => column.field === "selected"
  );
  if (selectionColumn) selectionColumn.visible = true;
  const hasVisibleDataColumn = columnsList.value.some(
    (column) => column.field !== "selected" && column.visible !== false
  );
  if (!hasVisibleDataColumn) {
    columnsList.value.forEach((column) => {
      if (column.field !== "selected") column.visible = true;
    });
    localStorage.removeItem(VISIBILITY_KEY);
  }
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
      selected: false,
      row_id: `${row.pk}_${row.name || index}`,
      flowcell_group: `${row.pk}_${row.flowcell_id || ""}`,
      create_time_display: formatRunStatisticsDate(row.create_time),
      reads_pf_m:
        row.reads_pf === null || row.reads_pf === undefined || row.reads_pf === ""
          ? ""
          : Number(row.reads_pf) / 1000000
    }));
  } catch (error) {
    handleError(error);
    rows.value = [];
  } finally {
    loading.value = false;
  }
}

function updateSourceSelection(rowId, selected) {
  const row = rows.value.find((item) => item.row_id === rowId);
  if (row) row.selected = selected;
}

function setGroupSelection(groupKey, selected) {
  rows.value.forEach((row) => {
    if (row.flowcell_group === groupKey) row.selected = selected;
  });
  const group = tableRef.value
    ?.getTable()
    ?.getGroups()
    .find((item) => item.getKey() === groupKey);
  if (group && group._group && !group._group.visible) {
    group.getElement()?.click();
  }
  group?.getRows().forEach((row) => row.update({ selected }));
}

function handleGroupButtonClick(event, groupValue, action) {
  event?.stopPropagation?.();
  if (action === "selectAll") {
    setGroupSelection(groupValue, true);
    return;
  }
  if (action === "deselectAll") {
    setGroupSelection(groupValue, false);
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
  dateTimer = setTimeout(fetchRows, DATE_FILTER_DEBOUNCE_MS);
}

function handleDateChange(type, value) {
  if (type === "start") {
    startDateString.value = value;
    startDateValid.value = isValidDate(value);
  } else {
    endDateString.value = value;
    endDateValid.value = isValidDate(value);
  }
  if (!startDateValid.value || !endDateValid.value) return;
  scheduleDateReload();
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

function handleExportClick() {
  hasSelectedRows.value = rows.value.some((row) => row.selected);
  exportSelection.value = hasSelectedRows.value ? "selected" : "all";
  showExportPopup.value = true;
  showExportHelpTooltip.value = false;
  isDragOver.value = false;
  showAdvancedFilters.value = false;
  showSelectColumns.value = false;
}

function closeExportPopup() {
  showExportPopup.value = false;
  showExportHelpTooltip.value = false;
  isDragOver.value = false;
  selectedFile.value = "without-file";
}

async function fetchExportTemplates() {
  try {
    const response = await axiosRef.get(`${TEMPLATE_API_URL}/`);
    uploadedExportTemplates.value = response.data;
  } catch (error) {
    handleError(error);
  }
}

async function uploadExportTemplate(event) {
  const file = event.target.files?.[0];
  await processUploadedFile(file);
  event.target.value = "";
}

async function downloadExportTemplate(file) {
  if (!file?.id) return;
  try {
    const response = await axiosRef.get(`${TEMPLATE_API_URL}/${file.id}/download/`, {
      responseType: "blob"
    });
    saveAs(
      response.data,
      buildExcelDownloadFilename("RunStatistics", file.name, response.data?.type)
    );
  } catch {
    showNotification("File download failed.", "error");
  }
}

async function removeExportTemplate(index) {
  const file = uploadedExportTemplates.value[index];
  if (!file?.id) return;
  try {
    await axiosRef.delete(`${TEMPLATE_API_URL}/${file.id}/remove/`);
    uploadedExportTemplates.value.splice(index, 1);
    showNotification("File removed successfully.", "success");
  } catch {
    showNotification("File removal failed.", "error");
  } finally {
    selectedFile.value = "without-file";
  }
}

function handleDragOver(event) {
  event.preventDefault();
  isDragOver.value = true;
}

function handleDragEnter(event) {
  event.preventDefault();
  isDragOver.value = true;
}

function handleDragLeave(event) {
  if (!event.currentTarget.contains(event.relatedTarget)) {
    isDragOver.value = false;
  }
}

async function handleDrop(event) {
  event.preventDefault();
  isDragOver.value = false;
  const files = event.dataTransfer.files;
  if (files.length > 1) {
    showNotification("Upload only one XLSX or XLSM file.", "error");
    return;
  }
  await processUploadedFile(files[0]);
}

async function processUploadedFile(file) {
  if (!file) return;
  if (!isSupportedExcelTemplateFile(file)) {
    showNotification("Upload a valid XLSX or XLSM file.", "error");
    return;
  }
  const formData = new FormData();
  formData.append("file", file);
  try {
    await axiosRef.post(`${TEMPLATE_API_URL}/upload/`, formData, {
      headers: {
        "Content-Type": "multipart/form-data"
      }
    });
    showNotification("File uploaded successfully.", "success");
    await fetchExportTemplates();
  } catch {
    showNotification("File upload failed.", "error");
  } finally {
    selectedFile.value = "without-file";
  }
}

async function handleExport() {
  const exportRows = getRowsForExport();
  if (!exportRows.length) {
    showNotification("No run statistics available for export.", "warning");
    return;
  }
  try {
    const formattedDate = new Date().toISOString().split("T")[0];
    const selectedTemplate =
      selectedFile.value !== "without-file" ? selectedFile.value : null;
    const filename =
      exportSelection.value === "selected"
        ? `${formattedDate}_selected_run_statistics`
        : `${formattedDate}_run_statistics`;
    const blob = await createExcelExportBlob({
      rows: exportRows,
      exportColumns: runStatisticsExportColumns(),
      axiosInstance: axiosRef,
      templateDownloadUrl:
        selectedTemplate !== null
          ? `${TEMPLATE_API_URL}/${selectedTemplate.id}/download/`
          : null,
      templateFileName: selectedTemplate?.name || ""
    });
    saveAs(
      blob,
      buildExcelExportFilename(filename, selectedTemplate?.name || "")
    );
  } catch (error) {
    showNotification("Error during export. Please try again.\n" + error, "error");
  } finally {
    closeExportPopup();
  }
}

function getRowsForExport() {
  return exportSelection.value === "selected"
    ? rows.value.filter((row) => row.selected)
    : filteredRows.value;
}

function handleSearchAction() {
  searchQuery.value = searchQuery.value.trim();
  appliedSearchQuery.value = searchQuery.value;
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
  const exportPopup = document.querySelector(".statistics-export-popup");
  const exportButton = document.getElementById("openRunStatisticsExportPopupButton");
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
  if (
    showExportPopup.value &&
    !exportPopup?.contains(event.target) &&
    !exportButton?.contains(event.target)
  ) {
    closeExportPopup();
  }
}

function handleKeyDown(event) {
  if (event.key !== "Escape") return;
  showAdvancedFilters.value = false;
  showSelectColumns.value = false;
  closeExportPopup();
}

onMounted(() => {
  fetchRows();
  fetchExportTemplates();
  window.handleGroupButtonClick = handleGroupButtonClick;
  document.addEventListener("click", handleDocumentClick);
  document.addEventListener("keydown", handleKeyDown);
});

onBeforeUnmount(() => {
  clearTimeout(dateTimer);
  window.handleGroupButtonClick = null;
  document.removeEventListener("click", handleDocumentClick);
  document.removeEventListener("keydown", handleKeyDown);
});

setColumns();

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
      showExportPopup,
      showExportHelpTooltip,
      isDragOver,
      uploadedExportTemplates,
      selectedFile,
      exportSelection,
      hasSelectedRows,
      iconExportTemplateFile,
      iconExportTemplateFileLines,
      iconExportDownload,
      iconExportRemove,
      iconExportUpload,
      iconStatisticsHeader,
      filters,
      tableOptions,
      sequencerOptions,
      readLengthOptions,
      preparationOptions,
      analysisTypeOptions,
      selectableColumns,
      filteredRows,
      toggleAdvancedFilters,
      toggleSelectColumns,
      resetAdvancedFilters,
      handleDateChange,
      handleExportClick,
      closeExportPopup,
      handleExport,
      uploadExportTemplate,
      downloadExportTemplate,
      removeExportTemplate,
      handleDragOver,
      handleDragEnter,
      handleDragLeave,
      handleDrop,
      handleSearchAction,
      toggleColumnVisibility,
      resetColumnVisibility,
      resetColumnWidths
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

.statistics-header-icon {
  flex: 0 0 auto;
  width: 34px;
  height: 34px;
  margin-right: 12px;
  color: white;
}

.table-container {
  flex: 1;
  overflow-x: auto;
  overflow-y: auto;
  position: relative;
}

.table-container :deep(.tabulator),
.table-container :deep(.tabulator *),
.table-container :deep(.tabulator *::before),
.table-container :deep(.tabulator *::after) {
  box-sizing: border-box;
}

.statistics-filters-popup {
  left: -80px;
  width: 290px;
  max-height: calc(100vh - 100px);
  overflow-y: auto;
}

.statistics-columns-popup {
  left: -55px;
  width: 320px;
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

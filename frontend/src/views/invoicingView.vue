<template>
  <div class="parent-container">
    <!-- Loading overlay -->
    <div v-if="loading || fakeLoading" class="loading-overlay">
      <div v-if="!fakeLoading" class="spinner"></div>
      <p v-if="!fakeLoading">
        Loading <span style="font-weight: bold">Invoicing</span>...
      </p>
    </div>

    <!-- Header -->
    <div class="header">
      <div class="header-logo" style="display: inline; margin-right: 10px">
        <img
          :src="iconHeader"
          alt="Invoicing"
          width="42"
          height="42"
          style="display: block"
        />
      </div>
      <div class="header-title" style="display: inline">Invoicing</div>

      <!-- Sticky right section for filters and report actions -->
      <div class="sticky-actions">
        <div class="search-bar">
          <input
            ref="searchInput"
            v-model="searchQuery"
            type="text"
            placeholder="Search"
            aria-label="Search all invoicing history"
            :aria-busy="allInvoicingLoading"
          />
          <font-awesome-icon
            icon="fa-solid fa-magnifying-glass"
            style="color: darkgrey"
          />
        </div>
        <span
          v-if="allInvoicingLoading"
          class="invoicing-history-loading"
          role="status"
        >
          Searching history...
        </span>

        <!-- Billing-month filter: always exactly one whole month, present or
             past — never a range. -->
        <div class="date-filters">
          <div class="date-filter">
            <label for="invoicingMonth">Month</label>
            <div
              class="month-year-picker"
              :class="{ 'invalid-date': !billingMonthValid }"
            >
              <select
                id="invoicingMonth"
                class="month-year-picker-month"
                :value="monthPickerMonth"
                @change="onBillingMonthChange($event.target.value)"
              >
                <option
                  v-for="option in billingMonthOptions"
                  :key="option.value"
                  :value="option.value"
                  :disabled="option.disabled"
                >
                  {{ option.label }}
                </option>
              </select>
              <select
                class="month-year-picker-year"
                aria-label="Billing year"
                :value="monthPickerYear"
                @change="onBillingYearChange($event.target.value)"
              >
                <option
                  v-for="option in billingYearOptions"
                  :key="option.value"
                  :value="option.value"
                  :disabled="option.disabled"
                >
                  {{ option.label }}
                </option>
              </select>
            </div>
          </div>
        </div>

        <div class="button-popup-wrapper">
          <button
            id="toggleInvoicingColumnsButton"
            class="header-button"
            type="button"
            aria-haspopup="dialog"
            :aria-expanded="showSelectColumns"
            @click="toggleSelectColumns"
          >
            <font-awesome-icon
              icon="fa-solid fa-columns"
              style="color: white"
            />
            <span>Select Columns</span>
          </button>
          <div
            v-if="showSelectColumns"
            id="invoicingColumnsDialog"
            ref="columnsDialog"
            class="button-popup-container invoicing-columns-dialog"
            role="dialog"
            aria-modal="false"
            aria-labelledby="invoicing-columns-title"
            tabindex="-1"
          >
            <div id="invoicing-columns-title" class="visually-hidden">
              Select invoicing columns
            </div>
            <ul class="invoicing-columns-list">
              <li v-for="column in columnsList" :key="column.field">
                <label>
                  <input
                    v-model="column.visible"
                    type="checkbox"
                    @change="setColumnVisibility(column)"
                  />
                  <span>{{ column.title }}</span>
                </label>
              </li>
            </ul>
            <div class="invoicing-columns-actions">
              <button class="reset-button" @click="resetColumnVisibility">
                Reset Visibility Settings
              </button>
              <button class="reset-button" @click="resetColumnWidths">
                Reset Width Settings
              </button>
            </div>
          </div>
        </div>

        <button
          id="openCostsPanelButton"
          class="header-button"
          type="button"
          aria-haspopup="dialog"
          :aria-expanded="showCostsPanel"
          @click.stop="openCostsPanel"
        >
          <font-awesome-icon
            icon="fa-solid fa-money-bill"
            style="color: white"
          />
          <span> Costs </span>
        </button>
        <button
          class="header-button"
          id="openInvoicingExportPopupButton"
          type="button"
          aria-haspopup="dialog"
          :aria-expanded="showExportPopup"
          :disabled="allInvoicingLoading"
          @click="handleExportClick"
        >
          <font-awesome-icon
            icon="fa-solid fa-file-excel"
            style="color: white"
          />
          <span> Export to Excel </span>
        </button>
      </div>
    </div>

    <!-- Main content section with table -->
    <div class="table-container">
      <TabulatorTable
        v-if="!loading"
        ref="tabulatorTableRef"
        :rowData="tableRowData"
        :columnDefs="columnsList"
        :enableDefaultFilters="false"
        :tableOptions="{
          ...tableOptions,
          fakeLoadingStart,
          fakeLoadingStop,
          handleColumnResized,
          handleColumnVisibilityChanged
        }"
      />
    </div>

    <!-- Costs side panel -->
    <div
      v-if="showCostsPanel"
      class="costs-panel-overlay"
      @click.self.stop="closeCostsPanel"
    >
      <div
        ref="costsDialog"
        class="costs-panel"
        role="dialog"
        aria-modal="true"
        aria-labelledby="costs-panel-title"
        tabindex="-1"
      >
        <div class="costs-panel-header">
          <span id="costs-panel-title" class="costs-panel-title">Costs</span>
          <button
            class="popup-close-button"
            type="button"
            aria-label="Close costs"
            @click="closeCostsPanel"
          >
            &times;
          </button>
        </div>

        <div class="costs-panel-body">
          <div
            v-for="section in costsSections"
            :key="section.key"
            class="costs-section"
          >
            <div class="costs-section-title">{{ section.title }}</div>
            <div v-if="section.loading" class="costs-section-loading">
              Loading...
            </div>
            <table v-else class="costs-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Price</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in section.items" :key="row.id">
                  <td class="costs-name-cell" :title="row.name">
                    {{ row.name }}
                  </td>
                  <td class="costs-price-cell">
                    {{ formatInvoicingCurrency(row.price) }}
                  </td>
                </tr>
                <tr v-if="section.items.length === 0">
                  <td colspan="2" class="costs-empty-row">No entries.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- Export to Excel popup: reuses the template-append pattern from the other tabs -->
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
        ref="exportDialog"
        class="popup-container export-popup"
        role="dialog"
        aria-modal="true"
        aria-labelledby="invoicing-export-title"
        tabindex="-1"
        :style="{ width: '670px', height: '500px' }"
      >
        <div class="popup-header">
          <span id="invoicing-export-title" class="popup-title">
            Export Options
          </span>
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
                  Use export when you want to download the invoicing rows
                  currently shown in the table to Excel.
                </p>
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
              </div>
            </div>
          </span>
          <button
            class="popup-close-button"
            type="button"
            aria-label="Close export options"
            @click="closeExportPopup"
          >
            &times;
          </button>
        </div>
        <div class="popup-body">
          <div class="export-section" style="height: 100%">
            <div style="font-weight: bold; margin-bottom: 8px">
              Upload additional excel sheet templates to append:
            </div>
            <div class="file-list-section" style="height: 280px">
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
                      id="invoicing-without-file"
                      type="radio"
                      title="Select"
                      value="without-file"
                      v-model="selectedFile"
                    />
                  </div>
                </div>
              </div>
              <div
                v-for="(file, index) in fetchedInvoicingTemplates"
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
                    @click.stop="downloadExportTemplate(file)"
                    class="download-button"
                    title="Download Original File"
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
                    @click.stop="removeExportTemplate(index)"
                    class="remove-button"
                    title="Remove File"
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
                      type="radio"
                      title="Select File"
                      :id="'invoicing-file-radio-' + index"
                      :value="file"
                      v-model="selectedFile"
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
              for="invoicing-file-upload"
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
              id="invoicing-file-upload"
              type="file"
              accept=".xlsx,.xlsm"
              @change="uploadExportTemplate"
              style="display: none"
            />
          </div>
          <button
            class="popup-button yes-button"
            :disabled="allInvoicingLoading"
            @click="handleExport"
          >
            OK
          </button>
          <button class="popup-button" @click="closeExportPopup">Cancel</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import TabulatorTable from "../components/TabulatorTableFull.vue";
import { saveAs } from "file-saver";
import {
  showNotification,
  handleError,
  createAxiosObject,
  urlStringStartsWith,
  createExcelExportBlob,
  buildExcelExportFilename,
  buildExcelDownloadFilename,
  isSupportedExcelTemplateFile,
  focusFirstElement,
  trapFocus
} from "../utilities/utilityFunctions";
import {
  invoicingColumnDefs,
  invoicingExportColumns,
  formatInvoicingCurrency
} from "../constants/invoicingConsts";
import { isValidMonth, formatDateForInput } from "../utilities/dateUtils";
import iconHeader from "../assets/icons/header_invoicing.svg";
import iconExportTemplateFile from "../assets/icons/export_template.svg";
import iconExportTemplateFileLines from "../assets/icons/export_template_lines.svg";
import iconExportDownload from "../assets/icons/export_download.svg";
import iconExportRemove from "../assets/icons/export_remove.svg";
import iconExportUpload from "../assets/icons/export_upload.svg";

const axiosRef = createAxiosObject();
const urlStringStart = urlStringStartsWith();
// Wide enough to cover every request ever loaded, without needing a
// dedicated "give me everything" endpoint from the backend.
const FULL_HISTORY_START_MONTH = "2000-01";
const COLUMN_VISIBILITY_KEY = "invoicingColumnVisibility";
const COLUMN_WIDTHS_KEY = "invoicingColumnWidths";
const MONTH_NAMES = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec"
];
const COST_SECTION_DEFS = [
  { key: "fixed_costs", title: "Fixed Costs", endpoint: "fixed_costs" },
  {
    key: "preparation_costs",
    title: "Preparation Costs",
    endpoint: "library_preparation_costs"
  },
  {
    key: "sequencing_costs",
    title: "Sequencing Costs",
    endpoint: "sequencing_costs"
  }
];

function pad2(value) {
  return String(value).padStart(2, "0");
}

function readStoredObject(key) {
  try {
    return JSON.parse(localStorage.getItem(key) || "{}");
  } catch {
    localStorage.removeItem(key);
    return {};
  }
}

function todayString() {
  return formatDateForInput(new Date());
}

function monthOf(dateString) {
  return (dateString || "").slice(0, 7);
}

function currentMonthString() {
  return monthOf(todayString());
}

export default {
  name: "InvoicingView",
  components: {
    TabulatorTable
  },
  data() {
    return {
      iconHeader,
      iconExportTemplateFile,
      iconExportTemplateFileLines,
      iconExportDownload,
      iconExportRemove,
      iconExportUpload,
      loading: true,
      fakeLoading: false,
      invoicingList: [],
      // Only populated on demand, the first time a search is typed, so the
      // search box can look across the entire Invoicing History instead of
      // just the currently displayed billing month.
      allInvoicingList: [],
      allInvoicingLoaded: false,
      allInvoicingLoading: false,
      columnsList: [],
      readLengthNames: {},
      libraryProtocolNames: {},
      searchQuery: "",
      // Always defaults to the current calendar month and is never
      // persisted, so a new month never keeps showing stale/previous data
      // and requests can't accidentally be double-billed. The picker only
      // allows picking a whole month (present or past), never a partial
      // day-range within one.
      billingMonth: currentMonthString(),
      maxMonth: currentMonthString(),
      billingMonthValid: true,
      dateChangeTimer: null,
      invoicingRequestId: 0,
      showCostsPanel: false,
      costsPreviouslyFocusedElement: null,
      costsSections: COST_SECTION_DEFS.map((definition) => ({
        ...definition,
        items: [],
        loading: false
      })),
      showSelectColumns: false,
      showExportPopup: false,
      showExportHelpTooltip: false,
      isDragOver: false,
      fetchedInvoicingTemplates: [],
      selectedFile: "without-file",
      previouslyFocusedElement: null,
      tableOptions: {
        index: "request",
        placeholder: "No invoicing items to show.",
        clipboard: "copy"
      }
    };
  },
  computed: {
    // The table's rowData only swaps between the current month-scoped list
    // and the (lazily loaded) full history — never per keystroke. Per-
    // keystroke filtering is applied straight to the Tabulator instance
    // (see applySearchFilter), the same strategy the other tabs use, so
    // typing never forces a full table rebuild.
    tableRowData() {
      return this.searchQuery.trim() && this.allInvoicingLoaded
        ? this.allInvoicingList
        : this.invoicingList;
    },
    monthPickerYear() {
      return Number(this.billingMonth.slice(0, 4)) || new Date().getFullYear();
    },
    monthPickerMonth() {
      return this.billingMonth.slice(5, 7) || pad2(new Date().getMonth() + 1);
    },
    maxBillingYear() {
      return Number(this.maxMonth.slice(0, 4));
    },
    maxBillingMonth() {
      return this.maxMonth.slice(5, 7);
    },
    billingYearOptions() {
      const options = [];
      const topYear = Math.max(this.maxBillingYear, this.monthPickerYear);
      for (let year = 2000; year <= topYear; year += 1) {
        options.push({
          value: String(year),
          label: String(year),
          disabled: year > this.maxBillingYear
        });
      }
      return options;
    },
    billingMonthOptions() {
      return MONTH_NAMES.map((label, index) => {
        const value = pad2(index + 1);
        return {
          value,
          label,
          disabled:
            this.monthPickerYear === this.maxBillingYear &&
            value > this.maxBillingMonth
        };
      });
    }
  },
  watch: {
    billingMonth(newVal) {
      this.handleDateChange(newVal);
    },
    searchQuery(newVal) {
      this.applySearchFilter(newVal);
      if (newVal.trim() && !this.allInvoicingLoaded) {
        this.fetchAllInvoicing();
      }
    },
    allInvoicingLoaded(loaded) {
      if (loaded) {
        this.$nextTick(() => this.applySearchFilter(this.searchQuery));
      }
    }
  },
  async mounted() {
    this.setColumns();
    document.addEventListener("click", this.handleOutsideClick);
    document.addEventListener("keydown", this.handleKeyDown);
    await this.fetchLookups();
    await this.getInvoicing();
    this.fetchExportTemplates();
  },
  beforeUnmount() {
    if (this.dateChangeTimer) {
      clearTimeout(this.dateChangeTimer);
    }
    this.invoicingRequestId += 1;
    document.removeEventListener("click", this.handleOutsideClick);
    document.removeEventListener("keydown", this.handleKeyDown);
  },
  methods: {
    setColumns() {
      const storedVisibility = readStoredObject(COLUMN_VISIBILITY_KEY);
      const storedWidths = readStoredObject(COLUMN_WIDTHS_KEY);
      this.columnsList = invoicingColumnDefs().map((column) => ({
        ...column,
        width: storedWidths[column.field] || column.width,
        visible: storedVisibility[column.field] ?? column.visible ?? true
      }));
    },
    rememberFocus() {
      this.previouslyFocusedElement = document.activeElement;
    },
    restoreRememberedFocus() {
      const returnFocusTo = this.previouslyFocusedElement;
      this.previouslyFocusedElement = null;
      this.$nextTick(() => returnFocusTo?.focus?.());
    },
    handleOutsideClick(event) {
      const columnsDialog = this.$refs.columnsDialog;
      const columnsButton = this.$el.querySelector(
        "#toggleInvoicingColumnsButton"
      );
      const exportDialog = this.$refs.exportDialog;
      const exportButton = this.$el.querySelector(
        "#openInvoicingExportPopupButton"
      );
      const costsDialog = this.$refs.costsDialog;
      const costsButton = this.$el.querySelector("#openCostsPanelButton");

      if (
        this.showSelectColumns &&
        columnsDialog &&
        !columnsDialog.contains(event.target) &&
        !columnsButton?.contains(event.target)
      ) {
        this.closeSelectColumns();
      }
      if (
        this.showExportPopup &&
        exportDialog &&
        !exportDialog.contains(event.target) &&
        !exportButton?.contains(event.target)
      ) {
        this.closeExportPopup();
      }
      if (
        this.showCostsPanel &&
        costsDialog &&
        !costsDialog.contains(event.target) &&
        !costsButton?.contains(event.target)
      ) {
        this.closeCostsPanel();
      }
    },
    handleKeyDown(event) {
      if (this.showCostsPanel) {
        if (event.key === "Escape") {
          event.preventDefault();
          this.closeCostsPanel();
          return;
        }
        trapFocus(event, this.$refs.costsDialog);
        return;
      }
      if (this.showExportPopup) {
        if (event.key === "Escape") {
          event.preventDefault();
          this.closeExportPopup();
          return;
        }
        trapFocus(event, this.$refs.exportDialog);
        return;
      }
      if (this.showSelectColumns) {
        if (event.key === "Escape") {
          event.preventDefault();
          this.closeSelectColumns();
          return;
        }
        trapFocus(event, this.$refs.columnsDialog);
      }
    },
    fakeLoadingStart() {
      this.fakeLoading = true;
    },
    fakeLoadingStop() {
      setTimeout(() => {
        this.fakeLoading = false;
      }, 300);
    },
    toggleSelectColumns() {
      if (this.showSelectColumns) {
        this.closeSelectColumns();
        return;
      }
      this.rememberFocus();
      this.showExportPopup = false;
      this.showSelectColumns = true;
      this.$nextTick(() => focusFirstElement(this.$refs.columnsDialog));
    },
    closeSelectColumns() {
      if (!this.showSelectColumns) return;
      this.showSelectColumns = false;
      this.restoreRememberedFocus();
    },
    openCostsPanel() {
      this.showSelectColumns = false;
      this.showExportPopup = false;
      this.previouslyFocusedElement = null;
      this.costsPreviouslyFocusedElement = document.activeElement;
      this.showCostsPanel = true;
      this.fetchAllCostSections();
      this.$nextTick(() => focusFirstElement(this.$refs.costsDialog));
    },
    closeCostsPanel() {
      if (!this.showCostsPanel) return;
      this.showCostsPanel = false;
      const returnFocusTo = this.costsPreviouslyFocusedElement;
      this.costsPreviouslyFocusedElement = null;
      this.$nextTick(() => returnFocusTo?.focus?.());
    },
    async fetchAllCostSections() {
      await Promise.all(
        this.costsSections.map((section) => this.fetchCostSection(section))
      );
    },
    async fetchCostSection(section) {
      section.loading = true;
      try {
        const response = await axiosRef.get(
          `${urlStringStart}/api/${section.endpoint}/`
        );
        section.items = response.data || [];
      } catch (error) {
        handleError(error);
      } finally {
        section.loading = false;
      }
    },
    formatInvoicingCurrency,
    onBillingMonthChange(value) {
      this.billingMonth = `${this.monthPickerYear}-${value}`;
    },
    onBillingYearChange(value) {
      let month = this.monthPickerMonth;
      if (
        Number(value) === this.maxBillingYear &&
        month > this.maxBillingMonth
      ) {
        month = this.maxBillingMonth;
      }
      this.billingMonth = `${value}-${month}`;
    },
    setColumnVisibility(column) {
      const table = this.$refs.tabulatorTableRef?.getTable?.();
      if (column.visible) {
        table?.showColumn?.(column.field);
      } else {
        table?.hideColumn?.(column.field);
      }
    },
    handleColumnResized(column) {
      const field = column?.getField?.();
      if (!field) return;
      localStorage.setItem(
        COLUMN_WIDTHS_KEY,
        JSON.stringify({
          ...readStoredObject(COLUMN_WIDTHS_KEY),
          [field]: column.getWidth()
        })
      );
      this.fakeLoadingStart();
      setTimeout(() => this.fakeLoadingStop(), 50);
    },
    handleColumnVisibilityChanged(field, visible) {
      if (!field) return;
      localStorage.setItem(
        COLUMN_VISIBILITY_KEY,
        JSON.stringify({
          ...readStoredObject(COLUMN_VISIBILITY_KEY),
          [field]: visible
        })
      );
      const column = this.columnsList.find((item) => item.field === field);
      if (column) column.visible = visible;
      this.fakeLoadingStart();
      setTimeout(() => this.fakeLoadingStop(), 50);
    },
    resetColumnWidths() {
      localStorage.removeItem(COLUMN_WIDTHS_KEY);
      this.setColumns();
      this.fakeLoadingStart();
      setTimeout(() => this.fakeLoadingStop(), 300);
    },
    resetColumnVisibility() {
      localStorage.removeItem(COLUMN_VISIBILITY_KEY);
      this.setColumns();
      this.fakeLoadingStart();
      setTimeout(() => this.fakeLoadingStop(), 300);
    },
    async fetchLookups() {
      try {
        const [readLengths, protocols] = await Promise.all([
          axiosRef.get(urlStringStart + "/api/read_lengths_invoicing/"),
          axiosRef.get(urlStringStart + "/api/library_protocols_invoicing/")
        ]);
        (readLengths.data || []).forEach((item) => {
          this.readLengthNames[item.id] = item.name;
        });
        (protocols.data || []).forEach((item) => {
          this.libraryProtocolNames[item.id] = item.name;
        });
      } catch (error) {
        handleError(error);
      }
    },
    handleDateChange(value) {
      clearTimeout(this.dateChangeTimer);
      this.billingMonthValid = isValidMonth(value);
      if (!this.billingMonthValid) return;
      this.dateChangeTimer = setTimeout(() => {
        this.getInvoicing();
      }, 500);
    },
    // Applies (or clears) the search filter directly on the Tabulator
    // instance instead of recomputing/replacing the table's rowData, so
    // typing quickly never triggers a full table rebuild — the same
    // strategy the other tabs (Pooling, Library Preparation, etc.) use.
    applySearchFilter(query) {
      const table = this.$refs.tabulatorTableRef?.getTable?.();
      if (!table) return;
      const trimmed = (query || "").trim().toLowerCase();
      if (!trimmed) {
        table.clearFilter();
        return;
      }
      table.setFilter((rowData) =>
        [
          rowData.request,
          rowData.cost_unit,
          rowData.sequencer,
          rowData.library_protocol
        ]
          .join(" ")
          .toLowerCase()
          .includes(trimmed)
      );
    },
    // Shared by the current-month load and the full-history search fetch so
    // both stay in sync with how a row is built.
    mapInvoicingElement(element) {
      const sequencerList = [
        ...new Set((element.sequencer || []).map((x) => x.sequencer_name))
      ].sort();
      const percentage = (element.percentage || [])
        .map((flowcell) =>
          (flowcell.pools || []).map((p) => p.percentage).join(", ")
        )
        .join("; ");
      const readLength = [...(element.read_length || [])]
        .map((id) => this.readLengthNames[id] || id)
        .sort()
        .join("; ");
      // Each flowcell entry is "dd.mm.yyyy FLOWCELLID"; split into
      // separate Date and Flowcell ID columns.
      const flowcellEntries = element.flowcell || [];
      const flowcellDates = flowcellEntries.map((entry) => entry.split(" ")[0]);
      const flowcellIds = flowcellEntries.map((entry) =>
        entry.split(" ").slice(1).join(" ")
      );
      return {
        request: element.request || "",
        cost_unit: element.cost_unit || "",
        sequencer: sequencerList.join("; "),
        flowcell_date: flowcellDates.join("; "),
        flowcell_id: flowcellIds.join("; "),
        pool: (element.pool || []).join("; "),
        percentage,
        read_length: readLength,
        num_libraries_samples_show: element.num_libraries_samples_show || "",
        library_protocol:
          this.libraryProtocolNames[element.library_protocol] ||
          element.library_protocol ||
          "",
        fixed_costs: element.fixed_costs,
        sequencing_costs: element.sequencing_costs,
        preparation_costs: element.preparation_costs,
        variable_costs: element.variable_costs,
        total_costs: element.total_costs
      };
    },
    async getInvoicing() {
      if (!isValidMonth(this.billingMonth)) {
        return;
      }
      this.billingMonthValid = true;
      const requestId = ++this.invoicingRequestId;
      const requestedMonth = this.billingMonth;
      this.loading = true;
      this.invoicingList = [];
      try {
        const response = await axiosRef.get(
          urlStringStart + "/api/invoicing/",
          {
            params: {
              start: requestedMonth,
              end: requestedMonth
            }
          }
        );
        if (requestId !== this.invoicingRequestId) return;
        this.invoicingList = (response.data || [])
          .filter((element) => element.library_protocol !== "")
          .map((element) => this.mapInvoicingElement(element));
      } catch (error) {
        if (requestId !== this.invoicingRequestId) return;
        this.invoicingList = [];
        handleError(error);
      } finally {
        if (requestId === this.invoicingRequestId) {
          this.loading = false;
        }
      }
    },
    // Lazily loads every request ever loaded into the sequencer, so the
    // search box can look across the whole Invoicing History instead of
    // only the currently displayed billing month. Loaded once and cached;
    // it never replaces the default month-scoped view/report.
    async fetchAllInvoicing() {
      if (this.allInvoicingLoaded || this.allInvoicingLoading) return;
      this.allInvoicingLoading = true;
      try {
        const response = await axiosRef.get(
          urlStringStart + "/api/invoicing/",
          {
            params: {
              start: FULL_HISTORY_START_MONTH,
              end: currentMonthString()
            }
          }
        );
        this.allInvoicingList = (response.data || [])
          .filter((element) => element.library_protocol !== "")
          .map((element) => this.mapInvoicingElement(element));
        this.allInvoicingLoaded = true;
      } catch (error) {
        handleError(error);
      } finally {
        this.allInvoicingLoading = false;
      }
    },
    async fetchExportTemplates() {
      try {
        const response = await axiosRef.get(
          `${urlStringStart}/api/invoicing-templates/`
        );
        this.fetchedInvoicingTemplates = response.data;
      } catch (error) {
        handleError(error);
      }
    },
    async uploadExportTemplate(event) {
      const file = event.target.files[0];
      if (isSupportedExcelTemplateFile(file)) {
        const formData = new FormData();
        formData.append("file", file);
        try {
          await axiosRef.post(
            `${urlStringStart}/api/invoicing-templates/upload/`,
            formData,
            { headers: { "Content-Type": "multipart/form-data" } }
          );
          showNotification("File uploaded successfully.", "success");
          this.fetchExportTemplates();
        } catch (error) {
          showNotification("Error uploading file: " + error, "error");
        } finally {
          this.selectedFile = "without-file";
        }
      } else {
        showNotification("Please upload a valid XLSX or XLSM file.", "error");
      }
    },
    async downloadExportTemplate(file) {
      try {
        const response = await axiosRef.get(
          `${urlStringStart}/api/invoicing-templates/${file.id}/download/`,
          { responseType: "blob" }
        );
        saveAs(
          response.data,
          buildExcelDownloadFilename(
            "Invoicing",
            file.name,
            response.data?.type
          )
        );
      } catch (error) {
        showNotification("Error downloading file: " + error, "error");
      }
    },
    async removeExportTemplate(index) {
      const file = this.fetchedInvoicingTemplates[index];
      try {
        await axiosRef.delete(
          `${urlStringStart}/api/invoicing-templates/${file.id}/remove/`
        );
        this.fetchedInvoicingTemplates.splice(index, 1);
        showNotification("File removed successfully.", "success");
      } catch (error) {
        showNotification("Error removing file: " + error, "error");
      } finally {
        this.selectedFile = "without-file";
      }
    },
    handleExportClick() {
      if (this.allInvoicingLoading) return;
      this.rememberFocus();
      this.showSelectColumns = false;
      this.showExportHelpTooltip = false;
      this.isDragOver = false;
      this.showExportPopup = true;
      this.$nextTick(() => focusFirstElement(this.$refs.exportDialog));
    },
    closeExportPopup() {
      if (!this.showExportPopup) return;
      this.showExportPopup = false;
      this.showExportHelpTooltip = false;
      this.isDragOver = false;
      this.selectedFile = "without-file";
      this.restoreRememberedFocus();
    },
    // Tabulator's active rows include both the global search filter and every
    // per-column header filter, so the export matches the visible table.
    getDisplayedRows() {
      const table = this.$refs.tabulatorTableRef?.getTable?.();
      if (!table) return this.tableRowData;
      const activeRows = table.getRows?.("active");
      if (Array.isArray(activeRows)) {
        return activeRows.map((row) => row.getData());
      }
      const activeData = table.getData?.("active");
      return Array.isArray(activeData) ? activeData : this.tableRowData;
    },
    async handleExport() {
      if (this.allInvoicingLoading) {
        showNotification(
          "Please wait until the invoicing history search has finished.",
          "warning"
        );
        return;
      }
      const exportRows = this.getDisplayedRows();
      if (!exportRows.length) {
        showNotification("No invoicing rows available for export.", "warning");
        return;
      }
      try {
        this.fakeLoadingStart();
        const today = new Date();
        const formattedDate = `${today.getFullYear()}${String(
          today.getMonth() + 1
        ).padStart(2, "0")}${String(today.getDate()).padStart(2, "0")}`;
        const filename = `${formattedDate}_invoicing`;
        const exportColumns = invoicingExportColumns();
        const templateDownloadUrl =
          this.selectedFile !== "without-file"
            ? `${urlStringStart}/api/invoicing-templates/${this.selectedFile.id}/download/`
            : null;

        const blob = await createExcelExportBlob({
          rows: exportRows,
          exportColumns,
          axiosInstance: axiosRef,
          templateDownloadUrl,
          templateFileName:
            this.selectedFile !== "without-file" ? this.selectedFile.name : ""
        });
        saveAs(
          blob,
          buildExcelExportFilename(
            filename,
            this.selectedFile !== "without-file" ? this.selectedFile.name : ""
          )
        );
      } catch (error) {
        showNotification(
          "Error during export. Please try again.\n" + error,
          "error"
        );
      } finally {
        this.fakeLoadingStop();
        this.closeExportPopup();
      }
    },
    handleDragOver(e) {
      e.preventDefault();
      this.isDragOver = true;
    },
    handleDragEnter(e) {
      e.preventDefault();
      this.isDragOver = true;
    },
    handleDragLeave(e) {
      if (!e.currentTarget.contains(e.relatedTarget)) {
        this.isDragOver = false;
      }
    },
    handleDrop(e) {
      e.preventDefault();
      this.isDragOver = false;
      const files = e.dataTransfer.files;
      if (files.length > 1) {
        showNotification(
          "Please upload only one XLSX or XLSM file at a time.",
          "error"
        );
      } else {
        this.processUploadedFile(files[0]);
      }
    },
    processUploadedFile(file) {
      if (isSupportedExcelTemplateFile(file)) {
        this.uploadExportTemplate({ target: { files: [file] } });
      } else {
        showNotification("Please upload a valid XLSX or XLSM file.", "error");
      }
    }
  }
};
</script>

<style>
html,
body,
#app {
  height: 100%;
  margin: 0;
  padding: 0;
}

.parent-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 10px;
}

.table-container {
  flex: 1;
  overflow: auto;
  position: relative;
}

.invoicing-filter {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-right: 10px;
  color: white;
  font-size: 13px;
  white-space: nowrap;
}

.invoicing-filter input,
.invoicing-filter select {
  padding: 4px 6px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 13px;
}

.invoicing-columns-dialog {
  left: -50px;
  width: 260px;
  max-height: 475px;
  display: flex;
  flex-direction: column;
  padding: 10px;
}

.invoicing-columns-list {
  margin: 0;
  padding: 0 4px 8px;
  overflow-y: auto;
}

.invoicing-columns-list li {
  list-style: none;
}

.invoicing-columns-list label {
  cursor: pointer;
}

.invoicing-columns-actions {
  display: flex;
  flex-direction: column;
  gap: 5px;
  padding-top: 8px;
  border-top: 1px solid #eee;
}

.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.invoicing-history-loading {
  color: white;
  font-size: 12px;
  white-space: nowrap;
}

.month-year-picker {
  display: flex;
  flex-direction: row;
  gap: 4px;
}

.month-year-picker select {
  height: 28px;
  padding: 3px 6px;
  border: 1px solid rgba(0, 0, 0, 0.18);
  border-radius: 5px;
  background: #fff;
  color: #333;
  font-family: var(--app-font-family);
  font-size: 13px;
  line-height: 18px;
  box-sizing: border-box;
  cursor: pointer;
  outline: none;
}

.month-year-picker-month {
  width: 64px;
}

.month-year-picker-year {
  width: 68px;
}

.month-year-picker.invalid-date select {
  border-color: #ff6b6b;
  background-color: #fff0f0;
}

.costs-panel-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  justify-content: flex-end;
  background: rgba(0, 0, 0, 0.25);
}

.costs-panel {
  display: flex;
  width: 420px;
  max-width: 90vw;
  height: 100%;
  flex-direction: column;
  background: #fff;
  box-shadow: -4px 0 12px rgba(0, 0, 0, 0.2);
  animation: costs-panel-slide-in 0.2s ease-out;
}

@keyframes costs-panel-slide-in {
  from {
    transform: translateX(100%);
  }
  to {
    transform: translateX(0);
  }
}

.costs-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-bottom: 1px solid #e0e0e0;
  background: linear-gradient(180deg, #0b7f78 0%, #006c66 100%);
}

.costs-panel-title {
  color: white;
  font-size: 16px;
  font-weight: bold;
}

.costs-panel-body {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
}

.costs-section {
  margin-bottom: 20px;
}

.costs-section-title {
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: bold;
}

.costs-section-loading {
  color: #888;
  font-size: 13px;
}

.costs-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.costs-table th {
  padding: 4px 6px;
  border-bottom: 1px solid #ddd;
  color: #666;
  font-weight: 600;
  text-align: left;
}

.costs-table td {
  padding: 6px;
  border-bottom: 1px solid #f0f0f0;
  vertical-align: middle;
}

.costs-name-cell {
  max-width: 190px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.costs-price-cell {
  width: 90px;
}

.costs-empty-row {
  padding: 10px;
  color: #888;
  text-align: center;
}
</style>

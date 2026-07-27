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
          <input v-model="searchQuery" type="text" placeholder="Search" />
          <font-awesome-icon
            icon="fa-solid fa-magnifying-glass"
            style="color: darkgrey"
          />
        </div>

        <!-- Billing-month range filter: only whole months are selectable,
             never partial ranges within a month, present or past. -->
        <div class="date-filters">
          <div class="date-filter">
            <label for="invoicingStart">From</label>
            <MonthYearPicker
              id="invoicingStart"
              v-model="startMonth"
              :max="maxMonth"
              :invalid="!startMonthValid"
            />
          </div>
          <div class="date-filter">
            <label for="invoicingEnd">To</label>
            <MonthYearPicker
              id="invoicingEnd"
              v-model="endMonth"
              :max="maxMonth"
              :invalid="!endMonthValid"
            />
          </div>
        </div>

        <!-- Report actions -->
        <button class="header-button" @click="downloadReport">
          <font-awesome-icon icon="fa-solid fa-download" style="color: white" />
          <span> Download Report </span>
        </button>
        <button class="header-button" @click="showUploadPopup = true">
          <font-awesome-icon icon="fa-solid fa-upload" style="color: white" />
          <span> Upload Reports </span>
        </button>
        <button class="header-button" @click="openViewReports">
          <font-awesome-icon
            icon="fa-solid fa-folder-open"
            style="color: white"
          />
          <span> View Uploaded Reports </span>
        </button>
        <button
          class="header-button"
          id="openInvoicingExportPopupButton"
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
        :tableOptions="tableOptions"
      />
    </div>

    <!-- Upload Reports popup -->
    <div v-if="showUploadPopup" class="popup-overlay">
      <div class="popup-container" :style="{ width: '500px', height: '260px' }">
        <div class="popup-header">
          <span class="popup-title">Upload Reports</span>
          <button class="popup-close-button" @click="showUploadPopup = false">
            &times;
          </button>
        </div>
        <div class="popup-body">
          <div class="invoicing-form-row">
            <label>Select Month</label>
            <input v-model="uploadDate" type="date" />
          </div>
          <div class="invoicing-form-row">
            <label>Browse Report</label>
            <input ref="uploadFileInput" type="file" />
          </div>
        </div>
        <div class="popup-footer">
          <button class="popup-button yes-button" @click="uploadReport">
            Upload
          </button>
          <button
            class="popup-button secondary"
            @click="showUploadPopup = false"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>

    <!-- View Uploaded Reports popup: lists everything in the invoicing media dir -->
    <div v-if="showViewReportsPopup" class="popup-overlay">
      <div class="popup-container" :style="{ width: '640px', height: '520px' }">
        <div class="popup-header">
          <span class="popup-title">View Uploaded Reports</span>
          <button
            class="popup-close-button"
            @click="showViewReportsPopup = false"
          >
            &times;
          </button>
        </div>
        <div class="popup-body">
          <div
            v-if="uploadedReports.length === 0"
            style="text-align: center; padding: 30px; color: #888"
          >
            No uploaded reports found in the invoicing media directory.
          </div>
          <div v-else class="uploaded-reports-list" @scroll="onReportsScroll">
            <div
              v-for="file in visibleReports"
              :key="file.path"
              class="uploaded-report-item"
            >
              <div class="uploaded-report-info">
                <font-awesome-icon
                  icon="fa-solid fa-file-excel"
                  style="color: #1d6f42; margin-right: 8px"
                />
                <div>
                  <div class="uploaded-report-name">{{ file.name }}</div>
                  <div class="uploaded-report-meta">
                    {{ file.path }} · {{ formatSize(file.size) }} ·
                    {{ file.modified }}
                  </div>
                </div>
              </div>
              <a
                class="popup-button yes-button uploaded-report-download"
                :href="file.url"
                :download="file.name"
              >
                Download
              </a>
            </div>
          </div>
        </div>
        <div class="popup-footer">
          <span
            v-if="uploadedReports.length > 0"
            class="uploaded-report-meta"
            style="margin-right: auto"
          >
            Showing {{ visibleReports.length }} of
            {{ uploadedReports.length }}
          </span>
          <button
            class="popup-button secondary"
            @click="showViewReportsPopup = false"
          >
            Close
          </button>
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
        class="popup-container export-popup"
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
          <button class="popup-close-button" @click="closeExportPopup">
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
          <button class="popup-button yes-button" @click="handleExport">
            OK
          </button>
          <button
            class="popup-button"
            @click="
              showExportPopup = false;
              selectedFile = 'without-file';
            "
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import TabulatorTable from "../components/TabulatorTableFull.vue";
import MonthYearPicker from "../components/MonthYearPicker.vue";
import { saveAs } from "file-saver";
import {
  showNotification,
  handleError,
  createAxiosObject,
  urlStringStartsWith,
  createExcelExportBlob,
  buildExcelExportFilename,
  buildExcelDownloadFilename,
  isSupportedExcelTemplateFile
} from "../utilities/utilityFunctions";
import {
  invoicingColumnDefs,
  invoicingExportColumns
} from "../constants/invoicingConsts";
import {
  isValidDate,
  isValidMonth,
  formatDateForInput
} from "../utilities/dateUtils";
import iconHeader from "../assets/icons/header_statistics.svg";
import iconExportTemplateFile from "../assets/icons/export_template.svg";
import iconExportTemplateFileLines from "../assets/icons/export_template_lines.svg";
import iconExportDownload from "../assets/icons/export_download.svg";
import iconExportRemove from "../assets/icons/export_remove.svg";
import iconExportUpload from "../assets/icons/export_upload.svg";

const axiosRef = createAxiosObject();
const urlStringStart = urlStringStartsWith();
const REPORTS_PAGE_SIZE = 20;
// Wide enough to cover every request ever loaded, without needing a
// dedicated "give me everything" endpoint from the backend.
const FULL_HISTORY_START_MONTH = "2000-01";

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
    TabulatorTable,
    MonthYearPicker
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
      // and requests can't accidentally be double-billed. The pickers only
      // allow picking a whole month (present or past), never a partial
      // day-range within one.
      startMonth: currentMonthString(),
      endMonth: currentMonthString(),
      maxMonth: currentMonthString(),
      startMonthValid: true,
      endMonthValid: true,
      dateChangeTimer: null,
      showUploadPopup: false,
      showViewReportsPopup: false,
      uploadDate: todayString(),
      uploadedReports: [],
      visibleReportsCount: REPORTS_PAGE_SIZE,
      showExportPopup: false,
      showExportHelpTooltip: false,
      isDragOver: false,
      fetchedInvoicingTemplates: [],
      selectedFile: "without-file",
      tableOptions: {
        index: "request",
        placeholder: "No invoicing items to show."
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
    visibleReports() {
      return this.uploadedReports.slice(0, this.visibleReportsCount);
    }
  },
  watch: {
    startMonth(newVal) {
      this.handleDateChange("start", newVal);
    },
    endMonth(newVal) {
      this.handleDateChange("end", newVal);
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
    this.columnsList = invoicingColumnDefs();
    await this.fetchLookups();
    await this.getInvoicing();
    this.fetchExportTemplates();
  },
  beforeUnmount() {
    if (this.dateChangeTimer) {
      clearTimeout(this.dateChangeTimer);
    }
  },
  methods: {
    fakeLoadingStart() {
      this.fakeLoading = true;
    },
    fakeLoadingStop() {
      setTimeout(() => {
        this.fakeLoading = false;
      }, 300);
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
    handleDateChange(type, value) {
      clearTimeout(this.dateChangeTimer);
      this[`${type}MonthValid`] = isValidMonth(value);
      if (!this[`${type}MonthValid`]) return;
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
      if (!isValidMonth(this.startMonth) || !isValidMonth(this.endMonth)) {
        return;
      }
      if (this.startMonth > this.endMonth) {
        this.startMonthValid = false;
        this.endMonthValid = false;
        showNotification(
          "The 'From' month cannot be later than the 'To' month.",
          "warning"
        );
        return;
      }
      this.startMonthValid = true;
      this.endMonthValid = true;
      this.loading = true;
      try {
        const response = await axiosRef.get(
          urlStringStart + "/api/invoicing/",
          {
            params: {
              start: this.startMonth,
              end: this.endMonth
            }
          }
        );
        this.invoicingList = (response.data || [])
          .filter((element) => element.library_protocol !== "")
          .map((element) => this.mapInvoicingElement(element));
      } catch (error) {
        handleError(error);
      } finally {
        this.loading = false;
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
    downloadReport() {
      // Downloads whatever whole month(s) the From/To pickers are set to.
      // They default to the current month on every load and can only ever
      // select whole months, so this defaults to the current full month
      // while still allowing a deliberate switch to a previous one.
      const params = new URLSearchParams({
        start: this.startMonth,
        end: this.endMonth
      });
      window.open(
        `${urlStringStart}/api/invoicing/download/?${params.toString()}`,
        "_blank"
      );
    },
    async uploadReport() {
      const fileInput = this.$refs.uploadFileInput;
      const file = fileInput && fileInput.files && fileInput.files[0];
      if (!isValidDate(this.uploadDate)) {
        showNotification("Please select the month.", "warning");
        return;
      }
      if (!file) {
        showNotification("Please select the report file.", "warning");
        return;
      }
      const payload = new FormData();
      payload.append("report", file);
      payload.append("month", monthOf(this.uploadDate));
      try {
        await axiosRef.post(
          `${urlStringStart}/api/invoicing/upload/`,
          payload,
          { headers: { "Content-Type": "multipart/form-data" } }
        );
        showNotification("Report has been successfully uploaded.", "success");
        this.showUploadPopup = false;
      } catch (error) {
        showNotification("Error while uploading the report: " + error, "error");
      }
    },
    async openViewReports() {
      this.showViewReportsPopup = true;
      this.visibleReportsCount = REPORTS_PAGE_SIZE;
      try {
        const response = await axiosRef.get(
          `${urlStringStart}/api/invoicing/reports/`
        );
        this.uploadedReports = response.data || [];
      } catch (error) {
        handleError(error);
      }
    },
    onReportsScroll(event) {
      const el = event.target;
      const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 80;
      if (
        nearBottom &&
        this.visibleReportsCount < this.uploadedReports.length
      ) {
        this.visibleReportsCount += REPORTS_PAGE_SIZE;
      }
    },
    formatSize(bytes) {
      if (bytes === null || bytes === undefined) return "";
      if (bytes < 1024) return `${bytes} B`;
      if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
      return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
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
      this.showExportHelpTooltip = false;
      this.isDragOver = false;
      this.showExportPopup = true;
    },
    closeExportPopup() {
      this.showExportPopup = false;
      this.showExportHelpTooltip = false;
      this.isDragOver = false;
      this.selectedFile = "without-file";
    },
    // Mirrors whatever is currently visible in the table: the active search
    // filter (if any) applied on top of the current month/full-history
    // dataset, without needing to read Tabulator's internal filtered state.
    getDisplayedRows() {
      const query = this.searchQuery.trim().toLowerCase();
      if (!query) return this.tableRowData;
      return this.tableRowData.filter((row) =>
        [row.request, row.cost_unit, row.sequencer, row.library_protocol]
          .join(" ")
          .toLowerCase()
          .includes(query)
      );
    },
    async handleExport() {
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

.invoicing-form-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.invoicing-form-row label {
  width: 110px;
  font-weight: bold;
}

.invoicing-form-row input {
  flex: 1;
  padding: 5px 6px;
  border: 1px solid #ccc;
  border-radius: 4px;
}

.uploaded-reports-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 380px;
  overflow-y: auto;
}

.uploaded-report-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 10px;
  border: 1px solid #eee;
  border-radius: 6px;
}

.uploaded-report-info {
  display: flex;
  align-items: center;
  overflow: hidden;
}

.uploaded-report-name {
  font-weight: bold;
  font-size: 13px;
}

.uploaded-report-meta {
  font-size: 11px;
  color: #888;
}

.uploaded-report-download {
  text-decoration: none;
  white-space: nowrap;
  margin-left: 10px;
}
</style>

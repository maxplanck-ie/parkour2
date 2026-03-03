<template>
  <div class="parent-container">
    <!-- Loading overlay -->
    <div v-if="(loading || fakeLoading) && !exportLoading && !requestEditorSyncing" class="loading-overlay">
      <div v-if="!fakeLoading" class="spinner"></div>
      <p v-if="!fakeLoading">
        Loading <span style="font-weight: bold">Libraries & Samples</span>...
      </p>
    </div>
    <div v-if="exportLoading" class="loading-overlay">
      <div class="export-long-loading">
        <span> <strong>Please wait</strong>, this might take a while... </span>
        <div class="spinner" style="height: 35px; width: 35px"></div>
      </div>
    </div>

    <!-- Header -->
    <div class="header">
      <div class="header-logo" style="display: inline; margin-right: 10px">
        <img :src="iconLibrariesHeader" alt="Libraries & Samples" width="42" height="42" style="display: block" />
      </div>
      <div class="header-title" style="display: inline">
        Libraries & Samples
      </div>

      <!-- Sticky right section for search, date range, advanced filters, select columns and export-->
      <div class="sticky-actions">
        <div class="search-bar">
          <input ref="searchInput" v-model="searchQuery" @keyup.enter="handleSearchAction" type="text"
            placeholder="Search" />
          <font-awesome-icon icon="fa-solid fa-magnifying-glass" style="color: darkgrey; cursor: pointer"
            @click="handleSearchAction" />
        </div>
        <div class="date-filters">
          <div class="date-filter">
            <label for="startDate">From</label>
            <input type="date" id="startDate" :class="{ 'invalid-date': !startDateValid }" v-model="startDateString"
              required />
          </div>
          <div class="date-filter">
            <label for="endDate">To</label>
            <input type="date" id="endDate" :class="{ 'invalid-date': !endDateValid }" v-model="endDateString"
              required />
          </div>
        </div>
        <div class="button-popup-wrapper">
          <button class="header-button" id="toggleAdvancedFiltersButton" @click="toggleAdvancedFilters">
            <font-awesome-icon icon="fa-solid fa-filter" style="color: white" />
            <span> Advanced Filters </span>
          </button>
          <div id="advancedFiltersPopup" v-if="showAdvancedFilters" class="button-popup-container"
            style="height: 473px; width: 250px; left: -50px">
            <!-- Status Filter -->
            <div class="filter-item">
              <label>Status</label>
              <select v-model="filters.status" @change="getLibrariesSamples(1)">
                <option :value="null">All Statuses</option>
                <option v-for="(text, num) in statusMap" :key="num" :value="num">
                  {{ text }}
                </option>
              </select>
            </div>

            <!-- Protocol Filter -->
            <div class="filter-item">
              <label>Protocol</label>
              <select v-model="filters.protocol" @change="getLibrariesSamples(1)">
                <option :value="null">All Protocols</option>
                <option v-for="protocol in protocolsList" :key="protocol.id" :value="protocol.id">
                  {{ protocol.name }}
                </option>
              </select>
            </div>

            <!-- Analysis Type Filter -->
            <div class="filter-item">
              <label>Analysis Type</label>
              <select v-model="filters.analysisType" @change="getLibrariesSamples(1)">
                <option :value="null">All Analysis Types</option>
                <option v-for="type in analysisTypesList" :key="type.id" :value="type.id">
                  {{ type.name }}
                </option>
              </select>
            </div>

            <!-- Sequencer Filter -->
            <div class="filter-item">
              <label>Sequencer</label>
              <select v-model="filters.sequencer" @change="getLibrariesSamples(1)">
                <option :value="null">All Sequencers</option>
                <option v-for="sequencer in sequencersList" :key="sequencer.id" :value="sequencer.id">
                  {{ sequencer.name }}
                </option>
              </select>
            </div>

            <!-- Read Length Filter -->
            <div class="filter-item">
              <label>Read Length</label>
              <select v-model="filters.readLength" @change="getLibrariesSamples(1)">
                <option :value="null">All Read Lengths</option>
                <option v-for="length in readLengthsList" :key="length.id" :value="length.id">
                  {{ length.name }}
                </option>
              </select>
            </div>

            <!-- Reset Filters Button -->
            <button @click="resetAdvancedFilters" class="reset-button">
              Reset Filters
            </button>
          </div>
        </div>
        <div class="button-popup-wrapper">
          <button class="header-button" id="toggleSelectColumnsButton" @click="toggleSelectColumns">
            <font-awesome-icon icon="fa-solid fa-columns" style="color: white" />
            <span> Select Columns </span>
          </button>
          <div id="selectColumnsPopup" v-if="showSelectColumns" class="button-popup-container" style="
              left: -50px;
              width: 250px;
              max-height: 473px;
              display: flex;
              flex-direction: column;
              padding: 10px 10px 5px 10px;
            ">
            <ul style="
                padding: 5px 7px 7px;
                margin: 0;
                flex-grow: 1;
                overflow-y: auto;
              ">
              <li v-for="(column, index) in columnsList" :key="index" style="list-style: none">
                <template v-if="
                  column.field !== 'selected' ||
                  (column.field === 'selected' && column.visible == false)
                ">
                  <label :style="{
                    backgroundColor: column.columns ? '#33333310' : 'white',
                    cursor: column.columns ? 'default' : 'pointer'
                  }">
                    <input v-if="!column.columns" type="checkbox" v-model="column.visible"
                      @change="toggleColumnVisibility(column)" />
                    <font-awesome-icon v-if="column.columns" icon="fa-solid fa-caret-down" style="
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        border: 2px solid black;
                        height: 18px;
                        width: 18px;
                        border-radius: 4px;
                        text-align: center;
                        background-color: orange;
                        color: white;
                      " />
                    <span>{{ column.title }}</span>
                  </label>
                </template>
              </li>
            </ul>
            <div style="
                padding-top: 8px;
                border-top: 1px solid #eee;
                display: flex;
                flex-direction: column;
              ">
              <button @click="resetColumnVisibility" class="reset-button">
                Reset Visibility Settings
              </button>
              <button style="margin-bottom: 5px" @click="resetColumnWidths" class="reset-button">
                Reset Width Settings
              </button>
            </div>
          </div>
        </div>
        <button class="header-button" id="openExportPopupButton" @click="handleExportClick">
          <font-awesome-icon icon="fa-solid fa-file-excel" style="color: white" />
          <span> Export to Excel </span>
        </button>

        <button class="header-button" type="button" @click="openRequestEditorModal">
          <font-awesome-icon icon="fa-solid fa-square-plus" style="color: white" />
          <span> Add Request </span>
        </button>
      </div>
    </div>

    <!-- Main content section with table -->
    <div class="table-container">
      <LiteTabulatorTable v-if="!loading" ref="tabulatorTableRef" :rowData="librariesSamplesList"
        :columnDefs="columnsList" groupBy="request_name" :groupSort="{ field: 'request_name', order: 'desc' }"
        :groupStartOpen="false" :tableOptions="{
          ...tableOptions,
          fakeLoadingStart,
          fakeLoadingStop,
          handleColumnResized,
          handleColumnVisibilityChanged
        }" />
    </div>

    <!-- Pagination controls -->
    <div v-if="!loading" class="pagination-controls">
      <div class="pagination-info">
        Page {{ pagination.currentPage }} of {{ pagination.totalPages }} ({{
          new Intl.NumberFormat().format(pagination.totalRequests)
        }}
        requests)
      </div>

      <div class="pagination-buttons">
        <button class="pagination-button" @click="changePage(1)" :disabled="pagination.currentPage === 1">
          &laquo; First
        </button>

        <button class="pagination-button" @click="changePage(pagination.currentPage - 1)"
          :disabled="pagination.currentPage === 1">
          &lsaquo; Prev
        </button>

        <div class="page-input">
          <input type="number" v-model.number="pageInput" min="1" :max="pagination.totalPages" @keyup.enter="goToPage"
            @blur="validatePageInput" />
          <span>of {{ pagination.totalPages }}</span>
        </div>

        <button class="pagination-button" @click="changePage(pagination.currentPage + 1)"
          :disabled="pagination.currentPage === pagination.totalPages">
          Next &rsaquo;
        </button>

        <button class="pagination-button" @click="changePage(pagination.totalPages)"
          :disabled="pagination.currentPage === pagination.totalPages">
          Last &raquo;
        </button>
      </div>

      <div class="page-size-selector">
        <label>Show:</label>
        <select v-model="pagination.pageSize" @change="handlePageSizeChange">
          <option value="100">100</option>
          <option value="300">300</option>
          <option value="500">500</option>
          <option value="1000">1000</option>
        </select>
        <span>per page</span>
      </div>
    </div>

    <!-- Popup for Add Request -->
    <RequestEditorView :show="showRequestEditorModal" :mode="requestModalMode" :request-id="requestModalRequestId"
      :request-meta="activeRequestMeta" :is-staff-user="isStaffUser" :user-id="userId"
      :saving="requestEditorSyncing" :close-on-save="false" :notify-on-save="false"
      @close="closeRequestEditorModal"
      @saved="handleRequestEditorSaved" />

    <!-- Popup for Export Options -->
    <div v-if="showExportPopup" class="popup-overlay" @dragover.prevent="handleDragOver" @drop="handleDrop"
      @dragenter="handleDragEnter" @dragleave="handleDragLeave" :class="{ 'drag-over': isDragOver }">
      <div v-if="isStaffUser" class="drag-drop-indicator">
        <div style="
            display: flex;
            justify-content: center;
            align-items: center;
            height: 200px;
          ">
          <p>
            Drop <span style="font-weight: bold">XLSX file</span> here to upload
            as <span style="font-weight: bold">template</span>
          </p>
        </div>
      </div>
      <div v-if="!isDragOver" class="popup-container" :style="{ width: '670px', height: '500px' }">
        <div class="popup-header">
          <span class="popup-title">Export Options</span>
          <span class="popup-info-button" @mouseover="showExportHelpTooltip = true"
            @mouseleave="showExportHelpTooltip = false">
            ?
            <div v-if="showExportHelpTooltip" class="tooltip-box">
              <span style="font-weight: bold">INSTRUCTIONS:</span>
              <ol>
                <li>
                  To create custom templates, export the original sheet named
                  <span style="font-weight: bold">'Parkour'</span> by selecting
                  the
                  <span style="font-weight: bold">'Export without any additional sheets'</span>
                  option.
                </li>
                <li>
                  Add new custom sheets to this exported file, which will serve
                  as templates.
                </li>
                <li>
                  Upload the modified file, containing both the original
                  <span style="font-weight: bold">'Parkour'</span> sheet and
                  newly added
                  <span style="font-weight: bold">custom sheets</span>. After
                  uploading the file will appear in the list.
                </li>
                <li>
                  The template is now ready! When you select this modified file
                  from the list, the system will replace the
                  <span style="font-weight: bold">'Parkour'</span> sheet with
                  updated data while keeping all additional sheets intact.
                </li>
              </ol>
            </div>
          </span>
          <button class="popup-close-button" @click="showExportPopup = false">
            &times;
          </button>
        </div>
        <div class="popup-body">
          <div class="export-section">
            <div style="font-weight: bold; margin-bottom: 8px">
              Export Options:
            </div>
            <div class="export-selection-radio-option">
              <input type="radio" id="export-selected" value="selected" v-model="exportSelection"
                :disabled="!hasSelectedRows" />
              <label for="export-selected" :class="{ disabled: !hasSelectedRows }">
                Export selected libraries & samples
              </label>
            </div>
            <div class="export-selection-radio-option">
              <input type="radio" id="export-all" value="all" v-model="exportSelection" />
              <label for="export-all"> Export all libraries & samples </label>
            </div>
          </div>
          <div v-if="isStaffUser" class="export-section" style="height: 100%">
            <div style="font-weight: bold; margin-bottom: 8px">
              Upload additional excel sheet templates to append:
            </div>
            <div class="file-list-section">
              <div class="file-item">
                <div class="file-info">
                  <img :src="iconExportTemplateFile" alt="Export without any additional sheets" width="24" height="24"
                    style="display: block" />
                  <span>Export without any additional sheets</span>
                </div>
                <div class="file-actions">
                  <div class="file-actions-radio-button" style="border: none; margin-right: 5px">
                    <input type="radio" title="Select" id="without-file" value="without-file" v-model="selectedFile" />
                  </div>
                </div>
              </div>
              <div v-for="(file, index) in fetchedLibrariesAndSamplesTemplates" :key="index" class="file-item">
                <div class="file-info">
                  <img :src="iconExportTemplateFileLines" :alt="file.name" width="24" height="24"
                    style="display: block" />
                  <span>{{ file.name }}</span>
                </div>
                <div class="file-actions">
                  <button @click="downloadExportTemplate(file)" class="download-button" title="Download Original File">
                    <img :src="iconExportDownload" alt="Download" width="24" height="24" style="display: block" />
                  </button>
                  <button @click="removeExportTemplate(index)" class="remove-button" title="Remove File">
                    <img :src="iconExportRemove" alt="Remove" width="24" height="24" style="display: block" />
                  </button>
                  <div class="file-actions-radio-button">
                    <input type="radio" title="Select File" :id="'file-radio-' + index" :value="file"
                      v-model="selectedFile" />
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="export-section" style="height: 100%">
            <div style="font-weight: bold; margin-bottom: 8px">
              Upload additional excel sheet templates to append:
            </div>
            <p style="margin: 0; color: #666">
              Additional templates and uploads are limited to staff members.
            </p>
          </div>
        </div>
        <div class="popup-footer">
          <div v-if="isStaffUser" class="file-upload-section">
            <label for="file-upload" class="file-upload-label"
              title="Upload additional sheet to append to the exported sheet.">
              <img :src="iconExportUpload" alt="Upload" width="24" height="24"
                style="display: block; margin-right: 4px" />
              <span>Upload</span>
            </label>
            <input id="file-upload" type="file" accept=".xlsx" @change="uploadExportTemplate" style="display: none" />
          </div>
          <button class="popup-button yes-button" @click="handleExport">
            OK
          </button>
          <button class="popup-button" @click="
            showExportPopup = false;
          selectedFile = 'without-file';
          ">
            Cancel
          </button>
        </div>
      </div>
    </div>

    <RequestActionsPopups :active-action="activeRequestAction" :request-context="activeRequestContext"
      :is-staff-user="isStaffUser" :paperless-approval="paperlessApproval" @close="closeRequestActionModal"
      @refresh="handleRequestActionRefresh" />
  </div>
</template>

<script lang="jsx">
import LiteTabulatorTable from "../components/TabulatorTableLite.vue";
import { saveAs } from "file-saver";
import {
  showNotification,
  handleError,
  createAxiosObject,
  urlStringStartsWith,
  isValidDate,
  formatDateForInput,
  formatDisplayDate,
  createExcelExportBlob
} from "../utilities/utilityFunctions";
import {
  librariesAndSamplesGroupHeader,
  librariesAndSamplesColumnDefs,
  librariesAndSamplesExportColumns
} from "../constants/librariesAndSamplesConsts";
import { statusMap } from "../constants/statusConsts";
import RequestEditorView from "./requestEditorView.vue";
import RequestActionsPopups from "../components/RequestActionsPopups.vue";
import iconLibrariesHeader from "../assets/icons/header_libraries_samples.svg";
import iconExportTemplateFile from "../assets/icons/export_template.svg";
import iconExportTemplateFileLines from "../assets/icons/export_template_lines.svg";
import iconExportDownload from "../assets/icons/export_download.svg";
import iconExportRemove from "../assets/icons/export_remove.svg";
import iconExportUpload from "../assets/icons/export_upload.svg";
const axiosRef = createAxiosObject();
const urlStringStart = urlStringStartsWith();

export default {
  name: "LibrariesAndSamples",
  components: {
    LiteTabulatorTable,
    RequestEditorView,
    RequestActionsPopups
  },
  data() {
    const today = new Date();
    const initialStartDate = new Date();
    initialStartDate.setFullYear(today.getFullYear() - 10);
    return {
      iconLibrariesHeader,
      iconExportTemplateFile,
      iconExportTemplateFileLines,
      iconExportDownload,
      iconExportRemove,
      iconExportUpload,
      tabulatorInstance: null,
      loading: true,
      syncLoading: false,
      fakeLoading: false,
      exportLoading: false,
      isDragOver: false,
      librariesSamplesList: [],
      columnsList: [],
      showExportPopup: false,
      showExportHelpTooltip: false,
      fetchedLibrariesAndSamplesTemplates: [],
      selectedFile: "without-file",
      exportSelection: "selected",
      hasSelectedRows: false,
      isStaffUser: false,
      userId: null,
      pagination: {
        currentPage: 1,
        pageSize: 300,
        totalPages: 1,
        totalRequests: 0
      },
      pageInput: 1,
      tableOptions: {
        index: "barcode",
        placeholder: "No Libraries and Samples to show.",
        initialSort: [
          { column: "name", dir: "asc" },
          { column: "barcode", dir: "asc" }
        ],
        groupHeader: (value, count, data) => {
          const uniqueTypes = [
            ...new Set(
              data
                .map((item) => String(item.type || "").trim().toUpperCase())
                .filter((type) => type === "L" || type === "S")
            )
          ];
          const countLabel =
            uniqueTypes.length === 1
              ? uniqueTypes[0] === "L"
                ? "Libraries"
                : "Samples"
              : "Libraries/Samples";
          let totalDepth = data.reduce(
            (sum, row) => sum + (row.sequencing_depth || 0),
            0
          );

          totalDepth = Number(totalDepth.toFixed(1));

          const rows = Array.isArray(data) ? data : [];
          const requiresApproval =
            rows.length > 0 && rows.every((row) => Number(row.status) === 0);
          const requestId = rows[0]?.request_id;
          const meta = requestId ? this.requestMetaById[requestId] : null;
          const allowDelete = meta ? !meta.restrict_permissions : false;
          const canDownloadUpload =
            meta ? meta.deep_seq_request_path === "" : false;
          const hasAttachments =
            Array.isArray(meta?.files) && meta.files.length > 0;

          return librariesAndSamplesGroupHeader(value, count, countLabel, totalDepth, {
            showStaffActions: this.isStaffUser,
            showSolicitApproval: requiresApproval && this.paperlessApproval,
            allowDelete,
            showApprovalTag: requiresApproval && this.paperlessApproval,
            hasAttachments,
            canDownloadRequestForm: canDownloadUpload,
            canUploadSignedRequest: canDownloadUpload
          });
        }
      },
      searchQuery: "",
      filters: {
        status: null,
        protocol: null,
        analysisType: null,
        sequencer: null,
        readLength: null
      },
      protocolsList: [],
      analysisTypesList: [],
      sequencersList: [],
      readLengthsList: [],
      startDate: initialStartDate,
      endDate: today,
      startDateString: formatDateForInput(initialStartDate),
      endDateString: formatDateForInput(today),
      startDateValid: true,
      endDateValid: true,
      dateChangeTimer: null,
      showAdvancedFilters: false,
      showSelectColumns: false,
      inputColumnMode: "mode_user",
      showRequestEditorModal: false,
      requestModalMode: "create",
      requestModalRequestId: null,
      activeRequestMeta: null,
      activeRequestAction: null,
      activeRequestContext: null,
      requestEditorSyncing: false,
      requestEditorSyncTimer: null,
      pendingSavedRequestId: null,
      pendingSavedMode: null,
      paperlessApproval: false,
      requestMetaById: {}
    };
  },
  mounted() {
    this.getLibrariesSamples(1);
    this.setColumns();
    this.fetchFilterOptions();
    this.fetchStaffStatus();

    document.addEventListener("click", this.handleOutsideClick);
    document.addEventListener("keydown", this.handleKeyDown);
    window.handleGroupButtonClick = this.handleGroupButtonClick.bind(this);
  },
  updated() {
    this.tabulatorInstance = this.$refs.tabulatorTableRef;
  },
  beforeDestroy() {
    document.removeEventListener("click", this.handleOutsideClick);
    document.removeEventListener("keydown", this.handleKeyDown);
    this.stopRequestEditorSync();
  },
  computed: {
    statusMap() {
      return statusMap;
    }
  },
  watch: {
    "pagination.currentPage"(newPage) {
      this.pageInput = newPage;
    },
    startDateString(newVal) {
      this.handleDateChange("start", newVal);
    },
    endDateString(newVal) {
      this.handleDateChange("end", newVal);
    }
  },
  methods: {
    async fetchStaffStatus() {
      try {
        const response = await axiosRef.get(
          `${urlStringStart}/api_user_details`
        );
        const payload = response.data ? response.data.USER : null;
        const user =
          typeof payload === "string" ? JSON.parse(payload) : payload;
        const staffFlag = user?.is_staff;
        this.userId = user?.id;
        this.isStaffUser = staffFlag === true;
        this.paperlessApproval = user?.paperless_approval === true;
        if (this.isStaffUser) {
          this.fetchExportTemplates();
        }
        this.refreshGroupHeaders();
      } catch (error) {
        showNotification("User details fetch failed.", "error");
        this.isStaffUser = false;
      }
    },
    async getLibrariesSamples(page = 1, exportOnly, silent = false) {
      if (silent) {
        if (this.syncLoading) return;
        this.syncLoading = true;
      } else {
        this.loading = true;
      }
      try {
        const params = {
          start_date: formatDisplayDate(this.startDate),
          end_date: formatDisplayDate(this.endDate),
          page: page
        };

        if (!exportOnly) {
          params.size = this.pagination.pageSize;
        }

        // Add search parameter if exists
        if (this.searchQuery) {
          params.search = this.searchQuery;
        }

        // Add advanced filter parameters
        if (this.filters.status !== null) {
          params.status = this.filters.status;
        }
        if (this.filters.protocol !== null) {
          params.library_protocol = this.filters.protocol;
        }
        if (this.filters.analysisType !== null) {
          params.analysis_type = this.filters.analysisType;
        }
        if (this.filters.sequencer !== null) {
          params.sequencer = this.filters.sequencer;
        }
        if (this.filters.readLength !== null) {
          params.read_length = this.filters.readLength;
        }

        let response = await axiosRef.get(
          urlStringStart + "/api/libraries_and_samples/",
          { params }
        );

        if (!exportOnly) {
          this.pagination = {
            currentPage: page,
            pageSize: response.data.page_size,
            totalPages: response.data.total_pages,
            totalRequests: response.data.total
          };
        }

        const getValue = (val) => (val === 0 ? 0 : val || "");
        const buildInputValue = (measuredValueRaw, measuredUnitRaw) => {
          const measuredValueEmpty =
            measuredValueRaw === null ||
            measuredValueRaw === undefined ||
            measuredValueRaw === "";
          const measuredUnitEmpty =
            measuredUnitRaw === null ||
            measuredUnitRaw === undefined ||
            measuredUnitRaw === "";
          if (measuredValueEmpty && measuredUnitEmpty) {
            return "";
          }
          const measuredValue = getValue(measuredValueRaw);
          const measuredUnit = measuredUnitRaw || "";
          if (measuredValue === -1 && measuredUnit === "Unknown")
            return "Unknown";
          if (measuredValueEmpty && !measuredUnitEmpty) {
            return measuredUnit;
          }
          if (measuredUnit !== "") return `${measuredValue} ${measuredUnit}`;
          return `${measuredValue}`;
        };
        const getInput = (record) =>
          buildInputValue(record.measured_value, record.measuring_unit);
        const getInputFacility = (record) =>
          buildInputValue(
            record.measured_value_facility,
            record.measuring_unit_facility
          );
        const getFormattedDate = (str) => {
          const date = new Date(str);
          if (isNaN(date)) return "";
          const day = String(date.getDate()).padStart(2, "0");
          const month = String(date.getMonth() + 1).padStart(2, "0");
          const year = date.getFullYear();
          return `${day}.${month}.${year}`;
        };

        const coordinates = Array.from({ length: 96 }, (_, i) => {
          const row = String.fromCharCode(65 + (i % 8));
          const col = Math.floor(i / 8) + 1;
          return `${row}${col}`;
        });

        const groupsMap = new Map();
        const requestNamesSet = new Set();
        const allRows = [];
        const requestsMeta = response.data?.requests || {};

        (response.data?.children || []).forEach((e) => {
          const row = {
            pk: e.pk ?? "",
            record_type: e.record_type ?? "",
            request_id: e.request_id ?? "",
            request_name: e.request_name ?? "",
            name: e.name ?? "",
            type: e.barcode?.[2] ?? "",
            barcode: e.barcode ?? "",
            nucleic_acid_type_name: e.nucleic_acid_type_name ?? "",
            library_protocol_name: e.library_protocol_name ?? "",
            analysis_type_name: e.analysis_type_name ?? "",
            starting_amount: getValue(e.starting_amount),
            pcr_cycles: getValue(e.pcr_cycles),
            input: getInput(e),
            input_facility: getInputFacility(e),
            input_display: "",
            average_fragment_size: getValue(e.average_fragment_size),
            sequencing_depth: getValue(e.sequencing_depth),
            read_length_name: getValue(e.read_length_name),
            gmo: e.gmo === null ? "" : e.gmo === true ? "Yes" : "No",
            pool_names:
              Array.isArray(e.pool_names) && e.pool_names.length > 0
                ? e.pool_names.join(", ")
                : "",
            status: getValue(e.status),
            status_text: statusMap[e.status] ?? "-",
            well_position: "",
            concentration_library: getValue(e.concentration_library),
            create_time: e.create_time ? getFormattedDate(e.create_time) : "",
            index_type_name: e.index_type_name ?? "",
            coordinate: e.coordinate ?? "",
            i7_id: e.i7_id ?? "",
            i5_id: e.i5_id ?? "",
            index_i7: e.index_i7 ?? "",
            index_i5: e.index_i5 ?? "",
            flowcell_ids:
              Array.isArray(e.flowcell_ids) && e.flowcell_ids.length > 0
                ? e.flowcell_ids.join(", ")
                : "",
            sequencer_names:
              Array.isArray(e.sequencer_names) && e.sequencer_names.length > 0
                ? e.sequencer_names.join(", ")
                : ""
          };

          allRows.push(row);

          if (row.request_name && !requestNamesSet.has(row.request_name)) {
            requestNamesSet.add(row.request_name);
          }

          if (!groupsMap.has(row.request_name)) {
            groupsMap.set(row.request_name, []);
          }
          groupsMap.get(row.request_name).push(row);
        });

        for (const group of groupsMap.values()) {
          group.sort((a, b) =>
            (a.barcode || "").localeCompare(b.barcode || "", undefined, {
              numeric: true,
              sensitivity: "base"
            })
          );

          group.forEach((row, idx) => {
            row.well_position = coordinates[idx % 96];
          });
        }

        this.applyInputColumnMode(allRows);

        if (exportOnly) {
          return allRows;
        }

        this.librariesSamplesList = allRows;
        if (requestsMeta && Object.keys(requestsMeta).length) {
          this.requestMetaById = {
            ...this.requestMetaById,
            ...requestsMeta
          };
          this.refreshGroupHeaders();
        }
      } catch (error) {
        handleError(error);
      } finally {
        if (silent) {
          this.syncLoading = false;
        } else {
          this.loading = false;
        }
      }
    },
    async getROCrateData({ barcodes = [], requestName = "" } = {}) {
      if (!Array.isArray(barcodes) || barcodes.length === 0) {
        showNotification(
          "Select records to download RO-Crate.",
          "warning"
        );
        return;
      }

      try {
        this.exportLoading = true;

        const params = {
          barcodes: barcodes.join(",")
        };

        const response = await axiosRef.get(
          `${urlStringStart}/api/generate_ro_crate/`,
          { params }
        );

        const dataStr = JSON.stringify(response.data, null, 2);
        const blob = new Blob([dataStr], { type: "application/ld+json" });
        const url = URL.createObjectURL(blob);

        const link = document.createElement("a");
        link.href = url;
        const sanitize = (value) =>
          String(value || "")
            .replace(/[^a-z0-9-_.]+/gi, "_")
            .replace(/_+/g, "_")
            .replace(/^_|_$/g, "");
        const safeBarcodeName = sanitize(barcodes.join("_"));
        const filename = safeBarcodeName
          ? `${safeBarcodeName}_ro_crate.jsonld`
          : "ro_crate.jsonld";
        link.download = filename;
        document.body.appendChild(link);
        link.click();

        document.body.removeChild(link);
        URL.revokeObjectURL(url);

        showNotification("RO-Crate downloaded successfully.", "success");
      } catch (error) {
        handleError(error);
      } finally {
        if (this.exportLoading) {
          this.exportLoading = false;
        }
      }
    },
    async fetchFilterOptions() {
      try {
        const protocolsRes = await axiosRef.get(
          `${urlStringStart}/api/library_protocols/`
        );
        this.protocolsList = protocolsRes.data.sort((a, b) =>
          a.name.localeCompare(b.name, undefined, { sensitivity: "base" })
        );
        const readLengthsRes = await axiosRef.get(
          `${urlStringStart}/api/read_lengths/`
        );
        this.readLengthsList = readLengthsRes.data.sort((a, b) => {
          const getVal = (str) => str.match(/\d+/g)?.map(Number)[1] ?? Infinity;
          return getVal(a.name) - getVal(b.name);
        });
        const analysisRes = await axiosRef.get(
          `${urlStringStart}/api/library_types/`
        );
        this.analysisTypesList = analysisRes.data.sort((a, b) =>
          a.name.localeCompare(b.name, undefined, { sensitivity: "base" })
        );
        const sequencersRes = await axiosRef.get(
          `${urlStringStart}/api/sequencers/`
        );
        this.sequencersList = sequencersRes.data.sort((a, b) =>
          a.name.localeCompare(b.name, undefined, { sensitivity: "base" })
        );
      } catch (error) {
        handleError(error);
      }
    },
    handleSearchAction() {
      if (this.loading) return;
      const query = this.searchQuery?.trim() || "";
      this.searchQuery = query;
      this.getLibrariesSamples(1);
    },
    resetAdvancedFilters() {
      this.filters = {
        status: null,
        protocol: null,
        analysisType: null,
        sequencer: null,
        readLength: null
      };
      this.getLibrariesSamples(1);
    },
    syncInputHeaderMode(mode = this.inputColumnMode) {
      const normalizedMode =
        mode === "mode_facility" ? "mode_facility" : "mode_user";
      const inputColumn = this.columnsList.find(
        (column) => column.field === "input_display"
      );
      if (!inputColumn) return;
      inputColumn.titleFormatterParams = {
        ...(inputColumn.titleFormatterParams || {}),
        inputColumnMode: normalizedMode
      };
    },
    setColumns() {
      const storedVisibility = JSON.parse(
        localStorage.getItem("librariesAndSamplesColumnVisibility") || "{}"
      );
      const storedWidths = JSON.parse(
        localStorage.getItem("librariesAndSamplesColumnWidths") || "{}"
      );

      const storedInputColumnMode = localStorage.getItem(
        "librariesAndSamplesInputColumnMode"
      );
      if (
        storedInputColumnMode === "mode_facility" ||
        storedInputColumnMode === "mode_user"
      ) {
        this.inputColumnMode = storedInputColumnMode;
      }

      const applySettings = (columns) => {
        return columns.map((column) => {
          if (column.field) {
            if (
              Object.prototype.hasOwnProperty.call(storedWidths, column.field)
            ) {
              column.width = storedWidths[column.field];
              if (column.minWidth && column.width < column.minWidth) {
                column.width = column.minWidth;
              }
            }
            if (
              Object.prototype.hasOwnProperty.call(
                storedVisibility,
                column.field
              )
            ) {
              column.visible = storedVisibility[column.field];
            } else {
              column.visible = column.visible ?? true;
            }
          }
          if (column.columns) {
            column.columns = applySettings(column.columns);
          }
          return column;
        });
      };

      let columnDefs = librariesAndSamplesColumnDefs(
        () => this.tabulatorInstance,
        {
          inputColumnMode: this.inputColumnMode,
          onInputColumnModeChange: this.handleInputColumnModeChange.bind(this)
        }
      );

      this.columnsList = applySettings(columnDefs);
      this.syncInputHeaderMode();
    },
    handleOutsideClick(event) {
      const advancedFiltersPopup = this.$el.querySelector(
        "#advancedFiltersPopup"
      );
      const advancedFiltersButton = this.$el.querySelector(
        "#toggleAdvancedFiltersButton"
      );
      const selectColumnsPopup = this.$el.querySelector("#selectColumnsPopup");
      const selectColumnsButton = this.$el.querySelector(
        "#toggleSelectColumnsButton"
      );
      const exportPopup = this.$el.querySelector(".popup-container");
      const exportButton = this.$el.querySelector("#openExportPopupButton");

      if (
        this.showAdvancedFilters &&
        advancedFiltersPopup &&
        !advancedFiltersPopup.contains(event.target) &&
        advancedFiltersButton !== event.target &&
        !advancedFiltersButton.contains(event.target)
      ) {
        this.showAdvancedFilters = false;
      }

      if (
        this.showSelectColumns &&
        selectColumnsPopup &&
        !selectColumnsPopup.contains(event.target) &&
        selectColumnsButton !== event.target &&
        !selectColumnsButton.contains(event.target)
      ) {
        this.showSelectColumns = false;
      }

      const clickOnExportButton =
        exportButton &&
        (exportButton === event.target || exportButton.contains(event.target));

      if (
        this.showExportPopup &&
        exportPopup &&
        !exportPopup.contains(event.target) &&
        !clickOnExportButton
      ) {
        this.showExportPopup = false;
      }
    },
    handleKeyDown(event) {
      const isEscape = event.key === "Escape";
      if (isEscape && this.showExportPopup) {
        this.showExportPopup = false;
        return;
      }
      if (isEscape && this.showAdvancedFilters) {
        this.showAdvancedFilters = false;
        return;
      }
      if (isEscape && this.showSelectColumns) {
        this.showSelectColumns = false;
        return;
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
    handleDateChange(type, value) {
      clearTimeout(this.dateChangeTimer);
      this[`${type}DateValid`] = isValidDate(value);
      if (!this[`${type}DateValid`]) return;
      this.dateChangeTimer = setTimeout(() => {
        this.updateActualDate(type, value);
        this.validateDateRange();
        this.getLibrariesSamples(1);
      }, 500);
    },
    updateActualDate(type, value) {
      const newDate = new Date(value);
      this[`${type}Date`] = newDate;
      this[`lastValid${type.charAt(0).toUpperCase() + type.slice(1)}Date`] =
        newDate;
    },
    validateDateRange() {
      const sStr = this.startDateString;
      const eStr = this.endDateString;
      if (!isValidDate(sStr) || !isValidDate(eStr)) return;

      const sd = new Date(`${sStr}T00:00:00`);
      const ed = new Date(`${eStr}T00:00:00`);

      if (sd.getTime() > ed.getTime()) {
        showNotification("Start date must precede end date.", "warning");
        this.startDateValid = false;
        this.endDateValid = false;
      } else {
        this.startDateValid = true;
        this.endDateValid = true;
      }
    },
    toggleAdvancedFilters() {
      this.showAdvancedFilters = !this.showAdvancedFilters;
      if (this.showAdvancedFilters) {
        this.showSelectColumns = false;
      }
    },
    toggleSelectColumns() {
      this.showSelectColumns = !this.showSelectColumns;
    },
    handleColumnResized(column) {
      const field = column.getField();
      const width = column.getWidth();
      const storedWidths = JSON.parse(
        localStorage.getItem("librariesAndSamplesColumnWidths") || "{}"
      );
      const newWidths = {
        ...storedWidths,
        [field]: width
      };
      localStorage.setItem(
        "librariesAndSamplesColumnWidths",
        JSON.stringify(newWidths)
      );
      this.fakeLoadingStart();
      setTimeout(() => this.fakeLoadingStop(), 50);
    },
    handleColumnVisibilityChanged(field, visible) {
      const storedVisibility = JSON.parse(
        localStorage.getItem("librariesAndSamplesColumnVisibility") || "{}"
      );

      const newVisibility = {
        ...storedVisibility,
        [field]: visible
      };

      localStorage.setItem(
        "librariesAndSamplesColumnVisibility",
        JSON.stringify(newVisibility)
      );

      this.fakeLoadingStart();
      setTimeout(() => this.fakeLoadingStop(), 50);
    },
    toggleColumnVisibility(column) {
      if (this.tabulatorInstance) {
        this.tabulatorInstance.getTable().toggleColumn(column.field);
      }
    },
    resetColumnWidths() {
      localStorage.removeItem("librariesAndSamplesColumnWidths");
      this.setColumns();
      this.fakeLoadingStart();
      setTimeout(() => this.fakeLoadingStop(), 300);
    },
    resetColumnVisibility() {
      localStorage.removeItem("librariesAndSamplesColumnVisibility");
      this.setColumns();
      this.fakeLoadingStart();
      setTimeout(() => this.fakeLoadingStop(), 300);
    },
    async handleInputColumnModeChange(mode) {
      const normalizedMode =
        mode === "mode_facility" ? "mode_facility" : "mode_user";
      if (this.inputColumnMode === normalizedMode) return;
      this.fakeLoadingStart();
      try {
        this.inputColumnMode = normalizedMode;
        localStorage.setItem(
          "librariesAndSamplesInputColumnMode",
          this.inputColumnMode
        );
        this.syncInputHeaderMode(normalizedMode);
        this.applyInputColumnMode();
        await this.tabulatorInstance
          .getTable()
          .replaceData(this.librariesSamplesList);
      } finally {
        setTimeout(() => this.fakeLoadingStop(), 200);
      }
    },
    applyInputColumnMode(rows = this.librariesSamplesList) {
      if (!Array.isArray(rows)) return;
      const sourceField =
        this.inputColumnMode === "mode_facility" ? "input_facility" : "input";
      rows.forEach((row) => {
        row.input_display = row?.[sourceField] ?? "";
      });
    },
    buildOptionMap(options = []) {
      const map = new Map();
      options.forEach((option) => {
        if (!option) return;
        const key =
          option.id ??
          option.pk ??
          option.value ??
          option.name ??
          option.label;
        const label =
          option.name ?? option.label ?? option.text ?? option.value ?? "";
        if (key !== undefined && key !== null) {
          map.set(String(key), String(label));
        }
      });
      return map;
    },
    applyRequestEditorUpdate(payload) {
      if (!payload?.request_id || !Array.isArray(this.librariesSamplesList)) {
        return;
      }
      const protocolMap = this.buildOptionMap(this.protocolsList);
      const analysisMap = this.buildOptionMap(this.analysisTypesList);
      const readLengthMap = this.buildOptionMap(this.readLengthsList);
      const formatInputValue = (measuredValueRaw, measuredUnitRaw) => {
        const measuredValueEmpty =
          measuredValueRaw === null ||
          measuredValueRaw === undefined ||
          measuredValueRaw === "";
        const measuredUnitEmpty =
          measuredUnitRaw === null ||
          measuredUnitRaw === undefined ||
          measuredUnitRaw === "";
        if (measuredValueEmpty && measuredUnitEmpty) {
          return "";
        }
        const measuredValue = measuredValueRaw === 0 ? 0 : measuredValueRaw || "";
        const measuredUnit = measuredUnitRaw || "";
        if (measuredValue === -1 && measuredUnit === "Unknown") return "Unknown";
        if (measuredValueEmpty && !measuredUnitEmpty) {
          return measuredUnit;
        }
        if (measuredUnit !== "") return `${measuredValue} ${measuredUnit}`;
        return `${measuredValue}`;
      };
      const rowByBarcode = new Map(
        this.librariesSamplesList.map((row) => [row.barcode, row])
      );
      const allRecords = [
        ...(payload.records?.library || []),
        ...(payload.records?.sample || [])
      ];
      allRecords.forEach((record) => {
        const row = rowByBarcode.get(record.barcode);
        if (!row) return;
        if (record.name !== undefined) row.name = record.name;
        if (record.read_length !== undefined) {
          row.read_length_name =
            readLengthMap.get(String(record.read_length)) || row.read_length_name;
        }
        if (record.library_protocol !== undefined) {
          row.library_protocol_name =
            protocolMap.get(String(record.library_protocol)) ||
            row.library_protocol_name;
        }
        if (record.library_type !== undefined) {
          row.analysis_type_name =
            analysisMap.get(String(record.library_type)) ||
            row.analysis_type_name;
        }
        if (record.sequencing_depth !== undefined) {
          row.sequencing_depth = record.sequencing_depth;
        }
        if (record.index_i7 !== undefined) row.index_i7 = record.index_i7 || "";
        if (record.index_i5 !== undefined) row.index_i5 = record.index_i5 || "";
        if (
          record.measured_value !== undefined ||
          record.measuring_unit !== undefined
        ) {
          row.input = formatInputValue(
            record.measured_value,
            record.measuring_unit
          );
        }
        if (record.gmo !== undefined && record.record_type === "Sample") {
          row.gmo = record.gmo === null ? "" : record.gmo ? "Yes" : "No";
        }
      });
      this.applyInputColumnMode(this.librariesSamplesList);
      this.hasSelectedRows = this.librariesSamplesList.some((row) => row.selected);
      this.tabulatorInstance?.getTable?.().replaceData(this.librariesSamplesList);
    },
    openRequestEditorModal() {
      this.requestModalMode = "create";
      this.requestModalRequestId = null;
      this.activeRequestMeta = null;
      this.showRequestEditorModal = true;
    },
    closeRequestEditorModal() {
      this.showRequestEditorModal = false;
      this.requestModalMode = "create";
      this.requestModalRequestId = null;
      this.activeRequestMeta = null;
      this.stopRequestEditorSync();
    },
    handleRequestEditorSaved(payload) {
      if (payload?.mode === "edit" && payload?.request_id) {
        this.pendingSavedMode = "edit";
        this.applyRequestEditorUpdate(payload);
        const requestId = payload.request_id;
        const existing = this.requestMetaById?.[requestId] || {};
        const nextMeta = {
          ...existing,
          cost_unit: payload.cost_unit ?? existing.cost_unit ?? "",
          description: payload.description ?? existing.description ?? "",
          files: Array.isArray(payload.files) ? payload.files : existing.files
        };
        this.requestMetaById = {
          ...this.requestMetaById,
          [requestId]: nextMeta
        };
        if (this.activeRequestMeta && this.requestModalRequestId === requestId) {
          this.activeRequestMeta = nextMeta;
        }
        this.finishRequestEditorSync();
        return;
      }
      // New requests may be hidden by active search/filters; clear them so sync polling can detect the saved request.
      this.searchQuery = "";
      this.filters = {
        status: null,
        protocol: null,
        analysisType: null,
        sequencer: null,
        readLength: null
      };
      const requestId = payload?.pk ?? null;
      this.pendingSavedMode = this.requestModalMode;
      this.startRequestEditorSync(requestId);
    },
    startRequestEditorSync(requestId = null) {
      if (this.requestEditorSyncTimer) {
        clearInterval(this.requestEditorSyncTimer);
        this.requestEditorSyncTimer = null;
      }
      this.pendingSavedRequestId = requestId;
      this.requestEditorSyncing = true;

      if (!this.pendingSavedRequestId) {
        this.getLibrariesSamples(1, false, true).finally(() => {
          this.finishRequestEditorSync();
        });
        return;
      }

      const poll = async () => {
        if (this.loading || this.syncLoading) return;
        await this.getLibrariesSamples(1, false, true);
        if (
          this.pendingSavedRequestId &&
          this.requestMetaById?.[this.pendingSavedRequestId]
        ) {
          this.finishRequestEditorSync();
        }
      };

      const initialDelayMs = 2000;
      setTimeout(() => {
        poll();
        this.requestEditorSyncTimer = setInterval(poll, 2000);
      }, initialDelayMs);
    },
    stopRequestEditorSync() {
      if (this.requestEditorSyncTimer) {
        clearInterval(this.requestEditorSyncTimer);
        this.requestEditorSyncTimer = null;
      }
      this.pendingSavedRequestId = null;
      this.pendingSavedMode = null;
      this.requestEditorSyncing = false;
    },
    finishRequestEditorSync() {
      const message =
        this.pendingSavedMode === "edit"
          ? "Request updated successfully."
          : "Request created successfully.";
      showNotification(message, "success");
      this.stopRequestEditorSync();
      this.closeRequestEditorModal();
    },
    openEditRequestModal(requestId) {
      if (!requestId) return;
      this.requestModalMode = "edit";
      this.requestModalRequestId = requestId;
      this.activeRequestMeta = this.requestMetaById?.[requestId] || null;
      this.showRequestEditorModal = true;
    },
    openRequestActionModal(action, context) {
      this.activeRequestAction = action;
      this.activeRequestContext = context;
    },
    closeRequestActionModal() {
      this.activeRequestAction = null;
      this.activeRequestContext = null;
    },
    handleRequestActionRefresh() {
      this.requestMetaById = {};
      this.getLibrariesSamples(this.pagination.currentPage || 1);
    },
    async fetchRequestMeta(requestId) {
      if (!requestId) return null;
      if (this.requestMetaById[requestId]) {
        return this.requestMetaById[requestId];
      }
      try {
        const response = await axiosRef.get(
          `${urlStringStart}/api/requests/${requestId}/`
        );
        const data = response?.data || null;
        if (data) {
          this.requestMetaById = {
            ...this.requestMetaById,
            [requestId]: data
          };
        }
        return data;
      } catch (error) {
        handleError(error);
        return null;
      }
    },
    triggerDownload(url, filename) {
      const link = document.createElement("a");
      link.href = url;
      if (filename) {
        link.setAttribute("download", filename);
      }
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    },
    async handleDownloadRequestForm(requestId) {
      const meta = await this.fetchRequestMeta(requestId);
      if (!meta || meta.deep_seq_request_path !== "") return;
      const url = `${urlStringStart}/api/requests/${requestId}/download_deep_sequencing_request/`;
      this.triggerDownload(url);
      showNotification("Request form downloaded.", "success");
    },
    async handleUploadSignedRequest(requestId, requestName) {
      const meta = await this.fetchRequestMeta(requestId);
      if (!meta || meta.deep_seq_request_path !== "") return;
      this.openRequestActionModal("uploadSigned", {
        id: requestId,
        name: requestName
      });
    },
    refreshGroupHeaders() {
      const table = this.tabulatorInstance?.getTable?.();
      const groups = table?.getGroups?.() || [];
      groups.forEach((group) => {
        group?._group?.generateGroupHeaderContents?.();
      });
    },
    async handleGroupButtonClick(event, groupValue, action) {
      event.stopPropagation();

      const group = this.tabulatorInstance
        .getTable()
        .getGroups()
        .find((g) => g.getKey() === groupValue);
      if (!group) return;
      const groupRows = group.getRows();
      if (!groupRows.length) return;
      const groupElement = group.getElement();
      const selectedRows = groupRows.filter((row) => row.getData().selected);
      const type = selectedRows[0] && selectedRows[0].getData().type;
      const requestName = group._group.key;
      let requestId = groupRows[0]?.getData?.().request_id;
      if (!requestId && requestName) {
        const match = String(requestName).match(/^(\d+)_/);
        if (match) {
          requestId = Number(match[1]);
        }
      }
      const selectedNamesList = selectedRows.map((item) => {
        return { barcode: item.getData().barcode, name: item.getData().name };
      });
      const popupHeight = Math.min(420, 260 + selectedNamesList.length * 22);

      switch (action) {
        case "selectAll":
          groupRows.forEach((row) => {
            const data = row.getData();
            data.selected = true;
            row.update({});
            const rowElement = row.getElement();
            const checkbox = rowElement.querySelector('input[type="checkbox"]');
            if (checkbox) {
              checkbox.checked = true;
            }
          });
          if (!group._group.visible) groupElement.click();
          break;

        case "deselectAll":
          groupRows.forEach((row) => {
            const data = row.getData();
            data.selected = false;
            row.update({});
            const rowElement = row.getElement();
            const checkbox = rowElement.querySelector('input[type="checkbox"]');
            if (checkbox) {
              checkbox.checked = false;
            }
          });
          if (!group._group.visible) groupElement.click();
          break;
        case "viewRequest":
          this.openEditRequestModal(requestId);
          break;
        case "attachments": {
          const cachedMeta = this.requestMetaById?.[requestId] || null;
          const canEditRequest =
            this.isStaffUser || !cachedMeta?.restrict_permissions;
          const records = groupRows
            .map((row) => row.getData?.() || {})
            .filter((row) => row?.pk && row?.record_type)
            .map((row) => ({
              pk: row.pk,
              record_type: row.record_type
            }));
          this.openRequestActionModal("attachments", {
            id: requestId,
            name: requestName,
            canEditRequest,
            meta: cachedMeta,
            records
          });
          if (!cachedMeta) {
            this.fetchRequestMeta(requestId).then((meta) => {
              if (!meta) return;
              if (
                this.activeRequestAction !== "attachments" ||
                this.activeRequestContext?.id !== requestId
              ) {
                return;
              }
              this.activeRequestContext = {
                ...this.activeRequestContext,
                meta,
                canEditRequest:
                  this.isStaffUser || !meta?.restrict_permissions
              };
            });
          }
          break;
        }
        case "deleteRequest":
          {
            const meta = await this.fetchRequestMeta(requestId);
            if (meta?.restrict_permissions) {
              showNotification(
                "You lack permission to delete requests.",
                "warning"
              );
              break;
            }
          }
          this.openRequestActionModal("deleteRequest", {
            id: requestId,
            name: requestName
          });
          break;
        case "downloadRequestForm":
          await this.handleDownloadRequestForm(requestId);
          break;
        case "uploadSignedRequest":
          await this.handleUploadSignedRequest(requestId, requestName);
          break;
        case "viewFilePaths":
          if (!this.isStaffUser) {
            showNotification("You lack permission to view file paths.", "warning");
            break;
          }
          this.openRequestActionModal("filePaths", {
            id: requestId,
            name: requestName
          });
          break;
        case "composeEmail":
          if (!this.isStaffUser) {
            showNotification("You lack permission to compose email.", "warning");
            break;
          }
          this.openRequestActionModal("composeEmail", {
            id: requestId,
            name: requestName
          });
          break;
        case "solicitApproval":
        case "requestApproval":
          if (!this.paperlessApproval) {
            showNotification("Email approval is not enabled.", "warning");
            break;
          }
          this.openRequestActionModal("solicitApproval", {
            id: requestId,
            name: requestName
          });
          break;
        case "downloadROCrate": {
          if (!selectedRows.length) {
            showNotification(
              "Select records to download RO-Crate.",
              "warning"
            );
            if (!group._group.visible) groupElement.click();
            break;
          }
          const barcodes = Array.from(
            new Set(
              selectedRows
                .map((row) => row.getData().barcode)
                .map((barcode) => ((barcode ?? "") + "").trim())
                .filter((barcode) => Boolean(barcode))
            )
          );
          if (!barcodes.length) {
            showNotification(
              "Selected entries lack valid barcodes.",
              "error"
            );
            if (!group._group.visible) groupElement.click();
            break;
          }
          await this.getROCrateData({
            barcodes,
            requestName
          });
          if (!group._group.visible) groupElement.click();
          break;
        }
      }
    },
    async fetchExportTemplates() {
      if (!this.isStaffUser) {
        return;
      }
      try {
        const response = await axiosRef.get(
          `${urlStringStart}/api/libraries-and-samples-templates/`
        );
        this.fetchedLibrariesAndSamplesTemplates = response.data;
      } catch (error) {
        handleError(error);
      }
    },
    async uploadExportTemplate(event) {
      if (!this.isStaffUser) {
        return;
      }
      const file = event.target.files[0];
      if (
        file &&
        file.type ===
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
      ) {
        const formData = new FormData();
        formData.append("file", file);
        try {
          await axiosRef.post(
            `${urlStringStart}/api/libraries-and-samples-templates/upload/`,
            formData,
            {
              headers: {
                "Content-Type": "multipart/form-data"
              }
            }
          );
          showNotification("File uploaded successfully.", "success");
          this.fetchExportTemplates();
        } catch (error) {
          showNotification("File upload failed.", "error");
        } finally {
          this.selectedFile = "without-file";
        }
      } else {
        showNotification("Upload a valid XLSX file.", "error");
      }
    },
    async downloadExportTemplate(file) {
      if (!this.isStaffUser) {
        return;
      }
      try {
        const response = await axiosRef.get(
          `${urlStringStart}/api/libraries-and-samples-templates/${file.id}/download/`,
          {
            responseType: "blob"
          }
        );
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement("a");
        link.href = url;
        link.setAttribute("download", file.name || "LibrariesAndSamples.xlsx");
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
      } catch (error) {
        showNotification("File download failed.", "error");
      }
    },
    async removeExportTemplate(index) {
      if (!this.isStaffUser) {
        return;
      }
      const file = this.fetchedLibrariesAndSamplesTemplates[index];
      try {
        await axiosRef.delete(
          `${urlStringStart}/api/libraries-and-samples-templates/${file.id}/remove/`
        );
        this.fetchedLibrariesAndSamplesTemplates.splice(index, 1);
        showNotification("File removed successfully.", "success");
      } catch (error) {
        showNotification("File removal failed.", "error");
      } finally {
        this.selectedFile = "without-file";
      }
    },
    handleExportClick() {
      this.hasSelectedRows = this.librariesSamplesList.some(
        (row) => row.selected
      );
      this.exportSelection = this.hasSelectedRows ? "selected" : "all";
      this.showExportPopup = true;
    },
    async handleExport() {
      try {
        this.fakeLoadingStart();
        const today = new Date();
        const formattedDate = `${today.getFullYear()}${String(
          today.getMonth() + 1
        ).padStart(2, "0")}${String(today.getDate()).padStart(2, "0")}`;

        let exportRows = [];
        if (this.exportSelection === "selected") {
          exportRows = this.librariesSamplesList.filter((row) => row.selected);
        } else {
          this.exportLoading = true;
          exportRows = await this.getLibrariesSamples(1, true);
        }

        const sortedExportRows = [...exportRows].sort((a, b) => {
          const getRequestNum = (str) => {
            const match = String(str).match(/^(\d+)_/);
            return match ? parseInt(match[1], 10) : 0;
          };
          const aNum = getRequestNum(a.request_name);
          const bNum = getRequestNum(b.request_name);
          if (aNum !== bNum) return aNum - bNum;
          return a.barcode?.localeCompare(b.barcode);
        });

        const uniqueRequestIDs = [
          ...new Set(
            sortedExportRows.map((row) => {
              const match = row.request_name.match(/^(\d+)_/);
              return match ? match[1] : row.request_name;
            })
          )
        ]
          .sort()
          .join("_");

        let filename = "";
        if (this.exportSelection === "selected") {
          filename = `${formattedDate}_${uniqueRequestIDs}_libraries_and_samples`;
        } else {
          filename = `${formattedDate}_libraries_and_samples`;
        }

        const exportColumns = librariesAndSamplesExportColumns();

        const templateDownloadUrl =
          this.selectedFile !== "without-file"
            ? `${urlStringStart}/api/libraries-and-samples-templates/${this.selectedFile.id}/download/`
            : null;

        const blob = await createExcelExportBlob({
          rows: sortedExportRows,
          exportColumns,
          axiosInstance: axiosRef,
          templateDownloadUrl
        });
        saveAs(blob, filename);
      } catch (error) {
        showNotification("Export failed. Please try again.", "error");
      } finally {
        if (this.exportLoading) {
          this.exportLoading = false;
          showNotification("Export completed successfully.", "success");
        }
        this.fakeLoadingStop();
        if (!this.exportSelection === "selected")
          setTimeout(() => {
            this.loading = false;
          }, 2000);
        this.showExportPopup = false;
        this.selectedFile = "without-file";
      }
    },
    handleDragOver(e) {
      e.preventDefault();
      if (!this.isStaffUser) {
        this.isDragOver = false;
        return;
      }
      this.isDragOver = true;
    },
    handleDragEnter(e) {
      e.preventDefault();
      if (!this.isStaffUser) {
        this.isDragOver = false;
        return;
      }
      this.isDragOver = true;
    },
    handleDragLeave(e) {
      if (!this.isStaffUser) {
        this.isDragOver = false;
        return;
      }
      if (!e.currentTarget.contains(e.relatedTarget)) {
        this.isDragOver = false;
      }
    },
    handleDrop(e) {
      e.preventDefault();
      if (!this.isStaffUser) {
        this.isDragOver = false;
        return;
      }
      this.isDragOver = false;

      const files = e.dataTransfer.files;
      if (files.length > 1) {
        showNotification(
          "Upload only one XLSX file.",
          "error"
        );
      } else this.processUploadedFile(files[0]);
    },
    processUploadedFile(file) {
      if (!this.isStaffUser) {
        return;
      }
      if (
        file &&
        file.type ===
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
      ) {
        const event = {
          target: {
            files: [file]
          }
        };
        this.uploadExportTemplate(event);
      } else {
        showNotification("Upload a valid XLSX file.", "error");
      }
    },
    changePage(page) {
      if (
        page >= 1 &&
        page <= this.pagination.totalPages &&
        page !== this.pagination.currentPage
      ) {
        this.getLibrariesSamples(page);
      }
    },
    goToPage() {
      const page = Math.max(
        1,
        Math.min(this.pageInput, this.pagination.totalPages)
      );
      if (page !== this.pagination.currentPage) {
        this.changePage(page);
      } else {
        this.pageInput = this.pagination.currentPage;
      }
    },
    validatePageInput() {
      if (this.pageInput < 1) this.pageInput = 1;
      if (this.pageInput > this.pagination.totalPages)
        this.pageInput = this.pagination.totalPages;
    },
    handlePageSizeChange() {
      this.getLibrariesSamples(1);
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

.search-bar {
  width: 330px;
}

body.input-dropdown-open .tabulator-tooltip {
  display: none !important;
}

.export-long-loading {
  margin-top: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
  font-size: 16px;
  color: #333;
  background-color: white;
  padding: 20px;
  border: 1px solid #333;
  border-radius: 8px;
}


@media (max-width: 1550px) {
  .header-title {
    min-width: 80px;
  }

  .search-bar {
    width: 250px;
  }

  .search-bar input {
    padding: 8px;
  }

  .header-button {
    padding: 8px 12px;
  }
}

@media (max-width: 1470px) {
  .date-filter {
    padding: 2px;
  }

  .date-filters label {
    display: none;
  }

  .header-button span {
    display: none;
  }
}

@media (max-width: 950px) {
  .header-title {
    font-size: 16px;
  }

  .search-bar {
    width: 100px;
  }

  .search-bar input {
    width: 10px;
    padding-right: 25px;
  }

  .date-filters {
    display: none;
  }
}

@media (max-width: 600px) {
  .header-logo {
    display: none !important;
  }

  .search-bar {
    display: none;
  }

  .date-filters {
    display: none;
  }

  .header-button {
    display: none;
  }
}
</style>

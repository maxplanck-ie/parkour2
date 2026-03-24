<template>
  <div class="parent-container">
    <!-- Loading overlay -->
    <div v-if="loading || fakeLoading" class="loading-overlay">
      <div v-if="!fakeLoading" class="spinner"></div>
      <p v-if="!fakeLoading">
        Loading <span style="font-weight: bold">Library Preparation</span>...
      </p>
    </div>

    <!-- Header -->
    <div class="header">
      <div class="header-logo" style="display: inline; margin-right: 10px">
        <img
          :src="iconLibraryPrepHeader"
          alt="Library Preparation"
          width="42"
          height="42"
          style="display: block"
        />
      </div>
      <div class="header-title" style="display: inline">
        Library Preparation
      </div>

      <!-- Sticky right section for search, and select columns -->
      <div class="sticky-actions">
        <div class="search-bar">
          <input
            ref="searchInput"
            v-model="searchQuery"
            type="text"
            placeholder="Search"
          />
          <font-awesome-icon
            icon="fa-solid fa-magnifying-glass"
            style="color: darkgrey"
          />
        </div>
        <div class="button-popup-wrapper">
          <button
            class="header-button"
            id="toggleSelectColumnsButton"
            @click="toggleSelectColumns"
          >
            <font-awesome-icon
              icon="fa-solid fa-columns"
              style="color: white"
            />
            <span> Select Columns </span>
          </button>
          <div
            id="selectColumnsPopup"
            v-if="showSelectColumns"
            class="button-popup-container"
            style="
              left: -50px;
              width: 250px;
              max-height: 473px;
              display: flex;
              flex-direction: column;
              padding: 10px 10px 5px 10px;
            "
          >
            <ul
              style="
                padding: 5px 7px 7px;
                margin: 0;
                flex-grow: 1;
                overflow-y: auto;
              "
            >
              <li
                v-for="(column, index) in columnsList"
                :key="index"
                style="list-style: none"
              >
                <template
                  v-if="
                    column.field !== 'selected' ||
                    (column.field === 'selected' && column.visible == false)
                  "
                >
                  <label
                    :style="{
                      backgroundColor: column.columns ? '#33333310' : 'white',
                      cursor: column.columns ? 'default' : 'pointer'
                    }"
                  >
                    <input
                      v-if="!column.columns"
                      type="checkbox"
                      v-model="column.visible"
                      @change="toggleColumnVisibility(column)"
                    />
                    <font-awesome-icon
                      v-if="column.columns"
                      icon="fa-solid fa-caret-down"
                      style="
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
                      "
                    />
                    <span>{{ column.title }}</span>
                  </label>
                </template>
              </li>
            </ul>
            <div
              style="
                padding-top: 8px;
                border-top: 1px solid #eee;
                display: flex;
                flex-direction: column;
              "
            >
              <button @click="resetColumnVisibility" class="reset-button">
                Reset Visibility Settings
              </button>
              <button
                style="margin-bottom: 5px"
                @click="resetColumnWidths"
                class="reset-button"
              >
                Reset Width Settings
              </button>
            </div>
          </div>
        </div>
        <div class="button-popup-wrapper">
          <button class="header-button" @click="toggleGroups">
            <font-awesome-icon
              icon="fa-solid fa-layer-group"
              style="color: white"
            />
            <span> Toggle Views </span>
          </button>
        </div>
        <button
          class="header-button"
          id="openExportPopupButton"
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
        :rowData="librariesSamplesList"
        :columnDefs="columnsList"
        groupBy="library_protocol_name"
        :groupSort="{ field: 'library_protocol_name', order: 'asc' }"
        :groupStartOpen="false"
        :tableOptions="{
          ...tableOptions,
          onBatchCellValueChanged,
          fakeLoadingStart,
          fakeLoadingStop,
          handleColumnResized,
          handleColumnVisibilityChanged
        }"
      />
    </div>

    <!-- Popup window -->
    <div v-if="showPopupWindow" class="popup-overlay">
      <div
        class="popup-container confirmation-popup"
        :style="{
          height: popupContents.popupHeight + 'px',
          width: popupContents.popupWidth + 'px'
        }"
      >
        <div class="popup-header">
          <img
            :src="iconConfirmationAlert"
            alt="Confirmation"
            width="42"
            height="42"
            style="display: block"
          />
          <span class="popup-title">{{ popupContents.popupTitle }}</span>
          <button class="popup-close-button" @click="showPopupWindow = false">
            &times;
          </button>
        </div>
        <div class="popup-body">
          <div v-html="popupContents.popupDescription"></div>
          <div
            v-if="popupContents.popupList && popupContents.popupList.length > 0"
            class="popup-scrollable-content"
          >
            <div class="popup-scrollable-content-inner">
              <ol style="padding-left: 25px">
                <li v-for="item in popupContents.popupList" :key="item">
                  <span style="font-weight: bold">{{ item.barcode }}</span>
                  <span>{{ " - " + item.name }}</span>
                </li>
              </ol>
            </div>
          </div>
        </div>
        <div class="popup-footer">
          <button class="popup-button yes-button" @click="popupContents.onYes">
            Yes
          </button>
          <button class="popup-button" @click="popupContents.onNo">No</button>
        </div>
      </div>
    </div>

    <!-- Popup for Export Options -->
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
            Drop <span style="font-weight: bold">XLSX file</span> here to upload
            as <span style="font-weight: bold">template</span>
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
                  Use export when you want to download the selected Library
                  Preparation rows to Excel. This export works on the rows you
                  selected before opening the popup.
                </p>
                <section class="tooltip-section">
                  <div class="tooltip-section-title">What this export does</div>
                  <ul class="tooltip-list">
                    <li>This screen exports the selected preparation rows only.</li>
                    <li>All selected rows must belong to a single Library Preparation Protocol before export can continue.</li>
                    <li>If you need a different result, change the row selection in the table first and then reopen export.</li>
                  </ul>
                </section>
                <section class="tooltip-section">
                  <div class="tooltip-section-title">How template files work</div>
                  <ol class="tooltip-list tooltip-steps">
                    <li>Start by exporting with <strong>Export without any additional sheets</strong>. This creates the base Excel file and keeps the original <strong>Parkour</strong> sheet.</li>
                    <li>Open that file in Excel and add your own extra sheets for notes, calculations, or reporting.</li>
                    <li>Upload the edited file here as a reusable template. It will appear in the list of available templates.</li>
                    <li>Later, when you export using that template, Parkour replaces only the <strong>Parkour</strong> sheet with fresh data and keeps your extra sheets unchanged.</li>
                  </ol>
                </section>
                <section class="tooltip-section">
                  <div class="tooltip-section-title">When to use this</div>
                  <ul class="tooltip-list">
                    <li>Share a preparation-specific Excel file with colleagues.</li>
                    <li>Keep a reusable reporting workbook for one protocol workflow.</li>
                    <li>Reuse the same export format whenever you need updated preparation data.</li>
                  </ul>
                </section>
              </div>
            </div>
          </span>
          <button class="popup-close-button" @click="showExportPopup = false">
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
                      type="radio"
                      title="Select"
                      id="without-file"
                      value="without-file"
                      v-model="selectedFile"
                    />
                  </div>
                </div>
              </div>
              <div
                v-for="(file, index) in fetchedLibraryPreparationTemplates"
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
                    @click="downloadExportTemplate(file)"
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
                    @click="removeExportTemplate(index)"
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
                      :id="'file-radio-' + index"
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
              for="file-upload"
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
              id="file-upload"
              type="file"
              accept=".xlsx"
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

<script lang="jsx">
import TabulatorTable from "../components/TabulatorTableFull.vue";
import { saveAs } from "file-saver";
import {
  showNotification,
  handleError,
  createAxiosObject,
  urlStringStartsWith,
  createExcelExportBlob
} from "../utilities/utilityFunctions";
import {
  libraryPreparationColumnDefs,
  libraryPreparationExportColumns,
  libraryPreparationGroupHeader
} from "../constants/libraryPreparationConsts";
import iconLibraryPrepHeader from "../assets/icons/header_library_prep.svg";
import iconConfirmationAlert from "../assets/icons/alert_confirmation.svg";
import iconExportTemplateFile from "../assets/icons/export_template.svg";
import iconExportTemplateFileLines from "../assets/icons/export_template_lines.svg";
import iconExportDownload from "../assets/icons/export_download.svg";
import iconExportRemove from "../assets/icons/export_remove.svg";
import iconExportUpload from "../assets/icons/export_upload.svg";
const axiosRef = createAxiosObject();
const urlStringStart = urlStringStartsWith();

export default {
  name: "LibraryPreparation",
  components: {
    TabulatorTable
  },
  data() {
    return {
      iconLibraryPrepHeader,
      iconConfirmationAlert,
      iconExportTemplateFile,
      iconExportTemplateFileLines,
      iconExportDownload,
      iconExportRemove,
      iconExportUpload,
      tabulatorInstance: null,
      loading: true,
      fakeLoading: false,
      isDragOver: false,
      librariesSamplesList: [],
      columnsList: [],
      showPopupWindow: false,
      showExportPopup: false,
      showExportHelpTooltip: false,
      fetchedLibraryPreparationTemplates: [],
      selectedFile: "without-file",
      pendingEditChanges: {},
      pendingEditTimer: null,
      isSavingEdits: false,
      popupContents: {
        popupTitle: "Are you sure?",
        popupDescription: "",
        popupList: [],
        onYes: null,
        onNo: null,
        popupHeight: 220,
        popupWidth: 600
      },
      tableOptions: {
        index: "barcode",
        placeholder: "No Libraries and Samples to show.",
        initialSort: [
          { column: "library_protocol_name", dir: "asc" },
          { column: "barcode", dir: "asc" },
          {
            column: "request_name",
            dir: "asc",
            sorter: (a, b) => {
              const getNum = (str) => {
                const match = String(str).match(/^(\d+)_/);
                return match ? parseInt(match[1], 10) : 0;
              };
              return getNum(a) - getNum(b);
            }
          }
        ],
        groupHeader: (value, count, data) => {
          return libraryPreparationGroupHeader(value, count);
        },
        getClearValueForField: (field) => {
          if (field === "smear_analysis") return 100;
          return "";
        },
        blockActionsOnDisabledCells: true
      },
      searchQuery: "",
      showSelectColumns: false
    };
  },
  mounted() {
    this.getLibrariesSamples();
    this.setColumns();
    this.fetchExportTemplates();

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
    if (this.pendingEditTimer) {
      clearTimeout(this.pendingEditTimer);
    }
  },
  watch: {
    searchQuery(newValue, oldValue) {
      if (newValue !== oldValue) {
        this.tabulatorInstance.filterTableData(
          "search_library_preparation",
          newValue === null ? "" : newValue
        );
      }
    },
    showPopupWindow(newVal) {
      if (newVal) {
        this.$nextTick(() => {
          const yesButton = document.querySelector(".popup-button.yes-button");
          yesButton.focus();
        });
      } else {
        document.getElementsByClassName("tabulator-cell")[1]?.click();
      }
    }
  },
  methods: {
    async getLibrariesSamples() {
      this.loading = true;
      try {
        let response = await axiosRef.get(
          urlStringStart + "/api/library_preparation/"
        );
        let fetchedRows = response.data.map((element) => ({
          pk: element.pk || "",
          name: element.name || "",
          type: element.barcode[2] || "",
          barcode: element.barcode || "",
          is_converted:
            element.is_converted === null ? "" : element.is_converted,
          request_name: element.request_name || "",
          pool_name: element.pool_name || "",
          library_protocol:
            element.library_protocol === 0 ? 0 : element.library_protocol || "",
          library_protocol_name: element.library_protocol_name || "",
          concentration_sample:
            element.concentration_sample === 0
              ? 0
              : element.concentration_sample || "",
          concentration_library:
            element.concentration_library === 0
              ? 0
              : element.concentration_library || "",
          starting_amount:
            element.starting_amount === 0 ? 0 : element.starting_amount || "",
          pcr_cycles: element.pcr_cycles === 0 ? 0 : element.pcr_cycles || "",
          mean_fragment_size:
            element.mean_fragment_size === 0
              ? 0
              : element.mean_fragment_size || "",
          smear_analysis:
            element.smear_analysis === 0 ? 0 : element.smear_analysis || "",
          comments: element.comments || "",
          comments_facility: element.comments_facility || "",
          comments_library_sample: element.comments_library_sample || "",
          coordinate: element.coordinate || "",
          index_type: element.index_type || "",
          index_i7_id: element.index_i7_id || "",
          index_i5_id: element.index_i5_id || "",
          create_time: element.create_time
            ? (() => {
                const date = new Date(element.create_time);
                if (isNaN(date)) return "";
                const day = String(date.getDate()).padStart(2, "0");
                const month = String(date.getMonth() + 1).padStart(2, "0");
                const year = date.getFullYear();
                return `${day}.${month}.${year}`;
              })()
            : "",
          measuring_unit_facility: element.measuring_unit_facility || "",
          measured_value_facility:
            element.measured_value_facility === 0
              ? 0
              : element.measured_value_facility || "",
          size_distribution_facility:
            element.size_distribution_facility === 0
              ? 0
              : element.size_distribution_facility || ""
        }));
        this.librariesSamplesList = fetchedRows;
      } catch (error) {
        handleError(error);
      } finally {
        this.loading = false;
      }
    },
    setColumns() {
      const storedVisibility = JSON.parse(
        localStorage.getItem("libraryPreparationColumnVisibility") || "{}"
      );
      const storedWidths = JSON.parse(
        localStorage.getItem("libraryPreparationColumnWidths") || "{}"
      );

      const applySettings = (columns) => {
        return columns.map((column) => {
          if (column.field) {
            if (storedWidths[column.field]) {
              column.width = storedWidths[column.field];
              if (column.minWidth && column.width < column.minWidth) {
                column.width = column.minWidth;
              }
            }
            column.visible =
              storedVisibility[column.field] ?? column.visible ?? true;
          }
          if (column.columns) {
            column.columns = applySettings(column.columns);
          }
          return column;
        });
      };

      let columnDefs = libraryPreparationColumnDefs(
        () => this.tabulatorInstance
      );

      this.columnsList = applySettings(columnDefs);
    },
    handleOutsideClick(event) {
      const selectColumnsPopup = this.$el.querySelector("#selectColumnsPopup");
      const selectColumnsButton = this.$el.querySelector(
        "#toggleSelectColumnsButton"
      );
      const exportPopup = this.$el.querySelector(".export-popup");
      const exportButton = this.$el.querySelector("#openExportPopupButton");
      const confirmationPopup = this.$el.querySelector(".confirmation-popup");
      const clickOnExportButton =
        exportButton &&
        (exportButton === event.target || exportButton.contains(event.target));

      if (
        this.showSelectColumns &&
        selectColumnsPopup &&
        !selectColumnsPopup.contains(event.target) &&
        selectColumnsButton !== event.target &&
        !selectColumnsButton.contains(event.target)
      ) {
        this.showSelectColumns = false;
      }

      if (
        this.showExportPopup &&
        exportPopup &&
        !exportPopup.contains(event.target) &&
        !clickOnExportButton
      ) {
        this.showExportPopup = false;
      }

      if (
        this.showPopupWindow &&
        confirmationPopup &&
        !confirmationPopup.contains(event.target)
      ) {
        this.showPopupWindow = false;
      }
    },
    handleKeyDown(event) {
      const isEscape = event.key === "Escape";
      if (isEscape && (this.showPopupWindow || this.showExportPopup)) {
        this.showPopupWindow = false;
        this.showExportPopup = false;
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
    toggleGroups(goToInitial) {
      this.fakeLoadingStart();
      this.tabulatorInstance.toggleGroups(goToInitial);
      this.fakeLoadingStop();
    },
    toggleSelectColumns() {
      this.showSelectColumns = !this.showSelectColumns;
    },
    handleColumnResized(column) {
      const field = column.getField();
      const width = column.getWidth();
      const storedWidths = JSON.parse(
        localStorage.getItem("libraryPreparationColumnWidths") || "{}"
      );
      const newWidths = {
        ...storedWidths,
        [field]: width
      };
      localStorage.setItem(
        "libraryPreparationColumnWidths",
        JSON.stringify(newWidths)
      );
      this.fakeLoadingStart();
      setTimeout(() => this.fakeLoadingStop(), 50);
    },
    handleColumnVisibilityChanged(field, visible) {
      const storedVisibility = JSON.parse(
        localStorage.getItem("libraryPreparationColumnVisibility") || "{}"
      );

      const newVisibility = {
        ...storedVisibility,
        [field]: visible
      };

      localStorage.setItem(
        "libraryPreparationColumnVisibility",
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
      localStorage.removeItem("libraryPreparationColumnWidths");
      this.setColumns();
      this.fakeLoadingStart();
      setTimeout(() => this.fakeLoadingStop(), 300);
    },
    resetColumnVisibility() {
      localStorage.removeItem("libraryPreparationColumnVisibility");
      this.setColumns();
      this.fakeLoadingStart();
      setTimeout(() => this.fakeLoadingStop(), 300);
    },
    handleGroupButtonClick(event, groupValue, action) {
      event.stopPropagation();

      const group = this.tabulatorInstance
        .getTable()
        .getGroups()
        .find((g) => g.getKey() === groupValue);
      const groupRows = group.getRows();
      const groupElement = group.getElement();
      const selectedRows = groupRows.filter((row) => row.getData().selected);
      const type = selectedRows[0] && selectedRows[0].getData().type;
      const requestName = group._group.key;
      const selectedNamesList = selectedRows.map((item) => {
        return { barcode: item.getData().barcode, name: item.getData().name };
      });
      const popupHeight = Math.min(420, 260 + selectedNamesList.length * 22);

      switch (action) {
        case "selectAll":
          groupRows.forEach((row) => {
            row.getData().selected = true;
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
            row.getData().selected = false;
            row.update({});
            const rowElement = row.getElement();
            const checkbox = rowElement.querySelector('input[type="checkbox"]');
            if (checkbox) {
              checkbox.checked = false;
            }
          });
          if (!group._group.visible) groupElement.click();
          break;

        case "qualityPassed":
          if (selectedRows.length === 0) {
            showNotification(
              "Please select libraries/samples in the request first.",
              "warning"
            );
            break;
          }
          let popupTitleQP = `Are you sure?`;
          let popupDescriptionQP = `Marking the following ${
            type === "L" ? "libraries" : "samples"
          } from the request <span style="font-weight: bold">'${requestName}'</span> as <span style="font-weight: bold">Quality Check: Passed</span>. Confirm your action by pressing the <span style="font-weight: bold">Yes</span> button.`;
          let popupListQP = [...selectedNamesList];
          let onYesQP = () => {
            this.qualityCheckChange(selectedRows, "passed");
            this.showPopupWindow = false;
          };
          let onNoQP = () => {
            this.showPopupWindow = false;
          };
          this.createPopupWindow(
            popupTitleQP,
            popupDescriptionQP,
            popupListQP,
            onYesQP,
            onNoQP,
            popupHeight,
            700
          );
          break;

        case "qualityFailed":
          if (selectedRows.length === 0) {
            showNotification(
              "Please select libraries/samples in the request first.",
              "warning"
            );
            break;
          }
          let popupTitleQF = `Are you sure?`;
          let popupDescriptionQF = `Marking the following ${
            type === "L" ? "libraries" : "samples"
          } from the request <span style="font-weight: bold">'${requestName}'</span> as <span style="font-weight: bold">Quality Check: Failed</span>. Confirm your action by pressing the <span style="font-weight: bold">Yes</span> button.`;
          let popupListQF = [...selectedNamesList];
          let onYesQF = () => {
            this.qualityCheckChange(selectedRows, "failed");
            this.showPopupWindow = false;
          };
          let onNoQF = () => {
            this.showPopupWindow = false;
          };
          this.createPopupWindow(
            popupTitleQF,
            popupDescriptionQF,
            popupListQF,
            onYesQF,
            onNoQF,
            popupHeight,
            700
          );
          break;
      }
    },
    onBatchCellValueChanged(batchChanges) {
      this.queueBatchChanges(batchChanges);
      this.scheduleBatchSave();
    },
    queueBatchChanges(batchChanges) {
      batchChanges.forEach((change) => {
        const key = `${change.record_type}:${change.pk}`;
        if (!this.pendingEditChanges[key]) {
          this.pendingEditChanges[key] = {
            pk: change.pk,
            record_type: change.record_type
          };
        }
        Object.keys(change).forEach((field) => {
          if (field !== "pk" && field !== "record_type") {
            this.pendingEditChanges[key][field] = change[field];
          }
        });
      });
    },
    scheduleBatchSave() {
      if (this.pendingEditTimer) {
        clearTimeout(this.pendingEditTimer);
      }
      this.pendingEditTimer = setTimeout(() => {
        this.flushPendingEdits();
      }, 300);
    },
    async flushPendingEdits() {
      if (this.isSavingEdits) {
        return;
      }
      const pending = Object.values(this.pendingEditChanges);
      if (pending.length === 0) return;

      this.pendingEditChanges = {};
      this.isSavingEdits = true;
      try {
        const payload = {
          data: JSON.stringify(pending)
        };
        await axiosRef.post(
          `${urlStringStart}/api/library_preparation/edit/`,
          payload
        );
      } catch (error) {
        this.queueBatchChanges(pending);
        handleError(error);
      } finally {
        this.isSavingEdits = false;
        if (Object.keys(this.pendingEditChanges).length > 0) {
          this.flushPendingEdits();
        }
      }
    },
    async qualityCheckChange(groupRows, qualityCheck) {
      this.fakeLoadingStart();
      const payload = {
        data: JSON.stringify(
          groupRows.map((row) => ({
            pk: row.getData().pk,
            record_type: row.getData().record_type,
            quality_check: qualityCheck
          }))
        )
      };
      try {
        await axiosRef.post(
          `${urlStringStart}/api/library_preparation/edit/`,
          payload
        );
        showNotification(
          "Quality check status updated successfully.",
          "success"
        );
        await this.getLibrariesSamples();
      } catch (error) {
        handleError(error);
      } finally {
        this.fakeLoadingStop();
      }
    },
    async fetchExportTemplates() {
      try {
        const response = await axiosRef.get(
          `${urlStringStart}/api/library-preparation-templates/`
        );
        this.fetchedLibraryPreparationTemplates = response.data;
      } catch (error) {
        handleError(error);
      }
    },
    async uploadExportTemplate(event) {
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
            `${urlStringStart}/api/library-preparation-templates/upload/`,
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
          showNotification("Error uploading file: " + error, "error");
        } finally {
          this.selectedFile = "without-file";
        }
      } else {
        showNotification("Please upload a valid XLSX file.", "error");
      }
    },
    async downloadExportTemplate(file) {
      try {
        const response = await axiosRef.get(
          `${urlStringStart}/api/library-preparation-templates/${file.id}/download/`,
          {
            responseType: "blob"
          }
        );
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement("a");
        link.href = url;
        link.setAttribute("download", file.name || "Library_Preparation.xlsx");
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
      } catch (error) {
        showNotification("Error downloading file: " + error, "error");
      }
    },
    async removeExportTemplate(index) {
      const file = this.fetchedLibraryPreparationTemplates[index];
      try {
        await axiosRef.delete(
          `${urlStringStart}/api/library-preparation-templates/${file.id}/remove/`
        );
        this.fetchedLibraryPreparationTemplates.splice(index, 1);
        showNotification("File removed successfully.", "success");
      } catch (error) {
        showNotification("Error removing file: " + error, "error");
      } finally {
        this.selectedFile = "without-file";
      }
    },
    handleExportClick() {
      const selected = this.librariesSamplesList.filter((row) => row.selected);
      if (selected.length === 0) {
        showNotification(
          "Please select at least one library or sample to export.",
          "warning"
        );
        return;
      }
      const protoSet = new Set(
        selected.map((r) => r.library_protocol_name || r.library_protocol)
      );
      if (protoSet.size > 1) {
        showNotification(
          "Please select rows from a single Library Preparation Protocol.",
          "warning"
        );
        return;
      }
      this.showExportPopup = true;
    },
    async handleExport() {
      try {
        this.fakeLoadingStart();
        const today = new Date();
        const formattedDate = `${today.getFullYear()}${String(
          today.getMonth() + 1
        ).padStart(2, "0")}${String(today.getDate()).padStart(2, "0")}`;

        let exportRows = this.librariesSamplesList.filter(
          (row) => row.selected
        );

        const sortedExportRows = [...exportRows].sort((a, b) => {
          const getRequestNum = (str) => {
            const match = String(str).match(/^(\d+)_/);
            return match ? parseInt(match[1], 10) : 0;
          };
          const protocolCompare = b.library_protocol_name?.localeCompare(
            a.library_protocol_name
          );
          if (protocolCompare !== 0) return protocolCompare;
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

        filename = `${formattedDate}_${uniqueRequestIDs}_preparation`;

        const exportColumns = libraryPreparationExportColumns();

        const templateDownloadUrl =
          this.selectedFile !== "without-file"
            ? `${urlStringStart}/api/library-preparation-templates/${this.selectedFile.id}/download/`
            : null;

        const blob = await createExcelExportBlob({
          rows: sortedExportRows,
          exportColumns,
          axiosInstance: axiosRef,
          templateDownloadUrl
        });
        saveAs(blob, filename);
      } finally {
        this.fakeLoadingStop();
        this.showExportPopup = false;
        this.selectedFile = "without-file";
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
          "Please upload only one XLSX file at a time.",
          "error"
        );
      } else this.processUploadedFile(files[0]);
    },
    processUploadedFile(file) {
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
        showNotification("Please upload a valid XLSX file.", "error");
      }
    },
    createPopupWindow(
      popupTitle,
      popupDescription,
      popupList,
      onYes,
      onNo,
      popupHeight,
      popupWidth
    ) {
      this.popupContents.popupTitle = popupTitle;
      this.popupContents.popupDescription = popupDescription;
      this.popupContents.popupList = popupList;
      this.popupContents.onYes = onYes;
      this.popupContents.onNo = onNo;
      if (popupWidth && popupHeight) {
        this.popupContents.popupHeight = popupHeight;
        this.popupContents.popupWidth = popupWidth;
      }
      this.showPopupWindow = true;
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

@media (max-width: 1400px) {
  .header-title {
    min-width: 80px;
  }

  .search-bar {
    width: 280px;
  }

  .search-bar input {
    padding: 8px;
  }

  .header-button {
    padding: 8px 12px;
  }
}

@media (max-width: 1100px) {
  .search-bar {
    width: 250px;
  }

  .search-bar input {
    padding: 6px;
  }

  .header-button span {
    display: none;
  }
}

@media (max-width: 700px) {
  .header-title {
    font-size: 16px;
  }

  .search-bar {
    width: 130px;
  }

  .search-bar input {
    width: 85px;
  }
}

@media (max-width: 550px) {
  .header-logo {
    display: none !important;
  }

  .search-bar {
    display: none;
  }

  .header-button {
    display: none;
  }
}
</style>

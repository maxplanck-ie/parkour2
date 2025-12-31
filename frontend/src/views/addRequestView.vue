<template>
  <div v-if="show" class="add-request-overlay" @click.self="emitClose">
    <div class="add-request-modal">
      <div class="add-request-header">
        <span class="title-with-icon">
          <font-awesome-icon icon="fa-solid fa-file-lines" class="header-icon" />
          <span>New Request</span>
        </span>
        <div class="header-actions">
          <button class="help-button" type="button" @click="openHelpPage" title="Open MAX page on Intranet">
            ?
          </button>
          <button class="popup-close-button" type="button" @click="emitClose">
            &times;
          </button>
        </div>
      </div>

      <div class="add-request-body">
        <div class="request-panel-container" :class="{ collapsed: isFormPanelCollapsed }">
          <section class="request-form-panel" :class="{ collapsed: isFormPanelCollapsed }">
            <label class="field-block">
              <span>
                Cost Unit<span v-if="!isStaffUser" class="required">*</span>
              </span>
              <select v-model="newRequest.cost_unit" :class="[
                costUnitError ? 'input-error' : '',
                !newRequest.cost_unit ? 'placeholder' : ''
              ]">
                <option value="" disabled>Select Cost Unit</option>
                <option v-for="cu in costUnits" :key="cu.id" :value="cu.id">
                  {{ cu.name }}
                </option>
              </select>
              <div v-if="costUnitError" class="field-error">
                {{ costUnitError }}
              </div>
            </label>

            <label class="field-block">
              <span>
                Description<span class="required">*</span>
              </span>
              <textarea v-model="newRequest.description" class="description-textarea" rows="6"
                placeholder="Describe Request" :class="{ 'input-error': descriptionError }"></textarea>
              <div v-if="descriptionError" class="field-error">
                {{ descriptionError }}
              </div>
            </label>

            <div class="files-section">
              <div class="files-header">
                <div>
                  <span>Files</span>
                  <small>Upload signed request and related documents.</small>
                </div>
                <button class="header-button ghost" type="button" @click="triggerRequestFileUpload">
                  <font-awesome-icon icon="fa-solid fa-square-plus" style="color: white" />
                  <span>Add Files</span>
                </button>
                <input ref="requestFileInput" type="file" multiple @change="handleRequestFileUpload"
                  style="display: none" />
              </div>
              <table class="files-table">
                <thead>
                  <tr>
                    <th style="width: 46%">Name</th>
                    <th style="width: 27%">Size</th>
                    <th style="width: 27%"></th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-if="!uploadedRequestFiles.length">
                    <td colspan="3" class="empty-cell">No files uploaded yet.</td>
                  </tr>
                  <tr v-for="file in uploadedRequestFiles" :key="file.id">
                    <td class="file-name-cell">
                      <span class="file-name-text" :title="file.name">{{ file.name }}</span>
                    </td>
                    <td class="file-size-cell" :title="formatFileSize(file.size)">
                      {{ formatFileSize(file.size) }}
                    </td>
                    <td class="actions-cell">
                      <button type="button" class="icon-action"
                        :title="file.path ? `Download ${file.name}` : 'Download unavailable'" :disabled="!file.path"
                        @click="downloadUploadedFile(file)">
                        <font-awesome-icon icon="fa-solid fa-download" />
                      </button>
                      <button type="button" class="icon-action danger" :title="`Remove ${file.name}`"
                        @click="removeUploadedFile(file.id)">
                        <font-awesome-icon icon="fa-solid fa-xmark" />
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div class="signed-request-info">
              <div class="signed-request-header">
                <div class="signed-request-label">
                  Signed Deep Sequencing Request
                </div>
                <button class="info-pill" type="button"
                  title="1. Save the request.&#10;2. Download the Deep Sequencing Request blank.&#10;3. Print, check GMO declaration(s), and sign it.&#10;4. Scan the blank and upload it back.&#10;&#10;Note: if the blank is already uploaded, you cannot update it.">
                  <font-awesome-icon icon="fa-solid fa-circle-info" />
                </button>
              </div>
              <div class="signed-request-row">
                <span class="signed-request-status"
                  :class="uploadedRequestFiles.length ? 'status-success' : 'status-warning'">
                  <font-awesome-icon
                    :icon="uploadedRequestFiles.length ? 'fa-solid fa-circle-check' : 'fa-solid fa-circle-exclamation'" />
                  {{ uploadedRequestFiles.length ? "Uploaded" : "Not Uploaded" }}
                </span>
              </div>
            </div>
          </section>
          <button class="panel-toggle-button" type="button" @click="toggleFormPanel"
            :aria-label="isFormPanelCollapsed ? 'Expand details panel' : 'Collapse details panel'">
            <font-awesome-icon :icon="isFormPanelCollapsed ? 'fa-solid fa-angle-right' : 'fa-solid fa-angle-left'" />
          </button>
        </div>

        <section class="records-panel" :class="{ expanded: isFormPanelCollapsed }">
          <div class="records-toolbar">
            <div class="switch-wrapper">
              <div class="controls-group">
                <label
                  class="record-type-switch"
                  title="Switch between Library and Sample entry modes"
                >
                <input type="checkbox" :checked="addRequestMode === 'sample'"
                  @change="requestRecordTypeSwitch($event)" />
                  <span class="slider">
                    <span
                      class="option"
                      :class="{ active: addRequestMode === 'library' }"
                    >
                      Library
                    </span>
                    <span
                      class="option"
                      :class="{ active: addRequestMode === 'sample' }"
                    >
                      Sample
                    </span>
                  </span>
                </label>
                <button class="icon-button" type="button" title="Add a new row" @click="addDraftRow">
                  <font-awesome-icon icon="fa-solid fa-square-plus" />
                </button>
                <button class="icon-button" type="button" title="Delete selected rows"
                  :disabled="!selectedDraftRowIds.length" @click="deleteSelectedDraftRows">
                  <font-awesome-icon icon="fa-solid fa-trash" />
                </button>
              </div>
              <div v-if="addRequestMode === 'sample'" class="download-buttons">
                <a
                  class="download-button"
                  :href="gmoFormUrl"
                  target="_blank"
                  rel="noopener"
                  title="Download Formblatt S1 (GMO)."
                >
                  <font-awesome-icon icon="fa-solid fa-download" />
                  <span>Formblatt S1</span>
                </a>
                <a
                  class="download-button"
                  :href="relacsDownloadUrl"
                  target="_blank"
                  rel="noopener"
                  title="Download RELACS Pellets Abs form."
                >
                  <font-awesome-icon icon="fa-solid fa-download" />
                  <span>RELACS Pellets Abs</span>
                </a>
              </div>
            </div>
          </div>
          <div class="draft-table" ref="draftTableWrapper">
            <LiteTabulatorTable ref="addRequestDraftTableRef" tableId="addRequestDraftTable"
              :rowData="addRequestDraftRows" :columnDefs="addRequestColumns"
              :tableOptions="addRequestDraftTableOptions" />
          </div>
        </section>
      </div>

      <div class="add-request-footer">
        <div class="footer-summary">
          <span>{{ footerLabel }}</span>
        </div>
        <div class="footer-actions">
          <button class="popup-button secondary" type="button" @click="emitClose">
            Cancel
          </button>
          <button class="popup-button yes-button" type="button" :disabled="isRequestSaving" @click="saveNewRequest">
            <span v-if="isRequestSaving">Saving...</span>
            <span v-else>Save Request</span>
          </button>
        </div>
      </div>
    </div>

    <div v-if="showToggleConfirm" class="confirm-overlay" @keydown="handleConfirmKeydown" tabindex="0">
      <div class="confirm-modal">
        <div class="confirm-header">
          <span class="confirm-title">Switch record type?</span>
          <button class="popup-close-button" type="button" @click="cancelToggleSwitch">
            &times;
          </button>
        </div>
        <div class="confirm-body">
          Switching between Library and Sample will clear all rows you have added.
          Do you want to continue?
        </div>
        <div class="confirm-footer">
          <button class="popup-button" type="button" @click="cancelToggleSwitch">
            Cancel
          </button>
          <button class="popup-button yes-button" type="button" @click="confirmToggleSwitch">
            OK
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import LiteTabulatorTable from "../components/LiteTabulatorTable.vue";
import {
  showNotification,
  handleError,
  createAxiosObject,
  urlStringStartsWith
} from "../utilities/utilityFunctions";
import {
  getAddRequestLibraryColumns,
  getAddRequestSampleColumns,
  LIBRARY_REQUIRED_FIELDS,
  SAMPLE_REQUIRED_FIELDS
} from "../constants/addRequestConsts";

const axiosRef = createAxiosObject();
const urlStringStart = urlStringStartsWith();

export default {
  name: "AddRequestView",
  components: {
    LiteTabulatorTable
  },
  props: {
    show: {
      type: Boolean,
      default: false
    },
    isStaffUser: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      addRequestMode: "library",
      isFormPanelCollapsed: false,
      addRequestDraftRows: [],
      selectedDraftRowIds: [],
      draftValidationState: {},
      validDraftCount: 0,
      isRequestSaving: false,
      draftRowCounter: 0,
      libraryMeasuringUnits: [
        { value: "ng/µl", label: "ng/µl (Concentration)" },
        { value: "Unknown", label: "Unknown" }
      ],
      sampleMeasuringUnits: [
        { value: "ng/µl", label: "ng/µl (Concentration)" },
        { value: "M", label: "M (Cells)" },
        { value: "k", label: "k (Cells)" },
        { value: "Unknown", label: "Unknown" }
      ],
      biosafetyLevelsOptions: [
        { value: "bsl1", label: "BSL1" },
        { value: "bsl2", label: "BSL2" }
      ],
      gmoOptions: [
        { value: true, label: "Yes" },
        { value: false, label: "No" }
      ],
      gmoFormUrl: `${urlStringStart}/static/docs/S1.docx`,
      relacsDownloadUrl: `${urlStringStart}/api/requests/download_RELACS_Pellets_Abs_form`,
      indexI7OptionsByType: {},
      indexI5OptionsByType: {},
      indexOptionsLoading: {},
      showToggleConfirm: false,
      pendingToggleMode: null,
      newRequest: {
        cost_unit: "",
        description: ""
      },
      costUnits: [],
      costUnitError: "",
      descriptionError: "",
      uploadedRequestFiles: [],
      uploadedRequestFileIds: [],
      protocolsList: [],
      analysisTypesList: [],
      readLengthsList: [],
      nucleicAcidTypesList: [],
      organismsList: [],
      indexTypesList: []
    };
  },
  watch: {
    show(newVal) {
      if (newVal) {
        this.prepareAddRequestModal();
      } else {
        this.resetState();
      }
    },
    showToggleConfirm(newVal) {
      if (newVal) {
        this.$nextTick(() => {
          const overlay = this.$el?.querySelector?.(".confirm-overlay");
          overlay?.focus?.();
        });
      }
    },
    "newRequest.cost_unit"(newValue) {
      if (newValue) {
        this.costUnitError = "";
      }
    },
    "newRequest.description"(newValue) {
      if ((newValue || "").trim()) {
        this.descriptionError = "";
      }
    }
  },
  mounted() {
    if (this.show) {
      this.prepareAddRequestModal();
    }
  },
  computed: {
    addRequestModeLabel() {
      return this.addRequestMode === "library" ? "Library" : "Sample";
    },
    addRequestColumns() {
      const normalizeOptions = (list = []) =>
        list.map((item) => ({
          value: item.id ?? item.value ?? item.pk ?? item.name,
          label: item.name ?? item.label ?? item.text ?? item.value ?? ""
        }));

      const getInstance = () =>
        this.$refs.addRequestDraftTableRef?.tabulatorInstance || null;
      const onSelectionChange = (table) => this.syncSelectedDraftRows(table);

      const libraryEditors = {
        protocols: normalizeOptions(this.protocolsList),
        analysisTypes: normalizeOptions(this.analysisTypesList),
        measuringUnits: this.libraryMeasuringUnits,
        readLengths: normalizeOptions(this.readLengthsList),
        indexTypes: normalizeOptions(this.indexTypesList),
        organisms: normalizeOptions(this.organismsList),
        getIndexReadsOptions: (row) =>
          this.getLibraryIndexReadsOptions(row),
        getIndexI7Options: (row) => this.getLibraryIndexI7Options(row),
        getIndexI5Options: (row) => this.getLibraryIndexI5Options(row)
      };

      const sampleEditors = {
        protocols: normalizeOptions(this.protocolsList),
        analysisTypes: normalizeOptions(this.analysisTypesList),
        measuringUnits: this.sampleMeasuringUnits,
        readLengths: normalizeOptions(this.readLengthsList),
        organisms: normalizeOptions(this.organismsList),
        nucleicAcidTypes: normalizeOptions(this.nucleicAcidTypesList),
        biosafetyLevels: this.biosafetyLevelsOptions,
        gmoOptions: this.gmoOptions
      };

      if (this.addRequestMode === "library") {
        return getAddRequestLibraryColumns(
          getInstance,
          libraryEditors,
          onSelectionChange
        );
      }
      return getAddRequestSampleColumns(
        getInstance,
        sampleEditors,
        onSelectionChange
      );
    },
    addRequestDraftTableOptions() {
      const vm = this;
      const getPlaceholder = () =>
        "Use the + button to create libraries/samples.";

      const handleSelection = () => this.syncSelectedDraftRows();

      return {
        index: "tempId",
        placeholder: getPlaceholder(),
        selectable: true,
        layout: "fitColumns",
        persistenceMode: false,
        rowSelectionChanged: () => handleSelection(),
        dataChanged: () => {
          handleSelection();
          this.revalidateDraftRows();
        },
        cellEditing(cell) {
          return vm.handleCellEditing(cell);
        },
        cellEdited(cell) {
          vm.handleCellEdited(cell);
        },
        handleRenderComplete: () => this.applyValidationStyling()
      };
    },
    footerLabel() {
      const count = this.validDraftCount;
      const labels =
        this.addRequestMode === "library"
          ? { singular: "library", plural: "libraries" }
          : { singular: "sample", plural: "samples" };
      const noun = count === 1 ? labels.singular : labels.plural;
      return `${count} valid ${noun} ready for this request.`;
    }
  },
  methods: {
    fieldHasValue(value) {
      if (value === null || value === undefined) return false;
      if (typeof value === "string") return value.trim() !== "";
      return value !== "";
    },
    isFieldRequired(field, rowData) {
      if (this.addRequestMode === "library") {
        if (field === "index_i7") {
          return Number(rowData.index_reads) >= 1;
        }
        if (field === "index_i5") {
          return Number(rowData.index_reads) >= 2;
        }
        if (field === "measured_value") {
          const unit = rowData.measuring_unit;
          return unit && unit !== "Unknown";
        }
        return LIBRARY_REQUIRED_FIELDS.has(field);
      }
      if (field === "measured_value") {
        const unit = rowData.measuring_unit;
        return unit && unit !== "Unknown";
      }
      return SAMPLE_REQUIRED_FIELDS.has(field);
    },
    toggleFormPanel() {
      this.isFormPanelCollapsed = !this.isFormPanelCollapsed;
    },
    openHelpPage() {
      window.open(
        "https://max.mpg.de/sites/mpi-ie/Facilities/Deep-Sequencing-Facility/Pages/Parkour-Help.aspx",
        "_blank",
        "noopener,noreferrer"
      );
    },
    emitClose() {
      this.$emit("close");
    },
    emitSaved(payload) {
      this.$emit("saved", payload);
    },
    resetState() {
      this.addRequestMode = "library";
      this.isFormPanelCollapsed = false;
      this.addRequestDraftRows = [];
      this.selectedDraftRowIds = [];
      this.draftValidationState = {};
      this.validDraftCount = 0;
      this.isRequestSaving = false;
      this.draftRowCounter = 0;
      this.newRequest = {
        cost_unit: "",
        description: ""
      };
      this.costUnitError = "";
      this.uploadedRequestFiles = [];
      this.uploadedRequestFileIds = [];
      this.showToggleConfirm = false;
      this.pendingToggleMode = null;
      if (this.$refs.requestFileInput) {
        this.$refs.requestFileInput.value = "";
      }
      this.$nextTick(() => this.applyValidationStyling());
    },
    async prepareAddRequestModal() {
      this.resetState();
      await this.ensureModalOptionsLoaded();
      await this.fetchCostUnits();
    },
    async ensureModalOptionsLoaded() {
      await Promise.all([
        this.fetchFilterOptions(),
        this.fetchIndexTypesList(),
        this.fetchNucleicAcidTypes(),
        this.fetchOrganismsList()
      ]);
    },
    triggerRequestFileUpload() {
      this.$refs.requestFileInput?.click?.();
    },
    addDraftRow() {
      this.draftRowCounter += 1;
      const tempId = `draft-${Date.now()}-${this.draftRowCounter}`;
      const baseRow = {
        tempId,
        selected: false,
        name: ""
      };
      const row =
        this.addRequestMode === "sample" ? { ...baseRow, gmo: false } : baseRow;
      this.addRequestDraftRows = [...this.addRequestDraftRows, row];
      this.$nextTick(() => this.revalidateDraftRows());
    },
    deleteSelectedDraftRows() {
      if (!this.selectedDraftRowIds.length) return;
      const ids = new Set(this.selectedDraftRowIds);
      this.addRequestDraftRows = this.addRequestDraftRows.filter(
        (row) => !ids.has(row.tempId)
      );
      this.selectedDraftRowIds = [];
      this.$nextTick(() => this.revalidateDraftRows());
    },
    handleRecordTypeSwitch(mode) {
      const normalized = mode === "sample" ? "sample" : "library";
      if (this.addRequestMode === normalized) return;
      this.addRequestMode = normalized;
      this.addRequestDraftRows = [];
      this.selectedDraftRowIds = [];
      this.draftValidationState = {};
      this.validDraftCount = 0;
      this.draftRowCounter = 0;
      this.$nextTick(() => {
        const table = this.$refs.addRequestDraftTableRef?.tabulatorInstance;
        table?.clearData?.();
        this.applyValidationStyling();
      });
    },
    requestRecordTypeSwitch(event) {
      const nextMode = event?.target?.checked ? "sample" : "library";
      const normalized = nextMode === "sample" ? "sample" : "library";
      if (this.addRequestMode === normalized) return;
      if (this.addRequestDraftRows.length > 0) {
        this.pendingToggleMode = normalized;
        this.showToggleConfirm = true;
        if (event?.target) {
          event.target.checked = this.addRequestMode === "sample";
        }
        return;
      }
      this.handleRecordTypeSwitch(normalized);
    },
    confirmToggleSwitch() {
      if (!this.pendingToggleMode) {
        this.showToggleConfirm = false;
        return;
      }
      const nextMode = this.pendingToggleMode;
      this.pendingToggleMode = null;
      this.showToggleConfirm = false;
      this.handleRecordTypeSwitch(nextMode);
    },
    cancelToggleSwitch() {
      this.pendingToggleMode = null;
      this.showToggleConfirm = false;
    },
    handleConfirmKeydown(event) {
      if (!this.showToggleConfirm) return;
      if (event.key === "Escape") {
        event.preventDefault();
        this.cancelToggleSwitch();
        return;
      }
      if (event.key === "Enter") {
        event.preventDefault();
        this.confirmToggleSwitch();
      }
    },
    formatFileSize(size) {
      if (size === undefined || size === null) return "-";
      const value = Number(size);
      if (Number.isNaN(value)) return "-";
      if (value >= 1024 * 1024) {
        return `${(value / (1024 * 1024)).toFixed(1)} MB`;
      }
      if (value >= 1024) {
        return `${(value / 1024).toFixed(1)} KB`;
      }
      return `${value} B`;
    },
    syncSelectedDraftRows(tableOverride = null) {
      const table =
        tableOverride ||
        this.$refs.addRequestDraftTableRef?.tabulatorInstance ||
        null;
      const rows = table?.getData?.() || this.addRequestDraftRows || [];
      const ids = rows
        .filter((row) => row?.selected)
        .map((row) => row?.tempId)
        .filter((id) => id !== undefined && id !== null);
      this.selectedDraftRowIds = ids;
    },
    revalidateDraftRows() {
      const table = this.$refs.addRequestDraftTableRef?.tabulatorInstance;
      const rows = table?.getData?.() || this.addRequestDraftRows || [];
      const validations = {};
      let validCount = 0;
      rows.forEach((row, index) => {
        if (!row.tempId) {
          row.tempId = `row-${index + 1}-${Date.now()}`;
        }
        const errors =
          this.addRequestMode === "library"
            ? this.validateLibraryRow(row, index)
            : this.validateSampleRow(row, index);
        validations[row.tempId || `row-${index}`] = errors;
        if (!Object.keys(errors).length) {
          validCount += 1;
        }
      });
      this.draftValidationState = validations;
      this.validDraftCount = validCount;
      this.$nextTick(() => this.applyValidationStyling());
      const result = {
        hasErrors: validCount !== rows.length,
        rowCount: rows.length
      };
      return result;
    },
    applyValidationStyling() {
      const table = this.$refs.addRequestDraftTableRef?.tabulatorInstance;
      if (!table) return;
      const cells = table.getCells?.() || [];
      cells.forEach((cell) => {
        const el = cell.getElement?.();
        if (!el) return;
        el.classList.remove("cell-valid", "cell-invalid");
        el.removeAttribute("title");
        el.style.removeProperty("background-color");
        const rowData = cell.getRow?.()?.getData?.();
        const field = cell.getField?.();
        if (!rowData || !field || field === "selected") return;
        const errors = this.draftValidationState[rowData.tempId] || {};
        const valuePresent = this.fieldHasValue(rowData[field]);
        const required = this.isFieldRequired(field, rowData);
        const requiredColorEmpty = "#fdeaea";
        const requiredColorFilled = "#e6f4f1";
        const optionalColor = "#e6f4f1";
        if (required) {
          const color = valuePresent ? requiredColorFilled : requiredColorEmpty;
          el.style.setProperty("background-color", color, "important");
        } else {
          el.style.setProperty("background-color", optionalColor, "important");
        }
        if (errors[field]) {
          el.classList.add("cell-invalid");
          el.setAttribute("title", errors[field]);
        } else if (
          valuePresent
        ) {
          el.classList.add("cell-valid");
        }
      });
    },
    getDraftTableRows() {
      const table = this.$refs.addRequestDraftTableRef?.tabulatorInstance;
      if (table?.getData) {
        return table.getData();
      }
      return this.addRequestDraftRows;
    },
    handleCellEditing(cell) {
      if (!cell) return true;
      const field = cell.getField?.();
      const rowData = cell.getRow?.()?.getData?.() || {};
      if (!field) return true;

      if (field === "measured_value") {
        if (!rowData.measuring_unit) {
          showNotification("Select a Measuring Unit first.", "warning");
          return false;
        }
        if (rowData.measuring_unit === "Unknown") {
          showNotification(
            "Measured Value is managed automatically when the unit is Unknown.",
            "warning"
          );
          return false;
        }
      }

      if (this.addRequestMode === "library") {
        if (field === "index_reads" && !rowData.index_type) {
          showNotification("Select an Index Type first.", "warning");
          return false;
        }
        if (field === "index_i7") {
          const reads = Number(rowData.index_reads) || 0;
          if (reads < 1) {
            return false;
          }
        }
        if (field === "index_i5") {
          const reads = Number(rowData.index_reads) || 0;
          if (reads < 2) {
            return false;
          }
        }
        if (field === "library_type" && !rowData.library_protocol) {
          showNotification("Select a Protocol first.", "warning");
          return false;
        }
        return true;
      }

      if (field === "library_protocol" && !rowData.nucleic_acid_type) {
        showNotification("Select an Input Type first.", "warning");
        return false;
      }
      if (field === "library_type" && !rowData.library_protocol) {
        showNotification("Select a Protocol first.", "warning");
        return false;
      }
      if (
        field === "gmo" &&
        !this.isCellSuspensionType(rowData.nucleic_acid_type)
      ) {
        showNotification(
          "GMO is editable only for Cell Suspension inputs.",
          "warning"
        );
        return false;
      }
      return true;
    },
    handleCellEdited(cell) {
      if (!cell) {
        this.revalidateDraftRows();
        return;
      }
      const field = cell.getField?.();
      const row = cell.getRow?.();
      if (!row) {
        this.revalidateDraftRows();
        return;
      }
      if (this.addRequestMode === "library" && field) {
        this.handleLibraryCellEdited(field, row);
      } else if (this.addRequestMode === "sample" && field) {
        this.handleSampleCellEdited(field, row);
      }
      this.revalidateDraftRows();
    },
    handleLibraryCellEdited(field, row) {
      const data = { ...row.getData() };
      if (field === "index_type") {
        const typeId = data.index_type;
        data.index_reads = "";
        data.index_i7 = "";
        data.index_i5 = "";
        row.update(data);
        if (typeId) {
          this.fetchIndexOptionsForType(typeId);
        }
        return;
      }
      if (field === "library_protocol") {
        data.library_type = "";
        row.update(data);
        return;
      }
      if (field === "measuring_unit") {
        this.applyMeasuringUnitSideEffects(data);
        row.update(data);
        return;
      }
      if (field === "measured_value") {
        if (data.measuring_unit === "Unknown") {
          data.measured_value = -1;
          row.update(data);
        }
        return;
      }
      if (field === "index_reads") {
        const reads = Number(data.index_reads);
        if (!Number.isFinite(reads) || reads < 0) {
          data.index_reads = "";
        }
        if (!reads || reads < 1) {
          data.index_i7 = "";
          data.index_i5 = "";
        } else if (reads === 1) {
          data.index_i5 = "";
        }
        row.update(data);
      }
    },
    handleSampleCellEdited(field, row) {
      const data = { ...row.getData() };
      if (field === "nucleic_acid_type") {
        data.library_protocol = "";
        data.library_type = "";
        data.gmo = this.isCellSuspensionType(data.nucleic_acid_type);
        row.update(data);
        return;
      }
      if (field === "library_protocol") {
        data.library_type = "";
        row.update(data);
        return;
      }
      if (field === "measuring_unit") {
        this.applyMeasuringUnitSideEffects(data);
        row.update(data);
        return;
      }
      if (field === "measured_value") {
        if (data.measuring_unit === "Unknown") {
          data.measured_value = -1;
          row.update(data);
        }
      }
    },
    buildIndexReadsOptions(typeId) {
      if (!typeId) return [];
      const typeKey = String(typeId);
      const match = this.indexTypesList.find((item) => {
        const key =
          item?.id ?? item?.value ?? item?.pk ?? item?.name ?? item?.label;
        return String(key) === typeKey;
      });
      const maxReads = Number(match?.index_reads);
      if (!Number.isFinite(maxReads) || maxReads < 0) return [];
      const options = [];
      for (let i = 0; i <= maxReads; i += 1) {
        options.push({ value: i, label: `${i}` });
      }
      return options;
    },
    getLibraryIndexReadsOptions(rowData = {}) {
      return this.buildIndexReadsOptions(rowData?.index_type);
    },
    getLibraryIndexI7Options(rowData = {}) {
      const typeKey = rowData?.index_type ? String(rowData.index_type) : "";
      if (!typeKey) return [];
      return this.indexI7OptionsByType[typeKey] || [];
    },
    getLibraryIndexI5Options(rowData = {}) {
      const typeKey = rowData?.index_type ? String(rowData.index_type) : "";
      if (!typeKey) return [];
      return this.indexI5OptionsByType[typeKey] || [];
    },
    async fetchIndexOptionsForType(typeId) {
      if (!typeId) return;
      const key = String(typeId);
      if (
        this.indexOptionsLoading[key] ||
        (this.indexI7OptionsByType[key] && this.indexI5OptionsByType[key])
      ) {
        return;
      }
      this.indexOptionsLoading = { ...this.indexOptionsLoading, [key]: true };
      try {
        const [i7Res, i5Res] = await Promise.all([
          axiosRef.get(`${urlStringStart}/api/indices/i7/`, {
            params: { index_type_id: key }
          }),
          axiosRef.get(`${urlStringStart}/api/indices/i5/`, {
            params: { index_type_id: key }
          })
        ]);
        const formatOptions = (response) => {
          const list = response?.data?.data || response?.data || [];
          return list.map((item) => ({
            value: item.index ?? item.value ?? item.id ?? item.name ?? "",
            label: item.name ?? item.index ?? item.index_id ?? ""
          }));
        };
        const i7Options = formatOptions(i7Res);
        const i5Options = formatOptions(i5Res);
        this.indexI7OptionsByType = {
          ...this.indexI7OptionsByType,
          [key]: i7Options
        };
        this.indexI5OptionsByType = {
          ...this.indexI5OptionsByType,
          [key]: i5Options
        };
        this.redrawDraftTable();
      } catch (error) {
        handleError(error);
      } finally {
        const { [key]: _discard, ...rest } = this.indexOptionsLoading;
        this.indexOptionsLoading = rest;
      }
    },
    redrawDraftTable() {
      const table = this.$refs.addRequestDraftTableRef?.tabulatorInstance;
      table?.redraw?.();
    },
    normalizeNumber(value) {
      if (value === "" || value === undefined || value === null) return null;
      const num = Number(value);
      return Number.isNaN(num) ? null : num;
    },
    normalizeId(value) {
      if (value === "" || value === undefined || value === null) {
        return null;
      }
      const numeric = Number(value);
      return Number.isNaN(numeric) ? value : numeric;
    },
    getNucleicAcidMeta(value) {
      if (value === null || value === undefined || value === "") return null;
      const target = String(value);
      return (
        this.nucleicAcidTypesList.find((item) => {
          const key =
            item?.id ?? item?.value ?? item?.pk ?? item?.name ?? item?.label;
          return String(key) === target;
        }) || null
      );
    },
    isCellSuspensionType(value) {
      const meta = this.getNucleicAcidMeta(value);
      if (!meta || typeof meta.name !== "string") {
        return false;
      }
      return meta.name.trim().toLowerCase() === "cell suspension";
    },
    applyMeasuringUnitSideEffects(rowData) {
      if (!rowData) return;
      const unit = rowData.measuring_unit;
      if (!unit) {
        rowData.measured_value = null;
        return;
      }
      if (unit === "Unknown") {
        rowData.measured_value = -1;
        return;
      }
      if (rowData.measured_value === null || rowData.measured_value === -1) {
        rowData.measured_value = null;
      }
    },
    coerceMeasuredValue(row) {
      if (row.measuring_unit === "Unknown") {
        return -1;
      }
      return this.normalizeNumber(row.measured_value);
    },
    validateLibraryRow(row, index) {
      const prefix = `Row ${index + 1}`;
      const errors = {};
      const name = (row.name || "").trim();
      if (!name) {
        errors.name = `${prefix}: Name is required.`;
      } else if (!/^[A-Za-z0-9_-]+$/.test(name)) {
        errors.name = `${prefix}: Name must contain only letters, numbers, _ or -.`;
      }
      if (!row.library_protocol) {
        errors.library_protocol = `${prefix}: Protocol is required.`;
      }
      if (!row.library_type) {
        errors.library_type = `${prefix}: Analysis Type is required.`;
      }
      if (!row.read_length) {
        errors.read_length = `${prefix}: Read Length is required.`;
      }
      const depth = this.normalizeNumber(row.sequencing_depth);
      if (depth === null || depth < 1) {
        errors.sequencing_depth = `${prefix}: Sequencing Depth must be at least 1.`;
      }
      if (!row.organism) {
        errors.organism = `${prefix}: Organism is required.`;
      }
      if (!row.index_type) {
        errors.index_type = `${prefix}: Index Type is required.`;
      }
      const reads = this.normalizeNumber(row.index_reads);
      if (reads === null) {
        errors.index_reads = `${prefix}: # of Index Reads is required.`;
      }
      if (reads >= 1 && !row.index_i7) {
        errors.index_i7 = `${prefix}: Index I7 is required.`;
      }
      if (reads >= 2 && !row.index_i5) {
        errors.index_i5 = `${prefix}: Index I5 is required when using 2 reads.`;
      }
      if (
        row.measuring_unit &&
        row.measuring_unit !== "Unknown" &&
        this.normalizeNumber(row.measured_value) === null
      ) {
        errors.measured_value = `${prefix}: Amount is required when a measuring unit is selected.`;
      }
      return errors;
    },
    validateSampleRow(row, index) {
      const prefix = `Row ${index + 1}`;
      const errors = {};
      const name = (row.name || "").trim();
      if (!name) {
        errors.name = `${prefix}: Name is required.`;
      } else if (!/^[A-Za-z0-9_-]+$/.test(name)) {
        errors.name = `${prefix}: Name must contain only letters, numbers, _ or -.`;
      }
      if (!row.nucleic_acid_type) {
        errors.nucleic_acid_type = `${prefix}: Input Type is required.`;
      }
      if (!row.library_protocol) {
        errors.library_protocol = `${prefix}: Protocol is required.`;
      }
      if (!row.library_type) {
        errors.library_type = `${prefix}: Analysis Type is required.`;
      }
      if (!row.read_length) {
        errors.read_length = `${prefix}: Read Length is required.`;
      }
      const depth = this.normalizeNumber(row.sequencing_depth);
      if (depth === null || depth < 1) {
        errors.sequencing_depth = `${prefix}: Sequencing Depth must be at least 1.`;
      }
      if (!row.organism) {
        errors.organism = `${prefix}: Organism is required.`;
      }
      if (!row.biosafety_level) {
        errors.biosafety_level = `${prefix}: Biosafety Level is required.`;
      }
      if (
        row.measuring_unit &&
        row.measuring_unit !== "Unknown" &&
        this.normalizeNumber(row.measured_value) === null
      ) {
        errors.measured_value = `${prefix}: Measured Value is required when a unit is selected.`;
      }
      return errors;
    },
    buildLibraryPayload(row) {
      return {
        name: (row.name || "").trim(),
        library_protocol: this.normalizeId(row.library_protocol),
        library_type: this.normalizeId(row.library_type),
        measuring_unit: row.measuring_unit || null,
        measured_value: this.coerceMeasuredValue(row),
        mean_fragment_size: this.normalizeNumber(row.mean_fragment_size),
        volume: this.normalizeNumber(row.volume),
        read_length: this.normalizeId(row.read_length),
        sequencing_depth: this.normalizeNumber(row.sequencing_depth),
        index_type: this.normalizeId(row.index_type),
        index_reads: this.normalizeNumber(row.index_reads),
        index_i7: row.index_i7 || null,
        index_i5: row.index_i5 || null,
        organism: this.normalizeId(row.organism),
        comments: row.comments || ""
      };
    },
    buildSamplePayload(row) {
      const rawGmo = row.gmo;
      const gmoValue =
        typeof rawGmo === "string"
          ? rawGmo === "true"
          : rawGmo === true;
      return {
        name: (row.name || "").trim(),
        nucleic_acid_type: this.normalizeId(row.nucleic_acid_type),
        library_protocol: this.normalizeId(row.library_protocol),
        library_type: this.normalizeId(row.library_type),
        measuring_unit: row.measuring_unit || null,
        measured_value: this.coerceMeasuredValue(row),
        volume: this.normalizeNumber(row.volume),
        read_length: this.normalizeId(row.read_length),
        sequencing_depth: this.normalizeNumber(row.sequencing_depth),
        organism: this.normalizeId(row.organism),
        comments: row.comments || "",
        biosafety_level: row.biosafety_level || null,
        gmo: gmoValue
      };
    },
    async handleRequestFileUpload(event) {
      const files = Array.from(event.target.files || []);
      if (!files.length) {
        showNotification("You did not select any files.", "warning");
        return;
      }
      const formData = new FormData();
      files.forEach((file) => formData.append("files", file));
      try {
        const response = await axiosRef.post(
          `${urlStringStart}/api/requests/upload_files/`,
          formData,
          {
            headers: { "Content-Type": "multipart/form-data" }
          }
        );
        if (response?.data?.success) {
          const ids = response.data.fileIds || [];
          this.uploadedRequestFileIds = [...this.uploadedRequestFileIds, ...ids];
          await this.fetchUploadedFilesDetails();
          showNotification("Files uploaded.", "success");
        } else {
          showNotification("Could not upload files.", "error");
        }
      } catch (error) {
        handleError(error);
      } finally {
        if (event?.target) {
          event.target.value = "";
        }
      }
    },
    async fetchUploadedFilesDetails() {
      if (!this.uploadedRequestFileIds.length) {
        this.uploadedRequestFiles = [];
        return;
      }
      try {
        const response = await axiosRef.get(
          `${urlStringStart}/api/requests/get_files_after_upload/`,
          {
            params: {
              file_ids: JSON.stringify(this.uploadedRequestFileIds)
            }
          }
        );
        if (response?.data?.success) {
          this.uploadedRequestFiles = response.data.data || [];
        }
      } catch (error) {
        handleError(error);
      }
    },
    removeUploadedFile(fileId) {
      this.uploadedRequestFileIds = this.uploadedRequestFileIds.filter(
        (id) => id !== fileId
      );
      this.uploadedRequestFiles = this.uploadedRequestFiles.filter(
        (f) => f.id !== fileId
      );
    },
    downloadUploadedFile(file) {
      if (!file?.path) {
        showNotification(
          "Download link is not available for this file.",
          "warning"
        );
        return;
      }
      const link = document.createElement("a");
      link.href = file.path;
      link.target = "_blank";
      link.rel = "noopener";
      link.download = file.name || "request-file";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    },
    async fetchCostUnits() {
      try {
        const response = await axiosRef.get(`${urlStringStart}/api/cost_units/`);
        this.costUnits = response.data || [];
      } catch (error) {
        handleError(error);
      }
    },
    async saveNewRequest() {
      if (this.isRequestSaving) return;
      const description = (this.newRequest.description || "").trim();
      const descriptionValid = !!description;
      if (!descriptionValid) {
        this.descriptionError = "Description is required.";
      }
      if (!this.isStaffUser && !this.newRequest.cost_unit) {
        this.costUnitError = "Cost unit is required.";
      }
      if (this.descriptionError || this.costUnitError) {
        showNotification("Please fill required fields.", "warning");
        return;
      }
      const { rowCount } = this.revalidateDraftRows();
      if (!rowCount) {
        showNotification("Add at least one Library or Sample before saving.", "warning");
        return;
      }
      if (this.validDraftCount !== rowCount) {
        showNotification("Please resolve all validation errors before saving.", "warning");
        return;
      }
      const drafts = this.getDraftTableRows();
      const payloads =
        this.addRequestMode === "library"
          ? drafts.map((row) => this.buildLibraryPayload(row))
          : drafts.map((row) => this.buildSamplePayload(row));
      const recordTypeLabel = this.addRequestModeLabel;
      const payload = {
        cost_unit: this.newRequest.cost_unit || null,
        description,
        records: [],
        files: this.uploadedRequestFileIds
      };
      try {
        this.isRequestSaving = true;
        const endpoint =
          this.addRequestMode === "library" ? "libraries" : "samples";
        const created = await this.submitAddRequest(endpoint, payloads);
        if (!created.length) {
          showNotification("No records were created.", "error");
          return;
        }
        payload.records = created.map((record, index) => ({
          pk: record.pk,
          record_type: record.record_type || recordTypeLabel,
          name: record.name,
          barcode: record.barcode,
          id: record.id || `Record-${record.pk || index + 1}`,
          status: record.status ?? null,
          is_converted: record.is_converted ?? false,
          selected: false
        }));
        const formData = new FormData();
        formData.append("data", JSON.stringify(payload));
        const response = await axiosRef.post(
          `${urlStringStart}/api/requests/`,
          formData,
          {
            headers: { "Content-Type": "multipart/form-data" }
          }
        );
        if (response?.data?.success) {
          showNotification("Request created successfully.", "success");
          this.emitSaved(response.data);
          this.emitClose();
        } else {
          showNotification("Failed to create request.", "error");
        }
      } catch (error) {
        handleError(error);
      } finally {
        this.isRequestSaving = false;
      }
    },
    async submitAddRequest(endpoint, payloads) {
      const formData = new FormData();
      formData.append("data", JSON.stringify(payloads));
      const response = await axiosRef.post(
        `${urlStringStart}/api/${endpoint}/`,
        formData,
        {
          headers: { "Content-Type": "multipart/form-data" }
        }
      );
      const success =
        response?.data?.success === undefined
          ? true
          : Boolean(response.data.success);
      if (!success) {
        throw new Error("Server rejected the request.");
      }
      return response?.data?.data || [];
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
      } catch (error) {
        handleError(error);
      }
    },
    async fetchIndexTypesList() {
      try {
        const response = await axiosRef.get(
          `${urlStringStart}/api/index_types/`
        );
        this.indexTypesList = (response.data || []).sort((a, b) =>
          a.name.localeCompare(b.name, undefined, { sensitivity: "base" })
        );
      } catch (error) {
        handleError(error);
      }
    },
    async fetchNucleicAcidTypes() {
      try {
        const response = await axiosRef.get(
          `${urlStringStart}/api/nucleic_acid_types/`
        );
        this.nucleicAcidTypesList = (response.data || []).sort((a, b) =>
          a.name.localeCompare(b.name, undefined, { sensitivity: "base" })
        );
      } catch (error) {
        handleError(error);
      }
    },
    async fetchOrganismsList() {
      try {
        const response = await axiosRef.get(`${urlStringStart}/api/organisms/`);
        this.organismsList = (response.data || []).sort((a, b) =>
          a.name.localeCompare(b.name, undefined, { sensitivity: "base" })
        );
      } catch (error) {
        handleError(error);
      }
    }
  }
};
</script>

<style scoped>
.add-request-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  z-index: 999;
}

.add-request-modal {
  background: white;
  border-radius: 8px;
  width: calc(100% - 60px);
  height: calc(100% - 60px);
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.2);
}

.confirm-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1001;
}

.confirm-modal {
  background: #ffffff;
  border-radius: 8px;
  width: 420px;
  max-width: calc(100% - 40px);
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.25);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.confirm-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #0b5f5a;
  background: #006c64;
}

.confirm-title {
  font-size: 14px;
  font-weight: 600;
  color: #ffffff;
}

.confirm-body {
  padding: 16px;
  font-size: 13px;
  color: #333;
  line-height: 1.5;
}

.confirm-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  padding: 12px 16px 16px;
}

.confirm-modal .popup-close-button {
  color: #ffffff;
}

.confirm-modal .popup-close-button:hover {
  color: #cfe9e6;
}

.confirm-modal .popup-button {
  background: #006c64;
  border: 1px solid #0b5f5a;
  color: #ffffff;
  border-radius: 6px;
  padding: 6px 16px;
  font-weight: 600;
}

.confirm-modal .popup-button:hover {
  background: #0a5d56;
}

.confirm-modal .popup-button:not(.yes-button) {
  background: #ffffff;
  color: #006c64;
}

.confirm-modal .popup-button:not(.yes-button):hover {
  background: #e8f2f1;
}

.add-request-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid #e5e7eb;
  font-size: 20px;
  font-weight: 600;
  color: #13415b;
}

.title-with-icon {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.header-icon {
  font-size: 20px;
  color: #13415b;
}

.header-actions {
  display: inline-flex;
  align-items: center;
  gap: 12px;
}

.add-request-header .popup-close-button {
  color: #13415b;
  font-size: 24px;
}

.add-request-header .popup-close-button:hover {
  color: #0f5c84;
}

.help-button {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: none;
  background: transparent;
  color: #13415b;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 600;
}

.help-button:hover {
  color: #0f5c84;
}

.add-request-body {
  flex: 1;
  display: flex;
  gap: 20px;
  padding: 20px 24px;
  overflow: hidden;
}

.request-form-panel {
  width: 320px;
  min-width: 290px;
  border-right: 1px solid #e5e7eb;
  padding-right: 12px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
  transition: width 0.25s ease, padding 0.25s ease, opacity 0.25s ease;
}

.request-panel-container {
  display: flex;
  align-items: stretch;
  position: relative;
}

.request-panel-container.collapsed {
  border-right: none;
}

.request-form-panel.collapsed {
  width: 0;
  min-width: 0;
  padding-right: 0;
  opacity: 0;
  pointer-events: none;
  border-right: none;
}

.field-block {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 13px;
  color: #333;
}

.field-block select {
  padding: 11px 8px;
  border: 1px solid #d0d0d0;
  border-radius: 8px;
  font-size: 14px;
  font-family: inherit;
  color: #232323;
  background: #f4f6f8;
  line-height: 1.5;
  box-sizing: border-box;
}

.field-block textarea {
  padding: 11px 12px;
  border: 1px solid #d0d0d0;
  border-radius: 8px;
  font-size: 14px;
  font-family: inherit;
  color: #232323;
  background: #f4f6f8;
  line-height: 1.5;
  box-sizing: border-box;
}

.field-block select.placeholder {
  color: #9ba3af;
}

.field-block select.placeholder option {
  color: #232323;
}

.description-textarea {
  width: 100%;
  min-height: 200px;
  resize: none;
  line-height: 1.5;
}

.description-textarea::placeholder {
  color: #9ba3af;
}

.input-error {
  border-color: #d14343 !important;
}

.field-error {
  margin-top: 4px;
  font-size: 12px;
  color: #b42318;
}

.required {
  color: #b42318;
  margin-left: 1px;
}

.files-section {
  border: 1px solid #d0d0d0;
  background: #f6f8fa;
  border-radius: 8px;
  padding: 12px;
}

.files-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.files-header small {
  display: block;
  font-size: 11px;
  color: #6b7280;
}

.files-table {
  width: 100%;
  border: 1px solid #d0d0d0;
  border-collapse: separate;
  border-spacing: 0;
  table-layout: fixed;
  overflow: hidden;
  margin-top: 8px;
  font-size: 12px;
  border-radius: 8px;
}

.files-table th,
.files-table td {
  padding: 8px 12px;
  text-align: left;
  vertical-align: middle;
  line-height: 1.4;
}

.files-table th {
  border-bottom: 1px solid #d0d0d0;
}

.files-table .empty-cell {
  text-align: center;
  color: #7b7f89;
}

.files-table td.actions-cell {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 3px;
}

.files-table td.actions-cell button+button {
  margin-left: 4px;
}

.file-name-cell {
  max-width: 220px;
  display: flex;
  align-items: center;
}

.file-name-text {
  display: inline-block;
  max-width: 100%;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-size-cell {
  max-width: 140px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.icon-action {
  border: none;
  background: #e6eaef;
  color: #13415b;
  width: 24px;
  height: 24px;
  border-radius: 6px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.icon-action:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.icon-action.danger {
  background: #f3d6d6;
  color: #a3272b;
}

.signed-request-info {
  font-size: 13px;
  color: #374151;
  border: 1px solid #d0d0d0;
  border-radius: 6px;
  padding: 12px 14px;
  background: #f9fafb;
  margin-bottom: 12px;
}

.signed-request-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.signed-request-row {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 10px;
  font-weight: 500;
  flex-wrap: wrap;
}

.signed-request-label {
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}

.signed-request-status {
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 2px 8px;
  border-radius: 999px;
  border: 1px solid;
}

.signed-request-info .info-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 8px;
  border: none;
  background: #1864ab;
  color: #ffffff;
  font-size: 12px;
  cursor: help;
}

.download-buttons {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px;
  border: 1px solid #d0d0d0;
  border-radius: 6px;
  background: #f6f8fa;
}

.download-button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border: 1px solid #0f5c84;
  border-radius: 6px;
  background: #ffffff;
  color: #0f5c84;
  font-size: 12px;
  font-weight: 600;
  text-decoration: none;
  transition: background 0.2s ease, color 0.2s ease, border-color 0.2s ease;
}

.download-button:hover {
  background: #e8f2f7;
  border-color: #0a4a6a;
  color: #0a4a6a;
}

.status-success {
  color: #0f766e;
  border-color: #0f766e;
  background: rgba(15, 118, 110, 0.08);
}

.status-warning {
  color: #b45309;
  border-color: #f59e0b;
  background: rgba(245, 158, 11, 0.12);
}

.records-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow: hidden;
}

.records-panel.expanded {
  flex-basis: calc(100% - 34px);
}

.panel-toggle-button {
  width: 34px;
  border: none;
  border-left: 1px solid #e5e7eb;
  background: #f6f8fa;
  color: #0f5c84;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s ease;
  border-top-right-radius: 8px;
  border-bottom-right-radius: 8px;
}

.panel-toggle-button:hover {
  background: #e2e7ea;
}

.records-toolbar {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.switch-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.controls-group {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px;
  border: 1px solid #d0d0d0;
  border-radius: 6px;
  background: #f6f8fa;
}

.switch-label {
  font-size: 12px;
  text-transform: uppercase;
  color: #5f6473;
  font-weight: 600;
}

.record-type-switch {
  position: relative;
  width: 150px;
  height: 36px;
  border-radius: 8px;
  background: #e1e6ea;
  border: 1px solid #d0d0d0;
  cursor: pointer;
  padding: 4px;
}

.record-type-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.record-type-switch .slider {
  position: absolute;
  inset: 4px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 12px;
  font-weight: 600;
  color: #4b5563;
}

.record-type-switch .slider::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  width: 50%;
  height: 100%;
  border-radius: 8px;
  background: #0f766e;
  transition: transform 0.25s ease;
  z-index: 0;
}

.record-type-switch input:checked+.slider::before {
  transform: translateX(100%);
}

.record-type-switch .option {
  flex: 1;
  text-align: center;
  z-index: 1;
  transition: color 0.2s ease;
}

.record-type-switch .option.active {
  color: white;
}

.icon-button {
  width: 34px;
  height: 34px;
  border-radius: 8px;
  border: none;
  background: #0f766e;
  color: white;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.icon-button:disabled {
  background: #e1e6ea;
  color: #707b8d;
  cursor: not-allowed;
}

.draft-table {
  flex: 1;
  min-height: 260px;
}

.add-request-footer {
  border-top: 1px solid #e5e7eb;
  padding: 12px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.footer-summary {
  font-size: 13px;
  color: #374151;
  display: flex;
  gap: 6px;
  align-items: center;
}

.footer-actions {
  display: flex;
  gap: 10px;
}

.header-button.ghost {
  background: #0f766e;
}

.add-request-modal .cell-valid {
  background-color: #e8f5e9 !important;
}

.add-request-modal .cell-invalid {
  background-color: #fdecea !important;
}
</style>


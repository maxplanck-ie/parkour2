<template>
  <div v-if="show" class="request-editor-overlay popup-overlay" :class="{ 'drag-over': isDragOver }"
    @dragover.prevent="handleDragOver" @dragenter.prevent="handleDragEnter" @dragleave.prevent="handleDragLeave"
    @drop.prevent="handleDrop">
    <div v-if="canEditRequest" class="drag-drop-indicator">
      <div style="display: flex; justify-content: center; align-items: center; height: 200px;">
        <p>
          Drop <span style="font-weight: bold">files</span> here to upload
        </p>
      </div>
    </div>
    <div class="request-editor-modal">
      <div v-if="fakeLoading" class="request-editor-loading-overlay" aria-hidden="true"></div>
      <div v-if="isEditMode && !requestDataReady" class="request-editor-loading-overlay" aria-live="polite"
        aria-busy="true">
        <div class="spinner"></div>
        <p>Loading request details...</p>
      </div>
      <div class="request-editor-content" :class="{ collapsed: isFormPanelCollapsed }">
        <div class="request-editor-header-left" :class="{ collapsed: isFormPanelCollapsed }">
          <span class="title-with-icon">
            <font-awesome-icon icon="fa-solid fa-file-lines" class="header-icon" />
            <span class="header-title-text" :title="headerTitle">{{ headerTitle }}</span>
          </span>
        </div>
        <button class="panel-toggle-button vertical-toggle" type="button" @click="toggleFormPanel"
          :aria-label="isFormPanelCollapsed ? 'Expand details panel' : 'Collapse details panel'">
          <font-awesome-icon :icon="isFormPanelCollapsed ? 'fa-solid fa-angle-right' : 'fa-solid fa-angle-left'" />
        </button>
        <div class="request-editor-header-right">
          <div class="header-table-actions" :class="{ hidden: !canEditRequest }">
            <div class="add-count-group">
              <input id="add-count-input" v-model.number="addRowCount" type="number" min="0"
                :class="['add-count-input', { 'input-error': hasEditedAddCount && !addRowCount }]"
                :disabled="!canEditRequest" @input="hasEditedAddCount = true" @blur="hasEditedAddCount = true" />
              <button class="icon-button text-button add-count-button" type="button" :title="addButtonTitle"
                :disabled="!canEditRequest" @click="addDraftRow(addRowCount)">
                <font-awesome-icon icon="fa-solid fa-square-plus" />
                <span>{{ addButtonLabel }}</span>
              </button>
            </div>
            <button class="icon-button text-button" type="button" :title="deleteButtonTitle"
              :disabled="!canEditRequest || !selectedDraftRowIds.length" @click="requestDeleteSelectedDraftRows">
              <font-awesome-icon icon="fa-solid fa-trash" />
              <span>Delete Selected</span>
            </button>
          </div>
          <div class="header-table-actions utility-actions" :class="{ hidden: !canEditRequest }"
            title="Clipboard Actions">
            <button class="icon-button text-button clipboard-button" type="button"
              title="Cut the selected range to the clipboard" :disabled="!canEditRequest || !hasEditableRangeSelection"
              @click="triggerTableCut">
              <font-awesome-icon icon="fa-solid fa-scissors" />
              <span>Cut</span>
            </button>
            <button class="icon-button text-button clipboard-button" type="button"
              title="Copy the selected range to the clipboard"
              :disabled="!requestEditorDraftRows.length || !hasRangeSelection" @click="triggerTableCopy">
              <font-awesome-icon icon="fa-solid fa-copy" />
              <span>Copy</span>
            </button>
            <button class="icon-button text-button clipboard-button" type="button"
              title="Paste clipboard data into the selected range"
              :disabled="!canEditRequest || !hasEditableRangeSelection" @click="triggerTablePaste">
              <font-awesome-icon icon="fa-solid fa-paste" />
              <span>Paste</span>
            </button>
            <button class="icon-button text-button clipboard-button" type="button"
              title="Clear values in the selected range" :disabled="!canEditRequest || !hasEditableRangeSelection"
              @click="triggerTableClear">
              <font-awesome-icon icon="fa-solid fa-eraser" />
              <span>Clear</span>
            </button>
            <button class="icon-button text-button clipboard-button" type="button"
              title="Apply the selected cell value to this column for all rows in this request"
              :disabled="!canEditRequest || !isSingleCellSelected" @click="triggerApplyToAll">
              <font-awesome-icon icon="fa-solid fa-wand-magic-sparkles" />
              <span>Apply to All</span>
            </button>
          </div>
          <div class="header-actions">
            <button class="help-button" type="button" @click="openHelpPage" title="Open MAX page on Intranet">
              ?
            </button>
            <button class="popup-close-button" type="button" @click="requestCloseModal" :disabled="saving">
              &times;
            </button>
          </div>
        </div>

        <div class="request-editor-body-left">
          <div class="request-panel-container" :class="{ collapsed: isFormPanelCollapsed }">
            <section class="request-form-panel" :class="{ collapsed: isFormPanelCollapsed }">
              <div class="request-form-actions">
                <div class="controls-group" :class="{ 'view-only': isEditMode }">
                  <label class="record-type-switch" title="Switch between Library and Sample entry modes">
                    <input type="checkbox" :checked="requestEditorMode === 'sample'" :disabled="!canEditRequest"
                      @change="requestRecordTypeSwitch($event)" />
                    <span class="slider">
                      <span class="option" :class="{ active: requestEditorMode === 'library' }">
                        Library
                      </span>
                      <span class="option" :class="{ active: requestEditorMode === 'sample' }">
                        Sample
                      </span>
                    </span>
                  </label>
                </div>
                <div v-if="requestEditorMode === 'sample' && !isEditMode" class="download-buttons">
                  <a class="download-button" :href="gmoFormUrl" target="_blank" rel="noopener"
                    title="Download Formblatt S1 (GMO)">
                    <font-awesome-icon icon="fa-solid fa-download" />
                    <span>Formblatt S1</span>
                  </a>
                  <a class="download-button" :href="relacsDownloadUrl" target="_blank" rel="noopener"
                    title="Download RELACS Pellets Abs form">
                    <font-awesome-icon icon="fa-solid fa-download" />
                    <span>RELACS Pellets Abs</span>
                  </a>
                </div>
              </div>

              <label class="field-block">
                <span>
                  Cost Unit<span v-if="!isStaffUser" class="required">*</span>
                </span>
                <select v-model="newRequest.cost_unit" :disabled="!canEditRequest" :class="[
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
                  :placeholder="isEditMode
                    ? 'Description not provided'
                    : 'Provide a brief description of your project, including any details important for handling and documentation. Indicate whether you have a backup of your study material (Yes/No).'"
                  :class="{ 'input-error': descriptionError }" :readonly="!canEditRequest"></textarea>
                <div v-if="descriptionError" class="field-error">
                  {{ descriptionError }}
                </div>
              </label>

              <div class="files-section">
                <div class="files-header">
                  <div>
                    <span>Files</span>
                    <small>Upload request related documents.</small>
                  </div>
                  <button v-if="canEditRequest" class="header-button ghost" type="button" :disabled="!canEditRequest"
                    @click="triggerRequestFileUpload">
                    <font-awesome-icon icon="fa-solid fa-square-plus" style="color: white" />
                    <span>Add Files</span>
                  </button>
                  <input ref="requestFileInput" type="file" multiple @change="handleRequestFileUpload"
                    style="display: none" />
                </div>
                <div class="files-table-wrapper">
                  <table class="files-table" :class="{ 'files-table-empty': !uploadedRequestFiles.length }">
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
                          <button v-if="canEditRequest" type="button" class="icon-action danger"
                            :title="`Remove ${file.name}`" :disabled="!canEditRequest"
                            @click="requestRemoveUploadedFile(file)">
                            <font-awesome-icon icon="fa-solid fa-xmark" />
                          </button>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>


            </section>
          </div>
        </div>

        <div class="request-editor-body-right">
          <section class="records-panel" :class="{ expanded: isFormPanelCollapsed }">
            <div class="draft-table" ref="draftTableWrapper">
              <TabulatorTable ref="requestEditorDraftTableRef" tableId="requestEditorDraftTable"
                :rowData="requestEditorDraftRows" :columnDefs="requestEditorColumns"
                :tableOptions="requestEditorDraftTableOptions" :groupBy="null" :groupSort="null" :groupStartOpen="false"
                :enableDefaultFilters="false" />
            </div>
          </section>
        </div>

        <div class="request-editor-footer">
          <div class="footer-summary">
            <span>{{ footerLabel }}</span>
          </div>
          <div class="footer-actions">
            <button class="popup-button secondary" type="button" @click="requestCloseModal" :disabled="saving">
              Cancel
            </button>
            <button class="popup-button yes-button" type="button"
              :disabled="isRequestSaving || (isEditMode && isRequestLoading) || !canEditRequest" @click="saveRequest">
              <span v-if="isRequestSaving">Saving...</span>
              <span v-else>{{ primaryActionLabel }}</span>
            </button>
          </div>
        </div>
      </div>
      <div v-if="saving" class="saving-overlay" aria-live="polite" aria-busy="true">
        <div class="saving-card">
          <div class="spinner"></div>
          <p>Saving request, please wait...</p>
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
          Switching between Library and Sample will clear all {{ switchClearLabel }} you have added.
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
    <div v-if="showDeleteConfirm" class="confirm-overlay" @keydown="handleDeleteConfirmKeydown" tabindex="0">
      <div class="confirm-modal">
        <div class="confirm-header">
          <span class="confirm-title">{{ deleteConfirmTitle }}</span>
          <button class="popup-close-button" type="button" @click="cancelDeleteSelectedRows">
            &times;
          </button>
        </div>
        <div class="confirm-body">
          This will permanently remove {{ selectedDraftRowIds.length }} {{ deleteConfirmNoun }}.
          Do you want to continue?
        </div>
        <div class="confirm-footer">
          <button class="popup-button" type="button" @click="cancelDeleteSelectedRows">
            Cancel
          </button>
          <button class="popup-button yes-button" type="button" @click="confirmDeleteSelectedRows">
            OK
          </button>
        </div>
      </div>
    </div>
    <div v-if="showCloseConfirm" class="confirm-overlay" @keydown="handleCloseConfirmKeydown" tabindex="0">
      <div class="confirm-modal">
        <div class="confirm-header">
          <span class="confirm-title">Discard new request?</span>
          <button class="popup-close-button" type="button" @click="cancelCloseModal">
            &times;
          </button>
        </div>
        <div class="confirm-body">
          Closing now will discard your entered data. Do you want to continue?
        </div>
        <div class="confirm-footer">
          <button class="popup-button" type="button" @click="cancelCloseModal">
            Cancel
          </button>
          <button class="popup-button yes-button" type="button" @click="confirmCloseModal">
            OK
          </button>
        </div>
      </div>
    </div>
    <div v-if="showFileDeleteConfirm" class="confirm-overlay" @keydown="handleFileDeleteConfirmKeydown" tabindex="0">
      <div class="confirm-modal">
        <div class="confirm-header">
          <span class="confirm-title">Delete file?</span>
          <button class="popup-close-button" type="button" @click="cancelFileDelete">
            &times;
          </button>
        </div>
        <div class="confirm-body">
          Are you sure you want to remove "{{ pendingFileDelete?.name }}" from this request?
        </div>
        <div class="confirm-footer">
          <button class="popup-button secondary" type="button" @click="cancelFileDelete">
            Cancel
          </button>
          <button class="popup-button yes-button" type="button" @click="confirmFileDelete">
            Remove
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import TabulatorTable from "../components/tabulatorTable.vue";
import {
  applyValueToAllRows,
  showNotification,
  handleError,
  createAxiosObject,
  urlStringStartsWith
} from "../utilities/utilityFunctions";
import {
  getRequestEditorLibraryColumns,
  getRequestEditorSampleColumns,
  LIBRARY_REQUIRED_FIELDS,
  SAMPLE_REQUIRED_FIELDS
} from "../constants/requestEditorConsts";

const axiosRef = createAxiosObject();
const urlStringStart = urlStringStartsWith();

export default {
  name: "RequestEditorView",
  components: {
    TabulatorTable
  },
  props: {
    show: {
      type: Boolean,
      default: false
    },
    saving: {
      type: Boolean,
      default: false
    },
    closeOnSave: {
      type: Boolean,
      default: true
    },
    notifyOnSave: {
      type: Boolean,
      default: true
    },
    mode: {
      type: String,
      default: "create"
    },
    requestId: {
      type: [Number, String],
      default: null
    },
    isStaffUser: {
      type: Boolean,
      default: false
    },
    userId: {
      type: [Number, String],
      default: null
    },
    requestMeta: {
      type: Object,
      default: null
    }
  },
  data() {
    return {
      requestEditorMode: "library",
      isFormPanelCollapsed: false,
      requestEditorDraftRows: [],
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
      indexPairsByType: {},
      indexOptionsLoading: {},
      hasEditedAddCount: false,
      allowDirtyTracking: false,
      suppressNextDirtyBatch: false,
      pendingDirtyTrackingResume: false,
      dirtyFieldsByRowId: {},
      validationFieldsByRowId: {},
      showToggleConfirm: false,
      showDeleteConfirm: false,
      showCloseConfirm: false,
      showFileDeleteConfirm: false,
      pendingToggleMode: null,
      existingRecords: [],
      isDragOver: false,
      editRecordsByType: {
        library: [],
        sample: []
      },
      editRecordTypesAvailable: {
        library: false,
        sample: false
      },
      pendingFileDelete: null,
      editSnapshot: {
        cost_unit: "",
        description: "",
        fileIds: []
      },
      requestName: "",
      restrictPermissions: false,
      isRequestLoading: false,
      newRequest: {
        cost_unit: "",
        description: ""
      },
      costUnits: [],
      costUnitError: "",
      descriptionError: "",
      requestOwnerId: null,
      uploadedRequestFiles: [],
      uploadedRequestFileIds: [],
      protocolsList: [],
      analysisTypesList: [],
      readLengthsList: [],
      nucleicAcidTypesList: [],
      organismsList: [],
      filterOptionsLoaded: false,
      indexTypesLoaded: false,
      nucleicAcidTypesLoaded: false,
      organismsLoaded: false,
      costUnitsLoadedForUser: null,
      prepareTimer: null,
      isPreparingModal: false,
      indexTypesList: [],
      fakeLoading: false,
      fakeLoadingTimer: null,
      requestDataReady: false,
      addRowCount: 1,
      hasRangeSelection: false,
      hasEditableRangeSelection: false,
      isSingleCellSelected: false,
      rangeListenersAttached: false,
      rangeSelectionHandler: null,
      rangeSelectionElement: null,
    };
  },
  watch: {
    show(newVal) {
      if (newVal) {
        if (this.isEditMode) {
          this.isRequestLoading = true;
          this.requestDataReady = false;
        }
        this.addRowCount = this.isEditMode ? 0 : 1;
        this.schedulePrepareRequestEditorModal();
      } else {
        if (this.prepareTimer) {
          clearTimeout(this.prepareTimer);
          this.prepareTimer = null;
        }
        this.resetState();
      }
    },
    mode() {
      if (this.show) {
        this.schedulePrepareRequestEditorModal();
      }
    },
    requestId() {
      if (this.show && this.isEditMode) {
        this.schedulePrepareRequestEditorModal();
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
    showDeleteConfirm(newVal) {
      if (newVal) {
        this.$nextTick(() => {
          const overlays = this.$el?.querySelectorAll?.(".confirm-overlay");
          const overlay = overlays?.[overlays.length - 1];
          overlay?.focus?.();
        });
      }
    },
    showCloseConfirm(newVal) {
      if (newVal) {
        this.$nextTick(() => {
          const overlays = this.$el?.querySelectorAll?.(".confirm-overlay");
          const overlay = overlays?.[overlays.length - 1];
          overlay?.focus?.();
        });
      }
    },
    showFileDeleteConfirm(newVal) {
      if (newVal) {
        this.$nextTick(() => {
          const overlays = this.$el?.querySelectorAll?.(".confirm-overlay");
          const overlay = overlays?.[overlays.length - 1];
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
      this.schedulePrepareRequestEditorModal();
    }
    document.addEventListener("keydown", this.handleKeyDown);
  },
  beforeDestroy() {
    this.unbindRangeSelectionListeners();
    document.removeEventListener("keydown", this.handleKeyDown);
  },
  computed: {
    isEditMode() {
      return this.mode === "edit";
    },
    headerTitle() {
      if (!this.isEditMode) return "New Request";
      return this.requestName || "Request";
    },
    primaryActionLabel() {
      return this.isEditMode ? "Update Request" : "Save Request";
    },
    canEditRequest() {
      if (!this.isEditMode) return true;
      if (this.isStaffUser) return true;
      return !this.restrictPermissions;
    },
    requestEditorModeLabel() {
      return this.requestEditorMode === "library" ? "Library" : "Sample";
    },
    recordLabelSet() {
      return this.requestEditorMode === "library"
        ? { singular: "library", plural: "libraries" }
        : { singular: "sample", plural: "samples" };
    },
    addButtonLabel() {
      return this.requestEditorMode === "library" ? "Add Libraries" : "Add Samples";
    },
    addButtonTitle() {
      return this.requestEditorMode === "library"
        ? "Add new libraries"
        : "Add new samples";
    },
    deleteButtonTitle() {
      return this.requestEditorMode === "library"
        ? "Delete selected libraries"
        : "Delete selected samples";
    },
    deleteConfirmTitle() {
      return this.requestEditorMode === "library"
        ? "Delete selected libraries?"
        : "Delete selected samples?";
    },
    deleteConfirmNoun() {
      const count = this.selectedDraftRowIds.length;
      return count === 1 ? this.recordLabelSet.singular : this.recordLabelSet.plural;
    },
    switchClearLabel() {
      return this.recordLabelSet.plural;
    },
    requestEditorColumns() {
      const normalizeOptions = (list = []) =>
        list.map((item) => ({
          value: item.id ?? item.value ?? item.pk ?? item.name,
          label: item.name ?? item.label ?? item.text ?? item.value ?? "",
          type: item.type,
          library_protocol: item.library_protocol
        }));

      const getInstance = () => this;
      const onSelectionChange = (table) => this.syncSelectedDraftRows(table);
      const applyReadOnly = (columns = []) =>
        columns.map((column) => {
          const next = { ...column };
          if (Array.isArray(next.columns)) {
            next.columns = applyReadOnly(next.columns);
          }
          if (next.field === "selected") {
            next.cellClick = null;
            next.contextMenu = () => [];
            next.formatter = (cell) => {
              const rowData = cell?.getRow?.().getData?.() || {};
              const checked = rowData.selected ? "checked" : "";
              return `<input type="checkbox" title="Select" disabled ${checked} />`;
            };
          }
          next.editable = false;
          next.editor = false;
          return next;
        });

      const libraryEditors = {
        protocols: normalizeOptions(this.protocolsList),
        analysisTypes: normalizeOptions(this.analysisTypesList),
        measuringUnits: this.libraryMeasuringUnits,
        readLengths: normalizeOptions(this.readLengthsList),
        indexTypes: normalizeOptions(this.indexTypesList),
        organisms: normalizeOptions(this.organismsList),
        getIndexReadsCount: (row) => this.getIndexReadsCount(row),
        getIndexI7Options: (row) => this.getLibraryIndexI7Options(row),
        getIndexI5Options: (row) => this.getLibraryIndexI5Options(row),
        showBarcode: this.isEditMode
      };

      const sampleEditors = {
        protocols: normalizeOptions(this.protocolsList),
        analysisTypes: normalizeOptions(this.analysisTypesList),
        measuringUnits: this.sampleMeasuringUnits,
        readLengths: normalizeOptions(this.readLengthsList),
        organisms: normalizeOptions(this.organismsList),
        nucleicAcidTypes: normalizeOptions(this.nucleicAcidTypesList),
        biosafetyLevels: this.biosafetyLevelsOptions,
        gmoOptions: this.gmoOptions,
        showBarcode: this.isEditMode
      };

      const columns =
        this.requestEditorMode === "library"
          ? getRequestEditorLibraryColumns(
            getInstance,
            libraryEditors,
            onSelectionChange
          )
          : getRequestEditorSampleColumns(
            getInstance,
            sampleEditors,
            onSelectionChange
          );

      if (!this.canEditRequest) {
        return applyReadOnly(columns);
      }

      return columns;
    },
    requestEditorDraftTableOptions() {
      const vm = this;
      const getPlaceholder = () =>
        "Use the + button to create libraries/samples.";

      const handleSelection = () => this.syncSelectedDraftRows();

      return {
        index: "tempId",
        placeholder: getPlaceholder(),
        selectable: vm.canEditRequest,
        layout: "fitColumns",
        persistenceMode: false,
        showPasteErrorRowNumber: true,
        editTriggerEvent: vm.canEditRequest ? "dblclick" : "manual",
        clipboard: vm.canEditRequest,
        rowFormatter: (row) => vm.applyRowStyling(row),
        rowSelectionChanged: () => handleSelection(),
        dataChanged: () => {
          handleSelection();
          this.revalidateDraftRows();
        },
        onBatchCellValueChanged: (changes) => {
          this.handleDraftBatchChanges(changes);
        },
        handlePasteApplied: (rows) => vm.handlePasteApplied(rows),
        handleDeleteApplied: () => {
          const table = this.$refs.requestEditorDraftTableRef?.tabulatorInstance;
          const rows = table?.getRows?.() || [];
          rows.forEach((row) => row.reformat?.());
          this.revalidateDraftRows();
        },
        handleRangeCleared: (payload = []) => {
          if (!this.isEditMode || !Array.isArray(payload)) return;
          payload.forEach((entry) => {
            const rowData = entry?.rowData || {};
            const fields = entry?.fields || [];
            if (!rowData?.tempId || !rowData?.pk || !fields.length) return;
            this.markDirtyFields(rowData.tempId, fields);
          });
          this.$nextTick(() => this.revalidateDraftRows());
        },
        cellEditing: (cell) => vm.handleCellEditing(cell),
        handleCellEdited: (cell) => vm.handleCellEdited(cell),
        handleRenderComplete: () => {
          this.applyValidationStyling();
          this.bindRangeSelectionListeners();
          this.updateRangeSelectionState();
          if (this.isEditMode && this.pendingDirtyTrackingResume) {
            this.pendingDirtyTrackingResume = false;
            this.resumeDirtyTracking();
          }
        },
        fakeLoadingStart: () => this.fakeLoadingStart(),
        fakeLoadingStop: () => this.fakeLoadingStop()
      };
    },
    footerLabel() {
      if (this.isEditMode) {
        const count =
          this.editRecordsByType?.[this.requestEditorMode]?.length || 0;
        const labels =
          this.requestEditorMode === "library"
            ? { singular: "library", plural: "libraries" }
            : { singular: "sample", plural: "samples" };
        const noun = count === 1 ? labels.singular : labels.plural;
        return `${count} ${noun} in this request.`;
      }
      const count = this.validDraftCount;
      const labels =
        this.requestEditorMode === "library"
          ? { singular: "library", plural: "libraries" }
          : { singular: "sample", plural: "samples" };
      const noun = count === 1 ? labels.singular : labels.plural;
      return `${count} valid ${noun} ready for this request.`;
    }
  },
  methods: {
    getTable() {
      return this.$refs.requestEditorDraftTableRef?.tabulatorInstance || null;
    },
    triggerClipboardPaste() {
      this.$refs.requestEditorDraftTableRef?.triggerClipboardPaste?.();
    },
    schedulePrepareRequestEditorModal() {
      if (this.prepareTimer) {
        clearTimeout(this.prepareTimer);
      }
      if (this.isEditMode) {
        this.isRequestLoading = true;
      }
      this.prepareTimer = setTimeout(() => {
        this.prepareTimer = null;
        this.prepareRequestEditorModal();
      }, 0);
    },
    findIndexOptionByValue(options = [], value) {
      if (value === "" || value === undefined || value === null) return null;
      const match = String(value);
      return (
        options.find((option) => String(option.value) === match) || null
      );
    },
    fieldHasValue(value) {
      if (value === null || value === undefined) return false;
      if (typeof value === "string") return value.trim() !== "";
      return value !== "";
    },
    refreshRowFormatting(row) {
      if (row?.reformat) {
        row.reformat();
        return;
      }
      const table = row?.getTable?.();
      table?.redraw?.();
    },
    refreshRowsForIndexType(typeKey) {
      const table = this.$refs.requestEditorDraftTableRef?.tabulatorInstance;
      const rows = table?.getRows?.() || [];
      rows.forEach((row) => {
        const rowData = row?.getData?.() || {};
        if (String(rowData.index_type || "") !== String(typeKey)) return;
        row?.reformat?.();
      });
    },
    handlePasteApplied(rows = []) {
      if (!this.canEditRequest) return;
      const table = this.$refs.requestEditorDraftTableRef?.tabulatorInstance;
      const list = Array.isArray(rows) ? rows : [];
      list.forEach((row) => {
        const rowRef = row?.getData ? row : table?.getRow?.(row?.tempId) || null;
        const rowData = rowRef?.getData ? rowRef.getData() : row;
        if (!rowData?.index_type || (!rowData?.index_i7 && !rowData?.index_i5)) {
          return;
        }
        const typeKey = String(rowData.index_type);
        const reads = this.getIndexReadsCount(rowData);
        if (reads >= 2) {
          const hasI7 = this.fieldHasValue(rowData.index_i7);
          const hasI5 = this.fieldHasValue(rowData.index_i5);
          const optionsReady =
            this.indexI7OptionsByType[typeKey] &&
            this.indexI5OptionsByType[typeKey] &&
            this.indexPairsByType[typeKey];

          if (optionsReady && rowRef) {
            if (hasI7) {
              this.tryAutoSelectI5(rowRef, rowData);
            } else if (hasI5) {
              this.tryAutoSelectI7(rowRef, rowData);
            }
          } else if (rowData.index_type) {
            this.fetchIndexOptionsForType(rowData.index_type, {
              row: rowRef,
              selectedI7: hasI7 ? rowData.index_i7 : null,
              selectedI5: !hasI7 && hasI5 ? rowData.index_i5 : null
            });
          }
        }
        if (rowData.index_type) {
          const hasI7 = Boolean(this.indexI7OptionsByType[typeKey]);
          const hasI5 = Boolean(this.indexI5OptionsByType[typeKey]);
          if (hasI7 && hasI5) {
            this.refreshRowsForIndexType(typeKey);
          } else {
            this.fetchIndexOptionsForType(rowData.index_type);
          }
        }
      });
      this.$nextTick(() => {
        this.revalidateDraftRows();
        this.applyValidationStyling();
      });
    },
    fakeLoadingStart() {
      if (this.fakeLoadingTimer) {
        clearTimeout(this.fakeLoadingTimer);
        this.fakeLoadingTimer = null;
      }
      this.fakeLoading = true;
    },
    fakeLoadingStop() {
      if (this.fakeLoadingTimer) {
        clearTimeout(this.fakeLoadingTimer);
      }
      this.fakeLoadingTimer = setTimeout(() => {
        this.fakeLoading = false;
        this.fakeLoadingTimer = null;
      }, 300);
    },
    hasMeasuredValueUnit(rowData) {
      const unit = rowData?.measuring_unit;
      return Boolean(unit) && unit !== "Unknown";
    },
    isLibraryFieldEditable(field, rowData) {
      if (field === "library_type") return Boolean(rowData.library_protocol);
      if (field === "index_i7") return this.getIndexReadsCount(rowData) >= 1;
      if (field === "index_i5") return this.getIndexReadsCount(rowData) >= 2;
      if (field === "measured_value") return this.hasMeasuredValueUnit(rowData);
      return true;
    },
    isSampleFieldEditable(field, rowData) {
      if (field === "library_protocol")
        return Boolean(rowData.nucleic_acid_type);
      if (field === "library_type") return Boolean(rowData.library_protocol);
      if (field === "measured_value") return this.hasMeasuredValueUnit(rowData);
      if (field === "gmo")
        return this.isGmoAllowedInputType(rowData.nucleic_acid_type);
      return true;
    },
    isFieldEditable(field, rowData) {
      if (this.requestEditorMode === "library") {
        return this.isLibraryFieldEditable(field, rowData);
      }
      return this.isSampleFieldEditable(field, rowData);
    },
    isFieldRequired(field, rowData) {
      if (field === "index_i7") {
        return this.requestEditorMode === "library"
          ? this.getIndexReadsCount(rowData) >= 1
          : false;
      }
      if (field === "index_i5") {
        return this.requestEditorMode === "library"
          ? this.getIndexReadsCount(rowData) >= 2
          : false;
      }
      if (field === "measured_value") {
        return this.hasMeasuredValueUnit(rowData);
      }
      if (field === "gmo") {
        return this.isGmoAllowedInputType(rowData.nucleic_acid_type);
      }
      return this.requestEditorMode === "library"
        ? LIBRARY_REQUIRED_FIELDS.has(field)
        : SAMPLE_REQUIRED_FIELDS.has(field);
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
    requestCloseModal() {
      if (this.saving) return;
      if (!this.hasUnsavedChanges()) {
        this.emitClose();
        return;
      }
      this.showCloseConfirm = true;
    },
    confirmCloseModal() {
      this.showCloseConfirm = false;
      this.emitClose();
    },
    cancelCloseModal() {
      this.showCloseConfirm = false;
    },
    handleCloseConfirmKeydown(event) {
      if (!this.showCloseConfirm) return;
      if (event.key === "Escape") {
        event.preventDefault();
        this.cancelCloseModal();
        return;
      }
      if (event.key === "Enter") {
        event.preventDefault();
        this.confirmCloseModal();
      }
    },
    hasUnsavedChanges() {
      const costUnitRaw = this.newRequest.cost_unit || "";
      const description = (this.newRequest.description || "").trim();
      if (this.isEditMode) {
        const hasDirtyTableEdits = Object.values(this.dirtyFieldsByRowId || {}).some(
          (fields) => fields instanceof Set ? fields.size > 0 : Boolean(fields)
        );
        if (hasDirtyTableEdits) {
          return true;
        }
        const snapshot = this.editSnapshot || {};
        const baseCostUnitRaw = snapshot.cost_unit || "";
        const costUnit =
          costUnitRaw === "" ? "" : String(costUnitRaw);
        const baseCostUnit =
          baseCostUnitRaw === "" ? "" : String(baseCostUnitRaw);
        const baseDescription = (snapshot.description || "").trim();
        const currentFileIds = (this.uploadedRequestFileIds || []).map(String);
        const baseFileIds = (snapshot.fileIds || []).map(String);
        const filesChanged =
          currentFileIds.length !== baseFileIds.length ||
          currentFileIds.some((id) => !baseFileIds.includes(id));
        return (
          costUnit !== baseCostUnit ||
          description !== baseDescription ||
          filesChanged
        );
      }
      if (costUnitRaw || description) return true;
      if (this.uploadedRequestFiles.length || this.uploadedRequestFileIds.length)
        return true;
      return this.getDraftTableRows().length > 0;
    },
    handleApplyToAllIndexPairs(rows = []) {
      if (!this.canEditRequest || !Array.isArray(rows)) return;
      rows.forEach((row) => {
        if (!row?.index_type) return;
        const rowRef = row?.getData ? row : null;
        const rowData = rowRef?.getData ? rowRef.getData() : row;
        if (!rowData) return;
        const typeKey = String(rowData.index_type);
        const reads = this.getIndexReadsCount(rowData);
        if (reads >= 2) {
          const hasI7 = this.fieldHasValue(rowData.index_i7);
          const hasI5 = this.fieldHasValue(rowData.index_i5);
          const optionsReady =
            this.indexI7OptionsByType[typeKey] &&
            this.indexI5OptionsByType[typeKey] &&
            this.indexPairsByType[typeKey];
          if (optionsReady && rowRef) {
            if (hasI7) {
              this.tryAutoSelectI5(rowRef, rowData);
            } else if (hasI5) {
              this.tryAutoSelectI7(rowRef, rowData);
            }
          } else if (rowData.index_type) {
            this.fetchIndexOptionsForType(rowData.index_type, {
              row: rowRef,
              selectedI7: hasI7 ? rowData.index_i7 : null,
              selectedI5: !hasI7 && hasI5 ? rowData.index_i5 : null
            });
          }
        }
        if (rowData.index_type) {
          const hasI7 = Boolean(this.indexI7OptionsByType[typeKey]);
          const hasI5 = Boolean(this.indexI5OptionsByType[typeKey]);
          if (hasI7 && hasI5) {
            this.refreshRowsForIndexType(typeKey);
          } else {
            this.fetchIndexOptionsForType(rowData.index_type);
          }
        }
      });
    },
    handleApplyToAllIndexPairing(cell, tableRef) {
      if (!this.canEditRequest || this.requestEditorMode !== "library") return;
      const field = cell?.getField?.();
      if (field !== "index_i7" && field !== "index_i5") return;
      const rows = tableRef?.getRows?.()?.map((row) => row.getData?.()) || [];
      this.handleApplyToAllIndexPairs(rows);
    },
    applyToAllFromCell(cell, { tableRef, tabulatorInstance } = {}) {
      if (!cell) return;
      this.fakeLoadingStart();
      const table =
        tabulatorInstance?.getTable?.() ||
        tabulatorInstance?.tabulatorInstance ||
        tabulatorInstance ||
        tableRef?.getTable?.() ||
        tableRef ||
        this.$refs.requestEditorDraftTableRef?.tabulatorInstance ||
        null;
      if (!table) {
        this.fakeLoadingStop();
        return;
      }
      applyValueToAllRows(cell, () => table, {
        blockActionsOnDisabledCells: true
      });
      this.handleApplyToAllIndexPairing(cell, table);
      this.$nextTick(() => {
        this.revalidateDraftRows();
        this.applyValidationStyling();
        this.fakeLoadingStop();
        this.$refs.requestEditorDraftTableRef?.restoreLastFocusedCell?.();
      });
    },
    handleApplyToAllFromContext(payload = {}) {
      this.applyToAllFromCell(payload?.cell, {
        tableRef: payload?.tableRef,
        tabulatorInstance: payload?.tabulatorInstance
      });
    },
    emitSaved(payload) {
      this.$emit("saved", payload);
    },
    resetState() {
      this.requestEditorMode = "library";
      this.isFormPanelCollapsed = false;
      this.requestEditorDraftRows = [];
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
      this.showDeleteConfirm = false;
      this.showCloseConfirm = false;
      this.showFileDeleteConfirm = false;
      this.pendingToggleMode = null;
      this.existingRecords = [];
      this.editSnapshot = {
        cost_unit: "",
        description: "",
        fileIds: []
      };
      this.requestName = "";
      this.restrictPermissions = false;
      this.isRequestLoading = false;
      this.requestOwnerId = null;
      this.resetDirtyTracking();
      this.editRecordsByType = {
        library: [],
        sample: []
      };
      this.editRecordTypesAvailable = {
        library: false,
        sample: false
      };
      this.pendingFileDelete = null;
      this.addRowCount = this.isEditMode ? 0 : 1;
      this.hasRangeSelection = false;
      this.unbindRangeSelectionListeners();
      if (this.$refs.requestFileInput) {
        this.$refs.requestFileInput.value = "";
      }
      this.$nextTick(() => this.applyValidationStyling());
    },
    resetDirtyTracking() {
      this.allowDirtyTracking = false;
      this.suppressNextDirtyBatch = false;
      this.pendingDirtyTrackingResume = false;
      this.dirtyFieldsByRowId = {};
      this.validationFieldsByRowId = {};
    },
    pauseDirtyTracking({ suppressNextBatch = false } = {}) {
      this.allowDirtyTracking = false;
      if (suppressNextBatch) {
        this.suppressNextDirtyBatch = true;
      }
    },
    resumeDirtyTracking() {
      this.allowDirtyTracking = true;
    },
    handleKeyDown(event) {
      if (!this.show) return;
      const key = event.key?.toLowerCase?.();
      const isCtrl = event.ctrlKey || event.metaKey;
      if (!isCtrl || key !== "x") return;
      const target = event.target;
      const isInput =
        target &&
        (target.tagName === "INPUT" ||
          target.tagName === "TEXTAREA" ||
          target.isContentEditable);
      if (isInput) return;
      if (!this.hasEditableRangeSelection || !this.canEditRequest) return;
      event.preventDefault();
      this.triggerTableCut();
    },
    async prepareRequestEditorModal() {
      if (this.isPreparingModal) return;
      this.isPreparingModal = true;
      this.resetState();
      await this.ensureModalOptionsLoaded();
      if (this.isEditMode) {
        await this.prepareEditRequestModal();
      }
      await this.fetchCostUnits();
      this.isPreparingModal = false;
    },
    async prepareEditRequestModal() {
      if (!this.requestId) {
        showNotification("Request ID is missing.", "error");
        return;
      }
      this.isRequestLoading = true;
      try {
        const meta = this.requestMeta || null;
        const fetchRequest = !meta;
        const metaFiles = Array.isArray(meta?.files) ? meta.files : [];
        const needsFileDetails =
          !metaFiles.length ||
          metaFiles.some(
            (file) =>
              !file?.path ||
              file?.size === undefined ||
              file?.size === null
          );
        const fetchFiles = needsFileDetails;

        const results = await Promise.allSettled([
          fetchRequest
            ? axiosRef.get(`${urlStringStart}/api/requests/${this.requestId}/`)
            : Promise.resolve({ data: meta }),
          fetchFiles
            ? axiosRef.get(
              `${urlStringStart}/api/requests/${this.requestId}/get_files/`
            )
            : Promise.resolve({ data: meta?.files || [] }),
          axiosRef.get(`${urlStringStart}/api/libraries/`, {
            params: { request_id: this.requestId }
          }),
          axiosRef.get(`${urlStringStart}/api/samples/`, {
            params: { request_id: this.requestId }
          })
        ]);

        const requestRes =
          results[0].status === "fulfilled" ? results[0].value : null;
        const filesRes =
          results[1].status === "fulfilled" ? results[1].value : null;
        const librariesRes =
          results[2].status === "fulfilled" ? results[2].value : null;
        const samplesRes =
          results[3].status === "fulfilled" ? results[3].value : null;

        if (!requestRes) {
          showNotification("Request details failed to load.", "error");
          return;
        }

        const requestData = requestRes?.data || {};
        this.requestName = requestData.name || "";
        this.restrictPermissions = Boolean(requestData.restrict_permissions);
        this.requestOwnerId = requestData.user || null;
        this.newRequest.cost_unit = requestData.cost_unit || "";
        this.newRequest.description = requestData.description || "";

        const libraries = Array.isArray(librariesRes?.data?.data)
          ? librariesRes.data.data
          : [];
        const samples = Array.isArray(samplesRes?.data?.data)
          ? samplesRes.data.data
          : [];

        this.editRecordsByType = {
          library: libraries,
          sample: samples
        };
        this.editRecordTypesAvailable = {
          library: libraries.length > 0,
          sample: samples.length > 0
        };
        const initialMode =
          this.editRecordTypesAvailable.library
            ? "library"
            : this.editRecordTypesAvailable.sample
              ? "sample"
              : "library";
        this.requestEditorMode = initialMode;
        this.loadEditRecordsForMode(initialMode);
        const indexTypes = [
          ...new Set(
            libraries
              .map((record) => record?.index_type)
              .filter((value) => value !== null && value !== undefined && value !== "")
              .map((value) => String(value))
          )
        ];
        await Promise.all(
          indexTypes.map((typeId) => this.fetchIndexOptionsForType(typeId))
        );
        indexTypes.forEach((typeId) => this.refreshRowsForIndexType(typeId));

        this.existingRecords = [
          ...libraries.map((record) => ({
            pk: record.pk,
            record_type: "Library",
            name: record.name,
            barcode: record.barcode
          })),
          ...samples.map((record) => ({
            pk: record.pk,
            record_type: "Sample",
            name: record.name,
            barcode: record.barcode
          }))
        ];

        const files = Array.isArray(filesRes?.data)
          ? filesRes.data
          : requestData.files || [];
        this.uploadedRequestFiles = files.map((file) => ({
          id: file.id ?? file.pk,
          name: file.name,
          size: file.size ?? null,
          path: file.path ?? file.file_path ?? ""
        }));
        this.uploadedRequestFileIds = this.uploadedRequestFiles
          .map((file) => file.id)
          .filter((id) => id !== undefined && id !== null);
        this.editSnapshot = {
          cost_unit: this.newRequest.cost_unit || "",
          description: this.newRequest.description || "",
          fileIds: [...this.uploadedRequestFileIds]
        };
      } catch (error) {
        handleError(error);
      } finally {
        this.isRequestLoading = false;
        this.requestDataReady = true;
      }
    },
    async ensureModalOptionsLoaded() {
      await Promise.all([
        this.fetchFilterOptions(),
        this.fetchIndexTypesList(),
        this.fetchNucleicAcidTypes(),
        this.fetchOrganismsList()
      ]);
    },
    loadEditRecordsForMode(mode) {
      const normalized = mode === "sample" ? "sample" : "library";
      this.pauseDirtyTracking({ suppressNextBatch: true });
      this.pendingDirtyTrackingResume = true;
      const source =
        normalized === "library"
          ? this.editRecordsByType.library
          : this.editRecordsByType.sample;
      const mapped = source.map((record) => {
        if (normalized === "library") {
          return {
            tempId: `edit-${record.pk}`,
            pk: record.pk,
            selected: false,
            record_type: "Library",
            barcode: record.barcode || "",
            barcode_original: record.barcode || "",
            name: record.name || "",
            library_protocol: record.library_protocol || null,
            library_type: record.library_type || null,
            measuring_unit: record.measuring_unit || null,
            measured_value: record.measured_value ?? null,
            mean_fragment_size: record.mean_fragment_size ?? null,
            volume: record.volume ?? null,
            read_length: record.read_length || null,
            sequencing_depth: record.sequencing_depth ?? null,
            index_type: record.index_type || null,
            index_reads: record.index_reads ?? null,
            index_i7: record.index_i7 || null,
            index_i5: record.index_i5 || null,
            organism: record.organism || null,
            comments: record.comments || ""
          };
        }
        return {
          tempId: `edit-${record.pk}`,
          pk: record.pk,
          selected: false,
          record_type: "Sample",
          barcode: record.barcode || "",
          barcode_original: record.barcode || "",
          name: record.name || "",
          nucleic_acid_type: record.nucleic_acid_type || null,
          library_protocol: record.library_protocol || null,
          library_type: record.library_type || null,
          measuring_unit: record.measuring_unit || null,
          measured_value: record.measured_value ?? null,
          volume: record.volume ?? null,
          read_length: record.read_length || null,
          sequencing_depth: record.sequencing_depth ?? null,
          organism: record.organism || null,
          comments: record.comments || "",
          biosafety_level: record.biosafety_level || null,
          gmo: record.gmo
        };
      });
      this.requestEditorDraftRows = mapped;
      this.selectedDraftRowIds = [];
      this.draftRowCounter = mapped.length;
      this.$nextTick(() => {
        this.revalidateDraftRows();
      });
    },
    persistDraftRowsToEditRecords(mode) {
      const normalized = mode === "sample" ? "sample" : "library";
      const rows = this.getDraftTableRows();
      if (normalized === "library") {
        this.editRecordsByType.library = rows;
      } else {
        this.editRecordsByType.sample = rows;
      }
    },
    triggerRequestFileUpload() {
      if (!this.canEditRequest) return;
      this.$refs.requestFileInput?.click?.();
    },
    triggerApplyToAll() {
      const table = this.$refs.requestEditorDraftTableRef?.tabulatorInstance;
      const cell = table?.getRanges?.()?.[0]?.getCells?.()?.[0]?.[0];
      this.applyToAllFromCell(cell, { tabulatorInstance: table });
    },

    triggerTableCopy() {
      const table = this.$refs.requestEditorDraftTableRef?.tabulatorInstance;
      const element = document.activeElement;
      if (element && (element.tagName === "INPUT" || element.tagName === "TEXTAREA")) {
        element.blur();
      }
      table?.copyToClipboard?.();
      this.$refs.requestEditorDraftTableRef?.restoreLastFocusedCell?.();
    },
    triggerTableCut() {
      if (!this.hasEditableRangeSelection || !this.canEditRequest) return;
      this.triggerTableCopy();
      this.triggerTableClear();
    },
    triggerTablePaste() {
      const tableComponent = this.$refs.requestEditorDraftTableRef;
      const element = document.activeElement;
      if (element && (element.tagName === "INPUT" || element.tagName === "TEXTAREA")) {
        element.blur();
      }
      tableComponent?.triggerClipboardPaste?.();
      tableComponent?.restoreLastFocusedCell?.();
    },
    triggerTableClear() {
      const table = this.$refs.requestEditorDraftTableRef?.tabulatorInstance;
      const element = document.activeElement;
      if (element && (element.tagName === "INPUT" || element.tagName === "TEXTAREA")) {
        element.blur();
      }
      const keyEvent = new KeyboardEvent("keydown", { key: "Delete", bubbles: true });
      table?.element?.dispatchEvent?.(keyEvent);
      this.$refs.requestEditorDraftTableRef?.restoreLastFocusedCell?.();
    },
    updateRangeSelectionState() {
      const table = this.$refs.requestEditorDraftTableRef?.tabulatorInstance;
      const ranges = table?.getRanges?.() || [];
      let hasSelection = false;
      let singleCell = false;
      let hasEditableCell = false;
      let singleCellEditable = false;
      if (ranges.length) {
        const cells = ranges[0]?.getCells?.() || [];
        hasSelection = cells.length > 0 && (cells[0]?.length || 0) > 0;
        singleCell = cells.length === 1 && (cells[0]?.length || 0) === 1;
        cells.forEach((row) => {
          row.forEach((cell) => {
            if (this.isEditableRangeCell(cell)) {
              hasEditableCell = true;
            }
          });
        });
        if (singleCell) {
          const cell = cells[0]?.[0] || null;
          singleCellEditable = this.isEditableRangeCell(cell);
        }
      }
      this.hasRangeSelection = hasSelection;
      this.hasEditableRangeSelection = hasSelection && hasEditableCell;
      this.isSingleCellSelected =
        hasSelection && singleCell && singleCellEditable;
    },
    isEditableRangeCell(cell) {
      if (!cell) return false;
      const field = cell.getField?.();
      if (!field || field === "selected") return false;
      const columnDef = cell.getColumn?.().getDefinition?.() || {};
      if (columnDef.editor === false) return false;
      if (typeof columnDef.editable === "function") {
        const rowData = cell.getRow?.().getData?.() || {};
        return columnDef.editable({
          getRow: () => ({ getData: () => rowData })
        });
      }
      if (typeof columnDef.editable === "boolean") {
        return columnDef.editable;
      }
      return true;
    },
    bindRangeSelectionListeners() {
      const element = document.getElementById("requestEditorDraftTable");
      if (!element || this.rangeListenersAttached) {
        return;
      }
      this.rangeSelectionHandler = () => {
        requestAnimationFrame(() => this.updateRangeSelectionState());
      };
      element.addEventListener("mouseup", this.rangeSelectionHandler, true);
      element.addEventListener("keyup", this.rangeSelectionHandler, true);
      element.addEventListener("keydown", this.rangeSelectionHandler, true);
      element.addEventListener("click", this.rangeSelectionHandler, true);
      this.rangeSelectionElement = element;
      this.rangeListenersAttached = true;
    },
    unbindRangeSelectionListeners() {
      if (!this.rangeListenersAttached || !this.rangeSelectionElement || !this.rangeSelectionHandler) {
        this.rangeListenersAttached = false;
        return;
      }
      const element = this.rangeSelectionElement;
      const handler = this.rangeSelectionHandler;
      element.removeEventListener("mouseup", handler, true);
      element.removeEventListener("keyup", handler, true);
      element.removeEventListener("keydown", handler, true);
      element.removeEventListener("click", handler, true);
      this.rangeSelectionElement = null;
      this.rangeSelectionHandler = null;
      this.rangeListenersAttached = false;
    },
    addDraftRow(count = 1) {
      if (this.isEditMode && !this.canEditRequest) return;
      const total = Number(count);
      if (!Number.isFinite(total) || total <= 0) return;
      const newRows = [];
      for (let i = 0; i < total; i += 1) {
        this.draftRowCounter += 1;
        const tempId = `draft-${Date.now()}-${this.draftRowCounter}-${i}`;
        const baseRow = {
          tempId,
          selected: false,
          name: ""
        };
        const row =
          this.requestEditorMode === "sample" ? { ...baseRow, gmo: null } : baseRow;
        newRows.push(row);
      }
      this.requestEditorDraftRows = [...this.requestEditorDraftRows, ...newRows];
      this.$nextTick(() => this.revalidateDraftRows());
      if (total > 5) {
        this.addRowCount = 0;
      }
    },
    requestDeleteSelectedDraftRows() {
      if (this.isEditMode && !this.canEditRequest) return;
      if (!this.selectedDraftRowIds.length) return;
      this.showDeleteConfirm = true;
    },
    confirmDeleteSelectedRows() {
      this.showDeleteConfirm = false;
      this.deleteSelectedDraftRows();
    },
    cancelDeleteSelectedRows() {
      this.showDeleteConfirm = false;
    },
    handleDeleteConfirmKeydown(event) {
      if (!this.showDeleteConfirm) return;
      if (event.key === "Escape") {
        event.preventDefault();
        this.cancelDeleteSelectedRows();
        return;
      }
      if (event.key === "Enter") {
        event.preventDefault();
        this.confirmDeleteSelectedRows();
      }
    },
    deleteSelectedDraftRows() {
      if (!this.selectedDraftRowIds.length) return;
      if (this.isEditMode) {
        this.deleteSelectedEditRows();
        return;
      }
      const ids = new Set(this.selectedDraftRowIds);
      this.requestEditorDraftRows = this.requestEditorDraftRows.filter(
        (row) => !ids.has(row.tempId)
      );
      this.selectedDraftRowIds = [];
      this.$nextTick(() => this.revalidateDraftRows());
    },
    handleRecordTypeSwitch(mode) {
      const normalized = mode === "sample" ? "sample" : "library";
      if (this.requestEditorMode === normalized) return;
      this.requestEditorMode = normalized;
      if (this.isEditMode) {
        this.loadEditRecordsForMode(normalized);
      } else {
        this.requestEditorDraftRows = [];
        this.selectedDraftRowIds = [];
        this.draftValidationState = {};
        this.validDraftCount = 0;
        this.draftRowCounter = 0;
        this.$nextTick(() => {
          const table = this.$refs.requestEditorDraftTableRef?.tabulatorInstance;
          table?.clearData?.();
          this.applyValidationStyling();
        });
      }
    },
    requestRecordTypeSwitch(event) {
      if (!this.canEditRequest) return;
      if (this.isEditMode) {
        const nextMode = event?.target?.checked ? "sample" : "library";
        const normalized = nextMode === "sample" ? "sample" : "library";
        const isAvailable =
          normalized === "library"
            ? this.editRecordTypesAvailable.library
            : this.editRecordTypesAvailable.sample;
        if (!isAvailable) {
          showNotification(
            `Switching library/sample mode is not available in edit mode.`,
            "warning"
          );
          if (event?.target) {
            event.target.checked = this.requestEditorMode === "sample";
          }
          return;
        }
        this.persistDraftRowsToEditRecords(this.requestEditorMode);
        this.handleRecordTypeSwitch(normalized);
        return;
      }
      const nextMode = event?.target?.checked ? "sample" : "library";
      const normalized = nextMode === "sample" ? "sample" : "library";
      if (this.requestEditorMode === normalized) return;
      if (this.requestEditorDraftRows.length > 0) {
        this.pendingToggleMode = normalized;
        this.showToggleConfirm = true;
        if (event?.target) {
          event.target.checked = this.requestEditorMode === "sample";
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
        this.$refs.requestEditorDraftTableRef?.tabulatorInstance ||
        null;
      const rows = table?.getData?.() || this.requestEditorDraftRows || [];
      const ids = rows
        .filter((row) => row?.selected)
        .map((row) => row?.tempId)
        .filter((id) => id !== undefined && id !== null);
      this.selectedDraftRowIds = ids;
    },
    handleDraftBatchChanges(batchChanges = []) {
      if (!this.isEditMode || !this.allowDirtyTracking || !Array.isArray(batchChanges)) {
        return;
      }
      if (this.suppressNextDirtyBatch) {
        this.suppressNextDirtyBatch = false;
        return;
      }
      const tableRows = this.getDraftTableRows() || [];
      const rowByPk = new Map(
        tableRows
          .filter((row) => row?.pk)
          .map((row) => [String(row.pk), row])
      );
      let hasDirtyUpdates = false;
      batchChanges.forEach((change) => {
        const rowId =
          change?.tempId ||
          rowByPk.get(String(change?.pk ?? ""))?.tempId ||
          null;
        if (!rowId) return;
        const fields = Object.keys(change || {}).filter(
          (key) => !["pk", "record_type", "tempId"].includes(key)
        );
        if (!fields.length) return;
        this.markDirtyFields(rowId, fields);
        hasDirtyUpdates = true;
      });
      if (hasDirtyUpdates) {
        this.$nextTick(() => this.revalidateDraftRows());
      }
    },
    markDirtyFields(rowId, fields = []) {
      if (!rowId) return;
      if (!this.dirtyFieldsByRowId[rowId]) {
        this.dirtyFieldsByRowId[rowId] = new Set();
      }
      const target = this.dirtyFieldsByRowId[rowId];
      fields.forEach((field) => {
        if (field) target.add(field);
      });
    },
    getValidationFieldsForRow(rowData, dirtyFields, mode) {
      const fields = new Set(dirtyFields || []);
      const normalizedMode = mode === "sample" ? "sample" : "library";
      if (normalizedMode === "library") {
        if (fields.has("library_protocol")) fields.add("library_type");
        if (fields.has("library_type")) fields.add("library_protocol");
        if (fields.has("index_type")) {
          const reads = this.getIndexReadsCount(rowData);
          if (reads >= 1) fields.add("index_i7");
          if (reads >= 2) fields.add("index_i5");
        }
        if (fields.has("index_i7") || fields.has("index_i5")) {
          fields.add("index_type");
        }
        if (fields.has("measuring_unit") || fields.has("measured_value")) {
          fields.add("measured_value");
        }
      } else {
        if (fields.has("nucleic_acid_type")) fields.add("library_protocol");
        if (fields.has("library_protocol")) {
          fields.add("library_type");
          fields.add("nucleic_acid_type");
        }
        if (fields.has("library_type")) fields.add("library_protocol");
        if (fields.has("measuring_unit") || fields.has("measured_value")) {
          fields.add("measured_value");
        }
      }
      return fields;
    },
    computeValidationState(rows = [], mode, options = {}) {
      const validations = {};
      const validationFieldsByRowId = {};
      const nameCounts = {};
      const normalizedMode = mode === "sample" ? "sample" : "library";
      const useDirtyValidation = options.useDirtyValidation === true;

      rows.forEach((row) => {
        const name = (row?.name || "").trim();
        if (!name) return;
        nameCounts[name] = (nameCounts[name] || 0) + 1;
      });

      let validCount = 0;
      rows.forEach((row, index) => {
        if (!row.tempId) {
          row.tempId = `row-${index + 1}-${Date.now()}`;
        }
        const rowId = row.tempId || `row-${index}`;
        const isNewRow = useDirtyValidation && !row.pk;
        let validationFields = null;
        if (useDirtyValidation && !isNewRow) {
          const dirtyFields = this.dirtyFieldsByRowId[rowId];
          if (!dirtyFields || dirtyFields.size === 0) {
            validations[rowId] = {};
            validationFieldsByRowId[rowId] = new Set();
            validCount += 1;
            return;
          }
          validationFields = this.getValidationFieldsForRow(
            row,
            dirtyFields,
            normalizedMode
          );
          validationFieldsByRowId[rowId] = validationFields;
        }

        const allErrors =
          normalizedMode === "library"
            ? this.validateLibraryRow(row, index, nameCounts)
            : this.validateSampleRow(row, index, nameCounts);
        let filteredErrors = allErrors;
        if (useDirtyValidation && validationFields instanceof Set) {
          filteredErrors = {};
          validationFields.forEach((field) => {
            if (allErrors[field]) {
              filteredErrors[field] = allErrors[field];
            }
          });
        }
        validations[rowId] = filteredErrors;
        if (!Object.keys(filteredErrors).length) {
          validCount += 1;
        }
      });

      return { validations, validationFieldsByRowId, validCount };
    },
    revalidateDraftRows() {
      const table = this.$refs.requestEditorDraftTableRef?.tabulatorInstance;
      const tableRows = table?.getRows?.() || [];
      const rows = tableRows.length
        ? tableRows.map((row) => row.getData())
        : this.requestEditorDraftRows || [];
      const { validations, validationFieldsByRowId, validCount } =
        this.computeValidationState(rows, this.requestEditorMode, {
          useDirtyValidation: this.isEditMode
        });
      this.draftValidationState = validations;
      if (this.isEditMode) {
        this.validationFieldsByRowId = {
          ...this.validationFieldsByRowId,
          ...validationFieldsByRowId
        };
      }
      this.validDraftCount = validCount;
      this.$nextTick(() => this.applyValidationStyling());
      const result = {
        hasErrors: validCount !== rows.length,
        rowCount: rows.length
      };
      return result;
    },
    applyCellStyling(cell) {
      const el = cell?.getElement?.();
      if (!el) return;
      el.classList.remove(
        "cell-valid",
        "cell-invalid",
        "required-empty",
        "required-filled"
      );
      el.removeAttribute("title");
      el.removeAttribute("data-tooltip-original");
      const tooltipNodes = el.querySelectorAll(
        "[data-tooltip-original],[title]"
      );
      tooltipNodes.forEach((node) => {
        if (node !== el) {
          node.removeAttribute("title");
          node.removeAttribute("data-tooltip-original");
        }
      });
      const rowData = cell.getRow?.()?.getData?.();
      const field = cell.getField?.();
      if (!rowData || !field || field === "selected") return;
      const rowId = rowData.tempId;
      const isExistingRow = this.isEditMode && rowData?.pk;
      const dirtyFields = rowId ? this.dirtyFieldsByRowId[rowId] : null;
      const hasDirtyFields =
        dirtyFields instanceof Set ? dirtyFields.size > 0 : Boolean(dirtyFields);
      const hasScope =
        this.isEditMode &&
        rowId &&
        Object.prototype.hasOwnProperty.call(
          this.validationFieldsByRowId,
          rowId
        );
      const scope =
        hasScope && rowId ? this.validationFieldsByRowId[rowId] : null;
      const shouldValidateField =
        (!hasScope || !(scope instanceof Set) || scope.has(field)) &&
        !(isExistingRow && !hasDirtyFields);
      const errors = this.draftValidationState[rowData.tempId] || {};
      const cellValue = cell.getValue?.();
      const valuePresent = this.fieldHasValue(cellValue);
      const required = this.isFieldRequired(field, rowData);
      const disabledTooltip = el.getAttribute("data-disabled-tooltip");
      const isDisabled = el.classList.contains("disable-editing");
      if (!shouldValidateField) {
        if (isDisabled && disabledTooltip) {
          el.setAttribute("data-tooltip-original", disabledTooltip);
        } else if (valuePresent) {
          el.classList.add("cell-valid");
        }
        return;
      }
      if (required) {
        el.classList.add(valuePresent ? "required-filled" : "required-empty");
      }
      if (errors[field]) {
        el.classList.add("cell-invalid");
        if (disabledTooltip) {
          el.setAttribute("data-tooltip-original", disabledTooltip);
        } else {
          el.setAttribute("data-tooltip-original", errors[field]);
        }
      } else if (isDisabled && disabledTooltip) {
        el.setAttribute("data-tooltip-original", disabledTooltip);
      } else if (valuePresent) {
        el.classList.add("cell-valid");
      }
      const hasValidationTooltip = el.getAttribute("data-tooltip-original");
      if (!hasValidationTooltip) {
        const displayText = (el.textContent || "").trim();
        if (displayText) {
          el.setAttribute("title", displayText);
        }
      }
    },
    applyRowStyling(row) {
      const rowData = row?.getData?.();
      const rowId = rowData?.tempId;
      const isExistingRow = this.isEditMode && rowData?.pk;
      const dirtyFields = rowId ? this.dirtyFieldsByRowId[rowId] : null;
      const hasDirtyFields =
        dirtyFields instanceof Set ? dirtyFields.size > 0 : Boolean(dirtyFields);
      const rowErrors = (rowId && this.draftValidationState[rowId]) || {};
      const hasErrors =
        !(isExistingRow && !hasDirtyFields) &&
        Object.keys(rowErrors).length > 0;
      const rowEl = row?.getElement?.();
      if (rowEl) {
        rowEl.classList.toggle("row-has-errors", hasErrors);
        rowEl.classList.toggle("row-all-valid", !hasErrors);
      }
      const cells = row?.getCells?.() || [];
      cells.forEach((cell) => this.applyCellStyling(cell));
    },
    applyValidationStyling() {
      const table = this.$refs.requestEditorDraftTableRef?.tabulatorInstance;
      if (!table) return;
      const rows = table.getRows?.() || [];
      rows.forEach((row) => this.applyRowStyling(row));
    },
    getDraftTableRows() {
      const table = this.$refs.requestEditorDraftTableRef?.tabulatorInstance;
      if (table?.getData) {
        return table.getData();
      }
      return this.requestEditorDraftRows;
    },
    handleCellEditing(cell) {
      if (!this.canEditRequest) return false;
      if (!cell) return true;
      const field = cell.getField?.();
      const rowData = cell.getRow?.()?.getData?.() || {};
      if (!field) return true;
      if (field === "barcode") {
        showNotification("Barcode is read-only.", "warning");
        return false;
      }

      if (field === "measured_value") {
        if (!rowData.measuring_unit) {
          showNotification("Select a measuring unit first.", "warning");
          return false;
        }
        if (rowData.measuring_unit === "Unknown") {
          showNotification(
            "Measured value auto-filled for Unknown units.",
            "warning"
          );
          return false;
        }
      }

      if (this.requestEditorMode === "library") {
        if (field === "index_i7") {
          if (this.getIndexReadsCount(rowData) < 1) {
            return false;
          }
        }
        if (field === "index_i5") {
          if (this.getIndexReadsCount(rowData) < 2) {
            return false;
          }
        }
        if (field === "library_type" && !rowData.library_protocol) {
          showNotification("Select a protocol first.", "warning");
          return false;
        }
        return true;
      }

      if (field === "library_protocol" && !rowData.nucleic_acid_type) {
        showNotification("Select an input type first.", "warning");
        return false;
      }
      if (field === "library_type" && !rowData.library_protocol) {
        showNotification("Select a protocol first.", "warning");
        return false;
      }
      if (
        field === "gmo" &&
        !this.isGmoAllowedInputType(rowData.nucleic_acid_type)
      ) {
        showNotification(
          "GMO only editable for Cell Suspension.",
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
      if (this.isEditMode && this.allowDirtyTracking && field) {
        const rowData = row.getData?.() || {};
        if (rowData?.tempId && rowData?.pk) {
          this.markDirtyFields(rowData.tempId, [field]);
        }
      }
      if (this.requestEditorMode === "library" && field) {
        this.handleLibraryCellEdited(field, row);
      } else if (this.requestEditorMode === "sample" && field) {
        this.handleSampleCellEdited(field, row);
      }
      this.revalidateDraftRows();
      const rowData = row.getData?.() || {};
      const rowErrors = this.draftValidationState[rowData.tempId] || {};
      this.applyRowStyling(row);
    },
    handleLibraryCellEdited(field, row) {
      const data = { ...row.getData() };
      if (field === "index_type") {
        const typeId = data.index_type;
        data.index_i7 = "";
        data.index_i5 = "";
        row.update(data);
        this.refreshRowFormatting(row);
        if (typeId) {
          this.fetchIndexOptionsForType(typeId);
        }
        return;
      }
      if (field === "library_protocol") {
        data.library_type = "";
        row.update(data);
        this.refreshRowFormatting(row);
        return;
      }
      if (field === "measuring_unit") {
        this.applyMeasuringUnitSideEffects(data);
        row.update(data);
        this.refreshRowFormatting(row);
        return;
      }
      if (field === "measured_value") {
        if (data.measuring_unit === "Unknown") {
          data.measured_value = -1;
          row.update(data);
        }
        return;
      }
      if (field === "index_i7") {
        const reads = this.getIndexReadsCount(data);
        if (reads >= 2) {
          const matched = this.tryAutoSelectI5(row, data);
          if (!matched && data.index_type) {
            this.fetchIndexOptionsForType(data.index_type, {
              row,
              selectedI7: data.index_i7
            });
          }
        }
      }
      if (field === "index_i5") {
        const reads = this.getIndexReadsCount(data);
        if (reads >= 2) {
          const matched = this.tryAutoSelectI7(row, data);
          if (!matched && data.index_type) {
            this.fetchIndexOptionsForType(data.index_type, {
              row,
              selectedI5: data.index_i5
            });
          }
        }
      }
    },
    handleSampleCellEdited(field, row) {
      const data = { ...row.getData() };
      if (field === "nucleic_acid_type") {
        data.library_protocol = "";
        data.library_type = "";
        data.gmo = null;
        row.update(data);
        this.refreshRowFormatting(row);
        return;
      }
      if (field === "library_protocol") {
        data.library_type = "";
        row.update(data);
        this.refreshRowFormatting(row);
        return;
      }
      if (field === "measuring_unit") {
        this.applyMeasuringUnitSideEffects(data);
        row.update(data);
        this.refreshRowFormatting(row);
        return;
      }
      if (field === "measured_value") {
        if (data.measuring_unit === "Unknown") {
          data.measured_value = -1;
          row.update(data);
        }
      }
    },
    getIndexReadsCount(rowData = {}) {
      const typeId = rowData?.index_type;
      if (!typeId) return 0;
      const typeKey = String(typeId);
      const match = this.indexTypesList.find((item) => {
        const key =
          item?.id ?? item?.value ?? item?.pk ?? item?.name ?? item?.label;
        return String(key) === typeKey;
      });
      const maxReads = Number(match?.index_reads);
      if (!Number.isFinite(maxReads) || maxReads < 0) return 0;
      return maxReads;
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
    async fetchIndexOptionsForType(typeId, autoSelect = null) {
      if (!typeId) return;
      const key = String(typeId);
      if (
        this.indexOptionsLoading[key] ||
        (this.indexI7OptionsByType[key] &&
          this.indexI5OptionsByType[key] &&
          this.indexPairsByType[key])
      ) {
        return;
      }
      this.indexOptionsLoading = { ...this.indexOptionsLoading, [key]: true };
      try {
        const [i7Res, i5Res, pairsRes] = await Promise.all([
          axiosRef.get(`${urlStringStart}/api/indices/i7/`, {
            params: { index_type_id: key }
          }),
          axiosRef.get(`${urlStringStart}/api/indices/i5/`, {
            params: { index_type_id: key }
          }),
          axiosRef.get(`${urlStringStart}/api/indices/pairs/`, {
            params: { index_type_id: key }
          })
        ]);
        const formatOptions = (response) => {
          const list = response?.data?.data || response?.data || [];
          return list.map((item) => ({
            value: item.index ?? item.value ?? item.id ?? item.name ?? "",
            label: item.name ?? item.index ?? item.index_id ?? "",
            index_id: item.index_id ?? "",
            index: item.index ?? ""
          }));
        };
        const i7Options = formatOptions(i7Res).sort((a, b) =>
          String(a.label || "").localeCompare(String(b.label || ""), undefined, {
            sensitivity: "base"
          })
        );
        const i5Options = formatOptions(i5Res).sort((a, b) =>
          String(a.label || "").localeCompare(String(b.label || ""), undefined, {
            sensitivity: "base"
          })
        );
        const pairsList = pairsRes?.data?.data || pairsRes?.data || [];
        const pairsMap = {};
        pairsList.forEach((pair) => {
          const i7Id = pair?.index1_id || "";
          const i5Id = pair?.index2_id || "";
          if (i7Id && i5Id) {
            pairsMap[i7Id] = i5Id;
          }
        });
        this.indexI7OptionsByType = {
          ...this.indexI7OptionsByType,
          [key]: i7Options
        };
        this.indexI5OptionsByType = {
          ...this.indexI5OptionsByType,
          [key]: i5Options
        };
        this.indexPairsByType = {
          ...this.indexPairsByType,
          [key]: pairsMap
        };
        if (autoSelect?.row && autoSelect?.selectedI7) {
          const rowData = {
            ...autoSelect.row.getData(),
            index_i7: autoSelect.selectedI7
          };
          this.tryAutoSelectI5(autoSelect.row, rowData);
        }
        if (autoSelect?.row && autoSelect?.selectedI5) {
          const rowData = {
            ...autoSelect.row.getData(),
            index_i5: autoSelect.selectedI5
          };
          this.tryAutoSelectI7(autoSelect.row, rowData);
        }
        this.$nextTick(() => {
          this.refreshRowsForIndexType(key);
          this.revalidateDraftRows();
          this.applyValidationStyling();
        });
      } catch (error) {
        handleError(error);
      } finally {
        const { [key]: _discard, ...rest } = this.indexOptionsLoading;
        this.indexOptionsLoading = rest;
      }
    },
    tryAutoSelectI5(row, rowData) {
      if (!row || !rowData) return false;
      if (!rowData.index_type || !rowData.index_i7) {
        return false;
      }
      const reads = this.getIndexReadsCount(rowData);
      if (reads < 2) return false;
      const typeKey = String(rowData.index_type);
      const i7Options = this.indexI7OptionsByType[typeKey] || [];
      const i5Options = this.indexI5OptionsByType[typeKey] || [];
      const pairsMap = this.indexPairsByType[typeKey] || null;
      if (!i7Options.length || !i5Options.length || !pairsMap) return false;
      const selectedI7 = this.findIndexOptionByValue(
        i7Options,
        rowData.index_i7
      );
      if (!selectedI7 || !selectedI7.index_id) return false;
      const i5IndexId = pairsMap[selectedI7.index_id];
      if (!i5IndexId) return false;
      const match = i5Options.find(
        (option) => option.index_id && option.index_id === i5IndexId
      );
      if (!match) return false;
      if (rowData.index_i5 === match.value) return true;
      const updated = { ...rowData, index_i5: match.value };
      row.update(updated);
      this.refreshRowFormatting(row);
      return true;
    },
    tryAutoSelectI7(row, rowData) {
      if (!row || !rowData) return false;
      if (!rowData.index_type || !rowData.index_i5) {
        return false;
      }
      const reads = this.getIndexReadsCount(rowData);
      if (reads < 2) return false;
      const typeKey = String(rowData.index_type);
      const i7Options = this.indexI7OptionsByType[typeKey] || [];
      const i5Options = this.indexI5OptionsByType[typeKey] || [];
      const pairsMap = this.indexPairsByType[typeKey] || null;
      if (!i7Options.length || !i5Options.length || !pairsMap) return false;
      const selectedI5 = this.findIndexOptionByValue(
        i5Options,
        rowData.index_i5
      );
      if (!selectedI5 || !selectedI5.index_id) return false;
      const i7IndexId = Object.keys(pairsMap).find(
        (key) => pairsMap[key] === selectedI5.index_id
      );
      if (!i7IndexId) return false;
      const match = i7Options.find(
        (option) => option.index_id && option.index_id === i7IndexId
      );
      if (!match) return false;
      if (rowData.index_i7 === match.value) return true;
      const updated = { ...rowData, index_i7: match.value };
      row.update(updated);
      this.refreshRowFormatting(row);
      return true;
    },
    redrawDraftTable() {
      const table = this.$refs.requestEditorDraftTableRef?.tabulatorInstance;
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
    isGmoAllowedInputType(value) {
      const meta = this.getNucleicAcidMeta(value);
      if (!meta || typeof meta.name !== "string") {
        return true;
      }
      const name = meta.name.trim().toLowerCase();
      if (!name) return true;
      return !(name.includes("dna") || name.includes("rna"));
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
    validateLibraryRow(row, index, nameCounts = {}) {
      const prefix = `Row ${index + 1}`;
      const errors = {};
      const isEditable = (field) => this.isLibraryFieldEditable(field, row);
      const name = (row.name || "").trim();
      if (!name) {
        errors.name = `${prefix}: Name is a required field.`;
      } else if (!/^[A-Za-z0-9_-]+$/.test(name)) {
        errors.name = `${prefix}: Name must contain only letters, numbers, _ or -.`;
      } else if ((nameCounts[name] || 0) > 1) {
        errors.name = `${prefix}: Name must be unique.`;
      }
      if (isEditable("measuring_unit") && !row.measuring_unit) {
        errors.measuring_unit = `${prefix}: Measuring Unit is a required field.`;
      }
      if (isEditable("library_protocol") && !row.library_protocol) {
        errors.library_protocol = `${prefix}: Protocol is a required field.`;
      }
      if (isEditable("library_type") && !row.library_type) {
        errors.library_type = `${prefix}: Analysis Type is a required field.`;
      }
      if (isEditable("read_length") && !row.read_length) {
        errors.read_length = `${prefix}: Read Length is a required field.`;
      }
      const depth = this.normalizeNumber(row.sequencing_depth);
      if (isEditable("sequencing_depth") && (depth === null || depth <= 0)) {
        errors.sequencing_depth = `${prefix}: Sequencing Depth must be greater than 0.`;
      }
      if (isEditable("organism") && !row.organism) {
        errors.organism = `${prefix}: Organism is a required field.`;
      }
      const volume = this.normalizeNumber(row.volume);
      if (isEditable("volume") && (volume === null || volume < 10)) {
        errors.volume = `${prefix}: Volume must be at least 10.`;
      }
      const fragmentSize = this.normalizeNumber(row.mean_fragment_size);
      if (
        isEditable("mean_fragment_size") &&
        (fragmentSize === null || fragmentSize <= 0)
      ) {
        errors.mean_fragment_size = `${prefix}: Size (bp) must be greater than 0.`;
      }
      if (isEditable("index_type") && !row.index_type) {
        errors.index_type = `${prefix}: Index Type is a required field.`;
      }
      const reads = this.getIndexReadsCount(row);
      if (isEditable("index_i7") && reads >= 1 && !row.index_i7) {
        errors.index_i7 = `${prefix}: Index I7 is required for this index type.`;
      }
      if (isEditable("index_i5") && reads >= 2 && !row.index_i5) {
        errors.index_i5 = `${prefix}: Index I5 is required for this index type.`;
      }
      if (
        isEditable("measured_value") &&
        row.measuring_unit &&
        row.measuring_unit !== "Unknown" &&
        this.normalizeNumber(row.measured_value) === null
      ) {
        errors.measured_value = `${prefix}: Value is required when a measuring unit is selected.`;
      }
      return errors;
    },
    validateSampleRow(row, index, nameCounts = {}) {
      const prefix = `Row ${index + 1}`;
      const errors = {};
      const isEditable = (field) => this.isSampleFieldEditable(field, row);
      const name = (row.name || "").trim();
      if (!name) {
        errors.name = `${prefix}: Name is a required field.`;
      } else if (!/^[A-Za-z0-9_-]+$/.test(name)) {
        errors.name = `${prefix}: Name must contain only letters, numbers, _ or -.`;
      } else if ((nameCounts[name] || 0) > 1) {
        errors.name = `${prefix}: Name must be unique.`;
      }
      if (isEditable("nucleic_acid_type") && !row.nucleic_acid_type) {
        errors.nucleic_acid_type = `${prefix}: Input Type is a required field.`;
      }
      if (isEditable("measuring_unit") && !row.measuring_unit) {
        errors.measuring_unit = `${prefix}: Measuring Unit is a required field.`;
      }
      if (isEditable("library_protocol") && !row.library_protocol) {
        errors.library_protocol = `${prefix}: Protocol is a required field.`;
      }
      if (isEditable("library_type") && !row.library_type) {
        errors.library_type = `${prefix}: Analysis Type is a required field.`;
      }
      if (isEditable("read_length") && !row.read_length) {
        errors.read_length = `${prefix}: Read Length is a required field.`;
      }
      const depth = this.normalizeNumber(row.sequencing_depth);
      if (isEditable("sequencing_depth") && (depth === null || depth <= 0)) {
        errors.sequencing_depth = `${prefix}: Sequencing Depth must be greater than 0.`;
      }
      if (isEditable("organism") && !row.organism) {
        errors.organism = `${prefix}: Organism is a required field.`;
      }
      const volume = this.normalizeNumber(row.volume);
      if (isEditable("volume") && (volume === null || volume < 10)) {
        errors.volume = `${prefix}: Volume must be at least 10.`;
      }
      if (isEditable("biosafety_level") && !row.biosafety_level) {
        errors.biosafety_level = `${prefix}: Biosafety Level is a required field.`;
      }
      if (
        isEditable("gmo") &&
        row.gmo !== true &&
        row.gmo !== false &&
        row.gmo !== "true" &&
        row.gmo !== "false"
      ) {
        errors.gmo = `${prefix}: Propagable & GMO is a required field.`;
      }
      if (
        isEditable("measured_value") &&
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
        index_reads: this.getIndexReadsCount(row),
        index_i7: row.index_i7 || null,
        index_i5: row.index_i5 || null,
        organism: this.normalizeId(row.organism),
        comments: row.comments || ""
      };
    },
    buildSamplePayload(row) {
      const gmoValue = (() => {
        const value = row.gmo;
        if (value === true || value === "true") return true;
        if (value === false || value === "false") return false;
        if (typeof value === "string") {
          const normalized = value.trim().toLowerCase();
          if (normalized === "yes") return true;
          if (normalized === "no") return false;
        }
        return null;
      })();
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
      try {
        await this.uploadRequestFiles(files);
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
    requestRemoveUploadedFile(file) {
      if (!file?.id) return;
      if (!this.canEditRequest) return;
      this.pendingFileDelete = file;
      this.showFileDeleteConfirm = true;
    },
    cancelFileDelete() {
      this.showFileDeleteConfirm = false;
      this.pendingFileDelete = null;
    },
    confirmFileDelete() {
      if (this.pendingFileDelete?.id) {
        this.removeUploadedFile(this.pendingFileDelete.id);
      }
      this.showFileDeleteConfirm = false;
      this.pendingFileDelete = null;
    },
    handleFileDeleteConfirmKeydown(event) {
      if (event.key === "Escape") {
        event.preventDefault();
        this.cancelFileDelete();
      } else if (event.key === "Enter") {
        event.preventDefault();
        this.confirmFileDelete();
      }
    },
    downloadUploadedFile(file) {
      if (!file?.path) {
        showNotification(
          "Download link unavailable for this file.",
          "warning"
        );
        return;
      }
      const path = String(file.path || "");
      const url = path.startsWith("http") ? path : `${urlStringStart}${path}`;
      axiosRef
        .get(url, { responseType: "blob" })
        .then((response) => {
          const blob = response?.data;
          if (!blob || blob.size === 0) {
            showNotification("Downloaded file is empty.", "warning");
            return;
          }
          const objectUrl = URL.createObjectURL(blob);
          const link = document.createElement("a");
          link.href = objectUrl;
          link.download = file.name || "request-file";
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          URL.revokeObjectURL(objectUrl);
        })
        .catch((error) => {
          handleError(error);
        });
    },
    handleDragOver() {
      if (!this.canEditRequest) {
        this.isDragOver = false;
        return;
      }
      this.isDragOver = true;
    },
    handleDragEnter() {
      if (!this.canEditRequest) {
        this.isDragOver = false;
        return;
      }
      this.isDragOver = true;
    },
    handleDragLeave(event) {
      if (!this.canEditRequest) {
        this.isDragOver = false;
        return;
      }
      if (!event.currentTarget.contains(event.relatedTarget)) {
        this.isDragOver = false;
      }
    },
    handleDrop(event) {
      this.isDragOver = false;
      if (!this.canEditRequest) {
        showNotification("You lack permission to upload files.", "warning");
        return;
      }
      const files = Array.from(event.dataTransfer?.files || []);
      if (!files.length) {
        showNotification("No files selected.", "warning");
        return;
      }
      this.uploadRequestFiles(files);
    },
    async uploadRequestFiles(files = []) {
      if (!files.length) {
        showNotification("No files selected.", "warning");
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
          showNotification("Files uploaded successfully.", "success");
        } else {
          showNotification("File upload failed.", "error");
        }
      } catch (error) {
        handleError(error);
      }
    },
    async fetchCostUnits() {
      const targetUserId = this.isEditMode ? this.requestOwnerId : this.userId;
      if (!targetUserId) return;
      if (!this.isEditMode) {
        if (
          this.costUnitsLoadedForUser === targetUserId &&
          this.costUnits.length
        ) {
          return;
        }
      }
      try {
        const params = {
          user_id: targetUserId
        };
        const response = await axiosRef.get(`${urlStringStart}/api/cost_units/`, {
          params
        });
        this.costUnits = (response.data || []).sort((a, b) =>
          String(a.name || "").localeCompare(String(b.name || ""), undefined, {
            sensitivity: "base"
          })
        );
        if (!this.isEditMode) {
          this.costUnitsLoadedForUser = targetUserId;
        }
      } catch (error) {
        handleError(error);
      }
    },
    saveRequest() {
      if (this.isEditMode) {
        return this.saveExistingRequest();
      }
      return this.saveNewRequest();
    },
    validateEditRecordsForSave() {
      const results = {};
      ["library", "sample"].forEach((mode) => {
        const rows =
          mode === "library"
            ? this.editRecordsByType.library || []
            : this.editRecordsByType.sample || [];
        if (!rows.length) return;
        results[mode] = {
          rows,
          ...this.computeValidationState(rows, mode, {
            useDirtyValidation: true
          })
        };
      });

      const currentMode = this.requestEditorMode === "sample" ? "sample" : "library";
      const currentResult = results[currentMode];
      if (currentResult) {
        this.draftValidationState = currentResult.validations;
        this.validationFieldsByRowId = {
          ...this.validationFieldsByRowId,
          ...currentResult.validationFieldsByRowId
        };
        this.validDraftCount = currentResult.validCount;
        this.$nextTick(() => this.applyValidationStyling());
      }

      const modeHasErrors = (mode) => {
        const result = results[mode];
        if (!result) return false;
        return result.validCount !== result.rows.length;
      };

      return {
        hasErrors: modeHasErrors("library") || modeHasErrors("sample"),
        currentModeHasErrors: modeHasErrors(currentMode),
        otherModeHasErrors:
          currentMode === "library"
            ? modeHasErrors("sample")
            : modeHasErrors("library")
      };
    },
    async saveExistingRequest() {
      if (!this.canEditRequest) {
        showNotification("You lack permission to edit requests.", "warning");
        return;
      }
      this.persistDraftRowsToEditRecords(this.requestEditorMode);
      if (this.isRequestSaving) return;
      if (!this.requestId) {
        showNotification("Request ID is missing.", "error");
        return;
      }
      const description = (this.newRequest.description || "").trim();
      const descriptionValid = !!description;
      if (!descriptionValid) {
        this.descriptionError = "Description is a required field.";
      }
      if (!this.isStaffUser && !this.newRequest.cost_unit) {
        this.costUnitError = "Cost unit is a required field.";
      }
      if (this.descriptionError || this.costUnitError) {
        showNotification("Required fields are missing.", "warning");
        return;
      }
      const totalRecords =
        (this.editRecordsByType.library || []).length +
        (this.editRecordsByType.sample || []).length;
      if (!totalRecords) {
        showNotification(
          "Request has no libraries or samples.",
          "warning"
        );
        return;
      }
      const validationStatus = this.validateEditRecordsForSave();
      if (validationStatus.currentModeHasErrors) {
        showNotification(
          "Resolve validation errors before updating this request.",
          "warning"
        );
        return;
      }
      if (validationStatus.otherModeHasErrors) {
        const otherModeLabel =
          this.requestEditorMode === "library" ? "Sample" : "Library";
        showNotification(
          `Resolve validation errors in ${otherModeLabel} records before updating.`,
          "warning"
        );
        return;
      }
      try {
        this.isRequestSaving = true;
        const updateType = async (mode) => {
          const endpoint = mode === "sample" ? "samples" : "libraries";
          const rows =
            mode === "sample"
              ? this.editRecordsByType.sample || []
              : this.editRecordsByType.library || [];

          const existingRows = rows.filter((row) => row.pk);
          const newRows = rows.filter((row) => !row.pk);

          if (existingRows.length) {
            const payloads = existingRows.map((row) => ({
              pk: row.pk,
              ...(mode === "sample"
                ? this.buildSamplePayload(row)
                : this.buildLibraryPayload(row))
            }));
            const formData = new FormData();
            formData.append("data", JSON.stringify(payloads));
            await axiosRef.post(`${urlStringStart}/api/${endpoint}/edit/`, formData, {
              headers: { "Content-Type": "multipart/form-data" }
            });
          }

          if (newRows.length) {
            const payloads = newRows.map((row) =>
              mode === "sample"
                ? this.buildSamplePayload(row)
                : this.buildLibraryPayload(row)
            );
            const created = await this.submitRequestEditor(endpoint, payloads);
            created.forEach((record, index) => {
              const row = newRows[index];
              if (row) {
                row.pk = record.pk;
                row.record_type = record.record_type || (mode === "sample" ? "Sample" : "Library");
                row.barcode = record.barcode;
              }
            });
          }
        };

        if (this.editRecordsByType.library?.length) {
          await updateType("library");
        }
        if (this.editRecordsByType.sample?.length) {
          await updateType("sample");
        }

        const allRecords = [
          ...(this.editRecordsByType.library || []).map((record) => ({
            pk: record.pk,
            record_type: "Library"
          })),
          ...(this.editRecordsByType.sample || []).map((record) => ({
            pk: record.pk,
            record_type: "Sample"
          }))
        ];

        const payload = {
          cost_unit: this.newRequest.cost_unit || null,
          description,
          records: allRecords,
          files: this.uploadedRequestFileIds
        };
        const formData = new FormData();
        formData.append("data", JSON.stringify(payload));
        const response = await axiosRef.post(
          `${urlStringStart}/api/requests/${this.requestId}/edit/`,
          formData,
          {
            headers: { "Content-Type": "multipart/form-data" }
          }
        );
        if (response?.data?.success) {
          if (this.notifyOnSave) {
            showNotification("Request updated successfully.", "success");
          }
          this.emitSaved({
            success: true,
            mode: "edit",
            request_id: this.requestId,
            cost_unit: this.newRequest.cost_unit || null,
            description,
            files: this.uploadedRequestFiles || [],
            fileIds: this.uploadedRequestFileIds || [],
            records: {
              library: this.editRecordsByType.library || [],
              sample: this.editRecordsByType.sample || []
            }
          });
          if (this.closeOnSave) {
            this.emitClose();
          }
        } else {
          showNotification("Request update failed.", "error");
        }
      } catch (error) {
        handleError(error);
      } finally {
        this.isRequestSaving = false;
      }
    },
    async saveNewRequest() {
      if (this.isRequestSaving) return;
      const description = (this.newRequest.description || "").trim();
      const descriptionValid = !!description;
      if (!descriptionValid) {
        this.descriptionError = "Description is a required field.";
      }
      if (!this.isStaffUser && !this.newRequest.cost_unit) {
        this.costUnitError = "Cost unit is a required field.";
      }
      if (this.descriptionError || this.costUnitError) {
        showNotification("Required fields are missing.", "warning");
        return;
      }
      const { rowCount } = this.revalidateDraftRows();
      if (!rowCount) {
        showNotification("Add at least one record before saving.", "warning");
        return;
      }
      if (this.validDraftCount !== rowCount) {
        showNotification("Resolve all validation errors before saving.", "warning");
        return;
      }
      const drafts = this.getDraftTableRows();
      const payloads =
        this.requestEditorMode === "library"
          ? drafts.map((row) => this.buildLibraryPayload(row))
          : drafts.map((row) => this.buildSamplePayload(row));
      const recordTypeLabel = this.requestEditorModeLabel;
      const payload = {
        cost_unit: this.newRequest.cost_unit || null,
        description,
        records: [],
        files: this.uploadedRequestFileIds
      };
      try {
        this.isRequestSaving = true;
        const endpoint =
          this.requestEditorMode === "library" ? "libraries" : "samples";
        const created = await this.submitRequestEditor(endpoint, payloads);
        if (!created.length) {
          const emptyLabel =
            this.requestEditorMode === "library"
              ? "No libraries were created."
              : "No samples were created.";
          showNotification(emptyLabel, "error");
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
          if (this.notifyOnSave) {
            showNotification("Request created successfully.", "success");
          }
          this.emitSaved(response.data);
          if (this.closeOnSave) {
            this.emitClose();
          }
        } else {
          showNotification("Request creation failed.", "error");
        }
      } catch (error) {
        handleError(error);
      } finally {
        this.isRequestSaving = false;
      }
    },
    async submitRequestEditor(endpoint, payloads) {
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
    async deleteSelectedEditRows() {
      const ids = new Set(this.selectedDraftRowIds);
      const rowsToDelete = this.requestEditorDraftRows.filter((row) =>
        ids.has(row.tempId)
      );
      if (!rowsToDelete.length) return;
      try {
      } catch (error) {
        handleError(error);
      } finally {
        const remaining = this.requestEditorDraftRows.filter(
          (row) => !ids.has(row.tempId)
        );
        this.requestEditorDraftRows = remaining;
        this.selectedDraftRowIds = [];
        this.persistDraftRowsToEditRecords(this.requestEditorMode);
        this.$nextTick(() => this.revalidateDraftRows());
      }
    },
    async fetchFilterOptions() {
      if (this.filterOptionsLoaded) return;
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
        this.filterOptionsLoaded = true;
      } catch (error) {
        handleError(error);
      }
    },
    async fetchIndexTypesList() {
      if (this.indexTypesLoaded) return;
      try {
        const response = await axiosRef.get(
          `${urlStringStart}/api/index_types/`
        );
        this.indexTypesList = (response.data || []).sort((a, b) =>
          a.name.localeCompare(b.name, undefined, { sensitivity: "base" })
        );
        this.indexTypesLoaded = true;
      } catch (error) {
        handleError(error);
      }
    },
    async fetchNucleicAcidTypes() {
      if (this.nucleicAcidTypesLoaded) return;
      try {
        const response = await axiosRef.get(
          `${urlStringStart}/api/nucleic_acid_types/`
        );
        this.nucleicAcidTypesList = (response.data || []).sort((a, b) =>
          a.name.localeCompare(b.name, undefined, { sensitivity: "base" })
        );
        this.nucleicAcidTypesLoaded = true;
      } catch (error) {
        handleError(error);
      }
    },
    async fetchOrganismsList() {
      if (this.organismsLoaded) return;
      try {
        const response = await axiosRef.get(`${urlStringStart}/api/organisms/`);
        this.organismsList = (response.data || []).sort((a, b) =>
          a.name.localeCompare(b.name, undefined, { sensitivity: "base" })
        );
        this.organismsLoaded = true;
      } catch (error) {
        handleError(error);
      }
    }
  }
};
</script>

<style scoped>
.request-editor-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  z-index: 999;
  animation: request-editor-fade-in 0.18s ease-out;
  overflow: hidden;
}

.request-editor-overlay.drag-over {
  border: none;
}

.request-editor-overlay.drag-over::after {
  content: "";
  position: absolute;
  inset: 0;
  background-color: #00bfff36;
  border: 2px dashed #2196f3;
  pointer-events: none;
  z-index: 2;
}

.request-editor-overlay.drag-over .request-editor-modal {
  transform: scale(1.02);
  transition: transform 0.2s ease;
}

.request-editor-modal {
  background: white;
  border-radius: 8px;
  width: calc(100% - 20px);
  height: calc(100% - 20px);
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.2);
  transform: scale(0.98);
  opacity: 0;
  animation: request-editor-pop-in 0.22s ease-out forwards;
  overflow: hidden;
  position: relative;
  z-index: 1;
}

.request-editor-loading-overlay {
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, 0.8);
  z-index: 4;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  animation: fade-in 0.15s ease-out forwards;
}

.request-editor-loading-overlay p {
  margin-top: 10px;
  margin-left: 10px;
  font-size: 15px;
  color: #555;
}

.saving-overlay {
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 5;
}

.saving-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 20px 24px;
  background: #ffffff;
  border: 1px solid #d0d0d0;
  border-radius: 10px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  font-size: 14px;
  color: #333;
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
  width: 460px;
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

.request-editor-content {
  height: 100%;
  display: grid;
  grid-template-columns: var(--left-panel-width) var(--panel-toggle-width) 1fr;
  grid-template-rows: auto 1fr auto;
  --left-panel-width: 320px;
  --panel-toggle-width: 34px;
}

.request-editor-content.collapsed {
  --left-panel-width: 0px;
}

.request-editor-header-left {
  grid-column: 1;
  grid-row: 1;
  display: flex;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid #e5e7eb;
  font-size: 20px;
  font-weight: 600;
  color: #13415b;
  overflow: hidden;
  min-width: 0;
}

.request-editor-header-left.collapsed {
  padding: 0;
  opacity: 0;
  pointer-events: none;
}

.title-with-icon {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.header-icon {
  font-size: 20px;
  color: #13415b;
}

.header-title-text {
  display: block;
  min-width: 0;
  max-width: 100%;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.request-editor-header-right {
  grid-column: 3;
  grid-row: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 16px 24px 16px 12px;
  border-bottom: 1px solid #e5e7eb;
  font-size: 20px;
  font-weight: 600;
  color: #13415b;
}

.header-actions {
  display: inline-flex;
  align-items: center;
  gap: 12px;
}

.header-table-actions {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 6px 8px;
  border: 1px solid #d0d0d0;
  border-radius: 8px;
  background: #f8fafb;
  box-shadow: inset 0 1px 0 #ffffff;
}

.header-table-actions.utility-actions {
  padding: 6px 8px;
  margin-right: auto;
  border: 1px solid #d7dee3;
  background: #f3f6f7;
  box-shadow: inset 0 1px 0 #ffffff;
  border-radius: 10px;
}

.clipboard-button {
  padding-left: 10px;
  padding-right: 10px;
}

.add-count-group {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px;
  border-radius: 10px;
  background: #eef2f3;
  border: 1px solid #d7dee3;
}

.add-count-input {
  width: 40px;
  height: 28px;
  border: 1px solid #0f766e;
  border-radius: 6px;
  padding: 2px 6px;
  font-size: 12px;
  text-align: right;

}

.add-count-input:focus {
  outline: none;
  box-shadow: 0 0 0 2px rgba(15, 118, 110, 0.2);
}

.add-count-input.input-error {
  border-color: #d14343;
}

.add-count-input.input-error:focus {
  box-shadow: 0 0 0 2px rgba(209, 67, 67, 0.2);
}

.add-count-button {
  padding-left: 10px;
  padding-right: 12px;
}

.add-count-input::-webkit-outer-spin-button,
.add-count-input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.add-count-input[type="number"] {
  -moz-appearance: textfield;
}

.header-table-actions .icon-button.text-button {
  height: 32px;
}

.header-table-actions.hidden {
  visibility: hidden;
  pointer-events: none;
}

.request-editor-header-right .popup-close-button {
  color: #13415b;
  font-size: 24px;
}

.request-editor-header-right .popup-close-button:hover {
  color: #0f5c84;
}

.request-editor-header-right .popup-close-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
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

.request-editor-body-left {
  grid-column: 1;
  grid-row: 2;
  padding: 20px 12px 20px 24px;
  overflow: hidden;
  min-width: 0;
}

.request-editor-content.collapsed .request-editor-body-left {
  padding: 0;
  pointer-events: none;
}

.request-editor-body-right {
  grid-column: 3;
  grid-row: 2;
  padding: 20px 24px 20px 12px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
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
  overflow-x: hidden;
  height: 100%;
  transition: width 0.25s ease, padding 0.25s ease, opacity 0.25s ease;
}

.request-panel-container {
  display: flex;
  align-items: stretch;
  position: relative;
  height: 100%;
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
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: clamp(280px, 45vh, 420px);
}

.files-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.files-header small {
  display: block;
  font-size: 11px;
  color: #6b7280;
}

.files-table-wrapper {
  width: 100%;
  border: 1px solid #d0d0d0;
  border-radius: 8px;
  overflow-y: auto;
  overflow-x: hidden;
  margin-top: 8px;
  flex: 1;
  min-height: 120px;
  display: flex;
  flex-direction: column;
  background: white;
}

.files-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  table-layout: fixed;
  font-size: 12px;
}

.files-table.files-table-empty {
  height: 100%;
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



.download-buttons {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px;
  border: 1px solid #d0d0d0;
  border-radius: 6px;
  background: #f6f8fa;
  width: 100%;
  min-width: 0;
}

.download-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 5px 12px;
  border: 1px solid #0f5c84;
  border-radius: 6px;
  background: #ffffff;
  color: #0f5c84;
  font-size: 11px;
  font-weight: 600;
  text-decoration: none;
  white-space: nowrap;
  transition: background 0.2s ease, color 0.2s ease, border-color 0.2s ease;
  flex: 1 1 0;
  min-width: 0;
  max-width: 100%;
  overflow: hidden;
}

.download-button:hover {
  background: #e8f2f7;
  border-color: #0a4a6a;
  color: #0a4a6a;
}

.download-button span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 100%;
}

.records-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow: hidden;
}

.records-panel.expanded {
  flex-basis: calc(100% - 34px);
}

.panel-toggle-button {
  width: var(--panel-toggle-width);
  border: none;
  background: #f6f8fa;
  color: #0f5c84;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s ease;
}

.panel-toggle-button:hover {
  background: #e2e7ea;
}

.panel-toggle-button.vertical-toggle {
  grid-column: 2;
  grid-row: 1 / span 2;
  align-self: stretch;
  border-left: 1px solid #e5e7eb;
  border-right: 1px solid #e5e7eb;
  z-index: 3;
}


.request-form-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 6px;
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

.record-type-switch {
  position: relative;
  width: 100%;
  height: 36px;
  border-radius: 8px;
  background: #e1e6ea;
  border: 1px solid #d0d0d0;
  cursor: pointer;
  padding: 0;
}

.record-type-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.record-type-switch .slider {
  position: absolute;
  inset: 0;
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
  flex: 1 1 50%;
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

.icon-button.text-button {
  width: auto;
  padding: 0 10px;
  gap: 6px;
  font-size: 12px;
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

.controls-group.view-only {
  background: #f6f8fa;
  color: #4b5563;
  font-weight: 600;
}

.request-editor-footer {
  grid-column: 1 / -1;
  grid-row: 3;
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

.footer-actions .popup-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.header-button.ghost {
  background: #0f766e;
}

@keyframes request-editor-fade-in {
  from {
    opacity: 0;
  }

  to {
    opacity: 1;
  }
}

@keyframes request-editor-pop-in {
  from {
    opacity: 0;
    transform: scale(0.98);
  }

  to {
    opacity: 1;
    transform: scale(1);
  }
}
</style>
<!--
refactor/simplify all the files
unit test all the pages

finsh request editor testing
when i do ctrl+x ctrl+c or ctrl+v or use any right click context options like apply all clear cut copy paste, or i use buttons in requesteditors for any of the list editor cells, reset the dependent cells too, currently only the cell is updated, but dependent cells are not updated, for example if i change index type, indices are not reset, or if i change library protocol, read length and analysis type are not reset.
when i do ctrl+x ctrl+c or ctrl+v or use any right click context options like apply all clear cut copy paste, or i use buttons in requesteditors for these, make sure that we focus on the current cell back, sometimes the focus is lost and i have to click on cell again (and after that i can use arrow keys, but with clicking i arrow keys dont work)
when there is an error in an error popup, focus should be on ok button, so that i can press enter to close it, instead of using mouse to click ok button in request editor
attachments shall be easier accessible. An attachment button shall show all attachments already uploaded and allow fast adding of them. Even more wonderful would be if the icon changes color if an attachment is there. This would help us in a way that we would spot immediately if user add attachments when creating the requests, instead of clicking multiple times.
compose email for users
question: i5 i7 Other Option, what to do if the index doest exist in any lists
test: name size in files appear different in Ulrike's computer (for empty table)
-->

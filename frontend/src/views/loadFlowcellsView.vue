<template>
  <div class="parent-container">
    <div v-if="loading || fakeLoading" class="loading-overlay">
      <div v-if="!fakeLoading" class="spinner"></div>
      <p v-if="!fakeLoading">
        Loading <span style="font-weight: bold">Flowcells</span>...
      </p>
    </div>

    <div class="header">
      <div class="header-logo" style="display: inline; margin-right: 10px">
        <img
          :src="iconLoadFlowcellsHeader"
          alt="Load Flowcells"
          width="42"
          height="42"
          style="display: block"
        />
      </div>
      <div class="header-title" style="display: inline">Load Flowcells</div>

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
        <div class="date-filters">
          <div class="date-filter">
            <label for="startDate">From</label>
            <input
              id="startDate"
              v-model="startDateString"
              type="date"
              :class="{ 'invalid-date': !startDateValid }"
            />
          </div>
          <div class="date-filter">
            <label for="endDate">To</label>
            <input
              id="endDate"
              v-model="endDateString"
              type="date"
              :class="{ 'invalid-date': !endDateValid }"
            />
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
        <button class="header-button" @click="handleExportClick">
          <font-awesome-icon
            icon="fa-solid fa-file-excel"
            style="color: white"
          />
          <span> Export to Excel </span>
        </button>
        <button class="header-button" @click="openLoadPopup">
          <font-awesome-icon
            icon="fa-solid fa-square-plus"
            style="color: white"
          />
          <span> Load </span>
        </button>
      </div>
    </div>

    <div class="table-container">
      <TabulatorTable
        v-if="!loading"
        :key="tableRenderKey"
        ref="tabulatorTableRef"
        :rowData="filteredFlowcellsList"
        :columnDefs="columnsList"
        :enableDefaultFilters="false"
        groupBy="flowcell_id"
        :groupStartOpen="false"
        :tableOptions="{
          ...tableOptions,
          fakeLoadingStart,
          fakeLoadingStop,
          handleCellEdited
        }"
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
                  Use export when you want to download the flowcell table to
                  Excel. You can export only the lanes you selected, or the full
                  visible result set for the current date range and search.
                </p>
                <section class="tooltip-section">
                  <div class="tooltip-section-title">Basic export choices</div>
                  <ul class="tooltip-list">
                    <li><strong>Export selected</strong> downloads only the selected lanes from one flowcell.</li>
                    <li><strong>Export all</strong> downloads the full visible lane list for the current filters.</li>
                    <li>Use the month range and search first if you want to narrow the exported dataset.</li>
                  </ul>
                </section>
                <section class="tooltip-section">
                  <div class="tooltip-section-title">How template files work</div>
                  <ol class="tooltip-list tooltip-steps">
                    <li>Start by exporting with <strong>Export without any additional sheets</strong>. This creates the base Excel file and keeps the original <strong>Parkour</strong> sheet.</li>
                    <li>Open that file in Excel and add your own extra sheets for notes, calculations, or run tracking.</li>
                    <li>Upload the edited file here as a reusable template. It will appear in the list of available templates.</li>
                    <li>Later, when you export using that template, Parkour replaces only the <strong>Parkour</strong> sheet with fresh data and keeps your extra sheets unchanged.</li>
                  </ol>
                </section>
              </div>
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
              <input
                id="flowcells-export-selected"
                v-model="exportSelection"
                type="radio"
                value="selected"
                :disabled="!hasSelectedRows"
              />
              <label
                for="flowcells-export-selected"
                :class="{ disabled: !hasSelectedRows }"
              >
                Export selected flowcell lanes
              </label>
            </div>
            <div class="export-selection-radio-option">
              <input
                id="flowcells-export-all"
                v-model="exportSelection"
                type="radio"
                value="all"
              />
              <label for="flowcells-export-all">Export all visible flowcell lanes</label>
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
                      id="flowcells-without-file"
                      v-model="selectedFile"
                      type="radio"
                      value="without-file"
                    />
                  </div>
                </div>
              </div>
              <div
                v-for="(file, index) in fetchedLoadFlowcellsTemplates"
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
                      :id="'flowcells-file-radio-' + index"
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
              for="flowcells-file-upload"
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
              id="flowcells-file-upload"
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

    <div v-if="showConfirmPopup" class="popup-overlay">
      <div class="popup-container confirmation-popup" style="width: 620px; height: 240px">
        <div class="popup-header">
          <span class="popup-title">{{ confirmPopup.title }}</span>
          <button class="popup-close-button" @click="closeConfirmPopup">
            &times;
          </button>
        </div>
        <div class="popup-body">
          <div v-html="confirmPopup.description"></div>
        </div>
        <div class="popup-footer">
          <button class="popup-button yes-button" @click="runConfirmPopupAction">
            Confirm
          </button>
          <button class="popup-button" @click="closeConfirmPopup">
            Cancel
          </button>
        </div>
      </div>
    </div>

    <div v-if="showPoolInfoPopup" class="popup-overlay">
      <div class="popup-container pool-info-popup" style="width: 720px; height: 580px">
        <div class="popup-header">
          <span class="popup-title">{{ poolInfoTitle }}</span>
          <button class="popup-close-button" @click="closePoolInfoPopup">
            &times;
          </button>
        </div>
        <div class="popup-body">
          <div v-if="poolInfoLoading" class="flowcell-inline-loading">
            Loading pool details...
          </div>
          <div v-else class="pool-info-table-wrapper">
            <table class="simple-data-table">
              <thead>
                <tr>
                  <th>Request</th>
                  <th>Type</th>
                  <th>Name</th>
                  <th>Barcode</th>
                  <th>Protocol</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in poolInfoRecords" :key="`${item.record_type}-${item.barcode}`">
                  <td>{{ item.request_name || "-" }}</td>
                  <td>{{ item.record_type || "-" }}</td>
                  <td>{{ item.name || "-" }}</td>
                  <td>{{ item.barcode || "-" }}</td>
                  <td>{{ item.protocol_name || "-" }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showLoadPopup" class="popup-overlay">
      <div class="popup-container load-flowcell-popup">
        <div class="popup-header">
          <img
            :src="iconLoadFlowcellsHeader"
            alt="Load Flowcell"
            width="42"
            height="42"
            style="display: block"
          />
          <span class="popup-title">Load Flowcell</span>
          <div class="load-popup-header-actions">
            <span
              class="popup-info-button"
              @mouseover="showPageHelp = true"
              @mouseleave="showPageHelp = false"
            >
              ?
              <div v-if="showPageHelp" class="tooltip-box load-flowcell-help-tooltip">
                <div class="tooltip-scroll">
                  <div class="tooltip-title">Load Flowcells Guide</div>
                  <p class="tooltip-intro">
                    Use this window to create a new flowcell load by assigning pooled libraries
                    to the lanes of a selected sequencer. The load is saved only after the
                    required fields are filled and every lane has a valid pool assignment.
                  </p>
                  <section class="tooltip-section">
                    <div class="tooltip-section-title">Loading a Flowcell</div>
                    <ul class="tooltip-list">
                      <li>Start by choosing a sequencer. The sequencer defines how many lanes are available in the lane assignment area.</li>
                      <li>Enter a Flowcell ID. This is required before the new flowcell can be created.</li>
                      <li>Drag ready pools from the Available Pools panel onto the lane cards on the right.</li>
                      <li>A pool can be placed only when it still has remaining loads and its read length is compatible with the other pools already assigned to the same flowcell.</li>
                      <li>All lanes must be filled before the new flowcell can be saved.</li>
                    </ul>
                  </section>
                  <section class="tooltip-section">
                    <div class="tooltip-section-title">Available Pools</div>
                    <ul class="tooltip-list">
                      <li>Green pool cards are ready to load and can be dragged to open lanes.</li>
                      <li>Each pool shows its read length and the remaining number of times it can still be loaded.</li>
                      <li>Disabled pools cannot be placed yet, are already fully used, or do not match the current lane assignment rules.</li>
                      <li>Clicking a pool name in the main table opens a detail view of the libraries and samples currently inside that pool.</li>
                    </ul>
                  </section>
                  <section class="tooltip-section">
                    <div class="tooltip-section-title">Unload and Destroy</div>
                    <ul class="tooltip-list">
                      <li>After a flowcell has been created, it appears in the main Load Flowcells table grouped by Flowcell ID.</li>
                      <li>Use the group actions in that table to select lanes, download the sample sheet, or destroy the flowcell.</li>
                      <li>Destroying a flowcell unloads its pools, removes the flowcell from the Load Flowcells view, and makes the pools available again in Pooling.</li>
                      <li>When the destroyed flowcell was the last active sequencing load for a request, the related libraries and samples move back from sequencing status to pooled status.</li>
                    </ul>
                  </section>
                </div>
              </div>
            </span>
            <button class="popup-close-button" @click="closeLoadPopup">
              &times;
            </button>
          </div>
        </div>
        <div class="popup-body">
          <div class="load-flowcell-layout">
            <div class="load-flowcell-left">
              <div class="load-panel load-flowcell-setup-panel">
                <div class="load-panel-header">
                  <span>Flowcell Setup</span>
                </div>
                <div class="load-panel-body">
                  <div class="load-form-grid">
                    <div class="filter-item load-form-field" style="margin-bottom: 0">
                      <label>Sequencer</label>
                      <select
                        v-model="loadForm.sequencerId"
                        :class="{ 'input-error': loadSequencerError }"
                        @change="handleSequencerChange"
                      >
                        <option :value="null">Select Sequencer</option>
                        <option
                          v-for="sequencer in sequencersList"
                          :key="sequencer.id"
                          :value="sequencer.id"
                        >
                          {{ sequencer.name }}
                        </option>
                      </select>
                    </div>
                    <div class="filter-item load-form-field" style="margin-bottom: 0">
                      <label>Flowcell ID</label>
                      <input
                        v-model.trim="loadForm.flowcellId"
                        type="text"
                        placeholder="Flowcell ID"
                        :class="{ 'input-error': flowcellIdError }"
                        @input="flowcellIdError = false"
                      />
                    </div>
                  </div>
                </div>
              </div>

              <div class="load-panel load-pools-panel">
                <div class="load-panel-header">
                  <span>Available Pools</span>
                  <span class="load-panel-subtitle">
                    Ready pools can be dragged into open lanes.
                  </span>
                </div>
                <div class="load-pools-list">
                  <div v-if="!loadModalAvailablePools.length" class="load-empty-state">
                    No pools are currently available for loading.
                  </div>
                  <template v-else>
                  <div
                    v-for="pool in loadModalAvailablePools"
                    :key="pool.pk"
                    class="load-pool-row"
                    :class="{
                      ready: pool.ready,
                      disabled: !pool.ready || pool.remainingLoads <= 0,
                      dragging: draggedPoolId === pool.pk
                    }"
                    :draggable="pool.ready && pool.remainingLoads > 0"
                    @dragstart="startPoolDrag(pool)"
                    @dragend="handlePoolDragEnd"
                  >
                      <div class="load-pool-main">
                        <span class="load-pool-name">{{ pool.name }}</span>
                        <span class="load-pool-read-length">
                          {{ pool.read_length_name || "-" }}
                        </span>
                      </div>
                      <div class="load-pool-meta">
                        {{ pool.remainingLoadsLabel }}
                      </div>
                    </div>
                  </template>
                </div>
              </div>
            </div>

            <div class="load-flowcell-right">
              <div class="load-panel lane-board">
                <div class="lane-board-header">
                  <div class="lane-board-title-block">
                    <span class="lane-board-title">Assign Pools to Lanes</span>
                    <span class="lane-board-subtitle">
                      Drag a ready pool from the left side onto each lane card.
                    </span>
                  </div>
                  <span v-if="currentLoadSequencer" class="lane-board-capacity">
                    Capacity {{ currentLoadSequencer.lane_capacity }}
                  </span>
                </div>
                <div v-if="!currentLoadSequencer" class="load-empty-state">
                  Choose a sequencer first to display its lanes.
                </div>
                <div v-else class="lane-grid">
                  <div
                    v-for="laneName in loadModalLaneNames"
                    :key="laneName"
                    class="lane-drop-card"
                    :class="{
                      loaded: !!loadAssignments[laneName],
                      droppable: isLaneDropAllowed(laneName),
                      'drop-hover': hoveredLaneName === laneName && isLaneDropAllowed(laneName)
                    }"
                    @dragover.prevent="handleLaneDragOver(laneName)"
                    @drop="handleLaneDrop(laneName)"
                  >
                    <div class="lane-drop-card-title">{{ laneName }}</div>
                    <div class="lane-drop-card-content">
                      <div
                        class="lane-drop-card-pool"
                        :class="{ 'lane-drop-card-hidden': !loadAssignments[laneName] }"
                      >
                        {{ loadAssignments[laneName]?.name || "-" }}
                      </div>
                      <div
                        class="lane-drop-card-meta"
                        :class="{ 'lane-drop-card-hidden': !loadAssignments[laneName] }"
                      >
                        {{ loadAssignments[laneName]?.read_length_name || "-" }}
                      </div>
                      <div
                        class="lane-drop-placeholder"
                        :class="{
                          'lane-drop-card-hidden': !!loadAssignments[laneName],
                          'lane-drop-placeholder-empty': !loadAssignments[laneName]
                        }"
                      >
                        Drop Pool Here
                      </div>
                    </div>
                    <button
                      class="lane-remove-button"
                      :class="{ 'lane-remove-button-hidden': !loadAssignments[laneName] }"
                      :disabled="!loadAssignments[laneName]"
                      @click="unassignLane(laneName)"
                    >
                      Remove
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="popup-footer">
          <button class="popup-button yes-button" @click="saveNewFlowcell">
            Save
          </button>
          <button class="popup-button" @click="closeLoadPopup">Cancel</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="jsx">
import { saveAs } from "file-saver";
import TabulatorTable from "../components/TabulatorTableFull.vue";
import {
  showNotification,
  handleError,
  createAxiosObject,
  urlStringStartsWith,
  createExcelExportBlob,
  formatDisplayDate,
  isValidDate
} from "../utilities/utilityFunctions";
import {
  loadFlowcellsGroupHeader,
  loadFlowcellsColumnDefs,
  loadFlowcellsExportColumns
} from "../constants/loadFlowcellsConsts";
import iconLoadFlowcellsHeader from "../assets/icons/header_load_flowcells.svg";
import iconExportTemplateFile from "../assets/icons/export_template.svg";
import iconExportTemplateFileLines from "../assets/icons/export_template_lines.svg";
import iconExportDownload from "../assets/icons/export_download.svg";
import iconExportRemove from "../assets/icons/export_remove.svg";
import iconExportUpload from "../assets/icons/export_upload.svg";

const axiosRef = createAxiosObject();
const urlStringStart = urlStringStartsWith();

export default {
  name: "LoadFlowcells",
  components: {
    TabulatorTable
  },
  data() {
    const now = new Date();
    const currentDate = `${now.getFullYear()}-${String(
      now.getMonth() + 1
    ).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
    return {
      iconLoadFlowcellsHeader,
      iconExportTemplateFile,
      iconExportTemplateFileLines,
      iconExportDownload,
      iconExportRemove,
      iconExportUpload,
      loading: true,
      fakeLoading: false,
      tabulatorInstance: null,
      tableRenderKey: 0,
      flowcellsList: [],
      columnsList: [],
      searchQuery: "",
      startDateString: currentDate,
      endDateString: currentDate,
      startDateValid: true,
      endDateValid: true,
      dateChangeTimer: null,
      tableOptions: {
        index: "pk",
        placeholder: "No loaded flowcells to show.",
        groupHeader: (value, count, data) => loadFlowcellsGroupHeader(value, data)
      },
      pendingLaneChanges: {},
      pendingEditTimer: null,
      isSavingEdits: false,
      originalLaneStateByPk: {},
      showPageHelp: false,
      showExportPopup: false,
      showExportHelpTooltip: false,
      isDragOver: false,
      fetchedLoadFlowcellsTemplates: [],
      selectedFile: "without-file",
      exportSelection: "selected",
      hasSelectedRows: false,
      showConfirmPopup: false,
      confirmPopup: {
        title: "",
        description: "",
        onConfirm: null
      },
      showPoolInfoPopup: false,
      poolInfoTitle: "Pool",
      poolInfoRecords: [],
      poolInfoLoading: false,
      showLoadPopup: false,
      sequencersList: [],
      poolSizesById: {},
      availablePoolsList: [],
      draggedPoolId: null,
      hoveredLaneName: null,
      loadSequencerError: false,
      flowcellIdError: false,
      loadForm: {
        sequencerId: null,
        flowcellId: ""
      },
      loadAssignments: {}
    };
  },
  computed: {
    filteredFlowcellsList() {
      const query = String(this.searchQuery || "").trim().toLowerCase();
      if (!query) {
        return this.flowcellsList;
      }
      return this.flowcellsList.filter((row) => {
        const haystack = [
          row.flowcell_id,
          row.name,
          row.pool_name,
          row.request,
          row.read_length_name,
          row.index_i7_show,
          row.index_i5_show,
          row.sequencer_name,
          row.protocol,
          row.create_time
        ]
          .filter((value) => value !== null && value !== undefined)
          .join(" ")
          .toLowerCase();
        return haystack.includes(query);
      });
    },
    selectedRows() {
      return this.flowcellsList.filter((row) => row.selected);
    },
    currentLoadSequencer() {
      return (
        this.sequencersList.find(
          (sequencer) => sequencer.id === this.loadForm.sequencerId
        ) || null
      );
    },
    loadModalLaneNames() {
      if (!this.currentLoadSequencer) return [];
      return Array.from(
        { length: this.currentLoadSequencer.lanes },
        (_, index) => `Lane ${index + 1}`
      );
    },
    loadModalAvailablePools() {
      return this.availablePoolsList.map((pool) => {
        const assignedCount = Object.values(this.loadAssignments).filter(
          (item) => item?.pk === pool.pk
        ).length;
        const remainingLoads = Math.max(
          0,
          Number(pool.pool_size || 0) - Number(pool.loaded || 0) - assignedCount
        );
        const poolSize = this.poolSizesById[pool.pool_size_id];
        return {
          ...pool,
          remainingLoads,
          remainingLoadsLabel: poolSize
            ? `${remainingLoads}x${poolSize.size}`
            : String(remainingLoads)
        };
      });
    }
  },
  mounted() {
    this.setColumns();
    this.getFlowcells();
    this.fetchExportTemplates();
    window.handleGroupButtonClick = this.handleGroupButtonClick.bind(this);
  },
  updated() {
    this.tabulatorInstance = this.$refs.tabulatorTableRef;
  },
  watch: {
    startDateString(newVal) {
      this.handleDateChange("start", newVal);
    },
    endDateString(newVal) {
      this.handleDateChange("end", newVal);
    }
  },
  beforeDestroy() {
    if (this.pendingEditTimer) {
      clearTimeout(this.pendingEditTimer);
    }
    if (this.dateChangeTimer) {
      clearTimeout(this.dateChangeTimer);
    }
    window.handleGroupButtonClick = null;
  },
  methods: {
    formatMonthString(value) {
      if (!value) return "";
      const date = new Date(value);
      if (Number.isNaN(date.getTime())) return "";
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, "0");
      return `${year}-${month}`;
    },
    formatApiDate(value) {
      if (!value) return "";
      const date = new Date(value);
      if (Number.isNaN(date.getTime())) return "";
      return formatDisplayDate(date);
    },
    handleDateChange(type, value) {
      clearTimeout(this.dateChangeTimer);
      this[`${type}DateValid`] = isValidDate(value);
      if (!this[`${type}DateValid`]) return;

      this.dateChangeTimer = setTimeout(() => {
        if (!this.validateDateRange()) return;
        this.getFlowcells();
      }, 500);
    },
    validateDateRange() {
      const sStr = this.startDateString;
      const eStr = this.endDateString;
      if (!isValidDate(sStr) || !isValidDate(eStr)) return false;

      const sd = new Date(`${sStr}T00:00:00`);
      const ed = new Date(`${eStr}T00:00:00`);

      if (sd.getTime() > ed.getTime()) {
        showNotification("Start date must precede end date.", "warning");
        this.startDateValid = false;
        this.endDateValid = false;
        return false;
      }

      this.startDateValid = true;
      this.endDateValid = true;
      return true;
    },
    setColumns() {
      this.columnsList = loadFlowcellsColumnDefs(
        () => this.tabulatorInstance,
        {
          onToggleSelected: this.handleRowSelectionToggle,
          onPoolClick: this.openPoolInfoPopup
        }
      );
    },
    fakeLoadingStart() {
      this.fakeLoading = true;
    },
    fakeLoadingStop() {
      this.fakeLoading = false;
    },
    async getFlowcells() {
      this.loading = true;
      try {
        const response = await axiosRef.get(`${urlStringStart}/api/flowcells/`, {
          params: {
            start: this.formatMonthString(this.startDateString),
            end: this.formatMonthString(this.endDateString)
          }
        });

        this.flowcellsList = (response.data || []).map((item) => ({
          ...item,
          selected: false,
          create_time_raw: item.create_time,
          create_time: this.formatApiDate(item.create_time)
        }));
        this.tableRenderKey += 1;

        this.originalLaneStateByPk = this.flowcellsList.reduce((acc, row) => {
          acc[row.pk] = {
            loading_concentration: row.loading_concentration,
            phix: row.phix
          };
          return acc;
        }, {});
        this.pendingLaneChanges = {};
      } catch (error) {
        handleError(error);
      } finally {
        this.loading = false;
      }
    },
    toggleGroups(goToInitial) {
      if (!this.tabulatorInstance) return;
      this.tabulatorInstance.toggleGroups(goToInitial);
    },
    getSelectedRowsFromAllData() {
      return this.flowcellsList.filter((row) => row.selected);
    },
    async updateRowSelection(pk, selected) {
      const target = this.flowcellsList.find((row) => row.pk === pk);
      if (target) {
        target.selected = selected;
      }
      const table = this.tabulatorInstance?.getTable?.();
      if (table) {
        await table.updateData([{ pk, selected }]);
      }
    },
    async handleRowSelectionToggle(rowData, checked) {
      const selectedRows = this.getSelectedRowsFromAllData().filter(
        (row) => row.pk !== rowData.pk && row.selected
      );
      const selectingDifferentFlowcell =
        checked &&
        selectedRows.length > 0 &&
        selectedRows.some((row) => row.flowcell !== rowData.flowcell);

      if (selectingDifferentFlowcell) {
        showNotification(
          "You can only select lanes from the same flowcell.",
          "warning"
        );
        await this.updateRowSelection(rowData.pk, false);
        return;
      }

      await this.updateRowSelection(rowData.pk, checked);
    },
    async setGroupSelection(flowcellId, selected) {
      const groupRows = this.flowcellsList.filter(
        (row) => row.flowcell_id === flowcellId
      );
      if (selected) {
        const existingSelected = this.getSelectedRowsFromAllData();
        if (
          existingSelected.length > 0 &&
          existingSelected.some((row) => row.flowcell_id !== flowcellId)
        ) {
          showNotification(
            "You can only select lanes from the same flowcell.",
            "warning"
          );
          return;
        }
      }

      const table = this.tabulatorInstance?.getTable?.();
      const updates = groupRows.map((row) => {
        row.selected = selected;
        return { pk: row.pk, selected };
      });
      if (table && updates.length) {
        await table.updateData(updates);
      }
    },
    async handleGroupButtonClick(event, groupValue, action) {
      event?.stopPropagation?.();
      switch (action) {
        case "selectAll":
          await this.setGroupSelection(groupValue, true);
          break;
        case "deselectAll":
          await this.setGroupSelection(groupValue, false);
          break;
        case "downloadSampleSheet":
          await this.downloadSampleSheetForFlowcell(groupValue);
          break;
        case "destroyFlowcell":
          this.confirmDestroyFlowcell(groupValue);
          break;
      }
    },
    async downloadSampleSheetForFlowcell(flowcellId) {
      const flowcellRows = this.flowcellsList.filter(
        (row) => row.flowcell_id === flowcellId
      );
      if (flowcellRows.length === 0) {
        showNotification("Flowcell was not found.", "warning");
        return;
      }

      try {
        await this.downloadSampleSheetForRows(flowcellRows);
      } catch (error) {
        handleError(error);
      }
    },
    confirmDestroyFlowcell(flowcellId) {
      const flowcellRows = this.flowcellsList.filter(
        (row) => row.flowcell_id === flowcellId
      );
      const flowcellPk = flowcellRows[0]?.flowcell;
      if (!flowcellPk) {
        showNotification("Flowcell was not found.", "error");
        return;
      }

      this.confirmPopup = {
        title: "Destroy Flowcell",
        description: `Are you sure you want to destroy the flowcell <span style="font-weight: bold">'${flowcellId}'</span>? Pools on this flowcell will become available again in Pooling.`,
        onConfirm: async () => {
          try {
            await axiosRef.post(
              `${urlStringStart}/api/flowcells/${flowcellPk}/destroy_flowcell/`
            );
            showNotification("Flowcell destroyed successfully.", "success");
            this.closeConfirmPopup();
            await this.getFlowcells();
          } catch (error) {
            this.closeConfirmPopup();
            handleError(error);
          }
        }
      };
      this.showConfirmPopup = true;
    },
    closeConfirmPopup() {
      this.showConfirmPopup = false;
      this.confirmPopup = {
        title: "",
        description: "",
        onConfirm: null
      };
    },
    runConfirmPopupAction() {
      if (typeof this.confirmPopup.onConfirm === "function") {
        this.confirmPopup.onConfirm();
      }
    },
    openPoolInfoPopup(rowData) {
      this.showPoolInfoPopup = true;
      this.poolInfoTitle = rowData.pool_name || "Pool";
      this.poolInfoRecords = [];
      this.poolInfoLoading = true;
      axiosRef
        .get(`${urlStringStart}/api/pools/${rowData.pool}/`)
        .then((response) => {
          this.poolInfoRecords = response.data || [];
        })
        .catch((error) => {
          this.closePoolInfoPopup();
          handleError(error);
        })
        .finally(() => {
          this.poolInfoLoading = false;
        });
    },
    closePoolInfoPopup() {
      this.showPoolInfoPopup = false;
      this.poolInfoRecords = [];
      this.poolInfoLoading = false;
    },
    handleCellEdited(cell) {
      const rowData = cell.getRow().getData();
      const field = cell.getField();
      if (!["loading_concentration", "phix"].includes(field)) {
        return;
      }

      const pk = rowData.pk;
      const original = this.originalLaneStateByPk[pk] || {};
      const nextValue = rowData[field];
      const normalizedOriginal =
        original[field] === undefined ? null : original[field];
      const normalizedNext = nextValue === undefined ? null : nextValue;

      if (!this.pendingLaneChanges[pk]) {
        this.pendingLaneChanges[pk] = { pk };
      }

      if (normalizedOriginal === normalizedNext) {
        delete this.pendingLaneChanges[pk][field];
      } else {
        this.pendingLaneChanges[pk][field] = normalizedNext;
      }

      if (Object.keys(this.pendingLaneChanges[pk]).length === 1) {
        delete this.pendingLaneChanges[pk];
      }
      this.scheduleBatchSave();
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
      const pending = Object.values(this.pendingLaneChanges);
      if (pending.length === 0) return;

      this.pendingLaneChanges = {};
      this.isSavingEdits = true;

      try {
        await axiosRef.post(`${urlStringStart}/api/flowcells/edit/`, {
          data: JSON.stringify(pending)
        });

        pending.forEach((change) => {
          const original = this.originalLaneStateByPk[change.pk] || {};
          Object.keys(change).forEach((field) => {
            if (field !== "pk") {
              original[field] = change[field];
            }
          });
          this.originalLaneStateByPk[change.pk] = original;
        });
      } catch (error) {
        pending.forEach((change) => {
          const existing = this.pendingLaneChanges[change.pk] || { pk: change.pk };
          Object.keys(change).forEach((field) => {
            if (field !== "pk") {
              existing[field] = change[field];
            }
          });
          this.pendingLaneChanges[change.pk] = existing;
        });
        handleError(error);
      } finally {
        this.isSavingEdits = false;
        if (Object.keys(this.pendingLaneChanges).length > 0) {
          this.flushPendingEdits();
        }
      }
    },
    async downloadBlob(url, payload, fallbackFilename) {
      const response = await axiosRef.post(url, payload, {
        responseType: "blob"
      });
      saveAs(response.data, fallbackFilename);
    },
    async downloadSampleSheet() {
      const selectedRows = this.getSelectedRowsFromAllData();
      if (selectedRows.length === 0) {
        showNotification("You did not select any lanes.", "warning");
        return;
      }

      try {
        await this.downloadSampleSheetForRows(selectedRows);
      } catch (error) {
        handleError(error);
      }
    },
    async downloadSampleSheetForRows(rows) {
      const selectedRows = rows || [];
      if (selectedRows.length === 0) {
        showNotification("You did not select any lanes.", "warning");
        return;
      }

      const flowcellPk = selectedRows[0]?.flowcell;
      if (!flowcellPk) {
        showNotification("Flowcell ID was not found.", "error");
        return;
      }

      if (selectedRows.some((row) => row.flowcell !== flowcellPk)) {
        showNotification(
          "Select lanes from the same flowcell to download a sample sheet.",
          "warning"
        );
        return;
      }

      await this.downloadBlob(
        `${urlStringStart}/api/flowcells/download_sample_sheet/`,
        {
          ids: JSON.stringify(selectedRows.map((row) => row.pk)),
          flowcell_id: flowcellPk
        },
        `${selectedRows[0].flowcell_id || "flowcell"}_SampleSheet.csv`
      );
    },
    async fetchExportTemplates() {
      try {
        const response = await axiosRef.get(
          `${urlStringStart}/api/load-flowcells-templates/`
        );
        this.fetchedLoadFlowcellsTemplates = response.data;
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
            `${urlStringStart}/api/load-flowcells-templates/upload/`,
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
          `${urlStringStart}/api/load-flowcells-templates/${file.id}/download/`,
          {
            responseType: "blob"
          }
        );
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement("a");
        link.href = url;
        link.setAttribute("download", file.name || "LoadFlowcells.xlsx");
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
      } catch (error) {
        showNotification("Error downloading file: " + error, "error");
      }
    },
    async removeExportTemplate(index) {
      const file = this.fetchedLoadFlowcellsTemplates[index];
      try {
        await axiosRef.delete(
          `${urlStringStart}/api/load-flowcells-templates/${file.id}/remove/`
        );
        this.fetchedLoadFlowcellsTemplates.splice(index, 1);
        showNotification("File removed successfully.", "success");
      } catch (error) {
        showNotification("Error removing file: " + error, "error");
      } finally {
        this.selectedFile = "without-file";
      }
    },
    handleExportClick() {
      this.hasSelectedRows = this.flowcellsList.some((row) => row.selected);
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

        const exportRows =
          this.exportSelection === "selected"
            ? this.getSelectedRowsFromAllData()
            : this.filteredFlowcellsList;

        if (exportRows.length === 0) {
          showNotification("There is nothing to export.", "warning");
          return;
        }

        const sortedExportRows = [...exportRows].sort((a, b) => {
          const flowcellCompare = String(a.flowcell_id || "").localeCompare(
            String(b.flowcell_id || "")
          );
          if (flowcellCompare !== 0) return flowcellCompare;

          const getLaneNumber = (laneName) => {
            const match = String(laneName || "").match(/(\d+)/);
            return match ? parseInt(match[1], 10) : 0;
          };

          return getLaneNumber(a.name) - getLaneNumber(b.name);
        });

        const uniqueFlowcellIDs = [
          ...new Set(
            sortedExportRows.map((row) => row.flowcell_id).filter(Boolean)
          )
        ]
          .sort()
          .join("_");

        let filename = "";
        if (this.exportSelection === "selected") {
          filename = `${formattedDate}_${uniqueFlowcellIDs}_load_flowcells`;
        } else {
          filename = `${formattedDate}_load_flowcells`;
        }

        const templateDownloadUrl =
          this.selectedFile !== "without-file"
            ? `${urlStringStart}/api/load-flowcells-templates/${this.selectedFile.id}/download/`
            : null;

        const blob = await createExcelExportBlob({
          rows: sortedExportRows,
          exportColumns: loadFlowcellsExportColumns,
          axiosInstance: axiosRef,
          templateDownloadUrl
        });
        saveAs(blob, filename);
      } catch (error) {
        showNotification(
          "Error during export. Please try again.\n" + error,
          "error"
        );
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
      } else {
        this.processUploadedFile(files[0]);
      }
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
    async openLoadPopup() {
      this.showLoadPopup = true;
      this.loadSequencerError = false;
      this.flowcellIdError = false;
      this.loadForm = {
        sequencerId: null,
        flowcellId: ""
      };
      this.loadAssignments = {};
      this.draggedPoolId = null;

      try {
        const [sequencersRes, poolSizesRes, poolsRes] = await Promise.all([
          axiosRef.get(`${urlStringStart}/api/sequencers/`),
          axiosRef.get(`${urlStringStart}/api/pool_sizes/`),
          axiosRef.get(`${urlStringStart}/api/flowcells/pool_list/`)
        ]);

        this.sequencersList = sequencersRes.data || [];
        this.poolSizesById = (poolSizesRes.data || []).reduce((acc, item) => {
          acc[item.id] = item;
          return acc;
        }, {});
        this.availablePoolsList = poolsRes.data || [];
      } catch (error) {
        this.closeLoadPopup();
        handleError(error);
      }
    },
    closeLoadPopup() {
      this.showLoadPopup = false;
      this.loadSequencerError = false;
      this.flowcellIdError = false;
      this.sequencersList = [];
      this.poolSizesById = {};
      this.availablePoolsList = [];
      this.loadAssignments = {};
      this.draggedPoolId = null;
    },
    handleSequencerChange() {
      this.loadSequencerError = false;
      this.loadAssignments = {};
      this.draggedPoolId = null;
      this.hoveredLaneName = null;
    },
    startPoolDrag(pool) {
      this.draggedPoolId = pool.pk;
      this.hoveredLaneName = null;
    },
    handlePoolDragEnd() {
      this.draggedPoolId = null;
      this.hoveredLaneName = null;
    },
    unassignLane(laneName) {
      const nextAssignments = { ...this.loadAssignments };
      delete nextAssignments[laneName];
      this.loadAssignments = nextAssignments;
    },
    getDraggedPool() {
      if (!this.draggedPoolId) return null;
      return (
        this.loadModalAvailablePools.find((item) => item.pk === this.draggedPoolId) ||
        null
      );
    },
    canAssignPoolToLane(pool, laneName, notify = false) {
      if (!this.currentLoadSequencer) {
        if (notify) {
          showNotification("Please select a sequencer first.", "warning");
        }
        return false;
      }

      if (this.loadAssignments[laneName]) {
        if (notify) {
          showNotification(
            `${laneName} is already loaded. Remove the assigned pool first.`,
            "warning"
          );
        }
        return false;
      }

      if (!pool.ready) {
        if (notify) {
          showNotification("Only ready pools can be loaded on a flowcell.", "warning");
        }
        return false;
      }

      if (pool.remainingLoads <= 0) {
        if (notify) {
          showNotification("This pool is already fully assigned.", "warning");
        }
        return false;
      }

      const poolSize = this.poolSizesById[pool.pool_size_id];
      if (
        poolSize &&
        Number(poolSize.size) > Number(this.currentLoadSequencer.lane_capacity)
      ) {
        if (notify) {
          showNotification(
            `Pool with size ${poolSize.size} cannot fit on a lane with capacity ${this.currentLoadSequencer.lane_capacity}.`,
            "warning"
          );
        }
        return false;
      }

      const assignedPools = Object.values(this.loadAssignments).filter(Boolean);
      if (
        assignedPools.length > 0 &&
        assignedPools[0].read_length !== pool.read_length
      ) {
        if (notify) {
          showNotification(
            "Read Length must be the same for all pools on a flowcell.",
            "warning"
          );
        }
        return false;
      }

      return true;
    },
    isLaneDropAllowed(laneName) {
      const pool = this.getDraggedPool();
      if (!pool) return false;
      return this.canAssignPoolToLane(pool, laneName, false);
    },
    handleLaneDragOver(laneName) {
      if (this.hoveredLaneName !== laneName) {
        this.hoveredLaneName = laneName;
      }
    },
    handleLaneDrop(laneName) {
      if (!this.draggedPoolId) return;
      const pool = this.getDraggedPool();
      this.hoveredLaneName = null;
      this.draggedPoolId = null;
      if (!pool) return;
      this.assignPoolToLane(pool, laneName);
    },
    assignPoolToLane(pool, laneName) {
      if (!this.canAssignPoolToLane(pool, laneName, true)) {
        return;
      }

      this.loadAssignments = {
        ...this.loadAssignments,
        [laneName]: pool
      };
    },
    async saveNewFlowcell() {
      const flowcellIdValue = String(this.loadForm.flowcellId || "").trim();
      this.loadSequencerError = !this.loadForm.sequencerId;
      this.flowcellIdError = !flowcellIdValue;

      if (this.loadSequencerError) {
        showNotification("Sequencer is required.", "warning");
        return;
      }

      if (this.flowcellIdError) {
        showNotification("Flowcell ID is required.", "warning");
        return;
      }

      if (
        this.loadModalLaneNames.length === 0 ||
        this.loadModalLaneNames.some((laneName) => !this.loadAssignments[laneName])
      ) {
        showNotification("All lanes must be loaded.", "warning");
        return;
      }

      const payload = {
        flowcell_id: flowcellIdValue,
        sequencer: this.loadForm.sequencerId,
        lanes: this.loadModalLaneNames.map((laneName) => ({
          name: laneName,
          pool_id: this.loadAssignments[laneName].pk
        }))
      };

      try {
        await axiosRef.post(`${urlStringStart}/api/flowcells/`, {
          data: JSON.stringify(payload)
        });
        showNotification("Flowcell has been successfully loaded.", "success");
        this.closeLoadPopup();
        await this.getFlowcells();
      } catch (error) {
        handleError(error);
      }
    }
  }
};
</script>

<style scoped>
.flowcell-actions-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px 14px;
}

.secondary-action {
  background: #f6f8f9;
  color: #33515d;
  border: 1px solid #ced6da;
}

.secondary-action:hover {
  background: #eef3f3;
}

.flowcell-inline-loading {
  padding: 18px 0;
}

.pool-info-popup {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.pool-info-popup .popup-body {
  min-height: 0;
  flex: 1;
  overflow: hidden;
}

.pool-info-table-wrapper {
  height: 100%;
  overflow: auto;
}

.simple-data-table {
  width: 100%;
  border-collapse: collapse;
}

.simple-data-table th,
.simple-data-table td {
  padding: 10px 12px;
  border: 1px solid #dce3e6;
  text-align: left;
}

.simple-data-table th {
  background: #f4f8f9;
}

.load-flowcell-popup {
  width: 1040px;
  height: 760px;
  max-height: calc(100vh - 32px);
  overflow: hidden;
}

.load-flowcell-popup .popup-body {
  background: #fbfcfd;
  padding: 14px 14px;
  min-height: 0;
  overflow: hidden;
}

.load-popup-header-actions {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  margin-left: 14px;
  flex-shrink: 0;
}

.load-popup-header-actions .popup-info-button {
  margin-right: 0;
}

.load-flowcell-layout {
  display: grid;
  grid-template-columns: 0.8fr 1.3fr;
  gap: 14px;
  height: 100%;
  min-height: 0;
}

.load-flowcell-left,
.load-flowcell-right {
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.load-flowcell-left {
  overflow: hidden;
}

.load-form-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.load-form-field label {
  padding: 0 0 5px;
  margin-bottom: 0;
  border: none;
  background: transparent;
  color: #244a60;
  font-size: 12px;
  font-weight: 700;
}

.load-form-field select,
.load-form-field input[type="text"] {
  width: 100%;
  height: 38px;
  padding: 8px 10px;
  border: 1px solid #ccd9df;
  border-radius: 10px;
  background: #fff;
  color: #2d4048;
  font-size: 13px;
  box-sizing: border-box;
}

.load-form-field .input-error {
  border-color: #d14343 !important;
  background: #fff8f8;
}

.load-form-field select:focus,
.load-form-field input[type="text"]:focus {
  outline: none;
  border-color: #0b7f78;
  box-shadow: 0 0 0 3px rgba(11, 127, 120, 0.12);
}

.load-panel,
.lane-board,
.load-pools-list {
  border: 1px solid #dce3e6;
  border-radius: 14px;
  background: #fff;
  box-shadow: 0 10px 24px rgba(20, 52, 62, 0.06);
}

.load-panel,
.load-pools-panel,
.lane-board {
  min-height: 0;
}

.load-panel-header {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 10px 14px;
  border-bottom: 1px solid #e5ecef;
  font-weight: 700;
  color: #244a60;
}

.load-panel-subtitle {
  font-size: 11px;
  font-weight: 500;
  color: #5c7480;
}

.load-panel-body {
  padding: 10px 14px 12px;
}

.lane-board {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
}

.lane-board-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  padding: 10px 14px;
  border-bottom: 1px solid #e5ecef;
}

.lane-board-title-block {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.lane-board-title {
  font-weight: 700;
  color: #244a60;
}

.lane-board-subtitle {
  font-size: 11px;
  color: #5c7480;
}

.lane-board-capacity {
  padding: 5px 9px;
  border-radius: 999px;
  background: #eef6f7;
  color: #0b7f78;
  font-size: 11px;
  font-weight: 700;
}

.lane-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(132px, 1fr));
  grid-auto-rows: minmax(134px, auto);
  gap: 10px;
  padding: 12px;
  flex: 1;
  min-height: 0;
  overflow: auto;
  align-content: start;
}

.load-empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 180px;
  margin: 16px;
  padding: 18px;
  border: 2px dashed #d2dee3;
  border-radius: 12px;
  background: #f8fbfc;
  color: #637d88;
  text-align: center;
}

.lane-drop-card {
  min-height: 134px;
  padding: 14px;
  border-radius: 12px;
  border: 2px dashed #b6c7cf;
  background: #f8fbfc;
  display: flex;
  flex-direction: column;
  gap: 8px;
  transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease,
    background 0.18s ease;
}

.lane-drop-card.loaded {
  border-style: solid;
  border-color: #0b7f78;
  background: #e9f7f4;
}

.lane-drop-card.droppable:not(.loaded) {
  border-color: #51a89d;
  background: linear-gradient(180deg, #fafdfe 0%, #eff8f6 100%);
  animation: lane-drop-pulse 1.2s ease-in-out infinite;
  cursor: grabbing;
}

.lane-drop-card.drop-hover:not(.loaded) {
  transform: translateY(-2px) scale(1.01);
  border-color: #0b7f78;
  box-shadow: 0 10px 26px rgba(11, 127, 120, 0.18);
  background: linear-gradient(180deg, #ebfbf5 0%, #d7f2e6 100%);
  animation: none;
  cursor: grabbing;
}

.lane-drop-card-title {
  font-weight: 700;
  color: #294856;
}

.lane-drop-placeholder {
  color: #6c828c;
  font-size: 12px;
}

.lane-drop-card-content {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-height: 52px;
  justify-content: flex-start;
  position: relative;
}

.lane-drop-card-hidden {
  visibility: hidden;
}

.lane-drop-card-pool {
  font-weight: 700;
  color: #0b7f78;
  word-break: break-word;
  min-height: 20px;
  line-height: 20px;
}

.lane-drop-card-meta {
  color: #59737f;
  font-size: 12px;
  min-height: 18px;
  line-height: 18px;
}

.lane-drop-placeholder {
  min-height: 20px;
  line-height: 20px;
}

.lane-drop-placeholder-empty {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
}

.lane-remove-button {
  margin-top: auto;
  border: 1px solid #d4dce0;
  border-radius: 8px;
  background: white;
  padding: 8px 10px;
  cursor: pointer;
}

.lane-remove-button-hidden {
  visibility: hidden;
  pointer-events: none;
}

.lane-remove-button:hover {
  background: #f6f8f9;
}

.load-pools-panel {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
}

.load-pools-list {
  flex: 1;
  min-height: 0;
  overflow: auto;
  padding: 10px;
  border: none;
  box-shadow: none;
  background: transparent;
}

.load-pool-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 9px 12px;
  border: 1px solid #dde5e8;
  border-radius: 12px;
  margin-bottom: 8px;
  background: linear-gradient(180deg, #ffffff 0%, #f9fbfc 100%);
  cursor: grab;
  transition: transform 0.18s ease, box-shadow 0.18s ease, opacity 0.18s ease,
    background 0.18s ease;
}

.load-pool-row.ready .load-pool-name,
.load-pool-row.ready .load-pool-meta {
  color: #238049;
}

.load-pool-row.disabled {
  cursor: not-allowed;
  background: linear-gradient(180deg, #fff7f7 0%, #fcf1f1 100%);
}

.load-pool-row.disabled .load-pool-name,
.load-pool-row.disabled .load-pool-meta {
  color: #c63b32;
}

.load-pool-row.dragging {
  opacity: 0.55;
  transform: scale(0.98);
  box-shadow: 0 14px 30px rgba(11, 127, 120, 0.18);
  background: linear-gradient(180deg, #f1faf8 0%, #e4f4f0 100%);
  cursor: grabbing;
}

.load-pool-main {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.load-pool-name {
  font-weight: 700;
  word-break: break-word;
}

.load-pool-read-length,
.load-pool-meta {
  font-size: 11px;
}

.load-flowcell-help-tooltip {
  left: auto;
  right: 0;
  top: calc(100% + 12px);
  transform: none;
  width: min(420px, calc(100vw - 48px));
  max-height: min(62vh, calc(100vh - 140px));
  z-index: 30;
}

.load-flowcell-help-tooltip .tooltip-scroll {
  max-height: min(62vh, calc(100vh - 140px));
}

@keyframes lane-drop-pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(81, 168, 157, 0.16);
  }
  70% {
    box-shadow: 0 0 0 10px rgba(81, 168, 157, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(81, 168, 157, 0);
  }
}

@media (max-width: 1180px) {
  .load-flowcell-popup {
    width: 92vw;
    height: 88vh;
  }

  .load-flowcell-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 1220px) {
  .header {
    height: auto;
    min-height: 70px;
    align-items: flex-start;
    flex-wrap: wrap;
    gap: 10px 14px;
  }

  .header-title {
    flex: 1 1 100%;
    min-width: 0;
    margin-right: 0;
  }

  .sticky-actions {
    display: flex;
    flex-wrap: wrap;
    width: 100%;
    justify-content: flex-start;
    row-gap: 10px;
    max-width: 100%;
    margin-left: 0;
  }

  .search-bar {
    width: 260px;
    flex: 1 1 260px;
    max-width: 100%;
  }

  .date-filters {
    flex-wrap: wrap;
  }

  .flowcell-actions-bar {
    flex-wrap: wrap;
    row-gap: 10px;
  }

  .load-form-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 950px) {
  .header-title {
    font-size: 16px;
    flex-basis: 100%;
  }

  .search-bar {
    width: 100%;
    flex: 1 1 260px;
    min-width: 200px;
  }

  .search-bar input {
    width: 100%;
    padding-right: 25px;
  }

  .date-filters {
    display: none;
  }

  .sticky-actions {
    gap: 8px;
  }

  .flowcell-actions-bar {
    padding: 10px 12px 14px;
  }

  .flowcell-actions-bar .header-button {
    width: 100%;
    justify-content: center;
  }

  .load-flowcell-popup {
    width: 96vw;
    height: 90vh;
    max-height: calc(100vh - 20px);
  }

  .load-flowcell-popup .popup-body {
    padding: 14px 12px;
  }

  .lane-board-header {
    flex-direction: column;
    align-items: stretch;
  }

  .lane-board-capacity {
    align-self: flex-start;
  }

  .load-popup-header-actions {
    gap: 8px;
    margin-left: 10px;
  }

  .load-flowcell-help-tooltip {
    right: -6px;
    width: min(360px, calc(100vw - 28px));
    max-height: min(58vh, calc(100vh - 120px));
  }

  .load-flowcell-help-tooltip .tooltip-scroll {
    max-height: min(58vh, calc(100vh - 120px));
  }

  .lane-grid {
    grid-template-columns: 1fr;
  }
}
</style>

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
        <div class="date-filters">
          <div class="date-filter">
            <label for="startDate">From</label>
            <input
              id="startDate"
              v-model="startDateString"
              type="date"
              @change="handleDateFilterChange"
            />
          </div>
          <div class="date-filter">
            <label for="endDate">To</label>
            <input
              id="endDate"
              v-model="endDateString"
              type="date"
              @change="handleDateFilterChange"
            />
          </div>
        </div>
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
        <button class="header-button" @click="toggleGroups">
          <font-awesome-icon
            icon="fa-solid fa-layer-group"
            style="color: white"
          />
          <span> Toggle Views </span>
        </button>
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
        ref="tabulatorTableRef"
        :rowData="filteredFlowcellsList"
        :columnDefs="columnsList"
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

    <div v-if="!loading" class="flowcell-actions-bar">
      <button class="header-button secondary-action" @click="downloadBenchtopProtocol">
        Download Benchtop Protocol
      </button>
      <button class="header-button secondary-action" @click="downloadSampleSheet">
        Download Sample Sheet
      </button>
      <div style="flex: 1"></div>
      <button class="header-button secondary-action" @click="cancelPendingChanges">
        Cancel
      </button>
      <button
        class="header-button"
        :disabled="pendingLaneChangesCount === 0"
        @click="savePendingChanges"
      >
        Save
      </button>
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
      <div class="popup-container" style="width: 720px; height: 580px">
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
          <span class="popup-title">Load Flowcell</span>
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
                  Use this window to place pools onto a flowcell, review lane setup,
                  and save the full load in one step.
                </p>
                <section class="tooltip-section">
                  <div class="tooltip-section-title">Loading a flowcell</div>
                  <ul class="tooltip-list">
                    <li>Choose a sequencer and enter the Flowcell ID first.</li>
                    <li>Drag ready pools from the Available Pools panel onto the lane cards.</li>
                    <li>All lanes must be filled before the new flowcell can be saved.</li>
                  </ul>
                </section>
                <section class="tooltip-section">
                  <div class="tooltip-section-title">Available pools</div>
                  <ul class="tooltip-list">
                    <li>Green pools are ready to load.</li>
                    <li>Disabled pools cannot be placed yet or have no remaining loads.</li>
                    <li>Read length must stay compatible across the same flowcell.</li>
                  </ul>
                </section>
                <section class="tooltip-section">
                  <div class="tooltip-section-title">Unload and destroy</div>
                  <ul class="tooltip-list">
                    <li>Use the flowcell group actions in the main table to destroy a loaded flowcell.</li>
                    <li>Destroying a flowcell unloads its pools and makes them available again in Pooling.</li>
                    <li>Libraries and samples move back from sequencing to pooled status when appropriate.</li>
                  </ul>
                </section>
              </div>
            </div>
          </span>
          <button class="popup-close-button" @click="closeLoadPopup">
            &times;
          </button>
        </div>
        <div class="popup-body">
          <div class="load-flowcell-layout">
            <div class="load-flowcell-left">
              <div class="load-panel">
                <div class="load-panel-header">
                  <span>Flowcell Setup</span>
                </div>
                <div class="load-panel-body">
                  <div class="load-form-grid">
                    <div class="filter-item" style="margin-bottom: 0">
                      <label>Sequencer</label>
                      <select v-model="loadForm.sequencerId">
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
                    <div class="filter-item" style="margin-bottom: 0">
                      <label>Flowcell ID</label>
                      <input
                        v-model.trim="loadForm.flowcellId"
                        type="text"
                        placeholder="Flowcell ID"
                      />
                    </div>
                  </div>
                </div>
              </div>

              <div class="load-panel lane-board">
                <div class="lane-board-header">
                  <div class="lane-board-title-block">
                    <span class="lane-board-title">Assign Pools to Lanes</span>
                    <span class="lane-board-subtitle">
                      Drag a ready pool from the right side onto each lane card.
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
                    :class="{ loaded: !!loadAssignments[laneName] }"
                    @dragover.prevent
                    @drop="handleLaneDrop(laneName)"
                  >
                    <div class="lane-drop-card-title">{{ laneName }}</div>
                    <template v-if="loadAssignments[laneName]">
                      <div class="lane-drop-card-pool">
                        {{ loadAssignments[laneName].name }}
                      </div>
                      <div class="lane-drop-card-meta">
                        {{ loadAssignments[laneName].read_length_name || "-" }}
                      </div>
                      <button
                        class="lane-remove-button"
                        @click="unassignLane(laneName)"
                      >
                        Remove
                      </button>
                    </template>
                    <template v-else>
                      <div class="lane-drop-placeholder">Drop Pool Here</div>
                    </template>
                  </div>
                </div>
              </div>
            </div>

            <div class="load-flowcell-right">
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
                        disabled: !pool.ready || pool.remainingLoads <= 0
                      }"
                      :draggable="pool.ready && pool.remainingLoads > 0"
                      @dragstart="startPoolDrag(pool)"
                      @dragend="draggedPoolId = null"
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
  formatDisplayDate
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
      flowcellsList: [],
      columnsList: [],
      searchQuery: "",
      startDateString: currentDate,
      endDateString: currentDate,
      tableOptions: {
        index: "pk",
        placeholder: "No loaded flowcells to show.",
        groupHeader: (value, count, data) => loadFlowcellsGroupHeader(value, data)
      },
      pendingLaneChanges: {},
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
    pendingLaneChangesCount() {
      return Object.keys(this.pendingLaneChanges).length;
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
  beforeDestroy() {
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
    handleDateFilterChange() {
      if (!this.startDateString || !this.endDateString) return;
      if (this.startDateString > this.endDateString) {
        showNotification("'From' date cannot be after 'To' date.", "warning");
        return;
      }
      this.getFlowcells();
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
        case "destroyFlowcell":
          this.confirmDestroyFlowcell(groupValue);
          break;
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
    },
    async savePendingChanges() {
      const payloadRows = Object.values(this.pendingLaneChanges);
      if (payloadRows.length === 0) {
        showNotification("There are no pending changes to save.", "info");
        return;
      }

      this.fakeLoadingStart();
      try {
        await axiosRef.post(`${urlStringStart}/api/flowcells/edit/`, {
          data: JSON.stringify(payloadRows)
        });
        showNotification("Flowcell lanes updated successfully.", "success");
        await this.getFlowcells();
      } catch (error) {
        handleError(error);
      } finally {
        this.fakeLoadingStop();
      }
    },
    async cancelPendingChanges() {
      await this.getFlowcells();
      showNotification("Unsaved lane changes were discarded.", "info");
    },
    async downloadBlob(url, payload, fallbackFilename) {
      const response = await axiosRef.post(url, payload, {
        responseType: "blob"
      });
      saveAs(response.data, fallbackFilename);
    },
    async downloadBenchtopProtocol() {
      const selectedRows = this.getSelectedRowsFromAllData();
      if (selectedRows.length === 0) {
        showNotification("You did not select any lanes.", "warning");
        return;
      }

      try {
        await this.downloadBlob(
          `${urlStringStart}/api/flowcells/download_benchtop_protocol/`,
          {
            ids: JSON.stringify(selectedRows.map((row) => row.pk))
          },
          "FC_Loading_Benchtop_Protocol.xls"
        );
      } catch (error) {
        handleError(error);
      }
    },
    async downloadSampleSheet() {
      const selectedRows = this.getSelectedRowsFromAllData();
      if (selectedRows.length === 0) {
        showNotification("You did not select any lanes.", "warning");
        return;
      }

      const flowcellPk = selectedRows[0]?.flowcell;
      if (!flowcellPk) {
        showNotification("Flowcell ID was not found.", "error");
        return;
      }

      try {
        await this.downloadBlob(
          `${urlStringStart}/api/flowcells/download_sample_sheet/`,
          {
            ids: JSON.stringify(selectedRows.map((row) => row.pk)),
            flowcell_id: flowcellPk
          },
          `${selectedRows[0].flowcell_id || "flowcell"}_SampleSheet.csv`
        );
      } catch (error) {
        handleError(error);
      }
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
        const exportRows =
          this.exportSelection === "selected"
            ? this.getSelectedRowsFromAllData()
            : this.filteredFlowcellsList;

        if (exportRows.length === 0) {
          showNotification("There is nothing to export.", "warning");
          return;
        }

        const templateDownloadUrl =
          this.selectedFile !== "without-file"
            ? `${urlStringStart}/api/load-flowcells-templates/${this.selectedFile.id}/download/`
            : null;

        const blob = await createExcelExportBlob({
          rows: exportRows,
          exportColumns: loadFlowcellsExportColumns,
          axiosInstance: axiosRef,
          templateDownloadUrl
        });
        saveAs(blob, "Load_Flowcells.xlsx");
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
      this.sequencersList = [];
      this.poolSizesById = {};
      this.availablePoolsList = [];
      this.loadAssignments = {};
      this.draggedPoolId = null;
    },
    startPoolDrag(pool) {
      this.draggedPoolId = pool.pk;
    },
    unassignLane(laneName) {
      const nextAssignments = { ...this.loadAssignments };
      delete nextAssignments[laneName];
      this.loadAssignments = nextAssignments;
    },
    handleLaneDrop(laneName) {
      if (!this.draggedPoolId) return;
      const pool = this.loadModalAvailablePools.find(
        (item) => item.pk === this.draggedPoolId
      );
      this.draggedPoolId = null;
      if (!pool) return;
      this.assignPoolToLane(pool, laneName);
    },
    assignPoolToLane(pool, laneName) {
      if (!this.currentLoadSequencer) {
        showNotification("Please select a sequencer first.", "warning");
        return;
      }

      if (this.loadAssignments[laneName]) {
        showNotification(
          `${laneName} is already loaded. Remove the assigned pool first.`,
          "warning"
        );
        return;
      }

      if (!pool.ready) {
        showNotification("Only ready pools can be loaded on a flowcell.", "warning");
        return;
      }

      if (pool.remainingLoads <= 0) {
        showNotification("This pool is already fully assigned.", "warning");
        return;
      }

      const poolSize = this.poolSizesById[pool.pool_size_id];
      if (
        poolSize &&
        Number(poolSize.size) > Number(this.currentLoadSequencer.lane_capacity)
      ) {
        showNotification(
          `Pool with size ${poolSize.size} cannot fit on a lane with capacity ${this.currentLoadSequencer.lane_capacity}.`,
          "warning"
        );
        return;
      }

      const assignedPools = Object.values(this.loadAssignments).filter(Boolean);
      if (
        assignedPools.length > 0 &&
        assignedPools[0].read_length !== pool.read_length
      ) {
        showNotification(
          "Read Length must be the same for all pools on a flowcell.",
          "warning"
        );
        return;
      }

      this.loadAssignments = {
        ...this.loadAssignments,
        [laneName]: pool
      };
    },
    async saveNewFlowcell() {
      if (!this.loadForm.sequencerId || !this.loadForm.flowcellId) {
        showNotification("Sequencer and Flowcell ID are required.", "warning");
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
        flowcell_id: this.loadForm.flowcellId,
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
}

.load-flowcell-layout {
  display: grid;
  grid-template-columns: 1.15fr 0.85fr;
  gap: 18px;
  height: 100%;
}

.load-flowcell-left,
.load-flowcell-right {
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.load-form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.load-panel,
.lane-board,
.load-pools-list {
  border: 1px solid #dce3e6;
  border-radius: 14px;
  background: #fff;
}

.load-panel-header {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 14px 16px;
  border-bottom: 1px solid #e5ecef;
  font-weight: 700;
  color: #244a60;
}

.load-panel-subtitle {
  font-size: 12px;
  font-weight: 500;
  color: #5c7480;
}

.load-panel-body {
  padding: 14px 16px 16px;
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
  padding: 14px 16px;
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
  font-size: 12px;
  color: #5c7480;
}

.lane-board-capacity {
  padding: 6px 10px;
  border-radius: 999px;
  background: #eef6f7;
  color: #0b7f78;
  font-size: 12px;
  font-weight: 700;
}

.lane-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(132px, 1fr));
  gap: 12px;
  padding: 16px;
  overflow: auto;
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
  gap: 10px;
}

.lane-drop-card.loaded {
  border-style: solid;
  border-color: #0b7f78;
  background: #e9f7f4;
}

.lane-drop-card-title {
  font-weight: 700;
  color: #294856;
}

.lane-drop-placeholder {
  color: #6c828c;
  font-size: 12px;
}

.lane-drop-card-pool {
  font-weight: 700;
  color: #0b7f78;
  word-break: break-word;
}

.lane-drop-card-meta {
  color: #59737f;
  font-size: 12px;
}

.lane-remove-button {
  margin-top: auto;
  border: 1px solid #d4dce0;
  border-radius: 8px;
  background: white;
  padding: 8px 10px;
  cursor: pointer;
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
  padding: 12px;
}

.load-pool-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border: 1px solid #dde5e8;
  border-radius: 10px;
  margin-bottom: 10px;
  background: #fff;
  cursor: grab;
}

.load-pool-row.ready .load-pool-name,
.load-pool-row.ready .load-pool-meta {
  color: #238049;
}

.load-pool-row.disabled {
  cursor: not-allowed;
  background: #fbf4f4;
}

.load-pool-row.disabled .load-pool-name,
.load-pool-row.disabled .load-pool-meta {
  color: #c63b32;
}

.load-pool-main {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.load-pool-name {
  font-weight: 700;
  word-break: break-word;
}

.load-pool-read-length,
.load-pool-meta {
  font-size: 12px;
}

.load-flowcell-help-tooltip {
  top: calc(100% + 10px);
  right: -8px;
  width: min(460px, calc(100vw - 40px));
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
</style>

<template>
  <div class="parent-container index-generator-page">
    <div class="header">
      <div class="header-logo" style="display: inline; margin-right: 10px">
        <img
          :src="iconIndexGeneratorHeader"
          alt="Index Generator"
          width="42"
          height="42"
          style="display: block"
        />
      </div>
      <div class="header-title">Index Generator</div>

      <div class="sticky-actions">
        <div class="header-generate-controls">
          <select
            v-if="requiresStrictStartCoordinate"
            id="index-generator-start-coordinate"
            class="pool-size-select coordinate-input"
            :value="selectedStartCoordinate"
            :disabled="
              startCoordinatesLoading || !startCoordinateOptions.length
            "
            @change="onStartCoordinateSelect($event.target.value)"
          >
            <option :value="''">Start coordinate</option>
            <option
              v-for="coordinate in startCoordinateOptions"
              :key="`start-coord-${coordinate}`"
              :value="coordinate"
            >
              {{ coordinate }}
            </option>
          </select>
          <input
            v-else
            id="index-generator-start-coordinate"
            class="pool-size-select coordinate-input"
            :value="selectedStartCoordinate"
            placeholder="Start (e.g. A1)"
            @change="onStartCoordinateChange($event.target.value)"
          />
          <select
            id="index-generator-direction"
            class="pool-size-select"
            :value="selectedDirection"
            @change="onDirectionChange($event.target.value)"
          >
            <option
              v-for="directionOption in directionOptions"
              :key="`direction-${directionOption.value}`"
              :value="directionOption.value"
            >
              {{ directionOption.label }}
            </option>
          </select>
        </div>
        <div class="header-pool-size-controls">
          <select
            id="index-generator-pool-multiplier"
            class="pool-size-select"
            :value="selectedPoolMultiplier"
            @change="onPoolMultiplierChange($event.target.value)"
          >
            <option :value="''">Multiplier</option>
            <option
              v-for="multiplier in poolMultiplierOptions"
              :key="`multiplier-${multiplier}`"
              :value="multiplier"
            >
              {{ multiplier }}
            </option>
          </select>

          <select
            id="index-generator-pool-size"
            class="pool-size-select"
            :value="selectedPoolActualSize"
            :disabled="!selectedPoolMultiplier"
            @change="onPoolActualSizeChange($event.target.value)"
          >
            <option :value="''">Size</option>
            <option
              v-for="size in filteredPoolSizeOptions"
              :key="`size-${size}`"
              :value="size"
            >
              {{ size }}
            </option>
          </select>
        </div>
        <button
          class="header-button"
          :disabled="!canGenerate"
          @click="generateIndices"
        >
          <span>Generate Indices</span>
        </button>
        <button
          class="header-button save-pool-button"
          :disabled="!canSave"
          @click="savePool"
        >
          <span>Save Pool</span>
        </button>
      </div>
    </div>

    <div class="table-container tables-wrap">
      <section
        class="panel left-panel"
        :class="{ 'left-panel-collapsed': isLeftPanelCollapsed }"
        :style="leftPanelInlineStyle"
      >
        <div
          class="panel-heading"
          :class="{ 'panel-heading-stacked': isLeftPanelNarrow }"
        >
          <div class="panel-heading-primary">
            <h3>Libraries and Samples for Pooling</h3>
          </div>
          <div class="panel-heading-actions">
            <div
              class="apply-all-controls"
              :class="{ compact: isLeftPanelNarrow }"
            >
              <label class="apply-all-label">Apply to selected records</label>
              <select
                :value="applyAllReadLength"
                @change="applyFieldToAll('read_length', $event.target.value)"
              >
                <option :value="''">Read Length</option>
                <option
                  v-for="readLength in readLengths"
                  :key="`apply-read-length-${readLength.id}`"
                  :value="readLength.id"
                >
                  {{ readLength.name }}
                </option>
              </select>
              <select
                class="apply-index-type-select"
                :value="applyAllIndexType"
                @change="applyFieldToAll('index_type', $event.target.value)"
              >
                <option :value="''">Index Type</option>
                <option
                  v-for="indexType in generatorIndexTypes"
                  :key="`apply-index-type-${indexType.id}`"
                  :value="indexType.id"
                >
                  {{ indexType.name }}
                </option>
              </select>
            </div>
          </div>
        </div>
        <div class="table-scroll">
          <table>
            <thead>
              <tr>
                <th class="checkbox-column"></th>
                <th class="name-column">Name</th>
                <th class="barcode-column">Barcode</th>
                <th class="depth-column">Depth (M)</th>
                <th class="length-column">Length</th>
                <th class="protocol-column">Protocol</th>
                <th class="index-type-column">Index Type</th>
                <th class="sequence-column">Index I7</th>
                <th class="sequence-column">Index I5</th>
              </tr>
            </thead>
            <tbody
              v-for="(groupRows, requestName) in groupedRecords"
              :key="requestName"
            >
              <tr class="group-row" @click="toggleRequestGroup(requestName)">
                <td colspan="9">
                  <div class="group-row-content">
                    <div class="group-row-main">
                      <button
                        class="group-toggle-button"
                        type="button"
                        :aria-expanded="!isRequestCollapsed(requestName)"
                      >
                        {{ isRequestCollapsed(requestName) ? "▸" : "▾" }}
                      </button>
                      <div>
                        <span class="group-row-title">{{ requestName }}</span>
                        <span class="group-row-summary">
                          (#: {{ groupRows.length }}
                          {{ requestGroupSummary(requestName).countLabel }},
                          Total Depth:
                          {{ requestGroupSummary(requestName).totalDepth }}M,
                          Read Lengths:
                          {{
                            requestGroupSummary(requestName).readLengthDisplay
                          }},
                          {{ requestGroupSummary(requestName).biosafetyLevel }})
                        </span>
                      </div>
                      <div class="group-action-buttons-container" @click.stop>
                        <div
                          title="Select All"
                          class="group-action-button"
                          @click="selectAllInGroup(groupRows)"
                        >
                          <img
                            :src="iconSelectAll"
                            alt="Select All"
                            width="24"
                            height="24"
                          />
                        </div>
                        <div
                          title="Deselect All"
                          class="group-action-button"
                          @click="deselectAllInGroup(groupRows)"
                        >
                          <img
                            :src="iconDeselectAll"
                            alt="Deselect All"
                            width="24"
                            height="24"
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                </td>
              </tr>
              <tr
                v-for="row in groupRows"
                v-show="!isRequestCollapsed(requestName)"
                :key="row.rowKey"
                :class="{
                  'duplicate-index-row': isRowDuplicateInPool(row.rowKey)
                }"
              >
                <td class="checkbox-column">
                  <input
                    type="checkbox"
                    :checked="row.selected"
                    @change="toggleSelection(row, $event)"
                  />
                </td>
                <td class="name-column">{{ row.name }}</td>
                <td class="barcode-column barcode-text">{{ row.barcode }}</td>
                <td class="depth-column">{{ row.sequencing_depth }}</td>
                <td class="length-column">
                  <select
                    :value="row.read_length"
                    @change="
                      updateRecordField(row, 'read_length', $event.target.value)
                    "
                  >
                    <option :value="''">-</option>
                    <option
                      v-for="readLength in readLengths"
                      :key="readLength.id"
                      :value="readLength.id"
                    >
                      {{ readLength.name }}
                    </option>
                  </select>
                </td>
                <td class="protocol-column">{{ row.library_protocol_name }}</td>
                <td>
                  <select
                    :value="row.index_type"
                    :disabled="row.type === 'L'"
                    @change="
                      updateRecordField(row, 'index_type', $event.target.value)
                    "
                  >
                    <option :value="0">-</option>
                    <option
                      v-for="indexType in generatorIndexTypes"
                      :key="indexType.id"
                      :value="indexType.id"
                    >
                      {{ indexType.name }}
                    </option>
                  </select>
                </td>
                <td class="sequence-column sequence-text">
                  <span v-if="row.index_i7" class="sequence-colored">
                    <span
                      v-for="(item, idx) in colorizeIndex(row.index_i7)"
                      :key="`${row.rowKey}-i7-${idx}`"
                      :class="['nt', item.className]"
                    >
                      {{ item.base }}
                    </span>
                  </span>
                  <span v-else>-</span>
                </td>
                <td class="sequence-column sequence-text">
                  <span v-if="row.index_i5" class="sequence-colored">
                    <span
                      v-for="(item, idx) in colorizeIndex(row.index_i5)"
                      :key="`${row.rowKey}-i5-${idx}`"
                      :class="['nt', item.className]"
                    >
                      {{ item.base }}
                    </span>
                  </span>
                  <span v-else>-</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <div
        class="panel-splitter"
        :class="{ 'is-collapsed': isLeftPanelCollapsed }"
        @mousedown="startPanelResize"
      >
        <button
          type="button"
          class="splitter-toggle-button"
          :aria-label="
            isLeftPanelCollapsed ? 'Expand left panel' : 'Collapse left panel'
          "
          :title="
            isLeftPanelCollapsed ? 'Expand left panel' : 'Collapse left panel'
          "
          @click.stop="toggleLeftPanelCollapse"
        >
          {{ isLeftPanelCollapsed ? "❯" : "❮" }}
        </button>
      </div>

      <section class="panel right-panel" :style="rightPanelInlineStyle">
        <h3>
          Pool (# {{ poolRows.length }} {{ poolCountLabel }}, Total size:
          {{ totalDepthRounded }} M)
        </h3>
        <div class="table-scroll">
          <table>
            <thead>
              <tr>
                <th class="name-column">Name</th>
                <th class="barcode-column">Barcode</th>
                <th class="type-column">L/S</th>
                <th class="depth-column">Depth (M)</th>
                <th class="coord-column">Coord</th>
                <th class="index-id-column">Index I7 ID</th>
                <th class="sequence-column">Index I7</th>
                <th class="index-id-column">Index I5 ID</th>
                <th class="sequence-column">Index I5</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="row in poolRows"
                :key="row.rowKey"
                :class="{
                  'duplicate-index-row': isRowDuplicateInPool(row.rowKey)
                }"
              >
                <td class="name-column">{{ row.name }}</td>
                <td class="barcode-column barcode-text">{{ row.barcode }}</td>
                <td class="type-column">{{ row.type }}</td>
                <td class="depth-column">{{ row.sequencing_depth }}</td>
                <td class="coord-column">{{ row.coordinate || "-" }}</td>
                <td class="index-id-column">{{ row.index_i7_id || "-" }}</td>
                <td class="sequence-column sequence-text">
                  <span v-if="row.index_i7" class="sequence-colored">
                    <span
                      v-for="(item, idx) in colorizeIndex(row.index_i7)"
                      :key="`${row.rowKey}-pool-i7-${idx}`"
                      :class="['nt', item.className]"
                    >
                      {{ item.base }}
                    </span>
                  </span>
                  <span v-else>-</span>
                </td>
                <td class="index-id-column">{{ row.index_i5_id || "-" }}</td>
                <td class="sequence-column sequence-text">
                  <span v-if="row.index_i5" class="sequence-colored">
                    <span
                      v-for="(item, idx) in colorizeIndex(row.index_i5)"
                      :key="`${row.rowKey}-pool-i5-${idx}`"
                      :class="['nt', item.className]"
                    >
                      {{ item.base }}
                    </span>
                  </span>
                  <span v-else>-</span>
                </td>
              </tr>
              <tr v-if="poolRows.length === 0">
                <td colspan="9">No records selected.</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="balance-block">
          <h4>Color Balance (i7, R/G)</h4>
          <p class="balance-description">
            Proportion shown as Red/Green percentages per cycle (Red = A/C,
            Green = G/T), weighted by sequencing depth.
          </p>
          <div class="balance-grid">
            <span
              v-for="item in i7Balance"
              :key="`i7-${item.cycle}`"
              :class="{ problematic: item.problematic }"
            >
              {{ item.label }}
            </span>
          </div>
        </div>

        <div class="balance-block">
          <h4>Color Balance (i5, R/G)</h4>
          <p class="balance-description">
            Proportion shown as Red/Green percentages per cycle (Red = A/C,
            Green = G/T), weighted by sequencing depth.
          </p>
          <div class="balance-grid">
            <span
              v-for="item in i5Balance"
              :key="`i5-${item.cycle}`"
              :class="{ problematic: item.problematic }"
            >
              {{ item.label }}
            </span>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script>
import {
  createAxiosObject,
  handleError,
  showNotification,
  showUndoNotification,
  urlStringStartsWith
} from "../utilities/utilityFunctions";
import iconIndexGeneratorHeader from "../assets/icons/header_index_generator.svg";
import iconSelectAll from "../assets/icons/action_select_all.svg";
import iconDeselectAll from "../assets/icons/action_deselect_all.svg";
import { buildRequestGroupSummary } from "../constants/requestGroupingConsts";

const axiosRef = createAxiosObject();
const urlStringStart = urlStringStartsWith();

export default {
  name: "IndexGenerator",
  data() {
    return {
      iconIndexGeneratorHeader,
      iconSelectAll,
      iconDeselectAll,
      records: [],
      poolRows: [],
      readLengths: [],
      poolSizes: [],
      generatorIndexTypes: [],
      selectedPoolSizeId: null,
      selectedPoolMultiplier: "",
      selectedPoolActualSize: "",
      collapsedRequests: {},
      activeResize: null,
      activePanelResize: null,
      applyAllReadLength: "",
      applyAllIndexType: "",
      isLeftPanelCollapsed: false,
      defaultLeftPanelWidthPercent: 50,
      leftPanelWidthPercent: 50,
      selectedStartCoordinate: "A1",
      selectedDirection: "down",
      startCoordinateOptions: [],
      startCoordinatesLoading: false,
      directionOptions: [
        { value: "down", label: "Column-wise" },
        { value: "right", label: "Row-wise" },
        { value: "diagonal", label: "Diagonal" }
      ]
    };
  },
  computed: {
    groupedRecords() {
      return this.records.reduce((acc, row) => {
        const key = row.request_name || "-";
        if (!acc[key]) {
          acc[key] = [];
        }
        acc[key].push(row);
        return acc;
      }, {});
    },
    canGenerate() {
      return this.poolRows.some((row) => row.type === "S");
    },
    canSave() {
      return this.poolRows.length > 0 && !!this.selectedPoolSizeId;
    },
    poolCountLabel() {
      return this.poolRows.length === 1
        ? "library/sample"
        : "libraries/samples";
    },
    totalDepth() {
      return this.poolRows.reduce(
        (sum, row) => sum + Number(row.sequencing_depth || 0),
        0
      );
    },
    totalDepthRounded() {
      return (Math.round(this.totalDepth * 10) / 10).toFixed(1);
    },
    i7Balance() {
      return this.computeColorBalance("index_i7", 12);
    },
    i5Balance() {
      return this.computeColorBalance("index_i5", 12);
    },
    readLengthNameMap() {
      return (this.readLengths || []).reduce((acc, item) => {
        acc[String(item.id)] = item.name;
        return acc;
      }, {});
    },
    parsedPoolSizes() {
      return (this.poolSizes || []).map((size) => {
        const parsed = this.parsePoolSizeName(size.name);
        return {
          ...size,
          multiplier: parsed.multiplier,
          actualSize: parsed.actualSize
        };
      });
    },
    poolMultiplierOptions() {
      const unique = new Set(
        this.parsedPoolSizes
          .map((item) => item.multiplier)
          .filter((value) => value)
      );

      return Array.from(unique).sort((a, b) => {
        const aNum = Number(a);
        const bNum = Number(b);
        const bothNumeric = Number.isFinite(aNum) && Number.isFinite(bNum);
        return bothNumeric ? aNum - bNum : String(a).localeCompare(String(b));
      });
    },
    filteredPoolSizeOptions() {
      if (!this.selectedPoolMultiplier) {
        return [];
      }

      const unique = new Set(
        this.parsedPoolSizes
          .filter(
            (item) =>
              String(item.multiplier) === String(this.selectedPoolMultiplier)
          )
          .map((item) => item.actualSize)
          .filter((value) => value)
      );

      return Array.from(unique).sort((a, b) => {
        const aNum = Number(a);
        const bNum = Number(b);
        const bothNumeric = Number.isFinite(aNum) && Number.isFinite(bNum);
        return bothNumeric ? aNum - bNum : String(a).localeCompare(String(b));
      });
    },
    requestGroupSummaries() {
      return Object.entries(this.groupedRecords).reduce(
        (acc, [requestName, rows]) => {
          acc[requestName] = buildRequestGroupSummary(rows);
          return acc;
        },
        {}
      );
    },
    duplicatePoolRowKeys() {
      const pairToKeys = this.poolRows.reduce((acc, row) => {
        const pairKey = this.getIndexPairKey(row);
        if (!pairKey) {
          return acc;
        }
        if (!acc[pairKey]) {
          acc[pairKey] = [];
        }
        acc[pairKey].push(row.rowKey);
        return acc;
      }, {});

      return Object.values(pairToKeys).reduce((set, keys) => {
        if (keys.length > 1) {
          keys.forEach((key) => set.add(key));
        }
        return set;
      }, new Set());
    },
    selectedPoolIndexTypeIds() {
      const unique = new Set(
        this.poolRows
          .map((row) => Number(row.index_type) || 0)
          .filter((id) => id > 0)
      );
      return Array.from(unique);
    },
    platePoolIndexTypeIds() {
      return this.selectedPoolIndexTypeIds.filter((id) => {
        const meta = this.indexTypeMeta(id);
        return meta?.format === "plate";
      });
    },
    requiresStrictStartCoordinate() {
      return this.platePoolIndexTypeIds.length > 0;
    },
    leftPanelInlineStyle() {
      if (this.isLeftPanelCollapsed) {
        return {};
      }

      const width = `${this.leftPanelWidthPercent}%`;
      return {
        flex: `0 0 ${width}`,
        width
      };
    },
    rightPanelInlineStyle() {
      if (this.isLeftPanelCollapsed) {
        return { flex: "1 1 auto" };
      }

      const width = `${100 - this.leftPanelWidthPercent}%`;
      return {
        flex: `0 0 ${width}`,
        width
      };
    },
    isLeftPanelNarrow() {
      return !this.isLeftPanelCollapsed && this.leftPanelWidthPercent <= 42;
    }
  },
  watch: {
    "$route.name"(name) {
      if (name === "Index Generator") {
        this.loadInitialData();
      }
    },
    poolRows: {
      deep: true,
      handler() {
        this.refreshStartCoordinateOptions();
      }
    },
    generatorIndexTypes() {
      this.refreshStartCoordinateOptions();
    }
  },
  mounted() {
    this.loadInitialData();
  },
  beforeUnmount() {
    document.removeEventListener("mousemove", this.onColumnResizeMove);
    document.removeEventListener("mouseup", this.onColumnResizeEnd);
    document.removeEventListener("mousemove", this.onPanelResizeMove);
    document.removeEventListener("mouseup", this.onPanelResizeEnd);
    document.body.classList.remove("index-generator-resizing");
  },
  methods: {
    async loadInitialData() {
      try {
        const [
          recordsResponse,
          readLengthsResponse,
          poolSizesResponse,
          indexTypesResponse
        ] = await Promise.all([
          axiosRef.get(`${urlStringStart}/api/index_generator/`),
          axiosRef.get(`${urlStringStart}/api/read_lengths/`),
          axiosRef.get(`${urlStringStart}/api/pool_sizes/`),
          axiosRef.get(`${urlStringStart}/api/generator_index_types/`)
        ]);

        this.readLengths = readLengthsResponse.data || [];
        this.records = (recordsResponse.data || []).map((row) =>
          this.normalizeRecord(row)
        );
        this.poolSizes = poolSizesResponse.data || [];
        this.syncSelectedPoolSizeId();
        this.generatorIndexTypes = indexTypesResponse.data || [];
        this.syncCollapsedRequests();
      } catch (error) {
        handleError(error);
      } finally {
        this.$nextTick(() => {
          this.initResizableTables();
        });
      }
    },
    initResizableTables() {
      const tables = this.$el.querySelectorAll(".table-scroll table");
      tables.forEach((table) => this.makeTableResizable(table));
    },
    makeTableResizable(table) {
      const headers = table.querySelectorAll("thead th");
      headers.forEach((th, columnIndex) => {
        if (th.querySelector(".col-resizer")) {
          return;
        }

        const currentWidth = th.getBoundingClientRect().width;
        if (currentWidth > 0 && !th.style.width) {
          this.applyColumnWidth(table, columnIndex, Math.round(currentWidth));
        }

        const resizer = document.createElement("span");
        resizer.className = "col-resizer";
        resizer.addEventListener("mousedown", (event) =>
          this.startColumnResize(event, table, columnIndex)
        );
        th.appendChild(resizer);
      });
    },
    startColumnResize(event, table, columnIndex) {
      event.preventDefault();
      event.stopPropagation();

      const header = table.querySelectorAll("thead th")[columnIndex];
      if (!header) {
        return;
      }

      this.activeResize = {
        table,
        columnIndex,
        startX: event.clientX,
        startWidth: header.offsetWidth
      };

      document.addEventListener("mousemove", this.onColumnResizeMove);
      document.addEventListener("mouseup", this.onColumnResizeEnd);
    },
    onColumnResizeMove(event) {
      if (!this.activeResize) {
        return;
      }

      const delta = event.clientX - this.activeResize.startX;
      const nextWidth = Math.max(64, this.activeResize.startWidth + delta);
      this.applyColumnWidth(
        this.activeResize.table,
        this.activeResize.columnIndex,
        nextWidth
      );
    },
    onColumnResizeEnd() {
      document.removeEventListener("mousemove", this.onColumnResizeMove);
      document.removeEventListener("mouseup", this.onColumnResizeEnd);
      this.activeResize = null;
    },
    applyColumnWidth(table, columnIndex, width) {
      const headers = table.querySelectorAll("thead th");
      const header = headers[columnIndex];
      if (!header) {
        return;
      }

      const px = `${Math.round(width)}px`;
      header.style.width = px;
      header.style.minWidth = px;

      const headerCount = headers.length;
      const rows = table.querySelectorAll("tbody tr");
      rows.forEach((row) => {
        if (row.classList.contains("group-row")) {
          return;
        }

        if (row.children.length !== headerCount) {
          return;
        }

        const cell = row.children[columnIndex];
        if (cell) {
          cell.style.width = px;
          cell.style.minWidth = px;
        }
      });
    },
    syncCollapsedRequests() {
      const updated = {};
      Object.keys(this.groupedRecords).forEach((requestName) => {
        if (
          Object.prototype.hasOwnProperty.call(
            this.collapsedRequests,
            requestName
          )
        ) {
          updated[requestName] = this.collapsedRequests[requestName];
        } else {
          updated[requestName] = true;
        }
      });
      this.collapsedRequests = updated;
    },
    isRequestCollapsed(requestName) {
      return this.collapsedRequests[requestName] !== false;
    },
    toggleRequestGroup(requestName) {
      this.collapsedRequests = {
        ...this.collapsedRequests,
        [requestName]: !this.isRequestCollapsed(requestName)
      };
    },
    toggleLeftPanelCollapse() {
      if (this.isLeftPanelCollapsed) {
        this.leftPanelWidthPercent = this.defaultLeftPanelWidthPercent;
        this.isLeftPanelCollapsed = false;
        return;
      }

      this.isLeftPanelCollapsed = true;
    },
    startPanelResize(event) {
      if (this.isLeftPanelCollapsed) {
        return;
      }

      if (event.target.closest(".splitter-toggle-button")) {
        return;
      }

      const container = this.$el?.querySelector(".tables-wrap");
      if (!container) {
        return;
      }

      const rect = container.getBoundingClientRect();
      this.activePanelResize = {
        containerLeft: rect.left,
        containerWidth: rect.width
      };

      document.addEventListener("mousemove", this.onPanelResizeMove);
      document.addEventListener("mouseup", this.onPanelResizeEnd);
      document.body.classList.add("index-generator-resizing");
    },
    onPanelResizeMove(event) {
      if (!this.activePanelResize || this.isLeftPanelCollapsed) {
        return;
      }

      const { containerLeft, containerWidth } = this.activePanelResize;
      if (!containerWidth) {
        return;
      }

      const nextPercent =
        ((event.clientX - containerLeft) / containerWidth) * 100;
      this.leftPanelWidthPercent = Math.max(22, Math.min(78, nextPercent));
    },
    onPanelResizeEnd() {
      document.removeEventListener("mousemove", this.onPanelResizeMove);
      document.removeEventListener("mouseup", this.onPanelResizeEnd);
      this.activePanelResize = null;
      document.body.classList.remove("index-generator-resizing");
    },
    requestGroupSummary(requestName) {
      return (
        this.requestGroupSummaries[requestName] || buildRequestGroupSummary([])
      );
    },
    colorizeIndex(index) {
      return String(index || "")
        .split("")
        .map((base) => {
          const upper = String(base).toUpperCase();
          if (upper === "A" || upper === "C") {
            return { base, className: "nt-red" };
          }
          if (upper === "G" || upper === "T") {
            return { base, className: "nt-green" };
          }
          return { base, className: "nt-other" };
        });
    },
    resolveReadLengthName(readLengthId) {
      return this.readLengthNameMap[String(readLengthId)] || "";
    },
    getIndexPairKey(row) {
      const i7 = String(row.index_i7 || "").trim();
      const i5 = String(row.index_i5 || "").trim();
      if (!i7) {
        return "";
      }
      return `${i7}::${i5}`;
    },
    isRowDuplicateInPool(rowKey) {
      return this.duplicatePoolRowKeys.has(rowKey);
    },
    getDuplicateGroups(rows = this.poolRows) {
      const grouped = rows.reduce((acc, row) => {
        const pairKey = this.getIndexPairKey(row);
        if (!pairKey) {
          return acc;
        }
        if (!acc[pairKey]) {
          acc[pairKey] = [];
        }
        acc[pairKey].push(row);
        return acc;
      }, {});

      return Object.values(grouped).filter((group) => group.length > 1);
    },
    notifyDuplicateGroups(groups, prefix = "Duplicate indices detected") {
      if (!groups.length) {
        return;
      }

      const details = groups
        .map((group) => group.map((row) => row.name).join(", "))
        .join(" | ");
      showNotification(`${prefix}: ${details}`, "warning");
    },
    rowPairCompatibility(first, row) {
      if (String(first.read_length || "") !== String(row.read_length || "")) {
        return false;
      }

      const firstMeta = this.indexTypeMeta(first.index_type);
      const rowMeta = this.indexTypeMeta(row.index_type);
      if (firstMeta && rowMeta && firstMeta.is_dual !== rowMeta.is_dual) {
        return false;
      }

      return true;
    },
    syncPoolRowFromRecord(row) {
      const index = this.poolRows.findIndex(
        (item) => item.rowKey === row.rowKey
      );
      if (index < 0) {
        return;
      }

      const updated = {
        ...this.poolRows[index],
        ...this.normalizePoolRow(row)
      };
      this.poolRows.splice(index, 1, updated);
    },
    reconcilePoolCompatibility() {
      if (this.poolRows.length <= 1) {
        return;
      }

      const first = this.poolRows[0];
      const removed = [];
      const next = [];

      this.poolRows.forEach((row, idx) => {
        if (idx === 0 || this.rowPairCompatibility(first, row)) {
          next.push(row);
          return;
        }
        removed.push(row.rowKey);
      });

      if (!removed.length) {
        return;
      }

      this.poolRows = next;
      this.records = this.records.map((row) =>
        removed.includes(row.rowKey) ? { ...row, selected: false } : row
      );
      showNotification(
        "Some selected records were deselected because their read length/index mode became incompatible.",
        "warning"
      );
    },
    onStartCoordinateChange(value) {
      this.selectedStartCoordinate = String(value || "")
        .trim()
        .toUpperCase();
    },
    onStartCoordinateSelect(value) {
      this.selectedStartCoordinate = String(value || "")
        .trim()
        .toUpperCase();
    },
    sortDirectionOptions(options) {
      if (!Array.isArray(options)) {
        return [];
      }

      const order = {
        down: 0,
        right: 1,
        diagonal: 2
      };

      return [...options].sort((a, b) => {
        const aOrder = order[a?.value] ?? Number.MAX_SAFE_INTEGER;
        const bOrder = order[b?.value] ?? Number.MAX_SAFE_INTEGER;
        return aOrder - bOrder;
      });
    },
    onDirectionChange(value) {
      this.selectedDirection = value || "down";
    },
    async refreshStartCoordinateOptions() {
      if (!this.requiresStrictStartCoordinate) {
        this.startCoordinateOptions = [];
        if (!this.selectedStartCoordinate) {
          this.selectedStartCoordinate = "A1";
        }
        return;
      }

      this.startCoordinatesLoading = true;
      try {
        const response = await axiosRef.post(
          `${urlStringStart}/api/index_generator/start_coordinates/`,
          {
            index_type_ids: JSON.stringify(this.platePoolIndexTypeIds)
          }
        );

        if (!response.data?.success) {
          showNotification(
            response.data?.message || "Failed to load start coordinates.",
            "error"
          );
          this.startCoordinateOptions = [];
          return;
        }

        this.startCoordinateOptions = response.data?.coordinates || [];

        if (Array.isArray(response.data?.direction_options)) {
          this.directionOptions = this.sortDirectionOptions(
            response.data.direction_options
          );
        }

        if (!this.startCoordinateOptions.length) {
          this.selectedStartCoordinate = "";
          return;
        }

        if (
          !this.startCoordinateOptions.includes(this.selectedStartCoordinate)
        ) {
          this.selectedStartCoordinate =
            response.data?.default_start_coord ||
            this.startCoordinateOptions[0];
        }

        const allowedDirections = this.directionOptions.map(
          (item) => item.value
        );
        if (!allowedDirections.includes(this.selectedDirection)) {
          this.selectedDirection = allowedDirections.includes("down")
            ? "down"
            : allowedDirections[0] || "down";
        }
      } catch (error) {
        this.startCoordinateOptions = [];
        this.handleApiError(error, "Failed to load start coordinates.");
      } finally {
        this.startCoordinatesLoading = false;
      }
    },
    async applyFieldToAll(field, value) {
      const normalizedValue = Number(value) || 0;

      if (!normalizedValue) {
        if (field === "read_length") {
          this.applyAllReadLength = "";
        } else if (field === "index_type") {
          this.applyAllIndexType = "";
        }
        return;
      }

      const targetRows = this.records.filter((row) => {
        if (!row.selected) {
          return false;
        }

        if (field === "index_type") {
          return row.type === "S";
        }
        return true;
      });

      if (!targetRows.length) {
        showNotification(
          "No selected records available for this field.",
          "warning"
        );
        return;
      }

      const readLengthUndoEntries =
        field === "read_length"
          ? this.buildReadLengthUndoEntries(targetRows)
          : [];

      targetRows.forEach((row) => {
        row[field] = normalizedValue;
        if (field === "read_length") {
          row.read_length_name = this.resolveReadLengthName(normalizedValue);
        }
        if (field === "index_type") {
          row.index_i7 = "";
          row.index_i5 = "";
        }
        this.syncPoolRowFromRecord(row);
      });

      this.reconcilePoolCompatibility();
      await this.refreshStartCoordinateOptions();

      try {
        await axiosRef.post(`${urlStringStart}/api/index_generator/edit/`, {
          data: JSON.stringify(
            targetRows.map((row) => ({
              pk: row.pk,
              record_type: row.record_type,
              [field]: normalizedValue
            }))
          )
        });
        if (field === "read_length") {
          const affectedLabel =
            targetRows.length === 1
              ? "1 record"
              : `${targetRows.length} records`;
          showUndoNotification(
            `Read length updated for ${affectedLabel}.`,
            async () => {
              await this.undoReadLengthChanges(readLengthUndoEntries);
            },
            { type: "success", timeout: 10000 }
          );
        } else {
          showNotification("Values applied to selected records.", "success");
        }
      } catch (error) {
        this.handleApiError(error, `Failed to apply ${field}.`);
      }

      if (field === "read_length") {
        this.applyAllReadLength = String(normalizedValue);
      } else if (field === "index_type") {
        this.applyAllIndexType = String(normalizedValue);
      }
    },
    handleApiError(error, fallbackMessage) {
      const message =
        error?.response?.data?.message ||
        error?.response?.data?.detail ||
        fallbackMessage;
      if (message) {
        showNotification(message, "error");
      }
      handleError(error);
    },
    buildReadLengthUndoEntries(rows) {
      return rows.map((row) => ({
        rowKey: row.rowKey,
        pk: row.pk,
        record_type: row.record_type,
        read_length: Number(row.read_length) || 0
      }));
    },
    async undoReadLengthChanges(undoEntries) {
      if (!Array.isArray(undoEntries) || !undoEntries.length) {
        return;
      }

      const payload = [];
      undoEntries.forEach((entry) => {
        const row = this.records.find(
          (record) => record.rowKey === entry.rowKey
        );
        if (!row) {
          return;
        }

        row.read_length = entry.read_length;
        row.read_length_name = this.resolveReadLengthName(entry.read_length);
        this.syncPoolRowFromRecord(row);

        payload.push({
          pk: entry.pk,
          record_type: entry.record_type,
          read_length: entry.read_length
        });
      });

      this.reconcilePoolCompatibility();
      await this.refreshStartCoordinateOptions();

      if (!payload.length) {
        showNotification(
          "Undo skipped because records are no longer available.",
          "warning"
        );
        return;
      }

      try {
        await axiosRef.post(`${urlStringStart}/api/index_generator/edit/`, {
          data: JSON.stringify(payload)
        });
        showNotification("Undo applied.", "success");
      } catch (error) {
        this.handleApiError(error, "Failed to undo read length changes.");
      }
    },
    setRowSelection(row, checked) {
      if (checked && !this.selectedPoolSizeId) {
        return false;
      }

      if (checked && row.type === "S" && !row.index_type) {
        return false;
      }

      if (checked && !this.isCompatibleWithPool(row)) {
        return false;
      }

      row.selected = checked;

      if (checked) {
        const candidate = this.normalizePoolRow(row);
        const alreadySelected = this.poolRows.some(
          (item) => item.rowKey === candidate.rowKey
        );
        if (!alreadySelected) {
          this.poolRows.push(candidate);
        }
      } else {
        this.poolRows = this.poolRows.filter(
          (item) => item.rowKey !== row.rowKey
        );
      }

      return true;
    },
    selectAllInGroup(groupRows) {
      if (!this.selectedPoolSizeId) {
        showNotification("Pool Size must be set.", "warning");
        return;
      }

      for (const row of groupRows) {
        if (row.selected) {
          continue;
        }

        if (row.type === "S" && !row.index_type) {
          showNotification("Index Type must be set.", "warning");
          return;
        }

        if (!this.setRowSelection(row, true)) {
          return;
        }
      }
    },
    deselectAllInGroup(groupRows) {
      groupRows.forEach((row) => {
        if (row.selected) {
          this.setRowSelection(row, false);
        }
      });
    },
    normalizeRecord(row) {
      const type = row.barcode?.[2] || "";
      return {
        ...row,
        rowKey: `${row.record_type}:${row.pk}`,
        type,
        selected: false,
        read_length: row.read_length || "",
        read_length_name:
          row.read_length_name || this.resolveReadLengthName(row.read_length),
        index_type: row.index_type || 0,
        index_i7: row.index_i7 || "",
        index_i5: row.index_i5 || ""
      };
    },
    normalizePoolRow(row) {
      const i7 = this.extractIndexString(row.index_i7);
      const i5 = this.extractIndexString(row.index_i5);
      return {
        ...row,
        rowKey: `${row.record_type}:${row.pk}`,
        type: row.barcode?.[2] || "",
        index_i7: i7,
        index_i5: i5
      };
    },
    extractIndexString(value) {
      if (!value) return "";
      if (typeof value === "string") return value;
      if (typeof value === "object" && value.index) return value.index;
      return "";
    },
    indexTypeMeta(indexTypeId) {
      return this.generatorIndexTypes.find(
        (item) => String(item.id) === String(indexTypeId)
      );
    },
    parsePoolSizeName(value) {
      const raw = String(value || "").trim();
      const parsed = raw.match(/^(\d+)\s*[xX]\s*(.+)$/);
      if (parsed) {
        return {
          multiplier: parsed[1],
          actualSize: parsed[2].trim()
        };
      }

      return {
        multiplier: "",
        actualSize: raw
      };
    },
    onPoolMultiplierChange(value) {
      this.selectedPoolMultiplier = value || "";
      this.selectedPoolActualSize = "";
      this.syncSelectedPoolSizeId();
    },
    onPoolActualSizeChange(value) {
      this.selectedPoolActualSize = value || "";
      this.syncSelectedPoolSizeId();
    },
    syncSelectedPoolSizeId() {
      if (!this.selectedPoolMultiplier || !this.selectedPoolActualSize) {
        this.selectedPoolSizeId = null;
        return;
      }

      const selectedPoolSize = this.parsedPoolSizes.find(
        (item) =>
          String(item.multiplier) === String(this.selectedPoolMultiplier) &&
          String(item.actualSize) === String(this.selectedPoolActualSize)
      );

      this.selectedPoolSizeId = selectedPoolSize ? selectedPoolSize.id : null;
    },
    isNanoporeProtocol(row) {
      const protocol = String(row.library_protocol_name || "").toLowerCase();
      return /oxford\s*nanopore|nanopore|\bont\b/.test(protocol);
    },
    async updateRecordField(row, field, value) {
      const previousReadLength = Number(row.read_length) || 0;
      const normalizedValue =
        field === "read_length" || field === "index_type"
          ? Number(value) || 0
          : value;
      row[field] = normalizedValue;

      if (field === "read_length") {
        row.read_length_name = this.resolveReadLengthName(normalizedValue);
      }

      if (field === "index_type") {
        row.index_i7 = "";
        row.index_i5 = "";
      }

      this.syncPoolRowFromRecord(row);
      this.reconcilePoolCompatibility();

      try {
        await axiosRef.post(`${urlStringStart}/api/index_generator/edit/`, {
          data: JSON.stringify([
            {
              pk: row.pk,
              record_type: row.record_type,
              [field]: normalizedValue
            }
          ])
        });

        if (field === "read_length" && normalizedValue !== previousReadLength) {
          const undoEntry = [
            {
              rowKey: row.rowKey,
              pk: row.pk,
              record_type: row.record_type,
              read_length: previousReadLength
            }
          ];
          showUndoNotification(
            `Read length updated for ${row.name}.`,
            async () => {
              await this.undoReadLengthChanges(undoEntry);
            },
            { type: "success", timeout: 10000 }
          );
        }
      } catch (error) {
        this.handleApiError(error, `Failed to update ${field}.`);
      }
    },
    splitPoolRowsByType() {
      return this.poolRows.reduce(
        (acc, row) => {
          const key = row.record_type === "Library" ? "libraries" : "samples";
          acc[key].push(row);
          return acc;
        },
        { libraries: [], samples: [] }
      );
    },
    buildPoolRowIndexPayload(rows) {
      return rows.map((row) => ({
        pk: row.pk,
        index_i7: row.index_i7 || "",
        index_i5: row.index_i5 || ""
      }));
    },
    validateSelectedRowsBeforeSave() {
      if (this.poolRows.length <= 1) {
        return true;
      }

      for (const row of this.poolRows) {
        if (!row.index_i7) {
          showNotification(`Index I7 is not set for "${row.name}".`, "warning");
          return false;
        }
        const indexMeta = this.indexTypeMeta(row.index_type);
        if (indexMeta?.is_dual && !row.index_i5) {
          showNotification(`Index I5 is not set for "${row.name}".`, "warning");
          return false;
        }
      }

      return true;
    },
    toggleSelection(row, event) {
      const checked = event.target.checked;

      if (checked && !this.selectedPoolSizeId) {
        showNotification("Pool Size must be set.", "warning");
        row.selected = false;
        event.target.checked = false;
        return;
      }

      if (checked && row.type === "S" && !row.index_type) {
        showNotification("Index Type must be set.", "warning");
        row.selected = false;
        event.target.checked = false;
        return;
      }

      if (checked && !this.isCompatibleWithPool(row)) {
        row.selected = false;
        event.target.checked = false;
        return;
      }

      this.setRowSelection(row, checked);
    },
    isCompatibleWithPool(row) {
      if (!this.poolRows.length) return true;

      const first = this.poolRows[0];
      if (!this.rowPairCompatibility(first, row)) {
        if (String(first.read_length || "") !== String(row.read_length || "")) {
          showNotification("Read lengths must be the same.", "warning");
          return false;
        }

        const firstMeta = this.indexTypeMeta(first.index_type);
        const rowMeta = this.indexTypeMeta(row.index_type);
        if (firstMeta && rowMeta && firstMeta.is_dual !== rowMeta.is_dual) {
          showNotification(
            "Pooling of dual and single indices is not allowed.",
            "warning"
          );
        }
        return false;
      }

      return true;
    },
    async generateIndices() {
      const normalizedStart = String(this.selectedStartCoordinate || "")
        .trim()
        .toUpperCase();

      if (this.requiresStrictStartCoordinate) {
        if (!this.startCoordinateOptions.includes(normalizedStart)) {
          showNotification(
            "Please select a valid start coordinate from the dropdown.",
            "warning"
          );
          return;
        }
      } else if (!/^([A-Z]+)(\d+)$/.test(normalizedStart)) {
        showNotification(
          "Invalid start coordinate. Use format like A1.",
          "warning"
        );
        return;
      }

      const { libraries: libraryRows, samples: sampleRows } =
        this.splitPoolRowsByType();
      const libraries = libraryRows.map((row) => row.pk);
      const samples = sampleRows.map((row) => row.pk);

      try {
        const response = await axiosRef.post(
          `${urlStringStart}/api/index_generator/generate_indices/`,
          {
            libraries: JSON.stringify(libraries),
            samples: JSON.stringify(samples),
            start_coord: normalizedStart,
            direction: this.selectedDirection || "down"
          }
        );

        if (!response.data?.success) {
          showNotification(
            response.data?.message || "Index generation failed.",
            "error"
          );
          return;
        }

        const generatedRows = (response.data.data || []).map((row) =>
          this.normalizePoolRow(row)
        );
        const generatedByKey = new Map(
          generatedRows.map((generated) => [generated.rowKey, generated])
        );

        this.poolRows = generatedRows;
        this.records = this.records.map((record) => {
          const generated = generatedByKey.get(record.rowKey);
          if (!generated) return record;
          return {
            ...record,
            selected: this.poolRows.some((row) => row.rowKey === record.rowKey),
            index_i7: generated?.index_i7 || "",
            index_i5: generated?.index_i5 || ""
          };
        });
      } catch (error) {
        const duplicateGroups = this.getDuplicateGroups();
        if (duplicateGroups.length) {
          this.notifyDuplicateGroups(
            duplicateGroups,
            "Potential overlap in fixed/selected index pairs"
          );
        }
        this.handleApiError(error, "Index generation failed.");
      }
    },
    async savePool() {
      if (!this.validateSelectedRowsBeforeSave()) {
        return;
      }

      const duplicateGroups = this.getDuplicateGroups();
      if (duplicateGroups.length) {
        this.notifyDuplicateGroups(
          duplicateGroups,
          "Duplicate index pairs in pool"
        );
        return;
      }

      const { libraries: libraryRows, samples: sampleRows } =
        this.splitPoolRowsByType();
      const libraries = this.buildPoolRowIndexPayload(libraryRows);
      const samples = this.buildPoolRowIndexPayload(sampleRows);

      try {
        const response = await axiosRef.post(
          `${urlStringStart}/api/index_generator/save_pool/`,
          {
            pool_size_id: this.selectedPoolSizeId,
            libraries: JSON.stringify(libraries),
            samples: JSON.stringify(samples)
          }
        );

        if (!response.data?.success) {
          showNotification(
            response.data?.message || "Saving pool failed.",
            "error"
          );
          return;
        }

        showNotification("Pool has been saved!", "success");
        this.poolRows = [];
        this.selectedPoolSizeId = null;
        this.selectedPoolMultiplier = "";
        this.selectedPoolActualSize = "";
        await this.loadInitialData();
      } catch (error) {
        this.handleApiError(error, "Saving pool failed.");
      }
    },
    computeColorBalance(field, maxCycles) {
      const result = [];
      for (let cycle = 0; cycle < maxCycles; cycle += 1) {
        let green = 0;
        let red = 0;
        let total = 0;

        for (const row of this.poolRows) {
          if (this.isNanoporeProtocol(row)) {
            continue;
          }
          const index = String(row[field] || "");
          if (!index || !index[cycle]) {
            continue;
          }

          const nucleotide = index[cycle].toUpperCase();
          const depth = Number(row.sequencing_depth || 0);
          if (nucleotide === "G" || nucleotide === "T") {
            green += depth;
          } else if (nucleotide === "A" || nucleotide === "C") {
            red += depth;
          }
          total += depth;
        }

        if (this.poolRows.length <= 1 || total <= 0) {
          result.push({
            cycle: cycle + 1,
            label: `C${cycle + 1}: -`,
            problematic: false
          });
          continue;
        }

        const greenPct = Math.round((green / total) * 100);
        const redPct = Math.round((red / total) * 100);
        const problematic =
          (greenPct < 20 && redPct > 80) || (redPct < 20 && greenPct > 80);

        result.push({
          cycle: cycle + 1,
          label: `C${cycle + 1}: ${redPct}%/${greenPct}%`,
          problematic
        });
      }
      return result;
    }
  }
};
</script>

<style scoped>
.index-generator-page {
  height: 100%;
  font-family: var(--app-font-family);
  font-size: inherit;
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

.sticky-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-pool-size-controls {
  display: flex;
  align-items: center;
  gap: 6px;
}

.header-generate-controls {
  display: flex;
  align-items: center;
  gap: 6px;
}

.panel-heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.panel-heading-primary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  min-width: 0;
  flex: 1 1 auto;
}

.panel-heading-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.apply-all-controls {
  display: flex;
  align-items: center;
  gap: 5px;
  min-width: 0;
  flex-wrap: nowrap;
}

.apply-all-controls select {
  height: 28px;
  border: 1px solid #cfd8dc;
  border-radius: 6px;
  font-size: 13px;
  padding: 0 8px;
  background: #fff;
  min-width: 0;
}

.apply-index-type-select {
  width: 208px;
}

.left-panel .panel-heading {
  flex-wrap: wrap;
  align-items: flex-start;
}

.left-panel .panel-heading-actions {
  min-width: 0;
  flex: 0 1 auto;
  margin-left: auto;
  justify-content: flex-end;
  flex-wrap: wrap;
}

.left-panel .panel-heading.panel-heading-stacked .panel-heading-primary,
.left-panel .panel-heading.panel-heading-stacked .panel-heading-actions {
  flex: 1 1 100%;
}

.apply-all-controls.compact {
  display: flex;
  flex-wrap: nowrap;
  align-items: center;
  gap: 5px;
}

.apply-all-controls.compact .apply-all-label {
  flex: 0 0 auto;
}

.apply-all-controls.compact select:nth-of-type(1) {
  flex: 0 1 130px;
}

.apply-all-controls.compact select:nth-of-type(2) {
  flex: 0 1 180px;
}

.apply-all-controls.compact .apply-index-type-select {
  max-width: none;
}

.apply-all-label {
  font-size: 11px;
  color: #4b5557;
  white-space: nowrap;
}

.pool-size-select {
  min-width: 90px;
  height: 33px;
  border: 1px solid #cfd8dc;
  border-radius: 7px;
  background-color: #ffffff;
  padding: 0 10px;
  font-size: 13px;
}

.pool-size-select:focus {
  outline: none;
  border-color: #0b7f78;
  box-shadow: 0 0 0 2px rgba(11, 127, 120, 0.15);
}

.save-pool-button {
  background-color: #0b7f78;
}

.save-pool-button:hover:not(:disabled) {
  background-color: #0a6f68;
}

.header-button:disabled,
.save-pool-button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.tables-wrap {
  margin-top: 10px;
  display: flex;
  flex-direction: row;
  gap: 4px;
  min-height: 0;
  flex: 1;
}

.panel-splitter {
  width: 8px;
  min-width: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  user-select: none;
  cursor: col-resize;
}

.panel-splitter::before {
  content: "";
  width: 1px;
  height: 100%;
  background: #d9d9d9;
}

.panel-splitter.is-collapsed {
  cursor: default;
}

.splitter-toggle-button {
  width: 12px;
  height: 56px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  background: #f7f9f9;
  color: #0b7f78;
  cursor: pointer;
  font-size: 10px;
  line-height: 1;
  padding: 0;
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 1;
}

.splitter-toggle-button:hover {
  background: #eef5f4;
}

.panel {
  border: 1px solid #d9d9d9;
  border-radius: 8px;
  padding: 8px;
  min-height: 0;
  display: flex;
  flex-direction: column;
  flex: 1;
  transition:
    flex-basis 0.22s ease,
    width 0.22s ease,
    opacity 0.2s ease,
    padding 0.22s ease,
    border-width 0.22s ease,
    margin 0.22s ease;
}

.left-panel.left-panel-collapsed {
  flex: 0 0 0;
  width: 0;
  min-width: 0;
  opacity: 0;
  padding-left: 0;
  padding-right: 0;
  border-left-width: 0;
  border-right-width: 0;
  margin: 0;
  overflow: hidden;
}

.panel h3 {
  margin: 0;
}

.table-scroll {
  overflow: auto;
  flex: 1;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  table-layout: fixed;
}

.left-panel table {
  min-width: 1150px;
}

.right-panel table {
  min-width: 1100px;
}

th,
td {
  border: 1px solid #ececec;
  padding: 6px;
  text-align: left;
  position: relative;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

td select {
  width: 100%;
  min-width: 0;
  box-sizing: border-box;
}

th {
  overflow: hidden;
}

.col-resizer {
  position: absolute;
  top: 0;
  right: -3px;
  width: 8px;
  height: 100%;
  cursor: col-resize;
  user-select: none;
  z-index: 3;
}

.col-resizer:hover {
  background: rgba(11, 127, 120, 0.2);
}

.group-row td {
  background: #f4f7f7;
  font-weight: 600;
  cursor: pointer;
}

.group-row-content {
  display: flex;
  justify-content: flex-start;
  align-items: center;
  gap: 8px;
}

.group-row-main {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.group-row-title {
  font-weight: bold;
  font-size: 13px;
  color: #333;
}

.group-row-summary {
  font-weight: normal;
  font-size: 13px;
  margin-left: 2px;
  color: black;
}

.group-toggle-button {
  border: none;
  background: transparent;
  cursor: pointer;
  margin-right: 6px;
  padding: 0;
  width: 16px;
  color: #0b7f78;
  font-size: 13px;
  font-weight: 700;
}

.group-action-buttons-container {
  display: flex;
  gap: 5px;
}

.group-action-button {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.protocol-column {
  min-width: 230px;
  width: 230px;
  max-width: 360px;
}

.index-type-column {
  min-width: 110px;
  width: 110px;
}

.checkbox-column {
  min-width: 40px;
  width: 40px;
  text-align: center;
}

.name-column {
  min-width: 220px;
  width: 220px;
}

.barcode-column,
.coord-column {
  min-width: 110px;
  width: 110px;
}

.depth-column,
.length-column {
  min-width: 90px;
  width: 90px;
}

.type-column {
  min-width: 68px;
  width: 68px;
}

.index-id-column {
  min-width: 104px;
  width: 104px;
}

.sequence-column {
  min-width: 130px;
  width: 130px;
}

.coordinate-input {
  min-width: 122px;
}

.barcode-text {
  font-family: var(--app-font-family);
}

.sequence-text {
  font-family: "Courier New", Courier, monospace;
}

.sequence-colored {
  letter-spacing: 0.4px;
}

.nt {
  font-weight: 700;
}

.nt-red {
  color: #c53030;
}

.nt-green {
  color: #2f855a;
}

.nt-other {
  color: #5c6670;
}

.duplicate-index-row td {
  background: #ffe7e7;
}

.balance-block {
  margin-top: 8px;
}

.balance-block h4 {
  margin: 0 0 6px 0;
}

.balance-grid {
  display: grid;
  grid-template-columns: repeat(12, minmax(0, 1fr));
  gap: 4px;
}

.balance-description {
  margin: 0 0 6px 0;
  font-size: 11px;
  color: #4c5457;
}

.balance-grid span {
  font-size: 11px;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 3px 4px;
  background: #fafafa;
}

.balance-grid span.problematic {
  border-color: #de4b4b;
  background: #ffd7d7;
}

@media (max-width: 980px) {
  .tables-wrap {
    flex-direction: column;
  }

  .panel-splitter {
    display: none;
  }

  .pool-size-select {
    min-width: 120px;
  }
}

@media (max-width: 550px) {
  .panel-heading {
    flex-wrap: wrap;
    align-items: flex-start;
  }

  .pool-size-select {
    width: 100%;
    min-width: 0;
  }
}
</style>

<template>
  <div class="parent-container index-generator-page">
    <div v-if="loading" class="loading-overlay">
      <div class="spinner"></div>
      <p>Loading <span style="font-weight: bold">Index Generator</span>...</p>
    </div>

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
      <div class="header-title" style="display: inline">Index Generator</div>

      <div class="header-center">
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
      </div>

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
            <option :value="''">Start Coordinate</option>
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
              <label class="apply-all-label">Apply to Selected Records</label>
              <select
                :value="applyAllReadLength"
                @change="
                  applyFieldToAll(
                    indexGeneratorFields.readLength,
                    $event.target.value
                  )
                "
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
                @change="
                  applyFieldToAll(
                    indexGeneratorFields.indexType,
                    $event.target.value
                  )
                "
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
              <button
                type="button"
                class="add-selected-pool-button"
                @click="addSelectedRowsToPool"
              >
                Add Selected to Pool
              </button>
            </div>
          </div>
        </div>
        <div class="table-scroll">
          <TabulatorTable
            v-if="!loading"
            ref="sourceTabulatorTableRef"
            tableId="indexGeneratorSourceTable"
            :rowData="records"
            :columnDefs="sourceColumnsList"
            :enableDefaultFilters="false"
            groupBy="request_name"
            :groupStartOpen="false"
            :tableOptions="sourceTableOptions"
          />
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
            isLeftPanelCollapsed ? 'Expand Left Panel' : 'Collapse Left Panel'
          "
          :data-tooltip-original="
            isLeftPanelCollapsed ? 'Expand Left Panel' : 'Collapse Left Panel'
          "
          @click.stop="toggleLeftPanelCollapse"
        >
          {{ isLeftPanelCollapsed ? "❯" : "❮" }}
        </button>
      </div>

      <section class="panel right-panel" :style="rightPanelInlineStyle">
        <div class="panel-heading">
          <div class="panel-heading-primary">
            <h3>
              Pool (# {{ poolRows.length }} {{ poolCountLabel }}, Total size:
              {{ totalDepthRounded }} M, Fill: {{ poolFillPercentageDisplay }})
            </h3>
          </div>
        </div>
        <div class="table-scroll">
          <TabulatorTable
            v-if="!loading"
            ref="poolTabulatorTableRef"
            tableId="indexGeneratorPoolTable"
            :rowData="poolRows"
            :columnDefs="poolColumnsList"
            :enableDefaultFilters="false"
            groupBy="request_name"
            :groupStartOpen="true"
            :tableOptions="poolTableOptions"
          />
        </div>

        <div class="balance-block">
          <h4>Color Balance (I7, R/G)</h4>
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
          <h4>Color Balance (I5, R/G)</h4>
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
import iconIndexGeneratorHeader from "../assets/icons/header_index_generator_cog.svg";
import iconSelectAll from "../assets/icons/action_select_all.svg";
import iconDeselectAll from "../assets/icons/action_deselect_all.svg";
import TabulatorTable from "../components/TabulatorTableFull.vue";
import {
  INDEX_GENERATOR_API_ENDPOINTS,
  INDEX_GENERATOR_COLOR_BALANCE,
  INDEX_GENERATOR_DEFAULTS,
  INDEX_GENERATOR_DIRECTION_OPTIONS,
  INDEX_GENERATOR_DIRECTION_ORDER,
  INDEX_GENERATOR_FIELDS,
  INDEX_GENERATOR_INDEX_FIELDS,
  INDEX_GENERATOR_POOL_PAYLOAD_KEYS,
  INDEX_GENERATOR_PROTOCOL_PATTERNS,
  INDEX_GENERATOR_RESPONSE_KEYS,
  INDEX_GENERATOR_RECORD_TYPES,
  indexGeneratorPoolColumnDefs,
  indexGeneratorPoolGroupHeader,
  indexGeneratorSourceColumnDefs,
  indexGeneratorSourceGroupHeader
} from "../constants/indexGeneratorConsts";
import { buildRequestGroupSummary } from "../constants/requestGroupingConsts";

const axiosRef = createAxiosObject();
const urlStringStart = urlStringStartsWith();
const apiUrl = (endpoint) => `${urlStringStart}${endpoint}`;
const fields = INDEX_GENERATOR_FIELDS;

export default {
  name: "IndexGenerator",
  components: {
    TabulatorTable
  },
  data() {
    return {
      iconIndexGeneratorHeader,
      iconSelectAll,
      iconDeselectAll,
      indexGeneratorFields: INDEX_GENERATOR_FIELDS,
      indexGeneratorRecordTypes: INDEX_GENERATOR_RECORD_TYPES,
      records: [],
      poolRows: [],
      sourceColumnsList: [],
      poolColumnsList: [],
      sourceTabulatorInstance: null,
      poolTabulatorInstance: null,
      readLengths: [],
      poolSizes: [],
      generatorIndexTypes: [],
      selectedPoolSizeId: null,
      selectedPoolMultiplier: "",
      selectedPoolActualSize: "",
      collapsedRequests: {},
      activePanelResize: null,
      applyAllReadLength: "",
      applyAllIndexType: "",
      generatedIndexRowKeys: [],
      isLeftPanelCollapsed: false,
      defaultLeftPanelWidthPercent:
        INDEX_GENERATOR_DEFAULTS.leftPanelWidthPercent,
      leftPanelWidthPercent: INDEX_GENERATOR_DEFAULTS.leftPanelWidthPercent,
      selectedStartCoordinate: INDEX_GENERATOR_DEFAULTS.startCoordinate,
      selectedDirection: INDEX_GENERATOR_DEFAULTS.direction,
      startCoordinateOptions: [],
      loading: true,
      hasCompletedInitialLoad: false,
      startCoordinatesLoading: false,
      directionOptions: [...INDEX_GENERATOR_DIRECTION_OPTIONS]
    };
  },
  computed: {
    groupedRecords() {
      return this.records.reduce((acc, row) => {
        const key =
          row[fields.requestName] || INDEX_GENERATOR_DEFAULTS.emptyDisplay;
        if (!acc[key]) {
          acc[key] = [];
        }
        acc[key].push(row);
        return acc;
      }, {});
    },
    canGenerate() {
      return this.poolRows.some(
        (row) => row[fields.type] === INDEX_GENERATOR_RECORD_TYPES.sampleCode
      );
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
        (sum, row) => sum + Number(row[fields.sequencingDepth] || 0),
        0
      );
    },
    totalDepthRounded() {
      return (Math.round(this.totalDepth * 10) / 10).toFixed(1);
    },
    selectedPoolCapacityM() {
      const parsed = Number.parseFloat(
        String(this.selectedPoolActualSize || "")
          .replace(",", ".")
          .match(/\d+(?:\.\d+)?/)?.[0] || ""
      );
      return Number.isFinite(parsed) ? parsed : 0;
    },
    poolFillPercentage() {
      if (!this.selectedPoolCapacityM) {
        return null;
      }

      return (this.totalDepth / this.selectedPoolCapacityM) * 100;
    },
    poolFillPercentageDisplay() {
      if (this.poolFillPercentage === null) {
        return "-";
      }

      return `${(Math.round(this.poolFillPercentage * 10) / 10).toFixed(1)}%`;
    },
    i7Balance() {
      return this.computeColorBalance(
        INDEX_GENERATOR_INDEX_FIELDS.i7,
        INDEX_GENERATOR_DEFAULTS.maxColorBalanceCycles
      );
    },
    i5Balance() {
      return this.computeColorBalance(
        INDEX_GENERATOR_INDEX_FIELDS.i5,
        INDEX_GENERATOR_DEFAULTS.maxColorBalanceCycles
      );
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
    groupedPoolRows() {
      return this.poolRows.reduce((acc, row) => {
        const key =
          row[fields.requestName] || INDEX_GENERATOR_DEFAULTS.emptyDisplay;
        if (!acc[key]) {
          acc[key] = [];
        }
        acc[key].push(row);
        return acc;
      }, {});
    },
    poolRequestGroupSummaries() {
      return Object.entries(this.groupedPoolRows).reduce(
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
          .map((row) => Number(row[fields.indexType]) || 0)
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

      const width = `calc(${this.leftPanelWidthPercent}% - 8px)`;
      return {
        flex: `0 0 ${width}`,
        width
      };
    },
    rightPanelInlineStyle() {
      if (this.isLeftPanelCollapsed) {
        return { flex: "1 1 auto" };
      }

      const width = `calc(${100 - this.leftPanelWidthPercent}% - 8px)`;
      return {
        flex: `0 0 ${width}`,
        width
      };
    },
    isLeftPanelNarrow() {
      return !this.isLeftPanelCollapsed && this.leftPanelWidthPercent <= 42;
    },
    sourceTableOptions() {
      return {
        index: fields.rowKey,
        layout: "fitDataStretch",
        placeholder: "No libraries or samples to show.",
        groupHeader: (value, count, data) =>
          indexGeneratorSourceGroupHeader(
            value,
            count,
            data,
            this.requestGroupSummary,
            this.selectAllInGroup,
            this.deselectAllInGroup,
            {
              selectAll: this.iconSelectAll,
              deselectAll: this.iconDeselectAll
            }
          ),
        rowFormatter: this.formatTabulatorRow,
        handleCellEdited: this.handleSourceCellEdited
      };
    },
    poolTableOptions() {
      return {
        index: fields.rowKey,
        layout: "fitDataStretch",
        placeholder: "No records selected.",
        groupHeader: (value, count, data) =>
          indexGeneratorPoolGroupHeader(
            value,
            count,
            data,
            this.poolRequestGroupSummary,
            this.removePoolRowsInGroup
          ),
        groupToggleElement: false,
        rowFormatter: this.formatTabulatorRow
      };
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
      this.setColumns();
      this.refreshStartCoordinateOptions();
    },
    readLengths() {
      this.setColumns();
    }
  },
  mounted() {
    this.setColumns();
    this.loadInitialData();
  },
  updated() {
    this.sourceTabulatorInstance = this.$refs.sourceTabulatorTableRef;
    this.poolTabulatorInstance = this.$refs.poolTabulatorTableRef;
  },
  beforeUnmount() {
    document.removeEventListener("mousemove", this.onPanelResizeMove);
    document.removeEventListener("mouseup", this.onPanelResizeEnd);
    document.body.classList.remove("index-generator-resizing");
  },
  activated() {
    if (this.hasCompletedInitialLoad) {
      this.loadInitialData();
    }
  },
  methods: {
    setColumns() {
      this.sourceColumnsList = indexGeneratorSourceColumnDefs({
        readLengths: this.readLengths,
        generatorIndexTypes: this.generatorIndexTypes,
        onSelectionChange: this.handleSourceSelectionChange,
        isCompatibleWithPool: this.isCompatibleWithPool,
        getIndexTypeName: this.getIndexTypeName
      });
      this.poolColumnsList = indexGeneratorPoolColumnDefs({
        onRemoveRow: this.removePoolRow
      });
    },
    async loadInitialData() {
      this.loading = true;
      try {
        const [
          recordsResponse,
          readLengthsResponse,
          poolSizesResponse,
          indexTypesResponse
        ] = await Promise.all([
          axiosRef.get(apiUrl(INDEX_GENERATOR_API_ENDPOINTS.records)),
          axiosRef.get(apiUrl(INDEX_GENERATOR_API_ENDPOINTS.readLengths)),
          axiosRef.get(apiUrl(INDEX_GENERATOR_API_ENDPOINTS.poolSizes)),
          axiosRef.get(apiUrl(INDEX_GENERATOR_API_ENDPOINTS.indexTypes))
        ]);

        this.readLengths = readLengthsResponse.data || [];
        this.records = (recordsResponse.data || []).map((row) =>
          this.normalizeRecord(row)
        );
        this.poolSizes = poolSizesResponse.data || [];
        this.syncSelectedPoolSizeId();
        this.generatorIndexTypes = indexTypesResponse.data || [];
        this.poolRows = [];
        this.generatedIndexRowKeys = [];
        this.syncCollapsedRequests();
      } catch (error) {
        handleError(error);
      } finally {
        this.loading = false;
        this.hasCompletedInitialLoad = true;
      }
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
    poolRequestGroupSummary(requestName) {
      return (
        this.poolRequestGroupSummaries[requestName] ||
        buildRequestGroupSummary([])
      );
    },
    formatTabulatorRow(row) {
      const rowData = row.getData();
      row
        .getElement()
        .classList.toggle(
          "duplicate-index-row",
          this.isRowDuplicateInPool(rowData[fields.rowKey])
        );
    },
    refreshTabulatorTables() {
      this.$nextTick(() => {
        this.sourceTabulatorInstance?.getTable?.()?.redraw?.(true);
        this.poolTabulatorInstance?.getTable?.()?.redraw?.(true);
      });
    },
    refreshTabulatorData() {
      this.$nextTick(() => {
        this.sourceTabulatorInstance?.getTable?.()?.setData?.(this.records);
        this.poolTabulatorInstance?.getTable?.()?.setData?.(this.poolRows);
      });
    },
    handleSourceSelectionChange(row, checked) {
      this.setRowSelection(row, checked);
      this.refreshTabulatorTables();
    },
    handleSourceCellEdited(cell) {
      const row = cell.getRow().getData();
      const field = cell.getField();
      if (![fields.readLength, fields.indexType].includes(field)) {
        return;
      }
      this.updateRecordField(row, field, cell.getValue(), cell.getOldValue());
    },
    resolveReadLengthName(readLengthId) {
      return this.readLengthNameMap[String(readLengthId)] || "";
    },
    getIndexPairKey(row) {
      const i7 = String(row[fields.indexI7] || "").trim();
      const i5 = String(row[fields.indexI5] || "").trim();
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
    isLikelyOverlapGenerationError(error, duplicateGroups = []) {
      if (error?.response?.status !== 400 || !duplicateGroups.length) {
        return false;
      }

      const serverMessage = String(
        error?.response?.data?.[INDEX_GENERATOR_RESPONSE_KEYS.message] ||
          error?.response?.data?.[INDEX_GENERATOR_RESPONSE_KEYS.detail] ||
          ""
      ).toLowerCase();

      if (!serverMessage) {
        return true;
      }

      return /overlap|duplicate|already\s*assigned|collision|conflict/.test(
        serverMessage
      );
    },
    rowPairCompatibility(first, row) {
      if (
        String(first[fields.readLength] || "") !==
        String(row[fields.readLength] || "")
      ) {
        return false;
      }

      const firstMeta = this.indexTypeMeta(first[fields.indexType]);
      const rowMeta = this.indexTypeMeta(row[fields.indexType]);
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
      this.poolRows = this.poolRows.map((item, itemIndex) =>
        itemIndex === index ? updated : item
      );
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
      this.refreshTabulatorTables();
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

      return [...options].sort((a, b) => {
        const aOrder =
          INDEX_GENERATOR_DIRECTION_ORDER[a?.value] ?? Number.MAX_SAFE_INTEGER;
        const bOrder =
          INDEX_GENERATOR_DIRECTION_ORDER[b?.value] ?? Number.MAX_SAFE_INTEGER;
        return aOrder - bOrder;
      });
    },
    onDirectionChange(value) {
      this.selectedDirection = value || INDEX_GENERATOR_DEFAULTS.direction;
    },
    async refreshStartCoordinateOptions() {
      if (!this.requiresStrictStartCoordinate) {
        this.startCoordinateOptions = [];
        if (!this.selectedStartCoordinate) {
          this.selectedStartCoordinate = INDEX_GENERATOR_DEFAULTS.startCoordinate;
        }
        return;
      }

      this.startCoordinatesLoading = true;
      try {
        const response = await axiosRef.post(
          apiUrl(INDEX_GENERATOR_API_ENDPOINTS.startCoordinates),
          {
            [INDEX_GENERATOR_POOL_PAYLOAD_KEYS.indexTypeIds]: JSON.stringify(
              this.platePoolIndexTypeIds
            )
          }
        );

        if (!response.data?.[INDEX_GENERATOR_RESPONSE_KEYS.success]) {
          showNotification(
            response.data?.[INDEX_GENERATOR_RESPONSE_KEYS.message] ||
              "Failed to load start coordinates.",
            "error"
          );
          this.startCoordinateOptions = [];
          return;
        }

        this.startCoordinateOptions =
          response.data?.[INDEX_GENERATOR_RESPONSE_KEYS.coordinates] || [];

        if (
          Array.isArray(
            response.data?.[INDEX_GENERATOR_RESPONSE_KEYS.directionOptions]
          )
        ) {
          this.directionOptions = this.sortDirectionOptions(
            response.data[INDEX_GENERATOR_RESPONSE_KEYS.directionOptions]
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
            response.data?.[
              INDEX_GENERATOR_RESPONSE_KEYS.defaultStartCoordinate
            ] ||
            this.startCoordinateOptions[0];
        }

        const allowedDirections = this.directionOptions.map(
          (item) => item.value
        );
        if (!allowedDirections.includes(this.selectedDirection)) {
          this.selectedDirection = allowedDirections.includes(
            INDEX_GENERATOR_DEFAULTS.direction
          )
            ? INDEX_GENERATOR_DEFAULTS.direction
            : allowedDirections[0] || INDEX_GENERATOR_DEFAULTS.direction;
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
        if (field === fields.readLength) {
          this.applyAllReadLength = "";
        } else if (field === fields.indexType) {
          this.applyAllIndexType = "";
        }
        return;
      }

      const targetRows = this.records.filter((row) => {
        if (!row[fields.selected]) {
          return false;
        }

        if (field === fields.indexType) {
          return row[fields.type] === INDEX_GENERATOR_RECORD_TYPES.sampleCode;
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
        field === fields.readLength
          ? this.buildReadLengthUndoEntries(targetRows)
          : [];

      targetRows.forEach((row) => {
        row[field] = normalizedValue;
        if (field === fields.readLength) {
          row[fields.readLengthName] =
            this.resolveReadLengthName(normalizedValue);
        }
        if (field === fields.indexType) {
          row[fields.indexI7] = "";
          row[fields.indexI5] = "";
        }
        this.syncPoolRowFromRecord(row);
      });

      await this.refreshStartCoordinateOptions();

      try {
        await axiosRef.post(apiUrl(INDEX_GENERATOR_API_ENDPOINTS.edit), {
          [INDEX_GENERATOR_POOL_PAYLOAD_KEYS.data]: JSON.stringify(
            targetRows.map((row) => ({
              [fields.pk]: row[fields.pk],
              [fields.recordType]: row[fields.recordType],
              [field]: normalizedValue
            }))
          )
        });
        if (field === fields.readLength) {
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
        this.refreshTabulatorData();
      } catch (error) {
        this.handleApiError(
          error,
          `Failed to apply ${this.getFieldDisplayName(field)}.`
        );
      }

      if (field === fields.readLength) {
        this.applyAllReadLength = String(normalizedValue);
      } else if (field === fields.indexType) {
        this.applyAllIndexType = String(normalizedValue);
      }
    },
    handleApiError(error, fallbackMessage) {
      if (error?.response?.status === 403) {
        handleError(error);
        return;
      }

      const message =
        error?.response?.data?.[INDEX_GENERATOR_RESPONSE_KEYS.message] ||
        error?.response?.data?.[INDEX_GENERATOR_RESPONSE_KEYS.detail] ||
        fallbackMessage;
      if (message) {
        showNotification(message, "error");
      }

      if (!error?.response) {
        handleError(error);
      }
    },
    getFieldDisplayName(field) {
      if (field === fields.readLength) {
        return "read length";
      }
      if (field === fields.indexType) {
        return "index type";
      }
      return String(field || "field").replaceAll("_", " ");
    },
    buildReadLengthUndoEntries(rows) {
      return rows.map((row) => ({
        [fields.rowKey]: row[fields.rowKey],
        [fields.pk]: row[fields.pk],
        [fields.recordType]: row[fields.recordType],
        [fields.readLength]: Number(row[fields.readLength]) || 0
      }));
    },
    async undoReadLengthChanges(undoEntries) {
      if (!Array.isArray(undoEntries) || !undoEntries.length) {
        return;
      }

      const payload = [];
      undoEntries.forEach((entry) => {
        const row = this.records.find(
          (record) => record[fields.rowKey] === entry[fields.rowKey]
        );
        if (!row) {
          return;
        }

        row[fields.readLength] = entry[fields.readLength];
        row[fields.readLengthName] = this.resolveReadLengthName(
          entry[fields.readLength]
        );
        this.syncPoolRowFromRecord(row);

        payload.push({
          [fields.pk]: entry[fields.pk],
          [fields.recordType]: entry[fields.recordType],
          [fields.readLength]: entry[fields.readLength]
        });
      });

      await this.refreshStartCoordinateOptions();

      if (!payload.length) {
        showNotification(
          "Undo skipped because records are no longer available.",
          "warning"
        );
        return;
      }

      try {
        await axiosRef.post(apiUrl(INDEX_GENERATOR_API_ENDPOINTS.edit), {
          [INDEX_GENERATOR_POOL_PAYLOAD_KEYS.data]: JSON.stringify(payload)
        });
        showNotification("Undo applied.", "success");
        this.refreshTabulatorData();
      } catch (error) {
        this.handleApiError(error, "Failed to undo read length changes.");
      }
    },
    setRowSelection(row, checked) {
      row.selected = checked;

      this.refreshTabulatorTables();
      return true;
    },
    selectAllInGroup(groupRows) {
      for (const row of groupRows) {
        if (row.selected) {
          continue;
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
    addSelectedRowsToPool() {
      const selectedRows = this.records.filter((row) => row[fields.selected]);
      if (!selectedRows.length) {
        showNotification("No selected records to add to the pool.", "warning");
        return;
      }

      const existingKeys = new Set(
        this.poolRows.map((row) => row[fields.rowKey])
      );
      const rowsToAdd = selectedRows
        .filter((row) => !existingKeys.has(row[fields.rowKey]))
        .map((row) => this.normalizePoolRow(row));

      if (!rowsToAdd.length) {
        showNotification("Selected records are already in the pool.", "warning");
        return;
      }

      this.poolRows = this.sortPoolRows([...this.poolRows, ...rowsToAdd]);
      this.refreshTabulatorData();
      showNotification(
        `Added ${rowsToAdd.length} selected record(s) to the pool.`,
        "success"
      );
    },
    clearGeneratedIndicesForRowKeys(rowKeys) {
      const keys = new Set(rowKeys);
      if (!keys.size) {
        return;
      }

      this.generatedIndexRowKeys = this.generatedIndexRowKeys.filter(
        (rowKey) => !keys.has(rowKey)
      );
      this.records = this.records.map((row) =>
        keys.has(row[fields.rowKey])
          ? {
              ...row,
              [fields.indexI7]: "",
              [fields.indexI5]: ""
            }
          : row
      );
    },
    removePoolRowsByKeys(rowKeys) {
      const keys = new Set(rowKeys);
      if (!keys.size) {
        return;
      }

      this.clearGeneratedIndicesForRowKeys(keys);
      this.poolRows = this.poolRows.filter(
        (row) => !keys.has(row[fields.rowKey])
      );
      this.refreshTabulatorData();
    },
    removePoolRow(row) {
      this.removePoolRowsByKeys([row[fields.rowKey]]);
    },
    removePoolRowsInGroup(groupRows) {
      this.removePoolRowsByKeys(
        (groupRows || []).map((row) => row[fields.rowKey])
      );
    },
    normalizeRecord(row) {
      const type = row[fields.barcode]?.[2] || "";
      return {
        ...row,
        [fields.rowKey]: `${row[fields.recordType]}:${row[fields.pk]}`,
        [fields.requestName]:
          row[fields.requestName] || INDEX_GENERATOR_DEFAULTS.emptyDisplay,
        [fields.type]: type,
        [fields.selected]: false,
        [fields.readLength]: row[fields.readLength] || "",
        [fields.readLengthName]:
          row[fields.readLengthName] ||
          this.resolveReadLengthName(row[fields.readLength]),
        [fields.indexType]: row[fields.indexType] || 0,
        [fields.indexI7]: row[fields.indexI7] || "",
        [fields.indexI5]: row[fields.indexI5] || ""
      };
    },
    normalizePoolRow(row) {
      const i7 = this.extractIndexString(row[fields.indexI7]);
      const i5 = this.extractIndexString(row[fields.indexI5]);
      return {
        ...row,
        [fields.rowKey]: `${row[fields.recordType]}:${row[fields.pk]}`,
        [fields.type]: row[fields.barcode]?.[2] || "",
        [fields.indexI7]: i7,
        [fields.indexI5]: i5
      };
    },
    sortPoolRows(rows) {
      return [...rows].sort((left, right) => {
        const requestCompare = String(left[fields.requestName] || "").localeCompare(
          String(right[fields.requestName] || "")
        );
        if (requestCompare !== 0) return requestCompare;
        return String(left[fields.barcode] || "").localeCompare(
          String(right[fields.barcode] || "")
        );
      });
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
    getIndexTypeName(indexTypeId) {
      return this.indexTypeMeta(indexTypeId)?.name || "";
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
      const protocol = String(row[fields.libraryProtocolName] || "").toLowerCase();
      return INDEX_GENERATOR_PROTOCOL_PATTERNS.nanopore.test(protocol);
    },
    async updateRecordField(row, field, value, previousValue = undefined) {
      const previousReadLength =
        previousValue === undefined
          ? Number(row[fields.readLength]) || 0
          : Number(previousValue) || 0;
      const normalizedValue =
        field === fields.readLength || field === fields.indexType
          ? Number(value) || 0
          : value;
      row[field] = normalizedValue;

      if (field === fields.readLength) {
        row[fields.readLengthName] =
          this.resolveReadLengthName(normalizedValue);
      }

      if (field === fields.indexType) {
        row[fields.indexI7] = "";
        row[fields.indexI5] = "";
      }

      this.syncPoolRowFromRecord(row);

      try {
        await axiosRef.post(apiUrl(INDEX_GENERATOR_API_ENDPOINTS.edit), {
          [INDEX_GENERATOR_POOL_PAYLOAD_KEYS.data]: JSON.stringify([
            {
              [fields.pk]: row[fields.pk],
              [fields.recordType]: row[fields.recordType],
              [field]: normalizedValue
            }
          ])
        });

        if (field === fields.readLength && normalizedValue !== previousReadLength) {
          const undoEntry = [
            {
              [fields.rowKey]: row[fields.rowKey],
              [fields.pk]: row[fields.pk],
              [fields.recordType]: row[fields.recordType],
              [fields.readLength]: previousReadLength
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
        this.refreshTabulatorData();
      } catch (error) {
        this.handleApiError(
          error,
          `Failed to update ${this.getFieldDisplayName(field)}.`
        );
      }
    },
    splitPoolRowsByType() {
      return this.poolRows.reduce(
        (acc, row) => {
          const key =
            row[fields.recordType] === INDEX_GENERATOR_RECORD_TYPES.library
              ? INDEX_GENERATOR_POOL_PAYLOAD_KEYS.libraries
              : INDEX_GENERATOR_POOL_PAYLOAD_KEYS.samples;
          acc[key].push(row);
          return acc;
        },
        {
          [INDEX_GENERATOR_POOL_PAYLOAD_KEYS.libraries]: [],
          [INDEX_GENERATOR_POOL_PAYLOAD_KEYS.samples]: []
        }
      );
    },
    buildPoolRowIndexPayload(rows) {
      return rows.map((row) => ({
        [fields.pk]: row[fields.pk],
        [fields.indexI7]: row[fields.indexI7] || "",
        [fields.indexI5]: row[fields.indexI5] || ""
      }));
    },
    validateSelectedRowsBeforeSave() {
      if (this.poolRows.length <= 1) {
        return true;
      }

      for (const row of this.poolRows) {
        if (!row[fields.indexI7]) {
          showNotification(
            `Index I7 is not set for "${row[fields.name]}".`,
            "warning"
          );
          return false;
        }
        const indexMeta = this.indexTypeMeta(row[fields.indexType]);
        if (indexMeta?.is_dual && !row[fields.indexI5]) {
          showNotification(
            `Index I5 is not set for "${row[fields.name]}".`,
            "warning"
          );
          return false;
        }
      }

      return true;
    },
    validateSelectedRowsBeforeGeneration() {
      const missingIndexTypeRows = this.poolRows.filter(
        (row) =>
          row[fields.type] === INDEX_GENERATOR_RECORD_TYPES.sampleCode &&
          !(Number(row[fields.indexType]) > 0)
      );

      if (missingIndexTypeRows.length) {
        const namesPreview = missingIndexTypeRows
          .slice(0, INDEX_GENERATOR_DEFAULTS.duplicatePreviewLimit)
          .map((row) => row[fields.name])
          .join(", ");
        const remaining =
          missingIndexTypeRows.length -
          INDEX_GENERATOR_DEFAULTS.duplicatePreviewLimit;
        const suffix = remaining > 0 ? ` (+${remaining} more)` : "";
        const message =
          `Index Type is missing for ${missingIndexTypeRows.length} selected ` +
          `sample(s): ${namesPreview}${suffix}. Set Index Type first.`;

        showNotification(message, "warning");
        return false;
      }

      return this.validatePoolCompatibility();
    },
    toggleSelection(row, event) {
      const checked = event.target.checked;

      this.setRowSelection(row, checked);
    },
    validatePoolCompatibility() {
      if (this.poolRows.length <= 1) return true;

      const first = this.poolRows[0];
      const incompatibleRow = this.poolRows.find(
        (row) => !this.rowPairCompatibility(first, row)
      );
      if (incompatibleRow) {
        if (
          String(first[fields.readLength] || "") !==
          String(incompatibleRow[fields.readLength] || "")
        ) {
          showNotification("Read lengths must be the same.", "warning");
          return false;
        }

        const firstMeta = this.indexTypeMeta(first[fields.indexType]);
        const rowMeta = this.indexTypeMeta(incompatibleRow[fields.indexType]);
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
    isCompatibleWithPool() {
      return true;
    },
    async generateIndices() {
      if (!this.validateSelectedRowsBeforeGeneration()) {
        return;
      }

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
      const libraries = libraryRows.map((row) => row[fields.pk]);
      const samples = sampleRows.map((row) => row[fields.pk]);

      this.loading = true;
      try {
        const response = await axiosRef.post(
          apiUrl(INDEX_GENERATOR_API_ENDPOINTS.generateIndices),
          {
            [INDEX_GENERATOR_POOL_PAYLOAD_KEYS.libraries]:
              JSON.stringify(libraries),
            [INDEX_GENERATOR_POOL_PAYLOAD_KEYS.samples]: JSON.stringify(samples),
            [INDEX_GENERATOR_POOL_PAYLOAD_KEYS.startCoordinate]:
              normalizedStart,
            [INDEX_GENERATOR_POOL_PAYLOAD_KEYS.direction]:
              this.selectedDirection || INDEX_GENERATOR_DEFAULTS.direction
          }
        );

        if (!response.data?.[INDEX_GENERATOR_RESPONSE_KEYS.success]) {
          showNotification(
            response.data?.[INDEX_GENERATOR_RESPONSE_KEYS.message] ||
              "Index generation failed.",
            "error"
          );
          return;
        }

        const generatedRows = (
          response.data[INDEX_GENERATOR_RESPONSE_KEYS.data] || []
        ).map((row) => this.normalizePoolRow(row));
        const previouslyGeneratedRowKeys = [...this.generatedIndexRowKeys];
        const generatedByKey = new Map(
          generatedRows.map((generated) => [
            generated[fields.rowKey],
            generated
          ])
        );

        this.generatedIndexRowKeys = generatedRows.map((row) => row[fields.rowKey]);
        this.poolRows = this.sortPoolRows(generatedRows);
        this.records = this.records.map((record) => {
          const generated = generatedByKey.get(record[fields.rowKey]);
          if (!generated) {
            if (previouslyGeneratedRowKeys.includes(record[fields.rowKey])) {
              return {
                ...record,
                [fields.indexI7]: "",
                [fields.indexI5]: ""
              };
            }
            return record;
          }
          return {
            ...record,
            [fields.selected]: this.poolRows.some(
              (row) => row[fields.rowKey] === record[fields.rowKey]
            ),
            [fields.indexI7]: generated?.[fields.indexI7] || "",
            [fields.indexI5]: generated?.[fields.indexI5] || ""
          };
        });
      } catch (error) {
        const duplicateGroups = this.getDuplicateGroups();
        if (this.isLikelyOverlapGenerationError(error, duplicateGroups)) {
          this.notifyDuplicateGroups(
            duplicateGroups,
            "Overlapping index pairs detected"
          );
          return;
        }

        this.handleApiError(error, "Index generation failed.");
      } finally {
        this.loading = false;
      }
    },
    async savePool() {
      if (!this.validateSelectedRowsBeforeSave()) {
        return;
      }
      if (!this.validatePoolCompatibility()) {
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

      this.loading = true;
      try {
        const response = await axiosRef.post(
          apiUrl(INDEX_GENERATOR_API_ENDPOINTS.savePool),
          {
            [INDEX_GENERATOR_POOL_PAYLOAD_KEYS.poolSizeId]:
              this.selectedPoolSizeId,
            [INDEX_GENERATOR_POOL_PAYLOAD_KEYS.libraries]:
              JSON.stringify(libraries),
            [INDEX_GENERATOR_POOL_PAYLOAD_KEYS.samples]: JSON.stringify(samples)
          }
        );

        if (!response.data?.[INDEX_GENERATOR_RESPONSE_KEYS.success]) {
          showNotification(
            response.data?.[INDEX_GENERATOR_RESPONSE_KEYS.message] ||
              "Saving pool failed.",
            "error"
          );
          return;
        }

        showNotification("Pool saved successfully.", "success");
        this.poolRows = [];
        this.generatedIndexRowKeys = [];
        this.selectedPoolSizeId = null;
        this.selectedPoolMultiplier = "";
        this.selectedPoolActualSize = "";
        await this.loadInitialData();
      } catch (error) {
        this.handleApiError(error, "Saving pool failed.");
      } finally {
        this.loading = false;
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
          const depth = Number(row[fields.sequencingDepth] || 0);
          if (INDEX_GENERATOR_COLOR_BALANCE.greenBases.includes(nucleotide)) {
            green += depth;
          } else if (
            INDEX_GENERATOR_COLOR_BALANCE.redBases.includes(nucleotide)
          ) {
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
          (greenPct <
            INDEX_GENERATOR_COLOR_BALANCE.warningThresholdPercent &&
            redPct >
              INDEX_GENERATOR_COLOR_BALANCE.warningDominancePercent) ||
          (redPct < INDEX_GENERATOR_COLOR_BALANCE.warningThresholdPercent &&
            greenPct > INDEX_GENERATOR_COLOR_BALANCE.warningDominancePercent);

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
  margin-left: auto;
  flex: 0 1 auto;
  min-width: 0;
  flex-wrap: nowrap;
}

.header-center {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
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
  margin-bottom: 10px;
  min-height: 38px;
  padding: 4px 8px;
}

.panel-heading-primary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  min-width: 0;
  flex: 1 1 auto;
}

.panel-heading-primary h3 {
  margin-bottom: 0;
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
  border: 1px solid rgba(0, 0, 0, 0.18);
  border-radius: 6px;
  font-size: 12px;
  padding: 0 8px;
  background: #fff;
  min-width: 0;
}

.apply-index-type-select {
  width: 208px;
}

.left-panel .panel-heading {
  flex-wrap: wrap;
  align-items: center;
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

.add-selected-pool-button,
:deep(.pool-row-remove-button),
:deep(.text-action-button) {
  border: 1px solid rgba(11, 127, 120, 0.35);
  border-radius: 8px;
  background: #ffffff;
  color: #0b6f69;
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
  min-height: 28px;
  padding: 4px 8px;
  white-space: nowrap;
}

.add-selected-pool-button:hover,
:deep(.pool-row-remove-button:hover),
:deep(.text-action-button:hover) {
  background: #f4f8f8;
  border-color: #0b7f78;
}

.apply-all-label {
  font-size: 11px;
  color: #4b5557;
  white-space: nowrap;
}

.pool-size-select {
  min-width: 90px;
  height: 36px;
  border: 1px solid rgba(0, 0, 0, 0.18);
  border-radius: 8px;
  background-color: #ffffff;
  padding: 0 12px;
  color: #333;
  font-size: 14px;
}

.pool-size-select:focus {
  outline: none;
  border-color: #0b7f78;
  box-shadow: 0 0 0 2px rgba(11, 127, 120, 0.15);
}

.header-button:disabled,
.save-pool-button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.tables-wrap {
  display: flex;
  flex-direction: row;
  gap: 4px;
  min-height: 0;
  flex: 1;
  overflow: hidden;
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
  min-width: 0;
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
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 400;
  line-height: 1.3;
  color: #333;
}

.table-scroll {
  overflow: auto;
  flex: 1;
  min-height: 0;
}

:deep(.normal-tabulator-table .tabulator-col),
:deep(.normal-tabulator-table .tabulator-col-title) {
  font-family: var(--app-font-family);
  font-size: 12px;
  font-weight: 500;
  color: #333;
}

:deep(.group-row-content) {
  display: flex;
  justify-content: flex-start;
  align-items: center;
  gap: 8px;
}

:deep(.group-row-main) {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

:deep(.group-row-title) {
  font-weight: bold;
  font-size: 13px;
  color: #333;
}

:deep(.group-row-summary) {
  font-weight: normal;
  font-size: 13px;
  margin-left: 2px;
  color: black;
}

:deep(.group-toggle-button) {
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

:deep(.group-action-buttons-container) {
  display: flex;
  gap: 5px;
}

:deep(.group-action-button) {
  display: flex;
  align-items: center;
  border: 0;
  background: transparent;
  padding: 0;
  cursor: pointer;
}

:deep(.group-action-button.text-action-button) {
  border: 1px solid #0b7f78;
  padding: 4px 8px;
}

.right-panel :deep(.tabulator-group-toggle) {
  display: none;
}

.protocol-column {
  min-width: 230px;
  width: 230px;
  max-width: 360px;
}

.index-type-column {
  min-width: 190px;
  width: 190px;
}

.index-type-select-wrapper {
  width: 100%;
}

.index-type-select-wrapper.is-disabled {
  cursor: not-allowed;
}

.index-type-select-wrapper.is-disabled select {
  pointer-events: none;
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

:deep(.sequence-text) {
  font-family: "Courier New", Courier, monospace;
}

:deep(.sequence-colored) {
  letter-spacing: 0.4px;
}

:deep(.nt) {
  font-weight: 700;
}

:deep(.nt-red) {
  color: #c53030;
}

:deep(.nt-green) {
  color: #2f855a;
}

:deep(.nt-other) {
  color: #5c6670;
}

:deep(.duplicate-index-row .tabulator-cell) {
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
  .header {
    height: auto;
    min-height: 70px;
    align-items: flex-start;
    flex-wrap: wrap;
    gap: 10px 14px;
  }

  .sticky-actions {
    width: 100%;
    margin-left: 0;
    flex-wrap: wrap;
    justify-content: flex-start;
  }

  .header-center {
    position: static;
    transform: none;
    width: 100%;
    order: 3;
  }

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

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

    <div class="table-container tables-wrap" :style="tablesWrapStyle">
      <section class="panel left-panel">
        <div class="panel-heading">
          <h3>Libraries and Samples for Pooling</h3>
          <select
            id="index-generator-pool-size"
            class="pool-size-select"
            v-model="selectedPoolSizeId"
          >
            <option :value="null">Select Pool Size</option>
            <option v-for="size in poolSizes" :key="size.id" :value="size.id">
              {{ size.name }}
            </option>
          </select>
        </div>
        <div class="table-scroll">
          <table>
            <thead>
              <tr>
                <th></th>
                <th>Name</th>
                <th>Barcode</th>
                <th>Depth (M)</th>
                <th>Length</th>
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
                  <button
                    class="group-toggle-button"
                    type="button"
                    :aria-expanded="!isRequestCollapsed(requestName)"
                  >
                    {{ isRequestCollapsed(requestName) ? "▸" : "▾" }}
                  </button>
                  {{ requestName }} ({{ groupRows.length }})
                </td>
              </tr>
              <tr
                v-for="row in groupRows"
                v-show="!isRequestCollapsed(requestName)"
                :key="row.rowKey"
              >
                <td>
                  <input
                    type="checkbox"
                    :checked="row.selected"
                    @change="toggleSelection(row, $event)"
                  />
                </td>
                <td>{{ row.name }}</td>
                <td>{{ row.barcode }}</td>
                <td>{{ row.sequencing_depth }}</td>
                <td>
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
                <td class="sequence-column">{{ row.index_i7 || "-" }}</td>
                <td class="sequence-column">{{ row.index_i5 || "-" }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <div
        class="panel-splitter"
        role="separator"
        aria-orientation="vertical"
        aria-label="Resize left and right tables"
        @mousedown="startPanelResize"
      ></div>

      <section class="panel right-panel">
        <h3>Pool (total size: {{ totalDepthRounded }} M)</h3>
        <div class="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Type</th>
                <th>Depth (M)</th>
                <th>Coord</th>
                <th>Index I7 ID</th>
                <th>Index I7</th>
                <th>Index I5 ID</th>
                <th>Index I5</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in poolRows" :key="row.rowKey">
                <td>{{ row.name }}</td>
                <td>{{ row.type }}</td>
                <td>{{ row.sequencing_depth }}</td>
                <td>{{ row.coordinate || "-" }}</td>
                <td>{{ row.index_i7_id || "-" }}</td>
                <td>{{ row.index_i7 || "-" }}</td>
                <td>{{ row.index_i5_id || "-" }}</td>
                <td>{{ row.index_i5 || "-" }}</td>
              </tr>
              <tr v-if="poolRows.length === 0">
                <td colspan="8">No records selected.</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="balance-block">
          <h4>Color Balance (i7)</h4>
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
          <h4>Color Balance (i5)</h4>
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
  urlStringStartsWith
} from "../utilities/utilityFunctions";
import iconIndexGeneratorHeader from "../assets/icons/header_index_generator.svg";

const axiosRef = createAxiosObject();
const urlStringStart = urlStringStartsWith();

export default {
  name: "IndexGenerator",
  data() {
    return {
      iconIndexGeneratorHeader,
      records: [],
      poolRows: [],
      readLengths: [],
      poolSizes: [],
      generatorIndexTypes: [],
      selectedPoolSizeId: null,
      collapsedRequests: {},
      activeResize: null,
      leftPanelWidth: 50,
      activePanelResize: false
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
    tablesWrapStyle() {
      return {
        "--left-panel-width": `${this.leftPanelWidth}%`
      };
    }
  },
  mounted() {
    this.loadInitialData();
    this.$nextTick(() => {
      this.initResizableTables();
    });
  },
  beforeUnmount() {
    document.removeEventListener("mousemove", this.onColumnResizeMove);
    document.removeEventListener("mouseup", this.onColumnResizeEnd);
    document.removeEventListener("mousemove", this.onPanelResizeMove);
    document.removeEventListener("mouseup", this.onPanelResizeEnd);
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

        this.records = (recordsResponse.data || []).map((row) =>
          this.normalizeRecord(row)
        );
        this.readLengths = readLengthsResponse.data || [];
        this.poolSizes = poolSizesResponse.data || [];
        this.generatorIndexTypes = indexTypesResponse.data || [];
        this.syncCollapsedRequests();
        this.$nextTick(() => {
          this.initResizableTables();
        });
      } catch (error) {
        handleError(error);
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
    startPanelResize(event) {
      if (window.innerWidth <= 980) {
        return;
      }

      event.preventDefault();
      this.activePanelResize = true;
      document.body.style.cursor = "col-resize";

      document.addEventListener("mousemove", this.onPanelResizeMove);
      document.addEventListener("mouseup", this.onPanelResizeEnd);
    },
    onPanelResizeMove(event) {
      if (!this.activePanelResize) {
        return;
      }

      const wrap = this.$el.querySelector(".tables-wrap");
      if (!wrap) {
        return;
      }

      const rect = wrap.getBoundingClientRect();
      if (rect.width <= 0) {
        return;
      }

      const relativeX = event.clientX - rect.left;
      const pct = (relativeX / rect.width) * 100;
      this.leftPanelWidth = Math.max(28, Math.min(72, pct));
    },
    onPanelResizeEnd() {
      this.activePanelResize = false;
      document.body.style.cursor = "";
      document.removeEventListener("mousemove", this.onPanelResizeMove);
      document.removeEventListener("mouseup", this.onPanelResizeEnd);
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
    normalizeRecord(row) {
      const type = row.barcode?.[2] || "";
      return {
        ...row,
        rowKey: `${row.record_type}:${row.pk}`,
        type,
        selected: false,
        read_length: row.read_length || "",
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
    isNanoporeProtocol(row) {
      const protocol = String(row.library_protocol_name || "").toLowerCase();
      return /oxford\s*nanopore|nanopore|\bont\b/.test(protocol);
    },
    async updateRecordField(row, field, value) {
      const normalizedValue =
        field === "read_length" || field === "index_type"
          ? Number(value) || 0
          : value;
      row[field] = normalizedValue;

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
      } catch (error) {
        handleError(error);
      }
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

      row.selected = checked;
      if (checked) {
        const candidate = this.normalizePoolRow(row);
        this.poolRows.push(candidate);
      } else {
        this.poolRows = this.poolRows.filter(
          (item) => item.rowKey !== row.rowKey
        );
      }
    },
    isCompatibleWithPool(row) {
      if (!this.poolRows.length) return true;

      const first = this.poolRows[0];
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
        return false;
      }

      return true;
    },
    async generateIndices() {
      const libraries = this.poolRows
        .filter((row) => row.record_type === "Library")
        .map((row) => row.pk);
      const samples = this.poolRows
        .filter((row) => row.record_type === "Sample")
        .map((row) => row.pk);

      try {
        const response = await axiosRef.post(
          `${urlStringStart}/api/index_generator/generate_indices/`,
          {
            libraries: JSON.stringify(libraries),
            samples: JSON.stringify(samples)
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
        const selectedKeys = new Set(generatedRows.map((row) => row.rowKey));

        this.poolRows = generatedRows;
        this.records = this.records.map((record) => {
          if (!selectedKeys.has(record.rowKey)) return record;
          const generated = generatedRows.find(
            (row) => row.rowKey === record.rowKey
          );
          return {
            ...record,
            index_i7: generated?.index_i7 || "",
            index_i5: generated?.index_i5 || ""
          };
        });
      } catch (error) {
        handleError(error);
      }
    },
    async savePool() {
      const poolCount = this.poolRows.length;

      if (poolCount > 1) {
        for (const row of this.poolRows) {
          if (!row.index_i7) {
            showNotification(
              `Index I7 is not set for \"${row.name}\".`,
              "warning"
            );
            return;
          }
          const indexMeta = this.indexTypeMeta(row.index_type);
          if (indexMeta?.is_dual && !row.index_i5) {
            showNotification(
              `Index I5 is not set for \"${row.name}\".`,
              "warning"
            );
            return;
          }
        }
      }

      const libraries = this.poolRows
        .filter((row) => row.record_type === "Library")
        .map((row) => ({
          pk: row.pk,
          index_i7: row.index_i7 || "",
          index_i5: row.index_i5 || ""
        }));
      const samples = this.poolRows
        .filter((row) => row.record_type === "Sample")
        .map((row) => ({
          pk: row.pk,
          index_i7: row.index_i7 || "",
          index_i5: row.index_i5 || ""
        }));

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
        await this.loadInitialData();
      } catch (error) {
        handleError(error);
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
          label: `C${cycle + 1}: ${greenPct}%/${redPct}%`,
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
  align-items: center;
  gap: 8px;
}

.panel-heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.pool-size-select {
  min-width: 150px;
  height: 33px;
  border: 1px solid #cfd8dc;
  border-radius: 7px;
  background-color: #ffffff;
  padding: 0 10px;
  font-size: 12px;
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
  display: grid;
  grid-template-columns: minmax(380px, var(--left-panel-width)) 10px minmax(
      380px,
      calc(100% - var(--left-panel-width))
    );
  gap: 12px;
  min-height: 0;
  flex: 1;
}

.panel-splitter {
  width: 10px;
  border-radius: 5px;
  background: linear-gradient(180deg, #d8dfdf 0%, #b8c2c2 100%);
  cursor: col-resize;
  align-self: stretch;
  transition: background 0.2s ease;
}

.panel-splitter:hover {
  background: linear-gradient(180deg, #8fa2a2 0%, #0b7f78 100%);
}

.panel {
  border: 1px solid #d9d9d9;
  border-radius: 8px;
  padding: 8px;
  min-height: 0;
  display: flex;
  flex-direction: column;
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
  font-size: 12px;
  table-layout: fixed;
}

.left-panel table {
  min-width: 1080px;
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

.group-toggle-button {
  border: none;
  background: transparent;
  cursor: pointer;
  margin-right: 6px;
  padding: 0;
  width: 16px;
  color: #0b7f78;
  font-size: 12px;
  font-weight: 700;
}

.protocol-column {
  min-width: 260px;
  width: 260px;
  max-width: 360px;
}

.index-type-column {
  min-width: 120px;
  width: 120px;
}

.sequence-column {
  min-width: 140px;
  width: 140px;
  font-family: "Courier New", Courier, monospace;
}

.balance-block {
  margin-top: 8px;
}

.balance-block h4 {
  margin: 0 0 6px 0;
}

.balance-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 4px;
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
  .pool-size-select {
    min-width: 120px;
  }

  .tables-wrap {
    grid-template-columns: 1fr;
  }

  .panel-splitter {
    display: none;
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

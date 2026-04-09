<template>
  <!-- This Tabulator table is specially optimized for handling large numbers of records. -->
  <!-- Table Element -->
  <div class="lite-tabulator-table" style="height: 100%">
    <div :id="tableId" ref="tabulatorTableRef"></div>
  </div>
</template>

<script>
import { TabulatorFull as Tabulator } from "tabulator-tables";
import * as XLSX from "xlsx";
import "tabulator-tables/dist/css/tabulator_bootstrap5.min.css";
import { markRaw } from "vue";

export default {
  name: "LiteTabulatorTable",
  props: {
    rowData: {
      type: Array
    },
    tableId: {
      type: String,
      default: "tabulatorTable"
    },
    columnDefs: {
      type: Array,
      required: true
    },
    groupBy: {
      type: [String, Function, Boolean],
      required: false,
      default: null
    },
    groupSort: {
      type: Object,
      required: false,
      default: null
    },
    groupStartOpen: {
      type: Boolean,
      required: false,
      default: true
    },
    tableOptions: {
      type: Object,
      default: () => ({})
    }
  },
  data() {
    return {
      tabulatorInstance: null,
      tableGroupsConfig: {
        groupBy: this.groupBy ?? false,
        noGroupByClass: false
      },
      scrollPosition: 0,
      lastGroupValues: []
    };
  },
  watch: {
    rowData(newData, oldData) {
      if (newData !== oldData) {
        this.updateTableData();
      }
    },
    columnDefs(newColumns, oldColumns) {
      if (newColumns !== oldColumns) {
        this.updateTableColumns();
      }
    }
  },
  mounted() {
    this.initializeTable();
  },
  methods: {
    initializeTable() {
      if (this.rowData && this.columnDefs) {
        let options = {
          data: this.rowData,
          columns: this.columnDefs,
          layout: "fitColumns",
          columnDefaults: {
            headerSort: false,
            headerFilter: false,
            editor: false,
            headerHozAlign: "center",
            resizable: "header",
            headerContextMenu: []
          },
          renderVertical: "basic",
          tooltips: true,
          resizableColumns: true,
          selectable: true,
          selectableRange: 1,
          selectableRangeColumns: false,
          selectableRangeRows: false,
          selectableRangeClearCells: false,
          editTriggerEvent: "dblclick",
          clipboard: "copy",
          clipboardCopyStyled: false,
          clipboardCopyConfig: {
            formatCells: false,
            rowHeaders: false,
            columnHeaders: false
          },
          clipboardCopyRowRange: "range",
          clipboardCopyFormatter: function (type, output) {
            if (type !== "plain") {
              return output;
            }
            const isMultiCell = output.includes("\t") || output.includes("\n");
            return isMultiCell ? `${output}\n` : output;
          },
          dependencies: {
            XLSX: XLSX
          },
          downloadConfig: {},
          groupToggleElement: "header",
          groupContextMenu: [],
          groupBy: this.tableGroupsConfig.groupBy || false,
          groupStartOpen: this.groupStartOpen,
          debugInvalidOptions: false,

          ...this.tableOptions
        };

        this.tabulatorInstance = markRaw(
          new Tabulator(`#${this.tableId}`, options)
        );

        this.tabulatorInstance.on("tableBuilt", () => {
          this.tabulatorInstance.blockRedraw();
          const tabulatorElement = this.getTabulatorElement();
          if (this.tableGroupsConfig.noGroupByClass) {
            tabulatorElement.classList.add("no-group-by");
          } else {
            tabulatorElement.classList.remove("no-group-by");
          }
          this.tabulatorInstance.restoreRedraw();
        });

        this.tabulatorInstance.on("renderComplete", () => {
          const rows = this.tabulatorInstance?.rowManager?.activeRows || [];
          this.updateGroupValuesFromRows(rows);
          if (this.tableOptions.handleRenderComplete) {
            this.tableOptions.handleRenderComplete();
          }
        });

        this.tabulatorInstance.on("columnResized", (column) => {
          if (this.tableOptions.handleColumnResized) {
            this.tableOptions.handleColumnResized(column);
          }
        });

        this.tabulatorInstance.on(
          "columnVisibilityChanged",
          (column, visible) => {
            if (this.tableOptions.handleColumnVisibilityChanged) {
              this.tableOptions.handleColumnVisibilityChanged(
                column.getField(),
                visible
              );
            }
          }
        );

        this.tabulatorInstance.on("clipboardCopied", () => {
          this.tableOptions.fakeLoadingStart();
          this.refreshTable();
          this.tableOptions.fakeLoadingStop();
        });

        this.tabulatorInstance.on("groupClick", (e, group) => {
          const scrollElement = this.tabulatorInstance.rowManager.element;
          this.scrollPosition = scrollElement.scrollTop;
        });

        this.tabulatorInstance.on(
          "groupVisibilityChanged",
          (group, visible) => {
            requestAnimationFrame(() => {
              const scrollElement = this.tabulatorInstance.rowManager.element;
              scrollElement.scrollTop = this.scrollPosition;
            });
            if (!visible) {
              this.refreshTable();
            }
          }
        );
      }
    },

    getTabulatorElement() {
      return document.getElementById(this.tableId);
    },

    updateGroupValuesFromRows(rows) {
      if (!this.tabulatorInstance || !this.groupBy || !rows) return;
      const uniqueGroups = new Set();
      rows.forEach((row) => {
        const val =
          row?._row?.data?.[this.groupBy] ?? row?.getData?.()?.[this.groupBy];
        if (val) uniqueGroups.add(val);
      });
      const sortedGroupValues = Array.from(uniqueGroups).sort((a, b) => {
        const getNum = (val) => parseInt(val?.split("_")[0], 10) || 0;
        return getNum(b) - getNum(a);
      });
      const isSameOrder =
        this.lastGroupValues.length === sortedGroupValues.length &&
        this.lastGroupValues.every((v, i) => v === sortedGroupValues[i]);
      if (!isSameOrder) {
        this.lastGroupValues = sortedGroupValues;
        this.tabulatorInstance.setGroupValues([sortedGroupValues]);
      }
    },

    updateTableData() {
      if (this.tabulatorInstance) {
        this.tabulatorInstance.replaceData(this.rowData);
      }
    },

    updateTableColumns() {
      if (this.tabulatorInstance) {
        this.tabulatorInstance.setColumns(this.columnDefs);
        this.tabulatorInstance.setGroupBy(this.groupBy || false);
        this.refreshTable();
      }
    },

    refreshTable() {
      if (this.tabulatorInstance) {
        this.tabulatorInstance.redraw();
      }
    },

    getTable() {
      return this.tabulatorInstance;
    }
  }
};
</script>

<style>
.lite-tabulator-table .tabulator {
  height: 100%;
  font-size: 12px;
  border: 1px solid #d0d0d0;
  border-radius: 8px !important;
  border-bottom-left-radius: 0px !important;
  border-bottom-right-radius: 0px !important;
}

.lite-tabulator-table .tabulator-table {
  background-color: #7788992d !important;
  z-index: 10;
}

.lite-tabulator-table .tabulator-header {
  border: none !important;
}

.lite-tabulator-table .tabulator-placeholder {
  text-align: center;
  width: 600px !important;
  height: 100%;
  background-color: #7788992d !important;
  white-space: nowrap;
}

.lite-tabulator-table .tabulator-range-active {
  border: none !important;
}

.lite-tabulator-table .tabulator-cell {
  height: 30px !important;
  line-height: 6px;
  padding: 0px !important;
  border-bottom: 1px solid #d0d0d0 !important;
  border-right: none !important;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.lite-tabulator-table .tabulator-cell.right-border {
  border-right: 1px solid #d0d0d0 !important;
}

.lite-tabulator-table .tabulator-cell.no-right-border {
  border-right: none !important;
}

.lite-tabulator-table .tabulator-cell.disable-range-selection {
  pointer-events: none;
}

.lite-tabulator-table .tabulator-cell.tabulator-range-selected {
  background-color: #c0e7fd !important;
  color: #003757 !important;
  border-bottom: 1px solid #d0d0d0 !important;
}

.lite-tabulator-table .tabulator-cell.tabulator-editing {
  background-color: lightgoldenrodyellow !important;
  padding-left: 10px !important;
}

.lite-tabulator-table .tabulator-cell.tabulator-editable {
  cursor: pointer;
}

.lite-tabulator-table .tabulator-cell.tabulator-frozen {
  z-index: 1 !important;
}

.lite-tabulator-table .tabulator-col {
  border-right: 1px solid #d0d0d0 !important;
  border-bottom: 1px solid #d0d0d0 !important;
}

.lite-tabulator-table .tabulator-col-group-cols {
  border: none !important;
  border-top: 1px solid #d0d0d0 !important;
}

.lite-tabulator-table .tabulator-col-content {
  padding: 5px !important;
}

.lite-tabulator-table .tabulator-row {
  min-height: 0;
  height: 30px !important;
}

.lite-tabulator-table .tabulator-row[role="row"] {
  border: none !important;
}

.lite-tabulator-table .tabulator-row:not(.tabulator-group) {
  background-color: white !important;
  border-right: 1px solid #d0d0d0 !important;
}

.lite-tabulator-table .tabulator-row:not(.tabulator-group):hover {
  mix-blend-mode: multiply;
}

.lite-tabulator-table .tabulator-row.tabulator-group {
  margin-top: 3px;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  background-color: white !important;
  border-top: 1px solid #d0d0d0 !important;
  border-bottom: 1px solid #d0d0d0 !important;
  z-index: 20;
}

.lite-tabulator-table .tabulator-row.tabulator-group:hover {
  background-color: white !important;
}

.lite-tabulator-table .tabulator-row.tabulator-group:has(.request-approval-pending-marker) {
  background-color: #fff1f1 !important;
}

.lite-tabulator-table .tabulator-row.tabulator-group:has(.request-approval-pending-marker):hover {
  background-color: #fff1f1 !important;
}

.lite-tabulator-table .tabulator-row:hover .group-action-buttons-container {
  display: flex;
}

.lite-tabulator-table .tabulator-header-filter input {
  height: 24px;
  font-size: 12px !important;
  border: 1px solid #d0d0d0 !important;
}

.lite-tabulator-table .tabulator-group.hidden-group {
  display: none !important;
}

.lite-tabulator-table .no-group-by .tabulator-row-odd:nth-child(1) {
  margin-top: 5px;
}

.lite-tabulator-table
  .no-group-by
  .tabulator-row-odd:nth-child(1)
  .tabulator-cell {
  border-top: 1px solid #d0d0d0 !important;
}

.lite-tabulator-table .checkbox-column:not(.tabulator-col) {
  padding: 10px 0px !important;
}

.lite-tabulator-table .title-field-group > .tabulator-col-content > div > div {
  font-weight: 600 !important;
  color: rgb(99, 99, 99) !important;
}
</style>

<!--
Add VirtualDOM support
Allow opening only 3 groups at a time
-->


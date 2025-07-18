<template>
  <!-- Table Element -->
  <div id="tabulatorTable" ref="tabulatorTableRef"></div>
</template>

<script>
import { TabulatorFull as Tabulator } from "tabulator-tables";
import * as XLSX from "xlsx";
import "tabulator-tables/dist/css/tabulator_bootstrap5.min.css";
import { showNotification } from "../utils/utilities";
import { markRaw } from "vue";

export default {
  name: "LiteTabulatorTable",
  props: {
    rowData: {
      type: Array
    },
    columnDefs: {
      type: Array,
      required: true
    },
    groupValues: {
      type: Array,
      required: false,
      default: () => []
    },
    groupBy: {
      type: String,
      required: true
    },
    groupSort: {
      type: Object,
      required: false
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
      tableFiltersState: {
        typesIn: [
          { field: "type", type: "=", value: "L" },
          { field: "type", type: "=", value: "S" }
        ],
        typesNotIn: []
      },
      tableRangeBoundsState: {
        start: null,
        end: null
      },
      tableGroupsToggleState: 0,
      tableGroupsConfig: {
        groupBy: this.groupBy,
        noGroupByClass: false
      },
      tableColumnWidths: {},
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
    },
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
          reactiveData: true,
          layout: "fitColumns",
          columnDefaults: {
            headerSort: false,
            headerFilter: false,
            editor: false,
            headerHozAlign: "center",
            resizable: "header",
            headerContextMenu: []
          },
          tooltips: true,
          resizableColumns: true,
          groupValues: [this.groupValues],
          groupToggleElement: "header",
          selectable: true,
          selectableRange: 1,
          selectableRangeColumns: false,
          selectableRangeRows: false,
          selectableRangeClearCells: false,
          editTriggerEvent: "dblclick",
          clipboard: true,
          clipboardCopyStyled: false,
          clipboardCopyConfig: {
            formatCells: false,
            rowHeaders: false,
            columnHeaders: false
          },
          clipboardCopyRowRange: "range",
          clipboardCopyFormatter: function (type, output) {
            if (type == "plain") {
              output += "\n";
            }
            return output;
          },
          dependencies: {
            XLSX: XLSX
          },
          downloadConfig: {},
          groupContextMenu: [],
          groupBy: this.tableGroupsConfig.groupBy,
          groupStartOpen: this.groupStartOpen,
          ...this.tableOptions
        };

        this.tabulatorInstance = markRaw(new Tabulator("#tabulatorTable", options));

        this.tabulatorInstance.on("tableBuilt", () => {
          this.tabulatorInstance.blockRedraw();

          const tabulatorElement = this.getTabulatorElement();
          if (this.tableGroupsConfig.noGroupByClass) {
            tabulatorElement.classList.add("no-group-by");
          } else {
            tabulatorElement.classList.remove("no-group-by");
          }

          this.tabulatorInstance.setGroupBy(this.tableGroupsConfig.groupBy);

          let typesNotIn = this.tableFiltersState.typesNotIn;
          let flatFilters = Object.entries(this.tableFiltersState)
            .filter(([key, value]) => {
              if (key === "typesNotIn") return false;
              return Array.isArray(value)
                ? value.length > 0
                : Object.keys(value).length > 0;
            })
            .map(([key, value]) => value);

          if (typesNotIn.length > 0) {
            flatFilters.push(...typesNotIn);
          }
          this.tabulatorInstance.setFilter(flatFilters);

          const columns = this.tabulatorInstance.getColumns();
          columns.forEach((column) => {
            const field = column.getField();
            if (this.tableColumnWidths[field]) {
              column.setWidth(this.tableColumnWidths[field]);
            }
          });
          this.tabulatorInstance.restoreRedraw();
        });

        this.tabulatorInstance.on("columnResized", (column) => {
          const field = column.getField();
          const width = column.getWidth();
          this.tableColumnWidths[field] = width;
        });

        this.tabulatorInstance.on("rangeChanged", (range) => {
          console.log(range)
          const start = range.getBounds().start;
          const end = range.getBounds().end;
          this.tableRangeBoundsState = {
            start: start,
            end: end
          };
        });

        this.tabulatorInstance.on("clipboardCopied", () => {
          this.tableOptions.fakeLoadingStart();
          this.refreshTable();
          this.tableOptions.fakeLoadingStop();
        });

      }
    },

    getTabulatorElement() {
      return document.getElementById("tabulatorTable");
    },

    updateTableData() {
      if (this.tabulatorInstance) {
        this.tabulatorInstance.setData(this.rowData);
      }
    },

    updateTableColumns() {
      if (this.tabulatorInstance) {
        this.tabulatorInstance.setColumns(this.columnDefs);
        if (this.groupBy)
          this.tabulatorInstance.setGroupBy(this.groupBy);
        this.refreshTable();
      }
    },

    filterTableData(operation, keyword) {
      let typesIn = this.tableFiltersState.typesIn;
      let typesNotIn = this.tableFiltersState.typesNotIn;
      switch (operation) {
        case "search_incoming_libraries_and_samples":
          if (keyword !== "") {
            this.tableFiltersState.search = [
              [
                { field: "name", type: "like", value: keyword },
                { field: "request_name", type: "like", value: keyword },
                { field: "barcode", type: "like", value: keyword },
                {
                  field: "nucleic_acid_type_name",
                  type: "like",
                  value: keyword
                },
                {
                  field: "library_protocol_name",
                  type: "like",
                  value: keyword
                },
                { field: "comments", type: "like", value: keyword },
                { field: "comments_facility", type: "like", value: keyword }
              ]
            ];
          } else {
            delete this.tableFiltersState.search;
          }
          break;

        case "search_library_preparation":
          if (keyword !== "") {
            this.tableFiltersState.search = [
              [
                { field: "name", type: "like", value: keyword },
                { field: "request_name", type: "like", value: keyword },
                { field: "barcode", type: "like", value: keyword },
                {
                  field: "comments_library_sample",
                  type: "like",
                  value: keyword
                },
                { field: "comments", type: "like", value: keyword },
                { field: "comments_facility", type: "like", value: keyword }
              ]
            ];
          } else {
            delete this.tableFiltersState.search;
          }
          break;

        case "search_pooling":
          if (keyword !== "") {
            this.tableFiltersState.search = [
              [
                { field: "name", type: "like", value: keyword },
                { field: "request_name", type: "like", value: keyword },
                { field: "pool_name", type: "like", value: keyword },
                { field: "barcode", type: "like", value: keyword }
              ]
            ];
          } else {
            delete this.tableFiltersState.search;
          }
          break;

        case "showLibraries":
          const foundInL = typesIn.find((item) => item.value === "L");
          if (keyword === true && !foundInL) {
            typesIn.push({ field: "type", type: "=", value: "L" });
            typesNotIn = typesNotIn.filter((item) => item.value !== "L");
          } else if (keyword === false && foundInL) {
            typesIn = typesIn.filter((item) => item.value !== "L");
            typesNotIn.push({ field: "type", type: "!=", value: "L" });
          }
          this.tableFiltersState.typesIn = typesIn;
          this.tableFiltersState.typesNotIn = typesNotIn;
          break;

        case "showSamples":
          const foundInS = typesIn.find((item) => item.value === "S");
          if (keyword === true && !foundInS) {
            typesIn.push({ field: "type", type: "=", value: "S" });
            typesNotIn = typesNotIn.filter((item) => item.value !== "S");
          } else if (keyword === false && foundInS) {
            typesIn = typesIn.filter((item) => item.value !== "S");
            typesNotIn.push({ field: "type", type: "!=", value: "S" });
          }
          this.tableFiltersState.typesIn = typesIn;
          this.tableFiltersState.typesNotIn = typesNotIn;
          break;

        case "onlySamplesSubmitted":
          if (keyword === true) {
            this.tableFiltersState.onlySamplesSubmitted = {
              field: "samples_submitted",
              type: "=",
              value: keyword
            };
          } else {
            delete this.tableFiltersState.onlySamplesSubmitted;
          }
          break;

        case "onlyGmo":
          if (keyword === true) {
            this.tableFiltersState.onlyGmo = {
              field: "gmo",
              type: "=",
              value: true
            };
          } else {
            delete this.tableFiltersState.onlyGmo;
          }
          break;

        default:
          break;
      }

      let flatFilters = Object.entries(this.tableFiltersState)
        .filter(([key, value]) => {
          if (key === "typesNotIn") return false;
          return Array.isArray(value)
            ? value.length > 0
            : Object.keys(value).length > 0;
        })
        .map(([key, value]) => value);

      if (typesNotIn.length > 0) {
        flatFilters.push(...typesNotIn);
      }

      this.tabulatorInstance.setFilter(flatFilters);
    },

    showAllGroups() {
      if (this.tabulatorInstance) {
        this.tabulatorInstance.blockRedraw();
        this.tabulatorInstance.getGroups().forEach((group) => group.show());
        this.tabulatorInstance.restoreRedraw();
      }
    },

    hideAllGroups() {
      if (this.tabulatorInstance) {
        this.tabulatorInstance.blockRedraw();
        this.tabulatorInstance.getGroups().forEach((group) => group.hide());
        this.tabulatorInstance.restoreRedraw();
      }
    },

    getTableGroupsToggleState() {
      return this.tableGroupsToggleState;
    },

    toggleGroups(goToInitial) {
      if (goToInitial === true || this.tableGroupsToggleState == 2) {
        this.tableGroupsToggleState = 0;
      } else {
        const allGroups = this.tabulatorInstance.getGroups();
        const closedGroupCount = allGroups.filter(
          (group) => !group._group.visible
        ).length;

        if (closedGroupCount === allGroups.length) {
          this.tableGroupsToggleState = 2;
        } else if (closedGroupCount === 0) {
          this.tableGroupsToggleState = 1;
        } else {
          this.tableGroupsToggleState = 0;
        }
      }

      switch (this.tableGroupsToggleState) {
        case 0:
          this.showAllGroups();
          this.tableGroupsConfig.groupBy = this.groupBy;
          this.tableGroupsConfig.noGroupByClass = false;
          break;

        case 1:
          this.hideAllGroups();
          this.tableGroupsConfig.groupBy = this.groupBy;
          this.tableGroupsConfig.noGroupByClass = false;
          break;

        case 2:
          this.showAllGroups();
          this.tableGroupsConfig.groupBy = false;
          this.tableGroupsConfig.noGroupByClass = true;
          break;
      }

      this.refreshTable();
    },

    refreshTable() {
      if (this.tabulatorInstance) {
        this.tabulatorInstance.redraw();
      }
    },

    recreateTable() {
      const oldTable = document.getElementById("tabulatorTable");
      const newTable = oldTable.cloneNode(false);
      oldTable.replaceWith(newTable);
      this.$nextTick(() => {
        this.initializeTable();
      });
    },

    getTable() {
      return this.tabulatorInstance;
    },
  }
};
</script>

<style>
.tabulator {
  height: 100%;
  font-size: 12px;
  border: 1px solid #d0d0d0;
  border-radius: 4px !important;
}

.tabulator-table {
  background-color: #7788992d !important;
  z-index: 10;
}

.tabulator-header {
  border: none !important;
}

.tabulator-placeholder {
  text-align: center;
  width: 600px !important;
  background-color: #7788992d !important;
  white-space: nowrap;
}

.tabulator-range-active {
  border: none !important;
}

.tabulator-cell {
  height: 30px !important;
  line-height: 6px;
  padding: 0px !important;
  border-bottom: 1px solid #d0d0d0 !important;
  border-right: none !important;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.tabulator-cell.right-border {
  border-right: 1px solid #d0d0d0 !important;
}

.tabulator-cell.no-right-border {
  border-right: none !important;
}

.tabulator-cell.disable-range-selection {
  pointer-events: none;
}

.tabulator-cell.tabulator-range-selected {
  background-color: #c0e7fd !important;
  color: #003757 !important;
  border-bottom: 1px solid #d0d0d0 !important;
}

.tabulator-cell.tabulator-editing {
  background-color: lightgoldenrodyellow !important;
  padding-left: 10px !important;
}

.tabulator-cell.tabulator-editable {
  cursor: pointer;
}

.tabulator-cell.tabulator-frozen {
  z-index: 1 !important;
}

.tabulator-cell.user-entry-column {
  background-color: #ffebee;
  color: #c62828;
}

.tabulator-cell.facility-entry-column {
  background-color: #c4ecc2;
  color: #388e3c;
}

.tabulator-cell.facility-entry-column.disable-editing {
  background-color: #b6dbb4;
}

.tabulator-col {
  border-right: 1px solid #d0d0d0 !important;
  border-bottom: 1px solid #d0d0d0 !important;
}

.tabulator-col-group-cols {
  border: none !important;
  border-top: 1px solid #d0d0d0 !important;
}

.tabulator-col-content {
  padding: 5px !important;
}

.tabulator-row {
  min-height: 0;
  height: 30px !important;
}

.tabulator-row[role="row"] {
  border: none !important;
}

.tabulator-row:not(.tabulator-group) {
  background-color: white !important;
}

.tabulator-row:not(.tabulator-group):hover {
  mix-blend-mode: multiply;
}

.tabulator-row.tabulator-group {
  margin-top: 3px;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  background-color: white;
  border-top: 1px solid #d0d0d0 !important;
  border-bottom: 1px solid #d0d0d0 !important;
  z-index: 20;
}

.tabulator-row.tabulator-group:hover {
  background-color: white;
}

.tabulator-row:hover .group-action-buttons-container {
  display: flex;
}

.tabulator-header-filter input {
  height: 24px;
  font-size: 12px !important;
  border: 1px solid #d0d0d0 !important;
}

.tabulator-group.hidden-group {
  display: none !important;
}

.no-group-by .tabulator-row-odd:nth-child(1) {
  margin-top: 5px;
}

.no-group-by .tabulator-row-odd:nth-child(1) .tabulator-cell {
  border-top: 1px solid #d0d0d0 !important;
}

.checkbox-column:not(.tabulator-col) {
  padding: 10px 0px !important;
}

.title-field-group>.tabulator-col-content>div>div {
  font-weight: 600 !important;
  color: rgb(99, 99, 99) !important;
}
</style>

<!--
scroll to focused cell after copy
select all, change columns checkboxes delay
resize width of table or collapse/expand side modules should refresh the table width
show hover tooltips with use of a library
-->

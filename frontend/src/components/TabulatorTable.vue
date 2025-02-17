<template>
  <!-- Table Element -->
  <div id="tabulatorTable" ref="tabulatorTableRef"></div>

  <!-- Errors window -->
  <div v-if="showErrorsWindow" class="popup-overlay">
    <div class="popup-container" :style="{
      height: errorsPopupContents.errorsPopupHeight + 'px',
      width: errorsPopupContents.errorsPopupWidth + 'px'
    }">
      <div class="popup-header">
        <svg style="display: block" fill="none" width="42px" height="42px" version="1.1"
          xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
          <g>
            <path opacity="0.3"
              d="M3 9.22843V14.7716C3 15.302 3.21071 15.8107 3.58579 16.1858L7.81421 20.4142C8.18929 20.7893 8.69799 21 9.22843 21H14.7716C15.302 21 15.8107 20.7893 16.1858 20.4142L20.4142 16.1858C20.7893 15.8107 21 15.302 21 14.7716V9.22843C21 8.69799 20.7893 8.18929 20.4142 7.81421L16.1858 3.58579C15.8107 3.21071 15.302 3 14.7716 3H9.22843C8.69799 3 8.18929 3.21071 7.81421 3.58579L3.58579 7.81421C3.21071 8.18929 3 8.69799 3 9.22843Z"
              fill="#323232" />
            <path
              d="M3 9.22843V14.7716C3 15.302 3.21071 15.8107 3.58579 16.1858L7.81421 20.4142C8.18929 20.7893 8.69799 21 9.22843 21H14.7716C15.302 21 15.8107 20.7893 16.1858 20.4142L20.4142 16.1858C20.7893 15.8107 21 15.302 21 14.7716V9.22843C21 8.69799 20.7893 8.18929 20.4142 7.81421L16.1858 3.58579C15.8107 3.21071 15.302 3 14.7716 3H9.22843C8.69799 3 8.18929 3.21071 7.81421 3.58579L3.58579 7.81421C3.21071 8.18929 3 8.69799 3 9.22843Z"
              stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
            <path d="M12 8V13" stroke="white" stroke-width="1.5" stroke-linecap="round" />
            <path d="M12 16V15.9888" stroke="white" stroke-width="1.5" stroke-linecap="round" />
          </g>
        </svg>
        <span class="popup-title">Paste Error</span>
        <button class="popup-close-button" @click="showErrorsWindow = false">
          &times;
        </button>
      </div>
      <div class="popup-body">
        <div> Following errors occured while pasting, please try again after fixing:</div>
        <div v-if="errorsPopupContents.errorsList?.length" class="popup-scrollable-content">
          <ol style="padding-left: 25px;">
            <li v-for="(item, index) in errorsPopupContents.errorsList" :key="index">
              {{ item.barcode + " ➜ " }}
              <span style="font-weight: bold">{{ item.message }}</span>
            </li>
          </ol>
        </div>
      </div>
      <div class="popup-footer">
        <button class="popup-button" @click="showErrorsWindow = false">OK</button>
      </div>
    </div>
  </div>
</template>

<script>
import { TabulatorFull as Tabulator } from "tabulator-tables";
import * as XLSX from "xlsx";
import "tabulator-tables/dist/css/tabulator_bootstrap5.min.css";
import { showNotification } from "../utils/utilities";

export default {
  name: "TabulatorTable",
  props: {
    rowData: {
      type: Array
    },
    columnDefs: {
      type: Array,
      required: true
    },
    tableOptions: {
      type: Object,
      default: () => ({})
    }
  },
  data() {
    return {
      tabulatorInstance: null,
      previousData: null,
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
        groupBy: "request_name",
        noGroupByClass: false
      },
      tableEachGroupsToggleState: [],
      tableColumnWidths: {},
      showErrorsWindow: false,
      errorsPopupContents: {
        errorsList: [],
        errorsPopupHeight: 220,
        errorsPopupWidth: 600,
      },
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
  beforeDestroy() {
    document.removeEventListener("keydown", this.handleKeyDown);
  },
  methods: {
    initializeTable() {
      if (this.rowData && this.columnDefs) {
        const options = {
          data: this.rowData,
          columns: this.columnDefs,
          layout: "fitColumns",
          columnDefaults: {
            headerSort: true,
            headerFilter: false,
            editor: false,
            headerHozAlign: "center",
            resizable: "header",
            headerContextMenu: []
          },
          tooltips: true,
          resizableColumns: true,
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
          clipboardPasteAction: "range",
          clipboardCopyFormatter: function (type, output) {
            if (type == "plain") {
              output += "\n";
            }
            return output;
          },
          clipboardPasteParser: async (clipboard) => {
            this.errorsPopupContents.errorsList = [];
            const errors = [];
            const selectedRanges = this.tabulatorInstance.getRanges();
            if (!selectedRanges?.length) {
              showNotification("Please select a range before pasting.", "warning");
              return [];
            }

            const { top: rowStart, bottom: rowEnd, left: colStart, right: colEnd } = selectedRanges[0]._range;
            const visibleColumns = this.tabulatorInstance.getColumns().filter(col => col._column.visible);
            let pastedData = clipboard.split(/\r?\n/).map(row => row.split("\t"));
            if (pastedData[pastedData.length - 1]?.length === 1 && pastedData[pastedData.length - 1][0] === "")
              pastedData.pop();

            const pastedColumnCount = Math.max(...pastedData.map(row => row.length));
            const rangeColumns = visibleColumns.slice(colStart, colStart + pastedColumnCount);
            const batchUpdates = {};
            const isSingleCell = rowStart === rowEnd && colStart === colEnd;
            let targetRequestName = null;
            let hasValidationErrors = false;
            let changedRows = new Set();
            let changedCols = new Set();

            if (isSingleCell) {
              const selectedRow = this.tabulatorInstance.getRowFromPosition(rowStart + 1);
              targetRequestName = selectedRow?.getData().request_name;
            }

            pastedData.forEach((pastedRow, rowOffset) => {
              const tableRow = this.tabulatorInstance.getRowFromPosition(rowStart + rowOffset + 1);
              if (!tableRow) return;
              if (isSingleCell && tableRow.getData().request_name !== targetRequestName) return;

              let cellNumber = 0;
              const rowData = tableRow.getData();
              const updatedRow = { ...rowData };

              pastedRow.forEach((cellValue, colOffset) => {
                const column = rangeColumns[colOffset];
                if (!column) return;
                const field = column.getField();
                const columnDef = column.getDefinition();
                const cell = tableRow.getCell(field);
                cellNumber++;

                if (columnDef.editor === false || cell.getElement().classList.contains("disable-editing")) {
                  hasValidationErrors = true;
                  errors.push({
                    barcode: rowData.barcode,
                    message: `Cell ${cellNumber}: Editing is not allowd in this cell.`
                  });
                  return;
                }

                try {
                  updatedRow[field] = this.validateCellValue(cellValue, columnDef, rowData);
                  changedRows.add(rowStart + rowOffset + 1);
                  changedCols.add(colStart + colOffset);
                } catch (error) {
                  hasValidationErrors = true;
                  errors.push({
                    barcode: rowData.barcode,
                    message: `Cell ${cellNumber}: ${error.message}`
                  });
                }
              });

              batchUpdates[rowData.barcode] = updatedRow;
            });

            if (hasValidationErrors) {
              if (errors.length) {
                this.errorsPopupContents = {
                  errorsList: errors,
                  errorsPopupHeight: Math.min(420, 260 + errors.length * 34),
                  errorsPopupWidth: 600
                };
                this.showErrorsWindow = true;
                return [];
              }
              return [];
            }

            const updatedRowsArray = Object.values(batchUpdates);
            if (updatedRowsArray.length) {
              this.tabulatorInstance.updateData(updatedRowsArray);

              if (changedRows.size && changedCols.size) {
                const startRow = this.tabulatorInstance.getRowFromPosition(Math.min(...changedRows));
                const endRow = this.tabulatorInstance.getRowFromPosition(Math.max(...changedRows));
                const startCol = visibleColumns[Math.min(...changedCols)];
                const endCol = visibleColumns[Math.max(...changedCols)];

                if (startRow && endRow && startCol && endCol) {
                  this.tabulatorInstance.addRange(
                    startRow.getCell(startCol.getField()),
                    endRow.getCell(endCol.getField())
                  );
                }
              }
            }

            return [];
          },
          dependencies: {
            XLSX: XLSX
          },
          downloadConfig: {},
          groupContextMenu: [],
          groupBy: this.tableGroupsConfig.groupBy,
          groupStartOpen: (value) => {
            const groupState = this.tableEachGroupsToggleState.find(
              (item) => item.group === value
            );
            return groupState ? !groupState.isClose : true;
          },
          ...this.tableOptions
        };

        this.tabulatorInstance = new Tabulator("#tabulatorTable", options);

        this.tabulatorInstance.on("tableBuilt", () => {
          document.addEventListener("keydown", this.handleKeyDown);

          if (
            this.tableRangeBoundsState.start &&
            this.tableRangeBoundsState.end
          ) {
            let start = this.tableRangeBoundsState.start;
            let end = this.tableRangeBoundsState.end;
            this.tabulatorInstance.addRange(
              start.getComponent(),
              end.getComponent()
            );
          }

          if (!document.querySelector(".button-popup-container")) {
            document
              .getElementsByClassName("tabulator-range-selected")[0]
              ?.click();
          }

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
        });

        this.previousData = JSON.stringify(this.rowData);

        this.tabulatorInstance.on("dataChanged", (updatedData) => {
          const currentData = JSON.stringify(updatedData);
          const previousParsed = JSON.parse(this.previousData);
          const batchChanges = [];

          updatedData.forEach((row, index) => {
            const oldRow = previousParsed[index] || {};
            const changedFields = {};

            Object.keys(row).forEach((key) => {
              if (
                key !== "selected" &&
                key !== "samples_submitted" &&
                key !== "quality_check"
              ) {
                if (row[key] !== oldRow[key]) {
                  changedFields[key] = row[key] === "" ? null : row[key];
                }
              }
            });

            if (Object.keys(changedFields).length > 0) {
              batchChanges.push({
                pk: row.pk,
                record_type: row.record_type,
                ...changedFields
              });
            }
          });

          this.previousData = currentData;

          if (batchChanges.length > 0) {
            this.tableOptions.onBatchCellValueChanged(batchChanges);
          }
        });

        this.tabulatorInstance.on("columnResized", (column) => {
          const field = column.getField();
          const width = column.getWidth();
          this.tableColumnWidths[field] = width;
          this.refreshTable();
        });

        this.tabulatorInstance.on("rangeChanged", (range) => {
          const start = range.getBounds().start;
          const end = range.getBounds().end;
          this.tableRangeBoundsState = {
            start: start,
            end: end
          };
        });

        this.tabulatorInstance.on("clipboardCopied", () => {
          this.tableOptions.fakeLoadingStart();
          this.recreateTable();
          this.tableOptions.fakeLoadingStop();
        });

        this.tabulatorInstance.on("clipboardPasted", () => {
          if (this.errorsPopupContents.errorsList.length == 0) {
            this.tableOptions.fakeLoadingStart();
            this.tableOptions.fakeLoadingStop();
          }
        });

        this.tabulatorInstance.on(
          "groupVisibilityChanged",
          (group, visible) => {
            const groupValue = group.getKey();

            const index = this.tableEachGroupsToggleState.findIndex(
              (item) => item.group === groupValue
            );

            if (index !== -1) {
              this.tableEachGroupsToggleState[index].isClose = !visible;
            } else {
              this.tableEachGroupsToggleState.push({
                group: groupValue,
                isClose: !visible
              });
            }

            const rows = this.tabulatorInstance.getRows();
            if (rows.length > 0) {
              const firstRow = rows[0];
              const cells = firstRow.getCells();
              if (cells.length > 0) {
                const topLeftCell = cells[0];
                this.tabulatorInstance.addRange(topLeftCell, topLeftCell);
              }
            }
          }
        );
      }
    },

    getTabulatorElement() {
      return document.getElementById("tabulatorTable");
    },

    // Tabulator Bug: When we use table.setData() or table.replaceData(), range paste does not work and gives "No bounds defined for this range" error.
    // Hence we need to destroy and recreate table again, when using these methods.
    updateTableData() {
      if (this.tabulatorInstance) {
        this.tabulatorInstance.setData(this.rowData);
      }
    },

    updateTableColumns() {
      if (this.tabulatorInstance) {
        this.tabulatorInstance.setColumns(this.columnDefs);
        this.getTabulatorElement().classList.remove("no-group-by");
        this.showAllGroups();
        this.tabulatorInstance.setGroupBy("request_name");
        this.tableRangeBoundsState = {
          start: null,
          end: null
        };
        this.recreateTable();
      }
    },

    filterTableData(operation, keyword) {
      let typesIn = this.tableFiltersState.typesIn;
      let typesNotIn = this.tableFiltersState.typesNotIn;
      switch (operation) {
        case "search":
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
          this.tableGroupsConfig.groupBy = "request_name";
          this.tableGroupsConfig.noGroupByClass = false;
          break;

        case 1:
          this.hideAllGroups();
          this.tableGroupsConfig.groupBy = "request_name";
          this.tableGroupsConfig.noGroupByClass = false;
          break;

        case 2:
          this.showAllGroups();
          this.tableGroupsConfig.groupBy = false;
          this.tableGroupsConfig.noGroupByClass = true;
          break;
      }

      this.recreateTable();
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

    handleKeyDown(event) {
      const isDeleteOrBackspace =
        event.key === "Delete" || event.key === "Backspace";
      const isPrintableKey =
        event.key.length === 1 &&
        !event.ctrlKey &&
        !event.metaKey &&
        !event.altKey;

      let selectedRanges = this.tabulatorInstance.getRanges();
      let selectedRangesData = this.tabulatorInstance.getRangesData();
      let isRangeSelected =
        selectedRangesData.length > 0 &&
        (selectedRangesData[0].length > 0 ||
          Object.keys(selectedRangesData[0][0]).length > 0);

      if (
        document.activeElement &&
        document.activeElement.tagName === "INPUT"
      ) {
        return;
      }

      if (isDeleteOrBackspace) {
        if (!isRangeSelected) return;
        const clearableFields = [
          "measuring_unit_facility",
          "measured_value_facility",
          "sample_volume_facility",
          "size_distribution_facility",
          "rna_quality",
          "gmo_facility",
          "comments_facility"
        ];
        let firstRangeCells = selectedRanges[0]
          ? selectedRanges[0].getCells()
          : [];
        firstRangeCells.forEach((row) => {
          row.forEach((cell) => {
            let columnField = cell.getField();
            let disabledEditing = cell
              .getElement()
              .classList.contains("disable-editing");

            if (clearableFields.includes(columnField) && !disabledEditing) {
              cell.setValue("");
            }
          });
        });
        event.preventDefault();
        return;
      }

      if (isPrintableKey) {
        let firstRangeCells = selectedRanges[0]
          ? selectedRanges[0].getCells()
          : [];
        let firstCell = firstRangeCells[0][0];
        if (firstCell) {
          let disabledEditing = firstCell
            .getElement()
            .classList.contains("disable-editing");
          if (disabledEditing) {
            showNotification("Editing is disabled for this field.", "warning");
            return;
          }
          firstCell.edit();

          const input = document.activeElement;
          if (input && input.tagName === "INPUT") {
            input.value = "";
            input.dispatchEvent(new Event("input", { bubbles: true }));
          }
        }
      }
    },

    validateCellValue(value, columnDef, rowData) {
      const editorType = columnDef.editor;

      switch (editorType) {
        case "number":
          const numValue = parseFloat(value);
          const editorParamsNumber = columnDef.editorParams || {};
          const min = editorParamsNumber.min;
          const max = editorParamsNumber.max;
          if (isNaN(numValue) && value !== "") {
            throw new Error("Invalid numeric format, please check!");
          }
          if ((min !== undefined && numValue < min) || (max !== undefined && numValue > max)) {
            throw new Error(`Value must be between ${min} and ${max}.`);
          }
          return value == "" ? "" : numValue;

        case "list":
          const editorParamsList =
            typeof columnDef.editorParams === "function"
              ? columnDef.editorParams({
                getRow: () => ({ getData: () => rowData })
              })
              : columnDef.editorParams;
          const options =
            editorParamsList?.values?.map((opt) =>
              typeof opt === "object" ? opt.value : opt
            ) || [];
          const optionLabels =
            editorParamsList?.values?.map((opt) =>
              typeof opt === "object" ? opt.label : opt
            ) || [];
          if (!options.includes(value)) {
            throw new Error(
              `Invalid option! valid choices are ➜ \n${optionLabels.join(
                ", "
              )}.`
            );
          }
          return value;

        case "input":
        default:
          if (columnDef.validator) {
            const validationResult = columnDef.validator(value);
            if (validationResult !== true) {
              throw new Error(
                validationResult || "Invalid data format, please check!"
              );
            }
          }
          return value;
      }
    }
  }
};
</script>

<style>
.tabulator {
  font-size: 12px;
  border: 1px solid grey;
  border-radius: 4px !important;
}

.tabulator-table {
  height: 544px;
  background-color: #7788992d !important;
  z-index: 10;
}

.tabulator-header {
  border: none !important;
}

.tabulator-tableholder {
  overflow-x: scroll !important;
}

.tabulator-placeholder {
  text-align: center;
  width: 600px !important;
  height: 544px !important;
  background-color: #7788992d !important;
  white-space: nowrap;
}

.tabulator-cell {
  height: 35px !important;
  line-height: 10px;
  padding: 0px !important;
  border-bottom: 1px solid grey !important;
  border-right: 1px solid grey !important;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.tabulator-cell.no-right-border {
  border-right: none !important;
}

.tabulator-cell.disable-range-selection {
  pointer-events: none;
}

.tabulator-cell.tabulator-range-selected {
  background-color: #c0e7fd !important;
  border: none !important;
  color: #003757 !important;
  border-bottom: 1px solid grey !important;
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

.tabulator-cell.details-column {
  font-weight: bold !important;
  color: darkslategrey !important;
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
  font-size: 13px;
  border-right: 1px solid grey !important;
  border-bottom: 1px solid grey !important;
}

.tabulator-col-vertical:not(.tabulator-frozen) {
  border-top: 1px solid grey !important;
}

.tabulator-col-group-cols {
  border: none !important;
}

.tabulator-row {
  min-height: 0;
  height: 35px !important;
}

.tabulator-row[role="row"] {
  border: none !important;
}

.tabulator-row:not(.tabulator-group):nth-child(even),
.tabulator-row:not(.tabulator-group):nth-child(odd) {
  background-color: white !important;
}

.tabulator-row.tabulator-group {
  margin-top: 5px;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  background-color: #faf1d2;
  z-index: 20;
}

.tabulator-row.tabulator-group:hover {
  background-color: #fff9e1;
}

.tabulator-row:hover .group-action-buttons-container {
  display: flex;
}

.barcode-column .tabulator-col-title {
  padding-right: 12px !important;
}

.no-group-by .tabulator-row-odd:nth-child(1) {
  margin-top: 5px;
}

.no-group-by .tabulator-row-odd:nth-child(1) .tabulator-cell {
  border-top: 1px solid grey !important;
}

.checkbox-column:not(.tabulator-col) {
  padding: 12px 8px !important;
}
</style>

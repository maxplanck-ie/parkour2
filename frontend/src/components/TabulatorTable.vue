<template>
  <!-- Table Element -->
  <div class="normal-tabulator-table" style="height: 100%">
    <div id="tabulatorTable" ref="tabulatorTableRef"></div>
  </div>

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
        <div>
          Following errors occurred while pasting, please try again after
          fixing:
        </div>
        <div v-if="errorsPopupContents.errorsList?.length" class="popup-scrollable-content">
          <ol style="padding-left: 25px">
            <li v-for="(item, index) in errorsPopupContents.errorsList" :key="index">
              {{ item.barcode + " ➜ " }}
              <span style="font-weight: bold">{{ item.message }}</span>
            </li>
          </ol>
        </div>
      </div>
      <div class="popup-footer">
        <button class="popup-button" @click="showErrorsWindow = false">
          OK
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { TabulatorFull as Tabulator } from "tabulator-tables";
import * as XLSX from "xlsx";
import "tabulator-tables/dist/css/tabulator_bootstrap5.min.css";
import { showNotification } from "../utilities/utilityFunctions";
import { markRaw } from "vue";

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
      previousData: null,
      tableFiltersState: {
        typesIn: [
          { field: "type", type: "=", value: "L" },
          { field: "type", type: "=", value: "S" }
        ],
        typesNotIn: []
      },
      tableGroupsToggleState: 0,
      tableGroupsConfig: {
        groupBy: this.groupBy,
        noGroupByClass: false
      },
      tableEachGroupsToggleState: [],
      tableColumnWidths: {},
      showErrorsWindow: false,
      errorsPopupContents: {
        errorsList: [],
        errorsPopupHeight: 220,
        errorsPopupWidth: 600
      }
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
    showErrorsWindow(newVal) {
      if (newVal) {
        this.$nextTick(() => {
          const okButton = document.querySelector(".popup-button");
          okButton.focus();
        });
      } else {
        document.getElementsByClassName("tabulator-range-selected")[0]?.click();
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
            headerSort: false,
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
              showNotification(
                "Please select a range before pasting.",
                "warning"
              );
              return [];
            }

            const {
              top: rowStart,
              bottom: rowEnd,
              left: colStart,
              right: colEnd
            } = selectedRanges[0]._range;
            const visibleColumns = this.tabulatorInstance
              .getColumns()
              .filter((col) => col._column.visible);
            let pastedData = clipboard
              .split(/\r?\n/)
              .map((row) => row.split("\t"));
            if (
              pastedData[pastedData.length - 1]?.length === 1 &&
              pastedData[pastedData.length - 1][0] === ""
            )
              pastedData.pop();

            const pastedColumnCount = Math.max(
              ...pastedData.map((row) => row.length)
            );
            const rangeColumns = visibleColumns.slice(
              colStart,
              colStart + pastedColumnCount
            );
            const batchUpdates = {};
            const isSingleCell = rowStart === rowEnd && colStart === colEnd;
            let targetGroup = null;
            let hasValidationErrors = false;
            let changedRows = new Set();
            let changedCols = new Set();

            if (isSingleCell) {
              const selectedRow = this.tabulatorInstance.getRowFromPosition(
                rowStart + 1
              );
              targetGroup = selectedRow?.getData()?.[this.groupBy];
            }

            pastedData.forEach((pastedRow, rowOffset) => {
              const tableRow = this.tabulatorInstance.getRowFromPosition(
                rowStart + rowOffset + 1
              );
              if (!tableRow) return;
              if (
                isSingleCell &&
                tableRow.getData()?.[this.groupBy] !== targetGroup
              )
                return;

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

                if (
                  columnDef.editor === false ||
                  cell.getElement().classList.contains("disable-editing")
                ) {
                  hasValidationErrors = true;
                  errors.push({
                    barcode: rowData.barcode,
                    message: `Cell ${cellNumber}: Editing is not allowed in this cell.`
                  });
                  return;
                }

                try {
                  updatedRow[field] = this.validateCellValue(
                    cellValue,
                    columnDef,
                    rowData
                  );
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
                const startRow = this.tabulatorInstance.getRowFromPosition(
                  Math.min(...changedRows)
                );
                const endRow = this.tabulatorInstance.getRowFromPosition(
                  Math.max(...changedRows)
                );
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
          groupStartOpen: this.groupStartOpen,
          ...this.tableOptions
        };

        this.tabulatorInstance = markRaw(
          new Tabulator("#tabulatorTable", options)
        );

        this.tabulatorInstance.on("tableBuilt", () => {
          document.addEventListener("keydown", this.handleKeyDown);

          const tabulatorElement = this.getTabulatorElement();
          tabulatorElement.addEventListener("keydown", (e) => {
            const tag = e.target && e.target.tagName;
            if ((tag === "INPUT" || tag === "TEXTAREA") && (e.key === "ArrowLeft" || e.key === "ArrowRight")) {
              e.stopPropagation();
            }
          }, true);
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

        this.tabulatorInstance.on("dataFiltered", () => {
          setTimeout(() => {
            if (this.groupSort && this.groupBy) {
              let groupValues = [
                ...new Set(
                  this.tabulatorInstance
                    .getData("active")
                    .map((item) => item[this.groupSort.field])
                )
              ];

              if (this.groupSort.field === "request_name") {
                groupValues.sort((a, b) => {
                  const getNumber = (val) => {
                    const num = parseInt(val.split("_")[0], 10);
                    return isNaN(num) ? 0 : num;
                  };
                  return getNumber(a) - getNumber(b);
                });
              } else {
                groupValues.sort();
              }

              if (this.groupSort.order === "desc") {
                groupValues.reverse();
              }
              this.tabulatorInstance.setGroupValues([groupValues]);
            }
          }, 0);
        });

        this.tabulatorInstance.on("clipboardCopied", () => {
          this.tableOptions.fakeLoadingStart();
          this.tableOptions.fakeLoadingStop();
        });

        this.tabulatorInstance.on("clipboardPasted", () => {
          if (this.errorsPopupContents.errorsList.length == 0) {
            this.tableOptions.fakeLoadingStart();
            this.tableOptions.fakeLoadingStop();
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
      this.tabulatorInstance.blockRedraw();
      if (this.tabulatorInstance) {
        this.tabulatorInstance.setColumns(this.columnDefs);
        this.getTabulatorElement().classList.remove("no-group-by");
        this.showAllGroups();
        if (this.groupBy) this.tabulatorInstance.setGroupBy(this.groupBy);
      }
      this.tabulatorInstance.restoreRedraw();
    },

    // Make sure that records in rowData have "type" field, in order for these filters to work. Check the definition of "this.tableFiltersState" to get more context.
    // If "type" is not defined, then the records won't show up in the table.
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
      if (goToInitial === true) {
        this.tableGroupsToggleState = 0;
        this.showAllGroups();
        this.tableGroupsConfig.groupBy = this.groupBy;
        this.tableGroupsConfig.noGroupByClass = false;
        return;
      }

      const allGroups = this.tabulatorInstance?.getGroups?.() || [];
      if (allGroups.length === 0) return;

      const closedCount = allGroups.filter((g) => !g._group.visible).length;
      if (closedCount === allGroups.length) {
        this.tableGroupsToggleState = 0;
        this.showAllGroups();
      } else {
        this.tableGroupsToggleState = 1;
        this.hideAllGroups();
      }

      this.tableGroupsConfig.groupBy = this.groupBy;
      this.tableGroupsConfig.noGroupByClass = false;
    },

    refreshTable(hard) {
      if (this.tabulatorInstance) {
        this.tabulatorInstance.redraw(hard);
      }
    },

    getTable() {
      return this.tabulatorInstance;
    },

    handleKeyDown(event) {
      const isDeleteOrBackspace =
        event.key === "Delete" || event.key === "Backspace";
      const isEscape = event.key === "Escape";
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
          (selectedRangesData[0][0] &&
            Object.keys(selectedRangesData[0][0]).length > 0));
      if (isEscape && this.showErrorsWindow) {
        this.showErrorsWindow = false;
        return;
      }
      if (
        document.activeElement &&
        (document.activeElement.tagName === "INPUT" ||
          document.activeElement.tagName === "TEXTAREA")
      ) {
        return;
      }
      if (isDeleteOrBackspace) {
        if (!isRangeSelected) return;
        let firstRangeCells = selectedRanges[0]
          ? selectedRanges[0].getCells()
          : [];
        firstRangeCells.forEach((row) => {
          row.forEach((cell) => {
            let isEditable = cell._cell.column.getDefinition().editor;
            let disabledEditing = cell
              .getElement()
              .classList.contains("disable-editing");

            if (isEditable && !disabledEditing) {
              const fieldName = cell._cell.column.getField();
              const overrideFn = this.tableOptions && this.tableOptions.getClearValueForField;
              const clearVal = typeof overrideFn === "function" ? overrideFn(fieldName) : "";
              cell.setValue(clearVal);
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
          if (
            input &&
            (document.activeElement.tagName === "INPUT" ||
              document.activeElement.tagName === "TEXTAREA")
          ) {
            input.value = "";
            input.dispatchEvent(new Event("input", { bubbles: true }));
          }
        }
      }
    },

    validateCellValue(value, columnDef, rowData) {
      const editorType = columnDef.editor;
      const resolveEditorParams = () =>
        typeof columnDef.editorParams === "function"
          ? columnDef.editorParams({ getRow: () => ({ getData: () => rowData }) })
          : columnDef.editorParams || {};
      const applyValidators = (val) => {
        if (!columnDef.validator) return;
        const validators = Array.isArray(columnDef.validator)
          ? columnDef.validator
          : [columnDef.validator];
        for (const rule of validators) {
          if (typeof rule === "function") {
            const res = rule(val);
            if (res !== true) throw new Error(res || "Invalid value.");
          } else if (typeof rule === "string") {
            const trimmed = rule.trim().toLowerCase();
            if (trimmed === "integer") {
              if (!Number.isInteger(val)) throw new Error("Value must be an integer.");
            } else if (trimmed.startsWith("min:")) {
              const v = Number(trimmed.slice(4));
              if (!Number.isNaN(v) && val < v)
                throw new Error(`Value should be more than ${new Intl.NumberFormat().format(v)}.`);
            } else if (trimmed.startsWith("max:")) {
              const v = Number(trimmed.slice(4));
              if (!Number.isNaN(v) && val > v)
                throw new Error(`Value should be less than ${new Intl.NumberFormat().format(v)}.`);
            }
          }
        }
      };
      switch (editorType) {
        case "number": {
          const str = String(value).trim();
          if (str === "") return "";
          const numValue = Number(str);
          if (Number.isNaN(numValue)) throw new Error("Invalid numeric format, please check!");
          applyValidators(numValue);
          const { min, max } = resolveEditorParams();
          if ((min !== undefined && numValue < min) || (max !== undefined && numValue > max)) {
            const nf = new Intl.NumberFormat();
            const hasMin = min !== undefined;
            const hasMax = max !== undefined;
            const minStr = hasMin ? nf.format(Number(min)) : undefined;
            const maxStr = hasMax ? nf.format(Number(max)) : undefined;
            let message;
            if (hasMin && hasMax) message = `Value must be between ${minStr} and ${maxStr}.`;
            else if (hasMin) message = `Value should be more than ${minStr}.`;
            else message = `Value should be less than ${maxStr}.`;
            throw new Error(message);
          }
          return numValue;
        }
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
.normal-tabulator-table .tabulator {
  height: 100%;
  font-size: 12px;
  border: 1px solid #d0d0d0;
  border-radius: 4px !important;
}

.normal-tabulator-table .tabulator-table {
  background-color: #7788992d !important;
  z-index: 10;
}

.normal-tabulator-table .tabulator-header {
  border: none !important;
}

.normal-tabulator-table .tabulator-placeholder {
  text-align: center;
  width: 600px !important;
  height: 100%;
  background-color: #7788992d !important;
  white-space: nowrap;
}

.normal-tabulator-table .tabulator-range-active {
  border: none !important;
}

.normal-tabulator-table .tabulator-cell {
  height: 30px !important;
  line-height: 6px;
  padding: 0px !important;
  border-bottom: 1px solid #d0d0d0 !important;
  border-right: none !important;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.normal-tabulator-table .tabulator-cell.right-border {
  border-right: 1px solid #d0d0d0 !important;
}

.normal-tabulator-table .tabulator-cell.no-right-border {
  border-right: none !important;
}

.normal-tabulator-table .tabulator-cell.disable-range-selection {
  pointer-events: none;
}

.normal-tabulator-table .tabulator-cell.tabulator-range-selected {
  background-color: #c0e7fd !important;
  color: #003757 !important;
  border-bottom: 1px solid #d0d0d0 !important;
}

.normal-tabulator-table .tabulator-cell.tabulator-editing {
  background-color: lightgoldenrodyellow !important;
  padding-left: 10px !important;
}

.normal-tabulator-table .tabulator-cell.tabulator-editable {
  cursor: pointer;
}

.normal-tabulator-table .tabulator-cell.tabulator-frozen {
  z-index: 1 !important;
}

.normal-tabulator-table .tabulator-cell.user-entry-column {
  background-color: #ffebee;
  color: #c62828;
}

.normal-tabulator-table .tabulator-cell.facility-entry-column {
  background-color: #c4ecc2;
  color: #388e3c;
}

.normal-tabulator-table .tabulator-cell.facility-entry-column.disable-editing {
  background-color: #b6dbb4;
}

.normal-tabulator-table .tabulator-col {
  border-right: 1px solid #d0d0d0 !important;
  border-bottom: 1px solid #d0d0d0 !important;
}

.normal-tabulator-table .tabulator-col-group-cols {
  border: none !important;
  border-top: 1px solid #d0d0d0 !important;
}

.normal-tabulator-table .tabulator-col-content {
  padding: 5px !important;
}

.normal-tabulator-table .tabulator-row {
  min-height: 0;
  height: 30px !important;
}

.normal-tabulator-table .tabulator-row[role="row"] {
  border: none !important;
}

.normal-tabulator-table .tabulator-row:not(.tabulator-group) {
  background-color: white !important;
}

.normal-tabulator-table .tabulator-row:not(.tabulator-group):hover {
  mix-blend-mode: multiply;
}

.normal-tabulator-table .tabulator-row.tabulator-group {
  margin-top: 3px;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  background-color: white;
  border-top: 1px solid #d0d0d0 !important;
  border-bottom: 1px solid #d0d0d0 !important;
  z-index: 20;
}

.normal-tabulator-table .tabulator-row.tabulator-group:hover {
  background-color: white;
}

.normal-tabulator-table .tabulator-row:hover .group-action-buttons-container {
  display: flex;
}

.normal-tabulator-table .tabulator-header-filter input {
  height: 24px;
  font-size: 12px !important;
  border: 1px solid #d0d0d0 !important;
}

.normal-tabulator-table .tabulator-group.hidden-group {
  display: none !important;
}

.normal-tabulator-table .no-group-by .tabulator-row-odd:nth-child(1) {
  margin-top: 5px;
}

.normal-tabulator-table .no-group-by .tabulator-row-odd:nth-child(1) .tabulator-cell {
  border-top: 1px solid #d0d0d0 !important;
}

.normal-tabulator-table .checkbox-column:not(.tabulator-col) {
  padding: 10px 0px !important;
}

.normal-tabulator-table .title-field-group>.tabulator-col-content>div>div {
  font-weight: 600 !important;
  color: rgb(99, 99, 99) !important;
}

.normal-tabulator-table input[type="number"]::-webkit-outer-spin-button,
.normal-tabulator-table input[type="number"]::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
</style>

<!--
Fix APIs failing when multiple edits together, especially when DEL or BACKSPACE
-->

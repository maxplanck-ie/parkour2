<template>
  <!-- Table Element -->
  <div class="normal-tabulator-table" style="height: 100%">
    <div :id="tableId" ref="tabulatorTableRef"></div>
  </div>

  <!-- Errors window -->
  <div v-if="showErrorsWindow" class="popup-overlay">
    <div class="popup-container" :style="{
      height: errorsPopupContents.errorsPopupHeight + 'px',
      width: errorsPopupContents.errorsPopupWidth + 'px'
    }">
      <div class="popup-header">
        <img
          :src="iconPasteError"
          alt="Paste Error"
          width="42"
          height="42"
          style="display: block"
        />
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
          <div class="popup-scrollable-content-inner">
            <ol style="padding-left: 25px">
              <li v-for="(item, index) in errorsPopupContents.errorsList" :key="index">
                <span v-if="tableOptions && tableOptions.showPasteErrorRowNumber && item.rowNumber">
                  {{ "Row " + item.rowNumber + " ➜ " }}
                </span>
                <span v-else-if="item.barcode">
                  {{ item.barcode + " ➜ " }}
                </span>
                <span style="font-weight: bold">{{ item.message }}</span>
              </li>
            </ol>
          </div>
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
import iconPasteError from "../assets/icons/alert_confirmation.svg";

export default {
  name: "TabulatorTable",
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
      type: String,
      required: false,
      default: null
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
    enableDefaultFilters: {
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
      iconPasteError,
      tabulatorInstance: null,
      previousData: null,
      preventEditorBlurHandler: null,
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
      lastGroupValues: [],
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
    const tabulatorElement = this.getTabulatorElement();
    if (tabulatorElement && this.preventEditorBlurHandler) {
      tabulatorElement.removeEventListener(
        "mousedown",
        this.preventEditorBlurHandler,
        true
      );
      tabulatorElement.removeEventListener(
        "click",
        this.preventEditorBlurHandler,
        true
      );
    }
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
          clipboardCopyFormatter: (type, output) => {
            if (type !== "plain") return output;
            const customCopy = this.buildClipboardOutputFromSelection();
            if (customCopy?.usedCustom) {
              return `${customCopy.output}\n`;
            }
            return `${output}\n`;
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
            const batchUpdates = new Map();
            const isSingleCell = rowStart === rowEnd && colStart === colEnd;
            let targetGroup = null;
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

              const rowData = tableRow.getData();
              const workingRow = { ...rowData };
              const rowNumber = rowStart + rowOffset + 1;
              const updatedRow = { ...rowData };

              pastedRow.forEach((cellValue, colOffset) => {
                const column = rangeColumns[colOffset];
                if (!column) return;
                const cellNumber = colStart + colOffset + 1;
                const field = column.getField();
                const columnDef = column.getDefinition();
                const cell = tableRow.getCell(field);
                const columnTitle =
                  columnDef?.title || field || `Cell ${cellNumber}`;
                const isEditable = (() => {
                  const shouldBlockDisabledCells =
                    this.tableOptions?.blockActionsOnDisabledCells === true;
                  const cellEl = cell?.getElement?.();
                  if (
                    shouldBlockDisabledCells &&
                    cellEl?.classList?.contains("disable-editing")
                  ) {
                    return false;
                  }
                  if (columnDef.editor === false) return false;
                  if (typeof columnDef.editable === "function") {
                    return columnDef.editable({
                      getRow: () => ({ getData: () => workingRow })
                    });
                  }
                  if (typeof columnDef.editable === "boolean") {
                    return columnDef.editable;
                  }
                  return true;
                })();

                if (!isEditable) {
                  const trimmedValue = String(cellValue ?? "").trim();
                  if (trimmedValue === "") {
                    return;
                  }
                  errors.push({
                    barcode: rowData.barcode,
                    rowNumber,
                    message: `${columnTitle}: Editing is not allowed in this cell.`
                  });
                  return;
                }

                try {
                  updatedRow[field] = this.validateCellValue(
                    cellValue,
                    columnDef,
                    workingRow
                  );
                  workingRow[field] = updatedRow[field];
                  changedRows.add(rowStart + rowOffset + 1);
                  changedCols.add(colStart + colOffset);
                } catch (error) {
                  errors.push({
                    barcode: rowData.barcode,
                    rowNumber,
                    message: `${columnTitle}: ${error.message}`
                  });
                }
              });

              const updateKey =
                rowData?.tempId ?? rowData?.barcode ?? `row-${rowNumber}`;
              batchUpdates.set(updateKey, updatedRow);
            });

            const updatedRowsArray = Array.from(batchUpdates.values());
            if (updatedRowsArray.length) {
              this.tabulatorInstance.updateData(updatedRowsArray);

              if (changedRows.size) {
                changedRows.forEach((rowPosition) => {
                  const row = this.tabulatorInstance.getRowFromPosition(
                    rowPosition
                  );
                  row?.reformat?.();
                });
              }

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

            if (
              updatedRowsArray.length &&
              typeof this.tableOptions.handlePasteApplied === "function"
            ) {
              this.tableOptions.handlePasteApplied(updatedRowsArray);
            }

            if (errors.length) {
              this.errorsPopupContents = {
                errorsList: errors,
                errorsPopupHeight: Math.min(420, 260 + errors.length * 34),
                errorsPopupWidth: 600
              };
              this.showErrorsWindow = true;
            }

            return [];
          },
          dependencies: {
            XLSX: XLSX
          },
          downloadConfig: {},
          groupContextMenu: [],
          groupBy: this.tableGroupsConfig.groupBy || false,
          groupStartOpen: this.groupStartOpen,
          ...this.tableOptions
        };

        this.tabulatorInstance = markRaw(
          new Tabulator(`#${this.tableId}`, options)
        );

        this.tabulatorInstance.on("tableBuilt", () => {
          document.addEventListener("keydown", this.handleKeyDown);

          const tabulatorElement = this.getTabulatorElement();
          tabulatorElement.addEventListener(
            "keydown",
            (e) => {
              const tag = e.target && e.target.tagName;
              if (
                (tag === "INPUT" || tag === "TEXTAREA") &&
                (e.key === "ArrowLeft" || e.key === "ArrowRight")
              ) {
                e.stopPropagation();
              }
            },
            true
          );

          if (this.preventEditorBlurHandler) {
            tabulatorElement.removeEventListener(
              "mousedown",
              this.preventEditorBlurHandler,
              true
            );
            tabulatorElement.removeEventListener(
              "click",
              this.preventEditorBlurHandler,
              true
            );
          }

          this.preventEditorBlurHandler = (event) => {
            if (event.target.closest(".tabulator-cell.tabulator-editing")) {
              event.stopPropagation();
            }
          };

          tabulatorElement.addEventListener(
            "mousedown",
            this.preventEditorBlurHandler,
            true
          );
          tabulatorElement.addEventListener(
            "click",
            this.preventEditorBlurHandler,
            true
          );
          if (this.tableGroupsConfig.noGroupByClass) {
            tabulatorElement.classList.add("no-group-by");
          } else {
            tabulatorElement.classList.remove("no-group-by");
          }

          this.tabulatorInstance.setGroupBy(this.tableGroupsConfig.groupBy);

          if (this.enableDefaultFilters) {
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
          }
        });

        this.previousData = JSON.stringify(this.rowData);

        this.tabulatorInstance.on("dataChanged", (updatedData) => {
          if (typeof this.tableOptions.onBatchCellValueChanged !== "function") {
            this.previousData = JSON.stringify(updatedData);
            return;
          }
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
                if (key === "gmo_facility") {
                  if (row[key] !== oldRow[key]) {
                    if (row[key] === "Not Needed" || row[key] === false) {
                      changedFields[key] = false;
                    } else if (
                      row[key] === "Risk Assessment Done" ||
                      row[key] === true
                    ) {
                      changedFields[key] = true;
                    } else {
                      changedFields[key] = row[key];
                    }
                  }
                } else {
                  if (row[key] !== oldRow[key]) {
                    changedFields[key] = row[key] === "" ? null : row[key];
                  }
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

        this.tabulatorInstance.on("renderComplete", () => {
          const rows = this.tabulatorInstance?.rowManager?.activeRows || [];
          this.updateGroupValuesFromRows(rows);
          if (this.tableOptions.handleRenderComplete) {
            this.tableOptions.handleRenderComplete();
          }
        });

        this.tabulatorInstance.on("cellEdited", (cell) => {
          if (this.tableOptions.handleCellEdited) {
            this.tableOptions.handleCellEdited(cell);
          }
        });

        this.tabulatorInstance.on("clipboardCopied", () => {
          if (this.tableOptions.fakeLoadingStart) {
            this.tableOptions.fakeLoadingStart();
          }
          if (this.tableOptions.fakeLoadingStop) {
            this.tableOptions.fakeLoadingStop();
          }
        });

        this.tabulatorInstance.on("clipboardPasted", () => {
          if (this.errorsPopupContents.errorsList.length == 0) {
            if (this.tableOptions.fakeLoadingStart) {
              this.tableOptions.fakeLoadingStart();
            }
            if (this.tableOptions.fakeLoadingStop) {
              this.tableOptions.fakeLoadingStop();
            }
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
      return document.getElementById(this.tableId);
    },

    updateGroupValuesFromRows(rows) {
      if (!this.tabulatorInstance || !this.groupBy || !this.groupSort || !rows)
        return;
      const uniqueGroups = new Set();
      rows.forEach((row) => {
        const val =
          row?._row?.data?.[this.groupBy] ?? row?.getData?.()?.[this.groupBy];
        if (val) uniqueGroups.add(val);
      });
      let sortedGroupValues = Array.from(uniqueGroups);
      if (this.groupSort.field === "request_name") {
        const getNumber = (val) => {
          const num = parseInt(val.split("_")[0], 10);
          return isNaN(num) ? 0 : num;
        };
        sortedGroupValues.sort((a, b) => getNumber(a) - getNumber(b));
      } else {
        sortedGroupValues.sort();
      }
      if (this.groupSort.order === "desc") {
        sortedGroupValues.reverse();
      }
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
      const selectedRanges = this.tabulatorInstance.getRanges?.() || [];
      const rangeCells = selectedRanges[0]?.getCells?.() || [];
      const getIsEditable = (cell, rowData) => {
        const shouldBlockDisabledCells =
          this.tableOptions?.blockActionsOnDisabledCells === true;
        const cellEl = cell.getElement?.();
        if (shouldBlockDisabledCells && cellEl?.classList?.contains("disable-editing")) {
          return false;
        }
        const columnDef = cell.getColumn?.().getDefinition?.() || {};
        if (columnDef.editor === false) return false;
        if (typeof columnDef.editable === "function") {
          return columnDef.editable({
            getRow: () => ({ getData: () => rowData })
          });
        }
        if (typeof columnDef.editable === "boolean") {
          return columnDef.editable;
        }
        return Boolean(columnDef.editor);
      };
      if (isDeleteOrBackspace) {
        if (!rangeCells.length) return;
        const rowOriginals = new Map();
        const rowUpdates = new Map();
        rangeCells.forEach((row) => {
          row.forEach((cell) => {
            const rowComp = cell.getRow?.();
            if (!rowComp) return;
            if (!rowOriginals.has(rowComp)) {
              rowOriginals.set(rowComp, rowComp.getData?.() || {});
            }
            const rowData = rowOriginals.get(rowComp) || {};
            if (!getIsEditable(cell, rowData)) return;
            const fieldName = cell.getField?.();
            const overrideFn =
              this.tableOptions && this.tableOptions.getClearValueForField;
            const clearVal =
              typeof overrideFn === "function" ? overrideFn(fieldName) : "";
            const base = rowUpdates.get(rowComp) || { ...rowData };
            rowUpdates.set(rowComp, { ...base, [fieldName]: clearVal });
          });
        });
        rowUpdates.forEach((data, rowComp) => {
          rowComp?.update?.(data);
        });
        if (
          rowUpdates.size &&
          typeof this.tableOptions.handleDeleteApplied === "function"
        ) {
          this.tableOptions.handleDeleteApplied(
            Array.from(rowUpdates.values())
          );
        }
        event.preventDefault();
        return;
      }
      if (isPrintableKey) {
        const firstCell = rangeCells[0]?.[0];
        if (firstCell) {
          const rowData = firstCell.getRow?.().getData?.() || {};
          if (!getIsEditable(firstCell, rowData)) {
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

    buildClipboardOutputFromSelection() {
      const ranges = this.tabulatorInstance?.getRanges?.() || [];
      if (!ranges.length) return null;
      const cells = ranges[0]?.getCells?.() || [];
      if (!cells.length) return null;
      let usedCustom = false;
      const rows = cells.map((rowCells) =>
        rowCells.map((cell) => {
          const columnDef = cell.getColumn?.().getDefinition?.() || {};
          if (typeof columnDef.clipboardCopyValue === "function") {
            usedCustom = true;
            const custom = columnDef.clipboardCopyValue(cell);
            if (custom === undefined || custom === null) return "";
            return String(custom);
          }
          const value = cell.getValue?.();
          if (value === undefined || value === null) return "";
          return String(value);
        })
      );
      const output = rows.map((row) => row.join("\t")).join("\n");
      return { output, usedCustom };
    },

    validateCellValue(value, columnDef, rowData) {
      const editorType = columnDef.editor;
      const resolveEditorParams = () =>
        typeof columnDef.editorParams === "function"
          ? columnDef.editorParams({
            getRow: () => ({ getData: () => rowData })
          })
          : columnDef.editorParams || {};
      const applyValidators = (val) => {
        if (!columnDef.validator) return;
        const validators = Array.isArray(columnDef.validator)
          ? columnDef.validator
          : [columnDef.validator];
        for (const rule of validators) {
          if (typeof rule === "function") {
            const res = rule(val);
            if (res !== true) throw new Error(res || "Entered value is invalid.");
          } else if (typeof rule === "string") {
            const trimmed = rule.trim().toLowerCase();
            if (trimmed === "integer") {
              if (!Number.isInteger(val))
                throw new Error("Entered value must be an integer.");
            } else if (trimmed.startsWith("min:")) {
              const v = Number(trimmed.slice(4));
              if (!Number.isNaN(v) && val < v)
                throw new Error(
                  `Entered value should be more than ${new Intl.NumberFormat().format(v)}.`
                );
            } else if (trimmed.startsWith("max:")) {
              const v = Number(trimmed.slice(4));
              if (!Number.isNaN(v) && val > v)
                throw new Error(
                  `Entered value should be less than ${new Intl.NumberFormat().format(v)}.`
                );
            }
          }
        }
      };
      switch (editorType) {
        case "number": {
          const str = String(value).trim();
          if (str === "") return "";
          const numValue = Number(str);
          if (Number.isNaN(numValue))
            throw new Error("Entered number format is invalid.");
          applyValidators(numValue);
          const { min, max } = resolveEditorParams();
          if (
            (min !== undefined && numValue < min) ||
            (max !== undefined && numValue > max)
          ) {
            const nf = new Intl.NumberFormat();
            const hasMin = min !== undefined;
            const hasMax = max !== undefined;
            const minStr = hasMin ? nf.format(Number(min)) : undefined;
            const maxStr = hasMax ? nf.format(Number(max)) : undefined;
            let message;
            if (hasMin && hasMax)
              message = `Entered value must be between ${minStr} and ${maxStr}.`;
            else if (hasMin) message = `Entered value should be more than ${minStr}.`;
            else message = `Entered value should be less than ${maxStr}.`;
            throw new Error(message);
          }
          return numValue;
        }
        case "list": {
          if (value === "" || value === undefined || value === null) {
            return "";
          }
          const editorParamsList =
            typeof columnDef.editorParams === "function"
              ? columnDef.editorParams({
                getRow: () => ({ getData: () => rowData })
              })
              : columnDef.editorParams;
          let options = [];
          let optionLabels = [];
          if (Array.isArray(editorParamsList?.values)) {
            options = editorParamsList.values.map((opt) =>
              typeof opt === "object" ? opt.value : opt
            );
            optionLabels = editorParamsList.values.map((opt) =>
              typeof opt === "object" ? opt.label : opt
            );
          } else if (
            editorParamsList?.values &&
            typeof editorParamsList.values === "object"
          ) {
            options = Object.keys(editorParamsList.values);
            optionLabels = Object.values(editorParamsList.values);
          }
          if (!options.includes(value)) {
            const normalized = String(value).trim();
            if (normalized !== "") {
              const exactIndex = optionLabels.findIndex(
                (label) => String(label).trim() === normalized
              );
              if (exactIndex !== -1) {
                return options[exactIndex];
              }
              const normalizedLower = normalized.toLowerCase();
              const ciIndex = optionLabels.findIndex(
                (label) => String(label).trim().toLowerCase() === normalizedLower
              );
              if (ciIndex !== -1) {
                return options[ciIndex];
              }
            }
            if (typeof columnDef.pasteValueResolver === "function") {
              const resolved = columnDef.pasteValueResolver(value, {
                options,
                optionLabels,
                rowData
              });
              if (resolved !== undefined && resolved !== null && resolved !== "") {
                applyValidators(resolved);
                return resolved;
              }
            }
            if (columnDef.validator) {
              applyValidators(value);
              return value;
            }
            throw new Error(
              "Entered value must be from the dropdown list."
            );
          }
          return value;
        }
        case "input":
        default:
          if (columnDef.validator) {
            const validationResult = columnDef.validator(value);
            if (validationResult !== true) {
              throw new Error(
                validationResult || "Entered date format is invalid."
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
  border-radius: 8px !important;
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

.normal-tabulator-table input[type="number"] {
  -moz-appearance: textfield;
  appearance: textfield;
}

.normal-tabulator-table input[type="number"]::-moz-number-spin-box,
.normal-tabulator-table input[type="number"]::-moz-number-spin-up,
.normal-tabulator-table input[type="number"]::-moz-number-spin-down {
  display: none;
}

.tabulator-edit-list .tabulator-edit-list-item.active,
.tabulator-edit-list .tabulator-edit-list-item.focused,
.tabulator-edit-list .tabulator-edit-list-item.active .tabulator-edit-list-item-label,
.tabulator-edit-list .tabulator-edit-list-item.focused .tabulator-edit-list-item-label {
  background-color: #2967c5;
  color: #fff !important;
  outline: none;
}

.normal-tabulator-table .tabulator-cell.required-empty {
  background-color: #f5bcbc;
}

.normal-tabulator-table .tabulator-cell.cell-invalid:not(.tabulator-range-selected) {
  background-color: #f5bcbc !important;
}

.normal-tabulator-table .tabulator-row.row-has-errors .tabulator-cell.required-filled:not(.disable-editing) {
  background-color: #f9e5e5;
}

.normal-tabulator-table .tabulator-row.row-has-errors .tabulator-cell:not(.required-empty):not(.cell-invalid):not(.tabulator-range-selected):not(.disable-editing) {
  background-color: #f9e5e5;
}

.normal-tabulator-table .tabulator-row.row-has-errors .tabulator-cell.disable-editing:not(.required-empty):not(.cell-invalid):not(.tabulator-range-selected) {
  background-color: #f9e5e5;
}

.normal-tabulator-table .tabulator-row.row-all-valid .tabulator-cell.required-filled:not(.disable-editing),
.normal-tabulator-table .tabulator-row.row-all-valid .tabulator-cell:not(.required-empty):not(.cell-invalid):not(.tabulator-range-selected):not(.disable-editing) {
  background-color: #e4fae3;
}

.normal-tabulator-table .tabulator-row.row-all-valid .tabulator-cell.disable-editing:not(.required-empty):not(.cell-invalid):not(.tabulator-range-selected) {
  background-color: #e4fae3;
}

.normal-tabulator-table .tabulator-cell.disable-editing {
  background-image: repeating-linear-gradient(135deg,
      rgba(156, 163, 175, 0.3),
      rgba(156, 163, 175, 0.3) 6px,
      rgba(255, 255, 255, 0) 6px,
      rgba(255, 255, 255, 0) 12px) !important;
  color: #6f7680 !important;
  cursor: not-allowed;
}
</style>

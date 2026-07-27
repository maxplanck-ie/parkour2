<template>
  <!-- Table Element -->
  <div class="normal-tabulator-table" style="height: 100%">
    <div :id="tableId" ref="tabulatorTableRef"></div>
  </div>

  <!-- Errors window -->
  <div v-if="showErrorsWindow" class="popup-overlay">
    <div
      class="popup-container"
      :style="{
        height: errorsPopupContents.errorsPopupHeight + 'px',
        width: errorsPopupContents.errorsPopupWidth + 'px'
      }"
    >
      <div class="popup-header">
        <img
          :src="iconPasteError"
          alt="Paste Error"
          width="42"
          height="42"
          style="display: block"
        />
        <span class="popup-title">Paste Error</span>
        <button class="popup-close-button" @click="closeErrorsWindow">
          &times;
        </button>
      </div>
      <div class="popup-body">
        <div>
          Following errors occurred while pasting, please try again after
          fixing:
        </div>
        <div
          v-if="errorsPopupContents.errorsList?.length"
          class="popup-scrollable-content"
        >
          <div class="popup-scrollable-content-inner">
            <ol style="padding-left: 25px">
              <li
                v-for="(item, index) in errorsPopupContents.errorsList"
                :key="index"
              >
                <span
                  v-if="
                    tableOptions &&
                    tableOptions.showPasteErrorRowNumber &&
                    item.rowNumber
                  "
                >
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
        <button
          ref="pasteErrorOkButton"
          class="popup-button"
          @click="closeErrorsWindow"
        >
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

const TABULATOR_TABLE_DEFAULT_ID = "tabulatorTable";
const TABULATOR_SELECTOR_PREFIX = "#";
const GROUP_VALUE_SEPARATOR = "_";
const DEFAULT_DOUBLE_CLICK_EDIT_DELAY_MS = 1000;
const LARGE_PASTE_CELL_THRESHOLD = 200;

const TABULATOR_OPTIONS = {
  layout: "fitColumns",
  headerAlign: "center",
  resizableHeader: "header",
  groupToggleElement: "header",
  editTriggerEvent: "dblclick",
  manualEditTriggerEvent: "manual",
  copyRowRange: "range",
  pasteAction: "range",
  copyPlainType: "plain"
};

const TABULATOR_EVENTS = {
  tableBuilt: "tableBuilt",
  dataChanged: "dataChanged",
  renderComplete: "renderComplete",
  cellEdited: "cellEdited",
  cellClick: "cellClick",
  cellFocused: "cellFocused",
  cellContext: "cellContext",
  clipboardCopied: "clipboardCopied",
  clipboardPasted: "clipboardPasted",
  columnResized: "columnResized",
  columnVisibilityChanged: "columnVisibilityChanged"
};

const DOM_EVENTS = {
  keydown: "keydown",
  mousedown: "mousedown",
  mouseup: "mouseup",
  click: "click",
  input: "input"
};

const KEY_NAMES = {
  arrowDown: "ArrowDown",
  arrowLeft: "ArrowLeft",
  arrowRight: "ArrowRight",
  backspace: "Backspace",
  delete: "Delete",
  enter: "Enter",
  escape: "Escape",
  cut: "x",
  copy: "c",
  paste: "v",
  selectAll: "a"
};

const HTML_TAGS = {
  input: "INPUT",
  select: "SELECT",
  textarea: "TEXTAREA"
};

const TABULATOR_CLASSES = {
  noGroupBy: "no-group-by",
  disableEditing: "disable-editing",
  pendingRangeInteraction: "pending-range-interaction"
};

const TABULATOR_SELECTORS = {
  editingCell: ".tabulator-cell.tabulator-editing",
  editList: ".tabulator-edit-list",
  groupRow: ".tabulator-row.tabulator-group",
  tableHolder: ".tabulator-tableholder",
  tableContainer: ".table-container",
  editorInput: "input, select, textarea, [contenteditable='true']"
};

const TABLE_FIELDS = {
  barcode: "barcode",
  comments: "comments",
  commentsFacility: "comments_facility",
  commentsLibrarySample: "comments_library_sample",
  gmo: "gmo",
  gmoFacility: "gmo_facility",
  libraryProtocolName: "library_protocol_name",
  name: "name",
  nucleicAcidTypeName: "nucleic_acid_type_name",
  poolName: "pool_name",
  qualityCheck: "quality_check",
  recordType: "record_type",
  requestName: "request_name",
  samplesSubmitted: "samples_submitted",
  selected: "selected",
  type: "type"
};

const RECORD_TYPES = {
  library: "L",
  sample: "S"
};

const FILTER_TYPES = {
  equals: "=",
  notEquals: "!=",
  like: "like"
};

const FILTER_KEYS = {
  typesNotIn: "typesNotIn"
};

const FILTER_OPERATIONS = {
  searchIncomingLibrariesAndSamples: "search_incoming_libraries_and_samples",
  searchLibraryPreparation: "search_library_preparation",
  searchPooling: "search_pooling",
  showLibraries: "showLibraries",
  showSamples: "showSamples",
  onlySamplesSubmitted: "onlySamplesSubmitted",
  onlyGmo: "onlyGmo"
};

const GMO_FACILITY_VALUES = {
  notNeeded: "Not Needed",
  riskAssessmentDone: "Risk Assessment Done"
};

const EDITOR_TYPES = {
  number: "number",
  list: "list",
  select: "select",
  input: "input"
};

const VALIDATOR_RULES = {
  integer: "integer",
  minPrefix: "min:",
  maxPrefix: "max:"
};

const PASTE_ERROR_POPUP = {
  defaultHeight: 220,
  defaultWidth: 600,
  maxHeight: 420,
  baseHeight: 260,
  rowHeight: 34
};

const WARNING_NOTIFICATION_TYPE = "warning";
const IGNORED_FROZEN_COLUMN_WARNING =
  "Using frozen columns that are not the range header";

export default {
  name: "TabulatorTable",
  props: {
    rowData: {
      type: Array
    },
    tableId: {
      type: String,
      default: TABULATOR_TABLE_DEFAULT_ID
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
      tableBuilt: false,
      consoleWarnOriginal: null,
      previousData: null,
      preventEditorBlurHandler: null,
      preserveScrollOnGroupToggleHandler: null,
      pendingGroupScrollRestore: null,
      tableFiltersState: {
        typesIn: [
          {
            field: TABLE_FIELDS.type,
            type: FILTER_TYPES.equals,
            value: RECORD_TYPES.library
          },
          {
            field: TABLE_FIELDS.type,
            type: FILTER_TYPES.equals,
            value: RECORD_TYPES.sample
          }
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
      lastFocusedCell: null,
      lastFocusedCellRef: null,
      showErrorsWindow: false,
      errorsPopupContents: {
        errorsList: [],
        errorsPopupHeight: PASTE_ERROR_POPUP.defaultHeight,
        errorsPopupWidth: PASTE_ERROR_POPUP.defaultWidth
      },
      clipboardPasteParser: null,
      clipboardCopyValueByField: {},
      pasteDefaultsByField: {},
      suppressDataChangedProcessing: false,
      pendingEditClick: null,
      useExtendedDoubleClickEdit: false,
      doubleClickEditDelayMs: DEFAULT_DOUBLE_CLICK_EDIT_DELAY_MS
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
        this.focusErrorsPopupOkButton();
      } else {
        this.$nextTick(() => {
          this.restoreLastFocusedCell();
        });
      }
    }
  },
  mounted() {
    this.initializeTable();
  },
  beforeUnmount() {
    document.removeEventListener(DOM_EVENTS.keydown, this.handleKeyDown);
    const tabulatorElement = this.getTabulatorElement();
    if (tabulatorElement && this.preventEditorBlurHandler) {
      tabulatorElement.removeEventListener(
        DOM_EVENTS.mousedown,
        this.preventEditorBlurHandler,
        true
      );
      tabulatorElement.removeEventListener(
        DOM_EVENTS.click,
        this.preventEditorBlurHandler,
        true
      );
    }
    if (tabulatorElement && this.preserveScrollOnGroupToggleHandler) {
      tabulatorElement.removeEventListener(
        DOM_EVENTS.click,
        this.preserveScrollOnGroupToggleHandler,
        true
      );
      this.preserveScrollOnGroupToggleHandler = null;
    }
    this.tableBuilt = false;
    if (this.consoleWarnOriginal) {
      console.warn = this.consoleWarnOriginal;
      this.consoleWarnOriginal = null;
    }
  },
  methods: {
    closeErrorsWindow() {
      this.showErrorsWindow = false;
    },

    focusErrorsPopupOkButton() {
      this.$nextTick(() => {
        this.$refs?.pasteErrorOkButton?.focus?.();
      });
    },

    isKeyboardEventForThisTable(event) {
      const tableEl =
        this.tabulatorInstance?.element || this.getTabulatorElement?.();
      if (!tableEl) return true;

      const eventTargetTable = event.target?.closest?.(".tabulator") || null;
      const activeElementTable =
        document.activeElement?.closest?.(".tabulator") || null;
      const ownerTable = eventTargetTable || activeElementTable;

      return ownerTable ? ownerTable === tableEl : true;
    },

    setLastFocusedCell(cell) {
      this.lastFocusedCell = cell || null;
      if (!cell) {
        this.lastFocusedCellRef = null;
        return;
      }
      const row = cell.getRow?.();
      const rowData = row?.getData?.() || {};
      const field = cell.getField?.() || null;
      const rowKeyRaw =
        rowData?.tempId ??
        rowData?.pk ??
        rowData?.id ??
        rowData?.[TABLE_FIELDS.barcode] ??
        null;
      const rowPositionRaw = row?.getPosition?.(true);
      const rowPosition = Number.isFinite(rowPositionRaw)
        ? rowPositionRaw
        : null;
      this.lastFocusedCellRef = {
        field,
        rowKey:
          rowKeyRaw === null || rowKeyRaw === undefined ? null : rowKeyRaw,
        rowPosition
      };
    },

    initializeTable() {
      if (this.rowData && this.columnDefs) {
        const rawDelay = Number(this.tableOptions?.doubleClickEditDelayMs);
        this.doubleClickEditDelayMs =
          Number.isFinite(rawDelay) && rawDelay > 0
            ? rawDelay
            : DEFAULT_DOUBLE_CLICK_EDIT_DELAY_MS;
        const requestedEditTriggerEvent =
          this.tableOptions?.editTriggerEvent ||
          TABULATOR_OPTIONS.editTriggerEvent;
        this.useExtendedDoubleClickEdit =
          requestedEditTriggerEvent === TABULATOR_OPTIONS.editTriggerEvent;
        const forwardedTableOptions = { ...(this.tableOptions || {}) };
        delete forwardedTableOptions.doubleClickEditDelayMs;

        this.pasteDefaultsByField = this.buildPasteDefaults(this.columnDefs);
        const options = {
          data: this.rowData,
          columns: this.columnDefs,
          layout: TABULATOR_OPTIONS.layout,
          columnDefaults: {
            headerSort: false,
            headerFilter: false,
            editor: false,
            headerHozAlign: TABULATOR_OPTIONS.headerAlign,
            resizable: TABULATOR_OPTIONS.resizableHeader,
            headerContextMenu: []
          },
          tooltips: true,
          resizableColumns: true,
          groupToggleElement: TABULATOR_OPTIONS.groupToggleElement,
          selectable: true,
          selectableRange: 1,
          selectableRangeColumns: false,
          selectableRangeRows: false,
          selectableRangeClearCells: false,
          editTriggerEvent: this.useExtendedDoubleClickEdit
            ? TABULATOR_OPTIONS.manualEditTriggerEvent
            : requestedEditTriggerEvent,
          clipboard: true,
          clipboardCopyStyled: false,
          clipboardCopyConfig: {
            formatCells: false,
            rowHeaders: false,
            columnHeaders: false
          },
          clipboardCopyRowRange: TABULATOR_OPTIONS.copyRowRange,
          clipboardPasteAction: TABULATOR_OPTIONS.pasteAction,
          clipboardCopyFormatter: (type, output) => {
            if (type !== TABULATOR_OPTIONS.copyPlainType) return output;
            const customCopy = this.buildClipboardOutputFromSelection();
            const withExcelLikeTerminator = (text) => {
              const isMultiCell = text.includes("\t") || text.includes("\n");
              return isMultiCell ? `${text}\n` : text;
            };
            if (customCopy?.usedCustom) {
              return withExcelLikeTerminator(customCopy.output);
            }
            return withExcelLikeTerminator(output);
          },
          clipboardPasteParser: async (clipboard) => {
            this.errorsPopupContents.errorsList = [];
            const errors = [];
            const selectedRanges = this.tabulatorInstance.getRanges();
            if (!selectedRanges?.length) {
              showNotification(
                "Please select a range before pasting.",
                WARNING_NOTIFICATION_TYPE
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
            const totalPastedCells = pastedData.length * pastedColumnCount;
            const useFastPath = totalPastedCells > LARGE_PASTE_CELL_THRESHOLD;
            const rangeColumns = visibleColumns.slice(
              colStart,
              colStart + pastedColumnCount
            );
            const batchUpdates = new Map();
            const isSingleCell = rowStart === rowEnd && colStart === colEnd;
            let targetGroup = null;
            let changedRows = new Set();
            let changedCols = new Set();
            let blockedPaste = false;
            const blockedFields = new Set();

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
                if (columnDef?.disablePaste === true) {
                  blockedPaste = true;
                  if (field) {
                    blockedFields.add(field);
                  }
                  return;
                }
                const isEditable = (() => {
                  const shouldBlockDisabledCells =
                    this.tableOptions?.blockActionsOnDisabledCells === true;
                  const cellEl = cell?.getElement?.();
                  if (
                    shouldBlockDisabledCells &&
                    cellEl?.classList?.contains(
                      TABULATOR_CLASSES.disableEditing
                    )
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
                    barcode: rowData[TABLE_FIELDS.barcode],
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
                    barcode: rowData[TABLE_FIELDS.barcode],
                    rowNumber,
                    message: `${columnTitle}: ${error.message}`
                  });
                }
              });

              const updateKey =
                rowData?.tempId ??
                rowData?.[TABLE_FIELDS.barcode] ??
                `row-${rowNumber}`;
              batchUpdates.set(updateKey, updatedRow);
            });

            const updatedRowsArray = Array.from(batchUpdates.values());
            if (updatedRowsArray.length) {
              if (useFastPath) {
                this.tabulatorInstance.blockRedraw();
                this.tabulatorInstance.updateData(updatedRowsArray);
                this.tabulatorInstance.restoreRedraw();
                this.tabulatorInstance.redraw(true);
              } else {
                this.tabulatorInstance.updateData(updatedRowsArray);

                if (changedRows.size) {
                  changedRows.forEach((rowPosition) => {
                    const row =
                      this.tabulatorInstance.getRowFromPosition(rowPosition);
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
                errorsPopupHeight: Math.min(
                  PASTE_ERROR_POPUP.maxHeight,
                  PASTE_ERROR_POPUP.baseHeight +
                    errors.length * PASTE_ERROR_POPUP.rowHeight
                ),
                errorsPopupWidth: PASTE_ERROR_POPUP.defaultWidth
              };
              this.showErrorsWindow = true;
            }
            if (blockedPaste) {
              if (blockedFields.has(TABLE_FIELDS.barcode)) {
                showNotification(
                  "Barcode is read-only and cannot be pasted.",
                  WARNING_NOTIFICATION_TYPE
                );
              } else {
                showNotification(
                  "Paste is disabled for some columns.",
                  WARNING_NOTIFICATION_TYPE
                );
              }
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
          debugInvalidOptions: false,
          ...forwardedTableOptions
        };

        this.consoleWarnOriginal = console.warn;
        console.warn = (...args) => {
          const first = args?.[0];
          if (
            typeof first === "string" &&
            first.includes(IGNORED_FROZEN_COLUMN_WARNING)
          ) {
            return;
          }
          this.consoleWarnOriginal?.(...args);
        };

        this.tabulatorInstance = markRaw(
          new Tabulator(`${TABULATOR_SELECTOR_PREFIX}${this.tableId}`, options)
        );
        this.clipboardPasteParser = options.clipboardPasteParser;
        this.clipboardCopyValueByField = this.buildClipboardValueLookup(
          this.columnDefs
        );

        this.tabulatorInstance.on(TABULATOR_EVENTS.tableBuilt, () => {
          this.tableBuilt = true;
          document.addEventListener(DOM_EVENTS.keydown, this.handleKeyDown);

          // The range-select module auto-selects cell (0,0) on build, which
          // renders as a gray/blue highlight on the first row until the user
          // clicks elsewhere. Removing the range doesn't fully prevent this:
          // the module always keeps one active range and immediately
          // recreates a default one, which can end up with real bounds and
          // get painted anyway. So also gate the paint itself via CSS until
          // the first real interaction (see .pending-range-interaction).
          this.tabulatorInstance.getRanges().forEach((range) => range.remove());

          const tabulatorElement = this.getTabulatorElement();
          tabulatorElement.classList.add(
            TABULATOR_CLASSES.pendingRangeInteraction
          );
          const clearPendingRangeInteraction = () => {
            tabulatorElement.classList.remove(
              TABULATOR_CLASSES.pendingRangeInteraction
            );
          };
          tabulatorElement.addEventListener(
            DOM_EVENTS.mousedown,
            clearPendingRangeInteraction,
            { capture: true, once: true }
          );
          tabulatorElement.addEventListener(
            DOM_EVENTS.keydown,
            clearPendingRangeInteraction,
            { capture: true, once: true }
          );
          tabulatorElement.addEventListener(
            DOM_EVENTS.keydown,
            (e) => {
              const tag = e.target && e.target.tagName;
              if (
                (tag === HTML_TAGS.input || tag === HTML_TAGS.textarea) &&
                (e.key === KEY_NAMES.arrowLeft ||
                  e.key === KEY_NAMES.arrowRight)
              ) {
                e.stopPropagation();
              }
            },
            true
          );

          if (this.preventEditorBlurHandler) {
            tabulatorElement.removeEventListener(
              DOM_EVENTS.mousedown,
              this.preventEditorBlurHandler,
              true
            );
            tabulatorElement.removeEventListener(
              DOM_EVENTS.click,
              this.preventEditorBlurHandler,
              true
            );
          }

          this.preventEditorBlurHandler = (event) => {
            if (event.target.closest(TABULATOR_SELECTORS.editingCell)) {
              event.stopPropagation();
            }
          };

          tabulatorElement.addEventListener(
            DOM_EVENTS.mousedown,
            this.preventEditorBlurHandler,
            true
          );
          tabulatorElement.addEventListener(
            DOM_EVENTS.click,
            this.preventEditorBlurHandler,
            true
          );
          if (this.tableOptions.preserveScrollOnGroupToggle) {
            if (this.preserveScrollOnGroupToggleHandler) {
              tabulatorElement.removeEventListener(
                DOM_EVENTS.click,
                this.preserveScrollOnGroupToggleHandler,
                true
              );
            }
            this.preserveScrollOnGroupToggleHandler = (event) => {
              const groupRow = event.target.closest(
                TABULATOR_SELECTORS.groupRow
              );
              if (!groupRow) return;
              const holder = tabulatorElement.querySelector(
                TABULATOR_SELECTORS.tableHolder
              );
              const outer = tabulatorElement.closest(
                TABULATOR_SELECTORS.tableContainer
              );
              this.pendingGroupScrollRestore = {
                holderScrollTop: holder ? holder.scrollTop : null,
                outerScrollTop: outer ? outer.scrollTop : null
              };
            };
            tabulatorElement.addEventListener(
              DOM_EVENTS.click,
              this.preserveScrollOnGroupToggleHandler,
              true
            );
          }
          if (this.tableGroupsConfig.noGroupByClass) {
            tabulatorElement.classList.add(TABULATOR_CLASSES.noGroupBy);
          } else {
            tabulatorElement.classList.remove(TABULATOR_CLASSES.noGroupBy);
          }

          this.tabulatorInstance.setGroupBy(this.tableGroupsConfig.groupBy);

          if (this.enableDefaultFilters) {
            let typesNotIn = this.tableFiltersState.typesNotIn;
            let flatFilters = Object.entries(this.tableFiltersState)
              .filter(([key, value]) => {
                if (key === FILTER_KEYS.typesNotIn) return false;
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

        this.tabulatorInstance.on(
          TABULATOR_EVENTS.dataChanged,
          (updatedData) => {
            if (this.suppressDataChangedProcessing) {
              return;
            }
            if (
              typeof this.tableOptions.onBatchCellValueChanged !== "function"
            ) {
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
                  key !== TABLE_FIELDS.selected &&
                  key !== TABLE_FIELDS.samplesSubmitted &&
                  key !== TABLE_FIELDS.qualityCheck
                ) {
                  if (key === TABLE_FIELDS.gmoFacility) {
                    if (row[key] !== oldRow[key]) {
                      if (
                        row[key] === GMO_FACILITY_VALUES.notNeeded ||
                        row[key] === false
                      ) {
                        changedFields[key] = false;
                      } else if (
                        row[key] === GMO_FACILITY_VALUES.riskAssessmentDone ||
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
                  tempId: row.tempId,
                  [TABLE_FIELDS.recordType]: row[TABLE_FIELDS.recordType],
                  ...changedFields
                });
              }
            });

            this.previousData = currentData;

            if (batchChanges.length > 0) {
              this.tableOptions.onBatchCellValueChanged(batchChanges);
            }
          }
        );

        this.tabulatorInstance.on(TABULATOR_EVENTS.renderComplete, () => {
          const rows = this.tabulatorInstance?.rowManager?.activeRows || [];
          this.updateGroupValuesFromRows(rows);
          if (this.tableOptions.handleRenderComplete) {
            this.tableOptions.handleRenderComplete();
          }
          if (this.pendingGroupScrollRestore) {
            const tabulatorEl = this.getTabulatorElement();
            const holder =
              tabulatorEl?.querySelector(TABULATOR_SELECTORS.tableHolder) ||
              null;
            const outer =
              tabulatorEl?.closest?.(TABULATOR_SELECTORS.tableContainer) ||
              null;
            const { holderScrollTop, outerScrollTop } =
              this.pendingGroupScrollRestore;
            this.pendingGroupScrollRestore = null;
            const restore = () => {
              if (holder && holderScrollTop !== null) {
                holder.scrollTop = holderScrollTop;
              }
              if (outer && outerScrollTop !== null) {
                outer.scrollTop = outerScrollTop;
              }
            };
            requestAnimationFrame(() => {
              restore();
              requestAnimationFrame(restore);
            });
          }
        });

        this.tabulatorInstance.on(TABULATOR_EVENTS.cellEdited, (cell) => {
          if (this.tableOptions.handleCellEdited) {
            this.tableOptions.handleCellEdited(cell);
          }
        });

        this.tabulatorInstance.on(TABULATOR_EVENTS.cellClick, (e, cell) => {
          const clickedCell =
            (cell && typeof cell.getField === "function" ? cell : null) ||
            (e && typeof e.getField === "function" ? e : null);
          if (!clickedCell) return;
          this.setLastFocusedCell(clickedCell);
          if (this.useExtendedDoubleClickEdit) {
            this.handleExtendedDoubleClickEdit(clickedCell);
          }
        });
        this.tabulatorInstance.on(TABULATOR_EVENTS.cellFocused, (cell) => {
          this.setLastFocusedCell(cell);
        });
        this.tabulatorInstance.on(TABULATOR_EVENTS.cellContext, (e, cell) => {
          this.setLastFocusedCell(cell);
        });

        this.tabulatorInstance.on(TABULATOR_EVENTS.clipboardCopied, () => {
          if (this.tableOptions.fakeLoadingStart) {
            this.tableOptions.fakeLoadingStart();
          }
          if (this.tableOptions.fakeLoadingStop) {
            this.tableOptions.fakeLoadingStop();
          }
          this.restoreLastFocusedCell();
        });

        this.tabulatorInstance.on(TABULATOR_EVENTS.clipboardPasted, () => {
          if (this.errorsPopupContents.errorsList.length !== 0) {
            return;
          }
          if (this.tableOptions.fakeLoadingStart) {
            this.tableOptions.fakeLoadingStart();
          }
          if (this.tableOptions.fakeLoadingStop) {
            this.tableOptions.fakeLoadingStop();
          }
          this.restoreLastFocusedCell();
        });

        this.tabulatorInstance.on(TABULATOR_EVENTS.columnResized, (column) => {
          if (this.tableOptions.handleColumnResized) {
            this.tableOptions.handleColumnResized(column);
          }
        });

        this.tabulatorInstance.on(
          TABULATOR_EVENTS.columnVisibilityChanged,
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
      if (this.groupSort.field === TABLE_FIELDS.requestName) {
        const getNumber = (val) => {
          const num = parseInt(val.split(GROUP_VALUE_SEPARATOR)[0], 10);
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
      if (this.tabulatorInstance && this.tableBuilt) {
        this.tabulatorInstance.setData(this.rowData);
      }
    },

    updateTableColumns() {
      if (!this.tabulatorInstance || !this.tableBuilt) return;
      this.clipboardCopyValueByField = this.buildClipboardValueLookup(
        this.columnDefs
      );
      this.pasteDefaultsByField = this.buildPasteDefaults(this.columnDefs);
      this.tabulatorInstance.blockRedraw();
      this.tabulatorInstance.setColumns(this.columnDefs);
      this.getTabulatorElement().classList.remove(TABULATOR_CLASSES.noGroupBy);
      this.showAllGroups();
      if (this.groupBy) this.tabulatorInstance.setGroupBy(this.groupBy);
      this.tabulatorInstance.restoreRedraw();
    },

    refreshPreviousDataSnapshot() {
      this.previousData = JSON.stringify(
        this.tabulatorInstance?.getData?.() || []
      );
    },

    beginBulkMutation() {
      this.suppressDataChangedProcessing = true;
    },

    endBulkMutation() {
      this.suppressDataChangedProcessing = false;
      this.refreshPreviousDataSnapshot();
    },

    async triggerClipboardPaste() {
      if (!this.clipboardPasteParser) {
        this.tabulatorInstance?.pasteFromClipboard?.();
        return;
      }
      try {
        if (!navigator?.clipboard?.readText) {
          this.tabulatorInstance?.pasteFromClipboard?.();
          return;
        }
        const text = await navigator.clipboard.readText();
        if (!text) {
          showNotification("Clipboard is empty.", WARNING_NOTIFICATION_TYPE);
          return;
        }
        await this.clipboardPasteParser(text);
        if (this.errorsPopupContents.errorsList.length === 0) {
          if (this.tableOptions.fakeLoadingStart) {
            this.tableOptions.fakeLoadingStart();
          }
          if (this.tableOptions.fakeLoadingStop) {
            this.tableOptions.fakeLoadingStop();
          }
        } else {
          this.focusErrorsPopupOkButton();
        }
        this.restoreLastFocusedCell();
      } catch (error) {
        this.tabulatorInstance?.pasteFromClipboard?.();
      }
    },

    buildPasteDefaults(columns = []) {
      const map = {};
      const walk = (col) => {
        if (!col || typeof col !== "object") return;
        if (Array.isArray(col.columns)) {
          col.columns.forEach(walk);
          return;
        }
        if (col.field && col.defaultOnEmptyPaste !== undefined) {
          map[col.field] = col.defaultOnEmptyPaste;
        }
      };
      columns.forEach(walk);
      return map;
    },

    // Make sure that records in rowData have "type" field, in order for these filters to work. Check the definition of "this.tableFiltersState" to get more context.
    // If "type" is not defined, then the records won't show up in the table.
    filterTableData(operation, keyword) {
      let typesIn = this.tableFiltersState.typesIn;
      let typesNotIn = this.tableFiltersState.typesNotIn;
      switch (operation) {
        case FILTER_OPERATIONS.searchIncomingLibrariesAndSamples:
          if (keyword !== "") {
            this.tableFiltersState.search = [
              [
                {
                  field: TABLE_FIELDS.name,
                  type: FILTER_TYPES.like,
                  value: keyword
                },
                {
                  field: TABLE_FIELDS.requestName,
                  type: FILTER_TYPES.like,
                  value: keyword
                },
                {
                  field: TABLE_FIELDS.barcode,
                  type: FILTER_TYPES.like,
                  value: keyword
                },
                {
                  field: TABLE_FIELDS.nucleicAcidTypeName,
                  type: FILTER_TYPES.like,
                  value: keyword
                },
                {
                  field: TABLE_FIELDS.libraryProtocolName,
                  type: FILTER_TYPES.like,
                  value: keyword
                },
                {
                  field: TABLE_FIELDS.comments,
                  type: FILTER_TYPES.like,
                  value: keyword
                },
                {
                  field: TABLE_FIELDS.commentsFacility,
                  type: FILTER_TYPES.like,
                  value: keyword
                }
              ]
            ];
          } else {
            delete this.tableFiltersState.search;
          }
          break;
        case FILTER_OPERATIONS.searchLibraryPreparation:
          if (keyword !== "") {
            this.tableFiltersState.search = [
              [
                {
                  field: TABLE_FIELDS.name,
                  type: FILTER_TYPES.like,
                  value: keyword
                },
                {
                  field: TABLE_FIELDS.requestName,
                  type: FILTER_TYPES.like,
                  value: keyword
                },
                {
                  field: TABLE_FIELDS.barcode,
                  type: FILTER_TYPES.like,
                  value: keyword
                },
                {
                  field: TABLE_FIELDS.libraryProtocolName,
                  type: FILTER_TYPES.like,
                  value: keyword
                },
                {
                  field: TABLE_FIELDS.commentsLibrarySample,
                  type: FILTER_TYPES.like,
                  value: keyword
                },
                {
                  field: TABLE_FIELDS.comments,
                  type: FILTER_TYPES.like,
                  value: keyword
                },
                {
                  field: TABLE_FIELDS.commentsFacility,
                  type: FILTER_TYPES.like,
                  value: keyword
                }
              ]
            ];
          } else {
            delete this.tableFiltersState.search;
          }
          break;
        case FILTER_OPERATIONS.searchPooling:
          if (keyword !== "") {
            this.tableFiltersState.search = [
              [
                {
                  field: TABLE_FIELDS.name,
                  type: FILTER_TYPES.like,
                  value: keyword
                },
                {
                  field: TABLE_FIELDS.requestName,
                  type: FILTER_TYPES.like,
                  value: keyword
                },
                {
                  field: TABLE_FIELDS.poolName,
                  type: FILTER_TYPES.like,
                  value: keyword
                },
                {
                  field: TABLE_FIELDS.barcode,
                  type: FILTER_TYPES.like,
                  value: keyword
                }
              ]
            ];
          } else {
            delete this.tableFiltersState.search;
          }
          break;
        case FILTER_OPERATIONS.showLibraries:
          const foundInL = typesIn.find(
            (item) => item.value === RECORD_TYPES.library
          );
          if (keyword === true && !foundInL) {
            typesIn.push({
              field: TABLE_FIELDS.type,
              type: FILTER_TYPES.equals,
              value: RECORD_TYPES.library
            });
            typesNotIn = typesNotIn.filter(
              (item) => item.value !== RECORD_TYPES.library
            );
          } else if (keyword === false && foundInL) {
            typesIn = typesIn.filter(
              (item) => item.value !== RECORD_TYPES.library
            );
            typesNotIn.push({
              field: TABLE_FIELDS.type,
              type: FILTER_TYPES.notEquals,
              value: RECORD_TYPES.library
            });
          }
          this.tableFiltersState.typesIn = typesIn;
          this.tableFiltersState.typesNotIn = typesNotIn;
          break;
        case FILTER_OPERATIONS.showSamples:
          const foundInS = typesIn.find(
            (item) => item.value === RECORD_TYPES.sample
          );
          if (keyword === true && !foundInS) {
            typesIn.push({
              field: TABLE_FIELDS.type,
              type: FILTER_TYPES.equals,
              value: RECORD_TYPES.sample
            });
            typesNotIn = typesNotIn.filter(
              (item) => item.value !== RECORD_TYPES.sample
            );
          } else if (keyword === false && foundInS) {
            typesIn = typesIn.filter(
              (item) => item.value !== RECORD_TYPES.sample
            );
            typesNotIn.push({
              field: TABLE_FIELDS.type,
              type: FILTER_TYPES.notEquals,
              value: RECORD_TYPES.sample
            });
          }
          this.tableFiltersState.typesIn = typesIn;
          this.tableFiltersState.typesNotIn = typesNotIn;
          break;
        case FILTER_OPERATIONS.onlySamplesSubmitted:
          if (keyword === true) {
            this.tableFiltersState.onlySamplesSubmitted = {
              field: TABLE_FIELDS.samplesSubmitted,
              type: FILTER_TYPES.equals,
              value: keyword
            };
          } else {
            delete this.tableFiltersState.onlySamplesSubmitted;
          }
          break;
        case FILTER_OPERATIONS.onlyGmo:
          if (keyword === true) {
            this.tableFiltersState.onlyGmo = {
              field: TABLE_FIELDS.gmo,
              type: FILTER_TYPES.equals,
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
          if (key === FILTER_KEYS.typesNotIn) return false;
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

    getCellIdentity(cell) {
      if (!cell) return null;
      const row = cell.getRow?.();
      const rowData = cell.getRow?.().getData?.() || {};
      const field = cell.getField?.() || null;
      const fallbackPosition = row?.getPosition?.(true);
      const rowKeyRaw =
        rowData?.tempId ??
        rowData?.pk ??
        rowData?.id ??
        rowData?.[TABLE_FIELDS.barcode] ??
        null;
      const rowKey =
        rowKeyRaw !== null && rowKeyRaw !== undefined
          ? rowKeyRaw
          : Number.isFinite(fallbackPosition)
            ? `pos:${fallbackPosition}`
            : null;
      if (field === null || rowKey === null || rowKey === undefined) {
        return null;
      }
      return { rowKey, field };
    },

    isCellEditableForManualEdit(cell) {
      if (!cell) return false;
      const columnDef = cell.getColumn?.().getDefinition?.() || {};
      if (columnDef.editor === false) return false;
      const shouldBlockDisabledCells =
        this.tableOptions?.blockActionsOnDisabledCells === true;
      const cellEl = cell.getElement?.();
      if (
        shouldBlockDisabledCells &&
        cellEl?.classList?.contains(TABULATOR_CLASSES.disableEditing)
      ) {
        return false;
      }
      if (typeof columnDef.editable === "boolean") {
        return columnDef.editable;
      }
      if (typeof columnDef.editable === "function") {
        const rowData = cell.getRow?.().getData?.() || {};
        return Boolean(
          columnDef.editable({
            getRow: () => ({ getData: () => rowData })
          })
        );
      }
      return Boolean(columnDef.editor);
    },

    openDropdownEditorIfNeeded(cell) {
      const columnDef = cell?.getColumn?.().getDefinition?.() || {};
      const editorType = columnDef?.editor;
      const isDropdownEditor =
        editorType === EDITOR_TYPES.list || editorType === EDITOR_TYPES.select;
      if (!isDropdownEditor) return;
      const maxAttempts = 8;
      const tryOpen = (attempt = 0) => {
        const cellEl = cell?.getElement?.() || null;
        const active = document.activeElement;
        const editorEl =
          (cellEl && cellEl.querySelector(TABULATOR_SELECTORS.editorInput)) ||
          (active && cellEl?.contains?.(active) ? active : null);
        if (!editorEl) {
          if (attempt < maxAttempts) {
            setTimeout(() => tryOpen(attempt + 1), 16);
          }
          return;
        }
        editorEl.focus?.();
        try {
          editorEl.dispatchEvent(
            new KeyboardEvent(DOM_EVENTS.keydown, {
              key: KEY_NAMES.arrowDown,
              bubbles: true
            })
          );
        } catch (error) {
          // no-op
        }
        editorEl.dispatchEvent(
          new MouseEvent(DOM_EVENTS.mousedown, {
            bubbles: true,
            cancelable: true
          })
        );
        editorEl.dispatchEvent(
          new MouseEvent(DOM_EVENTS.mouseup, {
            bubbles: true,
            cancelable: true
          })
        );
        if (typeof editorEl.click === "function") {
          editorEl.click();
        }
      };
      setTimeout(() => tryOpen(0), 0);
    },

    handleExtendedDoubleClickEdit(cell) {
      if (!cell || !this.tabulatorInstance) return;
      const identity = this.getCellIdentity(cell);
      if (!identity) return;
      const now = Date.now();
      const previous = this.pendingEditClick;
      const isSecondClickSameCell =
        previous &&
        previous.field === identity.field &&
        previous.rowKey === identity.rowKey &&
        now - previous.timestamp <= this.doubleClickEditDelayMs;

      if (isSecondClickSameCell) {
        this.pendingEditClick = null;
        const editable = this.isCellEditableForManualEdit(cell);
        if (editable) {
          requestAnimationFrame(() => {
            cell.edit?.();
            this.openDropdownEditorIfNeeded(cell);
          });
        }
        return;
      }

      this.pendingEditClick = {
        ...identity,
        timestamp: now
      };
    },

    getFocusCandidateCell() {
      const table = this.tabulatorInstance;
      const ranges = table?.getRanges?.() || [];
      const rangeCell = ranges[0]?.getCells?.()?.[0]?.[0] || null;
      const isCellUsable = (cell) => {
        const el = cell?.getElement?.();
        return Boolean(el && el.isConnected);
      };
      if (isCellUsable(this.lastFocusedCell)) {
        return this.lastFocusedCell;
      }
      const ref = this.lastFocusedCellRef;
      if (table && ref?.field) {
        let row = null;
        if (ref.rowKey !== null && ref.rowKey !== undefined) {
          row = table.getRow?.(ref.rowKey) || null;
        }
        if (!row && Number.isFinite(ref.rowPosition)) {
          row = table.getRowFromPosition?.(ref.rowPosition) || null;
        }
        const resolved = row?.getCell?.(ref.field) || null;
        if (isCellUsable(resolved)) {
          this.lastFocusedCell = resolved;
          return resolved;
        }
      }
      return rangeCell || this.lastFocusedCell || null;
    },

    restoreLastFocusedCell() {
      const table = this.tabulatorInstance;
      if (!table) return;
      if (this.showErrorsWindow) {
        this.focusErrorsPopupOkButton();
        return;
      }
      const tableEl = table.element || this.getTabulatorElement?.() || null;
      const focusTableElement = () => {
        if (!tableEl) return;
        if (!tableEl.hasAttribute("tabindex")) {
          tableEl.setAttribute("tabindex", "-1");
        }
        try {
          tableEl.focus({ preventScroll: true });
        } catch (error) {
          tableEl.focus();
        }
      };
      const attemptRestore = () => {
        const cell = this.getFocusCandidateCell();
        if (!cell) {
          focusTableElement();
          return false;
        }
        const el = cell.getElement?.();
        if (!el || !el.isConnected) {
          focusTableElement();
          return false;
        }
        if (!el.hasAttribute("tabindex")) {
          el.setAttribute("tabindex", "-1");
        }
        try {
          el.focus({ preventScroll: true });
        } catch (error) {
          el.focus();
        }
        this.setLastFocusedCell(cell);
        if (typeof table.addRange === "function") {
          const ranges = table.getRanges?.() || [];
          if (!ranges.length) {
            table.addRange(cell, cell);
          }
        }
        return true;
      };

      if (!attemptRestore()) {
        requestAnimationFrame(() => {
          attemptRestore();
        });
        return;
      }
    },

    handleKeyDown(event) {
      const isDeleteOrBackspace =
        event.key === KEY_NAMES.delete || event.key === KEY_NAMES.backspace;
      const isEnter = event.key === KEY_NAMES.enter;
      const isEscape = event.key === KEY_NAMES.escape;
      const key = event.key?.toLowerCase?.();
      const isCtrl = event.ctrlKey || event.metaKey;
      const isCut = isCtrl && key === KEY_NAMES.cut;
      const isCopy = isCtrl && key === KEY_NAMES.copy;
      const isPaste = isCtrl && key === KEY_NAMES.paste;
      const isSelectAll = isCtrl && key === KEY_NAMES.selectAll;
      const isPrintableKey =
        event.key.length === 1 &&
        !event.ctrlKey &&
        !event.metaKey &&
        !event.altKey;
      if (isEscape && this.showErrorsWindow) {
        this.closeErrorsWindow();
        return;
      }
      const isEditorElement = (element) =>
        element &&
        (element.tagName === HTML_TAGS.input ||
          element.tagName === HTML_TAGS.select ||
          element.tagName === HTML_TAGS.textarea ||
          element.isContentEditable ||
          element.closest?.(TABULATOR_SELECTORS.editingCell) ||
          element.closest?.(TABULATOR_SELECTORS.editList));
      const eventPath =
        typeof event.composedPath === "function" ? event.composedPath() : [];
      const eventStartedInEditor = eventPath.some(
        (element) =>
          element?.classList?.contains?.("tabulator-editing") ||
          element?.classList?.contains?.("tabulator-edit-list")
      );
      const activeEditorElement =
        isEditorElement(document.activeElement) ||
        isEditorElement(event.target) ||
        eventStartedInEditor;
      if (activeEditorElement) {
        return;
      }
      if (!this.isKeyboardEventForThisTable(event)) {
        return;
      }

      if (isSelectAll) {
        if (!this.tableOptions?.enableSelectAllRange) {
          return;
        }
        const rows = this.tabulatorInstance?.getRows?.() || [];
        const columns = this.tabulatorInstance?.getColumns?.() || [];
        const visibleColumns = columns.filter((col) => col?._column?.visible);
        const firstRow = rows[0];
        const lastRow = rows[rows.length - 1];
        const firstCol = visibleColumns[0];
        const lastCol = visibleColumns[visibleColumns.length - 1];
        if (firstRow && lastRow && firstCol && lastCol) {
          const startCell = firstRow.getCell(firstCol.getField());
          const endCell = lastRow.getCell(lastCol.getField());
          if (startCell && endCell) {
            event.preventDefault();
            this.tabulatorInstance?.addRange?.(startCell, endCell);
            this.restoreLastFocusedCell();
          }
        }
        return;
      }
      const selectedRanges = this.tabulatorInstance.getRanges?.() || [];
      const rangeCells = selectedRanges[0]?.getCells?.() || [];
      const getIsEditable = (cell, rowData) => {
        const shouldBlockDisabledCells =
          this.tableOptions?.blockActionsOnDisabledCells === true;
        const cellEl = cell.getElement?.();
        if (
          shouldBlockDisabledCells &&
          cellEl?.classList?.contains(TABULATOR_CLASSES.disableEditing)
        ) {
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
      const clearSelectedRange = () => {
        if (!rangeCells.length) return;
        const rowOriginals = new Map();
        const rowUpdates = new Map();
        const clearedFieldsByRow = new Map();
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
            if (fieldName) {
              if (!clearedFieldsByRow.has(rowComp)) {
                clearedFieldsByRow.set(rowComp, new Set());
              }
              clearedFieldsByRow.get(rowComp).add(fieldName);
            }
          });
        });
        if (rowUpdates.size === 0) {
          return;
        }
        if (this.tableOptions.fakeLoadingStart) {
          this.tableOptions.fakeLoadingStart();
        }
        if (typeof this.tableOptions.handleRangeClearStart === "function") {
          this.tableOptions.handleRangeClearStart();
        }
        this.beginBulkMutation();
        try {
          rowUpdates.forEach((data, rowComp) => {
            rowComp?.update?.(data);
          });
        } finally {
          this.endBulkMutation();
        }
        if (
          rowUpdates.size &&
          typeof this.tableOptions.handleDeleteApplied === "function"
        ) {
          this.tableOptions.handleDeleteApplied(
            Array.from(rowUpdates.values())
          );
        }
        if (
          clearedFieldsByRow.size &&
          typeof this.tableOptions.handleRangeCleared === "function"
        ) {
          const payload = Array.from(clearedFieldsByRow.entries()).map(
            ([rowComp, fields]) => ({
              rowData: rowComp?.getData?.() || {},
              fields: Array.from(fields)
            })
          );
          this.tableOptions.handleRangeCleared(payload);
        }
        if (this.tableOptions.fakeLoadingStop) {
          this.tableOptions.fakeLoadingStop();
        }
        if (typeof this.tableOptions.handleRangeClearEnd === "function") {
          this.tableOptions.handleRangeClearEnd();
        }
      };

      if (isCut) {
        if (!rangeCells.length) return;
        const hasEditable = rangeCells.some((row) =>
          row.some((cell) => {
            const rowData = cell.getRow?.().getData?.() || {};
            return getIsEditable(cell, rowData);
          })
        );
        if (!hasEditable) return;
        event.preventDefault();
        this.tabulatorInstance?.copyToClipboard?.();
        clearSelectedRange();
        this.restoreLastFocusedCell();
        return;
      }

      if (isCopy) {
        requestAnimationFrame(() => this.restoreLastFocusedCell());
      }

      if (isPaste) {
        requestAnimationFrame(() => this.restoreLastFocusedCell());
      }

      if (isDeleteOrBackspace) {
        if (!rangeCells.length) return;
        clearSelectedRange();
        event.preventDefault();
        this.restoreLastFocusedCell();
        return;
      }
      if (isEnter) {
        const firstCell = rangeCells[0]?.[0] || this.getFocusCandidateCell();
        if (!firstCell) return;
        const rowData = firstCell.getRow?.().getData?.() || {};
        if (!getIsEditable(firstCell, rowData)) return;
        event.preventDefault();
        firstCell.edit?.();
        this.openDropdownEditorIfNeeded(firstCell);
        return;
      }
      if (isPrintableKey) {
        const firstCell = rangeCells[0]?.[0];
        if (firstCell) {
          const rowData = firstCell.getRow?.().getData?.() || {};
          if (!getIsEditable(firstCell, rowData)) {
            return;
          }
          firstCell.edit();
          const input = document.activeElement;
          if (
            input &&
            (document.activeElement.tagName === HTML_TAGS.input ||
              document.activeElement.tagName === HTML_TAGS.textarea)
          ) {
            input.value = "";
            input.dispatchEvent(new Event(DOM_EVENTS.input, { bubbles: true }));
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
          const field = cell.getField?.();
          const customGetter =
            columnDef.clipboardCopyValue ||
            (field ? this.clipboardCopyValueByField[field] : null);
          if (typeof customGetter === "function") {
            usedCustom = true;
            const custom = customGetter(cell);
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

    buildClipboardValueLookup(columns = [], map = {}) {
      columns.forEach((column) => {
        if (!column) return;
        if (Array.isArray(column.columns)) {
          this.buildClipboardValueLookup(column.columns, map);
        } else if (column.field && column.clipboardCopyValue) {
          map[column.field] = column.clipboardCopyValue;
        }
      });
      return map;
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
            if (res !== true)
              throw new Error(res || "Entered value is invalid.");
          } else if (typeof rule === "string") {
            const trimmed = rule.trim().toLowerCase();
            if (trimmed === VALIDATOR_RULES.integer) {
              if (!Number.isInteger(val))
                throw new Error("Entered value must be an integer.");
            } else if (trimmed.startsWith(VALIDATOR_RULES.minPrefix)) {
              const v = Number(trimmed.slice(4));
              if (!Number.isNaN(v) && val < v)
                throw new Error(
                  `Entered value should be more than ${new Intl.NumberFormat().format(v)}.`
                );
            } else if (trimmed.startsWith(VALIDATOR_RULES.maxPrefix)) {
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
        case EDITOR_TYPES.number: {
          const str = String(value).trim();
          if (str === "") {
            const fieldName = columnDef.field;
            const defaultValue =
              columnDef.defaultOnEmptyPaste ??
              (fieldName ? this.pasteDefaultsByField[fieldName] : undefined);
            if (defaultValue !== undefined) {
              return defaultValue;
            }
            return "";
          }
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
            else if (hasMin)
              message = `Entered value should be more than ${minStr}.`;
            else message = `Entered value should be less than ${maxStr}.`;
            throw new Error(message);
          }
          return numValue;
        }
        case EDITOR_TYPES.list: {
          if (value === "" || value === undefined || value === null) {
            const fieldName = columnDef.field;
            const defaultValue =
              columnDef.defaultOnEmptyPaste ??
              (fieldName ? this.pasteDefaultsByField[fieldName] : undefined);
            if (defaultValue !== undefined) {
              return defaultValue;
            }
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
                (label) =>
                  String(label).trim().toLowerCase() === normalizedLower
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
              if (
                resolved !== undefined &&
                resolved !== null &&
                resolved !== ""
              ) {
                applyValidators(resolved);
                return resolved;
              }
            }
            if (columnDef.validator) {
              applyValidators(value);
              return value;
            }
            throw new Error("Entered value must be from the dropdown list.");
          }
          return value;
        }
        case EDITOR_TYPES.input:
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
  font-family: var(--app-font-family);
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

/* Tabulator's range-select module always keeps one active range, and
   recreates a default one (at cell 0,0) the instant we remove it on build —
   which can end up with real bounds and get painted before the user ever
   interacts with the table. Suppress the paint until a real click/keypress
   happens, so no cell looks pre-selected on load. */
.normal-tabulator-table.pending-range-interaction
  .tabulator-cell.tabulator-range-selected {
  background-color: inherit !important;
  color: inherit !important;
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

.normal-tabulator-table
  .no-group-by
  .tabulator-row-odd:nth-child(1)
  .tabulator-cell {
  border-top: 1px solid #d0d0d0 !important;
}

.normal-tabulator-table .checkbox-column:not(.tabulator-col) {
  padding: 10px 0px !important;
}

.normal-tabulator-table
  .title-field-group
  > .tabulator-col-content
  > div
  > div {
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
.tabulator-edit-list
  .tabulator-edit-list-item.active
  .tabulator-edit-list-item-label,
.tabulator-edit-list
  .tabulator-edit-list-item.focused
  .tabulator-edit-list-item-label {
  background-color: #2967c5;
  color: #fff !important;
  outline: none;
}

.normal-tabulator-table .tabulator-cell.required-empty {
  background-color: #f5bcbc;
}

.normal-tabulator-table
  .tabulator-cell.cell-invalid:not(.tabulator-range-selected) {
  background-color: #f5bcbc !important;
}

.normal-tabulator-table
  .tabulator-row.row-has-errors
  .tabulator-cell.required-filled:not(.disable-editing) {
  background-color: #f9e5e5;
}

.normal-tabulator-table
  .tabulator-row.row-has-errors
  .tabulator-cell:not(.required-empty):not(.cell-invalid):not(
    .tabulator-range-selected
  ):not(.disable-editing) {
  background-color: #f9e5e5;
}

.normal-tabulator-table
  .tabulator-row.row-has-errors
  .tabulator-cell.disable-editing:not(.required-empty):not(.cell-invalid):not(
    .tabulator-range-selected
  ) {
  background-color: #f9e5e5;
}

.normal-tabulator-table
  .tabulator-row.row-all-valid
  .tabulator-cell.required-filled:not(.disable-editing),
.normal-tabulator-table
  .tabulator-row.row-all-valid
  .tabulator-cell:not(.required-empty):not(.cell-invalid):not(
    .tabulator-range-selected
  ):not(.disable-editing) {
  background-color: #e4fae3;
}

.normal-tabulator-table
  .tabulator-row.row-all-valid
  .tabulator-cell.disable-editing:not(.required-empty):not(.cell-invalid):not(
    .tabulator-range-selected
  ) {
  background-color: #e4fae3;
}

.normal-tabulator-table .tabulator-cell.disable-editing {
  background-image: repeating-linear-gradient(
    135deg,
    rgba(156, 163, 175, 0.3),
    rgba(156, 163, 175, 0.3) 6px,
    rgba(255, 255, 255, 0) 6px,
    rgba(255, 255, 255, 0) 12px
  ) !important;
  color: #6f7680 !important;
  cursor: not-allowed;
}
</style>

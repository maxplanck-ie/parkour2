<template>
    <!-- This Tabulator Table uses Virtual DOM and performs smoothly for usecase with plenty of records -->
    <!-- Table Element -->
    <div class="lite-tabulator-table" style="height: 100%;">
        <div id="tabulatorTable" ref="tabulatorTableRef"></div>
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
                    renderVertical: "basic",
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

                    this.tabulatorInstance.restoreRedraw();
                });

                this.tabulatorInstance.on("groupVisibilityChanged", (group, visible) => {
                    console.log(group)
                    if (group._group.visible) {
                        this.tabulatorInstance.getGroups().forEach(g => {
                            if (g._group.key !== group._group.key && g._group.visible) {
                                g.toggle();
                            }
                        });
                    }
                })

                this.tabulatorInstance.on("columnResized", (column) => {
                    const field = column.getField();
                    const width = column.getWidth();
                    this.tableColumnWidths[field] = width;
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
                this.tabulatorInstance.replaceData(this.rowData);
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

        refreshTable() {
            if (this.tabulatorInstance) {
                this.tabulatorInstance.redraw();
            }
        },

        getTable() {
            return this.tabulatorInstance;
        },
    }
};
</script>

<style>
.lite-tabulator-table .tabulator {
    height: 100%;
    font-size: 12px;
    border: 1px solid #d0d0d0;
    border-radius: 4px !important;
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

.lite-tabulator-table .tabulator-cell.user-entry-column {
    background-color: #ffebee;
    color: #c62828;
}

.lite-tabulator-table .tabulator-cell.facility-entry-column {
    background-color: #c4ecc2;
    color: #388e3c;
}

.lite-tabulator-table .tabulator-cell.facility-entry-column.disable-editing {
    background-color: #b6dbb4;
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
}

.lite-tabulator-table .tabulator-row:not(.tabulator-group):hover {
    mix-blend-mode: multiply;
}

.lite-tabulator-table .tabulator-row.tabulator-group {
    margin-top: 3px;
    display: flex;
    align-items: center;
    justify-content: flex-start;
    background-color: white;
    border-top: 1px solid #d0d0d0 !important;
    border-bottom: 1px solid #d0d0d0 !important;
    z-index: 20;
}

.lite-tabulator-table .tabulator-row.tabulator-group:hover {
    background-color: white;
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

.lite-tabulator-table .no-group-by .tabulator-row-odd:nth-child(1) .tabulator-cell {
    border-top: 1px solid #d0d0d0 !important;
}

.lite-tabulator-table .checkbox-column:not(.tabulator-col) {
    padding: 10px 0px !important;
}

.lite-tabulator-table .title-field-group>.tabulator-col-content>div>div {
    font-weight: 600 !important;
    color: rgb(99, 99, 99) !important;
}
</style>

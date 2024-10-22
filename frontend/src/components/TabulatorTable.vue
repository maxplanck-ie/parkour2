<template>
    <div ref="table"></div>
</template>

<script>
import { TabulatorFull as Tabulator } from "tabulator-tables";
import "tabulator-tables/dist/css/tabulator.min.css";
import { ref, onMounted, watch } from "vue";

export default {
    name: "TabulatorTable",
    props: {
        rowData: {
            type: Array,
            required: true,
        },
        columnDefs: {
            type: Array,
            required: true,
        },
    },
    setup(props) {
        const table = ref(null);

        watch(
            [() => props.rowData, () => props.columnDefs],
            ([newData, newColumns]) => {
                if (table.value) {
                    table.value.setColumns(newColumns);
                    table.value.setData(newData);
                }
            }
        );

        onMounted(() => {
            table.value = new Tabulator(table.value, {
                data: props.rowData,
                columns: props.columnDefs,
                layout: "fitColumns",
                reactiveData: true,
                pagination: "local",
                paginationSize: 10,
                paginationSizeSelector: [10, 25, 50, 100],
                initialSort: [{ column: "name", dir: "asc" }],
                headerFilterPlaceholder: "Search...",
                columns: props.columnDefs.map((col) => ({
                    ...col,
                    headerFilter: col.field === "name" ? "input" : col.headerFilter || false,
                    headerFilterPlaceholder: "Filter...",
                })),
                clipboard: true,
                clipboardPasteAction: "replace",
                selectableRange: 1,
                selectableRangeColumns: true,
                selectableRangeRows: true,
                selectableRangeClearCells: true,
                editTriggerEvent: "dblclick",
                clipboard: true,
                clipboardCopyStyled: false,
                clipboardCopyConfig: {
                    rowHeaders: false,
                    columnHeaders: false,
                },
                clipboardCopyRowRange: "range",
                clipboardPasteParser: "range",
                clipboardPasteAction: "range",
                columnDefaults: {
                    headerSort: false,
                    headerHozAlign: "center",
                    editor: "input",
                    resizable: "header",
                    width: 100,
                },
                rowHeader: { resizable: false, frozen: true, width: 40, hozAlign: "center", formatter: "rownum", cssClass: "range-header-col", editor: false },
                rowSelected: function (row) {
                    console.log("Row selected:", row.getData());
                },

                rowDeselected: function (row) {
                    console.log("Row deselected:", row.getData());
                },
                tooltips: true,
                resizableColumns: true,
                movableColumns: true,
            });
            table.value.on("clipboardCopied", function () {
                console.log("Data has been copied to the clipboard.");
            });
            table.value.on("rowMoved", function (row) {
                console.log("Row: " + row.getData().name + " has been moved");
            });
        });

        return {
            table,
        };
    },
};
</script>

<style></style>
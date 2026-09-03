import {
  applyContextMenuToColumns,
  cellContextMenu,
  ellipsisContainer,
  showNotification
} from "../utilities/utilityFunctions";
import iconSelectAll from "../assets/icons/action_select_all.svg";
import iconDeselectAll from "../assets/icons/action_deselect_all.svg";
import iconQualityPassed from "../assets/icons/status_quality_passed.svg";
import iconQualityFailed from "../assets/icons/status_quality_failed.svg";
import { numericFilterConfig } from "../utilities/numericHeaderFilter";

export function libraryPreparationGroupHeader(value, count) {
  return `
  <div style="display: flex; justify-content: space-between; align-items: center;">
<div style="display: flex; justify-content: space-between; align-items: center;">
  <div>
    <span style="font-weight: bold; font-size: 12px; color: #333;">${value}</span>
    <span style="font-weight: normal; font-size: 12px; margin-left: 2px; color: black;">
      (# of Libraries: ${count})
    </span>
  </div>
</div>
    <div class="group-action-buttons-container" style="position: sticky; gap: 5px;">
      <div title="Select All" class="group-action-button" onclick="handleGroupButtonClick(event, '${value}', 'selectAll')">
        <img src="${iconSelectAll}" alt="Select All" width="24" height="24" />
      </div>
      <div title="Deselect All" class="group-action-button" onclick="handleGroupButtonClick(event, '${value}', 'deselectAll')">
        <img src="${iconDeselectAll}" alt="Deselect All" width="24" height="24" />
      </div>
      <div title="Mark selected as Quality Checked: Passed" class="group-action-button" onclick="handleGroupButtonClick(event, '${value}', 'qualityPassed')">
        <img src="${iconQualityPassed}" alt="Quality Passed" width="24" height="24" />
      </div>
      <div title="Mark selected as Quality Checked: Failed" class="group-action-button" onclick="handleGroupButtonClick(event, '${value}', 'qualityFailed')">
        <img src="${iconQualityFailed}" alt="Quality Failed" width="24" height="24" />
      </div>
    </div>
  </div>
`;
}

export function libraryPreparationColumnDefs(getTabulatorInstance) {
  const columns = [
    {
      field: "selected",
      visible: true,
      headerVertical: false,
      frozen: true,
      resizable: false,
      formatter: (cell) => {
        const row = cell.getRow();
        const rowData = row.getData();
        const checkbox = `<input type="checkbox" title="Select" style="top:-4px" ${
          rowData.selected ? "checked" : ""
        } />`;

        return checkbox;
      },
      hozAlign: "center",
      width: 30,
      minWidth: 30,
      cssClass: "checkbox-column right-border",
      clipboardCopyValue: () => "",
      contextMenu: () =>
        cellContextMenu(false, false, false, getTabulatorInstance, {
          blockActionsOnDisabledCells: true
        }),
      cellClick: function (e, cell) {
        const clickedRow = cell.getRow();
        const rowData = clickedRow.getData();
        const checkbox = e.target;
        rowData.selected = checkbox.checked;
      }
    },
    {
      title: "Request",
      field: "request_name",
      minWidth: 140,
      headerFilter: true,
      headerFilterPlaceholder: "Filter...",
      headerTooltip: "Request",
      visible: true,
      frozen: true,
      cssClass: "right-border",
      contextMenu: () =>
        cellContextMenu(true, false, false, getTabulatorInstance, {
          blockActionsOnDisabledCells: true
        }),
      cellDblClick: function (e, cell) {
        showNotification("This field is not editable.", "warning");
      },
      formatter: (cell) => {
        const value = cell.getValue();
        const finalString = value || "-";
        return ellipsisContainer(finalString, false);
      }
    },
    {
      title: "Barcode",
      field: "barcode",
      width: 95,
      minWidth: 95,
      headerFilter: true,
      headerFilterPlaceholder: "Filter...",
      headerTooltip: "Barcode",
      visible: true,
      frozen: true,
      cssClass: "right-border",
      contextMenu: () =>
        cellContextMenu(true, false, false, getTabulatorInstance, {
          blockActionsOnDisabledCells: true
        }),
      cellDblClick: function (e, cell) {
        showNotification("This field is not editable.", "warning");
      },
      formatter: (cell) => {
        const value = cell.getValue();
        const finalString = value + "*" || "-";
        return ellipsisContainer(finalString);
      }
    },
    {
      title: "Name",
      field: "name",
      width: 110,
      minWidth: 60,
      headerFilter: true,
      headerFilterPlaceholder: "Filter...",
      headerTooltip: "Sample Name",
      visible: true,
      contextMenu: () =>
        cellContextMenu(true, false, false, getTabulatorInstance, {
          blockActionsOnDisabledCells: true
        }),
      cellDblClick: function (e, cell) {
        showNotification("This field is not editable.", "warning");
      },
      formatter: (cell) => {
        const value = cell.getValue();
        const finalString = value || "-";
        return ellipsisContainer(finalString, false);
      }
    },
    {
      title: "Date",
      field: "create_time",
      width: 90,
      minWidth: 60,
      headerFilter: true,
      headerFilterPlaceholder: "Filter...",
      headerTooltip: "Date (Since)",
      visible: true,
      cssClass: "regular-column",
      contextMenu: () =>
        cellContextMenu(true, false, false, getTabulatorInstance, {
          blockActionsOnDisabledCells: true
        }),
      cellDblClick: function (e, cell) {
        showNotification("This field is not editable.", "warning");
      },
      formatter: (cell) => {
        const value = cell.getValue();
        const finalString = value || "-";
        return ellipsisContainer(finalString);
      }
    },
    {
      title: "Protocol",
      field: "library_protocol_name",
      width: 110,
      minWidth: 60,
      visible: true,
      cssClass: "regular-column",
      headerFilter: true,
      headerFilterPlaceholder: "Filter...",
      headerTooltip: "Library Preparation Protocol",
      contextMenu: () =>
        cellContextMenu(true, false, false, getTabulatorInstance, {
          blockActionsOnDisabledCells: true
        }),
      cellDblClick: function (e, cell) {
        showNotification("This field is not editable.", "warning");
      },
      formatter: (cell) => {
        const value = cell.getValue();
        const finalString = value || "No Protocol";
        return ellipsisContainer(finalString);
      }
    },
    {
      title: "Comment Library/Input",
      field: "comments_library_sample",
      width: 140,
      minWidth: 60,
      headerVertical: false,
      headerFilter: true,
      headerFilterPlaceholder: "Filter...",
      headerTooltip: "Comment (User)",
      visible: true,
      cssClass: "regular-column",
      contextMenu: () =>
        cellContextMenu(true, false, false, getTabulatorInstance, {
          blockActionsOnDisabledCells: true
        }),
      formatter: (cell) => {
        const finalString = cell.getValue() || "-";
        return ellipsisContainer(finalString);
      },
      cellDblClick: function (e, cell) {
        showNotification("This field is not editable.", "warning");
      }
    },
    {
      title: "Pool",
      field: "pool_name",
      width: 84,
      minWidth: 60,
      headerVertical: false,
      headerFilter: true,
      headerFilterPlaceholder: "Filter...",
      headerTooltip: "Pool ID",
      visible: true,
      cssClass: "regular-column",
      contextMenu: () =>
        cellContextMenu(true, false, false, getTabulatorInstance, {
          blockActionsOnDisabledCells: true
        }),
      formatter: (cell) => {
        const finalString = cell.getValue() || "-";
        return ellipsisContainer(finalString);
      },
      cellDblClick: function (e, cell) {
        showNotification("This field is not editable.", "warning");
      }
    },
    {
      title: "Index Type",
      field: "index_type",
      width: 96,
      minWidth: 60,
      headerVertical: false,
      headerFilter: true,
      headerFilterPlaceholder: "Filter...",
      headerTooltip: "Index Type",
      visible: true,
      cssClass: "regular-column",
      contextMenu: () =>
        cellContextMenu(true, false, false, getTabulatorInstance, {
          blockActionsOnDisabledCells: true
        }),
      formatter: (cell) => {
        const finalString = cell.getValue() || "-";
        return ellipsisContainer(finalString);
      },
      cellDblClick: function (e, cell) {
        showNotification("This field is not editable.", "warning");
      }
    },
    {
      title: "I7 ID",
      field: "index_i7_id",
      width: 105,
      minWidth: 60,
      headerVertical: false,
      headerFilter: true,
      headerFilterPlaceholder: "Filter...",
      headerTooltip: "Index I7 ID",
      visible: true,
      cssClass: "regular-column",
      contextMenu: () =>
        cellContextMenu(true, false, false, getTabulatorInstance, {
          blockActionsOnDisabledCells: true
        }),
      formatter: (cell) => {
        const finalString = cell.getValue() || "-";
        return ellipsisContainer(finalString);
      },
      cellDblClick: function (e, cell) {
        showNotification("This field is not editable.", "warning");
      }
    },
    {
      title: "I5 ID",
      field: "index_i5_id",
      width: 105,
      minWidth: 60,
      headerVertical: false,
      headerFilter: true,
      headerFilterPlaceholder: "Filter...",
      headerTooltip: "Index I5 ID",
      visible: true,
      cssClass: "regular-column",
      contextMenu: () =>
        cellContextMenu(true, false, false, getTabulatorInstance, {
          blockActionsOnDisabledCells: true
        }),
      formatter: (cell) => {
        const finalString = cell.getValue() || "-";
        return ellipsisContainer(finalString);
      },
      cellDblClick: function (e, cell) {
        showNotification("This field is not editable.", "warning");
      }
    },
    {
      title: "Coordinate",
      field: "coordinate",
      width: 40,
      headerVertical: false,
      headerFilter: true,
      headerFilterPlaceholder: "Filter...",
      headerTooltip: "Index Pair Coordinate",
      visible: true,
      cssClass: "regular-column",
      contextMenu: () =>
        cellContextMenu(true, false, false, getTabulatorInstance, {
          blockActionsOnDisabledCells: true
        }),
      formatter: (cell) => {
        const finalString = cell.getValue() || "-";
        return ellipsisContainer(finalString);
      },
      cellDblClick: function (e, cell) {
        showNotification("This field is not editable.", "warning");
      }
    },
    {
      title: "Value",
      field: "measured_value_facility",
      minWidth: 60,
      width: "4%",
      editor: "number",
      headerVertical: false,
      ...numericFilterConfig((v) => Number(v)),
      visible: true,
      cssClass: "regular-column",
      editorParams: {
        min: 0,
        step: 0.1
      },
      validator: ["min:0"],
      contextMenu: () =>
        cellContextMenu(true, true, true, getTabulatorInstance, {
          blockActionsOnDisabledCells: true
        }),
      formatter: (cell) => {
        const rawValue = cell.getValue();
        const value = Number(rawValue);
        const finalString =
          rawValue === "" ||
          rawValue === undefined ||
          isNaN(value) ||
          value === -1
            ? "-"
            : value.toFixed(2);
        return ellipsisContainer(finalString);
      }
    },
    {
      title: "Unit",
      field: "measuring_unit_facility",
      minWidth: 80,
      width: "6%",
      editor: "list",
      editorParams: (cell) => {
        const row = cell.getRow().getData();
        const options = [
          { label: "ng/µl (Concentration)", value: "ng/µl" },
          { label: "Cells", value: "Cells" },
          { label: "k (Cells)", value: "k" },
          { label: "M (Cells)", value: "M" },
          { label: "Unknown", value: "Unknown" }
        ];
        return {
          values: options,
          autocomplete: true,
          listOnEmpty: true,
          freetext: false
        };
      },
      headerVertical: false,
      headerFilter: true,
      headerFilterPlaceholder: "Filter...",
      headerTooltip: "Measurement Unit",
      visible: true,
      cssClass: "regular-column",
      contextMenu: () =>
        cellContextMenu(true, true, true, getTabulatorInstance, {
          blockActionsOnDisabledCells: true
        }),
      formatter: (cell) => {
        const value = cell.getValue();
        const options = {
          "ng/µl": "ng/µl (Concentration)",
          Cells: "Cells",
          k: "k (Cells)",
          M: "M (Cells)",
          Unknown: "Unknown"
        };
        const finalString = options[value] || value || "Select";
        return ellipsisContainer(finalString);
      }
    },
    {
      title: "bp Sample",
      field: "size_distribution_facility",
      minWidth: 60,
      width: "4%",
      editor: "number",
      headerVertical: false,
      ...numericFilterConfig((v) => Number(v)),
      visible: true,
      cssClass: "regular-column",
      editorParams: {
        min: 0,
        step: 1
      },
      validator: ["min:0"],
      contextMenu: () =>
        cellContextMenu(true, true, true, getTabulatorInstance, {
          blockActionsOnDisabledCells: true
        }),
      formatter: (cell) => {
        const rawValue = cell.getValue();
        const value = Number(rawValue);
        let finalString;

        if (rawValue === "" || rawValue === undefined || isNaN(value)) {
          finalString = "-";
        } else {
          finalString = Math.round(value).toString();
        }

        return ellipsisContainer(finalString);
      }
    },
    {
      title: "Starting Amount",
      field: "starting_amount",
      minWidth: 60,
      width: "4%",
      editor: "number",
      headerVertical: false,
      ...numericFilterConfig((v) => Number(v)),
      visible: true,
      cssClass: "regular-column",
      editorParams: {
        min: 0,
        step: 0.1
      },
      validator: ["min:0"],
      contextMenu: () =>
        cellContextMenu(true, true, true, getTabulatorInstance, {
          blockActionsOnDisabledCells: true
        }),
      formatter: (cell) => {
        const rawValue = cell.getValue();
        const value = Number(rawValue);
        const finalString =
          rawValue === "" || rawValue === undefined || isNaN(value)
            ? "-"
            : value.toFixed(1);
        return ellipsisContainer(finalString);
      }
    },
    {
      title: "Cycles",
      field: "pcr_cycles",
      minWidth: 60,
      width: "4%",
      editor: "number",
      headerVertical: false,
      ...numericFilterConfig((v) => Number(v)),
      visible: true,
      cssClass: "regular-column",
      editorParams: {
        min: 0,
        step: 1
      },
      validator: ["integer", "min:0"],
      contextMenu: () =>
        cellContextMenu(true, true, true, getTabulatorInstance, {
          blockActionsOnDisabledCells: true
        }),
      formatter: (cell) => {
        const rawValue = cell.getValue();
        const value = Number(rawValue);
        let finalString;

        if (rawValue === "" || rawValue === undefined || isNaN(value)) {
          finalString = "-";
        } else {
          finalString = Math.round(value).toString();
        }

        return ellipsisContainer(finalString);
      }
    },
    {
      title: "ng/µl",
      field: "concentration_library",
      minWidth: 60,
      width: "4%",
      editor: "number",
      headerVertical: false,
      ...numericFilterConfig((v) => Number(v)),
      visible: true,
      cssClass: "regular-column",
      editorParams: {
        min: 0,
        step: 0.1
      },
      validator: ["min:0"],
      contextMenu: () =>
        cellContextMenu(true, true, true, getTabulatorInstance, {
          blockActionsOnDisabledCells: true
        }),
      formatter: (cell) => {
        const rawValue = cell.getValue();
        const value = Number(rawValue);
        const finalString =
          rawValue === "" || rawValue === undefined || isNaN(value)
            ? "-"
            : value === 0
              ? "0.0"
              : value.toFixed(2);
        return ellipsisContainer(finalString);
      }
    },
    {
      title: "bp Library",
      field: "mean_fragment_size",
      minWidth: 60,
      width: "4%",
      editor: "number",
      headerVertical: false,
      ...numericFilterConfig((v) => Number(v)),
      visible: true,
      cssClass: "regular-column",
      editorParams: {
        min: 0,
        step: 1
      },
      validator: ["integer", "min:0"],
      contextMenu: () =>
        cellContextMenu(true, true, true, getTabulatorInstance, {
          blockActionsOnDisabledCells: true
        }),
      formatter: (cell) => {
        const rawValue = cell.getValue();
        const value = Number(rawValue);
        let finalString;

        if (rawValue === "" || rawValue === undefined || isNaN(value)) {
          finalString = "-";
        } else {
          finalString = Math.round(value).toString();
        }

        return ellipsisContainer(finalString);
      }
    },
    {
      title: "% Total",
      field: "smear_analysis",
      minWidth: 60,
      width: "4%",
      editor: "number",
      defaultOnEmptyPaste: 100,
      headerVertical: false,
      ...numericFilterConfig((v) => Number(v)),
      visible: true,
      cssClass: "regular-column",
      editorParams: {
        min: 0,
        max: 100,
        step: 0.1
      },
      validator: ["min:0", "max:100"],
      contextMenu: () =>
        cellContextMenu(true, true, true, getTabulatorInstance, {
          blockActionsOnDisabledCells: true
        }),
      formatter: (cell) => {
        const rawValue = cell.getValue();
        const value = Number(rawValue);
        const finalString =
          rawValue === "" || rawValue === undefined || isNaN(value)
            ? "-"
            : value === 0
              ? "0.0"
              : value.toFixed(1);
        return ellipsisContainer(finalString);
      }
    },
    {
      title: "Comment",
      field: "comments_facility",
      width: 140,
      minWidth: 60,
      editor: "input",
      headerVertical: false,
      headerFilter: true,
      headerFilterPlaceholder: "Filter...",
      headerTooltip: "Comment (Facility)",
      visible: true,
      cssClass: "regular-column",
      contextMenu: () =>
        cellContextMenu(true, true, true, getTabulatorInstance, {
          blockActionsOnDisabledCells: true
        }),
      formatter: (cell) => {
        const value = cell.getValue() || "-";
        return ellipsisContainer(value);
      }
    }
  ];

  return applyContextMenuToColumns(columns, getTabulatorInstance, {
    allowCopy: true,
    allowEdit: true,
    allowApplyToAll: true,
    blockActionsOnDisabledCells: true,
    overrideExisting: true,
    skipFields: new Set(["selected"])
  });
}

export function libraryPreparationExportColumns() {
  return [
    { header: "Request", key: "request_name", width: 25 },
    { header: "Barcode", key: "barcode", width: 15 },
    { header: "Name", key: "name", width: 20 },
    { header: "Date", key: "create_time", width: 15 },
    { header: "Protocol", key: "library_protocol_name", width: 20 },
    {
      header: "Comment Library/Sample",
      key: "comments_library_sample",
      width: 25
    },
    { header: "Pool", key: "pool_name", width: 10 },
    { header: "Index Type", key: "index_type", width: 20 },
    { header: "I7 ID", key: "index_i7_id", width: 20 },
    { header: "I5 ID", key: "index_i5_id", width: 20 },
    { header: "Coordinate", key: "coordinate", width: 10 },
    {
      header: "Value",
      key: "measured_value_facility",
      width: 15,
      excelType: "number"
    },
    { header: "Unit", key: "measuring_unit_facility", width: 15 },
    {
      header: "bp Sample",
      key: "size_distribution_facility",
      width: 15,
      excelType: "number"
    }
  ];
}

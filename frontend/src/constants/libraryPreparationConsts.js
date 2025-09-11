import {
  cellContextMenu,
  ellipsisContainer
} from "../utilities/utilityFunctions";

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
        <svg fill="none" width="24px" height="24px" version="1.1" xmlns="http://www.w3.org/2000/svg">
          <g>
            <path opacity="0.5" d="M21 12H12V3H15.024C19.9452 3 21 4.05476 21 8.976V12Z" fill="lightblue"/>
            <path opacity="0.5" d="M3 15.024V12H12V21H8.976C4.05476 21 3 19.9452 3 15.024Z" fill="lightblue"/>
            <path d="M3 8.976C3 4.05476 4.05476 3 8.976 3H15.024C19.9452 3 21 4.05476 21 8.976V15.024C21 19.9452 19.9452 21 15.024 21H8.976C4.05476 21 3 19.9452 3 15.024V8.976Z" stroke="#323232" stroke-width="1.8"/>
            <path d="M12 3V21" stroke="#323232" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M21 12L3 12" stroke="#323232" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
          </g>
        </svg>
      </div>
      <div title="Deselect All" class="group-action-button" onclick="handleGroupButtonClick(event, '${value}', 'deselectAll')">
        <svg fill="none" width="24px" height="24px" version="1.1" xmlns="http://www.w3.org/2000/svg">
          <g>
            <path opacity="0.5" d="M3 12C3 4.5885 4.5885 3 12 3C19.4115 3 21 4.5885 21 12C21 19.4115 19.4115 21 12 21C4.5885 21 3 19.4115 3 12Z" fill="lightblue"/>
            <path d="M3 12C3 4.5885 4.5885 3 12 3C19.4115 3 21 4.5885 21 12C21 19.4115 19.4115 21 12 21C4.5885 21 3 19.4115 3 12Z" stroke="#323232" stroke-width="1.8"/>
          </g>
        </svg>
      </div>
      <div title="Mark selected as Quality Checked: Passed" class="group-action-button" onclick="handleGroupButtonClick(event, '${value}', 'qualityPassed')">
        <svg fill="none" width="24px" height="24px" version="1.1" xmlns="http://www.w3.org/2000/svg">
          <g>
            <path opacity="0.3" d="M3 12C3 4.5885 4.5885 3 12 3C19.4115 3 21 4.5885 21 12C21 19.4115 19.4115 21 12 21C4.5885 21 3 19.4115 3 12Z" fill="green"/>
            <path d="M3 12C3 4.5885 4.5885 3 12 3C19.4115 3 21 4.5885 21 12C21 19.4115 19.4115 21 12 21C4.5885 21 3 19.4115 3 12Z" stroke="#323232" stroke-width="1.8"/>
            <path d="M9 12L10.6828 13.6828V13.6828C10.858 13.858 11.142 13.858 11.3172 13.6828V13.6828L15 10" stroke="#323232" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
          </g>
        </svg>
      </div>
      <div title="Mark selected as Quality Checked: Failed" class="group-action-button" onclick="handleGroupButtonClick(event, '${value}', 'qualityFailed')">
        <svg fill="none" width="24px" height="24px" version="1.1" xmlns="http://www.w3.org/2000/svg">
          <g>
            <path opacity="0.3" d="M3 12C3 4.5885 4.5885 3 12 3C19.4115 3 21 4.5885 21 12C21 19.4115 19.4115 21 12 21C4.5885 21 3 19.4115 3 12Z" fill="red"/>
            <path d="M9 9L15 15" stroke="#323232" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M15 9L9 15" stroke="#323232" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M3 12C3 4.5885 4.5885 3 12 3C19.4115 3 21 4.5885 21 12C21 19.4115 19.4115 21 12 21C4.5885 21 3 19.4115 3 12Z" stroke="#323232" stroke-width="1.8"/>
          </g>
        </svg>
      </div>
    </div>
  </div>
`;
}

export function libraryPreparationColumnDefs(getTabulatorInstance) {
  return [
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
      contextMenu: () =>
        cellContextMenu(false, false, false, getTabulatorInstance),
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
      headerTooltip: "Request",
      visible: true,
      frozen: true,
      cssClass: "right-border",
      contextMenu: () =>
        cellContextMenu(true, false, false, getTabulatorInstance),
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
      headerTooltip: "Barcode",
      visible: true,
      frozen: true,
      cssClass: "right-border",
      contextMenu: () =>
        cellContextMenu(true, false, false, getTabulatorInstance),
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
      title: "Name",
      field: "name",
      width: 110,
      minWidth: 60,
      headerFilter: true,
      headerTooltip: "Sample Name",
      visible: true,
      contextMenu: () =>
        cellContextMenu(true, false, false, getTabulatorInstance),
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
      headerTooltip: "Date",
      visible: true,
      cssClass: "regular-column",
      contextMenu: () =>
        cellContextMenu(true, false, false, getTabulatorInstance),
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
      headerTooltip: "Library Preparation Protocol",
      contextMenu: () =>
        cellContextMenu(true, false, false, getTabulatorInstance),
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
      headerTooltip: "Comment (User)",
      visible: true,
      cssClass: "regular-column",
      contextMenu: () =>
        cellContextMenu(true, false, false, getTabulatorInstance),
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
      headerTooltip: "Pool ID",
      visible: true,
      cssClass: "regular-column",
      contextMenu: () =>
        cellContextMenu(true, false, false, getTabulatorInstance),
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
      headerTooltip: "Index Type",
      visible: true,
      cssClass: "regular-column",
      contextMenu: () =>
        cellContextMenu(true, false, false, getTabulatorInstance),
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
      headerTooltip: "Index I7 ID",
      visible: true,
      cssClass: "regular-column",
      contextMenu: () =>
        cellContextMenu(true, false, false, getTabulatorInstance),
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
      headerTooltip: "Index I5 ID",
      visible: true,
      cssClass: "regular-column",
      contextMenu: () =>
        cellContextMenu(true, false, false, getTabulatorInstance),
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
      headerTooltip: "Index Pair Coordinate",
      visible: true,
      cssClass: "regular-column",
      contextMenu: () =>
        cellContextMenu(true, false, false, getTabulatorInstance),
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
      headerTooltip: "Measured Value",
      visible: true,
      cssClass: "regular-column",
      contextMenu: () =>
        cellContextMenu(true, true, true, getTabulatorInstance),
      formatter: (cell) => {
        const rawValue = cell.getValue();
        const value = Number(rawValue);
        const finalString =
          rawValue === "" ||
          rawValue === undefined ||
          isNaN(value) ||
          value === -1
            ? "-"
            : value === 0
              ? "0.0"
              : value.toFixed(1);
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
          { label: "ng/µl (Concentration)", value: "concentration" },
          { label: "M (Cells)", value: "m" },
          { label: "k (Cells)", value: "k" },
          { label: "Unknown", value: "-" }
        ];
        return { values: options };
      },
      headerVertical: false,
      headerTooltip: "Measurement Unit",
      visible: true,
      cssClass: "regular-column",
      contextMenu: () =>
        cellContextMenu(true, true, true, getTabulatorInstance),
      formatter: (cell) => {
        const value = cell.getValue();
        const options = {
          concentration: "ng/µl (Concentration)",
          m: "M (Cells)",
          k: "k (Cells)",
          "-": "Unknown"
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
      headerTooltip: "Sample Average Fragment Size (bp)",
      visible: true,
      cssClass: "regular-column",
      contextMenu: () =>
        cellContextMenu(true, true, true, getTabulatorInstance),
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
      headerTooltip: "Starting Amount (ng or fmol)",
      visible: true,
      cssClass: "regular-column",
      contextMenu: () =>
        cellContextMenu(true, true, true, getTabulatorInstance),
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
      title: "Cycles",
      field: "pcr_cycles",
      minWidth: 60,
      width: "4%",
      editor: "number",
      headerVertical: false,
      headerTooltip: "PCR Cycles",
      visible: true,
      cssClass: "regular-column",
      editorParams: {
        min: 0,
        step: 1
      },
      validator: ["integer", "min:0"],
      contextMenu: () =>
        cellContextMenu(true, true, true, getTabulatorInstance),
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
      headerTooltip: "Concentration Library (ng/µl)",
      visible: true,
      cssClass: "regular-column",
      contextMenu: () =>
        cellContextMenu(true, true, true, getTabulatorInstance),
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
      title: "bp Library",
      field: "mean_fragment_size",
      minWidth: 60,
      width: "4%",
      editor: "number",
      headerVertical: false,
      headerTooltip: "Library Average Fragment Size (bp)",
      visible: true,
      cssClass: "regular-column",
      editorParams: {
        min: 0,
        step: 1
      },
      validator: ["integer", "min:0"],
      contextMenu: () =>
        cellContextMenu(true, true, true, getTabulatorInstance),
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
      headerVertical: false,
      headerTooltip: "Smear Analysis (% Total)",
      visible: true,
      cssClass: "regular-column",
      editorParams: {
        min: 0,
        max: 100,
        step: 0.1
      },
      validator: ["min:0", "max:100"],
      contextMenu: () =>
        cellContextMenu(true, true, true, getTabulatorInstance),
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
      headerTooltip: "Comment (Facility)",
      visible: true,
      cssClass: "regular-column",
      contextMenu: () =>
        cellContextMenu(true, true, true, getTabulatorInstance),
      formatter: (cell) => {
        const value = cell.getValue() || "-";
        return ellipsisContainer(value);
      }
    }
  ];
}

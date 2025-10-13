import {
  cellContextMenu,
  ellipsisContainer,
} from "../utilities/utilityFunctions";

export function poolingGroupHeader(
  value,
  count,
  headerClass,
  totalDepth,
  pool_size,
  comment
) {
  return `
  <div class="${headerClass}" style="display: flex; justify-content: space-between; align-items: center; padding: 5px;">
<div style="display: flex; justify-content: space-between; align-items: center;">
  <div>
    <span style="font-weight: bold; font-size: 12px; color: #333;">${value}</span>
    <span style="font-weight: normal; font-size: 12px; margin-left: 1px; color: black;">
        | Pool Size: ${totalDepth}M reads (${pool_size}) ${
    comment ? "| Comment: " + comment : ""
  }
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
      <div title="Edit Comment" class="group-action-button" onclick="handleGroupButtonClick(event, '${value}', 'editComment')">
        <svg fill="none" width="24px" height="24px" version="1.1" xmlns="http://www.w3.org/2000/svg">
          <g>
            <path opacity="0.3" d="M21 13V7C21 5.11438 21 4.17157 20.4142 3.58579C19.8284 3 18.8856 3 17 3H7C5.11438 3 4.17157 3 3.58579 3.58579C3 4.17157 3 5.11438 3 7V13C3 14.8856 3 15.8284 3.58579 16.4142C4.17157 17 5.11438 17 7 17H9H9.02322C9.31982 17 9.5955 17.1528 9.75269 17.4043L11.864 20.7824C11.9268 20.8829 12.0732 20.8829 12.136 20.7824L14.2945 17.3288C14.4223 17.1242 14.6465 17 14.8877 17H15H17C18.8856 17 19.8284 17 20.4142 16.4142C21 15.8284 21 14.8856 21 13Z" fill="orange"/>
            <path d="M7 9L17 9" stroke="#323232" stroke-width="1.8" stroke-linecap="round"/>
            <path d="M7 12L13 12" stroke="#323232" stroke-width="1.8" stroke-linecap="round"/>
            <path d="M21 13V7C21 5.11438 21 4.17157 20.4142 3.58579C19.8284 3 18.8856 3 17 3H7C5.11438 3 4.17157 3 3.58579 3.58579C3 4.17157 3 5.11438 3 7V13C3 14.8856 3 15.8284 3.58579 16.4142C4.17157 17 5.11438 17 7 17H9H9.02322C9.31982 17 9.5955 17.1528 9.75269 17.4043L11.864 20.7824C11.9268 20.8829 12.0732 20.8829 12.136 20.7824L14.2945 17.3288C14.4223 17.1242 14.6465 17 14.8877 17H15H17C18.8856 17 19.8284 17 20.4142 16.4142C21 15.8284 21 14.8856 21 13Z" stroke="#323232" stroke-width="1.8" stroke-linejoin="round"/>
          </g>
        </svg>
      </div>
      <div title="Destroy Pool" class="group-action-button" onclick="handleGroupButtonClick(event, '${value}', 'destroyPool')">
        <svg fill="none" width="24px" height="24px" version="1.1" xmlns="http://www.w3.org/2000/svg">
          <g> 
            <path opacity="0.3" d="M9 8H15L14 18H10L9 8Z" fill="#323232"/>
            <path d="M9 10V15" stroke="#323232" stroke-width="1.8" stroke-linecap="round"/>
            <path d="M12 10V15" stroke="#323232" stroke-width="1.8" stroke-linecap="round"/>
            <path d="M15 10V15" stroke="#323232" stroke-width="1.8" stroke-linecap="round"/>
            <path d="M6 8H18" stroke="#323232" stroke-width="1.8" stroke-linecap="round"/>
            <path d="M8 8L9 18H15L16 8" stroke="#323232" stroke-width="1.8" stroke-linejoin="round"/>
            <path d="M3 12C3 4.5885 4.5885 3 12 3C19.4115 3 21 4.5885 21 12C21 19.4115 19.4115 21 12 21C4.5885 21 3 19.4115 3 12Z" stroke="#323232" stroke-width="1.8"/>
          </g>
        </svg>
      </div>
    </div>
  </div>
`;
}

export function poolingColumnDefs(getTabulatorInstance) {
  return [
    {
      field: "selected",
      visible: true,
      headerVertical: false,
      frozen: true,
      resizable: false,
      formatter: (cell) => {
        const rowData = cell.getRow().getData();
        const shouldShowCheckbox = !(
          rowData.record_type === "Sample" &&
          (rowData.status === 2 || rowData.status === -2)
        );
        if (!shouldShowCheckbox) {
          return "";
        }
        const checkbox = `
              <input
                type="checkbox"
                title="Select"
                style="top:-4px"
                ${rowData.selected ? "checked" : ""}
              />
            `;
        return checkbox;
      },
      hozAlign: "center",
      width: 30,
      minWidth: 30,
      cssClass: "checkbox-column right-border",
      contextMenu: () =>
        cellContextMenu(false, false, false, getTabulatorInstance),
      cellClick: function (e, cell) {
        const row = cell.getRow();
        const rowData = row.getData();
        const checkbox = e.target;
        if (checkbox && checkbox.type === "checkbox") {
          rowData.selected = checkbox.checked;
        }
      },
    },
    {
      title: "Request",
      field: "request_name",
      minWidth: 140,
      headerFilter: true,
      headerTooltip: "Request ID",
      visible: true,
      frozen: true,
      cssClass: "right-border",
      contextMenu: () =>
        cellContextMenu(true, false, false, getTabulatorInstance),
      formatter: (cell) => {
        const pool_name = cell.getRow().getData().pool_name;
        const name = cell.getValue();
        const tabulatorInstance = getTabulatorInstance();
        const tableGroupsToggleState =
          tabulatorInstance.getTableGroupsToggleState();
        return `
              <div style="padding: 4px 12px; display: flex; align-items: center;">
                <span title="${name}" style="padding: 8px 0px; overflow: hidden; white-space: nowrap; text-overflow: ellipsis;">${
                  (tableGroupsToggleState == 2 ? pool_name + " ➜ " : "") + name
                }</span>
              </div>`;
      },
    },
    {
      title: "Name",
      field: "name",
      minWidth: 60,
      headerFilter: true,
      headerTooltip: "Library Name",
      visible: true,
      frozen: true,
      cssClass: "right-border",
      contextMenu: () =>
        cellContextMenu(true, false, false, getTabulatorInstance),
      formatter: (cell) => {
        const value = cell.getValue();
        const finalString = value || "-";
        return ellipsisContainer(finalString, false);
      },
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
      formatter: (cell) => {
        const rowData = cell.getRow().getData();
        const value = cell.getValue();
        const barcode = value || "-";
        const barcodeSuffix = value?.[2] ?? "";
        const finalString =
          rowData.record_type === "Sample" && barcodeSuffix === "L"
            ? barcode + "*"
            : barcode;
        return ellipsisContainer(finalString);
      },
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
      formatter: (cell) => {
        const value = cell.getValue();
        const finalString = value || "-";
        return ellipsisContainer(finalString);
      },
    },
    {
      title: "ng/µl",
      field: "concentration_library",
      minWidth: 60,
      width: "6%",
      headerVertical: false,
      headerTooltip: "Concentration Library (ng/µl)",
      visible: true,
      cssClass: "regular-column",
      contextMenu: () =>
        cellContextMenu(true, false, false, getTabulatorInstance),
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
      },
    },
    {
      title: "% Total",
      field: "combined_smear_analysis",
      minWidth: 60,
      width: "6%",
      headerVertical: false,
      headerTooltip: "Smear Analysis (% Total)",
      visible: true,
      cssClass: "regular-column",
      contextMenu: () =>
        cellContextMenu(true, false, false, getTabulatorInstance),
      formatter: (cell) => {
        const rawValue = cell.getValue();
        return ellipsisContainer(rawValue + "%" || "-");
      },
    },
    {
      title: "bp",
      field: "mean_fragment_size",
      minWidth: 60,
      width: "6%",
      headerVertical: false,
      headerTooltip: "Mean Fragment Size (bp)",
      visible: true,
      cssClass: "regular-column",
      contextMenu: () =>
        cellContextMenu(true, false, false, getTabulatorInstance),
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
      },
    },
    {
      title: "Depth (M)",
      field: "sequencing_depth",
      minWidth: 60,
      width: "6%",
      headerVertical: false,
      headerTooltip: "Sequencing Depth (M)",
      visible: true,
      cssClass: "regular-column",
      contextMenu: () =>
        cellContextMenu(true, false, false, getTabulatorInstance),
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
      },
    },
    {
      title: "%",
      field: "percentage_library",
      minWidth: 60,
      width: "6%",
      headerVertical: false,
      headerTooltip: "% Library in Pool",
      visible: true,
      cssClass: "regular-column",
      contextMenu: () =>
        cellContextMenu(true, false, false, getTabulatorInstance),
      formatter: (cell) => {
        const rawValue = cell.getValue();
        return ellipsisContainer(rawValue + "%" || "-");
      },
    },
    {
      title: "Coord",
      field: "coordinate",
      width: 80,
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
    },
    {
      title: "I7 ID",
      field: "index_i7_id",
      minWidth: 60,
      width: "6%",
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
    },
    {
      title: "Index I7",
      field: "index_i7",
      minWidth: 60,
      width: "6%",
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
    },
    {
      title: "I5 ID",
      field: "index_i5_id",
      minWidth: 60,
      width: "6%",
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
    },
    {
      title: "Index I5",
      field: "index_i5",
      minWidth: 60,
      width: "6%",
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
    },
  ];
}

export function poolingExportColumns() {
  return [
    { header: "Pool", key: "pool_name", width: 20 },
    { header: "Request", key: "request_name", width: 25 },
    { header: "Name", key: "name", width: 25 },
    { header: "Barcode", key: "barcode", width: 15 },
    { header: "Date", key: "create_time", width: 15 },
    {
      header: "Concentration Library",
      key: "concentration_library",
      width: 20,
    },
    { header: "% Total", key: "combined_smear_analysis", width: 20 },
    { header: "bp", key: "mean_fragment_size", width: 20 },
    { header: "Depth (M)", key: "sequencing_depth", width: 20 },
    { header: "%", key: "percentage_library", width: 20 },
    { header: "Coord", key: "coordinate", width: 10 },
    { header: "I7 ID", key: "index_i7_id", width: 20 },
    { header: "Index I7", key: "index_i7", width: 20 },
    { header: "I5 ID", key: "index_i5_id", width: 20 },
    { header: "Index I5", key: "index_i5", width: 20 },
  ];
}

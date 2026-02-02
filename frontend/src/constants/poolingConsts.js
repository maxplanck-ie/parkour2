import {
  applyContextMenuToColumns,
  cellContextMenu,
  ellipsisContainer
} from "../utilities/utilityFunctions";
import iconSelectAll from "../assets/icons/action_select_all.svg";
import iconDeselectAll from "../assets/icons/action_deselect_all.svg";
import iconQualityPassed from "../assets/icons/status_quality_passed.svg";
import iconQualityFailed from "../assets/icons/status_quality_failed.svg";
import iconEditComment from "../assets/icons/action_pool_edit_comment.svg";
import iconDestroyPool from "../assets/icons/action_pool_destroy.svg";

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
      <div title="Edit Comment" class="group-action-button" onclick="handleGroupButtonClick(event, '${value}', 'editComment')">
        <img src="${iconEditComment}" alt="Edit Comment" width="24" height="24" />
      </div>
      <div title="Destroy Pool" class="group-action-button" onclick="handleGroupButtonClick(event, '${value}', 'destroyPool')">
        <img src="${iconDestroyPool}" alt="Destroy Pool" width="24" height="24" />
      </div>
    </div>
  </div>
`;
}

export function poolingColumnDefs(getTabulatorInstance) {
  const columns = [
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
      }
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
      }
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
      formatter: (cell) => {
        const value = cell.getValue();
        const finalString = value || "-";
        return ellipsisContainer(finalString);
      }
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
      }
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
      }
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
      }
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
      }
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
      }
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
      }
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
      }
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
      }
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
      }
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
      }
    }
  ];

  return applyContextMenuToColumns(columns, getTabulatorInstance, {
    allowCopy: true,
    allowPaste: false,
    allowApplyToAll: false,
    blockActionsOnDisabledCells: true,
    overrideExisting: true,
    skipFields: new Set(["selected"]),
  });
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
      width: 20
    },
    { header: "% Total", key: "combined_smear_analysis", width: 20 },
    { header: "bp", key: "mean_fragment_size", width: 20 },
    { header: "Depth (M)", key: "sequencing_depth", width: 20 },
    { header: "%", key: "percentage_library", width: 20 },
    { header: "Coord", key: "coordinate", width: 10 },
    { header: "I7 ID", key: "index_i7_id", width: 20 },
    { header: "Index I7", key: "index_i7", width: 20 },
    { header: "I5 ID", key: "index_i5_id", width: 20 },
    { header: "Index I5", key: "index_i5", width: 20 }
  ];
}

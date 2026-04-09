import {
  applyContextMenuToColumns,
  cellContextMenu,
  ellipsisContainer
} from "../utilities/utilityFunctions";
import iconSelectAll from "../assets/icons/action_select_all.svg";
import iconDeselectAll from "../assets/icons/action_deselect_all.svg";
import iconDestroyPool from "../assets/icons/action_pool_destroy.svg";

export function loadFlowcellsGroupHeader(value, rows = []) {
  const formattedDate = rows[0]?.create_time || "";

  return `
    <div style="display: flex; justify-content: space-between; align-items: center;">
      <div style="display: flex; align-items: center; gap: 4px;">
        <div>
          <span style="font-weight: bold; font-size: 12px; color: #333;">${value}</span>
          <span style="font-weight: normal; font-size: 12px; margin-left: 2px; color: black;">
            (${formattedDate})
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
        <div title="Destroy Flowcell" class="group-action-button" onclick="handleGroupButtonClick(event, '${value}', 'destroyFlowcell')">
          <img src="${iconDestroyPool}" alt="Destroy Flowcell" width="24" height="24" />
        </div>
      </div>
    </div>
  `;
}

export function loadFlowcellsColumnDefs(getTabulatorInstance, callbacks = {}) {
  const {
    onToggleSelected = () => {},
    onPoolClick = () => {}
  } = callbacks;

  const columns = [
    {
      field: "selected",
      visible: true,
      headerVertical: false,
      frozen: true,
      resizable: false,
      formatter: (cell) => {
        const rowData = cell.getRow().getData();
        return `<input type="checkbox" title="Select" style="top:-4px" ${
          rowData.selected ? "checked" : ""
        } />`;
      },
      hozAlign: "center",
      width: 30,
      minWidth: 30,
      cssClass: "checkbox-column right-border",
      clipboardCopyValue: () => "",
      contextMenu: () =>
        cellContextMenu(false, false, false, getTabulatorInstance),
      cellClick: function (e, cell) {
        const checkbox = e.target;
        if (checkbox?.type !== "checkbox") return;
        onToggleSelected(cell.getRow().getData(), checkbox.checked);
      }
    },
    {
      title: "Lane",
      field: "name",
      minWidth: 80,
      width: 90,
      headerFilter: true,
      visible: true,
      frozen: true,
      cssClass: "right-border",
      formatter: (cell) => ellipsisContainer(cell.getValue() || "-")
    },
    {
      title: "Pool",
      field: "pool_name",
      minWidth: 105,
      width: 110,
      headerFilter: true,
      visible: true,
      cssClass: "right-border",
      formatter: (cell) => {
        const value = cell.getValue() || "-";
        return `<a href="javascript:void(0)" class="flowcell-pool-link" style="padding: 12px 8px 12px 12px; display: inline-block;">${value}</a>`;
      },
      cellClick: function (e, cell) {
        if (e.target?.classList?.contains("flowcell-pool-link")) {
          onPoolClick(cell.getRow().getData());
        }
      }
    },
    {
      title: "Date",
      field: "create_time",
      width: 95,
      minWidth: 90,
      headerFilter: true,
      visible: true,
      formatter: (cell) => ellipsisContainer(cell.getValue() || "-")
    },
    {
      title: "Request",
      field: "request",
      minWidth: 150,
      headerFilter: true,
      visible: true,
      formatter: (cell) => ellipsisContainer(cell.getValue() || "-")
    },
    {
      title: "Read Length",
      field: "read_length_name",
      minWidth: 100,
      headerFilter: true,
      visible: true,
      formatter: (cell) => ellipsisContainer(cell.getValue() || "-")
    },
    {
      title: "Index I7",
      field: "index_i7_show",
      minWidth: 90,
      headerFilter: true,
      visible: true,
      formatter: (cell) => ellipsisContainer(cell.getValue() || "-")
    },
    {
      title: "Index I5",
      field: "index_i5_show",
      minWidth: 90,
      headerFilter: true,
      visible: true,
      formatter: (cell) => ellipsisContainer(cell.getValue() || "-")
    },
    {
      title: "Sequencer",
      field: "sequencer_name",
      minWidth: 110,
      headerFilter: true,
      visible: true,
      formatter: (cell) => ellipsisContainer(cell.getValue() || "-")
    },
    {
      title: "Library Protocol",
      field: "protocol",
      minWidth: 150,
      headerFilter: true,
      visible: true,
      formatter: (cell) => ellipsisContainer(cell.getValue() || "-")
    },
    {
      title: "Loading Concentration",
      field: "loading_concentration",
      minWidth: 110,
      width: 120,
      visible: true,
      editor: "number",
      editorParams: {
        min: 0,
        step: 0.1,
        verticalNavigation: "table"
      },
      formatter: (cell) => {
        const rawValue = cell.getValue();
        const value = Number(rawValue);
        const finalString =
          rawValue === "" || rawValue === null || rawValue === undefined || isNaN(value)
            ? "-"
            : value.toFixed(1);
        return ellipsisContainer(finalString);
      }
    },
    {
      title: "PhiX %",
      field: "phix",
      minWidth: 90,
      width: 95,
      visible: true,
      editor: "number",
      editorParams: {
        min: 0,
        step: 0.1,
        verticalNavigation: "table"
      },
      formatter: (cell) => {
        const rawValue = cell.getValue();
        const value = Number(rawValue);
        const finalString =
          rawValue === "" || rawValue === null || rawValue === undefined || isNaN(value)
            ? "-"
            : value.toFixed(1);
        return ellipsisContainer(finalString);
      }
    }
  ];

  return applyContextMenuToColumns(columns, getTabulatorInstance, {
    allowCopy: true,
    allowEdit: true,
    allowApplyToAll: true,
    skipFields: new Set(["selected", "pool_name"])
  });
}

export const loadFlowcellsExportColumns = [
  { header: "Flowcell ID", key: "flowcell_id", width: 20 },
  { header: "Lane", key: "name", width: 12 },
  { header: "Pool", key: "pool_name", width: 16 },
  { header: "Date", key: "create_time", width: 14 },
  { header: "Request", key: "request", width: 24 },
  { header: "Read Length", key: "read_length_name", width: 14 },
  { header: "Index I7", key: "index_i7_show", width: 14 },
  { header: "Index I5", key: "index_i5_show", width: 14 },
  { header: "Sequencer", key: "sequencer_name", width: 16 },
  { header: "Library Protocol", key: "protocol", width: 24 },
  { header: "Loading Concentration", key: "loading_concentration", width: 18 },
  { header: "PhiX %", key: "phix", width: 10 }
];

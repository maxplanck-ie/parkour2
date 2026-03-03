import {
  applyContextMenuToColumns,
  cellContextMenu,
  ellipsisContainer
} from "../utilities/utilityFunctions";
import { statusMap, getStatusClass } from "./statusConsts";
import iconEdit from "../assets/icons/action_edit.svg";
import iconDelete from "../assets/icons/action_delete_request.svg";
import iconSolicitApproval from "../assets/icons/action_solicit_approval.svg";
import iconFilePaths from "../assets/icons/action_view_file_paths.svg";
import iconComposeEmail from "../assets/icons/action_compose_email.svg";
import iconSelectAll from "../assets/icons/action_select_all.svg";
import iconDeselectAll from "../assets/icons/action_deselect_all.svg";
import iconAttachmentsAvailable from "../assets/icons/action_attachments_available.svg";
import iconAttachmentsUnavailable from "../assets/icons/action_attachments_unavailable.svg";

const sortedStatusEntries = Object.entries(statusMap).sort(
  ([keyA], [keyB]) => Number(keyA) - Number(keyB)
);

function updateInputDropdownTooltipState(isOpen) {
  document.body.classList.toggle("input-dropdown-open", Boolean(isOpen));
}

function createInputColumnHeader(cellComponent, options = {}) {
  const mode =
    options.inputColumnMode === "mode_facility" ? "mode_facility" : "mode_user";

  const template = document.createElement("div");
  template.innerHTML = `
    <div class="tabulator-input-header" style="display: flex; flex-direction: column; gap: 4px; align-items: stretch; width: 100%;">
      <div class="tabulator-input-header__title" style="font-size: 12px; color: #333;">Input</div>
      <div class="tabulator-header-filter" style="margin-top: -2px;">
        <select class="tabulator-input-header__select" style="height: 24px; font-size: 12px !important; border: 1px solid #d0d0d0 !important; width: 100%; font-size: 12px; font-family: var(--app-font-family, 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif); padding: 2px 4px; border-radius: 4px; background-color: #fff; cursor: pointer; box-sizing: border-box;">
        <option value="mode_user">User</option>
        <option value="mode_facility">Facility</option>
        </select>
      </div>
    </div>
  `;

  const container = template.firstElementChild;
  const select = container.querySelector(".tabulator-input-header__select");
  if (select) {
    select.value = mode;
    select.addEventListener("focus", () =>
      updateInputDropdownTooltipState(true)
    );
    select.addEventListener("blur", () =>
      updateInputDropdownTooltipState(false)
    );
    select.addEventListener("change", (event) => {
      const newMode = event.target.value;
      if (typeof options.onInputColumnModeChange === "function") {
        options.onInputColumnModeChange(newMode);
      }
    });
  }

  return container;
}

function createStatusHeaderTooltip() {
  const rowsHtml = sortedStatusEntries
    .map(
      ([key, label]) => `
      <div style="display: flex; gap: 6px; align-items: center;">
        <span style="font-weight: 600; min-width: 20px; text-align: right;">${key}</span>
        <span>${label}</span>
      </div>`
    )
    .join("");

  const template = document.createElement("div");
  template.innerHTML = `
    <div style="text-align: left; display: flex; flex-direction: column; gap: 4px;">
      <div style="font-weight: 700; margin-bottom: 2px;">Status Codes</div>
      ${rowsHtml}
    </div>
  `;

  return template.firstElementChild;
}

export function librariesAndSamplesGroupHeader(
  value,
  count,
  totalDepth,
  options = {}
) {
  const {
    showStaffActions = false,
    allowDelete = true,
    showApprovalTag = false,
    hasAttachments = false
  } = options;

  const staffActions = showStaffActions
    ? `
      <div title="View File Paths" class="group-action-button" onclick="handleGroupButtonClick(event, '${value}', 'viewFilePaths')">
        <img class="group-action-icon-img" src="${iconFilePaths}" alt="File Paths" />
      </div>
      <div title="Compose Email" class="group-action-button" onclick="handleGroupButtonClick(event, '${value}', 'composeEmail')">
        <img class="group-action-icon-img" src="${iconComposeEmail}" alt="Compose Email" />
      </div>
    `
    : "";

  const deleteAction = allowDelete
    ? `
      <div title="Delete Request" class="group-action-button" onclick="handleGroupButtonClick(event, '${value}', 'deleteRequest')">
        <img class="group-action-icon-img" src="${iconDelete}" alt="Delete Request" />
      </div>
    `
    : "";

  const approvalTag = showApprovalTag
    ? `
      <div title="Solicit Approval via Email" class="group-action-button" onclick="handleGroupButtonClick(event, '${value}', 'requestApproval')">
        <img class="group-action-icon-img" src="${iconSolicitApproval}" alt="Solicit Approval" />
      </div>
    `
    : "";


  return `
  <div style="display: flex; justify-content: space-between; align-items: center; padding: 5px;">
    <div style="display: flex; justify-content: space-between; align-items: center;">
      <div style="display: flex; align-items: center; gap: 8px;">
        <span style="font-weight: bold; font-size: 12px; color: #333;">${value}</span>
        <span style="font-weight: normal; font-size: 12px; margin-left: 2px; color: black;">
          (#: ${count}, Total Depth: ${totalDepth})
        </span>
        ${approvalTag}
        <div title="Attachments" class="group-action-button" onclick="handleGroupButtonClick(event, '${value}', 'attachments')">
          <img class="group-action-icon-img icon-24" src="${hasAttachments ? iconAttachmentsAvailable : iconAttachmentsUnavailable}" alt="Attachments" />
        </div>
      </div>
    </div>
    <div class="group-action-buttons-container" style="position: sticky; gap: 6px; margin-left: 16px; padding: 0 16px;">
      <div title="View / Edit Request" class="group-action-button" onclick="handleGroupButtonClick(event, '${value}', 'viewRequest')">
        <img class="group-action-icon-img" src="${iconEdit}" alt="View / Edit Request" />
      </div>
      ${deleteAction}
      ${staffActions}
      ${showStaffActions ? '<span class="group-action-separator"></span>' : ''}
      <div title="Select All" class="group-action-button" onclick="handleGroupButtonClick(event, '${value}', 'selectAll')">
        <img class="group-action-icon-img icon-24" src="${iconSelectAll}" alt="Select All" />
      </div>
      <div title="Deselect All" class="group-action-button" onclick="handleGroupButtonClick(event, '${value}', 'deselectAll')">
        <img class="group-action-icon-img icon-24" src="${iconDeselectAll}" alt="Deselect All" />
      </div>
    </div>
  </div>
`;
}

export function librariesAndSamplesColumnDefs(
  getTabulatorInstance,
  columnOptions = {}
) {
  const { inputColumnMode = "mode_user", onInputColumnModeChange = () => {} } =
    columnOptions;

  const columns = [
    {
      field: "selected",
      visible: true,
      headerVertical: false,
      frozen: true,
      resizable: false,
      formatter: (cell) => {
        const rowData = cell.getRow().getData();
        const checkbox = `
              <input
                type="checkbox"
                title="Select"
                style="top: -4px;"
                ${rowData.selected ? "checked" : ""}
              />
            `;
        return checkbox;
      },
      hozAlign: "center",
      width: 30,
      minWidth: 30,
      cssClass: "checkbox-column right-border",
      clipboardCopyValue: () => "",
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
      title: "Name",
      field: "name",
      minWidth: 140,
      headerFilter: true,
      headerTooltip: "Name",
      visible: true,
      frozen: true,
      cssClass: "right-border",
      contextMenu: () =>
        cellContextMenu(true, false, false, getTabulatorInstance),
      formatter: (cell) => {
        const request_name = cell.getRow().getData().request_name;
        const name = cell.getValue();
        return `
                        <div style="padding: 4px 12px; display: flex; align-items: center;">
                          <span title="${name}" style="padding: 8px 0px; overflow: hidden; white-space: nowrap; text-overflow: ellipsis;">${name}</span>
                        </div>
                      `;
      }
    },
    {
      title: "Status",
      field: "status",
      width: 50,
      headerFilter: true,
      headerTooltip: () => createStatusHeaderTooltip(),
      visible: true,
      frozen: true,
      cssClass: "right-border",
      contextMenu: () =>
        cellContextMenu(true, false, false, getTabulatorInstance),
      formatter: (cell) => {
        const value = cell.getValue();
        const tooltip = statusMap[value];
        const statusClass = `status ${getStatusClass(value)}`;
        return `<div class="${statusClass}" title="${tooltip}"></div>`;
      }
    },
    {
      title: "S/L",
      field: "type",
      width: 45,
      minWidth: 45,
      headerFilter: true,
      headerTooltip: "Type",
      visible: true,
      frozen: true,
      cssClass: "right-border",
      contextMenu: () =>
        cellContextMenu(true, false, false, getTabulatorInstance),
      formatter: (cell) => {
        const value = cell.getValue();
        const finalString = value || "-";
        return ellipsisContainer(finalString);
      }
    },
    {
      title: "Plate Coord",
      field: "well_position",
      width: 80,
      minWidth: 60,
      headerFilter: true,
      headerTooltip: "Coordinate of Sample in 96-well Plate",
      visible: true,
      frozen: true,
      cssClass: "right-border",
      contextMenu: () =>
        cellContextMenu(true, false, false, getTabulatorInstance),
      formatter: (cell) => {
        const value = cell.getValue();
        const finalString = value || "-";
        return ellipsisContainer(finalString);
      }
    },
    {
      title: "Barcode",
      field: "barcode",
      width: 96,
      minWidth: 96,
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
      title: "Pool Paths",
      field: "pool_names",
      width: 85,
      minWidth: 60,
      headerFilter: true,
      headerTooltip: "Pool Paths",
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
      title: "Propagable & GMO",
      field: "gmo",
      width: 120,
      minWidth: 60,
      headerFilter: true,
      headerTooltip: "Genetically Modified Organism",
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
      title: "Input Type",
      field: "nucleic_acid_type_name",
      minWidth: 80,
      width: "5%",
      headerVertical: false,
      headerFilter: true,
      headerTooltip: "Input Type",
      visible: true,
      cssClass: "regular-column",
      contextMenu: () =>
        cellContextMenu(true, false, false, getTabulatorInstance),
      formatter: (cell) => {
        const value = cell.getValue();
        const finalString = value || "No Input Type";
        return ellipsisContainer(finalString);
      }
    },
    {
      title: "Protocol",
      field: "library_protocol_name",
      minWidth: 80,
      width: "5%",
      visible: true,
      headerFilter: true,
      cssClass: "regular-column",
      headerTooltip: "Library Preparation Protocol",
      contextMenu: () =>
        cellContextMenu(true, false, false, getTabulatorInstance),
      formatter: (cell) => {
        const value = cell.getValue();
        const finalString = value || "No Protocol";
        return ellipsisContainer(finalString);
      }
    },
    {
      title: "Analysis Type",
      field: "analysis_type_name",
      minWidth: 80,
      width: "5%",
      visible: true,
      headerFilter: true,
      cssClass: "regular-column",
      headerTooltip: "Analysis Type",
      contextMenu: () =>
        cellContextMenu(true, false, false, getTabulatorInstance),
      formatter: (cell) => {
        const value = cell.getValue();
        const finalString = value || "No Analysis Type";
        return ellipsisContainer(finalString);
      }
    },
    {
      title: "Input",
      field: "input_display",
      minWidth: 85,
      width: "5%",
      headerVertical: false,
      headerTooltip: "Measured Value with Unit",
      titleFormatter: (cell, formatterParams) =>
        createInputColumnHeader(cell, formatterParams),
      titleFormatterParams: {
        inputColumnMode,
        onInputColumnModeChange
      },
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
      title: "Starting Amount",
      field: "starting_amount",
      minWidth: 60,
      width: "3.5%",
      headerVertical: false,
      headerTooltip: "Starting Amount (ng or fmol)",
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
      title: "Cycles",
      field: "pcr_cycles",
      minWidth: 60,
      width: "3.5%",
      headerVertical: false,
      headerTooltip: "PCR Cycles",
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
      title: "ng/µl Library",
      field: "concentration_library",
      minWidth: 60,
      width: "3.5%",
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
      title: "bp",
      field: "average_fragment_size",
      minWidth: 60,
      width: "3.5%",
      headerVertical: false,
      headerTooltip: "Library Average Fragment Size",
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
      title: "Index Type",
      field: "index_type_name",
      minWidth: 60,
      width: "4%",
      headerVertical: false,
      headerFilter: true,
      headerTooltip: "Index Type",
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
      title: "Coord",
      field: "coordinate",
      minWidth: 60,
      width: "3.5%",
      headerVertical: false,
      headerFilter: true,
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
      field: "i7_id",
      minWidth: 60,
      width: "3.5%",
      headerVertical: false,
      headerFilter: true,
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
      width: "3.5%",
      headerVertical: false,
      headerFilter: true,
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
      field: "i5_id",
      minWidth: 60,
      width: "3.5%",
      headerVertical: false,
      headerFilter: true,
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
      width: "3.5%",
      headerVertical: false,
      headerFilter: true,
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
      title: "Length",
      field: "read_length_name",
      minWidth: 60,
      width: "3.5%",
      headerVertical: false,
      headerFilter: true,
      headerTooltip: "Read Length",
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
      title: "Depth (M)",
      field: "sequencing_depth",
      minWidth: 60,
      width: "3.5%",
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
      title: "Flowcell IDs",
      field: "flowcell_ids",
      minWidth: 60,
      width: "5.5%",
      headerVertical: false,
      headerFilter: true,
      headerTooltip: "Flowcell IDs",
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
      title: "Sequencers",
      field: "sequencer_names",
      minWidth: 60,
      width: "5.5%",
      headerVertical: false,
      headerFilter: true,
      headerTooltip: "Sequencer",
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
    allowEdit: false,
    allowApplyToAll: false,
    blockActionsOnDisabledCells: true,
    overrideExisting: true,
    skipFields: new Set(["selected"]),
  });
}

export function librariesAndSamplesExportColumns() {
  return [
    { header: "Request Name", key: "request_name", width: 25 },
    { header: "Name", key: "name", width: 25 },
    { header: "Status", key: "status_text", width: 15 },
    { header: "S/L", key: "type", width: 10 },
    { header: "Plate Coord", key: "well_position", width: 10 },
    { header: "Barcode", key: "barcode", width: 15 },
    { header: "Pool Paths", key: "pool_names", width: 20 },
    { header: "Propagable & GMO", key: "gmo", width: 22 },
    { header: "Date", key: "create_time", width: 15 },
    { header: "Input Type", key: "nucleic_acid_type_name", width: 20 },
    { header: "Protocol", key: "library_protocol_name", width: 20 },
    { header: "Analysis Type", key: "analysis_type_name", width: 20 },
    { header: "Input", key: "input_display", width: 15 },
    { header: "Starting Amount", key: "starting_amount", width: 18 },
    { header: "Cycles", key: "pcr_cycles", width: 12 },
    { header: "ng/µl Library", key: "concentration_library", width: 15 },
    { header: "bp", key: "average_fragment_size", width: 12 },
    { header: "Index Type", key: "index_type_name", width: 15 },
    { header: "Coord", key: "coordinate", width: 12 },
    { header: "I7 ID", key: "i7_id", width: 15 },
    { header: "Index I7", key: "index_i7", width: 15 },
    { header: "I5 ID", key: "i5_id", width: 15 },
    { header: "Index I5", key: "index_i5", width: 15 },
    { header: "Length", key: "read_length_name", width: 12 },
    { header: "Depth (M)", key: "sequencing_depth", width: 15 },
    { header: "Flowcell IDs", key: "flowcell_ids", width: 20 },
    { header: "Sequencers", key: "sequencer_names", width: 20 }
  ];
}

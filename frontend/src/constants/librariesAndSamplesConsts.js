import {
  cellContextMenu,
  ellipsisContainer,
} from "../utilities/utilityFunctions";
import { statusMap, getStatusClass } from "./statusConsts";

export function librariesAndSamplesGroupHeader(value, count, totalDepth) {
  return `
  <div style="display: flex; justify-content: space-between; align-items: center; padding: 5px;">
<div style="display: flex; justify-content: space-between; align-items: center;">
  <div>
    <span style="font-weight: bold; font-size: 12px; color: #333;">${value}</span>
    <span style="font-weight: normal; font-size: 12px; margin-left: 2px; color: black;">
      (#: ${count}, Total Depth: ${totalDepth})
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
    </div>
  </div>
`;
}

export function librariesAndSamplesColumnDefs(getTabulatorInstance) {
  return [
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
      },
    },
    {
      title: "Status",
      field: "status",
      width: 50,
      headerFilter: true,
      headerTooltip: "Status",
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
      },
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
      },
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
      },
    },
    {
      title: "GMO",
      field: "gmo",
      width: 85,
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
      },
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
      },
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
      },
    },
    {
      title: "Input",
      field: "input",
      minWidth: 60,
      width: "3.5%",
      headerVertical: false,
      headerTooltip: "Measured Amount with Unit",
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
      },
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
      },
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
      },
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
      },
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
      },
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
      },
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
      },
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
      },
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
      },
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
      },
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
      },
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
      },
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
      },
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
      },
    },
  ];
}

import {
  cellContextMenu,
  ellipsisContainer,
  showNotification,
} from "../utilities/utilityFunctions";

export function incomingLibrariesSamplesGroupHeader(
  value,
  count,
  samplesSubmitted,
  gmo,
  totalDepth,
  readLengthDisplay,
  biosafetyLevel,
) {
  return `
    <div style="display: flex; justify-content: space-between; align-items: center;">
      <div style="display: flex; justify-content: space-between; align-items: center;">
        ${
          samplesSubmitted
            ? `<div title="Samples Submitted" style="display: flex; align-items: center; cursor: pointer;" onclick="handleGroupButtonClick(event, '${value}', 'samplesSubmitted')">
                <svg fill="none" width="24px" height="24px" style="cursor: pointer;" version="1.1" xmlns="http://www.w3.org/2000/svg">
                  <g>
                    <path opacity="0.3" d="M13.8179 4.54512L13.6275 4.27845C12.8298 3.16176 11.1702 3.16176 10.3725 4.27845L10.1821 4.54512C9.76092 5.13471 9.05384 5.45043 8.33373 5.37041L7.48471 5.27608C6.21088 5.13454 5.13454 6.21088 5.27608 7.48471L5.37041 8.33373C5.45043 9.05384 5.13471 9.76092 4.54512 10.1821L4.27845 10.3725C3.16176 11.1702 3.16176 12.8298 4.27845 13.6275L4.54512 13.8179C5.13471 14.2391 5.45043 14.9462 5.37041 15.6663L5.27608 16.5153C5.13454 17.7891 6.21088 18.8655 7.48471 18.7239L8.33373 18.6296C9.05384 18.5496 9.76092 18.8653 10.1821 19.4549L10.3725 19.7215C11.1702 20.8382 12.8298 20.8382 13.6275 19.7215L13.8179 19.4549C14.2391 18.8653 14.9462 18.5496 15.6663 18.6296L16.5153 18.7239C17.7891 18.8655 18.8655 17.7891 18.7239 16.5153L18.6296 15.6663C18.5496 14.9462 18.8653 14.2391 19.4549 13.8179L19.7215 13.6275C20.8382 12.8298 20.8382 11.1702 19.7215 10.3725L19.4549 10.1821C18.8653 9.76092 18.5496 9.05384 18.6296 8.33373L18.7239 7.48471C18.8655 6.21088 17.7891 5.13454 16.5153 5.27608L15.6663 5.37041C14.9462 5.45043 14.2391 5.13471 13.8179 4.54512Z" fill="green"/>
                    <path d="M13.8179 4.54512L13.6275 4.27845C12.8298 3.16176 11.1702 3.16176 10.3725 4.27845L10.1821 4.54512C9.76092 5.13471 9.05384 5.45043 8.33373 5.37041L7.48471 5.27608C6.21088 5.13454 5.13454 6.21088 5.27608 7.48471L5.37041 8.33373C5.45043 9.05384 5.13471 9.76092 4.54512 10.1821L4.27845 10.3725C3.16176 11.1702 3.16176 12.8298 4.27845 13.6275L4.54512 13.8179C5.13471 14.2391 5.45043 14.9462 5.37041 15.6663L5.27608 16.5153C5.13454 17.7891 6.21088 18.8655 7.48471 18.7239L8.33373 18.6296C9.05384 18.5496 9.76092 18.8653 10.1821 19.4549L10.3725 19.7215C11.1702 20.8382 12.8298 20.8382 13.6275 19.7215L13.8179 19.4549C14.2391 18.8653 14.9462 18.5496 15.6663 18.6296L16.5153 18.7239C17.7891 18.8655 18.8655 17.7891 18.7239 16.5153L18.6296 15.6663C18.5496 14.9462 18.8653 14.2391 19.4549 13.8179L19.7215 13.6275C20.8382 12.8298 20.8382 11.1702 19.7215 10.3725L19.4549 10.1821C18.8653 9.76092 18.5496 9.05384 18.6296 8.33373L18.7239 7.48471C18.8655 6.21088 17.7891 5.13454 16.5153 5.27608L15.6663 5.37041C14.9462 5.45043 14.2391 5.13471 13.8179 4.54512Z" stroke="#323232" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M9 12L10.8189 13.8189V13.8189C10.9189 13.9189 11.0811 13.9189 11.1811 13.8189V13.8189L15 10" stroke="#323232" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
                  </g>
                </svg>
              </div>`
            : `<div title="Samples not Submitted" style="display: flex; align-items: center; cursor: pointer;" onclick="handleGroupButtonClick(event, '${value}', 'samplesSubmitted')">
                <svg fill="none" width="24px" height="24px" style="cursor: pointer;" version="1.1" xmlns="http://www.w3.org/2000/svg">
                  <g>
                    <path opacity="0.1" d="M13.8179 4.54512L13.6275 4.27845C12.8298 3.16176 11.1702 3.16176 10.3725 4.27845L10.1821 4.54512C9.76092 5.13471 9.05384 5.45043 8.33373 5.37041L7.48471 5.27608C6.21088 5.13454 5.13454 6.21088 5.27608 7.48471L5.37041 8.33373C5.45043 9.05384 5.13471 9.76092 4.54512 10.1821L4.27845 10.3725C3.16176 11.1702 3.16176 12.8298 4.27845 13.6275L4.54512 13.8179C5.13471 14.2391 5.45043 14.9462 5.37041 15.6663L5.27608 16.5153C5.13454 17.7891 6.21088 18.8655 7.48471 18.7239L8.33373 18.6296C9.05384 18.5496 9.76092 18.8653 10.1821 19.4549L10.3725 19.7215C11.1702 20.8382 12.8298 20.8382 13.6275 19.7215L13.8179 19.4549C14.2391 18.8653 14.9462 18.5496 15.6663 18.6296L16.5153 18.7239C17.7891 18.8655 18.8655 17.7891 18.7239 16.5153L18.6296 15.6663C18.5496 14.9462 18.8653 14.2391 19.4549 13.8179L19.7215 13.6275C20.8382 12.8298 20.8382 11.1702 19.7215 10.3725L19.4549 10.1821C18.8653 9.76092 18.5496 9.05384 18.6296 8.33373L18.7239 7.48471C18.8655 6.21088 17.7891 5.13454 16.5153 5.27608L15.6663 5.37041C14.9462 5.45043 14.2391 5.13471 13.8179 4.54512Z" fill="#323232"/>
                    <path d="M13.8179 4.54512L13.6275 4.27845C12.8298 3.16176 11.1702 3.16176 10.3725 4.27845L10.1821 4.54512C9.76092 5.13471 9.05384 5.45043 8.33373 5.37041L7.48471 5.27608C6.21088 5.13454 5.13454 6.21088 5.27608 7.48471L5.37041 8.33373C5.45043 9.05384 5.13471 9.76092 4.54512 10.1821L4.27845 10.3725C3.16176 11.1702 3.16176 12.8298 4.27845 13.6275L4.54512 13.8179C5.13471 14.2391 5.45043 14.9462 5.37041 15.6663L5.27608 16.5153C5.13454 17.7891 6.21088 18.8655 7.48471 18.7239L8.33373 18.6296C9.05384 18.5496 9.76092 18.8653 10.1821 19.4549L10.3725 19.7215C11.1702 20.8382 12.8298 20.8382 13.6275 19.7215L13.8179 19.4549C14.2391 18.8653 14.9462 18.5496 15.6663 18.6296L16.5153 18.7239C17.7891 18.8655 18.8655 17.7891 18.7239 16.5153L18.6296 15.6663C18.5496 14.9462 18.8653 14.2391 19.4549 13.8179L19.7215 13.6275C20.8382 12.8298 20.8382 11.1702 19.7215 10.3725L19.4549 10.1821C18.8653 9.76092 18.5496 9.05384 18.6296 8.33373L18.7239 7.48471C18.8655 6.21088 17.7891 5.13454 16.5153 5.27608L15.6663 5.37041C14.9462 5.45043 14.2391 5.13471 13.8179 4.54512Z" stroke="#323232" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
                  </g>
                </svg>
              </div>`
        }
    ${
      gmo
        ? `<div title="GMO: Yes" style="display: flex; align-items: center;">
                <svg fill="none" width="24px" height="24px" style="cursor: auto;" version="1.1" xmlns="http://www.w3.org/2000/svg">
                  <g>
                    <path d="M21 12 L18.36 18.36 L12 21 L5.64 18.36 L3 12 L5.64 5.64 L12 3 L18.36 5.64 Z" fill="#FFB6C1" stroke="#323232" stroke-width="1.8" stroke-linejoin="round" transform="rotate(-22.5 12 12)"/>
                    <text x="12" y="13" text-anchor="middle" fill="#333333" font-size="10.5" style="font-family: var(--app-font-family, Arial, sans-serif);" dominant-baseline="middle" stroke="#323232" stroke-width="0.8" paint-order="stroke">G</text>
                  </g>
                </svg>
              </div>`
        : `<div title="GMO: No" style="display: flex; align-items: center;">
                  <svg fill="none" width="24px" height="24px" style="cursor: auto;" version="1.1" xmlns="http://www.w3.org/2000/svg">
                    <g>
                      <path d="M21 12 L18.36 18.36 L12 21 L5.64 18.36 L3 12 L5.64 5.64 L12 3 L18.36 5.64 Z" fill="#B2D8B2" stroke="#323232" stroke-width="1.8" stroke-linejoin="round" transform="rotate(-22.5 12 12)"/>
                      <text x="12" y="13" text-anchor="middle" fill="#333333" font-size="10.5" style="font-family: var(--app-font-family, Arial, sans-serif);" dominant-baseline="middle" stroke="#323232" stroke-width="0.8" paint-order="stroke">G</text>
                    </g>
                  </svg>
              </div>`
    }
  <div>
    <span style="font-weight: bold; font-size: 12px; color: #333;">${value}</span>
    <span style="font-weight: normal; font-size: 12px; margin-left: 2px; color: black;">
      (#: ${count}, Total Depth: ${totalDepth}M, Read Lengths: ${
        readLengthDisplay || "No Read Length"
      }, ${biosafetyLevel})
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
      <div title="Mark selected as Quality Checked: Compromised" class="group-action-button" onclick="handleGroupButtonClick(event, '${value}', 'qualityCompromised')">
        <svg fill="none" width="40px" height="40px" version="1.1" xmlns="http://www.w3.org/2000/svg">
          <g>
            <path opacity="0.3" d="M3 12C3 4.5885 4.5885 3 12 3C19.4115 3 21 4.5885 21 12C21 19.4115 19.4115 21 12 21C4.5885 21 3 19.4115 3 12Z" fill="orange"/>
            <path d="M12 8L12 13" stroke="#323232" stroke-width="1.8" stroke-linecap="round"/>
            <path d="M12 16V15.9888" stroke="#323232" stroke-width="1.8" stroke-linecap="round"/>
            <path d="M3 12C3 4.5885 4.5885 3 12 3C19.4115 3 21 4.5885 21 12C21 19.4115 19.4115 21 12 21C4.5885 21 3 19.4115 3 12Z" stroke="#323232" stroke-width="1.8"/>
          </g>
        </svg>
      </div>
    </div>
  </div>
`;
}

export function incomingLibrariesSamplesColumnDefs(getTabulatorInstance) {
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
        cellContextMenu(false, false, false, getTabulatorInstance, { blockActionsOnDisabledCells: true }),
      cellClick: function (e, cell) {
        const clickedRow = cell.getRow();
        const rowData = clickedRow.getData();
        const checkbox = e.target;
        rowData.selected = checkbox.checked;
      },
    },
    {
      title: "Name",
      field: "name",
      minWidth: 100,
      headerFilter: true,
      headerTooltip: "Sample Name",
      visible: true,
      frozen: true,
      cssClass: "name-column right-border",
      sorter: (a, b, aRow, bRow) => {
        return aRow
          .getData()
          .request_name.localeCompare(bRow.getData().request_name);
      },
      contextMenu: () =>
        cellContextMenu(true, false, false, getTabulatorInstance, { blockActionsOnDisabledCells: true }),
      formatter: (cell) => {
        const type = cell.getRow().getData().type;
        const request_name = cell.getRow().getData().request_name;
        const name = cell.getValue();
        const tabulatorInstance = getTabulatorInstance();
        const tableGroupsToggleState =
          tabulatorInstance.getTableGroupsToggleState();
        return `
                        <div style="padding: 4px 8px; display: flex; align-items: center;">
                          <span title="${type === "S" ? "Sample" : "Library"}" 
                            style="
                              display: inline-block;
                              font-size: 10px;
                              font-weight: bold;
                              padding: 4px;
                              border: 2px solid #333;
                              border-radius: 4px;
                              margin-right: 8px;
                            ">
                            ${type}
                          </span>
                          <span title="${name}" style="padding: 8px 0px; overflow: hidden; white-space: nowrap; text-overflow: ellipsis;">${
                            (tableGroupsToggleState == 2
                              ? request_name + " ➜ "
                              : "") + name
                          }</span>
                        </div>
                      `;
      },
      contextMenu: () =>
        cellContextMenu(true, false, false, getTabulatorInstance, { blockActionsOnDisabledCells: true }),
      cellDblClick: function (e, cell) {
        showNotification("This field is not editable.", "warning");
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
      cssClass: "details-column barcode-column right-border",
      contextMenu: () =>
        cellContextMenu(true, false, false, getTabulatorInstance, { blockActionsOnDisabledCells: true }),
      cellDblClick: function (e, cell) {
        showNotification("This field is not editable.", "warning");
      },
      formatter: (cell) => {
        const value = cell.getValue();
        const finalString = value || "-";
        return ellipsisContainer(finalString, false);
      },
    },
    {
      title: "From Users",
      field: "from_user",
      headerHozAlign: "left",
      visible: true,
      cssClass: "title-field-group",
      columns: [
        {
          title: "Input Type",
          field: "nucleic_acid_type_name",
          minWidth: 80,
          width: "6%",
          headerVertical: false,
          headerTooltip: "Input Type",
          visible: true,
          cssClass: "user-entry-column",
          contextMenu: () =>
            cellContextMenu(true, false, false, getTabulatorInstance, { blockActionsOnDisabledCells: true }),
          formatter: (cell) => {
            const value = cell.getValue();
            const finalString = value || "No Input Type";
            return ellipsisContainer(finalString);
          },
          cellDblClick: function (e, cell) {
            showNotification("This field is not editable.", "warning");
          },
        },
        {
          title: "Protocol",
          field: "library_protocol_name",
          minWidth: 80,
          width: "6%",
          headerVertical: false,
          headerTooltip: "Library Preparation Protocol",
          visible: true,
          cssClass: "user-entry-column",
          contextMenu: () =>
            cellContextMenu(true, false, false, getTabulatorInstance, { blockActionsOnDisabledCells: true }),
          formatter: (cell) => {
            const value = cell.getValue();
            const finalString = value || "No Protocol";
            return ellipsisContainer(finalString);
          },
          cellDblClick: function (e, cell) {
            showNotification("This field is not editable.", "warning");
          },
        },
        {
          title: "Comment Library/Input",
          field: "comments",
          minWidth: 100,
          headerVertical: false,
          headerTooltip: "Comment (User)",
          visible: true,
          cssClass: "user-entry-column",
          contextMenu: () =>
            cellContextMenu(true, false, false, getTabulatorInstance, { blockActionsOnDisabledCells: true }),
          formatter: (cell) => {
            const finalString = cell.getValue() || "-";
            return ellipsisContainer(finalString);
          },
          cellDblClick: function (e, cell) {
            showNotification("This field is not editable.", "warning");
          },
        },
        {
          title: "Input",
          field: "input",
          minWidth: 60,
          width: "4%",
          headerVertical: false,
          headerTooltip: "Input (User)",
          visible: true,
          cssClass: "user-entry-column",
          contextMenu: () =>
            cellContextMenu(true, false, false, getTabulatorInstance, { blockActionsOnDisabledCells: true }),
          cellDblClick: function (e, cell) {
            showNotification("This field is not editable.", "warning");
          },
          formatter: (cell) => {
            const value = cell.getValue();
            const finalString = value || "-";
            return ellipsisContainer(finalString);
          },
        },
        {
          title: "µl",
          field: "volume",
          minWidth: 60,
          width: "4%",
          headerVertical: false,
          headerTooltip: "Volume (User)",
          visible: true,
          cssClass: "user-entry-column",
          contextMenu: () =>
            cellContextMenu(true, false, false, getTabulatorInstance, { blockActionsOnDisabledCells: true }),
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
          cellDblClick: function (e, cell) {
            showNotification("This field is not editable.", "warning");
          },
        },
        {
          title: "bp",
          field: "mean_fragment_size",
          minWidth: 60,
          width: "4%",
          headerVertical: false,
          headerTooltip: "Size Distribution (User)",
          visible: true,
          cssClass: "user-entry-column",
          contextMenu: () =>
            cellContextMenu(true, false, false, getTabulatorInstance, { blockActionsOnDisabledCells: true }),
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
          cellDblClick: function (e, cell) {
            showNotification("This field is not editable.", "warning");
          },
        },
      ],
    },
    {
      title: "From Facility",
      field: "from_facility",
      headerHozAlign: "left",
      visible: true,
      cssClass: "title-field-group",
      columns: [
        {
          title: "Value",
          field: "measured_value_facility",
          minWidth: 60,
          width: "4%",
          editor: "number",
          headerVertical: false,
          headerTooltip: "Measured Value",
          visible: true,
          cssClass: "facility-entry-column",
          editorParams: {
            min: 0,
            step: 0.1,
          },
          validator: ["min:0"],
          contextMenu: () =>
            cellContextMenu(true, true, true, getTabulatorInstance, { blockActionsOnDisabledCells: true }),
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
          },
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
              { label: "M (Cells)", value: "M" },
              { label: "k (Cells)", value: "k" },
              { label: "Unknown", value: "Unknown" },
            ];
            if (row.type === "L") {
              return {
                values: options.filter(
                  (option) => option.value !== "M" && option.value !== "k",
                ),
                autocomplete: true,
                listOnEmpty: true,
                freetext: false,
              };
            }
            return {
              values: options,
              autocomplete: true,
              listOnEmpty: true,
              freetext: false,
            };
          },
          headerVertical: false,
          headerTooltip: "Measurement Unit",
          visible: true,
          cssClass: "facility-entry-column",
          contextMenu: () =>
            cellContextMenu(true, true, true, getTabulatorInstance, { blockActionsOnDisabledCells: true }),
          formatter: (cell) => {
            const value = cell.getValue();
            const options = {
              "ng/µl": "ng/µl (Concentration)",
              M: "M (Cells)",
              k: "k (Cells)",
              Unknown: "Unknown",
            };
            const finalString = options[value] || value || "Select";
            return ellipsisContainer(finalString);
          },
        },
        {
          title: "µl",
          field: "sample_volume_facility",
          minWidth: 60,
          width: "4%",
          editor: "number",
          headerVertical: false,
          headerTooltip: "Volume (Facility)",
          visible: true,
          cssClass: "facility-entry-column",
          editorParams: {
            min: 0,
            step: 0.1,
          },
          validator: ["min:0"],
          contextMenu: () =>
            cellContextMenu(true, true, true, getTabulatorInstance, { blockActionsOnDisabledCells: true }),
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
          field: "size_distribution_facility",
          minWidth: 60,
          width: "4%",
          editor: "number",
          headerVertical: false,
          headerTooltip: "Size Distribution (Facility)",
          visible: true,
          cssClass: "facility-entry-column",
          editorParams: {
            min: 0,
            step: 1,
          },
          validator: ["min:0"],
          contextMenu: () =>
            cellContextMenu(true, true, true, getTabulatorInstance, { blockActionsOnDisabledCells: true }),
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
          title: "% Total",
          field: "percent_total",
          minWidth: 60,
          width: "4%",
          editor: "number",
          headerVertical: false,
          headerTooltip: "Smear Analysis (% Total)",
          visible: true,
          cssClass: "facility-entry-column",
          editorParams: {
            min: 0,
            max: 100,
            step: 0.1,
          },
          validator: ["min:0", "max:100"],
          contextMenu: () =>
            cellContextMenu(true, true, true, getTabulatorInstance, { blockActionsOnDisabledCells: true }),
          cellEditing: (cell) => {
            const rowData = cell.getRow().getData();
            if (rowData.type === "S") {
              showNotification(
                "This field is not available for samples.",
                "warning",
              );
            }
            if (rowData.type === "S") {
              cell.getTable().modules.edit.currentCell = null;
            }
          },
          formatter: (cell) => {
            const rowData = cell.getRow().getData();
            const rawValue = cell.getValue();
            const value = Number(rawValue);
            const finalString =
              rawValue === "" || rawValue === undefined || isNaN(value)
                ? "-"
                : value === 0
                  ? "0.0"
                  : value.toFixed(1);
            const cellElement = cell.getElement();
            if (rowData.type === "S") {
              cellElement.classList.add("disable-editing");
            } else {
              cellElement.classList.remove("disable-editing");
            }
            return ellipsisContainer(finalString);
          },
        },
        {
          title: "RQN",
          field: "rna_quality_facility",
          minWidth: 60,
          width: "4%",
          headerVertical: false,
          headerTooltip: "RNA Quality",
          visible: true,
          editor: "number",
          editorParams: {
            min: 0,
            max: 11,
            step: 0.1,
          },
          validator: ["min:0", "max:11"],
          cssClass: "facility-entry-column",
          contextMenu: () =>
            cellContextMenu(true, true, true, getTabulatorInstance, { blockActionsOnDisabledCells: true }),
          cellEditing: (cell) => {
            const rowData = cell.getRow().getData();
            if (rowData.type === "L") {
              showNotification(
                "This field is not available for libraries.",
                "warning",
              );
              cell.getTable().modules.edit.currentCell = null;
            }
          },
          formatter: (cell) => {
            const rawValue = cell.getValue();
            const value = Number(rawValue);
            const finalString =
              rawValue === "" || rawValue === undefined || isNaN(value)
                ? "-"
                : value === 0
                  ? "0.0"
                  : value.toFixed(1);
            const rowData = cell.getRow().getData();
            const cellElement = cell.getElement();
            if (rowData.type === "L") {
              cellElement.classList.add("disable-editing");
            } else {
              cellElement.classList.remove("disable-editing");
            }
            return ellipsisContainer(finalString);
          },
        },
        {
          title: "GMO",
          field: "gmo_facility",
          minWidth: 60,
          width: "6%",
          editor: "list",
          headerTooltip: "GMO Documentation",
          editorParams: {
            values: ["Not Needed", "Risk Assessment Done"].map((v) => ({
              label: v,
              value: v,
            })),
            autocomplete: true,
            listOnEmpty: true,
            freetext: false,
          },
          cssClass: "facility-entry-column",
          contextMenu: () =>
            cellContextMenu(true, true, true, getTabulatorInstance, { blockActionsOnDisabledCells: true }),
          cellEditing: (cell) => {
            const rowData = cell.getRow().getData();
            if (rowData.type === "L") {
              showNotification(
                "This field is not available for libraries.",
                "warning",
              );
            }
            if (rowData.gmo === false || rowData.gmo === "") {
              showNotification(
                "GMO is marked as 'NO' for this sample and cannot be edited.",
                "warning",
              );
            }
            if (
              rowData.type === "L" ||
              rowData.gmo == false ||
              rowData.gmo == ""
            ) {
              cell.getTable().modules.edit.currentCell = null;
            }
          },
          headerFilter: false,
          headerVertical: false,
          visible: true,
          formatter: (cell) => {
            const value = cell.getValue();
            const rowData = cell.getRow().getData();
            const cellElement = cell.getElement();
            const finalString = value || (rowData.gmo === true ? "-" : "No");
            if (
              rowData.type === "L" ||
              rowData.gmo === false ||
              rowData.gmo === ""
            ) {
              cellElement.classList.add("disable-editing");
            } else {
              cellElement.classList.remove("disable-editing");
            }
            return ellipsisContainer(finalString);
          },
        },
        {
          title: "Comment",
          field: "comments_facility",
          minWidth: 100,
          editor: "input",
          headerVertical: false,
          headerTooltip: "Comment (Facility)",
          visible: true,
          cssClass: "facility-entry-column no-right-border",
          contextMenu: () =>
            cellContextMenu(true, true, true, getTabulatorInstance, { blockActionsOnDisabledCells: true }),
          formatter: (cell) => {
            const value = cell.getValue() || "-";
            return ellipsisContainer(value);
          },
        },
      ],
    },
  ];
}

export function incomingLibrariesSamplesExportColumns() {
  return [
    { header: "Request", key: "request_name", width: 22 },
    { header: "Name", key: "name", width: 24 },
    { header: "Barcode", key: "barcode", width: 16 },
    { header: "Input Type", key: "nucleic_acid_type_name", width: 18 },
    { header: "Protocol", key: "library_protocol_name", width: 18 },
    { header: "Comment Library/Input", key: "comments", width: 24 },
    { header: "Input", key: "input", width: 16 },
    { header: "Volume (µl)", key: "volume", width: 12 },
    { header: "bp (User)", key: "mean_fragment_size", width: 12 },
    { header: "Value (Facility)", key: "measured_value_facility", width: 16 },
    { header: "Unit (Facility)", key: "measuring_unit_facility", width: 16 },
    { header: "Volume (Facility)", key: "sample_volume_facility", width: 16 },
    { header: "bp (Facility)", key: "size_distribution_facility", width: 14 },
    { header: "% Total", key: "percent_total", width: 10 },
    { header: "RQN", key: "rna_quality_facility", width: 10 },
    { header: "GMO", key: "gmo_facility", width: 16 },
    { header: "Comment (Facility)", key: "comments_facility", width: 24 },
  ];
}

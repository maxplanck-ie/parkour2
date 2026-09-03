import {
  applyContextMenuToColumns,
  cellContextMenu,
  ellipsisContainer,
  showNotification
} from "../utilities/utilityFunctions";
import iconSamplesSubmitted from "../assets/icons/status_samples_submitted.svg";
import iconSamplesNotSubmitted from "../assets/icons/status_samples_not_submitted.svg";
import iconGmoYes from "../assets/icons/status_gmo_yes.svg";
import iconGmoNo from "../assets/icons/status_gmo_no.svg";
import iconSelectAll from "../assets/icons/action_select_all.svg";
import iconDeselectAll from "../assets/icons/action_deselect_all.svg";
import iconQualityPassed from "../assets/icons/status_quality_passed.svg";
import iconQualityFailed from "../assets/icons/status_quality_failed.svg";
import iconQualityCompromised from "../assets/icons/status_quality_compromised.svg";
import {
  numericFilterConfig,
  numericFilterExamples
} from "../utilities/numericHeaderFilter";
import { textFilterConfig } from "../utilities/textHeaderFilter";

const GMO_TRUE_VALUES = new Set(["y", "yes", "true", "1"]);
const GMO_FALSE_VALUES = new Set(["n", "no", "false", "0"]);
const GMO_FACILITY_FILTER_PLACEHOLDER = "yes / no";
const GMO_FACILITY_FILTER_HELP =
  "Filter by GMO: yes/y/true or no/n/false, or search the text (e.g. Risk Assessment)";

function gmoFacilityHeaderFilter(headerValue, rowValue, rowData) {
  const query = String(headerValue ?? "")
    .trim()
    .toLowerCase();
  if (!query) return true;
  if (GMO_TRUE_VALUES.has(query)) return rowData.gmo === true;
  if (GMO_FALSE_VALUES.has(query)) return rowData.gmo !== true;
  return String(rowValue ?? "")
    .toLowerCase()
    .includes(query);
}

export function incomingLibrariesSamplesGroupHeader(
  value,
  count,
  countLabel,
  samplesSubmitted,
  gmo,
  totalDepth,
  readLengthDisplay,
  biosafetyLevel
) {
  return `
    <div style="display: flex; justify-content: space-between; align-items: center;">
      <div style="display: flex; justify-content: space-between; align-items: center;">
        ${
          samplesSubmitted
            ? `<div title="Samples Submitted" style="display: flex; align-items: center; cursor: pointer;" onclick="handleGroupButtonClick(event, '${value}', 'samplesSubmitted')">
                <img src="${iconSamplesSubmitted}" alt="Samples Submitted" width="24" height="24" style="cursor: pointer;" />
              </div>`
            : `<div title="Samples not Submitted" style="display: flex; align-items: center; cursor: pointer;" onclick="handleGroupButtonClick(event, '${value}', 'samplesSubmitted')">
                <img src="${iconSamplesNotSubmitted}" alt="Samples not Submitted" width="24" height="24" style="cursor: pointer;" />
              </div>`
        }
    ${
      gmo
        ? `<div title="Propagable and GMO: Yes" style="display: flex; align-items: center;">
                <img src="${iconGmoYes}" alt="Propagable and GMO: Yes" width="24" height="24" style="cursor: auto;" />
              </div>`
        : `<div title="Propagable and GMO: No" style="display: flex; align-items: center;">
                <img src="${iconGmoNo}" alt="Propagable and GMO: No" width="24" height="24" style="cursor: auto;" />
              </div>`
    }
  <div>
    <span style="font-weight: bold; font-size: 12px; color: #333;">${value}</span>
    <span style="font-weight: normal; font-size: 12px; margin-left: 2px; color: black;">
      (#: ${count} ${countLabel}, Total Depth: ${totalDepth}M, Read Lengths: ${
        readLengthDisplay || "No Read Length"
      }, Biosafety Level: ${biosafetyLevel})
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
      <div title="Mark selected as Quality Checked: Compromised" class="group-action-button" onclick="handleGroupButtonClick(event, '${value}', 'qualityCompromised')">
        <img src="${iconQualityCompromised}" alt="Quality Compromised" width="24" height="24" />
      </div>
    </div>
  </div>
`;
}

export function incomingLibrariesSamplesColumnDefs(getTabulatorInstance) {
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
      title: "Name",
      field: "name",
      minWidth: 100,
      ...textFilterConfig("Sample Name"),
      visible: true,
      frozen: true,
      cssClass: "name-column right-border",
      sorter: (a, b, aRow, bRow) => {
        return aRow
          .getData()
          .request_name.localeCompare(bRow.getData().request_name);
      },
      contextMenu: () =>
        cellContextMenu(true, false, false, getTabulatorInstance, {
          blockActionsOnDisabledCells: true
        }),
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
        cellContextMenu(true, false, false, getTabulatorInstance, {
          blockActionsOnDisabledCells: true
        }),
      cellDblClick: function (e, cell) {
        showNotification("This field is not editable.", "warning");
      }
    },
    {
      title: "Barcode",
      field: "barcode",
      width: 95,
      minWidth: 95,
      ...textFilterConfig("Barcode"),
      visible: true,
      frozen: true,
      cssClass: "details-column barcode-column right-border",
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
          ...textFilterConfig("Input Type"),
          visible: true,
          cssClass: "user-entry-column",
          contextMenu: () =>
            cellContextMenu(true, false, false, getTabulatorInstance, {
              blockActionsOnDisabledCells: true
            }),
          formatter: (cell) => {
            const value = cell.getValue();
            const finalString = value || "No Input Type";
            return ellipsisContainer(finalString);
          },
          cellDblClick: function (e, cell) {
            showNotification("This field is not editable.", "warning");
          }
        },
        {
          title: "Protocol",
          field: "library_protocol_name",
          minWidth: 80,
          width: "6%",
          headerVertical: false,
          ...textFilterConfig("Library Preparation Protocol"),
          visible: true,
          cssClass: "user-entry-column",
          contextMenu: () =>
            cellContextMenu(true, false, false, getTabulatorInstance, {
              blockActionsOnDisabledCells: true
            }),
          formatter: (cell) => {
            const value = cell.getValue();
            const finalString = value || "No Protocol";
            return ellipsisContainer(finalString);
          },
          cellDblClick: function (e, cell) {
            showNotification("This field is not editable.", "warning");
          }
        },
        {
          title: "Comment Library/Input",
          field: "comments",
          minWidth: 100,
          headerVertical: false,
          ...textFilterConfig("Comment (User)"),
          visible: true,
          cssClass: "user-entry-column",
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
          title: "Input",
          field: "input",
          minWidth: 60,
          width: "4%",
          headerVertical: false,
          ...textFilterConfig("Input (User)"),
          visible: true,
          cssClass: "user-entry-column",
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
          title: "µl",
          field: "volume",
          minWidth: 60,
          width: "4%",
          headerVertical: false,
          ...numericFilterConfig(
            (v) => Number(v),
            numericFilterExamples(30, 10, 10, 50)
          ),
          visible: true,
          cssClass: "user-entry-column",
          contextMenu: () =>
            cellContextMenu(true, false, false, getTabulatorInstance, {
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
          },
          cellDblClick: function (e, cell) {
            showNotification("This field is not editable.", "warning");
          }
        },
        {
          title: "bp",
          field: "mean_fragment_size",
          minWidth: 60,
          width: "4%",
          headerVertical: false,
          ...numericFilterConfig(
            (v) => Number(v),
            numericFilterExamples(400, 200, 150, 500)
          ),
          visible: true,
          cssClass: "user-entry-column",
          contextMenu: () =>
            cellContextMenu(true, false, false, getTabulatorInstance, {
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
          },
          cellDblClick: function (e, cell) {
            showNotification("This field is not editable.", "warning");
          }
        }
      ]
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
          ...numericFilterConfig(
            (v) => Number(v),
            numericFilterExamples(50, 10, 10, 100)
          ),
          visible: true,
          cssClass: "facility-entry-column",
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
            if (row.type === "L") {
              return {
                values: options.filter(
                  (option) =>
                    option.value !== "Cells" &&
                    option.value !== "M" &&
                    option.value !== "k"
                ),
                autocomplete: true,
                listOnEmpty: true,
                freetext: false
              };
            }
            return {
              values: options,
              autocomplete: true,
              listOnEmpty: true,
              freetext: false
            };
          },
          headerVertical: false,
          ...textFilterConfig("Measurement Unit"),
          visible: true,
          cssClass: "facility-entry-column",
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
          title: "µl",
          field: "sample_volume_facility",
          minWidth: 60,
          width: "4%",
          editor: "number",
          headerVertical: false,
          ...numericFilterConfig(
            (v) => Number(v),
            numericFilterExamples(30, 10, 10, 50)
          ),
          visible: true,
          cssClass: "facility-entry-column",
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
                  : value.toFixed(1);
            return ellipsisContainer(finalString);
          }
        },
        {
          title: "bp",
          field: "size_distribution_facility",
          minWidth: 60,
          width: "4%",
          editor: "number",
          headerVertical: false,
          ...numericFilterConfig(
            (v) => Number(v),
            numericFilterExamples(600, 200, 200, 800)
          ),
          visible: true,
          cssClass: "facility-entry-column",
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
          title: "% Total",
          field: "percent_total",
          minWidth: 60,
          width: "4%",
          editor: "number",
          headerVertical: false,
          ...numericFilterConfig(
            (v) => Number(v),
            numericFilterExamples(90, 50, 80, 100)
          ),
          visible: true,
          cssClass: "facility-entry-column",
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
          cellEditing: (cell) => {
            const rowData = cell.getRow().getData();
            if (rowData.type === "S") {
              showNotification(
                "This field is not available for samples.",
                "warning"
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
          }
        },
        {
          title: "RQN",
          field: "rna_quality_facility",
          minWidth: 60,
          width: "4%",
          headerVertical: false,
          ...numericFilterConfig(
            (v) => Number(v),
            numericFilterExamples(8, 5, 5, 9)
          ),
          visible: true,
          editor: "number",
          editorParams: {
            min: 0,
            max: 11,
            step: 0.1
          },
          validator: ["min:0", "max:11"],
          cssClass: "facility-entry-column",
          contextMenu: () =>
            cellContextMenu(true, true, true, getTabulatorInstance, {
              blockActionsOnDisabledCells: true
            }),
          cellEditing: (cell) => {
            const rowData = cell.getRow().getData();
            if (rowData.type === "L") {
              showNotification(
                "This field is not available for libraries.",
                "warning"
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
          }
        },
        {
          title: "Propagable & GMO",
          field: "gmo_facility",
          minWidth: 60,
          width: "7%",
          editor: "list",
          editorParams: {
            values: ["Not Needed", "Risk Assessment Done"].map((v) => ({
              label: v,
              value: v
            })),
            autocomplete: true,
            listOnEmpty: true,
            freetext: false
          },
          cssClass: "facility-entry-column",
          contextMenu: () =>
            cellContextMenu(true, true, true, getTabulatorInstance, {
              blockActionsOnDisabledCells: true
            }),
          cellEditing: (cell) => {
            const rowData = cell.getRow().getData();
            if (rowData.type === "L") {
              showNotification(
                "This field is not available for libraries.",
                "warning"
              );
            }
            if (rowData.gmo === false || rowData.gmo === "") {
              showNotification(
                "GMO is marked as 'NO' for this sample and cannot be edited.",
                "warning"
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
          headerFilter: "input",
          headerFilterPlaceholder: GMO_FACILITY_FILTER_PLACEHOLDER,
          headerFilterFunc: gmoFacilityHeaderFilter,
          headerTooltip: GMO_FACILITY_FILTER_HELP,
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
          }
        },
        {
          title: "Comment",
          field: "comments_facility",
          minWidth: 100,
          editor: "input",
          headerVertical: false,
          ...textFilterConfig("Comment (Facility)"),
          visible: true,
          cssClass: "facility-entry-column no-right-border",
          contextMenu: () =>
            cellContextMenu(true, true, true, getTabulatorInstance, {
              blockActionsOnDisabledCells: true
            }),
          formatter: (cell) => {
            const value = cell.getValue() || "-";
            return ellipsisContainer(value);
          }
        }
      ]
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

export function incomingLibrariesSamplesExportColumns() {
  return [
    { header: "Request", key: "request_name", width: 22 },
    { header: "Name", key: "name", width: 24 },
    { header: "Barcode", key: "barcode", width: 16 },
    { header: "Input Type", key: "nucleic_acid_type_name", width: 18 },
    { header: "Protocol", key: "library_protocol_name", width: 18 },
    { header: "Comment Library/Input", key: "comments", width: 24 },
    { header: "Input", key: "input", width: 16 },
    { header: "Volume (µl)", key: "volume", width: 12, excelType: "number" },
    {
      header: "bp (User)",
      key: "mean_fragment_size",
      width: 12,
      excelType: "number"
    },
    {
      header: "Value (Facility)",
      key: "measured_value_facility",
      width: 16,
      excelType: "number"
    },
    { header: "Unit (Facility)", key: "measuring_unit_facility", width: 16 },
    {
      header: "Volume (Facility)",
      key: "sample_volume_facility",
      width: 16,
      excelType: "number"
    },
    {
      header: "bp (Facility)",
      key: "size_distribution_facility",
      width: 14,
      excelType: "number"
    },
    { header: "% Total", key: "percent_total", width: 10, excelType: "number" },
    {
      header: "RQN",
      key: "rna_quality_facility",
      width: 10,
      excelType: "number"
    },
    { header: "Propagable & GMO", key: "gmo_facility", width: 24 },
    { header: "Comment (Facility)", key: "comments_facility", width: 24 }
  ];
}

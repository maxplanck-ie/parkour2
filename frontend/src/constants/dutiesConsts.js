import { ellipsisContainer } from "../utilities/utilityFunctions";
import { formatDisplayDate } from "../utilities/dateUtils";
import {
  dateFilterConfig,
  textFilterConfig
} from "../utilities/textHeaderFilter";

const DUTY_DATE_MIN = "2015-01-01";
const DUTY_DATE_MAX = "2099-12-31";

function formatDutyDate(value) {
  if (!value) return "-";

  const [year, month, day] = String(value).split("-").map(Number);
  const date = new Date(year, month - 1, day);
  return Number.isNaN(date.getTime()) ? value : formatDisplayDate(date);
}

function dutyDateFormatter(cell) {
  return ellipsisContainer(formatDutyDate(cell.getValue()));
}

// Same shape as the escapeHtml/ellipsisContainer/textFormatter trio in
// invoicingConsts.js, runStatisticsConsts.js and sequencesStatisticsConsts.js:
// Tabulator cells without a formatter render with this table's line-height: 6px
// (see TabulatorTableFull.vue), which clips plain text above the cell -- every
// other Tabulator view avoids that by wrapping cell content in a padded div.
// This one escapes HTML since, unlike the date columns above, "comment" is
// free-typed user text.
function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function dutyTextFormatter(cell) {
  const escapedValue = escapeHtml(cell.getValue() ?? "");
  return `<div title="${escapedValue}" style="padding: 8px 12px; overflow: hidden; white-space: nowrap; text-overflow: ellipsis;">${escapedValue}</div>`;
}

function dutyDateFilter(headerValue, rowValue) {
  return formatDutyDate(rowValue)
    .toLowerCase()
    .includes(
      String(headerValue || "")
        .trim()
        .toLowerCase()
    );
}

// Same shape as runStatisticsRowMatchesSearch / sequencesStatisticsRowMatchesSearch.
export function dutiesRowMatchesSearch(row, query) {
  const normalizedQuery = String(query || "")
    .trim()
    .toLowerCase();
  if (!normalizedQuery) return true;
  return Object.values(row).some((value) =>
    String(value ?? "")
      .toLowerCase()
      .includes(normalizedQuery)
  );
}

function responsiblePersonEditorParams(users) {
  return (cell) => {
    const { facility } = cell.getRow().getData();
    return {
      values: users
        .filter((user) => user.facility === facility)
        .map((user) => user.first_name),
      autocomplete: true,
      listOnEmpty: true,
      freetext: false
    };
  };
}

export function dutiesColumnDefs(users) {
  const personEditorParams = responsiblePersonEditorParams(users);

  return [
    {
      title: "Responsible Person",
      field: "main_name",
      minWidth: 200,
      widthGrow: 3,
      editor: "list",
      editorParams: personEditorParams,
      formatter: dutyTextFormatter,
      ...textFilterConfig()
    },
    {
      title: "Backup Person",
      field: "backup_name",
      minWidth: 150,
      widthGrow: 3,
      editor: "list",
      editorParams: personEditorParams,
      formatter: dutyTextFormatter,
      ...textFilterConfig()
    },
    {
      title: "Start Date",
      field: "start_date",
      minWidth: 120,
      widthGrow: 2,
      editor: "date",
      editorParams: {
        min: DUTY_DATE_MIN,
        max: DUTY_DATE_MAX
      },
      formatter: dutyDateFormatter,
      ...dateFilterConfig(),
      headerFilterFunc: dutyDateFilter
    },
    {
      title: "End Date",
      field: "end_date",
      minWidth: 120,
      widthGrow: 2,
      editor: "date",
      editorParams: {
        min: DUTY_DATE_MIN,
        max: DUTY_DATE_MAX
      },
      formatter: dutyDateFormatter,
      ...dateFilterConfig(),
      headerFilterFunc: dutyDateFilter
    },
    {
      title: "Facility",
      field: "facility",
      minWidth: 150,
      widthGrow: 2,
      formatter: dutyTextFormatter,
      ...textFilterConfig()
    },
    {
      title: "Platform",
      field: "platform",
      minWidth: 150,
      widthGrow: 2,
      editor: "list",
      editorParams: {
        values: ["Short", "Long", "Short + Long"],
        autocomplete: true,
        listOnEmpty: true,
        freetext: false
      },
      formatter: dutyTextFormatter,
      ...textFilterConfig()
    },
    {
      title: "Comments",
      field: "comment",
      minWidth: 300,
      widthGrow: 4,
      editor: "textarea",
      editorParams: {
        elementAttributes: {
          maxlength: 100
        }
      },
      formatter: dutyTextFormatter,
      ...textFilterConfig()
    }
  ];
}

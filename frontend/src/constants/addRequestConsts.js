import {
  cellContextMenu,
  ellipsisContainer,
} from "../utilities/utilityFunctions";

export const LIBRARY_REQUIRED_FIELDS = new Set([
  "name",
  "library_protocol",
  "library_type",
  "read_length",
  "sequencing_depth",
  "organism",
  "index_type",
  "index_reads",
]);

export const SAMPLE_REQUIRED_FIELDS = new Set([
  "name",
  "nucleic_acid_type",
  "library_protocol",
  "library_type",
  "read_length",
  "sequencing_depth",
  "organism",
  "biosafety_level",
]);

const defaultFormatter = (cell) => ellipsisContainer(cell.getValue() || "-");

function createValuesMap(options = []) {
  const map = {};
  options.forEach((option) => {
    const key =
      option?.value ??
      option?.id ??
      option?.pk ??
      option?.name ??
      option?.label;
    const label =
      option?.label ?? option?.name ?? option?.text ?? option?.value ?? "";
    if (key !== undefined && key !== null) {
      map[String(key)] = label;
    }
  });
  return map;
}

function findOptionLabel(options = [], value) {
  if (value === undefined || value === null || value === "") return null;
  const stringValue = String(value);
  const match = options.find((option) => {
    const key =
      option?.value ??
      option?.id ??
      option?.pk ??
      option?.name ??
      option?.label;
    return String(key) === stringValue;
  });
  return match
    ? match.label ?? match.name ?? match.text ?? stringValue
    : stringValue;
}

const numericFormatter = (cell) => ellipsisContainer(cell.getValue() ?? "-");

const createListFormatter =
  (options = []) =>
  (cell) =>
    ellipsisContainer(findOptionLabel(options, cell.getValue()) ?? "-");

function listEditorConfig(options = [], placeholder = "Select") {
  return {
    editor: "list",
    editorParams: {
      values: createValuesMap(options),
      clearable: true,
      emptyValue: "",
      placeholder,
    },
  };
}

function checkboxColumn(getTabulatorInstance, onSelectionChange) {
  return {
    title: "",
    field: "selected",
    width: 45,
    headerVertical: false,
    headerTooltip: "Select row",
    visible: true,
    cssClass: "checkbox-column right-border",
    headerSort: false,
    hozAlign: "center",
    formatter: (cell) => {
      const checked = cell.getValue() ? "checked" : "";
      return `<input type="checkbox" class="table-checkbox" ${checked} />`;
    },
    cellClick: (e, cell) => {
      const checkbox = e?.target?.closest(".table-checkbox");
      if (!checkbox) {
        e?.preventDefault?.();
        e?.stopPropagation?.();
        return;
      }
      const row = cell.getRow();
      const data = cell.getData();
      const nextState = !data.selected;
      data.selected = nextState;
      checkbox.checked = nextState;
      if (nextState) row.select();
      else row.deselect();
      row.update({});
      const table =
        typeof getTabulatorInstance === "function"
          ? getTabulatorInstance()
          : null;
      if (typeof onSelectionChange === "function") {
        onSelectionChange(table);
      }
      e?.stopPropagation?.();
    },
  };
}

export function getAddRequestLibraryColumns(
  getTabulatorInstance,
  editors = {},
  onSelectionChange
) {
  const {
    protocols = [],
    analysisTypes = [],
    measuringUnits = [],
    readLengths = [],
    indexTypes = [],
    organisms = [],
    getIndexReadsOptions,
    getIndexI7Options,
    getIndexI5Options,
  } = editors;

  const libraryUnits =
    measuringUnits.length > 0
      ? measuringUnits
      : [
          { value: "ng/µl", label: "ng/µl (Concentration)" },
          { value: "Unknown", label: "Unknown" },
        ];

  const dynamicOptions = {
    reads:
      typeof getIndexReadsOptions === "function"
        ? getIndexReadsOptions
        : () => [],
    i7: typeof getIndexI7Options === "function" ? getIndexI7Options : () => [],
    i5: typeof getIndexI5Options === "function" ? getIndexI5Options : () => [],
  };

  const getRowData = (cell) => cell?.getRow?.()?.getData?.() || {};
  const dynamicListFormatter = (getOptionsFn) => (cell) => {
    const options = getOptionsFn(getRowData(cell));
    const label = findOptionLabel(options, cell.getValue());
    if (label !== null && label !== undefined) {
      return ellipsisContainer(label);
    }
    const rawValue = cell.getValue();
    return ellipsisContainer(
      rawValue === undefined || rawValue === null || rawValue === ""
        ? "-"
        : rawValue
    );
  };

  const dynamicEditorParams = (getOptionsFn) => (cell) => {
    const options = getOptionsFn(getRowData(cell));
    return {
      values: createValuesMap(options),
      clearable: true,
      emptyValue: "",
      placeholder: "Select",
    };
  };

  const columns = [
    checkboxColumn(getTabulatorInstance, onSelectionChange),
    {
      title: "Name",
      field: "name",
      width: "10%",
      headerVertical: false,
      headerTooltip: "Name",
      visible: true,
      cssClass: "regular-column right-border",
      editor: "input",
      formatter: defaultFormatter,
    },
    {
      title: "Protocol",
      field: "library_protocol",
      width: "10%",
      headerVertical: false,
      headerTooltip: "Protocol for library preparation",
      visible: true,
      cssClass: "regular-column right-border",
      editor: "input",
      ...listEditorConfig(protocols),
      formatter: createListFormatter(protocols),
    },
    {
      title: "Comment Library",
      field: "comments",
      width: "10%",
      headerVertical: false,
      headerTooltip: "Comments",
      visible: true,
      cssClass: "regular-column right-border",
      editor: "input",
      formatter: defaultFormatter,
    },
    {
      title: "Analysis Type",
      field: "library_type",
      width: "8%",
      headerVertical: false,
      headerTooltip: "Analysis Type",
      visible: true,
      cssClass: "regular-column right-border",
      editor: "input",
      ...listEditorConfig(analysisTypes),
      formatter: createListFormatter(analysisTypes),
    },
    {
      title: "Unit",
      field: "measuring_unit",
      width: "6%",
      headerVertical: false,
      headerTooltip: "Measuring Unit",
      visible: true,
      cssClass: "regular-column right-border",
      editor: "input",
      ...listEditorConfig(libraryUnits),
      formatter: createListFormatter(libraryUnits),
    },
    {
      title: "Amount",
      field: "measured_value",
      width: "6%",
      headerVertical: false,
      headerTooltip: "Amount",
      visible: true,
      cssClass: "regular-column right-border",
      editor: "number",
      editorParams: { min: 0, step: 0.01 },
      hozAlign: "right",
      formatter: numericFormatter,
    },
    {
      title: "Size (bp)",
      field: "mean_fragment_size",
      width: "7%",
      headerVertical: false,
      headerTooltip: "Mean fragment size",
      visible: true,
      cssClass: "regular-column right-border",
      editor: "number",
      editorParams: { min: 0, step: 1 },
      hozAlign: "right",
      formatter: numericFormatter,
    },
    {
      title: "Volume (µl)",
      field: "volume",
      width: "7%",
      headerVertical: false,
      headerTooltip: "Volume in microliters",
      visible: true,
      cssClass: "regular-column right-border",
      editor: "number",
      editorParams: { min: 0, step: 0.01 },
      hozAlign: "right",
      formatter: numericFormatter,
    },
    {
      title: "Read Length",
      field: "read_length",
      width: "8%",
      headerVertical: false,
      headerTooltip: "Read Length",
      visible: true,
      cssClass: "regular-column right-border",
      editor: "input",
      ...listEditorConfig(readLengths),
      formatter: createListFormatter(readLengths),
    },
    {
      title: "Depth (M)",
      field: "sequencing_depth",
      width: "6%",
      headerVertical: false,
      headerTooltip: "Sequencing Depth (M)",
      visible: true,
      cssClass: "regular-column right-border",
      editor: "number",
      editorParams: { min: 0, step: 0.1 },
      hozAlign: "right",
      formatter: (cell) => {
        const raw = cell.getValue();
        if (raw === "" || raw === undefined || raw === null) {
          return ellipsisContainer("-");
        }
        const value = Number(raw);
        const display = Number.isNaN(value)
          ? "-"
          : Math.round(value).toString();
        return ellipsisContainer(display);
      },
    },
    {
      title: "Index Type",
      field: "index_type",
      width: "8%",
      headerVertical: false,
      headerTooltip: "Index Type",
      visible: true,
      cssClass: "regular-column right-border",
      editor: "input",
      ...listEditorConfig(indexTypes),
      formatter: createListFormatter(indexTypes),
    },
    {
      title: "# of Index Reads",
      field: "index_reads",
      width: "8%",
      headerVertical: false,
      headerTooltip: "Number of Index Reads",
      visible: true,
      cssClass: "regular-column right-border",
      editor: "list",
      editorParams: dynamicEditorParams(dynamicOptions.reads),
      hozAlign: "left",
      formatter: dynamicListFormatter(dynamicOptions.reads),
    },
    {
      title: "Index I7",
      field: "index_i7",
      width: "8%",
      headerVertical: false,
      headerTooltip: "Index 1 (I7)",
      visible: true,
      cssClass: "regular-column right-border",
      editor: "list",
      editorParams: dynamicEditorParams(dynamicOptions.i7),
      formatter: dynamicListFormatter(dynamicOptions.i7),
    },
    {
      title: "Index I5",
      field: "index_i5",
      width: "8%",
      headerVertical: false,
      headerTooltip: "Index 2 (I5)",
      visible: true,
      cssClass: "regular-column right-border",
      editor: "list",
      editorParams: dynamicEditorParams(dynamicOptions.i5),
      formatter: dynamicListFormatter(dynamicOptions.i5),
    },
    {
      title: "Organism",
      field: "organism",
      width: "10%",
      headerVertical: false,
      headerTooltip: "Organism",
      visible: true,
      cssClass: "regular-column",
      editor: "input",
      ...listEditorConfig(organisms),
      formatter: createListFormatter(organisms),
    },
  ];
  columns.forEach((column) => {
    if (column.field !== "selected") {
      column.contextMenu = () =>
        cellContextMenu(true, false, false, getTabulatorInstance);
    }
  });

  return columns;
}

export function getAddRequestSampleColumns(
  getTabulatorInstance,
  editors = {},
  onSelectionChange
) {
  const {
    nucleicAcidTypes = [],
    measuringUnits = [],
    protocols = [],
    analysisTypes = [],
    readLengths = [],
    organisms = [],
    biosafetyLevels = [],
    gmoOptions = [],
  } = editors;

  const sampleUnits =
    measuringUnits.length > 0
      ? measuringUnits
      : [
          { value: "ng/µl", label: "ng/µl (Concentration)" },
          { value: "M", label: "M (Cells)" },
          { value: "k", label: "k (Cells)" },
          { value: "Unknown", label: "Unknown" },
        ];

  const biosafety =
    biosafetyLevels.length > 0
      ? biosafetyLevels
      : [
          { value: "bsl1", label: "BSL1" },
          { value: "bsl2", label: "BSL2" },
        ];

  const gmo =
    gmoOptions.length > 0
      ? gmoOptions
      : [
          { value: true, label: "Yes" },
          { value: false, label: "No" },
        ];

  const columns = [
    checkboxColumn(getTabulatorInstance, onSelectionChange),
    {
      title: "Name",
      field: "name",
      width: "10%",
      headerVertical: false,
      headerTooltip: "Sample name",
      visible: true,
      cssClass: "regular-column right-border",
      editor: "input",
      formatter: defaultFormatter,
    },
    {
      title: "Input Type",
      field: "nucleic_acid_type",
      width: "10%",
      headerVertical: false,
      headerTooltip: "Input Type",
      visible: true,
      cssClass: "regular-column right-border",
      editor: "input",
      ...listEditorConfig(nucleicAcidTypes),
      formatter: createListFormatter(nucleicAcidTypes),
    },
    {
      title: "Comment Input",
      field: "comments",
      width: "10%",
      headerVertical: false,
      headerTooltip: "Comments",
      visible: true,
      cssClass: "regular-column right-border",
      editor: "input",
      formatter: defaultFormatter,
    },
    {
      title: "Measuring Unit",
      field: "measuring_unit",
      width: "8%",
      headerVertical: false,
      headerTooltip: "Measuring Unit",
      visible: true,
      cssClass: "regular-column right-border",
      editor: "input",
      ...listEditorConfig(sampleUnits),
      formatter: createListFormatter(sampleUnits),
    },
    {
      title: "Measured Value",
      field: "measured_value",
      width: "8%",
      headerVertical: false,
      headerTooltip: "Measured Value",
      visible: true,
      cssClass: "regular-column right-border",
      editor: "number",
      editorParams: { min: 0, step: 0.01 },
      hozAlign: "right",
      formatter: numericFormatter,
    },
    {
      title: "Volume (µl)",
      field: "volume",
      width: "8%",
      headerVertical: false,
      headerTooltip: "Volume in microliters",
      visible: true,
      cssClass: "regular-column right-border",
      editor: "number",
      editorParams: { min: 0, step: 0.01 },
      hozAlign: "right",
      formatter: numericFormatter,
    },
    {
      title: "Protocol",
      field: "library_protocol",
      width: "10%",
      headerVertical: false,
      headerTooltip: "Protocol",
      visible: true,
      cssClass: "regular-column right-border",
      editor: "input",
      ...listEditorConfig(protocols),
      formatter: createListFormatter(protocols),
    },
    {
      title: "Analysis Type",
      field: "library_type",
      width: "8%",
      headerVertical: false,
      headerTooltip: "Analysis Type",
      visible: true,
      cssClass: "regular-column right-border",
      editor: "input",
      ...listEditorConfig(analysisTypes),
      formatter: createListFormatter(analysisTypes),
    },
    {
      title: "Read Length",
      field: "read_length",
      width: "8%",
      headerVertical: false,
      headerTooltip: "Read Length",
      visible: true,
      cssClass: "regular-column right-border",
      editor: "input",
      ...listEditorConfig(readLengths),
      formatter: createListFormatter(readLengths),
    },
    {
      title: "Depth (M)",
      field: "sequencing_depth",
      width: "6%",
      headerVertical: false,
      headerTooltip: "Sequencing Depth (M)",
      visible: true,
      cssClass: "regular-column right-border",
      editor: "number",
      editorParams: { min: 0, step: 0.1 },
      hozAlign: "right",
      formatter: (cell) => {
        const raw = cell.getValue();
        if (raw === "" || raw === undefined || raw === null) {
          return ellipsisContainer("-");
        }
        const value = Number(raw);
        const display = Number.isNaN(value)
          ? "-"
          : Math.round(value).toString();
        return ellipsisContainer(display);
      },
    },
    {
      title: "Organism",
      field: "organism",
      width: "10%",
      headerVertical: false,
      headerTooltip: "Organism",
      visible: true,
      cssClass: "regular-column right-border",
      editor: "input",
      ...listEditorConfig(organisms),
      formatter: createListFormatter(organisms),
    },
    {
      title: "Biosafety Level",
      field: "biosafety_level",
      width: "7%",
      headerVertical: false,
      headerTooltip: "Biosafety Level",
      visible: true,
      cssClass: "regular-column right-border",
      editor: "input",
      ...listEditorConfig(biosafety),
      formatter: createListFormatter(biosafety),
    },
    {
      title: "GMO",
      field: "gmo",
      width: "5%",
      headerVertical: false,
      headerTooltip: "Genetically Modified Organism",
      visible: true,
      cssClass: "regular-column",
      editor: "input",
      ...listEditorConfig(gmo),
      formatter: createListFormatter(gmo),
    },
  ];
  columns.forEach((column) => {
    if (column.field !== "selected") {
      column.contextMenu = () =>
        cellContextMenu(true, false, false, getTabulatorInstance);
    }
  });

  return columns;
}

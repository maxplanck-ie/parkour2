import {
  cellContextMenu,
  ellipsisContainer,
} from "../utilities/utilityFunctions";

export const LIBRARY_REQUIRED_FIELDS = new Set([
  "name",
  "measuring_unit",
  "library_protocol",
  "library_type",
  "read_length",
  "sequencing_depth",
  "organism",
  "volume",
  "mean_fragment_size",
  "index_type",
  "index_reads",
]);

export const SAMPLE_REQUIRED_FIELDS = new Set([
  "name",
  "nucleic_acid_type",
  "measuring_unit",
  "library_protocol",
  "library_type",
  "read_length",
  "sequencing_depth",
  "organism",
  "volume",
  "biosafety_level",
]);

function createValuesMap(options = []) {
  const values = [];
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
      values.push({ label: String(label), value: String(key) });
    }
  });
  return values;
}

const INDEX_SEQUENCE_REGEX = /^[ATCG]{6,}$/;
const INDEX_SEQUENCE_LENGTHS = new Set([6, 8, 10, 12, 24]);
const indexSequenceValidator = (value) => {
  if (value === "" || value === undefined || value === null) return true;
  const text = String(value);
  if (!INDEX_SEQUENCE_REGEX.test(text)) {
    return "Only A, T, C, and G (uppercase) are allowed. Index length must be 6, 8, 10, 12, or 24.";
  }
  if (!INDEX_SEQUENCE_LENGTHS.has(text.length)) {
    return "Only A, T, C, and G (uppercase) are allowed. Index length must be 6, 8, 10, 12, or 24.";
  }
  return true;
};

const EMPTY_PLACEHOLDER = "-";
const SELECT_PLACEHOLDER = "Select";

function formatDisplayValue(value, placeholder = EMPTY_PLACEHOLDER) {
  if (value === undefined || value === null || value === "") {
    return placeholder;
  }
  return value;
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
    ? (match.label ?? match.name ?? match.text ?? stringValue)
    : stringValue;
}

const createListFormatter =
  (options = []) =>
  (cell) =>
    ellipsisContainer(
      formatDisplayValue(
        findOptionLabel(options, cell.getValue()),
        SELECT_PLACEHOLDER,
      ),
    );

function listEditorConfig(options = [], placeholder = "Select") {
  return {
    editor: "list",
    editorParams: {
      values: createValuesMap(options),
      clearable: true,
      emptyValue: "",
      autocomplete: true,
      listOnEmpty: true,
      placeholder,
    },
  };
}

function filterLibraryTypesByProtocol(types = [], protocolId) {
  if (!protocolId) return [];
  const matchId = String(protocolId);
  return types
    .filter((type) => {
      const protocols = Array.isArray(type.library_protocol)
        ? type.library_protocol.map((item) => String(item))
        : [];
      return protocols.includes(matchId);
    })
    .sort((a, b) =>
      String(a.label || "").localeCompare(String(b.label || ""), undefined, {
        sensitivity: "base",
      }),
    );
}

function decorateFormatter(formatter, editableChecker, disabledMessageFn) {
  return function (cell) {
    if (typeof editableChecker === "function") {
      const editable = editableChecker(cell);
      const el = cell.getElement?.();
      if (el) {
        el.classList.toggle("disable-editing", !editable);
        if (!editable && typeof disabledMessageFn === "function") {
          const message = disabledMessageFn(cell);
          if (message) {
            el.setAttribute("data-disabled-tooltip", message);
          } else {
            el.removeAttribute("data-disabled-tooltip");
          }
        } else {
          el.removeAttribute("data-disabled-tooltip");
        }
      }
    }
    return formatter ? formatter(cell) : cell.getValue();
  };
}

function checkboxColumn(getTabulatorInstance, onSelectionChange) {
  return {
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
    contextMenu: () =>
      cellContextMenu(false, false, false, getTabulatorInstance),
    cellClick: function (e, cell) {
      const row = cell.getRow();
      const rowData = row.getData();
      const checkbox = e.target;
      if (checkbox && checkbox.type === "checkbox") {
        rowData.selected = checkbox.checked;
        if (typeof onSelectionChange === "function") {
          onSelectionChange(getTabulatorInstance?.() || null);
        }
      }
    },
  };
}

export function getAddRequestLibraryColumns(
  getTabulatorInstance,
  editors = {},
  onSelectionChange,
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
    return ellipsisContainer(formatDisplayValue(rawValue, SELECT_PLACEHOLDER));
  };

  const dynamicEditorParams = (getOptionsFn) => (cell) => {
    const options = getOptionsFn(getRowData(cell));
    return {
      values: createValuesMap(options),
      clearable: true,
      emptyValue: "",
      autocomplete: true,
      listOnEmpty: true,
      placeholder: "Select",
    };
  };

  const getLibraryTypeOptions = (rowData) =>
    filterLibraryTypesByProtocol(analysisTypes, rowData.library_protocol);

  const isLibraryEditable = (field, rowData) => {
    if (field === "library_type") {
      return Boolean(rowData.library_protocol);
    }
    if (field === "index_reads") {
      return Boolean(rowData.index_type);
    }
    if (field === "index_i7") {
      return Number(rowData.index_reads) >= 1;
    }
    if (field === "index_i5") {
      return Number(rowData.index_reads) >= 2;
    }
    if (field === "measured_value") {
      return (
        Boolean(rowData.measuring_unit) && rowData.measuring_unit !== "Unknown"
      );
    }
    return true;
  };

  const libraryEditable = (field) => (cell) =>
    isLibraryEditable(field, getRowData(cell));
  const libraryDisabledMessage = (field) => (cell) => {
    const rowData = getRowData(cell);
    if (field === "library_type" && !rowData.library_protocol) {
      return "Select a Protocol first.";
    }
    if (field === "index_reads" && !rowData.index_type) {
      return "Select an Index Type first.";
    }
    if (field === "index_i7") {
      if (!rowData.index_type) {
        return "Select an Index Type first.";
      }
      const rawReads = rowData.index_reads;
      if (rawReads === "" || rawReads === null || rawReads === undefined) {
        return "Select # of Index Reads first.";
      }
      let reads = Number(rawReads);
      if (!Number.isFinite(reads)) reads = 0;
      if (reads < 1) {
        if (reads === 0) {
          return "Index Reads is 0. Increase to 1 to enable Index I7.";
        }
        return "Select # of Index Reads first.";
      }
    }
    if (field === "index_i5") {
      if (!rowData.index_type) {
        return "Select an Index Type first.";
      }
      const rawReads = rowData.index_reads;
      if (rawReads === "" || rawReads === null || rawReads === undefined) {
        return "Select # of Index Reads (2) first.";
      }
      let reads = Number(rawReads);
      if (!Number.isFinite(reads)) reads = 0;
      if (reads < 2) {
        if (reads === 0) {
          return "Index Reads is 0. Increase to 2 to enable Index I5.";
        }
        return "Select # of Index Reads (2) first.";
      }
    }
    if (field === "measured_value") {
      if (!rowData.measuring_unit) {
        return "Select a Measuring Unit first.";
      }
      if (rowData.measuring_unit === "Unknown") {
        return "Measured Value is disabled when unit is Unknown.";
      }
    }
    return "";
  };

  const columns = [
    checkboxColumn(getTabulatorInstance, onSelectionChange),
    {
      title: "Name",
      field: "name",
      width: "10%",
      headerVertical: false,
      headerTooltip: "Enter a Unique Name",
      frozen: true,
      visible: true,
      cssClass: "regular-column right-border",
      editor: "input",
      validator: (value) =>
        value === "" || value === undefined || value === null
          ? true
          : /^[A-Za-z0-9_-]+$/.test(String(value))
            ? true
            : "Only letters, numbers, _ and - are allowed.",
      formatter: decorateFormatter(
        (cell) => ellipsisContainer(formatDisplayValue(cell.getValue())),
        libraryEditable("name"),
        libraryDisabledMessage("name"),
      ),
    },
    {
      title: "Protocol",
      field: "library_protocol",
      width: "10%",
      headerVertical: false,
      headerTooltip: "Choose the Library Preparation Protocol",
      visible: true,
      cssClass: "regular-column",
      editor: "input",
      ...listEditorConfig(protocols),
      formatter: decorateFormatter(
        createListFormatter(protocols),
        libraryEditable("library_protocol"),
        libraryDisabledMessage("library_protocol"),
      ),
    },
    {
      title: "Comment Library",
      field: "comments",
      width: "10%",
      headerVertical: false,
      headerTooltip:
        "Description of the Library Generation and the Expected Quality <br><br> - ChIP-Seq library, includes adapter dimers <br> - ChIP-Seq library contains fragments > 1kbp <br> - Amplicon, bp is the product of interest",
      visible: true,
      cssClass: "regular-column",
      editor: "input",
      formatter: decorateFormatter(
        (cell) => ellipsisContainer(formatDisplayValue(cell.getValue())),
        libraryEditable("comments"),
        libraryDisabledMessage("comments"),
      ),
    },
    {
      title: "Analysis Type",
      field: "library_type",
      width: "8%",
      headerVertical: false,
      headerTooltip: "Choose the Analysis Type",
      visible: true,
      cssClass: "regular-column",
      editor: "list",
      editable: libraryEditable("library_type"),
      editorParams: dynamicEditorParams(getLibraryTypeOptions),
      formatter: decorateFormatter(
        dynamicListFormatter(getLibraryTypeOptions),
        libraryEditable("library_type"),
        libraryDisabledMessage("library_type"),
      ),
    },
    {
      title: "Unit",
      field: "measuring_unit",
      width: "6%",
      headerVertical: false,
      headerTooltip:
        "Choose the Measuring Unit <br><br> - Use 'Unknown' if no values are available",
      visible: true,
      cssClass: "regular-column",
      editor: "input",
      ...listEditorConfig(libraryUnits),
      formatter: decorateFormatter(
        createListFormatter(libraryUnits),
        libraryEditable("measuring_unit"),
        libraryDisabledMessage("measuring_unit"),
      ),
    },
    {
      title: "Amount",
      field: "measured_value",
      width: "6%",
      headerVertical: false,
      headerTooltip: "Enter the Measured Value",
      visible: true,
      cssClass: "regular-column",
      editor: "number",
      editorParams: { min: 0, step: 0.01 },
      validator: "min:0",
      hozAlign: "right",
      editable: libraryEditable("measured_value"),
      formatter: decorateFormatter(
        (cell) => {
          const value = cell.getValue();
          if (value === -1) {
            return ellipsisContainer(EMPTY_PLACEHOLDER);
          }
          return ellipsisContainer(formatDisplayValue(value));
        },
        libraryEditable("measured_value"),
        libraryDisabledMessage("measured_value"),
      ),
    },
    {
      title: "Size (bp)",
      field: "mean_fragment_size",
      width: "7%",
      headerVertical: false,
      headerTooltip: "Enter the Mean Fragment Size (in bp)",
      visible: true,
      cssClass: "regular-column",
      editor: "number",
      editorParams: { min: 1, step: 1 },
      validator: "min:1",
      hozAlign: "right",
      formatter: decorateFormatter(
        (cell) => ellipsisContainer(formatDisplayValue(cell.getValue())),
        libraryEditable("mean_fragment_size"),
        libraryDisabledMessage("mean_fragment_size"),
      ),
    },
    {
      title: "Volume (µl)",
      field: "volume",
      width: "7%",
      headerVertical: false,
      headerTooltip: "Enter the Measured Volume",
      visible: true,
      cssClass: "regular-column",
      editor: "number",
      editorParams: { min: 10, step: 0.01 },
      validator: "min:10",
      hozAlign: "right",
      formatter: decorateFormatter(
        (cell) => ellipsisContainer(formatDisplayValue(cell.getValue())),
        libraryEditable("volume"),
        libraryDisabledMessage("volume"),
      ),
    },
    {
      title: "Read Length",
      field: "read_length",
      width: "8%",
      headerVertical: false,
      headerTooltip: "Choose the Read Length",
      visible: true,
      cssClass: "regular-column",
      editor: "input",
      ...listEditorConfig(readLengths),
      formatter: decorateFormatter(
        createListFormatter(readLengths),
        libraryEditable("read_length"),
        libraryDisabledMessage("read_length"),
      ),
    },
    {
      title: "Depth (M)",
      field: "sequencing_depth",
      width: "6%",
      headerVertical: false,
      headerTooltip:
        "Enter the Sequencing Depth (in Millions of Paired-End Fragments)",
      visible: true,
      cssClass: "regular-column",
      editor: "number",
      editorParams: { min: 0.01, step: 0.1 },
      validator: "min:0.01",
      hozAlign: "right",
      formatter: decorateFormatter(
        (cell) => {
          const raw = cell.getValue();
          if (raw === "" || raw === undefined || raw === null) {
            return ellipsisContainer(EMPTY_PLACEHOLDER);
          }
          const value = Number(raw);
          const display = Number.isNaN(value)
            ? EMPTY_PLACEHOLDER
            : Math.round(value).toString();
          return ellipsisContainer(display);
        },
        libraryEditable("sequencing_depth"),
        libraryDisabledMessage("sequencing_depth"),
      ),
    },
    {
      title: "Index Type",
      field: "index_type",
      width: "8%",
      headerVertical: false,
      headerTooltip: "Choose the Index Type",
      visible: true,
      cssClass: "regular-column",
      editor: "input",
      ...listEditorConfig(indexTypes),
      formatter: decorateFormatter(
        createListFormatter(indexTypes),
        libraryEditable("index_type"),
        libraryDisabledMessage("index_type"),
      ),
    },
    {
      title: "# of Index Reads",
      field: "index_reads",
      width: "8%",
      headerVertical: false,
      headerTooltip: "Choose the Number of Index Reads",
      visible: true,
      cssClass: "regular-column",
      editor: "list",
      editorParams: dynamicEditorParams(dynamicOptions.reads),
      hozAlign: "left",
      editable: libraryEditable("index_reads"),
      formatter: decorateFormatter(
        dynamicListFormatter(dynamicOptions.reads),
        libraryEditable("index_reads"),
        libraryDisabledMessage("index_reads"),
      ),
    },
    {
      title: "Index I7",
      field: "index_i7",
      width: "8%",
      headerVertical: false,
      headerTooltip: "Choose Index I7",
      visible: true,
      cssClass: "regular-column",
      editor: "list",
      editorParams: dynamicEditorParams(dynamicOptions.i7),
      validator: indexSequenceValidator,
      editable: libraryEditable("index_i7"),
      formatter: decorateFormatter(
        dynamicListFormatter(dynamicOptions.i7),
        libraryEditable("index_i7"),
        libraryDisabledMessage("index_i7"),
      ),
    },
    {
      title: "Index I5",
      field: "index_i5",
      width: "8%",
      headerVertical: false,
      headerTooltip: "Choose Index I5",
      visible: true,
      cssClass: "regular-column",
      editor: "list",
      editorParams: dynamicEditorParams(dynamicOptions.i5),
      validator: indexSequenceValidator,
      editable: libraryEditable("index_i5"),
      formatter: decorateFormatter(
        dynamicListFormatter(dynamicOptions.i5),
        libraryEditable("index_i5"),
        libraryDisabledMessage("index_i5"),
      ),
    },
    {
      title: "Organism",
      field: "organism",
      width: "10%",
      headerVertical: false,
      headerTooltip: "Choose the Organism",
      visible: true,
      cssClass: "regular-column",
      editor: "input",
      ...listEditorConfig(organisms),
      formatter: decorateFormatter(
        createListFormatter(organisms),
        libraryEditable("organism"),
        libraryDisabledMessage("organism"),
      ),
    },
  ];
  columns.forEach((column) => {
    if (column.field !== "selected") {
      column.contextMenu = () =>
        cellContextMenu(true, true, true, getTabulatorInstance);
    }
  });

  return columns;
}

export function getAddRequestSampleColumns(
  getTabulatorInstance,
  editors = {},
  onSelectionChange,
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

  const getRowData = (cell) => cell?.getRow?.()?.getData?.() || {};
  const getNucleicAcidMeta = (rowData) => {
    const selectedId = rowData?.nucleic_acid_type;
    if (selectedId === undefined || selectedId === null) return null;
    return nucleicAcidTypes.find(
      (option) => String(option.value) === String(selectedId),
    );
  };
  const dynamicListFormatter = (getOptionsFn) => (cell) => {
    const options = getOptionsFn(getRowData(cell));
    const label = findOptionLabel(options, cell.getValue());
    if (label !== null && label !== undefined) {
      return ellipsisContainer(label);
    }
    const rawValue = cell.getValue();
    return ellipsisContainer(formatDisplayValue(rawValue, SELECT_PLACEHOLDER));
  };
  const dynamicEditorParams = (getOptionsFn) => (cell) => {
    const options = getOptionsFn(getRowData(cell));
    return {
      values: createValuesMap(options),
      clearable: true,
      emptyValue: "",
      autocomplete: true,
      listOnEmpty: true,
      placeholder: "Select",
    };
  };
  const getLibraryTypeOptions = (rowData) =>
    filterLibraryTypesByProtocol(analysisTypes, rowData.library_protocol);
  const getProtocolOptions = (rowData) => {
    const meta = getNucleicAcidMeta(rowData);
    const type = meta?.type ? String(meta.type).toLowerCase() : "";
    if (!type) return [];
    return protocols
      .filter((protocol) => String(protocol?.type ?? "").toLowerCase() === type)
      .sort((a, b) =>
        String(a.label || "").localeCompare(String(b.label || ""), undefined, {
          sensitivity: "base",
        }),
      );
  };
  const isCellSuspension = (rowData) => {
    const meta = getNucleicAcidMeta(rowData);
    const label = meta?.label ?? "";
    return String(label).trim().toLowerCase() === "cell suspension";
  };
  const isSampleEditable = (field, rowData) => {
    if (field === "library_protocol") {
      return Boolean(rowData.nucleic_acid_type);
    }
    if (field === "library_type") {
      return Boolean(rowData.library_protocol);
    }
    if (field === "measured_value") {
      return (
        Boolean(rowData.measuring_unit) && rowData.measuring_unit !== "Unknown"
      );
    }
    if (field === "gmo") {
      return isCellSuspension(rowData);
    }
    return true;
  };
  const sampleEditable = (field) => (cell) =>
    isSampleEditable(field, getRowData(cell));
  const sampleDisabledMessage = (field) => (cell) => {
    const rowData = getRowData(cell);
    if (field === "library_protocol" && !rowData.nucleic_acid_type) {
      return "Select an Input Type first.";
    }
    if (field === "library_type" && !rowData.library_protocol) {
      return "Select a Protocol first.";
    }
    if (field === "measured_value") {
      if (!rowData.measuring_unit) {
        return "Select a Measuring Unit first.";
      }
      if (rowData.measuring_unit === "Unknown") {
        return "Measured Value is disabled when unit is Unknown.";
      }
    }
    if (field === "gmo" && !isCellSuspension(rowData)) {
      return "GMO is enabled only for Cell Suspension inputs.";
    }
    return "";
  };

  const columns = [
    checkboxColumn(getTabulatorInstance, onSelectionChange),
    {
      title: "Name",
      field: "name",
      width: "10%",
      headerVertical: false,
      headerTooltip: "Enter a Unique Name",
      visible: true,
      cssClass: "regular-column",
      editor: "input",
      validator: (value) =>
        value === "" || value === undefined || value === null
          ? true
          : /^[A-Za-z0-9_-]+$/.test(String(value))
            ? true
            : "Only letters, numbers, _ and - are allowed.",
      formatter: decorateFormatter(
        (cell) => ellipsisContainer(formatDisplayValue(cell.getValue())),
        sampleEditable("name"),
        sampleDisabledMessage("name"),
      ),
    },
    {
      title: "Input Type",
      field: "nucleic_acid_type",
      width: "10%",
      headerVertical: false,
      headerTooltip: "Choose the Input Type",
      visible: true,
      cssClass: "regular-column",
      editor: "input",
      ...listEditorConfig(nucleicAcidTypes),
      formatter: decorateFormatter(
        createListFormatter(nucleicAcidTypes),
        sampleEditable("nucleic_acid_type"),
        sampleDisabledMessage("nucleic_acid_type"),
      ),
    },
    {
      title: "Comment Input",
      field: "comments",
      width: "10%",
      headerVertical: false,
      headerTooltip:
        "Description of the Input Generation and the Expected Quality <br><br> - pull-down assay, target: H3K9me3 <br> - Column-purified RNA, high quality, DNase treated <br> - FFPE extracted total RNA, fragmentation expected",
      visible: true,
      cssClass: "regular-column",
      editor: "input",
      formatter: decorateFormatter(
        (cell) => ellipsisContainer(formatDisplayValue(cell.getValue())),
        sampleEditable("comments"),
        sampleDisabledMessage("comments"),
      ),
    },
    {
      title: "Measuring Unit",
      field: "measuring_unit",
      width: "8%",
      headerVertical: false,
      headerTooltip:
        "Choose the Measuring Unit <br><br> - Use 'Unknown' if no values are available",
      visible: true,
      cssClass: "regular-column",
      editor: "input",
      ...listEditorConfig(sampleUnits),
      formatter: decorateFormatter(
        createListFormatter(sampleUnits),
        sampleEditable("measuring_unit"),
        sampleDisabledMessage("measuring_unit"),
      ),
    },
    {
      title: "Measured Value",
      field: "measured_value",
      width: "8%",
      headerVertical: false,
      headerTooltip: "Enter the Measured Value",
      visible: true,
      cssClass: "regular-column",
      editor: "number",
      editorParams: { min: 0, step: 0.01 },
      validator: "min:0",
      hozAlign: "right",
      editable: sampleEditable("measured_value"),
      formatter: decorateFormatter(
        (cell) => {
          const value = cell.getValue();
          if (value === -1) {
            return ellipsisContainer(EMPTY_PLACEHOLDER);
          }
          return ellipsisContainer(formatDisplayValue(value));
        },
        sampleEditable("measured_value"),
        sampleDisabledMessage("measured_value"),
      ),
    },
    {
      title: "Volume (µl)",
      field: "volume",
      width: "8%",
      headerVertical: false,
      headerTooltip: "Enter the Measured Volume",
      visible: true,
      cssClass: "regular-column",
      editor: "number",
      editorParams: { min: 10, step: 0.01 },
      validator: "min:10",
      hozAlign: "right",
      formatter: decorateFormatter(
        (cell) => ellipsisContainer(formatDisplayValue(cell.getValue())),
        sampleEditable("volume"),
        sampleDisabledMessage("volume"),
      ),
    },
    {
      title: "Protocol",
      field: "library_protocol",
      width: "10%",
      headerVertical: false,
      headerTooltip: "Choose the Library Preparation Protocol",
      visible: true,
      cssClass: "regular-column",
      editor: "list",
      editable: sampleEditable("library_protocol"),
      editorParams: dynamicEditorParams(getProtocolOptions),
      formatter: decorateFormatter(
        dynamicListFormatter(getProtocolOptions),
        sampleEditable("library_protocol"),
        sampleDisabledMessage("library_protocol"),
      ),
    },
    {
      title: "Analysis Type",
      field: "library_type",
      width: "8%",
      headerVertical: false,
      headerTooltip: "Choose the Analysis Type",
      visible: true,
      cssClass: "regular-column",
      editor: "list",
      editable: sampleEditable("library_type"),
      editorParams: dynamicEditorParams(getLibraryTypeOptions),
      formatter: decorateFormatter(
        dynamicListFormatter(getLibraryTypeOptions),
        sampleEditable("library_type"),
        sampleDisabledMessage("library_type"),
      ),
    },
    {
      title: "Read Length",
      field: "read_length",
      width: "8%",
      headerVertical: false,
      headerTooltip: "Choose the Read Length",
      visible: true,
      cssClass: "regular-column",
      editor: "input",
      ...listEditorConfig(readLengths),
      formatter: decorateFormatter(
        createListFormatter(readLengths),
        sampleEditable("read_length"),
        sampleDisabledMessage("read_length"),
      ),
    },
    {
      title: "Depth (M)",
      field: "sequencing_depth",
      width: "6%",
      headerVertical: false,
      headerTooltip:
        "Enter the Sequencing Depth (in Millions of Paired-End Fragments)",
      visible: true,
      cssClass: "regular-column",
      editor: "number",
      editorParams: { min: 0.01, step: 0.1 },
      validator: "min:0.01",
      hozAlign: "right",
      formatter: decorateFormatter(
        (cell) => {
          const raw = cell.getValue();
          if (raw === "" || raw === undefined || raw === null) {
            return ellipsisContainer(EMPTY_PLACEHOLDER);
          }
          const value = Number(raw);
          const display = Number.isNaN(value)
            ? EMPTY_PLACEHOLDER
            : Math.round(value).toString();
          return ellipsisContainer(display);
        },
        sampleEditable("sequencing_depth"),
        sampleDisabledMessage("sequencing_depth"),
      ),
    },
    {
      title: "Organism",
      field: "organism",
      width: "10%",
      headerVertical: false,
      headerTooltip: "Choose the Organism",
      visible: true,
      cssClass: "regular-column",
      editor: "input",
      ...listEditorConfig(organisms),
      formatter: decorateFormatter(
        createListFormatter(organisms),
        sampleEditable("organism"),
        sampleDisabledMessage("organism"),
      ),
    },
    {
      title: "Biosafety Level",
      field: "biosafety_level",
      width: "7%",
      headerVertical: false,
      headerTooltip: "Choose the Biosafety Level",
      visible: true,
      cssClass: "regular-column",
      editor: "input",
      ...listEditorConfig(biosafety),
      formatter: decorateFormatter(
        createListFormatter(biosafety),
        sampleEditable("biosafety_level"),
        sampleDisabledMessage("biosafety_level"),
      ),
    },
    {
      title: "GMO",
      field: "gmo",
      width: "5%",
      headerVertical: false,
      headerTooltip:
        "Choose if you are submitting Genetically Modified Organisms, often applies to living cells",
      visible: true,
      cssClass: "regular-column",
      editor: "input",
      editable: sampleEditable("gmo"),
      ...listEditorConfig(gmo),
      formatter: decorateFormatter(
        createListFormatter(gmo),
        sampleEditable("gmo"),
        sampleDisabledMessage("gmo"),
      ),
    },
  ];
  columns.forEach((column) => {
    if (column.field !== "selected") {
      column.contextMenu = () =>
        cellContextMenu(true, true, true, getTabulatorInstance);
    }
  });

  return columns;
}

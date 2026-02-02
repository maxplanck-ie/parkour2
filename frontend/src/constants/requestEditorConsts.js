import {
  cellContextMenu,
  ellipsisContainer,
  showNotification,
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

function formatBarcodeValue(value, rowData) {
  const barcode = value || EMPTY_PLACEHOLDER;
  const barcodeSuffix = value?.[2] ?? "";
  if (rowData?.record_type === "Sample" && barcodeSuffix === "L") {
    return `${barcode}*`;
  }
  return barcode;
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

const createListClipboardValueGetter =
  (options = [], placeholder = SELECT_PLACEHOLDER) =>
  (cell) => {
    const value = cell?.getValue?.();
    const label = findOptionLabel(options, value);
    if (label !== null && label !== undefined) {
      return String(label);
    }
    return formatDisplayValue(value, placeholder);
  };

const createDynamicListClipboardValueGetter =
  (getOptionsFn, getRowData, placeholder = SELECT_PLACEHOLDER) =>
  (cell) => {
    const options = getOptionsFn(getRowData(cell));
    const label = findOptionLabel(options, cell.getValue());
    if (label !== null && label !== undefined) {
      return String(label);
    }
    const rawValue = cell.getValue();
    return formatDisplayValue(rawValue, placeholder);
  };

function extractIndexSequence(value) {
  if (value === undefined || value === null) return "";
  const text = String(value).toUpperCase();
  const match = text.match(/[ATCG]{6,24}/);
  return match ? match[0] : "";
}

function listEditorConfig(options = [], placeholder = "Select") {
  return {
    editor: "list",
    editorParams: {
      values: createValuesMap(options),
      clearable: false,
      emptyValue: "",
      allowEmpty: true,
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

export function getRequestEditorLibraryColumns(
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
    getIndexReadsCount,
    getIndexI7Options,
    getIndexI5Options,
    showBarcode = false,
  } = editors;

  const libraryUnits =
    measuringUnits.length > 0
      ? measuringUnits
      : [
          { value: "ng/µl", label: "ng/µl (Concentration)" },
          { value: "Unknown", label: "Unknown" },
        ];

  const dynamicOptions = {
    i7: typeof getIndexI7Options === "function" ? getIndexI7Options : () => [],
    i5: typeof getIndexI5Options === "function" ? getIndexI5Options : () => [],
  };
  const resolveIndexReadsCount =
    typeof getIndexReadsCount === "function" ? getIndexReadsCount : () => 0;

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
      clearable: false,
      emptyValue: "",
      allowEmpty: true,
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
    if (field === "index_i7") {
      return resolveIndexReadsCount(rowData) >= 1;
    }
    if (field === "index_i5") {
      return resolveIndexReadsCount(rowData) >= 2;
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
    if (field === "index_i7") {
      if (!rowData.index_type) {
        return "Select an Index Type first.";
      }
      const reads = resolveIndexReadsCount(rowData);
      if (reads < 1) {
        return "Index I7 is not available for this Index Type.";
      }
    }
    if (field === "index_i5") {
      if (!rowData.index_type) {
        return "Select an Index Type first.";
      }
      const reads = resolveIndexReadsCount(rowData);
      if (reads < 2) {
        return "Index I5 is not available for this Index Type.";
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
    ...(showBarcode
      ? [
          {
            title: "Barcode",
            field: "barcode",
            width: 90,
            resizable: false,
            frozen: true,
            headerVertical: false,
            headerTooltip: "Barcode",
            visible: true,
            cssClass: "regular-column",
            editor: false,
            editable: false,
            contextMenu: (e, cell) =>
              cellContextMenu(true, false, false, getTabulatorInstance, {
                blockActionsOnDisabledCells: true,
                cell,
              }),
            cellDblClick: () => {
              showNotification("Barcode is read-only.", "warning");
            },
            formatter: (cell) => {
              const rowData = cell.getRow?.().getData?.() || {};
              return ellipsisContainer(
                formatBarcodeValue(cell.getValue(), rowData),
              );
            },
          },
        ]
      : []),
    {
      title: "Name",
      field: "name",
      minWidth: 110,
      widthGrow: 2,
      headerVertical: false,
      headerTooltip: "Enter a Unique Name",
      visible: true,
      frozen: true,
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
      minWidth: 110,
      widthGrow: 1.2,
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
      clipboardCopyValue: createListClipboardValueGetter(protocols),
    },
    {
      title: "Comment Library",
      field: "comments",
      minWidth: 110,
      widthGrow: 2,
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
      minWidth: 110,
      widthGrow: 1.2,
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
      clipboardCopyValue: createDynamicListClipboardValueGetter(
        getLibraryTypeOptions,
        getRowData,
      ),
    },
    {
      title: "Unit",
      field: "measuring_unit",
      width: 80,
      minWidth: 80,
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
      clipboardCopyValue: createListClipboardValueGetter(libraryUnits),
    },
    {
      title: "Value",
      field: "measured_value",
      width: 80,
      minWidth: 80,
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
      width: 80,
      minWidth: 80,
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
      width: 80,
      minWidth: 80,
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
      width: 100,
      minWidth: 100,
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
      clipboardCopyValue: createListClipboardValueGetter(readLengths),
    },
    {
      title: "Depth (M)",
      field: "sequencing_depth",
      width: 80,
      minWidth: 80,
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
      minWidth: 100,
      widthGrow: 1.2,
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
      clipboardCopyValue: createListClipboardValueGetter(indexTypes),
    },
    {
      title: "Index I7",
      field: "index_i7",
      minWidth: 100,
      widthGrow: 1.7,
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
      clipboardCopyValue: createDynamicListClipboardValueGetter(
        dynamicOptions.i7,
        getRowData,
      ),
      pasteValueResolver: (value) => extractIndexSequence(value),
    },
    {
      title: "Index I5",
      field: "index_i5",
      minWidth: 100,
      widthGrow: 1.7,
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
      clipboardCopyValue: createDynamicListClipboardValueGetter(
        dynamicOptions.i5,
        getRowData,
      ),
      pasteValueResolver: (value) => extractIndexSequence(value),
    },
    {
      title: "Organism",
      field: "organism",
      width: 100,
      minWidth: 100,
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
      clipboardCopyValue: createListClipboardValueGetter(organisms),
    },
  ];
  columns.forEach((column) => {
    if (column.field !== "selected" && !column.contextMenu) {
      column.contextMenu = (e, cell) =>
        cellContextMenu(true, true, true, getTabulatorInstance, {
          blockActionsOnDisabledCells: true,
          cell,
        });
    }
  });

  return columns;
}

export function getRequestEditorSampleColumns(
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
    showBarcode = false,
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
      clearable: false,
      emptyValue: "",
      allowEmpty: true,
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
  const isGmoAllowedInputType = (rowData) => {
    const meta = getNucleicAcidMeta(rowData);
    const label = meta?.label ?? "";
    const normalized = String(label).trim().toLowerCase();
    if (!normalized) return true;
    return !(normalized.includes("dna") || normalized.includes("rna"));
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
      return isGmoAllowedInputType(rowData);
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
    if (field === "gmo" && !isGmoAllowedInputType(rowData)) {
      return "Propagable & GMO is disabled when the Input Type contains DNA or RNA.";
    }
    return "";
  };

  const columns = [
    checkboxColumn(getTabulatorInstance, onSelectionChange),
    ...(showBarcode
      ? [
          {
            title: "Barcode",
            field: "barcode",
            width: 96,
            resizable: false,
            frozen: true,
            headerVertical: false,
            headerTooltip: "Barcode",
            visible: true,
            cssClass: "regular-column",
            editor: false,
            editable: false,
            contextMenu: (e, cell) =>
              cellContextMenu(true, false, false, getTabulatorInstance, {
                blockActionsOnDisabledCells: true,
                cell,
              }),
            cellDblClick: () => {
              showNotification("Barcode is read-only.", "warning");
            },
            formatter: (cell) => {
              const rowData = cell.getRow?.().getData?.() || {};
              return ellipsisContainer(
                formatBarcodeValue(cell.getValue(), rowData),
              );
            },
          },
        ]
      : []),
    {
      title: "Name",
      field: "name",
      minWidth: 110,
      widthGrow: 2,
      headerVertical: false,
      headerTooltip: "Enter a Unique Name",
      visible: true,
      frozen: true,
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
      minWidth: 110,
      widthGrow: 1.2,
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
      clipboardCopyValue: createListClipboardValueGetter(nucleicAcidTypes),
    },
    {
      title: "Comment Input",
      field: "comments",
      minWidth: 130,
      widthGrow: 2,
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
      title: "Unit",
      field: "measuring_unit",
      width: 90,
      minWidth: 80,
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
      clipboardCopyValue: createListClipboardValueGetter(sampleUnits),
    },
    {
      title: "Value",
      field: "measured_value",
      width: 90,
      minWidth: 80,
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
      width: 90,
      minWidth: 80,
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
      minWidth: 110,
      widthGrow: 1.2,
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
      clipboardCopyValue: createDynamicListClipboardValueGetter(
        getProtocolOptions,
        getRowData,
      ),
    },
    {
      title: "Analysis Type",
      field: "library_type",
      minWidth: 110,
      widthGrow: 1.2,
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
      clipboardCopyValue: createDynamicListClipboardValueGetter(
        getLibraryTypeOptions,
        getRowData,
      ),
    },
    {
      title: "Read Length",
      field: "read_length",
      width: 100,
      minWidth: 100,
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
      clipboardCopyValue: createListClipboardValueGetter(readLengths),
    },
    {
      title: "Depth (M)",
      field: "sequencing_depth",
      width: 90,
      minWidth: 80,
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
      width: 100,
      minWidth: 100,
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
      clipboardCopyValue: createListClipboardValueGetter(organisms),
    },
    {
      title: "Biosafety Level",
      field: "biosafety_level",
      width: 100,
      minWidth: 100,
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
      clipboardCopyValue: createListClipboardValueGetter(biosafety),
    },
    {
      title: "Propagable & GMO",
      field: "gmo",
      minWidth: 90,
      widthGrow: 1,
      headerVertical: false,
      headerTooltip:
        "Propagable & GMO:<br>Select 'Yes' if the material includes propagable, genetically modified organisms (e.g., viable genetically engineered cells).<br>In this case, complete and attach Formblatt S1 – Aufzeichnung weiterer genetischer Arbeiten. Documentation of all genetic engineering work is required under § 6 Gentechnikgesetz (GenTG).",
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
      clipboardCopyValue: createListClipboardValueGetter(gmo),
    },
  ];
  columns.forEach((column) => {
    if (column.field !== "selected" && !column.contextMenu) {
      column.contextMenu = (e, cell) =>
        cellContextMenu(true, true, true, getTabulatorInstance, {
          blockActionsOnDisabledCells: true,
          cell,
        });
    }
  });

  return columns;
}

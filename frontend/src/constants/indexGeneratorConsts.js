import iconDeleteRequest from "../assets/icons/action_delete_request.svg";

export const INDEX_GENERATOR_API_ENDPOINTS = {
  records: "/api/index_generator/",
  readLengths: "/api/read_lengths/",
  poolSizes: "/api/pool_sizes/",
  indexTypes: "/api/generator_index_types/",
  edit: "/api/index_generator/edit/",
  startCoordinates: "/api/index_generator/start_coordinates/",
  generateIndices: "/api/index_generator/generate_indices/",
  savePool: "/api/index_generator/save_pool/"
};

export const INDEX_GENERATOR_FIELDS = {
  pk: "pk",
  rowKey: "rowKey",
  recordType: "record_type",
  requestName: "request_name",
  barcode: "barcode",
  name: "name",
  type: "type",
  selected: "selected",
  sequencingDepth: "sequencing_depth",
  libraryProtocolName: "library_protocol_name",
  readLength: "read_length",
  readLengthName: "read_length_name",
  indexType: "index_type",
  indexI7: "index_i7",
  indexI5: "index_i5",
  indexI7Id: "index_i7_id",
  indexI5Id: "index_i5_id",
  coordinate: "coordinate"
};

export const INDEX_GENERATOR_POOL_ACTIONS = {
  removeFromPool: "removeFromPool"
};

export const INDEX_GENERATOR_RECORD_TYPES = {
  library: "Library",
  sample: "Sample",
  libraryCode: "L",
  sampleCode: "S"
};

export const INDEX_GENERATOR_POOL_PAYLOAD_KEYS = {
  libraries: "libraries",
  samples: "samples",
  indexTypeIds: "index_type_ids",
  poolSizeId: "pool_size_id",
  startCoordinate: "start_coord",
  direction: "direction",
  data: "data"
};

export const INDEX_GENERATOR_RESPONSE_KEYS = {
  success: "success",
  message: "message",
  detail: "detail",
  data: "data",
  coordinates: "coordinates",
  directionOptions: "direction_options",
  defaultStartCoordinate: "default_start_coord"
};

export const INDEX_GENERATOR_DEFAULTS = {
  leftPanelWidthPercent: 50,
  startCoordinate: "A1",
  direction: "down",
  emptyDisplay: "-",
  selectDisplay: "Select",
  maxColorBalanceCycles: 12,
  duplicatePreviewLimit: 3
};

export const INDEX_GENERATOR_DIRECTION_OPTIONS = [
  { value: "down", label: "Column-wise" },
  { value: "right", label: "Row-wise" },
  { value: "diagonal", label: "Diagonal" }
];

export const INDEX_GENERATOR_DIRECTION_ORDER = {
  down: 0,
  right: 1,
  diagonal: 2
};

export const INDEX_GENERATOR_INDEX_FIELDS = {
  i7: "index_i7",
  i5: "index_i5"
};

export const INDEX_GENERATOR_COLOR_BALANCE = {
  redBases: ["A", "C"],
  greenBases: ["G", "T"],
  warningThresholdPercent: 20,
  warningDominancePercent: 80
};

export const INDEX_GENERATOR_PROTOCOL_PATTERNS = {
  nanopore: /oxford\s*nanopore|nanopore|\bont\b/
};

const emptyFormatter = (value) => {
  const normalized = value === undefined || value === null ? "" : value;
  return normalized === "" ? INDEX_GENERATOR_DEFAULTS.emptyDisplay : normalized;
};

const escapeHtml = (value) =>
  String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");

const valueContainer = (
  displayHtml,
  boldText = false,
  includeTitle = true,
  tooltipText = displayHtml
) =>
  `<div ${
    includeTitle ? `title='${escapeHtml(tooltipText)}' ` : ""
  }style="overflow: hidden; white-space: nowrap; text-overflow: ellipsis; padding: 12px 8px 12px 12px; font-weight: ${
    boldText === true ? "bold" : "normal"
  }">
                ${displayHtml}
              </div>`;

const sequenceFormatter = (cell, { includeTitle = true } = {}) => {
  const sequence = String(cell.getValue() || "");
  if (!sequence) {
    return readonlyValueFormatter(INDEX_GENERATOR_DEFAULTS.emptyDisplay, {
      includeTitle
    });
  }

  const html = sequence
    .split("")
    .map((base) => {
      const upper = String(base).toUpperCase();
      let className = "nt-other";
      if (upper === "A" || upper === "C") {
        className = "nt-red";
      } else if (upper === "G" || upper === "T") {
        className = "nt-green";
      }
      return `<span class="nt ${className}">${escapeHtml(base)}</span>`;
    })
    .join("");

  return valueContainer(
    `<span class="sequence-colored">${html}</span>`,
    false,
    includeTitle,
    sequence
  );
};

const indexSequenceFormatter = (cell) => {
  const rowData = cell.getRow().getData();
  const hasIndexType = Boolean(rowData[INDEX_GENERATOR_FIELDS.indexType]);
  const hasIndexValue = Boolean(String(cell.getValue() || "").trim());
  const disabled = !hasIndexType || !hasIndexValue;
  setCellDisabledState(
    cell,
    disabled,
    !hasIndexType
      ? "Choose the Index Type first."
      : disabled
        ? "Generate indices to assign this value."
        : ""
  );

  return sequenceFormatter(cell, { includeTitle: !disabled });
};

const readonlyValueFormatter = (value, { includeTitle = true } = {}) =>
  valueContainer(
    escapeHtml(emptyFormatter(value)),
    false,
    includeTitle,
    emptyFormatter(value)
  );

const readonlyFormatter = (cell) => readonlyValueFormatter(cell.getValue());

const setCellTooltip = (cell, message = "") => {
  const element = cell.getElement?.();
  if (!element) {
    return;
  }

  const text = String(message || "").trim();
  element.removeAttribute("data-tooltip-original");
  element.removeAttribute("title");
  if (text) {
    element.setAttribute("data-tooltip-original", text);
  }
};

const setCellDisabledState = (cell, disabled, message = "") => {
  const element = cell.getElement?.();
  if (!element) {
    return;
  }

  element.classList.toggle("disable-editing", Boolean(disabled));
  if (disabled && message) {
    element.setAttribute("data-disabled-tooltip", message);
    element.setAttribute("data-tooltip-original", message);
    element.removeAttribute("title");
    element
      .querySelectorAll("[title],[data-tooltip-original]")
      .forEach((node) => {
        if (node !== element) {
          node.removeAttribute("title");
          node.removeAttribute("data-tooltip-original");
        }
      });
  } else {
    element.removeAttribute("data-disabled-tooltip");
    element.removeAttribute("data-tooltip-original");
    element.removeAttribute("title");
  }
};

const selectValueFormatter = (label, options = {}) =>
  readonlyValueFormatter(
    label || INDEX_GENERATOR_DEFAULTS.selectDisplay,
    options
  );

const selectCellFormatter = (cell, label, emptyTooltip) => {
  setCellTooltip(cell, label || emptyTooltip);
  return selectValueFormatter(label);
};

const selectOptions = (items, includeEmpty = false, emptyLabel = "-") => {
  const options = includeEmpty ? [{ label: emptyLabel, value: 0 }] : [];
  return options.concat(
    (items || []).map((item) => ({
      label: item.name,
      value: item.id
    }))
  );
};

const applyGroupHeaderStyles = (wrapper, main, title, details) => {
  Object.assign(wrapper.style, {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center"
  });
  Object.assign(main.style, {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center"
  });
  Object.assign(title.style, {
    fontWeight: "bold",
    fontSize: "12px",
    color: "#333"
  });
  Object.assign(details.style, {
    fontWeight: "normal",
    fontSize: "12px",
    marginLeft: "2px",
    color: "black"
  });
};

const createGroupHeaderBase = (
  value,
  count,
  requestGroupSummary,
  extraClass = ""
) => {
  const summary = requestGroupSummary(value);
  const wrapper = document.createElement("div");
  wrapper.className = ["group-row-content", extraClass]
    .filter(Boolean)
    .join(" ");

  const main = document.createElement("div");
  main.className = "group-row-main";

  const text = document.createElement("div");
  const title = document.createElement("span");
  title.className = "group-row-title";
  title.textContent = value;

  const details = document.createElement("span");
  details.className = "group-row-summary";
  details.textContent =
    ` (#: ${count} ${summary.countLabel}, Total Depth: ${summary.totalDepth}M, ` +
    `Read Lengths: ${summary.readLengthDisplay}, Biosafety Level: ${summary.biosafetyLevel})`;

  applyGroupHeaderStyles(wrapper, main, title, details);
  text.append(title, details);
  main.appendChild(text);

  const actions = document.createElement("div");
  actions.className = "group-action-buttons-container";
  actions.addEventListener("click", (event) => event.stopPropagation());

  return { wrapper, main, actions };
};

const createGroupActionButton = ({
  title,
  handler,
  icon,
  iconClass = "",
  fallbackText = title,
  ariaLabel = title
}) => {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "group-action-button";
  button.title = title;
  button.setAttribute("aria-label", ariaLabel);
  button.addEventListener("click", handler);

  if (icon) {
    const image = document.createElement("img");
    if (iconClass) {
      image.className = iconClass;
    }
    image.src = icon;
    image.alt = ariaLabel;
    image.width = 24;
    image.height = 24;
    button.appendChild(image);
  } else {
    button.textContent = fallbackText;
  }

  return button;
};

export function indexGeneratorSourceGroupHeader(
  value,
  count,
  data,
  requestGroupSummary,
  selectAllInGroup,
  deselectAllInGroup,
  icons = {}
) {
  const { wrapper, main, actions } = createGroupHeaderBase(
    value,
    count,
    requestGroupSummary
  );

  [
    {
      title: "Select All",
      icon: icons.selectAll,
      handler: () => selectAllInGroup(data)
    },
    {
      title: "Deselect All",
      icon: icons.deselectAll,
      handler: () => deselectAllInGroup(data)
    }
  ].forEach((action) => {
    actions.appendChild(createGroupActionButton(action));
  });

  wrapper.append(main, actions);
  return wrapper;
}

export function indexGeneratorPoolGroupHeader(
  value,
  count,
  data,
  requestGroupSummary,
  removePoolRowsInGroup
) {
  const { wrapper, main, actions } = createGroupHeaderBase(
    value,
    count,
    requestGroupSummary,
    "pool-group-row-content"
  );

  actions.appendChild(
    createGroupActionButton({
      title: "Remove All from This Request",
      ariaLabel: "Remove All from This Request",
      icon: iconDeleteRequest,
      iconClass: "group-action-icon-img",
      handler: () => removePoolRowsInGroup(data)
    })
  );

  wrapper.append(main, actions);
  return wrapper;
}

export function indexGeneratorSourceColumnDefs({
  readLengths = [],
  generatorIndexTypes = [],
  onSelectionChange,
  getIndexTypeName
} = {}) {
  return [
    {
      title: "",
      field: INDEX_GENERATOR_FIELDS.selected,
      width: 30,
      minWidth: 30,
      hozAlign: "center",
      headerSort: false,
      resizable: false,
      formatter: (cell) => {
        const rowData = cell.getRow().getData();
        const input = document.createElement("input");
        input.type = "checkbox";
        input.style.top = "-4px";
        input.checked = Boolean(cell.getValue());
        input.addEventListener("click", (event) => event.stopPropagation());
        input.addEventListener("change", (event) => {
          onSelectionChange(rowData, event.target.checked);
        });
        return input;
      },
      cssClass: "checkbox-column right-border",
      frozen: true,
      download: false,
      clipboard: false
    },
    {
      title: "Name",
      field: INDEX_GENERATOR_FIELDS.name,
      minWidth: 100,
      widthGrow: 2,
      formatter: readonlyFormatter,
      cssClass: "name-column right-border"
    },
    {
      title: "Barcode",
      field: INDEX_GENERATOR_FIELDS.barcode,
      minWidth: 98,
      widthGrow: 1.1,
      formatter: readonlyFormatter,
      cssClass: "details-column barcode-column right-border"
    },
    {
      title: "Depth (M)",
      field: INDEX_GENERATOR_FIELDS.sequencingDepth,
      minWidth: 70,
      widthGrow: 1,
      formatter: readonlyFormatter,
      cssClass: "depth-column right-border"
    },
    {
      title: "Length",
      field: INDEX_GENERATOR_FIELDS.readLength,
      minWidth: 85,
      widthGrow: 1,
      cssClass: "length-column right-border",
      editor: "list",
      headerTooltip: "Choose the Read Length",
      editorParams: {
        values: selectOptions(
          readLengths,
          true,
          INDEX_GENERATOR_DEFAULTS.selectDisplay
        ),
        placeholder: INDEX_GENERATOR_DEFAULTS.selectDisplay,
        emptyValue: 0,
        allowEmpty: true,
        autocomplete: true,
        listOnEmpty: true
      },
      formatter: (cell) => {
        const value = String(cell.getValue() || "");
        const match = (readLengths || []).find(
          (item) => String(item.id) === value
        );
        return selectCellFormatter(cell, match?.name, "Choose the Read Length");
      }
    },
    {
      title: "Protocol",
      field: INDEX_GENERATOR_FIELDS.libraryProtocolName,
      minWidth: 100,
      widthGrow: 1.8,
      formatter: readonlyFormatter,
      cssClass: "protocol-column right-border"
    },
    {
      title: "Index Type",
      field: INDEX_GENERATOR_FIELDS.indexType,
      minWidth: 100,
      widthGrow: 1.8,
      cssClass: "index-type-column right-border",
      editor: "list",
      headerTooltip: "Choose the Index Type",
      editable: (cell) =>
        cell.getRow().getData()[INDEX_GENERATOR_FIELDS.type] !==
        INDEX_GENERATOR_RECORD_TYPES.libraryCode,
      editorParams: {
        values: selectOptions(
          generatorIndexTypes,
          true,
          INDEX_GENERATOR_DEFAULTS.selectDisplay
        ),
        placeholder: INDEX_GENERATOR_DEFAULTS.selectDisplay,
        emptyValue: 0,
        allowEmpty: true,
        autocomplete: true,
        listOnEmpty: true
      },
      formatter: (cell) => {
        const rowData = cell.getRow().getData();
        const disabled =
          rowData[INDEX_GENERATOR_FIELDS.type] ===
          INDEX_GENERATOR_RECORD_TYPES.libraryCode;
        const label = getIndexTypeName?.(cell.getValue());
        if (disabled) {
          setCellDisabledState(
            cell,
            disabled,
            "Index Type is fixed for libraries."
          );
          return selectValueFormatter(label, { includeTitle: false });
        }

        setCellDisabledState(cell, false);
        return selectCellFormatter(cell, label, "Choose the Index Type");
      }
    },
    {
      title: "Index I7",
      field: INDEX_GENERATOR_FIELDS.indexI7,
      minWidth: 80,
      widthGrow: 1,
      formatter: indexSequenceFormatter,
      cssClass: "sequence-column sequence-text right-border"
    },
    {
      title: "Index I5",
      field: INDEX_GENERATOR_FIELDS.indexI5,
      minWidth: 80,
      widthGrow: 1,
      formatter: indexSequenceFormatter,
      cssClass: "sequence-column sequence-text"
    }
  ];
}

export function indexGeneratorPoolColumnDefs({ onRemoveRow } = {}) {
  return [
    {
      title: "",
      field: INDEX_GENERATOR_POOL_ACTIONS.removeFromPool,
      width: 34,
      minWidth: 34,
      hozAlign: "center",
      vertAlign: "middle",
      headerSort: false,
      resizable: false,
      formatter: (cell) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "pool-row-remove-button";
        button.title = "Remove from Pool";
        button.setAttribute("aria-label", "Remove from Pool");
        button.innerHTML = "&times;";
        button.addEventListener("click", (event) => {
          event.stopPropagation();
          onRemoveRow?.(cell.getRow().getData());
        });
        return button;
      },
      cssClass: "pool-row-remove-cell right-border",
      download: false,
      clipboard: false
    },
    {
      title: "Name",
      field: INDEX_GENERATOR_FIELDS.name,
      minWidth: 135,
      widthGrow: 1.5,
      formatter: readonlyFormatter,
      cssClass: "name-column right-border"
    },
    {
      title: "Barcode",
      field: INDEX_GENERATOR_FIELDS.barcode,
      minWidth: 92,
      widthGrow: 1,
      formatter: readonlyFormatter,
      cssClass: "details-column barcode-column right-border"
    },
    {
      title: "L/S",
      field: INDEX_GENERATOR_FIELDS.type,
      minWidth: 42,
      widthGrow: 0.5,
      formatter: readonlyFormatter,
      cssClass: "type-column right-border"
    },
    {
      title: "Depth (M)",
      field: INDEX_GENERATOR_FIELDS.sequencingDepth,
      minWidth: 70,
      widthGrow: 0.7,
      formatter: readonlyFormatter,
      cssClass: "depth-column right-border"
    },
    {
      title: "Coord",
      field: INDEX_GENERATOR_FIELDS.coordinate,
      minWidth: 68,
      widthGrow: 0.7,
      formatter: readonlyFormatter,
      cssClass: "coord-column right-border"
    },
    {
      title: "Index I7 ID",
      field: INDEX_GENERATOR_FIELDS.indexI7Id,
      minWidth: 78,
      widthGrow: 0.8,
      formatter: readonlyFormatter,
      cssClass: "index-id-column right-border"
    },
    {
      title: "Index I7",
      field: INDEX_GENERATOR_FIELDS.indexI7,
      minWidth: 92,
      widthGrow: 1,
      formatter: sequenceFormatter,
      cssClass: "sequence-column sequence-text right-border"
    },
    {
      title: "Index I5 ID",
      field: INDEX_GENERATOR_FIELDS.indexI5Id,
      minWidth: 78,
      widthGrow: 0.8,
      formatter: readonlyFormatter,
      cssClass: "index-id-column right-border"
    },
    {
      title: "Index I5",
      field: INDEX_GENERATOR_FIELDS.indexI5,
      minWidth: 92,
      widthGrow: 1,
      formatter: sequenceFormatter,
      cssClass: "sequence-column sequence-text"
    }
  ];
}

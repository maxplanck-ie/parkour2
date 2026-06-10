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

const sequenceFormatter = (cell) => {
  const sequence = String(cell.getValue() || "");
  if (!sequence) {
    return INDEX_GENERATOR_DEFAULTS.emptyDisplay;
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

  return `<span class="sequence-colored">${html}</span>`;
};

const readonlyFormatter = (cell) => emptyFormatter(cell.getValue());

const selectOptions = (items, includeEmpty = false, emptyLabel = "-") => {
  const options = includeEmpty ? [{ label: emptyLabel, value: 0 }] : [];
  return options.concat(
    (items || []).map((item) => ({
      label: item.name,
      value: item.id
    }))
  );
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
  const summary = requestGroupSummary(value);
  const wrapper = document.createElement("div");
  wrapper.className = "group-row-content";

  const main = document.createElement("div");
  main.className = "group-row-main";

  const text = document.createElement("div");
  const title = document.createElement("span");
  title.className = "group-row-title";
  title.textContent = value;

  const details = document.createElement("span");
  details.className = "group-row-summary";
  details.textContent = ` (#: ${count} ${summary.countLabel}, Total Depth: ${summary.totalDepth}M, Read Lengths: ${summary.readLengthDisplay}, ${summary.biosafetyLevel})`;

  text.append(title, details);

  const actions = document.createElement("div");
  actions.className = "group-action-buttons-container";
  actions.addEventListener("click", (event) => event.stopPropagation());

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
    const button = document.createElement("button");
    button.type = "button";
    button.className = "group-action-button";
    button.title = action.title;
    button.addEventListener("click", action.handler);

    if (action.icon) {
      const image = document.createElement("img");
      image.src = action.icon;
      image.alt = action.title;
      image.width = 24;
      image.height = 24;
      button.appendChild(image);
    } else {
      button.textContent = action.title;
    }

    actions.appendChild(button);
  });

  main.append(text, actions);
  wrapper.appendChild(main);
  return wrapper;
}

export function indexGeneratorSourceColumnDefs({
  readLengths = [],
  generatorIndexTypes = [],
  onSelectionChange,
  isCompatibleWithPool,
  getIndexTypeName
} = {}) {
  return [
    {
      title: "",
      field: INDEX_GENERATOR_FIELDS.selected,
      width: 44,
      minWidth: 44,
      hozAlign: "center",
      headerSort: false,
      formatter: (cell) => {
        const rowData = cell.getRow().getData();
        const input = document.createElement("input");
        input.type = "checkbox";
        input.checked = Boolean(cell.getValue());
        input.addEventListener("click", (event) => event.stopPropagation());
        input.addEventListener("change", (event) => {
          if (
            event.target.checked &&
            typeof isCompatibleWithPool === "function" &&
            !isCompatibleWithPool(rowData)
          ) {
            event.target.checked = false;
            rowData[INDEX_GENERATOR_FIELDS.selected] = false;
            return;
          }

          onSelectionChange(rowData, event.target.checked);
        });
        return input;
      },
      cssClass: "checkbox-column",
      frozen: true,
      download: false,
      clipboard: false
    },
    {
      title: "Name",
      field: INDEX_GENERATOR_FIELDS.name,
      width: 220,
      minWidth: 160,
      formatter: readonlyFormatter
    },
    {
      title: "Barcode",
      field: INDEX_GENERATOR_FIELDS.barcode,
      width: 120,
      minWidth: 110,
      formatter: readonlyFormatter,
      cssClass: "barcode-text"
    },
    {
      title: "Depth (M)",
      field: INDEX_GENERATOR_FIELDS.sequencingDepth,
      width: 95,
      minWidth: 90,
      formatter: readonlyFormatter
    },
    {
      title: "Length",
      field: INDEX_GENERATOR_FIELDS.readLength,
      width: 120,
      minWidth: 100,
      editor: "list",
      editorParams: {
        values: selectOptions(readLengths, true)
      },
      formatter: (cell) => {
        const value = String(cell.getValue() || "");
        const match = (readLengths || []).find(
          (item) => String(item.id) === value
        );
        return match?.name || INDEX_GENERATOR_DEFAULTS.emptyDisplay;
      }
    },
    {
      title: "Protocol",
      field: INDEX_GENERATOR_FIELDS.libraryProtocolName,
      width: 230,
      minWidth: 180,
      formatter: readonlyFormatter
    },
    {
      title: "Index Type",
      field: INDEX_GENERATOR_FIELDS.indexType,
      width: 190,
      minWidth: 160,
      editor: "list",
      editable: (cell) =>
        cell.getRow().getData()[INDEX_GENERATOR_FIELDS.type] !==
        INDEX_GENERATOR_RECORD_TYPES.libraryCode,
      editorParams: {
        values: selectOptions(generatorIndexTypes, true)
      },
      formatter: (cell) => {
        const rowData = cell.getRow().getData();
        if (
          rowData[INDEX_GENERATOR_FIELDS.type] ===
          INDEX_GENERATOR_RECORD_TYPES.libraryCode
        ) {
          cell.getElement().classList.add("disable-editing");
        } else {
          cell.getElement().classList.remove("disable-editing");
        }
        return (
          getIndexTypeName?.(cell.getValue()) ||
          INDEX_GENERATOR_DEFAULTS.emptyDisplay
        );
      }
    },
    {
      title: "Index I7",
      field: INDEX_GENERATOR_FIELDS.indexI7,
      width: 135,
      minWidth: 120,
      formatter: sequenceFormatter,
      cssClass: "sequence-text"
    },
    {
      title: "Index I5",
      field: INDEX_GENERATOR_FIELDS.indexI5,
      width: 135,
      minWidth: 120,
      formatter: sequenceFormatter,
      cssClass: "sequence-text"
    }
  ];
}

export function indexGeneratorPoolColumnDefs() {
  return [
    {
      title: "Name",
      field: INDEX_GENERATOR_FIELDS.name,
      width: 220,
      minWidth: 160,
      formatter: readonlyFormatter
    },
    {
      title: "Barcode",
      field: INDEX_GENERATOR_FIELDS.barcode,
      width: 120,
      minWidth: 110,
      formatter: readonlyFormatter,
      cssClass: "barcode-text"
    },
    {
      title: "L/S",
      field: INDEX_GENERATOR_FIELDS.type,
      width: 70,
      minWidth: 60,
      formatter: readonlyFormatter
    },
    {
      title: "Depth (M)",
      field: INDEX_GENERATOR_FIELDS.sequencingDepth,
      width: 95,
      minWidth: 90,
      formatter: readonlyFormatter
    },
    {
      title: "Coord",
      field: INDEX_GENERATOR_FIELDS.coordinate,
      width: 110,
      minWidth: 100,
      formatter: readonlyFormatter
    },
    {
      title: "Index I7 ID",
      field: INDEX_GENERATOR_FIELDS.indexI7Id,
      width: 110,
      minWidth: 100,
      formatter: readonlyFormatter
    },
    {
      title: "Index I7",
      field: INDEX_GENERATOR_FIELDS.indexI7,
      width: 135,
      minWidth: 120,
      formatter: sequenceFormatter,
      cssClass: "sequence-text"
    },
    {
      title: "Index I5 ID",
      field: INDEX_GENERATOR_FIELDS.indexI5Id,
      width: 110,
      minWidth: 100,
      formatter: readonlyFormatter
    },
    {
      title: "Index I5",
      field: INDEX_GENERATOR_FIELDS.indexI5,
      width: 135,
      minWidth: 120,
      formatter: sequenceFormatter,
      cssClass: "sequence-text"
    }
  ];
}

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

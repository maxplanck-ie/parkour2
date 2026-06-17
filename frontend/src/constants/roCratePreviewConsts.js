import roCrateHiddenFields from "../../../shared/roCrateHiddenFields.json";

// API contract
export const RO_CRATE_ENDPOINT = "/api/generate_ro_crate/";

// Export section selector
export const RO_CRATE_SECTION_OPTIONS = [
  {
    id: "request",
    label: "Request Details",
    description:
      "General request information, including the description, attached files, and request-level details."
  },
  {
    id: "samples",
    label: "Sample Metadata",
    description:
      "The selected sample records and their sample-specific metadata."
  },
  {
    id: "libraries",
    label: "Library Metadata",
    description:
      "The selected library records and their library-specific metadata."
  },
  {
    id: "library_preparation",
    label: "Library Preparation",
    description:
      "Preparation values such as starting amount, concentration, or PCR cycles."
  },
  {
    id: "pooling",
    label: "Pooling",
    description:
      "Pool membership and pooling information connected to the selected records."
  },
  {
    id: "protocols",
    label: "Protocols",
    description: "Protocols used for the selected libraries or samples."
  },
  {
    id: "organisms",
    label: "Organisms",
    description:
      "Organism names and related metadata linked to the selected records."
  },
  {
    id: "library_types",
    label: "Library Types",
    description: "Library type definitions used by the selected records."
  },
  {
    id: "read_lengths",
    label: "Read Lengths",
    description:
      "Read length settings linked to the selected sequencing records."
  },
  {
    id: "index_types",
    label: "Index Types",
    description: "Index type settings used for the selected records."
  },
  {
    id: "nucleic_acid_types",
    label: "Input Types",
    description:
      "Input material or nucleic-acid type information for the selected samples."
  },
  {
    id: "index_pools",
    label: "Index Pools",
    description:
      "Index pool assignments connected to the selected samples, libraries, or lanes."
  },
  {
    id: "flowcells",
    label: "Flowcells",
    description:
      "Flowcell or sequencing-run information linked to the exported records."
  },
  {
    id: "sequencers",
    label: "Sequencers",
    description:
      "Sequencing instrument details referenced by the exported flowcells."
  },
  {
    id: "lanes",
    label: "Lanes",
    description: "Lane information linked to the exported flowcells."
  }
];

// JSON-LD entity identifiers
export const RO_CRATE_ENTITY_IDS = {
  rootDataset: "./",
  metadataDescriptor: "ro-crate-metadata.json"
};

export const RO_CRATE_ENTITY_PREFIXES = {
  requestContext: "#request-context-",
  study: "#study-",
  libraryMaterial: "#library-material-",
  sampleMaterial: "#sample-material-",
  sourceSample: "#source-sample-",
  requestFile: "#request-file-",
  flowcellAssay: "#flowcell-assay-",
  lane: "#lane-",
  sequencer: "#sequencer-",
  indexPool: "#index-pool-",
  protocol: "#protocol-"
};

// JSON-LD property keys used by the preview parser
export const RO_CRATE_FIELD_KEYS = {
  id: "@id",
  type: "@type",
  name: "name",
  identifier: "identifier",
  additionalType: "additionalType",
  additionalProperty: "additionalProperty",
  parameterValue: "parameterValue",
  value: "value",
  materials: "materials",
  samples: "samples",
  otherMaterials: "otherMaterials",
  dataFiles: "dataFiles",
  processSequence: "processSequence",
  requestContext: "requestContext",
  contentUrl: "contentUrl",
  encodingFormat: "encodingFormat",
  isPartOf: "isPartOf"
};

// Display labels and fallback text
export const RO_CRATE_RECORD_TYPES = {
  library: "Library",
  sample: "Sample",
  fallback: "Record"
};

export const RO_CRATE_PREVIEW_LABELS = {
  emptyTitle: "RO-Crate preview",
  loadedTitle: "Review selected RO-Crate metadata",
  emptySubtitle:
    "Select libraries or samples and open Preview from the RO-Crate export dialog.",
  loadedSubtitle:
    "Inspect the selected Parkour records before exporting the final ZIP.",
  unnamedRequest: "Selected request",
  unnamedRecord: "Unnamed record",
  noRecords: "No library or sample records were identified for this request."
};

// Sensitive/backend-only field filtering
export const RO_CRATE_INBUILT_HIDDEN_FIELDS = [
  "@id",
  "@type",
  "about",
  "additionalProperty",
  "additionalType",
  "comment",
  "comments",
  "contentSize",
  "encodingFormat",
  "hasPart",
  "identifier",
  "includedInDataCatalog",
  "isPartOf",
  "mentions",
  "publisher",
  "sameAs",
  "subjectOf",
  "url"
];

export const RO_CRATE_RELATED_MODEL_HIDDEN_FIELDS = [
  "sample",
  "library"
];

export const USER_DEFINED_VARIABLE_HIDDEN_FIELDS =
  roCrateHiddenFields.userDefinedVariableHiddenFields;

export const RO_CRATE_VISIBLE_ID_FIELDS = [
  "i7_id",
  "i5_id",
  "indexI7Id",
  "indexI5Id"
];

// Relation display rules
export const RO_CRATE_LINKED_MODEL_RELATION_FIELDS = [
  "organism",
  "nucleicAcidType",
  "libraryType",
  "readLength",
  "indexType",
  "indexI7",
  "indexI5",
  "selectedIndexPair",
  "associatedPool"
];

export const RO_CRATE_RELATION_FIELDS = {
  indexI7: "Selected I7 Index",
  indexI5: "Selected I5 Index",
  availableProtocols: "Available Protocols",
  executesLabProtocol: "Protocol",
  instrument: "Instrument",
  hasInstrument: "Instrument",
  hasLane: "Lane",
  poolSize: "Pool Size",
  member: "Members",
  sequencedOn: "Sequenced On",
  object: "Input",
  result: "Output",
  dataFiles: "Data",
  processSequence: "Processes"
};

// PropertyValue grouping by source Django model
export const RO_CRATE_MODEL_SECTION_RULES = [
  {
    modelName: "Library",
    prefixes: ["library_db_"]
  },
  {
    modelName: "Sample",
    prefixes: ["sample_db_"]
  },
  {
    modelName: "LibraryPreparation",
    prefixes: ["library_preparation_"]
  },
  {
    modelName: "Pooling",
    prefixes: ["pooling_"]
  },
  {
    modelName: "Request",
    prefixes: ["request_"]
  },
  {
    modelName: "Flowcell",
    prefixes: ["flowcell_"]
  },
  {
    modelName: "Lane",
    prefixes: ["lane_"]
  },
  {
    modelName: "Sequencer",
    prefixes: ["sequencer_"]
  },
  {
    modelName: "IndexPool",
    prefixes: ["index_pool_"]
  },
  {
    modelName: "PoolSize",
    prefixes: ["index_pool_size_"]
  },
  {
    modelName: "Organism",
    prefixes: ["organism_"]
  },
  {
    modelName: "LibraryType",
    prefixes: ["library_type_"]
  },
  {
    modelName: "ReadLength",
    prefixes: ["read_length_"]
  },
  {
    modelName: "IndexType",
    prefixes: ["index_type_"]
  },
  {
    modelName: "NucleicAcidType",
    prefixes: ["nucleic_acid_type_"]
  },
  {
    modelName: "LibraryProtocol",
    prefixes: ["protocol_"]
  },
  {
    modelName: "IndexI7",
    prefixes: ["index_i7_"]
  },
  {
    modelName: "IndexI5",
    prefixes: ["index_i5_"]
  },
  {
    modelName: "IndexPair",
    prefixes: ["index_pair_"]
  },
  {
    modelName: "CompleteLibraryData",
    prefixes: ["library_mv_", "library_export_"],
    summaryOnly: true
  },
  {
    modelName: "CompleteSampleData",
    prefixes: ["sample_mv_", "sample_export_"],
    summaryOnly: true
  }
];

export const RO_CRATE_PROPERTY_PREFIX_PATTERN =
  /^(sample_db_|sample_mv_|library_db_|library_mv_|library_preparation_|pooling_|index_pool_size_|index_pool_|sample_export_|library_export_|request_|flowcell_|lane_|sequencer_|organism_|library_type_|read_length_|index_type_|nucleic_acid_type_|protocol_|index_i7_|index_i5_|index_pair_)/;

export const RO_CRATE_PROPERTY_LABEL_OVERRIDES = {
  dateCreated: "Date Created",
  datePublished: "Date Published",
  request_filepaths: "External File Paths",
  request_metapaths: "External Metadata Paths",
  barcode: "Barcode",
  identifier: "Barcode"
};

// Additional sensitive field patterns
export const RO_CRATE_HIDDEN_FIELD_PATTERNS = [
  /email/i,
  /telephone/i,
  /(^|_)token($|_)/i,
  /(^|_)status($|_)/i
];

// Backlink fields worth displaying as provenance links
export const RO_CRATE_BACKLINK_PROPERTIES = [
  "object",
  "result",
  "hasPart",
  "about",
  "dataFiles",
  "processSequence"
];

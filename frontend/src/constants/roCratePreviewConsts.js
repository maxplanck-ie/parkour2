import roCratePreviewFields from "../../../shared/roCratePreviewFields.json";

// API contract
export const RO_CRATE_ENDPOINT = "/api/generate_ro_crate/";

// JSON-LD entity identifiers
export const RO_CRATE_ENTITY_IDS = {
  rootDataset: "./",
  metadataDescriptor: "ro-crate-metadata.json"
};

export const RO_CRATE_ENTITY_PREFIXES = {
  requestContext: "#request-context-",
  study: "#study-",
  libraryMaterial: "#library-material-",
  sampleMaterial: "#sample-material-"
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
  requestContext: "requestContext",
  contentUrl: "contentUrl",
  isPartOf: "isPartOf"
};

// Display labels and fallback text
export const RO_CRATE_RECORD_TYPES = {
  library: "Library",
  sample: "Sample",
  fallback: "Record"
};

// Mirrors the Libraries & Samples column order, excluding Status and S/L.
export const RO_CRATE_REQUEST_DETAIL_FIELDS =
  roCratePreviewFields.requestDetails;

export const RO_CRATE_PREPARATION_CARD_FIELDS =
  roCratePreviewFields.preparation;

export const RO_CRATE_SEQUENCING_CARD_FIELDS =
  roCratePreviewFields.sequencing;

export const RO_CRATE_PREVIEW_LABELS = {
  loadedSubtitle:
    "Inspect the selected Parkour records before exporting the final ZIP.",
  unnamedRequest: "Selected request",
  unnamedRecord: "Unnamed record",
  noRecords: "No library or sample records were identified for this request."
};

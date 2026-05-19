import roCrateHiddenFields from "../../../shared/roCrateHiddenFields.json";

export const RO_CRATE_INBUILT_HIDDEN_FIELDS = [
  "@id",
  "@type",
  "about",
  "additionalProperty",
  "additionalType",
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

// Shared with backend/library/ro_crate.py. Keep RO-Crate export field exclusions
// in shared/roCrateHiddenFields.json so preview hiding and backend export filtering stay aligned.
export const USER_DEFINED_VARIABLE_HIDDEN_FIELDS =
  roCrateHiddenFields.userDefinedVariableHiddenFields;

export const RO_CRATE_PREVIEW_FIELD_RULES = {
  entityFields: {
    id: "@id",
    type: "@type",
    name: "name",
    title: "title",
    identifier: "identifier",
    alternateName: "alternateName",
    comments: "comments",
    additionalProperty: "additionalProperty",
    value: "value",
    isPartOf: "isPartOf"
  },
  entityIds: {
    rootDataset: "./",
    metadataDescriptor: "ro-crate-metadata.json"
  },
  recordEntity: {
    idPrefixes: ["#sample-material-", "#library-material-"],
    typeFragments: ["/Sample", "/Library"],
    typeLabels: {
      library: "Library",
      sample: "Sample",
      fallback: "Record"
    }
  },
  attachmentEntity: {
    type: "MediaObject"
  },
  hiddenContextEntityFields: ["name", "comments"],
  hiddenBacklinkProperties: [
    "about",
    "subjectOf",
    "isPartOf",
    "includedInDataCatalog"
  ],
  linkedSourceFields: ["variableMeasured", "measurementMethod"],
  visibleIdFields: ["i7_id", "i5_id", "indexI7Id", "indexI5Id"],
  visibleRequestFields: ["request_filepaths", "request_metapaths"],
  hiddenSensitiveFieldPatterns: [/email/i, /telephone/i],
  hiddenLinkedRecordLabelPatterns: [
    /^assay linked by /i,
    /^data linked by /i
  ],
  requestOverview: {
    // Hide low-level ISA helper entities from preview sections. They remain in
    // the JSON-LD export; preview keeps the human-facing request/record summary.
    hiddenIdFragments: [
      "#study-",
      "#sample-assay-",
      "#library-assay-",
      "#sample-data-",
      "#library-data-",
      "source-",
      "export-action",
      "metadata-export-terms"
    ],
    hiddenTypes: ["createaction", "definedterm"],
    hiddenTypeFragments: []
  },
  commentGroups: [
    {
      title: "Record Metadata",
      patterns: [/^(sample_db_|library_db_)/]
    },
    {
      title: "Export Metadata",
      patterns: [/^(sample_mv_|library_mv_|sample_export_|library_export_)/]
    },
    {
      title: "Preparation & Pooling",
      patterns: [/^(library_preparation_|pooling_)/]
    },
    {
      title: "Request Context",
      patterns: [/^request_/]
    }
  ],
  entityPropertyGroups: [
    {
      title: "Biology & Sequencing",
      fields: [
        "derivedFrom",
        "organism",
        "nucleicAcidType",
        "libraryType",
        "readLength",
        "indexType"
      ]
    },
    {
      title: "Preparation & Pooling",
      fields: ["associatedPool"]
    }
  ],
  entityKindRules: [
    {
      title: "Request",
      idEquals: ["./"],
      idFragments: ["#study-"]
    },
    {
      title: "Process",
      idFragments: ["process"],
      types: ["CreateAction"]
    },
    {
      title: "Data",
      idFragments: ["data"]
    },
    {
      title: "Assay",
      idFragments: ["assay"],
      typeFragments: ["/Assay"]
    },
    {
      title: "Source",
      idFragments: ["source"]
    },
    {
      title: "Attachment",
      types: ["MediaObject"]
    }
  ],
  commentLabelPrefixPattern:
    /^(sample_db_|sample_mv_|library_db_|library_mv_|library_preparation_|pooling_|sample_export_|library_export_|request_)/,
  propertyLabels: {
    dateCreated: "Date Created",
    datePublished: "Date Published",
    additionalProperty: "Additional Properties",
    hasPart: "Has Part",
    conformsTo: "Conforms To",
    isPartOf: "Is Part Of"
  },
  recordOverviewRows: {
    section: "Overview",
    nameLabel: "Name",
    barcodeLabel: "Barcode",
    recordTypeLabel: "Record Type"
  },
  linkedRecordsSection: "Linked Processes & Data",
  sectionOptions: {
    requestAttachments: "Request Attachments",
    defaultCommentGroup: "Linked Processes & Data",
    defaultEntityPropertyGroup: "Overview",
    unnamedGroup: "Unnamed Group",
    relatedEntityKind: "Related"
  }
};

import JSZip from "jszip";

const METADATA_FILE_NAME = "ro-crate-metadata.json";
const ROOT_DATASET_ID = "./";

function toArray(value) {
  if (Array.isArray(value)) return value;
  if (value === undefined || value === null) return [];
  return [value];
}

function isPlainObject(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function normalizeTypes(value) {
  return toArray(value)
    .map((entry) => String(entry || "").trim())
    .filter(Boolean);
}

function entityDescription(entity) {
  if (!entity) return "";
  const descriptionValue = entity.description;
  if (Array.isArray(descriptionValue)) {
    return descriptionValue.find((entry) => typeof entry === "string") || "";
  }
  return typeof descriptionValue === "string" ? descriptionValue : "";
}

function extractReferenceIds(value, collected = new Set()) {
  if (Array.isArray(value)) {
    value.forEach((item) => extractReferenceIds(item, collected));
    return collected;
  }

  if (!isPlainObject(value)) {
    return collected;
  }

  if (typeof value["@id"] === "string") {
    collected.add(value["@id"]);
  }

  Object.entries(value).forEach(([key, nestedValue]) => {
    if (key === "@id") return;
    extractReferenceIds(nestedValue, collected);
  });

  return collected;
}

function formatBytes(size) {
  if (!Number.isFinite(size) || size <= 0) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  let value = size;
  let unitIndex = 0;
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024;
    unitIndex += 1;
  }
  const digits = unitIndex === 0 ? 0 : value >= 10 ? 1 : 2;
  return `${value.toFixed(digits)} ${units[unitIndex]}`;
}

function inferMimeType(name = "") {
  const lower = String(name).toLowerCase();
  if (lower.endsWith(".json") || lower.endsWith(".jsonld")) {
    return "application/json";
  }
  if (lower.endsWith(".md")) return "text/markdown";
  if (lower.endsWith(".txt") || lower.endsWith(".tsv") || lower.endsWith(".csv")) {
    return "text/plain";
  }
  if (lower.endsWith(".html") || lower.endsWith(".htm")) return "text/html";
  if (lower.endsWith(".png")) return "image/png";
  if (lower.endsWith(".jpg") || lower.endsWith(".jpeg")) return "image/jpeg";
  if (lower.endsWith(".gif")) return "image/gif";
  if (lower.endsWith(".svg")) return "image/svg+xml";
  if (lower.endsWith(".pdf")) return "application/pdf";
  return "application/octet-stream";
}

function isDataEntity(entity) {
  const entityId = String(entity?.["@id"] || "");
  if (!entityId || entityId === ROOT_DATASET_ID || entityId === METADATA_FILE_NAME) {
    return false;
  }

  const types = normalizeTypes(entity?.["@type"]);
  return (
    types.includes("File") ||
    types.includes("MediaObject") ||
    (types.includes("Dataset") && !entityId.startsWith("#")) ||
    (!entityId.startsWith("#") && !/^https?:/i.test(entityId))
  );
}

function getCategoryKey(entity) {
  const types = normalizeTypes(entity?.["@type"]);
  const entityId = String(entity?.["@id"] || "");
  const typeSet = new Set(types);

  if (entityId === ROOT_DATASET_ID || entityId === METADATA_FILE_NAME) {
    return "overview";
  }
  if (
    typeSet.has("Study") ||
    typeSet.has("Investigation") ||
    typeSet.has("Project")
  ) {
    return "investigation";
  }
  if (
    typeSet.has("Sample") ||
    typeSet.has("Material") ||
    entityId.includes("sample") ||
    entityId.includes("library")
  ) {
    return "materials";
  }
  if (
    typeSet.has("CreateAction") ||
    typeSet.has("Action") ||
    typeSet.has("HowTo") ||
    entityId.includes("process") ||
    entityId.includes("protocol")
  ) {
    return "workflow";
  }
  if (typeSet.has("Person") || typeSet.has("Organization")) {
    return "people";
  }
  if (isDataEntity(entity)) {
    return "data";
  }
  return "context";
}

function buildSections(graph, archiveFiles) {
  const sections = {
    overview: {
      id: "overview",
      label: "Overview",
      description: "The root crate, metadata descriptor, and main profile information.",
      entityIds: []
    },
    investigation: {
      id: "investigation",
      label: "Investigation",
      description: "Investigation and study objects that organize the ISA RO-Crate.",
      entityIds: []
    },
    materials: {
      id: "materials",
      label: "Samples & Libraries",
      description: "Biological materials, libraries, and closely related record entities.",
      entityIds: []
    },
    workflow: {
      id: "workflow",
      label: "Processes & Protocols",
      description: "Preparation, sequencing, pooling, and protocol relationships.",
      entityIds: []
    },
    people: {
      id: "people",
      label: "People & Organizations",
      description: "People, organizations, request users, and other contributors.",
      entityIds: []
    },
    data: {
      id: "data",
      label: "Files & Data",
      description: "Files, payload entries, and referenced data artifacts inside the archive.",
      entityIds: []
    },
    context: {
      id: "context",
      label: "More Context",
      description: "Everything else linked into the graph.",
      entityIds: []
    }
  };

  graph.forEach((entity) => {
    const key = getCategoryKey(entity);
    sections[key].entityIds.push(entity["@id"]);
  });

  const orderedSections = Object.values(sections).filter(
    (section) => section.entityIds.length > 0
  );

  if (archiveFiles.orphaned.length > 0) {
    orderedSections.push({
      id: "archive",
      label: "Archive Inventory",
      description: "Files found in the ZIP that are not explicit graph entities.",
      entityIds: archiveFiles.orphaned.map((file) => file.id),
      isArchiveOnly: true
    });
  }

  return orderedSections;
}

function normalizeArchiveFiles(zip) {
  const files = Object.values(zip.files)
    .filter((entry) => !entry.dir)
    .map((entry) => {
      const mimeType = inferMimeType(entry.name);
      return {
        id: entry.name,
        name: entry.name.split("/").pop() || entry.name,
        path: entry.name,
        size: entry._data?.uncompressedSize || 0,
        sizeLabel: formatBytes(entry._data?.uncompressedSize || 0),
        mimeType,
        zipEntry: entry
      };
    });

  return files.sort((left, right) => left.path.localeCompare(right.path));
}

function createEntityIndex(graph) {
  const entityMap = {};
  graph.forEach((entity) => {
    entityMap[entity["@id"]] = entity;
  });
  return entityMap;
}

function createBacklinkIndex(graph) {
  const backlinkMap = {};

  graph.forEach((entity) => {
    const sourceId = entity["@id"];
    Object.entries(entity).forEach(([propertyName, propertyValue]) => {
      if (propertyName === "@id" || propertyName === "@type") return;
      extractReferenceIds(propertyValue).forEach((targetId) => {
        if (!backlinkMap[targetId]) {
          backlinkMap[targetId] = [];
        }
        backlinkMap[targetId].push({
          sourceId,
          property: propertyName
        });
      });
    });
  });

  Object.values(backlinkMap).forEach((entries) => {
    entries.sort((left, right) => {
      if (left.property === right.property) {
        return left.sourceId.localeCompare(right.sourceId);
      }
      return left.property.localeCompare(right.property);
    });
  });

  return backlinkMap;
}

function createStats(graph, sections, archiveFiles) {
  const rootDataset = graph.find((entity) => entity["@id"] === ROOT_DATASET_ID) || null;

  return {
    description: entityDescription(rootDataset),
    entityCount: graph.length,
    sectionCount: sections.length,
    archiveFileCount: archiveFiles.files.length,
    referencedFileCount: sections.find((section) => section.id === "data")?.entityIds
      .length || 0,
    rootDatasetId: rootDataset?.["@id"] || ROOT_DATASET_ID
  };
}

export async function parseRoCrateSource(file) {
  const lowerName = String(file?.name || "").toLowerCase();

  if (lowerName.endsWith(".zip")) {
    let zip;
    try {
      zip = await JSZip.loadAsync(file);
    } catch {
      throw new Error(
        "The uploaded ZIP file could not be opened. Upload a valid RO-Crate ZIP archive."
      );
    }
    const archiveFiles = normalizeArchiveFiles(zip);
    const metadataFile =
      archiveFiles.find((entry) => entry.path === METADATA_FILE_NAME) ||
      archiveFiles.find((entry) => entry.path.endsWith(`/${METADATA_FILE_NAME}`));

    if (!metadataFile) {
      throw new Error(
        "The uploaded ZIP does not contain ro-crate-metadata.json."
      );
    }

    const metadataText = await metadataFile.zipEntry.async("string");
    let roCrate;
    try {
      roCrate = JSON.parse(metadataText);
    } catch {
      throw new Error(
        "ro-crate-metadata.json inside the ZIP is not valid JSON."
      );
    }
    return buildRoCrateModel({
      file,
      roCrate,
      archiveFiles,
      zip
    });
  }

  if (lowerName.endsWith(".json") || lowerName.endsWith(".jsonld")) {
    const metadataText = await file.text();
    let roCrate;
    try {
      roCrate = JSON.parse(metadataText);
    } catch {
      throw new Error(
        "The uploaded JSON-LD file is not valid JSON."
      );
    }
    return buildRoCrateModel({
      file,
      roCrate,
      archiveFiles: [],
      zip: null
    });
  }

  throw new Error("Upload a .zip, .json, or .jsonld RO-Crate file.");
}

function buildRoCrateModel({ file, roCrate, archiveFiles, zip }) {
  const graph = Array.isArray(roCrate?.["@graph"]) ? roCrate["@graph"] : [];
  if (graph.length === 0) {
    throw new Error("The RO-Crate metadata does not contain an @graph array.");
  }

  const entityMap = createEntityIndex(graph);
  const archiveFilesById = {};
  archiveFiles.forEach((entry) => {
    archiveFilesById[entry.id] = entry;
  });

  const graphIds = new Set(graph.map((entity) => entity["@id"]));
  const orphaned = archiveFiles
    .filter((entry) => !graphIds.has(entry.id) && entry.id !== METADATA_FILE_NAME)
    .map((entry) => ({
      ...entry,
      archiveOnly: true
    }));

  const archiveModel = {
    files: archiveFiles.map((entry) => ({ ...entry })),
    byId: archiveFilesById,
    orphaned
  };

  const sections = buildSections(graph, archiveModel);
  const backlinkMap = createBacklinkIndex(graph);

  return {
    source: {
      name: file?.name || "ro-crate-metadata.json",
      size: file?.size || 0,
      sizeLabel: formatBytes(file?.size || 0),
      uploadedAt: new Date().toISOString()
    },
    roCrate,
    graph,
    entityMap,
    backlinkMap,
    stats: createStats(graph, sections, archiveModel),
    archive: archiveModel,
    zip
  };
}

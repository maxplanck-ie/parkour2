const METADATA_FILE_NAME = "ro-crate-metadata.json";
const ROOT_DATASET_ID = "./";

function isPlainObject(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function extractReferenceIds(value, collected = new Set()) {
  if (Array.isArray(value)) {
    value.forEach((item) => extractReferenceIds(item, collected));
    return collected;
  }

  if (!isPlainObject(value)) return collected;

  if (typeof value["@id"] === "string") {
    collected.add(value["@id"]);
  }

  Object.entries(value).forEach(([key, nestedValue]) => {
    if (key !== "@id") {
      extractReferenceIds(nestedValue, collected);
    }
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

function createEntityIndex(graph) {
  return Object.fromEntries(graph.map((entity) => [entity["@id"], entity]));
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

export function parseRoCratePayload(roCrate, source = {}) {
  const graph = Array.isArray(roCrate?.["@graph"]) ? roCrate["@graph"] : [];
  if (graph.length === 0) {
    throw new Error("The RO-Crate metadata does not contain an @graph array.");
  }

  const entityMap = createEntityIndex(graph);

  return {
    source: {
      name: source.name || METADATA_FILE_NAME,
      size: source.size || 0,
      sizeLabel: formatBytes(source.size || 0),
      loadedAt: new Date().toISOString()
    },
    roCrate,
    graph,
    entityMap,
    backlinkMap: createBacklinkIndex(graph),
    stats: {
      rootDatasetId: entityMap[ROOT_DATASET_ID]?.["@id"] || ROOT_DATASET_ID
    },
    archive: {
      files: [],
      byId: {},
      orphaned: []
    }
  };
}

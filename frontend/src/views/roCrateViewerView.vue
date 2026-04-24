<template>
  <div class="rocrate-viewer-page" :class="{ 'page-drag-over': isDragOver }">
    <div class="rocrate-viewer-shell" :class="{ 'is-empty': !model && !loading && !errorMessage }">
      <section class="upload-stage" :class="{ active: isDragOver, centered: !model && !loading && !errorMessage }"
        @dragover.stop.prevent="handleDragOver" @dragenter.stop.prevent="handleDragEnter"
        @dragleave.stop.prevent="handleDragLeave" @drop.stop.prevent="handleDrop">
        <input ref="uploadInput" class="hidden-upload" type="file"
          accept=".zip,.json,.jsonld,application/zip,application/json" @change="handleFileSelection" />
        <div class="upload-content" :class="{ 'drag-hidden': isDragOver }">
          <h1 class="upload-title-main">
            <img class="upload-title-icon" src="@/assets/favicon_32x32.png" alt="" />
            <span>Parkour RO-Crate Viewer</span>
          </h1>
          <div class="upload-title">Upload RO-Crate ZIP or JSON-LD file</div>
          <div class="upload-subtitle">
            You can drag and drop the file here, or choose it manually below.
          </div>
          <div class="upload-actions">
            <div v-if="model?.source?.name" class="upload-current-file">
              {{ model.source.name }}
            </div>
            <button class="hero-button primary" type="button" @click="triggerUpload">
              <font-awesome-icon icon="fa-solid fa-cloud-arrow-up" />
              {{ model ? "Choose Another File" : "Choose File" }}
            </button>
          </div>
        </div>
        <div class="upload-watermark" :class="{ 'drag-hidden': isDragOver }" aria-hidden="true">
          <div class="upload-watermark-crop">
            <img src="@/assets/icons/ro-crate-wide.svg" alt="" />
          </div>
        </div>
        <div v-if="isDragOver" class="page-drag-drop-indicator">
          <div class="page-drag-drop-copy">
            Drop <span>RO-Crate ZIP or JSON-LD file</span> here to upload
          </div>
        </div>
      </section>

      <div v-if="loading" class="viewer-feedback loading">
        <div class="loading-spinner"></div>
        <div>Parsing archive and indexing JSON-LD graph...</div>
      </div>

      <div v-else-if="errorMessage" class="viewer-feedback error">
        <font-awesome-icon icon="fa-solid fa-circle-exclamation" />
        <span>{{ errorMessage }}</span>
      </div>

      <section v-if="model" class="viewer-workspace">
        <section class="detail-card quick-summary-card">
          <div class="table-search-inline table-search-inline-top">
            <div class="table-search-input-wrap">
              <input v-model.trim="tableSearchTerm" class="table-search-input" type="search"
                placeholder="Search by field name or value" />
              <font-awesome-icon class="table-search-icon" icon="fa-solid fa-magnifying-glass" />
            </div>
          </div>
          <div class="detail-header">
            <div>
              <div class="detail-kicker">Request Overview</div>
            </div>
          </div>
          <div class="quick-summary-table">
            <div v-for="item in summaryKeyValuePairs" :key="item.key" class="quick-summary-row">
              <div class="quick-summary-key">{{ item.key }}</div>
              <div class="quick-summary-value">
                <template v-if="Array.isArray(item.value)">
                  {{ item.value.join(", ") }}
                </template>
                <template v-else>
                  {{ item.value }}
                </template>
              </div>
            </div>
          </div>

          <section v-for="section in requestOverviewSections" :key="`request-overview-${section.title}`"
            class="record-group">
            <div class="record-group-title">{{ section.title }}</div>
            <div class="quick-summary-table record-group-table">
              <div v-for="item in section.rows" :key="`request-overview-${section.title}-${item.key}`"
                class="quick-summary-row">
                <div class="quick-summary-key">{{ item.key }}</div>
                <div class="quick-summary-value">
                  <template v-if="Array.isArray(item.value)">
                    {{ item.value.join(", ") }}
                  </template>
                  <template v-else>
                    {{ item.value }}
                  </template>
                </div>
              </div>
            </div>
          </section>
        </section>

        <section class="detail-card records-summary-card">
          <div class="detail-header">
            <div>
              <div class="detail-kicker">Libraries & Samples</div>
            </div>
          </div>

          <div v-if="requestAttachmentRows.length" class="record-table-block">
            <div class="record-table-header">
              <div class="record-table-title">Request attachments</div>
              <div class="record-table-subtitle">
                Files attached to the request and included in this RO-Crate.
              </div>
            </div>
            <div class="quick-summary-table">
              <div v-for="item in requestAttachmentRows" :key="item.key" class="quick-summary-row">
                <div class="quick-summary-key">{{ item.key }}</div>
                <div class="quick-summary-value">
                  <template v-if="Array.isArray(item.value)">
                    {{ item.value.join(", ") }}
                  </template>
                  <template v-else>
                    {{ item.value }}
                  </template>
                </div>
              </div>
            </div>
          </div>

          <div v-if="recordTables.length" class="record-table-list">
            <article v-for="record in recordTables" :key="record.id" class="record-table-block">
              <div class="record-table-header">
                <div class="record-table-title">{{ record.title }}</div>
              </div>
              <section v-for="section in record.sections" :key="`${record.id}-${section.title}`" class="record-group">
                <div class="record-group-title">{{ section.title }}</div>
                <div class="quick-summary-table record-group-table">
                  <div v-for="item in section.rows" :key="`${record.id}-${section.title}-${item.key}`"
                    class="quick-summary-row">
                    <div class="quick-summary-key">{{ item.key }}</div>
                    <div class="quick-summary-value">
                      <template v-if="Array.isArray(item.value)">
                        {{ item.value.join(", ") }}
                      </template>
                      <template v-else>
                        {{ item.value }}
                      </template>
                    </div>
                  </div>
                </div>
              </section>
            </article>
          </div>
          <div v-else class="empty-inline">
            No sample or library records were identified from the uploaded RO-Crate.
          </div>
        </section>

      </section>
    </div>
  </div>
</template>

<script>
import { parseRoCrateSource } from "../utilities/roCrateViewer";
import { showNotification } from "../utilities/utilityFunctions";

export default {
  name: "ROCrateViewerView",
  data() {
    return {
      loading: false,
      errorMessage: "",
      model: null,
      tableSearchTerm: "",
      isDragOver: false,
      dragDepth: 0
    };
  },
  computed: {
    rootEntity() {
      if (!this.model) return null;
      return this.model.entityMap?.[this.model.stats.rootDatasetId] || null;
    },
    summaryKeyValuePairs() {
      if (!this.model) return [];

      const root = this.rootEntity || {};
      const shouldHideSummaryLabel = (label) => {
        const normalizedLabel = String(label || "").trim();
        const lowerLabel = normalizedLabel.toLowerCase();
        if (!normalizedLabel) return true;
        if (
          (/\bids?$/i.test(normalizedLabel) || /(^| )id$/i.test(normalizedLabel)) &&
          !/^i7 id$/i.test(normalizedLabel) &&
          !/^i5 id$/i.test(normalizedLabel)
        ) {
          return true;
        }
        if (/email/i.test(normalizedLabel) || /telephone/i.test(normalizedLabel)) {
          return true;
        }
        if (
          [
            "status",
            "is converted",
            "is pooled",
            "user is pi",
            "user is staff",
            "requested sections",
            "create time",
            "update time",
            "token",
            "user",
            "cost unit",
            "samples submitted",
            "sequenced"
          ].includes(lowerLabel)
        ) {
          return true;
        }
        return false;
      };
      const directRows = Object.entries(root)
        .filter(([key]) => !this.isHiddenSimpleTableKey(key))
        .map(([key, value]) => ({
          key: this.formatPropertyLabel(key),
          value: this.formatSummaryValue(value)
        }))
        .filter((row) => !shouldHideSummaryLabel(row.key))
        .filter((item) => {
          if (Array.isArray(item.value)) {
            return item.value.length > 0;
          }
          return item.value !== "" && item.value !== null && item.value !== undefined;
        })
        .filter((row) => this.rowMatchesSearch(row));

      const seen = new Set();
      const mergedRows = [...directRows, ...this.extractCommentRows(root)
        .map((row) => ({
          key: row.key,
          value: this.formatSummaryValue(row.value)
        }))
        .filter((row) => {
          if (!this.rowMatchesSearch(row)) return false;
          return !shouldHideSummaryLabel(row.key);
        })];

      return mergedRows.filter((row) => {
        const dedupeKey = `${row.key}:${JSON.stringify(row.value)}`;
        if (seen.has(dedupeKey)) return false;
        seen.add(dedupeKey);
        return true;
      });
    },
    requestAttachmentRows() {
      if (!this.model) return [];
      return this.model.graph
        .filter((entity) => this.isAttachmentEntity(entity))
        .map((entity, index) => {
          const fileEntry = this.model.archive?.byId?.[entity["@id"]] || null;
          return {
            key: `Attachment ${index + 1}`,
            value: [
              entity.name || entity.identifier || entity["@id"],
              fileEntry?.sizeLabel || "",
              fileEntry?.mimeType || ""
            ].filter(Boolean)
          };
        })
        .filter((row) => this.rowMatchesSearch(row));
    },
    requestOverviewSections() {
      if (!this.model) return [];
      return this.buildRequestOverviewSections();
    },
    recordTables() {
      if (!this.model) return [];
      return this.model.graph
        .filter((entity) => this.isRecordEntity(entity))
        .sort((left, right) =>
          this.entityLabelById(left["@id"]).localeCompare(
            this.entityLabelById(right["@id"])
          )
        )
        .map((entity, index) => {
          const kind = this.recordKindLabel(entity);
          return {
            id: entity["@id"],
            title: `${kind} ${index + 1}: ${entity.name || entity.identifier || entity["@id"]
              }`,
            sections: this.buildRecordSections(entity)
              .map((section) => ({
                ...section,
                rows: section.rows.filter((row) => this.rowMatchesSearch(row))
              }))
              .filter((section) => section.rows.length > 0)
          };
        })
        .filter((record) => record.sections.length > 0);
    }
  },
  beforeUnmount() {
    window.removeEventListener("dragenter", this.handleWindowDragEnter);
    window.removeEventListener("dragover", this.handleWindowDragOver);
    window.removeEventListener("dragleave", this.handleWindowDragLeave);
    window.removeEventListener("drop", this.handleWindowDrop);
  },
  mounted() {
    window.addEventListener("dragenter", this.handleWindowDragEnter);
    window.addEventListener("dragover", this.handleWindowDragOver);
    window.addEventListener("dragleave", this.handleWindowDragLeave);
    window.addEventListener("drop", this.handleWindowDrop);
  },
  methods: {
    isHiddenSimpleTableKey(key) {
      const normalizedKey = String(key || "");
      if (
        /^request_/.test(normalizedKey) &&
        !["request_filepaths", "request_metapaths"].includes(normalizedKey)
      ) {
        return true;
      }
      if (
        /id$/i.test(normalizedKey) &&
        !["i7_id", "i5_id", "indexI7Id", "indexI5Id"].includes(normalizedKey)
      ) {
        return true;
      }
      if (normalizedKey === "@id") {
        return true;
      }
      if (/email/i.test(normalizedKey)) {
        return true;
      }
      if (/telephone/i.test(normalizedKey)) {
        return true;
      }
      if (
        normalizedKey === "status" ||
        normalizedKey === "isConverted" ||
        normalizedKey === "isPooled" ||
        normalizedKey === "userIsPi" ||
        normalizedKey === "userIsStaff"
      ) {
        return true;
      }

      return [
        "@id",
        "@type",
        "identifier",
        "additionalType",
        "additionalProperty",
        "publisher",
        "hasPart",
        "mentions",
        "requestedSections",
        "sameAs",
        "url",
        "encodingFormat",
        "contentSize",
        "about",
        "subjectOf",
        "isPartOf",
        "includedInDataCatalog"
      ].includes(normalizedKey);
    },
    validateSourceFile(file) {
      if (!file) {
        return "No file was provided.";
      }

      const name = String(file.name || "").toLowerCase();
      const acceptedExtensions = [".zip", ".json", ".jsonld"];
      const hasAcceptedExtension = acceptedExtensions.some((extension) =>
        name.endsWith(extension)
      );

      if (!hasAcceptedExtension) {
        return "Upload a valid RO-Crate ZIP, JSON, or JSON-LD file.";
      }

      if (!Number.isFinite(file.size) || file.size <= 0) {
        return "The selected file is empty.";
      }

      return "";
    },
    pickSingleFile(fileList) {
      const files = Array.from(fileList || []).filter(Boolean);
      if (!files.length) {
        return { file: null, error: "No file was provided." };
      }
      if (files.length > 1) {
        return {
          file: null,
          error: "Upload only one RO-Crate ZIP or JSON-LD file at a time."
        };
      }

      const file = files[0];
      const validationMessage = this.validateSourceFile(file);
      if (validationMessage) {
        return { file: null, error: validationMessage };
      }

      return { file, error: "" };
    },
    hasFileDrag(event) {
      const types = event?.dataTransfer?.types;
      if (!types) return false;
      return Array.from(types).includes("Files");
    },
    triggerUpload() {
      this.$refs.uploadInput?.click?.();
    },
    handleDragOver() {
      this.isDragOver = true;
    },
    handleDragEnter(event) {
      if (!this.hasFileDrag(event)) return;
      this.dragDepth += 1;
      this.isDragOver = true;
    },
    handleDragLeave(event) {
      if (!this.hasFileDrag(event)) return;
      this.dragDepth = Math.max(0, this.dragDepth - 1);
      if (
        this.dragDepth === 0 ||
        !event.currentTarget?.contains?.(event.relatedTarget)
      ) {
        this.isDragOver = false;
      }
    },
    handleDrop(event) {
      if (!this.hasFileDrag(event)) return;
      this.dragDepth = 0;
      this.isDragOver = false;
      const { file, error } = this.pickSingleFile(event.dataTransfer?.files);
      if (error) {
        this.errorMessage = error;
        this.model = null;
        showNotification(error, "warning");
        return;
      }
      if (file) {
        this.loadSource(file);
      }
    },
    handleWindowDragEnter(event) {
      if (!this.hasFileDrag(event)) return;
      event.preventDefault();
      this.dragDepth += 1;
      this.isDragOver = true;
    },
    handleWindowDragOver(event) {
      if (!this.hasFileDrag(event)) return;
      event.preventDefault();
      this.isDragOver = true;
    },
    handleWindowDragLeave(event) {
      if (!this.hasFileDrag(event)) return;
      this.dragDepth = Math.max(0, this.dragDepth - 1);
      if (this.dragDepth === 0) {
        this.isDragOver = false;
      }
    },
    handleWindowDrop(event) {
      if (!this.hasFileDrag(event)) return;
      event.preventDefault();
      this.dragDepth = 0;
      this.isDragOver = false;
      const { file, error } = this.pickSingleFile(event.dataTransfer?.files);
      if (error) {
        this.errorMessage = error;
        this.model = null;
        showNotification(error, "warning");
        return;
      }
      if (file) {
        this.loadSource(file);
      }
    },
    handleFileSelection(event) {
      const { file, error } = this.pickSingleFile(event.target.files);
      if (error) {
        this.errorMessage = error;
        this.model = null;
        showNotification(error, "warning");
      }
      if (file) {
        this.loadSource(file);
      }
      event.target.value = "";
    },
    async loadSource(file) {
      const validationMessage = this.validateSourceFile(file);
      if (validationMessage) {
        this.errorMessage = validationMessage;
        this.model = null;
        showNotification(validationMessage, "warning");
        return;
      }

      this.loading = true;
      this.errorMessage = "";

      try {
        const parsedModel = await parseRoCrateSource(file);
        this.model = parsedModel;
        showNotification("RO-Crate loaded successfully.", "success");
      } catch (error) {
        this.model = null;
        this.errorMessage =
          error?.message || "The selected file could not be read as an RO-Crate.";
      } finally {
        this.loading = false;
      }
    },
    entityLabelById(entityId) {
      const entity = this.entityById(entityId);
      return entity?.name || entity?.title || entity?.identifier || entityId;
    },
    entityById(entityId) {
      return this.model?.entityMap?.[entityId] || null;
    },
    entityTypes(entity) {
      return Array.isArray(entity?.["@type"])
        ? entity["@type"]
        : entity?.["@type"]
          ? [entity["@type"]]
          : [];
    },
    isRootEntity(entity) {
      return String(entity?.["@id"] || "") === "./";
    },
    isMetadataDescriptorEntity(entity) {
      return String(entity?.["@id"] || "") === "ro-crate-metadata.json";
    },
    isRecordEntity(entity) {
      const entityId = String(entity?.["@id"] || "");
      const types = this.entityTypes(entity);
      return (
        entityId.startsWith("#sample-material-") ||
        entityId.startsWith("#library-material-") ||
        types.some((type) => String(type).includes("/Sample")) ||
        types.some((type) => String(type).includes("/Library"))
      );
    },
    isAttachmentEntity(entity) {
      return (
        this.entityTypes(entity).includes("MediaObject") &&
        entity?.isPartOf?.["@id"] === "./" &&
        entity?.["@id"] !== "ro-crate-metadata.json"
      );
    },
    isRequestOverviewEntity(entity) {
      if (!entity) return false;
      if (this.isRootEntity(entity)) return false;
      if (this.isMetadataDescriptorEntity(entity)) return false;
      if (this.isRecordEntity(entity)) return false;
      if (this.isAttachmentEntity(entity)) return false;
      if (this.shouldHideRequestOverviewEntity(entity)) return false;
      return true;
    },
    shouldHideRequestOverviewEntity(entity) {
      const id = String(entity?.["@id"] || "").toLowerCase();
      const name = String(entity?.name || "").toLowerCase();
      const types = this.entityTypes(entity).map((type) => String(type).toLowerCase());

      if (
        id.includes("#study-") ||
        id.includes("read-length") ||
        id.includes("source-") ||
        id.includes("sample-assay-") ||
        id.includes("export-action") ||
        id.includes("metadata-export-terms")
      ) {
        return true;
      }

      if (
        name.includes("parkour metadata export terms") ||
        name.includes("parkour ro-crate export generation") ||
        name.includes("sample metadata capture") ||
        name.includes("sample export metadata") ||
        name.startsWith("study for ") ||
        name.startsWith("source for ") ||
        name.includes("read length")
      ) {
        return true;
      }

      if (
        types.includes("createaction") ||
        types.some((type) => type.includes("/assay")) ||
        types.includes("definedterm")
      ) {
        return true;
      }

      return false;
    },
    recordKindLabel(entity) {
      const types = this.entityTypes(entity).map((type) => String(type));
      if (types.some((type) => type.includes("/Library"))) return "Library";
      if (types.some((type) => type.includes("/Sample"))) return "Sample";
      return "Record";
    },
    formatPropertyLabel(key) {
      const customLabels = {
        dateCreated: "Date Created",
        datePublished: "Date Published",
        additionalProperty: "Additional Properties",
        hasPart: "Has Part",
        conformsTo: "Conforms To",
        isPartOf: "Is Part Of"
      };
      if (customLabels[key]) return customLabels[key];
      return String(key)
        .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
        .replace(/[_-]+/g, " ")
        .replace(/\s+/g, " ")
        .trim()
        .replace(/\b\w/g, (char) => char.toUpperCase());
    },
    formatSummaryValue(value) {
      if (value === null || value === undefined || value === "") {
        return "-";
      }

      if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
        if (typeof value === "string") {
          const formattedDate = this.formatDisplayDate(value);
          if (formattedDate) {
            return formattedDate;
          }
        }
        return String(value);
      }

      if (Array.isArray(value)) {
        return value
          .map((entry) => this.formatSummaryValue(entry))
          .flat()
          .filter((entry) => entry !== "-");
      }

      if (value?.["@id"]) {
        return this.entityLabelById(value["@id"]);
      }

      if (value?.name && typeof value.name === "string") {
        return value.name;
      }

      if (typeof value === "object") {
        return JSON.stringify(value);
      }

      return String(value);
    },
    formatDisplayDate(value) {
      const text = String(value || "").trim();
      if (!text) return "";

      const looksLikeIsoDate =
        /^\d{4}-\d{2}-\d{2}$/.test(text) ||
        /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/.test(text);

      if (!looksLikeIsoDate) {
        return "";
      }

      const date = new Date(text);
      if (Number.isNaN(date.getTime())) {
        return "";
      }

      const separator = this.systemDateSeparator(date);
      const day = String(date.getDate()).padStart(2, "0");
      const month = String(date.getMonth() + 1).padStart(2, "0");
      const year = String(date.getFullYear());
      return `${day}${separator}${month}${separator}${year}`;
    },
    systemDateSeparator(date = new Date()) {
      const formatter = new Intl.DateTimeFormat(undefined, {
        day: "2-digit",
        month: "2-digit",
        year: "numeric"
      });
      const parts = formatter.formatToParts(date);
      return (
        parts.find(
          (part, index) =>
            part.type === "literal" &&
            index > 0 &&
            parts[index - 1]?.type === "day"
        )?.value || "/"
      );
    },
    buildRequestOverviewSections() {
      const sections = [];
      const groupedEntities = {};
      const overviewEntities = this.model.graph.filter((entity) =>
        this.isRequestOverviewEntity(entity)
      );

      overviewEntities.forEach((entity) => {
        const title = this.requestEntityGroupName(entity);
        if (!groupedEntities[title]) {
          groupedEntities[title] = [];
        }
        groupedEntities[title].push(entity);
      });

      Object.entries(groupedEntities).forEach(([title, entities]) => {
        const seen = new Set();
        const rows = entities
          .flatMap((entity) => this.buildContextEntityRows(entity))
          .filter((row) => {
            const dedupeKey = `${row.key}:${JSON.stringify(row.value)}`;
            if (seen.has(dedupeKey)) return false;
            seen.add(dedupeKey);
            return true;
          })
          .filter((row) => this.rowMatchesSearch(row));
        if (rows.length) {
          sections.push({ title, rows });
        }
      });

      if (this.requestAttachmentRows.length) {
        sections.push({
          title: "Request Attachments",
          rows: this.requestAttachmentRows
        });
      }

      return sections;
    },
    buildContextEntityRows(entity) {
      const rows = [];
      const seen = new Set();
      const addRow = (key, value) => {
        const formattedValue = this.formatSummaryValue(value);
        const normalizedKey = String(key || "").trim();
        const lowerKey = normalizedKey.toLowerCase();
        if (!normalizedKey) return;
        if (
          (/\bids?$/i.test(normalizedKey) || /(^| )id$/i.test(normalizedKey)) &&
          !/^i7 id$/i.test(normalizedKey) &&
          !/^i5 id$/i.test(normalizedKey)
        ) {
          return;
        }
        if (/email/i.test(normalizedKey)) return;
        if (/telephone/i.test(normalizedKey)) return;
        if (
          /^status$/i.test(normalizedKey) ||
          /^is converted$/i.test(normalizedKey) ||
          /^is pooled$/i.test(normalizedKey) ||
          /^user is pi$/i.test(normalizedKey) ||
          /^user is staff$/i.test(normalizedKey)
        ) {
          return;
        }
        if (
          [
            "requested sections",
            "create time",
            "update time",
            "token",
            "user",
            "cost unit",
            "samples submitted",
            "sequenced"
          ].includes(lowerKey)
        ) {
          return;
        }
        if (
          formattedValue === "-" ||
          formattedValue === "" ||
          formattedValue === null ||
          formattedValue === undefined ||
          (Array.isArray(formattedValue) && formattedValue.length === 0)
        ) {
          return;
        }
        const dedupeKey = `${normalizedKey}:${JSON.stringify(formattedValue)}`;
        if (seen.has(dedupeKey)) return;
        seen.add(dedupeKey);
        rows.push({ key: normalizedKey, value: formattedValue });
      };

      Object.entries(entity)
        .filter(([key]) => !["name", "comments"].includes(key))
        .filter(([key]) => !this.isHiddenSimpleTableKey(key))
        .forEach(([key, value]) => {
          addRow(this.formatPropertyLabel(key), value);
        });

      this.extractCommentRows(entity).forEach((row) => addRow(row.key, row.value));

      return rows;
    },
    buildRecordSections(entity) {
      const sections = [];
      const sectionMap = {};
      const seen = new Set();
      const addRow = (sectionTitle, key, value) => {
        const formattedValue = this.formatSummaryValue(value);
        const normalizedKey = String(key || "").trim();
        const lowerKey = normalizedKey.toLowerCase();
        if (!normalizedKey) return;
        if (
          (/\bids?$/i.test(normalizedKey) || /(^| )id$/i.test(normalizedKey)) &&
          !/^i7 id$/i.test(normalizedKey) &&
          !/^i5 id$/i.test(normalizedKey)
        ) {
          return;
        }
        if (/email/i.test(normalizedKey)) return;
        if (/telephone/i.test(normalizedKey)) return;
        if (
          /^status$/i.test(normalizedKey) ||
          /^is converted$/i.test(normalizedKey) ||
          /^is pooled$/i.test(normalizedKey) ||
          /^user is pi$/i.test(normalizedKey) ||
          /^user is staff$/i.test(normalizedKey) ||
          /^record type$/i.test(normalizedKey)
        ) {
          return;
        }
        if (
          [
            "requested sections",
            "create time",
            "update time",
            "token",
            "user",
            "cost unit",
            "samples submitted",
            "sequenced"
          ].includes(lowerKey)
        ) {
          return;
        }
        if (
          /^#sample-assay-/i.test(normalizedKey) ||
          /^related index /i.test(normalizedKey) ||
          /^related linked /i.test(normalizedKey) ||
          /^process linked by /i.test(normalizedKey) ||
          /^assay linked by /i.test(normalizedKey)
        ) {
          return;
        }
        if (
          formattedValue === "-" ||
          formattedValue === "" ||
          formattedValue === null ||
          formattedValue === undefined ||
          (Array.isArray(formattedValue) && formattedValue.length === 0)
        ) {
          return;
        }
        const dedupeKey = `${sectionTitle}:${normalizedKey}:${JSON.stringify(
          formattedValue
        )}`;
        if (seen.has(dedupeKey)) return;
        seen.add(dedupeKey);
        if (!sectionMap[sectionTitle]) {
          sectionMap[sectionTitle] = {
            title: sectionTitle,
            rows: []
          };
          sections.push(sectionMap[sectionTitle]);
        }
        sectionMap[sectionTitle].rows.push({
          key: normalizedKey,
          value: formattedValue
        });
      };

      addRow("Overview", "Name", entity.name || "-");
      addRow("Overview", "Barcode", entity.identifier || "-");
      addRow("Overview", "Record Type", this.recordKindLabel(entity));

      Object.entries(entity)
        .filter(([key]) => !["name", "comments"].includes(key))
        .filter(([key]) => !this.isHiddenSimpleTableKey(key))
        .forEach(([key, value]) => {
          const sectionTitle = this.groupEntityProperty(key);
          addRow(sectionTitle, this.formatPropertyLabel(key), value);
        });

      this.extractCommentRows(entity).forEach((row) =>
        addRow(row.group, row.key, row.value)
      );

      const incomingLinks = this.model?.backlinkMap?.[entity["@id"]] || [];
      incomingLinks.forEach((link) => {
        const sourceEntity = this.entityById(link.sourceId);
        if (!sourceEntity) return;
        if (["about", "subjectOf", "isPartOf", "includedInDataCatalog"].includes(link.property)) {
          return;
        }
        const sourceName = sourceEntity.name || link.sourceId;
        const propertyLabel = this.formatPropertyLabel(link.property);
        const sourceKind = this.simplifyEntityKind(sourceEntity);
        if (sourceKind === "Request") {
          return;
        }
        const linkedGroup = "Linked Processes & Data";
        addRow(linkedGroup, `${sourceKind} linked by ${propertyLabel}`, sourceName);

        ["variableMeasured", "measurementMethod"].forEach((key) => {
          if (sourceEntity[key] !== undefined && sourceEntity[key] !== null) {
            addRow(
              linkedGroup,
              `${sourceName} ${this.formatPropertyLabel(key)}`,
              sourceEntity[key]
            );
          }
        });

        this.extractCommentRows(sourceEntity).forEach((row) =>
          addRow(
            linkedGroup,
            `${sourceKind} ${row.key}`,
            row.value
          )
        );
      });

      return sections.filter((section) => section.rows.length > 0);
    },
    rowMatchesSearch(row) {
      const query = String(this.tableSearchTerm || "").trim().toLowerCase();
      if (!query) return true;

      const keyText = String(row?.key || "").toLowerCase();
      const valueText = this.searchableValueText(row?.value);
      return keyText.includes(query) || valueText.includes(query);
    },
    searchableValueText(value) {
      if (value === null || value === undefined) return "";
      if (Array.isArray(value)) {
        return value
          .map((entry) => this.searchableValueText(entry))
          .join(" ")
          .toLowerCase();
      }
      if (typeof value === "object") {
        return JSON.stringify(value).toLowerCase();
      }
      return String(value).toLowerCase();
    },
    extractCommentRows(entity) {
      const rows = [];
      const comments = Array.isArray(entity?.comments) ? entity.comments : [];
      comments.forEach((comment) => {
        if (!comment?.name) return;
        rows.push({
          group: this.commentGroup(comment.name),
          key: this.simplifyCommentLabel(comment.name),
          value: comment.value
        });
      });

      const additionalProperties = Array.isArray(entity?.additionalProperty)
        ? entity.additionalProperty
        : [];
      additionalProperties.forEach((property) => {
        if (!property?.name) return;
        rows.push({
          group: this.commentGroup(property.name),
          key: this.simplifyCommentLabel(property.name),
          value: property.value
        });
      });

      return rows;
    },
    simplifyCommentLabel(label) {
      return this.formatPropertyLabel(
        String(label).replace(
          /^(sample_db_|sample_mv_|library_db_|library_mv_|library_preparation_|pooling_|sample_export_|library_export_|request_)/,
          ""
        )
      );
    },
    commentGroup(label) {
      const value = String(label || "");
      if (/^(sample_db_|library_db_)/.test(value)) return "Record Metadata";
      if (/^(sample_mv_|library_mv_|sample_export_|library_export_)/.test(value)) {
        return "Export Metadata";
      }
      if (/^(library_preparation_|pooling_)/.test(value)) {
        return "Preparation & Pooling";
      }
      if (/^request_/.test(value)) return "Request Context";
      return "Linked Processes & Data";
    },
    groupEntityProperty(key) {
      const value = String(key || "");
      if (
        [
          "derivedFrom",
          "organism",
          "nucleicAcidType",
          "libraryType",
          "readLength",
          "indexType"
        ].includes(value)
      ) {
        return "Biology & Sequencing";
      }
      if (["associatedPool"].includes(value)) return "Preparation & Pooling";
      return "Overview";
    },
    contextEntityGroup(entity) {
      const id = String(entity?.["@id"] || "");
      const types = this.entityTypes(entity).map((type) => String(type));

      if (id.includes("protocol") || id.includes("type") || id.includes("organism")) {
        return "Protocols, Types & Terms";
      }
      if (
        id.includes("pool") ||
        id.includes("flowcell") ||
        id.includes("lane") ||
        id.includes("sequencer")
      ) {
        return "Pooling, Flowcells & Instruments";
      }
      if (
        types.includes("Person") ||
        types.includes("Organization") ||
        id.includes("person") ||
        id.includes("organization") ||
        id.includes("cost-unit")
      ) {
        return "People, Organizations & Request Roles";
      }
      if (
        id.includes("process") ||
        id.includes("data") ||
        id.includes("assay") ||
        id.includes("export-action") ||
        types.includes("CreateAction")
      ) {
        return "Processes, Assays & Export Data";
      }
      return "Other Request Metadata";
    },
    requestEntityGroupName(entity) {
      return (
        entity?.name ||
        entity?.title ||
        entity?.identifier ||
        entity?.alternateName ||
        entity?.["@id"] ||
        "Unnamed Group"
      );
    },
    simplifyEntityKind(entity) {
      if (!entity) return "Related";
      const id = String(entity["@id"] || "");
      if (id === "./" || id.includes("#study-")) return "Request";
      if (id.includes("process")) return "Process";
      if (id.includes("data")) return "Data";
      if (id.includes("assay")) return "Assay";
      if (id.includes("source")) return "Source";
      if (this.entityTypes(entity).includes("MediaObject")) return "Attachment";
      if (this.entityTypes(entity).includes("CreateAction")) return "Process";
      if (this.entityTypes(entity).some((type) => String(type).includes("/Assay"))) {
        return "Assay";
      }
      return "Related";
    }
  }
};
</script>

<style scoped>
.rocrate-viewer-page {
  min-height: 100vh;
  background:
    radial-gradient(circle at top left, rgba(15, 95, 135, 0.18), transparent 32%),
    radial-gradient(circle at top right, rgba(43, 167, 123, 0.18), transparent 28%),
    linear-gradient(180deg, #f4fafb 0%, #ecf3f5 50%, #f8fcfd 100%);
  color: #10242f;
}

.rocrate-viewer-page.page-drag-over {
  background-color: transparent;
}

.rocrate-viewer-shell {
  max-width: 1520px;
  margin: 0 auto;
  padding: 32px 24px 56px;
}

.rocrate-viewer-shell.is-empty {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

.upload-stage,
.detail-card {
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(16, 36, 47, 0.08);
  box-shadow: 0 20px 40px rgba(26, 58, 74, 0.08);
  backdrop-filter: blur(12px);
}

.upload-actions,
.reference-pill-list {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.hero-button {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  border-radius: 14px;
  border: 0;
  padding: 12px 16px;
  font-size: 14px;
  font-weight: 700;
  text-decoration: none;
  cursor: pointer;
  transition:
    transform 0.18s ease,
    box-shadow 0.18s ease,
    background-color 0.18s ease;
}

.hero-button:hover {
  transform: translateY(-1px);
}

.hero-button.primary {
  background: linear-gradient(135deg, #0d6f73, #1b9c7c);
  color: #fff;
}

.upload-stage {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 180px;
  gap: 12px;
  align-items: center;
  border-radius: 24px;
  padding: 20px 24px;
  margin-bottom: 20px;
  transition:
    transform 0.2s ease,
    border-color 0.2s ease,
    background-color 0.2s ease;
}

.upload-stage.centered {
  width: min(920px, 100%);
  min-height: 236px;
  margin: 0 auto;
}

.upload-content {
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-height: 168px;
}

.upload-stage.active {
  transform: none;
  border-color: transparent;
  background: transparent;
}

.page-drag-drop-indicator {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(255, 255, 255, 0.94);
  padding: 36px;
  border-radius: 24px;
  border: 2px dashed #2196f3;
  text-align: center;
  box-sizing: border-box;
  z-index: 2;
  box-shadow: 0 20px 44px rgba(0, 0, 0, 0.12);
  pointer-events: none;
  animation: dragOverlayGrow 0.2s ease-out;
}

.page-drag-drop-copy {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 140px;
  color: #173948;
  font-size: 24px;
  line-height: 1.5;
}

.page-drag-drop-copy span {
  margin: 0 6px;
  font-weight: 800;
}

@keyframes dragOverlayGrow {
  from {
    opacity: 0;
    transform: scale(0.96);
  }

  to {
    opacity: 1;
    transform: scale(1);
  }
}

.drag-hidden {
  opacity: 0;
  pointer-events: none;
}

.upload-title {
  font-size: 24px;
  font-weight: 800;
  letter-spacing: -0.03em;
  line-height: 1.16;
}

.upload-title-main {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0 0 12px;
  color: #0f2a38;
  font-size: clamp(1.5rem, 3vw, 2.2rem);
  font-weight: 800;
  letter-spacing: -0.04em;
  text-align: left;
}

.upload-title-icon {
  width: 30px;
  height: 30px;
  flex-shrink: 0;
}

.upload-subtitle {
  margin-top: 10px;
  color: #4d6671;
  line-height: 1.5;
  max-width: 620px;
}

.upload-actions {
  margin-top: 14px;
  align-items: center;
  gap: 14px;
}

.upload-current-file {
  max-width: min(520px, 100%);
  padding: 11px 14px;
  border-radius: 14px;
  background: rgba(228, 240, 243, 0.9);
  color: #214250;
  font-size: 14px;
  font-weight: 600;
  line-height: 1.4;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.upload-watermark {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 168px;
  pointer-events: none;
}

.upload-watermark-crop {
  width: 170px;
  height: 170px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: flex-start;
}

.upload-watermark img {
  width: 410px;
  height: auto;
  opacity: 0.12;
  filter: saturate(0.78);
  transform: translateX(0);
  transform-origin: left center;
}

.hidden-upload {
  display: none;
}

.viewer-feedback {
  display: flex;
  align-items: center;
  gap: 12px;
  border-radius: 18px;
  padding: 16px 18px;
  margin-bottom: 24px;
  font-weight: 700;
}

.viewer-feedback.loading {
  background: rgba(243, 249, 250, 0.9);
}

.viewer-feedback.error {
  background: rgba(255, 240, 240, 0.96);
  color: #7c2020;
}

.loading-spinner {
  width: 20px;
  height: 20px;
  border: 3px solid rgba(13, 111, 115, 0.14);
  border-top-color: #0d6f73;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.detail-kicker {
  display: inline-block;
  margin-bottom: 8px;
  font-size: 18px;
  font-weight: 800;
  letter-spacing: -0.02em;
  text-transform: none;
  color: #173948;
}

.quick-summary-card {
  margin-bottom: 18px;
}

.records-summary-card {
  margin-bottom: 18px;
}

.section-title {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  letter-spacing: -0.03em;
  color: #173948;
}

.table-search-inline {
  margin-top: 14px;
}

.table-search-inline-top {
  margin-top: 0;
  margin-bottom: 14px;
}

.table-search-input-wrap {
  position: relative;
}

.table-search-input {
  width: 100%;
  border: 1px solid rgba(16, 36, 47, 0.12);
  border-radius: 14px;
  padding: 12px 44px 12px 14px;
  font-size: 15px;
  color: #173948;
  background: rgba(255, 255, 255, 0.96);
}

.table-search-input::placeholder {
  color: #6a8591;
}

.table-search-icon {
  position: absolute;
  top: 50%;
  right: 14px;
  transform: translateY(-50%);
  color: #6a8591;
  pointer-events: none;
}

.record-table-list {
  display: flex;
  flex-direction: column;
  gap: 18px;
  margin-top: 18px;
}

.record-table-block {
  margin-top: 18px;
  padding-top: 18px;
  border-top: 1px solid rgba(16, 36, 47, 0.08);
}

.record-table-block:first-of-type {
  margin-top: 0;
  padding-top: 0;
  border-top: 0;
}

.record-table-header {
  margin-bottom: 12px;
}

.record-table-title {
  font-size: 18px;
  font-weight: 800;
  color: #173948;
}

.record-table-subtitle {
  margin-top: 4px;
  color: #5c7784;
  word-break: break-word;
}

.record-group {
  margin-top: 16px;
}

.record-group:first-of-type {
  margin-top: 0;
}

.quick-summary-card>.record-group:first-of-type {
  margin-top: 22px;
}

.record-group-title {
  margin-bottom: 8px;
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #1d5f78;
}

.record-group-table {
  margin-top: 0;
}

.quick-summary-table {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px 18px;
  margin-top: 14px;
}

.quick-summary-row {
  display: grid;
  grid-template-columns: 120px minmax(0, 1fr);
  gap: 12px;
  align-items: start;
  padding: 14px 16px;
  border-radius: 16px;
  background: linear-gradient(180deg, rgba(248, 251, 252, 0.96), rgba(255, 255, 255, 0.96));
  border: 1px solid rgba(16, 36, 47, 0.06);
}

.quick-summary-key {
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: #5e7884;
}

.quick-summary-value {
  color: #173948;
  line-height: 1.55;
  word-break: break-word;
}

.detail-card {
  border-radius: 22px;
  padding: 18px;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
}

.type-chip {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 8px 12px;
  background: rgba(13, 111, 115, 0.08);
  color: #0d6f73;
  font-size: 12px;
  font-weight: 800;
  cursor: default;
  pointer-events: none;
  user-select: text;
}

.empty-inline {
  color: #65818c;
  line-height: 1.6;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 1180px) {
  .quick-summary-table {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 760px) {
  .rocrate-viewer-shell {
    padding: 20px 14px 40px;
  }

  .detail-card,
  .upload-stage {
    border-radius: 20px;
    padding: 16px;
  }

  .upload-stage,
  .quick-summary-table {
    grid-template-columns: 1fr;
  }

  .upload-watermark {
    display: none;
  }

  .quick-summary-row {
    grid-template-columns: 1fr;
  }
}
</style>

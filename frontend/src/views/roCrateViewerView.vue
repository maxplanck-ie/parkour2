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
            <img class="upload-title-icon" src="@/assets/icons/parkour_32x32.png" alt="" />
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
import {
  RO_CRATE_INBUILT_HIDDEN_FIELDS,
  RO_CRATE_VIEWER_FIELD_RULES,
  USER_DEFINED_VARIABLE_HIDDEN_FIELDS
} from "../constants/roCrateViewerConsts";
import { parseRoCrateSource } from "../utilities/roCrateViewerUtils";
import { showNotification } from "../utilities/utilityFunctions";

const displayLabelForField = (field) =>
  String(field || "")
    .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
    .replace(/[_-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .toLowerCase();

const roCrateInbuiltHiddenFieldSet = new Set(RO_CRATE_INBUILT_HIDDEN_FIELDS);
const userDefinedVariableHiddenFieldSet = new Set(
  USER_DEFINED_VARIABLE_HIDDEN_FIELDS
);
const userDefinedVariableHiddenLabelSet = new Set(
  USER_DEFINED_VARIABLE_HIDDEN_FIELDS.map(displayLabelForField)
);
const visibleIdFieldSet = new Set(RO_CRATE_VIEWER_FIELD_RULES.visibleIdFields);
const visibleIdLabelSet = new Set(
  RO_CRATE_VIEWER_FIELD_RULES.visibleIdFields.map(displayLabelForField)
);
const visibleRequestFieldSet = new Set(
  RO_CRATE_VIEWER_FIELD_RULES.visibleRequestFields
);
const hiddenSensitiveFieldPatterns =
  RO_CRATE_VIEWER_FIELD_RULES.hiddenSensitiveFieldPatterns;
const hiddenLinkedRecordLabelPatterns =
  RO_CRATE_VIEWER_FIELD_RULES.hiddenLinkedRecordLabelPatterns;
const entityFields = RO_CRATE_VIEWER_FIELD_RULES.entityFields;
const entityIds = RO_CRATE_VIEWER_FIELD_RULES.entityIds;
const recordEntityRules = RO_CRATE_VIEWER_FIELD_RULES.recordEntity;
const attachmentEntityRules = RO_CRATE_VIEWER_FIELD_RULES.attachmentEntity;
const sectionOptions = RO_CRATE_VIEWER_FIELD_RULES.sectionOptions;
const hiddenContextEntityFieldSet = new Set(
  RO_CRATE_VIEWER_FIELD_RULES.hiddenContextEntityFields
);
const hiddenBacklinkPropertySet = new Set(
  RO_CRATE_VIEWER_FIELD_RULES.hiddenBacklinkProperties
);
const recordTypeLabel = displayLabelForField("recordType");

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
      const directRows = Object.entries(root)
        .filter(([key]) => !this.isHiddenSimpleTableKey(key))
        .map(([key, value]) => ({
          key: this.formatPropertyLabel(key),
          value: this.formatSummaryValue(value)
        }))
        .filter((row) => !this.shouldHideDisplayLabel(row.key))
        .filter((row) => !this.isEmptyDisplayValue(row.value))
        .filter((row) => this.rowMatchesSearch(row));

      const seen = new Set();
      const mergedRows = [...directRows, ...this.extractCommentRows(root)
        .map((row) => ({
          key: row.key,
          value: this.formatSummaryValue(row.value)
        }))
        .filter((row) => {
          if (!this.rowMatchesSearch(row)) return false;
          return !this.shouldHideDisplayLabel(row.key);
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
          const entityId = entity[entityFields.id];
          const fileEntry = this.model.archive?.byId?.[entityId] || null;
          return {
            key: `Attachment ${index + 1}`,
            value: [
              entity[entityFields.name] ||
                entity[entityFields.identifier] ||
                entityId,
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
          this.entityLabelById(left[entityFields.id]).localeCompare(
            this.entityLabelById(right[entityFields.id])
          )
        )
        .map((entity, index) => {
          const kind = this.recordKindLabel(entity);
          const entityId = entity[entityFields.id];
          return {
            id: entityId,
            title: `${kind} ${index + 1}: ${entity[entityFields.name] || entity[entityFields.identifier] || entityId
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
      return (
        (/^request_/.test(normalizedKey) &&
          !visibleRequestFieldSet.has(normalizedKey)) ||
        (/id$/i.test(normalizedKey) &&
          !visibleIdFieldSet.has(normalizedKey)) ||
        roCrateInbuiltHiddenFieldSet.has(normalizedKey) ||
        this.shouldHideSensitiveField(normalizedKey) ||
        userDefinedVariableHiddenFieldSet.has(normalizedKey)
      );
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
      return (
        entity?.[entityFields.name] ||
        entity?.[entityFields.title] ||
        entity?.[entityFields.identifier] ||
        entityId
      );
    },
    entityById(entityId) {
      return this.model?.entityMap?.[entityId] || null;
    },
    entityTypes(entity) {
      return Array.isArray(entity?.[entityFields.type])
        ? entity[entityFields.type]
        : entity?.[entityFields.type]
          ? [entity[entityFields.type]]
          : [];
    },
    isRootEntity(entity) {
      return String(entity?.[entityFields.id] || "") === entityIds.rootDataset;
    },
    isMetadataDescriptorEntity(entity) {
      return (
        String(entity?.[entityFields.id] || "") === entityIds.metadataDescriptor
      );
    },
    isRecordEntity(entity) {
      const entityId = String(entity?.[entityFields.id] || "");
      const types = this.entityTypes(entity);
      return (
        recordEntityRules.idPrefixes.some((prefix) =>
          entityId.startsWith(prefix)
        ) ||
        recordEntityRules.typeFragments.some((fragment) =>
          types.some((type) => String(type).includes(fragment))
        )
      );
    },
    isAttachmentEntity(entity) {
      return (
        this.entityTypes(entity).includes(attachmentEntityRules.type) &&
        entity?.[entityFields.isPartOf]?.[entityFields.id] ===
          entityIds.rootDataset &&
        entity?.[entityFields.id] !== entityIds.metadataDescriptor
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
      const id = String(entity?.[entityFields.id] || "").toLowerCase();
      const types = this.entityTypes(entity).map((type) => String(type).toLowerCase());
      const overviewRules = RO_CRATE_VIEWER_FIELD_RULES.requestOverview;

      if (
        overviewRules.hiddenIdFragments.some((fragment) =>
          id.includes(fragment)
        )
      ) {
        return true;
      }

      if (
        overviewRules.hiddenTypes.some((type) => types.includes(type)) ||
        overviewRules.hiddenTypeFragments.some((fragment) =>
          types.some((type) => type.includes(fragment))
        )
      ) {
        return true;
      }

      return false;
    },
    recordKindLabel(entity) {
      const types = this.entityTypes(entity).map((type) => String(type));
      if (types.some((type) => type.includes(recordEntityRules.typeFragments[1]))) {
        return recordEntityRules.typeLabels.library;
      }
      if (types.some((type) => type.includes(recordEntityRules.typeFragments[0]))) {
        return recordEntityRules.typeLabels.sample;
      }
      return recordEntityRules.typeLabels.fallback;
    },
    formatPropertyLabel(key) {
      const customLabels = RO_CRATE_VIEWER_FIELD_RULES.propertyLabels;
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

      if (value?.[entityFields.id]) {
        return this.entityLabelById(value[entityFields.id]);
      }

      if (
        value?.[entityFields.name] &&
        typeof value[entityFields.name] === "string"
      ) {
        return value[entityFields.name];
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
    shouldHideIdLabel(label) {
      const normalizedLabel = String(label || "").trim();
      const lowerLabel = normalizedLabel.toLowerCase();
      return (
        (/\bids?$/i.test(normalizedLabel) || /(^| )id$/i.test(normalizedLabel)) &&
        !visibleIdLabelSet.has(lowerLabel)
      );
    },
    shouldHideSensitiveField(field) {
      return hiddenSensitiveFieldPatterns.some((pattern) =>
        pattern.test(String(field || ""))
      );
    },
    isEmptyDisplayValue(value, options = {}) {
      return (
        value === "" ||
        value === null ||
        value === undefined ||
        (options.hideDash && value === "-") ||
        (Array.isArray(value) && value.length === 0)
      );
    },
    shouldHideDisplayLabel(label, options = {}) {
      const normalizedLabel = String(label || "").trim();
      const lowerLabel = normalizedLabel.toLowerCase();
      if (!normalizedLabel) return true;
      if (this.shouldHideIdLabel(normalizedLabel)) return true;
      if (this.shouldHideSensitiveField(normalizedLabel)) return true;
      if (userDefinedVariableHiddenLabelSet.has(lowerLabel)) return true;
      if (
        options.hideRecordLabels &&
        lowerLabel === recordTypeLabel
      ) {
        return true;
      }
      if (
        options.hideLinkedRecordLabels &&
        hiddenLinkedRecordLabelPatterns.some((pattern) =>
          pattern.test(normalizedLabel)
        )
      ) {
        return true;
      }
      return false;
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
          title: sectionOptions.requestAttachments,
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
        if (this.shouldHideDisplayLabel(normalizedKey)) return;
        if (this.isEmptyDisplayValue(formattedValue, { hideDash: true })) return;
        const dedupeKey = `${normalizedKey}:${JSON.stringify(formattedValue)}`;
        if (seen.has(dedupeKey)) return;
        seen.add(dedupeKey);
        rows.push({ key: normalizedKey, value: formattedValue });
      };

      Object.entries(entity)
        .filter(([key]) => !hiddenContextEntityFieldSet.has(key))
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
        if (
          this.shouldHideDisplayLabel(normalizedKey, {
            hideRecordLabels: true,
            hideLinkedRecordLabels: true
          })
        ) return;
        if (this.isEmptyDisplayValue(formattedValue, { hideDash: true })) return;
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

      const recordRows = RO_CRATE_VIEWER_FIELD_RULES.recordOverviewRows;
      addRow(
        recordRows.section,
        recordRows.nameLabel,
        entity[entityFields.name] || "-"
      );
      addRow(
        recordRows.section,
        recordRows.barcodeLabel,
        entity[entityFields.identifier] || "-"
      );
      addRow(
        recordRows.section,
        recordRows.recordTypeLabel,
        this.recordKindLabel(entity)
      );

      Object.entries(entity)
        .filter(([key]) => !hiddenContextEntityFieldSet.has(key))
        .filter(([key]) => !this.isHiddenSimpleTableKey(key))
        .forEach(([key, value]) => {
          const sectionTitle = this.groupEntityProperty(key);
          addRow(sectionTitle, this.formatPropertyLabel(key), value);
        });

      this.extractCommentRows(entity).forEach((row) =>
        addRow(row.group, row.key, row.value)
      );

      const incomingLinks =
        this.model?.backlinkMap?.[entity[entityFields.id]] || [];
      incomingLinks.forEach((link) => {
        const sourceEntity = this.entityById(link.sourceId);
        if (!sourceEntity) return;
        if (hiddenBacklinkPropertySet.has(link.property)) {
          return;
        }
        const sourceName = sourceEntity[entityFields.name] || link.sourceId;
        const propertyLabel = this.formatPropertyLabel(link.property);
        const sourceKind = this.simplifyEntityKind(sourceEntity);
        if (sourceKind === RO_CRATE_VIEWER_FIELD_RULES.entityKindRules[0].title) {
          return;
        }
        const linkedGroup = RO_CRATE_VIEWER_FIELD_RULES.linkedRecordsSection;
        addRow(linkedGroup, `${sourceKind} linked by ${propertyLabel}`, sourceName);

        RO_CRATE_VIEWER_FIELD_RULES.linkedSourceFields.forEach((key) => {
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
      const comments = Array.isArray(entity?.[entityFields.comments])
        ? entity[entityFields.comments]
        : [];
      comments.forEach((comment) => {
        if (!comment?.[entityFields.name]) return;
        rows.push({
          group: this.commentGroup(comment[entityFields.name]),
          key: this.simplifyCommentLabel(comment[entityFields.name]),
          value: comment[entityFields.value]
        });
      });

      const additionalProperties = Array.isArray(
        entity?.[entityFields.additionalProperty]
      )
        ? entity[entityFields.additionalProperty]
        : [];
      additionalProperties.forEach((property) => {
        if (!property?.[entityFields.name]) return;
        rows.push({
          group: this.commentGroup(property[entityFields.name]),
          key: this.simplifyCommentLabel(property[entityFields.name]),
          value: property[entityFields.value]
        });
      });

      return rows;
    },
    findRuleTitle(rules, matcher) {
      return rules.find((rule) => matcher(rule))?.title || "";
    },
    matchesEntityRule(rule, entity) {
      const id = String(entity?.[entityFields.id] || "");
      const types = this.entityTypes(entity).map((type) => String(type));
      return (
        rule.idEquals?.includes(id) ||
        rule.idFragments?.some((fragment) => id.includes(fragment)) ||
        rule.types?.some((type) => types.includes(type)) ||
        rule.typeFragments?.some((fragment) =>
          types.some((type) => type.includes(fragment))
        )
      );
    },
    simplifyCommentLabel(label) {
      return this.formatPropertyLabel(
        String(label).replace(
          RO_CRATE_VIEWER_FIELD_RULES.commentLabelPrefixPattern,
          ""
        )
      );
    },
    commentGroup(label) {
      const value = String(label || "");
      return (
        this.findRuleTitle(
          RO_CRATE_VIEWER_FIELD_RULES.commentGroups,
          (rule) => rule.patterns.some((pattern) => pattern.test(value))
        ) || sectionOptions.defaultCommentGroup
      );
    },
    groupEntityProperty(key) {
      const value = String(key || "");
      return (
        this.findRuleTitle(
          RO_CRATE_VIEWER_FIELD_RULES.entityPropertyGroups,
          (rule) => rule.fields.includes(value)
        ) || sectionOptions.defaultEntityPropertyGroup
      );
    },
    requestEntityGroupName(entity) {
      return (
        entity?.[entityFields.name] ||
        entity?.[entityFields.title] ||
        entity?.[entityFields.identifier] ||
        entity?.[entityFields.alternateName] ||
        entity?.[entityFields.id] ||
        sectionOptions.unnamedGroup
      );
    },
    simplifyEntityKind(entity) {
      return (
        this.findRuleTitle(
          RO_CRATE_VIEWER_FIELD_RULES.entityKindRules,
          (rule) => this.matchesEntityRule(rule, entity)
        ) || sectionOptions.relatedEntityKind
      );
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

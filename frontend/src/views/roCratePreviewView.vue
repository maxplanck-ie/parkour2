<template>
  <div class="rocrate-preview-page" :class="{ embedded }">
    <div class="rocrate-preview-shell" :class="{ 'is-empty': !model && !loading && !errorMessage }">
      <section class="upload-stage" :class="{ centered: !model && !loading && !errorMessage }">
        <div class="upload-content">
          <h1 class="upload-title-main">
            <img class="upload-title-icon" src="@/assets/icons/parkour_32x32.png" alt="" />
            <span>Parkour RO-Crate Preview</span>
          </h1>
          <div class="upload-title">
            {{
              activePreviewConfig
                ? "Review selected RO-Crate metadata"
                : "RO-Crate preview"
            }}
          </div>
          <div class="upload-subtitle">
            {{
              activePreviewConfig
                ? "Inspect the selected Parkour records before exporting the final ZIP."
                : "Select libraries or samples and open Preview from the RO-Crate export dialog."
            }}
          </div>
          <div class="upload-actions">
            <div v-if="model?.source?.name" class="upload-current-file">
              {{ model.source.name }}
            </div>
            <button
              v-if="model"
              class="hero-button primary rocrate-export-button"
              type="button"
              :disabled="exportBusy || !canExportPreview"
              @click="exportROCrate"
            >
              <font-awesome-icon icon="fa-solid fa-box-archive" />
              {{ exportBusy ? "Exporting..." : "Export RO-Crate" }}
            </button>
            <button v-if="model" class="hero-button secondary pdf-export-button" type="button" @click="exportToPdf">
              <font-awesome-icon icon="fa-solid fa-file-pdf" />
              Export to PDF
            </button>
          </div>
        </div>
        <div class="upload-watermark" aria-hidden="true">
          <div class="upload-watermark-crop">
            <img src="@/assets/icons/ro-crate-wide.svg" alt="" />
          </div>
        </div>
      </section>

      <div v-if="loading" class="preview-feedback loading">
        <div class="loading-spinner"></div>
        <div>Parsing archive and indexing JSON-LD graph...</div>
      </div>

      <div v-else-if="errorMessage" class="preview-feedback error">
        <font-awesome-icon icon="fa-solid fa-circle-exclamation" />
        <span>{{ errorMessage }}</span>
      </div>

      <div v-if="skippedRecords.length" class="preview-feedback warning">
        <font-awesome-icon icon="fa-solid fa-triangle-exclamation" />
        <span>
          {{ skippedRecords.length }}
          {{ skippedRecords.length === 1 ? "record was" : "records were" }}
          skipped because RO-Crate export requires Delivered status:
          {{ skippedRecords.join(", ") }}
        </span>
      </div>

      <section v-if="model" class="preview-workspace">
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
            <div v-for="item in summaryKeyValuePairs" :key="item.key" class="quick-summary-row"
              :class="{ 'wide-row': shouldUseWideRow(item) }">
              <div class="quick-summary-key">{{ item.key }}</div>
              <div class="quick-summary-value">
                <div
                  v-if="isStructuredDisplayValue(item.value)"
                  v-html="structuredValueHtml(item.value)"
                ></div>
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
                class="quick-summary-row" :class="{ 'wide-row': shouldUseWideRow(item) }">
                <div class="quick-summary-key">{{ item.key }}</div>
                <div class="quick-summary-value">
                  <div
                    v-if="isStructuredDisplayValue(item.value)"
                    v-html="structuredValueHtml(item.value)"
                  ></div>
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
              <div v-for="item in requestAttachmentRows" :key="item.key" class="quick-summary-row"
                :class="{ 'wide-row': shouldUseWideRow(item) }">
                <div class="quick-summary-key">{{ item.key }}</div>
                <div class="quick-summary-value">
                  <div
                    v-if="isStructuredDisplayValue(item.value)"
                    v-html="structuredValueHtml(item.value)"
                  ></div>
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
                    class="quick-summary-row" :class="{ 'wide-row': shouldUseWideRow(item) }">
                    <div class="quick-summary-key">{{ item.key }}</div>
                    <div class="quick-summary-value">
                      <div
                        v-if="isStructuredDisplayValue(item.value)"
                        v-html="structuredValueHtml(item.value)"
                      ></div>
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
            No sample or library records were identified from this RO-Crate.
          </div>
        </section>

      </section>
    </div>
  </div>
</template>

<script>
import {
  RO_CRATE_INBUILT_HIDDEN_FIELDS,
  RO_CRATE_PREVIEW_FIELD_RULES,
  USER_DEFINED_VARIABLE_HIDDEN_FIELDS
} from "../constants/roCratePreviewConsts";
import { saveAs } from "file-saver";
import { parseRoCratePayload } from "../utilities/roCratePreviewUtils";
import {
  createAxiosObject,
  handleError,
  showNotification,
  urlStringStartsWith
} from "../utilities/utilityFunctions";

const axiosRef = createAxiosObject();
const urlStringStart = urlStringStartsWith();
const RO_CRATE_ENDPOINT = "/api/generate_ro_crate/";

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
const visibleIdFieldSet = new Set(RO_CRATE_PREVIEW_FIELD_RULES.visibleIdFields);
const visibleIdLabelSet = new Set(
  RO_CRATE_PREVIEW_FIELD_RULES.visibleIdFields.map(displayLabelForField)
);
const visibleRequestFieldSet = new Set(
  RO_CRATE_PREVIEW_FIELD_RULES.visibleRequestFields
);
const hiddenSensitiveFieldPatterns =
  RO_CRATE_PREVIEW_FIELD_RULES.hiddenSensitiveFieldPatterns;
const hiddenLinkedRecordLabelPatterns =
  RO_CRATE_PREVIEW_FIELD_RULES.hiddenLinkedRecordLabelPatterns;
const entityFields = RO_CRATE_PREVIEW_FIELD_RULES.entityFields;
const entityIds = RO_CRATE_PREVIEW_FIELD_RULES.entityIds;
const recordEntityRules = RO_CRATE_PREVIEW_FIELD_RULES.recordEntity;
const attachmentEntityRules = RO_CRATE_PREVIEW_FIELD_RULES.attachmentEntity;
const sectionOptions = RO_CRATE_PREVIEW_FIELD_RULES.sectionOptions;
const hiddenContextEntityFieldSet = new Set(
  RO_CRATE_PREVIEW_FIELD_RULES.hiddenContextEntityFields
);
const hiddenBacklinkPropertySet = new Set(
  RO_CRATE_PREVIEW_FIELD_RULES.hiddenBacklinkProperties
);
const recordTypeLabel = displayLabelForField("recordType");

export default {
  name: "ROCratePreviewView",
  props: {
    previewConfig: {
      type: Object,
      default: null
    },
    embedded: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      loading: false,
      errorMessage: "",
      model: null,
      tableSearchTerm: "",
      activePreviewConfig: null,
      exportBusy: false,
      skippedRecords: []
    };
  },
  computed: {
    canExportPreview() {
      return Array.isArray(this.activePreviewConfig?.barcodes) && this.activePreviewConfig.barcodes.length > 0;
    },
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
  watch: {
    previewConfig: {
      immediate: true,
      deep: true,
      handler(newConfig) {
        if (newConfig) {
          this.loadPreviewFromConfig(newConfig);
        }
      }
    }
  },
  methods: {
    roCrateRequestParams(extra = {}) {
      return {
        barcodes: (this.activePreviewConfig?.barcodes || []).join(","),
        sections: (this.activePreviewConfig?.sections || []).join(","),
        ...extra
      };
    },
    sanitizeFilenamePart(value) {
      return String(value || "")
        .replace(/[^a-z0-9-_.]+/gi, "_")
        .replace(/_+/g, "_")
        .replace(/^_|_$/g, "");
    },
    parseContentDispositionFilename(header) {
      const match = String(header || "").match(/filename="?([^"]+)"?/i);
      return match?.[1] || "";
    },
    async loadPreviewFromConfig(previewConfig) {
      if (!Array.isArray(previewConfig?.barcodes) || !previewConfig.barcodes.length) {
        this.errorMessage = "Select at least one library or sample before previewing an RO-Crate.";
        return;
      }

      this.activePreviewConfig = {
        ...previewConfig,
        sections: Array.isArray(previewConfig.sections) ? previewConfig.sections : []
      };
      this.loading = true;
      this.errorMessage = "";

      try {
        const response = await axiosRef.get(`${urlStringStart}${RO_CRATE_ENDPOINT}`, {
          params: this.roCrateRequestParams({ preview: "true" })
        });
        const payload = response?.data || {};
        this.skippedRecords = Array.isArray(payload.skipped_records)
          ? payload.skipped_records
          : [];
        this.model = parseRoCratePayload(payload.ro_crate || payload, {
          name: payload.archive_name || "ro-crate-preview.jsonld"
        });
        showNotification("RO-Crate preview loaded successfully.", "success");
      } catch (error) {
        this.model = null;
        this.errorMessage =
          error?.response?.data?.error ||
          error?.message ||
          "The selected RO-Crate preview could not be loaded.";
      } finally {
        this.loading = false;
      }
    },
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
    exportToPdf() {
      if (!this.model) {
        showNotification("Load an RO-Crate before exporting to PDF.", "warning");
        return;
      }
      document.body.classList.add("rocrate-printing");
      const cleanupPrintClass = () => {
        document.body.classList.remove("rocrate-printing");
        window.removeEventListener("afterprint", cleanupPrintClass);
      };
      window.addEventListener("afterprint", cleanupPrintClass);
      window.print();
    },
    async exportROCrate() {
      if (!this.canExportPreview) {
        showNotification(
          "Open a Parkour RO-Crate preview before exporting the ZIP.",
          "warning"
        );
        return;
      }

      try {
        this.exportBusy = true;
        const response = await axiosRef.get(`${urlStringStart}${RO_CRATE_ENDPOINT}`, {
          params: this.roCrateRequestParams(),
          responseType: "blob"
        });
        const headerFilename = this.parseContentDispositionFilename(
          response?.headers?.["content-disposition"]
        );
        const safeBarcodeName = this.sanitizeFilenamePart(
          this.activePreviewConfig.barcodes.join("_")
        );
        const filename = headerFilename || `${safeBarcodeName || "ro_crate"}_ro_crate.zip`;
        saveAs(response?.data, filename);
        showNotification("RO-Crate exported successfully.", "success");
      } catch (error) {
        handleError(error);
      } finally {
        this.exportBusy = false;
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
      const overviewRules = RO_CRATE_PREVIEW_FIELD_RULES.requestOverview;

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
      const customLabels = RO_CRATE_PREVIEW_FIELD_RULES.propertyLabels;
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
          const structuredValue = this.parseStructuredStringValue(value);
          if (structuredValue !== null) {
            return this.formatSummaryValue(structuredValue);
          }
          const formattedDate = this.formatDisplayDate(value);
          if (formattedDate) {
            return formattedDate;
          }
        }
        return String(value);
      }

      if (Array.isArray(value)) {
        return value.map((entry) => this.formatSummaryValue(entry)).filter((entry) => entry !== "-");
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
        return Object.fromEntries(
          Object.entries(value)
            .map(([key, nestedValue]) => [this.formatPropertyLabel(key), this.formatSummaryValue(nestedValue)])
            .filter(([, nestedValue]) => !this.isEmptyDisplayValue(nestedValue, { hideDash: true }))
        );
      }

      return String(value);
    },
    parseStructuredStringValue(value) {
      const text = String(value || "").trim();
      if (!text || !["[", "{"].includes(text[0])) return null;
      try {
        const parsedValue = JSON.parse(text);
        return typeof parsedValue === "object" && parsedValue !== null
          ? parsedValue
          : null;
      } catch {
        return null;
      }
    },
    isStructuredDisplayValue(value) {
      return (
        (Array.isArray(value) && value.length > 0) ||
        (value !== null &&
          typeof value === "object" &&
          !Array.isArray(value) &&
          Object.keys(value).length > 0)
      );
    },
    escapeDisplayHtml(value) {
      return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
    },
    structuredValueHtml(value) {
      if (Array.isArray(value)) {
        if (!value.length) return "";
        if (value.every((entry) => entry === null || typeof entry !== "object")) {
          return `<ul class="structured-value-list">${value
            .map((entry) => `<li>${this.escapeDisplayHtml(entry)}</li>`)
            .join("")}</ul>`;
        }

        const rows = value.map((entry) =>
          entry !== null && typeof entry === "object" && !Array.isArray(entry)
            ? entry
            : { Value: entry }
        );
        const columns = [
          ...new Set(rows.flatMap((row) => Object.keys(row)))
        ].slice(0, 12);

        return `<div class="structured-value-scroll"><table class="structured-value-table"><thead><tr>${columns
          .map((column) => `<th>${this.escapeDisplayHtml(column)}</th>`)
          .join("")}</tr></thead><tbody>${rows
          .map(
            (row) =>
              `<tr>${columns
                .map((column) => `<td>${this.structuredCellHtml(row[column])}</td>`)
                .join("")}</tr>`
          )
          .join("")}</tbody></table></div>`;
      }

      return `<div class="structured-value-scroll"><table class="structured-value-table key-value"><tbody>${Object.entries(
        value
      )
        .map(
          ([key, nestedValue]) =>
            `<tr><th>${this.escapeDisplayHtml(key)}</th><td>${this.structuredCellHtml(nestedValue)}</td></tr>`
        )
        .join("")}</tbody></table></div>`;
    },
    structuredCellHtml(value) {
      if (value === null || value === undefined || value === "") return "-";
      if (Array.isArray(value)) {
        return value
          .map((entry) => this.structuredCellHtml(entry))
          .join("<br>");
      }
      if (typeof value === "object") {
        if (value[entityFields.id]) {
          return this.escapeDisplayHtml(this.entityLabelById(value[entityFields.id]));
        }
        return this.escapeDisplayHtml(JSON.stringify(value));
      }
      return this.escapeDisplayHtml(value);
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
    shouldUseWideRow(row) {
      const key = String(row?.key || "").toLowerCase();
      const value = row?.value;
      if (
        key.includes("flowcell") ||
        key.includes("filepath") ||
        key.includes("metapath") ||
        key.includes("requested barcode")
      ) return true;
      if (!this.isStructuredDisplayValue(value)) return false;
      if (Array.isArray(value)) {
        const objectRows = value.filter(
          (entry) => entry !== null && typeof entry === "object" && !Array.isArray(entry)
        );
        const columnCount = new Set(objectRows.flatMap((entry) => Object.keys(entry))).size;
        return columnCount > 4 || value.length > 6;
      }
      return Object.keys(value || {}).length > 4;
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

      const recordRows = RO_CRATE_PREVIEW_FIELD_RULES.recordOverviewRows;
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
        if (sourceKind === RO_CRATE_PREVIEW_FIELD_RULES.entityKindRules[0].title) {
          return;
        }
        const linkedGroup = RO_CRATE_PREVIEW_FIELD_RULES.linkedRecordsSection;
        addRow(linkedGroup, `${sourceKind} linked by ${propertyLabel}`, sourceName);

        RO_CRATE_PREVIEW_FIELD_RULES.linkedSourceFields.forEach((key) => {
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
          RO_CRATE_PREVIEW_FIELD_RULES.commentLabelPrefixPattern,
          ""
        )
      );
    },
    commentGroup(label) {
      const value = String(label || "");
      return (
        this.findRuleTitle(
          RO_CRATE_PREVIEW_FIELD_RULES.commentGroups,
          (rule) => rule.patterns.some((pattern) => pattern.test(value))
        ) || sectionOptions.defaultCommentGroup
      );
    },
    groupEntityProperty(key) {
      const value = String(key || "");
      return (
        this.findRuleTitle(
          RO_CRATE_PREVIEW_FIELD_RULES.entityPropertyGroups,
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
          RO_CRATE_PREVIEW_FIELD_RULES.entityKindRules,
          (rule) => this.matchesEntityRule(rule, entity)
        ) || sectionOptions.relatedEntityKind
      );
    }
  }
};
</script>

<style scoped>
.rocrate-preview-page {
  min-height: 100vh;
  background:
    radial-gradient(circle at top left, rgba(15, 95, 135, 0.18), transparent 32%),
    radial-gradient(circle at top right, rgba(43, 167, 123, 0.18), transparent 28%),
    linear-gradient(180deg, #f4fafb 0%, #ecf3f5 50%, #f8fcfd 100%);
  color: #10242f;
}

.rocrate-preview-page.embedded {
  height: 100%;
  min-height: 100%;
  overflow: auto;
  background: #f4fafb;
}

.rocrate-preview-shell {
  max-width: 1520px;
  margin: 0 auto;
  padding: 32px 24px 56px;
}

.rocrate-preview-page.embedded .rocrate-preview-shell {
  max-width: none;
  padding: 16px 18px 28px;
}

.rocrate-preview-shell.is-empty {
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

.hero-button.secondary {
  background: #e7f0f2;
  color: #173948;
  border: 1px solid rgba(16, 36, 47, 0.12);
}

.pdf-export-button {
  white-space: nowrap;
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

.rocrate-preview-page.embedded .upload-stage {
  border-radius: 8px;
  margin-bottom: 16px;
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

.preview-feedback {
  display: flex;
  align-items: center;
  gap: 12px;
  border-radius: 18px;
  padding: 16px 18px;
  margin-bottom: 24px;
  font-weight: 700;
}

.preview-feedback.loading {
  background: rgba(243, 249, 250, 0.9);
}

.preview-feedback.error {
  background: rgba(255, 240, 240, 0.96);
  color: #7c2020;
}

.preview-feedback.warning {
  background: rgba(255, 249, 229, 0.96);
  color: #755300;
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

.rocrate-preview-page.embedded .upload-title-main {
  display: none;
}

.rocrate-preview-page.embedded .upload-content {
  min-height: 112px;
}

.rocrate-preview-page.embedded .upload-watermark,
.rocrate-preview-page.embedded .upload-watermark-crop {
  min-height: 112px;
  height: 112px;
}

.rocrate-preview-page.embedded .upload-watermark-crop {
  width: 112px;
}

.rocrate-preview-page.embedded .upload-watermark img {
  width: 270px;
}

.quick-summary-row.wide-row {
  grid-column: 1 / -1;
  grid-template-columns: 140px minmax(0, 1fr);
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
  overflow-wrap: anywhere;
  word-break: normal;
}

.quick-summary-value :deep(.structured-value-scroll) {
  max-width: 100%;
  overflow-x: auto;
}

.quick-summary-value :deep(.structured-value-table) {
  width: 100%;
  min-width: 360px;
  border-collapse: collapse;
  font-size: 13px;
  line-height: 1.4;
}

.quick-summary-value :deep(.structured-value-table th),
.quick-summary-value :deep(.structured-value-table td) {
  border: 1px solid rgba(16, 36, 47, 0.12);
  padding: 8px 10px;
  text-align: left;
  vertical-align: top;
  background: rgba(255, 255, 255, 0.72);
}

.quick-summary-value :deep(.structured-value-table th) {
  background: rgba(231, 240, 242, 0.86);
  color: #244858;
  font-weight: 800;
}

.quick-summary-value :deep(.structured-value-table.key-value) {
  min-width: 0;
}

.quick-summary-value :deep(.structured-value-table.key-value th) {
  width: 180px;
}

.quick-summary-value :deep(.structured-value-list) {
  margin: 0;
  padding-left: 18px;
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
  .rocrate-preview-shell {
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

@media print {
  @page {
    size: A4;
    margin: 10mm;
  }

  :global(html),
  :global(body),
  :global(#app) {
    width: auto !important;
    height: auto !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: visible !important;
    background: #fff !important;
  }

  .rocrate-preview-page {
    min-height: auto;
    height: auto;
    overflow: visible;
    background: #fff;
    color: #10242f;
    font-size: 9pt;
  }

  .rocrate-preview-shell {
    max-width: none;
    padding: 0;
    margin: 0;
  }

  .upload-stage,
  .table-search-inline,
  .pdf-export-button {
    display: none !important;
  }

  .preview-workspace {
    display: block;
  }

  .detail-kicker {
    font-size: 12pt;
    margin-bottom: 5mm;
  }

  .detail-card {
    padding: 5mm;
    margin-bottom: 5mm;
    border-radius: 4mm;
    box-shadow: none;
    border: 1px solid #d8e0e4;
    background: #fff;
  }

  .record-table-title {
    font-size: 11pt;
  }

  .record-group-title,
  .quick-summary-key {
    font-size: 7.5pt;
    letter-spacing: 0.02em;
  }

  .quick-summary-table {
    display: grid !important;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 3mm;
    margin-top: 3mm;
  }

  .quick-summary-row {
    grid-template-columns: 28mm minmax(0, 1fr);
    gap: 3mm;
    padding: 3mm;
    border-radius: 3mm;
    background: #fff;
  }

  .quick-summary-row.wide-row {
    grid-column: 1 / -1;
    grid-template-columns: 30mm minmax(0, 1fr);
  }

  .quick-summary-value {
    line-height: 1.35;
    overflow-wrap: anywhere;
    word-break: normal;
  }

  .quick-summary-value :deep(.structured-value-scroll) {
    overflow: visible;
  }

  .quick-summary-value :deep(.structured-value-table) {
    min-width: 0;
    width: 100%;
    table-layout: fixed;
    font-size: 7.5pt;
    line-height: 1.25;
  }

  .quick-summary-value :deep(.structured-value-table th),
  .quick-summary-value :deep(.structured-value-table td) {
    padding: 1.5mm;
    overflow-wrap: anywhere;
    word-break: normal;
  }

  .quick-summary-value :deep(.structured-value-table.key-value th) {
    width: 24mm;
  }

  .quick-summary-row,
  .record-table-block {
    break-inside: avoid;
    page-break-inside: avoid;
  }

  .record-group {
    break-inside: auto;
    page-break-inside: auto;
  }
}
</style>


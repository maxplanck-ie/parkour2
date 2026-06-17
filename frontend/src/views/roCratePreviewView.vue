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
            {{ model ? labels.loadedTitle : labels.emptyTitle }}
          </div>
          <div class="upload-subtitle">
            {{ model ? labels.loadedSubtitle : labels.emptySubtitle }}
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
            <button
              v-if="model"
              class="hero-button secondary pdf-export-button"
              type="button"
              @click="exportToPdf"
            >
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
        <header class="print-report-header">
          <div>
            <div class="print-report-title">Parkour RO-Crate Preview</div>
            <div class="print-report-subtitle">{{ printReportSubtitle }}</div>
          </div>
          <div class="print-report-meta">{{ printGeneratedAt }}</div>
        </header>

        <section class="preview-search-panel" aria-label="Search RO-Crate preview">
          <div class="preview-search-copy">
            <div class="preview-search-title">Search Preview</div>
            <div class="preview-search-meta">{{ searchResultSummary }}</div>
          </div>
          <div class="table-search-inline">
            <div class="table-search-input-wrap">
              <input
                v-model.trim="tableSearchInput"
                class="table-search-input"
                type="search"
                placeholder="Search by request, record, field, or value"
              />
              <font-awesome-icon class="table-search-icon" icon="fa-solid fa-magnifying-glass" />
            </div>
          </div>
        </section>

        <section class="detail-card request-overview-card">
          <div class="detail-header">
            <div class="detail-kicker">Request(s) Overview</div>
          </div>
          <div class="request-overview-list">
            <article
              v-for="request in visibleRequestGroups"
              :key="`overview-${request.id}`"
              class="request-overview-item"
            >
              <div class="request-overview-title">{{ request.name }}</div>
              <div v-if="request.records.length" class="record-chip-list">
                <span
                  v-for="record in request.records"
                  :key="`overview-${request.id}-${record.id}`"
                  class="record-chip"
                >
                  {{ record.name }}<template v-if="record.barcode"> ({{ record.barcode }})</template>
                </span>
              </div>
              <div v-else class="empty-inline">{{ labels.noRecords }}</div>
            </article>
          </div>
        </section>

        <section
          v-for="(request, index) in visibleRequestGroups"
          :key="request.id"
          class="detail-card request-card"
        >
          <div class="detail-header">
            <div>
              <div class="detail-kicker">Request {{ index + 1 }}: {{ request.name }}</div>
            </div>
          </div>

          <section v-if="request.requestRows.length" class="record-group">
            <div class="record-group-title">Request Details</div>
            <div class="quick-summary-table record-group-table">
              <div
                v-for="row in request.requestRows"
                :key="`${request.id}-request-${row.key}`"
                class="quick-summary-row"
                :class="{ 'wide-row': row.wide }"
              >
                <div class="quick-summary-key">{{ row.key }}</div>
                <div class="quick-summary-value" :class="valueClassForRow(row)">
                  <component :is="displayComponent(row.value)" :value="row.value" />
                </div>
              </div>
            </div>
          </section>

          <section class="record-group">
            <div class="record-group-title">Libraries/Samples</div>
            <div v-if="request.records.length" class="record-table-list">
              <article
                v-for="record in request.records"
                :key="record.id"
                class="record-table-block"
              >
                <div class="record-table-header">
                  <div class="record-table-title">{{ record.type }}: {{ record.name }}</div>
                  <div v-if="record.barcode" class="record-table-subtitle">Barcode: {{ record.barcode }}</div>
                </div>
                <section
                  v-for="section in record.sections"
                  :key="`${record.id}-${section.title}`"
                  class="record-group nested"
                >
                  <div class="record-group-title">{{ section.title }}</div>
                  <div class="quick-summary-table record-group-table">
                    <div
                      v-for="row in section.rows"
                      :key="`${record.id}-${section.title}-${row.key}`"
                      class="quick-summary-row"
                      :class="{ 'wide-row': row.wide }"
                    >
                      <div class="quick-summary-key">{{ row.key }}</div>
                      <div class="quick-summary-value" :class="valueClassForRow(row)">
                        <component :is="displayComponent(row.value)" :value="row.value" />
                      </div>
                    </div>
                  </div>
                </section>
              </article>
            </div>
            <div v-else class="empty-inline">{{ labels.noRecords }}</div>
          </section>

          <section v-if="request.attachments.length" class="record-group">
            <div class="record-group-title">Attached Files</div>
            <div class="attachment-list">
              <div
                v-for="file in request.attachments"
                :key="file.id"
                class="attachment-item"
              >
                <font-awesome-icon icon="fa-solid fa-file-lines" />
                <span>{{ file.name }}</span>
              </div>
            </div>
          </section>
        </section>

        <footer class="print-report-footer">
          RO-Crate preview generated from Parkour metadata.
        </footer>
      </section>
    </div>
  </div>
</template>

<script>
import { h, nextTick } from "vue";
import { saveAs } from "file-saver";
import {
  RO_CRATE_BACKLINK_PROPERTIES,
  RO_CRATE_ENDPOINT,
  RO_CRATE_ENTITY_IDS,
  RO_CRATE_ENTITY_PREFIXES,
  RO_CRATE_FIELD_KEYS,
  RO_CRATE_HIDDEN_FIELD_PATTERNS,
  RO_CRATE_INBUILT_HIDDEN_FIELDS,
  RO_CRATE_LINKED_MODEL_RELATION_FIELDS,
  RO_CRATE_MODEL_SECTION_RULES,
  RO_CRATE_PREVIEW_LABELS,
  RO_CRATE_PROPERTY_LABEL_OVERRIDES,
  RO_CRATE_PROPERTY_PREFIX_PATTERN,
  RO_CRATE_RECORD_TYPES,
  RO_CRATE_RELATED_MODEL_HIDDEN_FIELDS,
  RO_CRATE_RELATION_FIELDS,
  RO_CRATE_VISIBLE_ID_FIELDS,
  USER_DEFINED_VARIABLE_HIDDEN_FIELDS
} from "../constants/roCratePreviewConsts";
import { parseRoCratePayload } from "../utilities/roCratePreviewUtils";
import {
  createAxiosObject,
  handleError,
  showNotification,
  urlStringStartsWith
} from "../utilities/utilityFunctions";

const axiosRef = createAxiosObject();
const urlStringStart = urlStringStartsWith();
const fieldKeys = RO_CRATE_FIELD_KEYS;
const hiddenFields = new Set(RO_CRATE_INBUILT_HIDDEN_FIELDS);
const userHiddenFields = new Set(USER_DEFINED_VARIABLE_HIDDEN_FIELDS || []);
const visibleIdFields = new Set(RO_CRATE_VISIBLE_ID_FIELDS);
const relatedModelHiddenFields = new Set(RO_CRATE_RELATED_MODEL_HIDDEN_FIELDS);
const normalisePolicyField = (value) =>
  String(value || "")
    .replace(/[^a-z0-9]+/gi, "")
    .toLowerCase();
const hiddenPolicyFields = new Set(
  [...hiddenFields, ...userHiddenFields].map((field) => normalisePolicyField(field))
);
const visibleIdPolicyFields = new Set(
  [...visibleIdFields].map((field) => normalisePolicyField(field))
);

const DisplayValue = {
  name: "ROCrateDisplayValue",
  props: {
    value: {
      type: [String, Number, Boolean, Array, Object],
      default: ""
    }
  },
  methods: {
    isObject(value) {
      return value && typeof value === "object" && !Array.isArray(value);
    },
    renderPrimitive(value) {
      return h("span", String(value ?? "-"));
    },
    isTableList(values) {
      return (
        Array.isArray(values) &&
        values.length > 0 &&
        values.every((value) => this.isObject(value))
      );
    },
    renderList(values) {
      if (this.isTableList(values)) return this.renderObjectTable(values);
      return h(
        "ol",
        { class: "structured-value-list" },
        values.map((value, index) => h("li", { key: index }, this.renderAny(value)))
      );
    },
    renderObjectTable(values) {
      const columns = [
        ...new Set(values.flatMap((value) => Object.keys(value || {})))
      ];
      return h(
        "div",
        { class: "structured-value-scroll" },
        h(
          "table",
          { class: "structured-value-table indexed-table" },
          [
            h(
              "thead",
              h("tr", [
                h("th", { class: "row-number-column" }, "#"),
                ...columns.map((column) => h("th", { key: column }, column))
              ])
            ),
            h(
              "tbody",
              values.map((value, index) =>
                h("tr", { key: index }, [
                  h("td", { class: "row-number-column" }, String(index + 1)),
                  ...columns.map((column) =>
                    h("td", { key: column }, this.renderAny(value?.[column]))
                  )
                ])
              )
            )
          ]
        )
      );
    },
    renderObject(value) {
      return h(
        "div",
        { class: "structured-value-scroll" },
        h(
          "table",
          { class: "structured-value-table key-value" },
          h(
            "tbody",
            Object.entries(value).map(([key, nestedValue]) =>
              h("tr", { key }, [
                h("th", key),
                h("td", this.renderAny(nestedValue))
              ])
            )
          )
        )
      );
    },
    renderAny(value) {
      if (Array.isArray(value)) return this.renderList(value);
      if (this.isObject(value)) return this.renderObject(value);
      return this.renderPrimitive(value);
    }
  },
  render() {
    return this.renderAny(this.value);
  }
};

export default {
  name: "ROCratePreviewView",
  components: {
    ROCrateDisplayValue: DisplayValue
  },
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
      tableSearchInput: "",
      activePreviewConfig: null,
      exportBusy: false,
      skippedRecords: []
    };
  },
  computed: {
    labels() {
      return RO_CRATE_PREVIEW_LABELS;
    },
    canExportPreview() {
      const identifiers = this.previewIdentifierValues(this.activePreviewConfig);
      return identifiers.barcodes.length > 0 || identifiers.requests.length > 0;
    },
    printGeneratedAt() {
      return `Generated ${this.formatDate(new Date().toISOString())}`;
    },
    printReportSubtitle() {
      const names = this.requestGroups.map((request) => request.name);
      return `${names.join(", ") || "Selected records"} | ${this.totalRecordCount} records`;
    },
    totalRecordCount() {
      return this.requestGroups.reduce(
        (count, request) => count + request.records.length,
        0
      );
    },
    searchTerm() {
      return String(this.tableSearchInput || "").toLowerCase();
    },
    searchResultSummary() {
      if (!this.searchTerm) {
        return "Search visible requests, records, fields, and values.";
      }
      return `${this.visibleRequestGroups.length} ${this.visibleRequestGroups.length === 1 ? "request" : "requests"} match "${this.tableSearchInput}"`;
    },
    rootEntity() {
      return this.entityById(RO_CRATE_ENTITY_IDS.rootDataset);
    },
    requestGroups() {
      if (!this.model) return [];
      const studies = this.model.graph.filter((entity) =>
        String(entity?.[fieldKeys.id] || "").startsWith(
          RO_CRATE_ENTITY_PREFIXES.study
        )
      );
      const groups = studies.map((study, index) =>
        this.buildRequestGroup(study, index)
      );
      if (groups.length) return groups;
      return [this.buildFallbackRequestGroup()];
    },
    visibleRequestGroups() {
      if (!this.searchTerm) return this.requestGroups;
      return this.requestGroups
        .map((request) => ({
          ...request,
          records: request.records.filter((record) =>
            this.matchesSearch([
              request.name,
              record.name,
              record.barcode,
              record.type,
              ...record.sections.flatMap((section) =>
                section.rows.flatMap((row) => [row.key, row.value])
              )
            ])
          ),
          requestRows: request.requestRows.filter((row) =>
            this.matchesSearch([request.name, row.key, row.value])
          ),
          attachments: request.attachments.filter((file) =>
            this.matchesSearch([request.name, file.name, file.id])
          )
        }))
        .filter(
          (request) =>
            this.matchesSearch([request.name]) ||
            request.records.length ||
            request.requestRows.length ||
            request.attachments.length
        );
    },
    zipContentRows() {
      const rows = [
        {
          path: RO_CRATE_ENTITY_IDS.metadataDescriptor,
          type: "RO-Crate metadata"
        }
      ];
      this.requestGroups.forEach((request) => {
        request.attachments.forEach((file) => {
          rows.push({
            path: file.contentUrl || file.id,
            type: `${request.name} attachment`
          });
        });
      });
      return rows.filter((row) => this.matchesSearch([row.path, row.type]));
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
    displayComponent() {
      return "ROCrateDisplayValue";
    },
    previewIdentifierValues(config = {}) {
      const barcodes = Array.isArray(config?.barcodes)
        ? config.barcodes.filter(Boolean)
        : [];
      if (barcodes.length) {
        return {
          barcodes,
          requests: []
        };
      }
      const requestNames = Array.isArray(config?.requestNames)
        ? config.requestNames.filter(Boolean)
        : [];
      const requestName = config?.requestName ? [config.requestName] : [];
      return {
        barcodes,
        requests: requestNames.length ? requestNames : requestName
      };
    },
    roCrateRequestParams(extra = {}) {
      const identifiers = this.previewIdentifierValues(this.activePreviewConfig);
      const sections = Array.isArray(this.activePreviewConfig?.sections)
        ? this.activePreviewConfig.sections.filter(Boolean)
        : [];
      const params = { ...extra };
      if (identifiers.barcodes.length) params.barcodes = identifiers.barcodes.join(",");
      if (identifiers.requests.length) params.requests = identifiers.requests.join(",");
      if (sections.length) params.sections = sections.join(",");
      return params;
    },
    async loadPreviewFromConfig(previewConfig) {
      const identifiers = this.previewIdentifierValues(previewConfig);
      if (!identifiers.barcodes.length && !identifiers.requests.length) {
        this.errorMessage =
          "Select at least one library or sample before previewing an RO-Crate.";
        return;
      }

      this.activePreviewConfig = {
        ...previewConfig,
        sections: Array.isArray(previewConfig.sections) ? previewConfig.sections : []
      };
      this.loading = true;
      this.errorMessage = "";
      this.model = null;

      try {
        const response = await axiosRef.get(`${urlStringStart}${RO_CRATE_ENDPOINT}`, {
          params: this.roCrateRequestParams({ preview: "true" })
        });
        const payload = response?.data || {};
        this.skippedRecords = Array.isArray(payload.skipped_records)
          ? payload.skipped_records
          : [];
        if (!payload.ro_crate) {
          throw new Error("The RO-Crate preview response did not include ro_crate.");
        }
        if (!payload.archive_name) {
          throw new Error("The RO-Crate preview response did not include archive_name.");
        }
        this.model = parseRoCratePayload(payload.ro_crate, {
          name: payload.archive_name
        });
      } catch (error) {
        this.errorMessage =
          error?.response?.data?.error ||
          error?.message ||
          "The selected RO-Crate preview could not be loaded.";
      } finally {
        this.loading = false;
      }
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
        const filename =
          this.parseContentDispositionFilename(
            this.responseHeader(response?.headers, "content-disposition")
          ) || this.fallbackArchiveFilename();
        saveAs(response?.data, filename);
        showNotification("RO-Crate exported successfully.", "success");
      } catch (error) {
        handleError(error);
      } finally {
        this.exportBusy = false;
      }
    },
    async exportToPdf() {
      if (!this.model) {
        showNotification("Load an RO-Crate before exporting to PDF.", "warning");
        return;
      }
      const printWindow = window.open("", "_blank");
      if (!printWindow) {
        showNotification("Allow pop-ups to export this preview to PDF.", "warning");
        return;
      }

      const originalSearch = this.tableSearchInput;
      if (originalSearch) {
        this.tableSearchInput = "";
        await nextTick();
      }

      const report = this.$el.querySelector(".preview-workspace");
      if (!report) {
        printWindow.close();
        showNotification("The RO-Crate preview is not ready to export.", "warning");
        if (originalSearch) this.tableSearchInput = originalSearch;
        return;
      }
      const reportHtml = report.innerHTML;
      const reportText = report.textContent?.trim() || "";
      if (originalSearch) {
        this.tableSearchInput = originalSearch;
        await nextTick();
      }
      if (!reportText) {
        printWindow.close();
        showNotification("The RO-Crate preview has no printable content.", "warning");
        return;
      }

      const html = this.printDocumentHtml(reportHtml);
      printWindow.document.open();
      printWindow.document.write(html);
      printWindow.document.close();
    },
    printDocumentHtml(reportHtml) {
      const documentTitle = this.printDocumentTitle();
      return `<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>${this.escapeHtml(documentTitle)}</title>
    <style>${this.printDocumentCss()}</style>
  </head>
  <body>
    <main class="rocrate-print-document">${reportHtml}</main>
    <script>
      (function () {
        var printStarted = false;
        window.addEventListener("afterprint", function () {
          setTimeout(function () {
            window.close();
          }, 750);
        }, { once: true });
        function afterFrames(callback) {
          requestAnimationFrame(function () {
            requestAnimationFrame(callback);
          });
        }
        function printWhenReady() {
          if (printStarted) return;
          printStarted = true;
          var fontsReady = document.fonts && document.fonts.ready
            ? document.fonts.ready.catch(function () {})
            : Promise.resolve();
          fontsReady.then(function () {
            afterFrames(function () {
              window.focus();
              window.print();
            });
          });
        }
        if (document.readyState === "complete") {
          printWhenReady();
        } else {
          window.addEventListener("load", printWhenReady, { once: true });
        }
      })();
    <\/script>
  </body>
</html>`;
    },
    printDocumentTitle() {
      const archiveName = String(this.model?.source?.name || "")
        .replace(/\.zip$/i, "")
        .trim();
      const requestIds = this.previewRequestIds();
      const fallbackName = requestIds.length
        ? `${requestIds.join("_")}_ro_crate`
        : "parkour_ro_crate_preview";
      const baseName = this.sanitizeFilenamePart(archiveName || fallbackName)
        .replace(/\.pdf$/i, "")
        .slice(0, 120);
      const timestamp = new Date()
        .toISOString()
        .replace(/\.\d+Z$/, "")
        .replace(/[T:]/g, "-");
      return `${baseName}_${timestamp}`;
    },
    printFooterText() {
      const requestNames = this.requestGroups.map((request) => request.name).filter(Boolean);
      const recordNames = this.requestGroups
        .flatMap((request) => request.records.map((record) => record.name))
        .filter(Boolean);
      const requestText =
        requestNames.length === 1
          ? `Request: ${requestNames[0]}`
          : `Requests: ${requestNames.join(", ") || "Selected requests"}`;
      const recordText =
        recordNames.length === 1
          ? `Library/Sample: ${recordNames[0]}`
          : `Libraries/Samples: ${recordNames.length || this.totalRecordCount} selected`;
      return `${requestText} | ${recordText}`;
    },
    printDocumentCss() {
      const footerText = this.escapeCssString(this.printFooterText());
      return `
@page {
  size: A4;
  margin: 12mm 9mm 14mm;
  @bottom-left {
    content: "${footerText}";
    color: #5e7884;
    font-family: Arial, Helvetica, sans-serif;
    font-size: 6.5pt;
  }
  @bottom-right {
    content: "Page " counter(page);
    color: #5e7884;
    font-family: Arial, Helvetica, sans-serif;
    font-size: 6.5pt;
  }
}
* { box-sizing: border-box; }
html, body {
  margin: 0;
  padding: 0;
  background: #fff;
  color: #10242f;
  font-family: Arial, Helvetica, sans-serif;
  font-size: 9pt;
  line-height: 1.35;
}
.rocrate-print-document { width: 100%; }
.upload-stage,
.preview-search-panel,
.pdf-export-button,
.rocrate-export-button { display: none !important; }
.print-report-header {
  display: flex;
  justify-content: space-between;
  gap: 8mm;
  margin-bottom: 3mm;
  padding-bottom: 2mm;
  border-bottom: 1px solid #d8e0e4;
}
.print-report-title { font-size: 9pt; font-weight: 800; }
.print-report-subtitle,
.print-report-meta {
  color: #5e7884;
  font-size: 7pt;
  line-height: 1.3;
}
.print-report-footer {
  display: block;
  margin-top: 4mm;
  padding-top: 2mm;
  border-top: 1px solid #d8e0e4;
  color: #6b818c;
  font-size: 6.5pt;
}
.detail-card {
  padding: 2.5mm 0;
  margin-bottom: 3mm;
  border-top: 1px solid #d8e0e4;
  background: #fff;
}
.detail-kicker,
.record-group-title {
  color: #1d5f78;
  font-weight: 800;
  text-transform: uppercase;
}
.request-overview-item,
.attachment-item,
.zip-content-row,
.quick-summary-row {
  break-inside: avoid;
  page-break-inside: avoid;
}
.request-overview-item,
.record-table-block,
.attachment-item,
.zip-content-row {
  padding: 2mm 0;
}
.request-overview-title,
.record-table-title { font-weight: 800; color: #173948; }
.record-chip-list,
.attachment-list,
.zip-content-list,
.record-table-list {
  display: block;
}
.record-chip {
  display: inline-block;
  margin: 0 3mm 1.5mm 0;
  color: #0d6f73;
  font-weight: 700;
}
.quick-summary-table { display: block; }
.quick-summary-row {
  display: grid;
  grid-template-columns: 38mm minmax(0, 1fr);
  gap: 2mm;
  margin-bottom: 1.4mm;
  padding: 1.8mm;
  border: 1px solid #edf1f3;
  border-radius: 1.5mm;
  background: #fff;
}
.quick-summary-key {
  color: #173948;
  font-size: 7.2pt;
  font-weight: 800;
  line-height: 1.2;
  text-transform: uppercase;
  overflow-wrap: anywhere;
}
.quick-summary-value {
  color: #173948;
  overflow-wrap: anywhere;
  word-break: normal;
}
.structured-value-list {
  margin: 0;
  padding-left: 18px;
}
.structured-value-scroll { overflow: visible; }
.structured-value-table {
  width: 100%;
  min-width: 0;
  border-collapse: collapse;
  font-size: 7.2pt;
  line-height: 1.25;
}
.structured-value-table th,
.structured-value-table td {
  border: 1px solid rgba(16, 36, 47, 0.14);
  padding: 1mm;
  text-align: left;
  vertical-align: top;
  overflow-wrap: anywhere;
}
.structured-value-table th {
  width: 28mm;
  background: #edf4f6;
  color: #244858;
  font-weight: 800;
}
.structured-value-table.indexed-table th { width: auto; }
.structured-value-table .row-number-column {
  width: 8mm;
  text-align: right;
  white-space: nowrap;
  color: #5e7884;
}
svg { display: none; }
`;
    },
    escapeHtml(value) {
      return String(value || "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
    },
    escapeCssString(value) {
      return String(value || "")
        .replace(/\\/g, "\\\\")
        .replace(/"/g, '\\"')
        .replace(/\r?\n/g, " ");
    },
    fallbackArchiveFilename() {
      const previewName = this.model?.source?.name || "";
      if (previewName.toLowerCase().endsWith(".zip")) {
        return this.sanitizeFilenamePart(previewName);
      }
      const requestIds = this.previewRequestIds();
      if (requestIds.length) {
        return `${requestIds.join("_")}_ro_crate.zip`;
      }
      return "parkour_ro_crate.zip";
    },
    previewRequestIds() {
      const configuredIds = Array.isArray(this.activePreviewConfig?.requestIds)
        ? this.activePreviewConfig.requestIds
        : [];
      const graphIds = this.requestGroups
        .map((request) => request.requestNumber)
        .filter(Boolean);
      return [...new Set([...configuredIds, ...graphIds].map(String).filter(Boolean))];
    },
    sanitizeFilenamePart(value) {
      return String(value || "")
        .replace(/[^a-z0-9-_.]+/gi, "_")
        .replace(/_+/g, "_")
        .replace(/^_|_$/g, "");
    },
    parseContentDispositionFilename(header) {
      const headerValue = String(header || "");
      const encodedMatch = headerValue.match(/filename\*=UTF-8''([^;]+)/i);
      if (encodedMatch?.[1]) {
        return decodeURIComponent(encodedMatch[1].replace(/^"|"$/g, ""));
      }
      return headerValue.match(/filename="?([^";]+)"?/i)?.[1] || "";
    },
    responseHeader(headers, key) {
      return (
        headers?.get?.(key) ||
        headers?.[key] ||
        headers?.[key.toLowerCase()] ||
        headers?.[key.toUpperCase()] ||
        ""
      );
    },
    buildRequestGroup(study, index) {
      const studyId = study?.[fieldKeys.id] || `request-${index + 1}`;
      const requestNumber = this.idSuffix(studyId);
      const requestEntity = this.entityById(
        `${RO_CRATE_ENTITY_PREFIXES.requestContext}${requestNumber}`
      );
      const recordIds = this.studyRecordIds(study);
      const records = recordIds
        .map((recordId) => this.buildRecord(recordId))
        .filter(Boolean)
        .sort((left, right) => left.name.localeCompare(right.name));

      return {
        id: studyId,
        requestNumber,
        name:
          requestEntity?.[fieldKeys.name] ||
          study?.[fieldKeys.name] ||
          `${RO_CRATE_PREVIEW_LABELS.unnamedRequest} ${index + 1}`,
        requestRows: this.rowsForEntity(requestEntity, "Request Details"),
        records,
        attachments: this.attachmentsForRequest(requestEntity?.[fieldKeys.id])
      };
    },
    buildFallbackRequestGroup() {
      const records = this.model.graph
        .filter((entity) => this.isRecordEntity(entity))
        .map((entity) => this.buildRecord(entity[fieldKeys.id]))
        .filter(Boolean)
        .sort((left, right) => left.name.localeCompare(right.name));
      return {
        id: "fallback-request",
        requestNumber: "",
        name:
          this.rootEntity?.[fieldKeys.name] ||
          this.activePreviewConfig?.requestName ||
          RO_CRATE_PREVIEW_LABELS.unnamedRequest,
        requestRows: this.rowsForEntity(this.rootEntity, "Request Details"),
        records,
        attachments: this.attachmentsForRequest("")
      };
    },
    studyRecordIds(study) {
      const materials = study?.[fieldKeys.materials] || {};
      const fromMaterials = [
        ...this.referenceIds(materials[fieldKeys.samples]),
        ...this.referenceIds(materials[fieldKeys.otherMaterials])
      ].filter((id) => this.isRecordId(id));
      if (fromMaterials.length) return [...new Set(fromMaterials)];
      return this.referenceIds(study?.hasPart).filter((id) => this.isRecordId(id));
    },
    buildRecord(recordId) {
      const entity = this.entityById(recordId);
      if (!entity) return null;
      const type = this.recordType(entity);
      const rowsBySection = new Map();
      const addRows = (title, rows) => {
        const visibleRows = rows.filter((row) => !this.isHiddenRow(row));
        if (!visibleRows.length) return;
        rowsBySection.set(title, [...(rowsBySection.get(title) || []), ...visibleRows]);
      };

      const recordName =
        entity[fieldKeys.name] ||
        entity[fieldKeys.identifier] ||
        RO_CRATE_PREVIEW_LABELS.unnamedRecord;
      const primaryModelSectionTitle = `${type}: ${recordName}`;
      addRows("Overview", [
        { key: "Name", value: entity[fieldKeys.name] || RO_CRATE_PREVIEW_LABELS.unnamedRecord },
        { key: "Barcode", value: entity[fieldKeys.identifier] || "" }
      ]);
      this.propertyRows(entity, { skipSummaryModels: true }).forEach((row) =>
        addRows(row.group === primaryModelSectionTitle ? "Overview" : row.group, [row])
      );
      this.relatedModelSections(entity).forEach((section) => {
        addRows(section.title, section.rows);
      });
      const sequencingSections = this.sequencingSections(entity);
      sequencingSections.forEach((section) => {
        addRows(section.title, section.rows);
      });
      const processEntities = this.recordProcessEntities(recordId);
      const processSections = this.processDetailSections(recordId, processEntities);
      processSections.forEach((section) => {
        addRows(section.title, section.rows);
      });
      addRows(
        "Processes & Data",
        this.backlinkRows(recordId, {
          omitSourceIds: processEntities.map((processEntity) => processEntity[fieldKeys.id])
        })
      );

      return {
        id: recordId,
        type,
        name: recordName,
        barcode: entity[fieldKeys.identifier] || "",
        sections: [...rowsBySection.entries()]
          .map(([title, rows]) => ({
            title,
            rows: this.uniqueRows(rows).filter((row) =>
              this.matchesSearch([title, row.key, row.value])
            )
          }))
          .filter((section) => section.rows.length)
      };
    },
    rowsForEntity(entity, defaultGroup) {
      if (!entity) return [];
      return [
        ...Object.entries(entity)
          .filter(([key]) => !hiddenFields.has(key))
          .filter(([key]) => !this.shouldHideField(key))
          .map(([key, value]) => ({
            key: this.labelForField(key),
            value: this.displayValue(value),
            group: defaultGroup,
            wide: this.isWideValue(key, value)
          })),
        ...this.propertyRows(entity)
      ]
        .filter((row) => !this.isHiddenRow(row))
        .filter((row) => this.matchesSearch([row.key, row.value]));
    },
    propertyRows(entity, options = {}) {
      const refs = [
        ...this.referenceValues(entity?.[fieldKeys.additionalProperty]),
        ...this.referenceValues(entity?.[fieldKeys.parameterValue])
      ];
      return refs
        .map((ref) => this.resolveReference(ref))
        .filter(Boolean)
        .map((property) => {
          const name = property[fieldKeys.name];
          if (options.skipSummaryModels && this.isSummaryModelProperty(name)) {
            return null;
          }
          if (this.duplicatesDirectEntityField(entity, name, property[fieldKeys.value])) {
            return null;
          }
          return {
            key: this.labelForField(name),
            value: this.displayValue(property[fieldKeys.value]),
            group: this.groupForProperty(name, entity),
            wide: this.isWideValue(name, property[fieldKeys.value])
          };
        })
        .filter(Boolean)
        .filter((row) => !this.isHiddenRow(row));
    },
    duplicatesDirectEntityField(entity, propertyName, propertyValue) {
      const directKey = this.directFieldKeyForProperty(propertyName);
      if (!directKey || !Object.prototype.hasOwnProperty.call(entity || {}, directKey)) {
        return false;
      }
      return (
        JSON.stringify(this.displayValue(entity[directKey])) ===
        JSON.stringify(this.displayValue(propertyValue))
      );
    },
    directFieldKeyForProperty(propertyName) {
      const normalized = String(propertyName || "").replace(
        RO_CRATE_PROPERTY_PREFIX_PATTERN,
        ""
      );
      const directFieldMap = {
        name: fieldKeys.name,
        description: "description",
        identifier: fieldKeys.identifier,
        barcode: fieldKeys.identifier
      };
      return directFieldMap[normalized] || "";
    },
    relatedModelSections(entity) {
      return this.relatedModelEntities(entity)
        .map((relatedEntity) => {
          const rows = this.rowsForRelatedModelEntity(
            relatedEntity,
            this.relatedModelDisplayOptions(relatedEntity)
          );
          return {
            title: this.modelSectionTitleForEntity(relatedEntity),
            rows
          };
        })
        .filter((section) => section.rows.length)
        .filter((section) => this.matchesSearch([section.title, section.rows]));
    },
    relatedModelDisplayOptions(entity) {
      const id = String(entity?.[fieldKeys.id] || "");
      if (id.startsWith("#library-type-")) {
        return { omitRelationKeys: ["availableProtocols"] };
      }
      if (id.startsWith("#index-pair-")) {
        return {
          omitDisplayKeys: ["indexType"],
          omitRelationKeys: ["indexI7", "indexI5"]
        };
      }
      return {};
    },
    sequencingSections(entity) {
      return this.referenceIds(entity?.sequencedOn)
        .map((flowcellId) => this.entityById(flowcellId))
        .filter(Boolean)
        .map((flowcell) => {
          const title = this.flowcellSectionTitle(flowcell);
          return {
            title,
            rows: this.rowsForFlowcell(flowcell)
          };
        })
        .filter((section) => section.rows.length)
        .filter((section) => this.matchesSearch([section.title, section.rows]));
    },
    rowsForFlowcell(flowcell) {
      const rows = [
        ...this.rowsForRelatedModelEntity(flowcell, {
          omitRelationKeys: ["instrument", "hasInstrument", "hasLane"]
        })
      ];
      this.referenceIds(flowcell?.hasInstrument).forEach((sequencerId) => {
        this.addNestedEntityRows(rows, "Sequencer", this.entityById(sequencerId));
      });
      const lanes = this.referenceIds(flowcell?.hasLane)
        .map((laneId) => this.entityById(laneId))
        .filter(Boolean);
      if (lanes.length > 1) {
        rows.push({
          key: "Lanes",
          value: lanes.map((lane) => this.laneTableRow(lane)),
          wide: true
        });
      } else {
        lanes.forEach((lane) => {
          this.addNestedEntityRows(rows, "Lane", lane);
        });
      }
      this.referenceIds(flowcell?.hasPart)
        .map((entityId) => this.entityById(entityId))
        .filter((relatedEntity) => !this.isLaneEntity(relatedEntity))
        .filter((relatedEntity) => !this.isGenericFlowcellDataEntity(relatedEntity))
        .forEach((dataEntity) => {
          this.addNestedEntityRows(rows, "Flowcell Data", dataEntity, {
            omitDirectKeys: ["additionalType", "encodingFormat"],
            omitRelationKeys: ["about", "isPartOf"],
            omitEntitySummary: true
          });
        });
      this.referenceIds(flowcell?.about).forEach((processId) => {
        this.addNestedEntityRows(rows, "Flowcell Process", this.entityById(processId), {
          omitDirectKeys: ["additionalType"],
          omitRelationKeys: ["instrument", "hasInstrument", "object", "result"],
          omitPropertyRows: true,
          omitEntitySummary: true
        });
      });
      return this.uniqueRows(rows)
        .filter((row) => !this.isHiddenRow(row))
        .filter((row) => !this.isLowValuePreviewRow(row))
        .filter((row) => this.matchesSearch([row.key, row.value]));
    },
    addNestedEntityRows(rows, label, entity, options = {}) {
      if (!entity) return;
      if (this.shouldSkipNestedEntity(label, entity)) return;
      if (!options.omitEntitySummary) {
        rows.push({
          key: label,
          value: this.entityLabel(entity),
          wide: false
        });
      }
      this.rowsForRelatedModelEntity(entity, options)
        .filter((row) => !this.isLowValuePreviewRow(row, label))
        .forEach((row) => {
          rows.push({
            ...row,
            key: `${label} ${row.key}`
          });
        });
    },
    laneTableRow(lane) {
      return this.rowsForRelatedModelEntity(lane, {
        omitDirectKeys: ["additionalType"],
        omitPropertyRows: false
      }).reduce(
        (row, item) => ({
          ...row,
          [item.key]: item.value
        }),
        { Lane: this.entityLabel(lane) }
      );
    },
    flowcellSectionTitle(flowcell) {
      return `Flowcell: ${this.shortEntityLabel(flowcell, "Flowcell")}`;
    },
    processSectionTitle(processEntity) {
      const label = this.entityLabel(processEntity);
      const match = label.match(/^(sample|library|sequencing)\s+metadata\s+capture\s+for\s+(.+)$/i);
      if (match) {
        return `Process: ${match[2]}`;
      }
      return `Process: ${label}`;
    },
    shortEntityLabel(entity, prefix) {
      const label = this.entityLabel(entity);
      return label.replace(new RegExp(`^${prefix}\\s+`, "i"), "");
    },
    processDetailSections(recordId, processEntities = this.recordProcessEntities(recordId)) {
      return processEntities
        .map((processEntity) => {
          const title = this.processSectionTitle(processEntity);
          return {
            title,
            rows: this.rowsForProcessEntity(processEntity)
          };
        })
        .filter((section) => section.rows.length)
        .filter((section) => this.matchesSearch([section.title, section.rows]));
    },
    recordProcessEntities(recordId) {
      const processIds = (this.model?.backlinkMap?.[recordId] || [])
        .filter((link) => ["object", "result"].includes(link.property))
        .map((link) => link.sourceId)
        .filter((entityId) => this.isProcessEntity(this.entityById(entityId)));
      return [...new Set(processIds)]
        .map((entityId) => this.entityById(entityId))
        .filter(Boolean);
    },
    rowsForProcessEntity(processEntity) {
      const rows = [
        ...this.rowsForRelatedModelEntity(processEntity, {
          omitRelationKeys: ["executesLabProtocol", "object", "result"]
        })
      ];
      this.referenceIds(processEntity?.executesLabProtocol).forEach((protocolId) => {
        this.addNestedEntityRows(rows, "Protocol", this.entityById(protocolId));
      });
      this.referenceIds(processEntity?.result).forEach((dataId) => {
        this.addNestedEntityRows(rows, "Data Object", this.entityById(dataId), {
          omitDirectKeys: ["additionalType", "encodingFormat"],
          omitRelationKeys: [
            "associatedPool",
            "derivedFrom",
            "libraryProtocol",
            "libraryType",
            "nucleicAcidType",
            "organism",
            "readLength",
            "requestContext",
            "selectedIndexPair",
            "sequencedOn"
          ],
          omitDisplayKeys: [
            "associatedPool",
            "derivedFrom",
            "libraryProtocol",
            "libraryType",
            "nucleicAcidType",
            "organism",
            "readLength",
            "requestContext",
            "selectedIndexPair",
            "sequencedOn"
          ],
          omitPropertyRows: true,
          omitEntitySummary: true
        });
      });
      this.assaysForProcess(processEntity).forEach((assayEntity) => {
        this.addNestedEntityRows(rows, "Assay", assayEntity, {
          omitDirectKeys: [
            "additionalType",
            "measurementMethod",
            "variableMeasured"
          ],
          omitRelationKeys: ["hasPart", "about"],
          omitPropertyRows: true,
          omitEntitySummary: true
        });
      });
      return this.uniqueRows(rows)
        .filter((row) => !this.isHiddenRow(row))
        .filter((row) => !this.isLowValuePreviewRow(row))
        .filter((row) => this.matchesSearch([row.key, row.value]));
    },
    assaysForProcess(processEntity) {
      const processId = processEntity?.[fieldKeys.id];
      if (!processId) return [];
      const assayIds = (this.model?.backlinkMap?.[processId] || [])
        .filter((link) => link.property === "about")
        .map((link) => link.sourceId)
        .filter((entityId) => this.isAssayEntity(this.entityById(entityId)));
      return [...new Set(assayIds)]
        .map((entityId) => this.entityById(entityId))
        .filter(Boolean);
    },
    relatedModelEntities(entity) {
      const relationValues = RO_CRATE_LINKED_MODEL_RELATION_FIELDS
        .flatMap((key) => this.referenceIds(entity?.[key]))
        .map((entityId) => this.entityById(entityId))
        .filter(Boolean)
        .filter((relatedEntity) => !this.isLowValueBacklink(relatedEntity));
      const seen = new Set();
      return relationValues.filter((relatedEntity) => {
        const entityId = relatedEntity[fieldKeys.id];
        if (!entityId || seen.has(entityId)) return false;
        seen.add(entityId);
        return true;
      });
    },
    rowsForRelatedModelEntity(entity, options = {}) {
      const omittedDirectKeys = new Set([
        ...(options.omitDirectKeys || []),
        ...(options.omitDisplayKeys || [])
      ]);
      const directRows = Object.entries(entity)
        .filter(([key]) => key !== fieldKeys.name)
        .filter(([key]) => !RO_CRATE_RELATION_FIELDS[key])
        .filter(([key]) => !omittedDirectKeys.has(key))
        .filter(([key]) => !relatedModelHiddenFields.has(key))
        .filter(([key]) => !hiddenFields.has(key))
        .filter(([key]) => !this.shouldHideField(key))
        .map(([key, value]) => ({
          key: this.labelForField(key),
          value: this.displayValue(value),
          wide: this.isWideValue(key, value)
        }));
      return [
        ...directRows,
        ...(options.omitPropertyRows
          ? []
          : this.propertyRows(entity, { skipSummaryModels: true })),
        ...this.relationRows(entity, options)
      ]
        .filter((row) => !this.isHiddenRow(row))
        .filter((row) => !this.isLowValuePreviewRow(row))
        .filter((row) => this.matchesSearch([row.key, row.value]));
    },
    shouldSkipNestedEntity(label, entity) {
      const normalizedLabel = this.normalizedDisplayKey(label);
      return normalizedLabel === "assay" && this.isAssayEntity(entity);
    },
    isLowValuePreviewRow(row, parentLabel = "") {
      const rowKey = this.normalizedDisplayKey(row?.key);
      const parentKey = this.normalizedDisplayKey(parentLabel);
      if (this.isRawPropertyNameListRow(row)) return true;
      if (rowKey.startsWith("assay")) return true;
      if (
        parentKey === "dataobject" &&
        this.isRepeatedDataObjectKey(rowKey)
      ) {
        return true;
      }
      return false;
    },
    isRawPropertyNameListRow(row) {
      const rowKey = this.normalizedDisplayKey(row?.key);
      if (!rowKey.endsWith("parametervalue")) return false;
      const values = Array.isArray(row?.value) ? row.value : [row?.value];
      const tokens = values
        .flatMap((value) => {
          if (typeof value === "string") return value.split(/\s*,\s*/);
          return [];
        })
        .map((value) => String(value || "").replace(/^\d+\.\s*/, "").trim())
        .filter(Boolean);
      return (
        tokens.length > 0 &&
        tokens.every((value) => RO_CRATE_PROPERTY_PREFIX_PATTERN.test(value))
      );
    },
    isRepeatedDataObjectKey(rowKey) {
      return [
        "dataobjectassociatedpool",
        "dataobjectderivedfrom",
        "dataobjectlibraryprotocol",
        "dataobjectlibrarytype",
        "dataobjectnucleicacidtype",
        "dataobjectorganism",
        "dataobjectreadlength",
        "dataobjectrequestcontext",
        "dataobjectselectedindexpair",
        "dataobjectsequencedon"
      ].includes(rowKey);
    },
    normalizedDisplayKey(value) {
      return String(value || "")
        .replace(/[^a-z0-9]+/gi, "")
        .toLowerCase();
    },
    relationRows(entity, options = {}) {
      const omittedKeys = new Set(options.omitRelationKeys || []);
      return Object.entries(RO_CRATE_RELATION_FIELDS)
        .filter(([key]) => !omittedKeys.has(key))
        .filter(([key]) => entity?.[key])
        .map(([key, label]) => ({
          key: label,
          value: this.displayValue(entity[key]),
          wide: this.isWideValue(key, entity[key])
        }))
        .filter((row) => !this.isHiddenRow(row));
    },
    backlinkRows(entityId, options = {}) {
      const omittedSourceIds = new Set(options.omitSourceIds || []);
      const backlinks = (this.model?.backlinkMap?.[entityId] || []).filter((link) =>
        RO_CRATE_BACKLINK_PROPERTIES.includes(link.property)
      );
      return backlinks
        .filter((link) => !omittedSourceIds.has(link.sourceId))
        .map((link) => {
          const entity = this.entityById(link.sourceId);
          if (!entity || this.isLowValueBacklink(entity)) return null;
          return {
            key: this.labelForField(link.property),
            value: this.entityLabel(entity),
            wide: false
          };
        })
        .filter(Boolean);
    },
    attachmentsForRequest(requestContextId) {
      return this.model.graph
        .filter((entity) => this.isAttachmentEntity(entity))
        .filter((entity) => {
          if (!requestContextId) return true;
          return this.referenceIds(entity[fieldKeys.requestContext]).includes(
            requestContextId
          );
        })
        .map((entity) => ({
          id: entity[fieldKeys.id],
          name:
            entity[fieldKeys.name] ||
            entity[fieldKeys.contentUrl] ||
            entity[fieldKeys.id],
          contentUrl: entity[fieldKeys.contentUrl]
        }))
        .filter((file) => this.matchesSearch([file.name, file.contentUrl, file.id]));
    },
    isRecordEntity(entity) {
      return this.isRecordId(entity?.[fieldKeys.id]);
    },
    isRecordId(entityId) {
      const id = String(entityId || "");
      return (
        id.startsWith(RO_CRATE_ENTITY_PREFIXES.libraryMaterial) ||
        id.startsWith(RO_CRATE_ENTITY_PREFIXES.sampleMaterial)
      );
    },
    recordType(entity) {
      const id = String(entity?.[fieldKeys.id] || "");
      if (id.startsWith(RO_CRATE_ENTITY_PREFIXES.libraryMaterial)) {
        return RO_CRATE_RECORD_TYPES.library;
      }
      if (id.startsWith(RO_CRATE_ENTITY_PREFIXES.sampleMaterial)) {
        return RO_CRATE_RECORD_TYPES.sample;
      }
      const typeRefs = this.referenceIds(entity?.[fieldKeys.additionalType]);
      if (typeRefs.some((type) => type.includes("/Library"))) {
        return RO_CRATE_RECORD_TYPES.library;
      }
      if (typeRefs.some((type) => type.includes("/Sample"))) {
        return RO_CRATE_RECORD_TYPES.sample;
      }
      return RO_CRATE_RECORD_TYPES.fallback;
    },
    isAttachmentEntity(entity) {
      const types = this.entityTypes(entity);
      return (
        types.includes("MediaObject") &&
        entity?.[fieldKeys.id] !== RO_CRATE_ENTITY_IDS.metadataDescriptor &&
        this.referenceIds(entity?.[fieldKeys.isPartOf]).includes(
          RO_CRATE_ENTITY_IDS.rootDataset
        )
      );
    },
    isLaneEntity(entity) {
      return String(entity?.[fieldKeys.id] || "").startsWith(
        RO_CRATE_ENTITY_PREFIXES.lane
      );
    },
    isProcessEntity(entity) {
      return this.entityTypes(entity).includes("CreateAction");
    },
    isAssayEntity(entity) {
      const id = String(entity?.[fieldKeys.id] || "");
      return id.startsWith(RO_CRATE_ENTITY_PREFIXES.flowcellAssay) ||
        id.startsWith("#sample-assay-") ||
        id.startsWith("#library-assay-");
    },
    isGenericFlowcellDataEntity(entity) {
      const id = String(entity?.[fieldKeys.id] || "");
      return /^#flowcell-data-\d+$/.test(id);
    },
    isLowValueBacklink(entity) {
      const id = String(entity?.[fieldKeys.id] || "");
      return (
        id.startsWith(RO_CRATE_ENTITY_PREFIXES.study) ||
        id.startsWith(RO_CRATE_ENTITY_PREFIXES.sourceSample)
      );
    },
    entityById(entityId) {
      return this.model?.entityMap?.[entityId] || null;
    },
    entityTypes(entity) {
      return Array.isArray(entity?.[fieldKeys.type])
        ? entity[fieldKeys.type]
        : entity?.[fieldKeys.type]
          ? [entity[fieldKeys.type]]
          : [];
    },
    entityLabel(entity) {
      return (
        entity?.[fieldKeys.name] ||
        entity?.[fieldKeys.identifier] ||
        entity?.[fieldKeys.id] ||
        ""
      );
    },
    referenceValues(value) {
      return Array.isArray(value) ? value : value ? [value] : [];
    },
    referenceIds(value) {
      return this.referenceValues(value)
        .flatMap((entry) => {
          if (Array.isArray(entry)) return this.referenceIds(entry);
          if (entry && typeof entry === "object" && entry[fieldKeys.id]) {
            return [String(entry[fieldKeys.id])];
          }
          return [];
        })
        .filter(Boolean);
    },
    resolveReference(value) {
      if (value && typeof value === "object" && value[fieldKeys.id]) {
        return this.entityById(value[fieldKeys.id]) || value;
      }
      return value;
    },
    displayValue(value) {
      if (Array.isArray(value)) {
        return value
          .map((entry) => this.displayValue(entry))
          .filter((entry) => !this.isEmpty(entry));
      }
      if (value && typeof value === "object") {
        if (value[fieldKeys.id]) {
          return this.entityLabel(this.entityById(value[fieldKeys.id]) || value);
        }
        return Object.fromEntries(
          Object.entries(value)
            .map(([key, nestedValue]) => [
              this.labelForField(key),
              this.displayValue(nestedValue)
            ])
            .filter(([, nestedValue]) => !this.isEmpty(nestedValue))
        );
      }
      if (typeof value === "string") {
        const parsed = this.parseStructuredString(value);
        if (parsed) return this.displayValue(parsed);
        const formattedDate = this.formatDate(value);
        return formattedDate || value;
      }
      return value === null || value === undefined || value === "" ? "" : String(value);
    },
    parseStructuredString(value) {
      const text = String(value || "").trim();
      if (!text || !["{", "["].includes(text[0])) return null;
      try {
        const parsed = JSON.parse(text);
        return parsed && typeof parsed === "object" ? parsed : null;
      } catch {
        return null;
      }
    },
    labelForField(field) {
      if (RO_CRATE_PROPERTY_LABEL_OVERRIDES[field]) {
        return RO_CRATE_PROPERTY_LABEL_OVERRIDES[field];
      }
      return String(field || "")
        .replace(RO_CRATE_PROPERTY_PREFIX_PATTERN, "")
        .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
        .replace(/[_-]+/g, " ")
        .replace(/\s+/g, " ")
        .trim()
        .replace(/\b\w/g, (char) => char.toUpperCase());
    },
    groupForProperty(name, entity) {
      const rule = this.modelSectionRuleForProperty(name);
      if (!rule) return "Additional Details";
      return `${rule.modelName}: ${this.entityLabel(entity) || "Record"}`;
    },
    modelSectionTitleForEntity(entity) {
      const firstPropertyName = [
        ...this.referenceValues(entity?.[fieldKeys.additionalProperty]),
        ...this.referenceValues(entity?.[fieldKeys.parameterValue])
      ]
        .map((ref) => this.resolveReference(ref))
        .find((property) => property?.[fieldKeys.name])?.[fieldKeys.name];
      const rule =
        this.modelSectionRuleForProperty(firstPropertyName) ||
        this.modelSectionRuleForEntityId(entity?.[fieldKeys.id]);
      return `${rule?.modelName || "Linked Model"}: ${
        this.entityLabel(entity) || "Record"
      }`;
    },
    modelSectionRuleForProperty(name) {
      const propertyName = String(name || "");
      return RO_CRATE_MODEL_SECTION_RULES.find((rule) =>
        rule.prefixes.some((prefix) => propertyName.startsWith(prefix))
      );
    },
    modelSectionRuleForEntityId(entityId) {
      const id = String(entityId || "");
      const prefixMap = [
        ["#organism-", "Organism"],
        ["#library-type-", "LibraryType"],
        ["#read-length-", "ReadLength"],
        ["#index-type-", "IndexType"],
        ["#nucleic-acid-type-", "NucleicAcidType"],
        ["#protocol-", "LibraryProtocol"],
        ["#index-i7-", "IndexI7"],
        ["#index-i5-", "IndexI5"],
        ["#index-pair-", "IndexPair"],
        ["#index-pool-size-", "PoolSize"],
        ["#index-pool-", "IndexPool"],
        ["#lane-", "Lane"],
        ["#sequencer-", "Sequencer"],
        ["#flowcell-", "Flowcell"]
      ];
      const match = prefixMap.find(([prefix]) => id.startsWith(prefix));
      return match ? { modelName: match[1] } : null;
    },
    isSummaryModelProperty(name) {
      const rule = this.modelSectionRuleForProperty(name);
      return Boolean(rule?.summaryOnly);
    },
    shouldHideField(field) {
      const key = String(field || "");
      const policyKey = normalisePolicyField(key);
      if (
        hiddenFields.has(key) ||
        userHiddenFields.has(key) ||
        hiddenPolicyFields.has(policyKey)
      ) return true;
      if (this.isHiddenCommentField(key)) return true;
      if (RO_CRATE_HIDDEN_FIELD_PATTERNS.some((pattern) => pattern.test(key))) {
        return true;
      }
      const normalised = key.replace(RO_CRATE_PROPERTY_PREFIX_PATTERN, "");
      const normalisedPolicyKey = normalisePolicyField(normalised);
      return (
        hiddenFields.has(normalised) ||
        userHiddenFields.has(normalised) ||
        hiddenPolicyFields.has(normalisedPolicyKey) ||
        this.isHiddenCommentField(normalised) ||
        (/(^|_)id$/i.test(normalised) &&
          !visibleIdFields.has(normalised) &&
          !visibleIdPolicyFields.has(normalisedPolicyKey))
      );
    },
    isHiddenCommentField(field) {
      const normalised = String(field || "")
        .replace(/[^a-z0-9]+/gi, "")
        .toLowerCase();
      return (
        normalised.endsWith("comment") || normalised.endsWith("comments")
      ) && !["usercomment", "usercomments"].includes(normalised);
    },
    isHiddenRow(row) {
      return (
        this.isEmpty(row?.value) ||
        this.shouldHideField(row?.key) ||
        userHiddenFields.has(String(row?.key || ""))
      );
    },
    isEmpty(value) {
      return (
        value === "" ||
        value === null ||
        value === undefined ||
        (Array.isArray(value) && value.length === 0) ||
        (value && typeof value === "object" && !Array.isArray(value) && !Object.keys(value).length)
      );
    },
    isWideValue(key, value) {
      const label = String(key || "").toLowerCase();
      return (
        label.includes("path") ||
        label.includes("flowcell") ||
        Array.isArray(value) ||
        (value && typeof value === "object")
      );
    },
    valueClassForRow(row) {
      const key = String(row?.key || "").toLowerCase();
      return {
        "path-value": key.includes("path"),
        "barcode-value": key.includes("barcode")
      };
    },
    uniqueRows(rows) {
      const seen = new Set();
      return rows.filter((row) => {
        const key = `${row.key}:${JSON.stringify(row.value)}`;
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      });
    },
    matchesSearch(values) {
      if (!this.searchTerm) return true;
      return values.some((value) =>
        JSON.stringify(value ?? "")
          .toLowerCase()
          .includes(this.searchTerm)
      );
    },
    idSuffix(entityId) {
      return String(entityId || "").match(/(\d+)$/)?.[1] || "";
    },
    formatDate(value) {
      const text = String(value || "").trim();
      if (!/^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2})?/.test(text)) return "";
      const date = new Date(text);
      if (Number.isNaN(date.getTime())) return "";
      return new Intl.DateTimeFormat(undefined, {
        day: "2-digit",
        month: "2-digit",
        year: "numeric"
      }).format(date);
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

.upload-stage {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 180px;
  gap: 12px;
  align-items: center;
  border-radius: 24px;
  padding: 20px 24px;
  margin-bottom: 20px;
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

.upload-title-main {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0 0 12px;
  color: #0f2a38;
  font-size: clamp(1.5rem, 3vw, 2.2rem);
  font-weight: 800;
  text-align: left;
}

.upload-title-icon {
  width: 30px;
  height: 30px;
  flex-shrink: 0;
}

.upload-title {
  font-size: 24px;
  font-weight: 800;
  line-height: 1.16;
}

.upload-subtitle {
  margin-top: 10px;
  color: #4d6671;
  line-height: 1.5;
  max-width: 620px;
}

.upload-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  align-items: center;
  margin-top: 14px;
}

.upload-current-file {
  max-width: min(520px, 100%);
  padding: 11px 14px;
  border-radius: 14px;
  background: rgba(228, 240, 243, 0.9);
  color: #214250;
  font-size: 14px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
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
  cursor: pointer;
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

.hero-button:disabled {
  opacity: 0.62;
  cursor: not-allowed;
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
  opacity: 0.12;
  filter: saturate(0.78);
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

.preview-search-panel {
  position: sticky;
  top: 0;
  z-index: 3;
  display: grid;
  grid-template-columns: minmax(220px, 320px) minmax(0, 1fr);
  gap: 18px;
  align-items: center;
  margin-bottom: 18px;
  padding: 14px 18px;
  border: 1px solid rgba(13, 111, 115, 0.24);
  border-radius: 0 0 14px 14px;
  background: rgba(243, 250, 251, 0.98);
  box-shadow: 0 10px 24px rgba(16, 36, 47, 0.08);
}

.preview-search-title {
  color: #173948;
  font-size: 16px;
  font-weight: 800;
}

.preview-search-meta {
  margin-top: 3px;
  color: #5e7884;
  font-size: 13px;
  line-height: 1.35;
}

.table-search-input-wrap {
  position: relative;
}

.table-search-input {
  width: 100%;
  border: 2px solid rgba(13, 111, 115, 0.36);
  border-radius: 0 0 14px 14px;
  padding: 13px 44px 13px 14px;
  font-size: 15px;
  color: #173948;
  background: rgba(255, 255, 255, 0.96);
}

.table-search-icon {
  position: absolute;
  top: 50%;
  right: 14px;
  transform: translateY(-50%);
  color: #0d6f73;
}

.detail-card {
  border-radius: 22px;
  padding: 18px;
  margin-bottom: 18px;
}

.detail-kicker {
  display: inline-block;
  margin-bottom: 8px;
  font-size: 18px;
  font-weight: 800;
  color: #173948;
}

.request-overview-list,
.record-table-list,
.attachment-list,
.zip-content-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 14px;
}

.request-overview-item,
.record-table-block,
.attachment-item,
.zip-content-row {
  min-width: 0;
  padding: 14px 16px;
  border-radius: 16px;
  background: linear-gradient(180deg, rgba(248, 251, 252, 0.96), rgba(255, 255, 255, 0.96));
  border: 1px solid rgba(16, 36, 47, 0.06);
}

.request-overview-title,
.record-table-title {
  color: #173948;
  font-size: 16px;
  font-weight: 800;
}

.record-table-subtitle {
  margin-top: 4px;
  color: #5c7784;
}

.record-chip-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}

.record-chip {
  display: inline-flex;
  max-width: 100%;
  border-radius: 999px;
  padding: 7px 10px;
  background: rgba(13, 111, 115, 0.08);
  color: #0d6f73;
  font-size: 12px;
  font-weight: 800;
  overflow-wrap: anywhere;
}

.record-group {
  margin-top: 16px;
}

.record-group.nested {
  margin-top: 14px;
}

.record-group-title,
.quick-summary-key {
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: #5e7884;
}

.record-group-title {
  margin-bottom: 8px;
  color: #1d5f78;
}

.quick-summary-table {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px 18px;
}

.quick-summary-row {
  display: grid;
  grid-template-columns: 112px minmax(0, 1fr);
  gap: 12px;
  align-items: start;
  padding: 14px 16px;
  border-radius: 16px;
  background: linear-gradient(180deg, rgba(248, 251, 252, 0.96), rgba(255, 255, 255, 0.96));
  border: 1px solid rgba(16, 36, 47, 0.06);
}

.quick-summary-row.wide-row {
  grid-column: 1 / -1;
  grid-template-columns: 112px minmax(0, 1fr);
}

.quick-summary-value {
  color: #173948;
  line-height: 1.55;
  overflow-wrap: anywhere;
}

.quick-summary-value.path-value {
  word-break: break-word;
}

.quick-summary-value :deep(.structured-value-list) {
  margin: 0;
  padding-left: 18px;
}

.quick-summary-value :deep(.structured-value-scroll) {
  max-width: 100%;
  overflow-x: auto;
}

.quick-summary-value :deep(.structured-value-table) {
  width: 100%;
  min-width: 320px;
  border-collapse: collapse;
  font-size: 13px;
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
  width: 180px;
  background: rgba(231, 240, 242, 0.86);
  color: #244858;
  font-weight: 800;
}

.quick-summary-value :deep(.structured-value-table.indexed-table th) {
  width: auto;
}

.quick-summary-value :deep(.structured-value-table .row-number-column) {
  width: 42px;
  text-align: right;
  white-space: nowrap;
  color: #5e7884;
}

.attachment-item,
.zip-content-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.attachment-item svg,
.zip-content-row svg {
  margin-top: 2px;
  color: #0d6f73;
  flex-shrink: 0;
}

.zip-content-path {
  font-weight: 700;
  overflow-wrap: anywhere;
}

.zip-content-meta,
.empty-inline {
  color: #65818c;
  line-height: 1.5;
}

.zip-content-meta {
  margin-top: 3px;
  font-size: 12px;
}

.print-report-header,
.print-report-footer {
  display: none;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 760px) {
  .rocrate-preview-shell {
    padding: 20px 14px 40px;
  }

  .upload-stage,
  .quick-summary-table,
  .preview-search-panel {
    grid-template-columns: 1fr;
  }

  .upload-watermark {
    display: none;
  }

  .quick-summary-row,
  .quick-summary-row.wide-row {
    grid-template-columns: 1fr;
  }
}

@media print {
  @page {
    size: A4;
    margin: 12mm 9mm 11mm;
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

  .rocrate-preview-page,
  .rocrate-preview-page.embedded {
    min-height: auto;
    height: auto;
    overflow: visible;
    background: #fff;
    color: #10242f;
    font-size: 9pt;
  }

  .rocrate-preview-shell,
  .rocrate-preview-page.embedded .rocrate-preview-shell {
    max-width: none;
    padding: 0;
    margin: 0;
  }

  .upload-stage,
  .preview-search-panel,
  .pdf-export-button {
    display: none !important;
  }

  .print-report-header {
    display: flex;
    justify-content: space-between;
    gap: 8mm;
    margin-bottom: 3mm;
    padding-bottom: 2mm;
    border-bottom: 1px solid #d8e0e4;
  }

  .print-report-title {
    font-size: 9pt;
    font-weight: 800;
  }

  .print-report-subtitle,
  .print-report-meta {
    color: #5e7884;
    font-size: 7pt;
    line-height: 1.3;
  }

  .print-report-footer {
    display: block;
    margin-top: 4mm;
    padding-top: 2mm;
    border-top: 1px solid #d8e0e4;
    color: #6b818c;
    font-size: 6.5pt;
  }

  .detail-card {
    padding: 2.5mm 0;
    margin-bottom: 3mm;
    border-radius: 0;
    box-shadow: none;
    border: 0;
    border-top: 1px solid #d8e0e4;
    background: #fff;
  }

  .quick-summary-table {
    display: block !important;
  }

  .quick-summary-row,
  .quick-summary-row.wide-row {
    display: grid;
    grid-template-columns: 38mm minmax(0, 1fr);
    gap: 2mm;
    margin-bottom: 1.4mm;
    padding: 1.8mm;
    border-radius: 1.5mm;
    background: #fff;
    break-inside: avoid;
    page-break-inside: avoid;
  }

  .quick-summary-key {
    font-size: 7.2pt;
    line-height: 1.2;
    overflow-wrap: anywhere;
  }

  .request-overview-item,
  .attachment-item,
  .zip-content-row {
    break-inside: avoid;
    page-break-inside: avoid;
  }

  .quick-summary-value,
  .quick-summary-value :deep(.structured-value-table) {
    font-size: 7.2pt;
    line-height: 1.25;
  }

  .quick-summary-value :deep(.structured-value-scroll) {
    overflow: visible;
  }
}
</style>

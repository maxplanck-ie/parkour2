<template>
  <div class="rocrate-preview-page">
    <div class="rocrate-preview-shell">
      <section v-if="model" class="preview-action-bar">
        <div class="preview-action-copy">
          <div class="preview-action-title">RO-Crate export</div>
          <div class="preview-action-subtitle">
            {{ labels.loadedSubtitle }}
          </div>
        </div>
        <div class="preview-actions">
          <div v-if="model?.source?.name" class="preview-output-file">
            <span class="preview-output-file-label">ZIP output:</span>
            <span class="preview-output-file-name">
              {{ model.source.name }}
            </span>
          </div>
          <button
            class="preview-action-button secondary"
            type="button"
            data-testid="export-ro-crate-pdf-button"
            title="Download this preview as a PDF"
            :disabled="pdfBusy || !canExportPreview"
            @click="exportToPdf"
          >
            <font-awesome-icon icon="fa-solid fa-download" />
            {{ pdfBusy ? "Exporting..." : "Export Preview" }}
          </button>
          <button
            class="preview-action-button primary"
            type="button"
            title="Download the selected records as an RO-Crate ZIP"
            :disabled="exportBusy || !canExportPreview"
            @click="exportROCrate"
          >
            <font-awesome-icon icon="fa-solid fa-download" />
            {{ exportBusy ? "Exporting..." : "Export RO-Crate" }}
          </button>
          <a
            class="preview-action-button secondary"
            href="https://www.researchobject.org/ro-crate/specification/1.1/introduction.html"
            target="_blank"
            rel="noopener noreferrer"
            title="Open the RO-Crate documentation in a new tab"
          >
            <font-awesome-icon icon="fa-solid fa-file-lines" />
            RO-Crate Documentation
          </a>
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
          skipped because RO-Crate export requires Sequencing or Delivered
          status:
          {{ skippedRecords.join(", ") }}
        </span>
      </div>

      <section v-if="model">
        <section
          class="detail-card request-overview-card"
          aria-label="Selected libraries and samples"
        >
          <div class="detail-header">
            <div class="detail-kicker">
              <font-awesome-icon
                class="detail-kicker-icon"
                icon="fa-solid fa-layer-group"
              />
              <span>Selected Libraries &amp; Samples</span>
            </div>
          </div>
          <div v-if="visibleRequestGroups.length" class="request-overview-list">
            <article
              v-for="request in visibleRequestGroups"
              :key="`overview-${request.id}`"
              class="request-overview-item"
            >
              <div class="request-overview-title">
                <ROCrateHighlightedText
                  :value="request.name"
                  :search-tokens="searchTokens"
                />
              </div>
              <div v-if="request.records.length" class="record-chip-list">
                <button
                  v-for="record in request.records"
                  :key="`overview-${request.id}-${record.id}`"
                  class="record-chip"
                  type="button"
                  :title="`Go to ${record.type.toLowerCase()} ${record.name}`"
                  @click="scrollToRecord(request.id, record.id)"
                >
                  <template v-if="record.barcode">
                    <span class="record-chip-barcode">
                      <ROCrateHighlightedText
                        :value="record.barcode"
                        :search-tokens="searchTokens"
                      />
                    </span>
                    <span class="record-chip-separator">:</span>
                  </template>
                  <ROCrateHighlightedText
                    :value="record.name"
                    :search-tokens="searchTokens"
                  />
                </button>
              </div>
              <div v-else class="empty-inline">{{ labels.noRecords }}</div>
            </article>
          </div>
        </section>

        <section
          class="preview-search-panel"
          aria-label="Search RO-Crate preview"
        >
          <div class="preview-search-copy">
            <div class="preview-search-title">Search Preview</div>
            <div class="preview-search-meta">{{ searchResultSummary }}</div>
          </div>
          <div class="preview-search-controls">
            <div class="table-search-input-wrap">
              <input
                ref="previewSearchInput"
                v-model="searchInput"
                class="table-search-input"
                type="search"
                placeholder="Search by request, record, barcode, or value"
                @keydown.enter.prevent="
                  navigateSearchResults($event.shiftKey ? -1 : 1)
                "
                @keydown.esc.prevent="clearSearch"
              />
              <button
                v-if="searchInput"
                class="table-search-clear"
                type="button"
                aria-label="Clear preview search"
                title="Clear search"
                @click="clearSearch"
              >
                <font-awesome-icon icon="fa-solid fa-xmark" />
              </button>
              <font-awesome-icon
                class="table-search-icon"
                icon="fa-solid fa-magnifying-glass"
              />
            </div>
            <div
              v-if="searchMatchRecords.length"
              class="preview-search-navigation"
              aria-label="Search result navigation"
            >
              <button
                type="button"
                title="Previous matching record (Shift+Enter)"
                aria-label="Previous matching record"
                @click="navigateSearchResults(-1)"
              >
                <font-awesome-icon icon="fa-solid fa-angle-left" />
              </button>
              <span>{{ activeSearchResultLabel }}</span>
              <button
                type="button"
                title="Next matching record (Enter)"
                aria-label="Next matching record"
                @click="navigateSearchResults(1)"
              >
                <font-awesome-icon icon="fa-solid fa-angle-right" />
              </button>
            </div>
          </div>
        </section>

        <section
          v-for="(request, index) in visibleRequestGroups"
          :key="request.id"
          class="detail-card request-card"
        >
          <div class="detail-header">
            <div>
              <div class="detail-kicker">
                <font-awesome-icon
                  class="detail-kicker-icon"
                  icon="fa-solid fa-folder-open"
                />
                <span>Request {{ index + 1 }}:</span>
                <ROCrateHighlightedText
                  :value="request.name"
                  :search-tokens="searchTokens"
                />
              </div>
            </div>
          </div>

          <section v-if="request.requestRows.length" class="record-group">
            <div class="record-group-title">Request Details</div>
            <div class="quick-summary-table">
              <div
                v-for="row in request.requestRows"
                :key="`${request.id}-request-${row.key}`"
                class="quick-summary-row"
                :class="{ 'wide-row': row.wide }"
              >
                <div class="quick-summary-key">{{ row.key }}</div>
                <div class="quick-summary-value" :class="valueClassForRow(row)">
                  <ROCrateDisplayValue
                    :value="row.value"
                    :search-tokens="searchTokens"
                  />
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
                :id="recordAnchorId(request.id, record.id)"
                tabindex="-1"
              >
                <div class="record-table-header">
                  <div class="record-table-heading">
                    <font-awesome-icon
                      class="record-table-title-icon"
                      icon="fa-solid fa-flask"
                    />
                    <div>
                      <div class="record-table-title">
                        {{ record.type }}:
                        <ROCrateHighlightedText
                          :value="record.name"
                          :search-tokens="searchTokens"
                        />
                      </div>
                      <div v-if="record.barcode" class="record-table-subtitle">
                        Barcode:
                        <ROCrateHighlightedText
                          :value="record.barcode"
                          :search-tokens="searchTokens"
                        />
                      </div>
                    </div>
                  </div>
                </div>
                <section
                  v-for="section in record.sections"
                  :key="`${record.id}-${section.title}`"
                  class="record-group nested"
                >
                  <div class="record-group-title">{{ section.title }}</div>
                  <div class="record-card-grid">
                    <div
                      v-for="row in section.rows"
                      :key="`${record.id}-${section.title}-${row.key}`"
                      class="record-data-card"
                    >
                      <div class="record-data-key">{{ row.key }}</div>
                      <div
                        class="record-data-value"
                        :class="valueClassForRow(row)"
                      >
                        <ROCrateDisplayValue
                          :value="row.value"
                          :search-tokens="searchTokens"
                        />
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
                <ROCrateHighlightedText
                  :value="file.name"
                  :search-tokens="searchTokens"
                />
              </div>
            </div>
          </section>
        </section>
      </section>
    </div>
  </div>
</template>

<script>
import { h } from "vue";
import { saveAs } from "file-saver";
import {
  RO_CRATE_ENDPOINT,
  RO_CRATE_ENTITY_IDS,
  RO_CRATE_ENTITY_PREFIXES,
  RO_CRATE_FIELD_KEYS,
  RO_CRATE_PREPARATION_CARD_FIELDS,
  RO_CRATE_PREVIEW_LABELS,
  RO_CRATE_RECORD_TYPES,
  RO_CRATE_REQUEST_DETAIL_FIELDS,
  RO_CRATE_SEQUENCING_CARD_FIELDS
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
const RO_CRATE_SEARCH_DEBOUNCE_MS = 250;
const RO_CRATE_EXPORT_FILENAME_MAX_LENGTH = 50;

function uniqueSearchTokens(tokens) {
  return [
    ...new Set(
      (tokens || [])
        .map((token) =>
          String(token || "")
            .trim()
            .toLowerCase()
        )
        .filter(Boolean)
    )
  ];
}

function escapedRegExp(value) {
  return String(value).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function highlightedTextNodes(value, tokens) {
  const text = String(value ?? "");
  const normalizedTokens = uniqueSearchTokens(tokens).sort(
    (left, right) => right.length - left.length
  );
  if (!text || !normalizedTokens.length) return [text];

  const tokenPattern = new RegExp(
    `(${normalizedTokens.map(escapedRegExp).join("|")})`,
    "gi"
  );
  const tokenSet = new Set(normalizedTokens);
  return text
    .split(tokenPattern)
    .filter((part) => part !== "")
    .map((part, index) =>
      tokenSet.has(part.toLowerCase())
        ? h("mark", { class: "search-match-highlight", key: index }, part)
        : part
    );
}

const HighlightedText = {
  name: "ROCrateHighlightedText",
  props: {
    value: {
      type: [String, Number, Boolean],
      default: ""
    },
    searchTokens: {
      type: Array,
      default: () => []
    }
  },
  render() {
    return h("span", highlightedTextNodes(this.value, this.searchTokens));
  }
};

const DisplayValue = {
  name: "ROCrateDisplayValue",
  props: {
    value: {
      type: [String, Number, Boolean, Array, Object],
      default: ""
    },
    searchTokens: {
      type: Array,
      default: () => []
    }
  },
  methods: {
    isObject(value) {
      return value && typeof value === "object" && !Array.isArray(value);
    },
    renderPrimitive(value) {
      return h("span", highlightedTextNodes(value ?? "-", this.searchTokens));
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
        values.map((value, index) =>
          h("li", { key: index }, this.renderAny(value))
        )
      );
    },
    renderObjectTable(values) {
      const columns = [
        ...new Set(values.flatMap((value) => Object.keys(value || {})))
      ];
      return h(
        "div",
        { class: "structured-value-scroll" },
        h("table", { class: "structured-value-table indexed-table" }, [
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
        ])
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
    ROCrateDisplayValue: DisplayValue,
    ROCrateHighlightedText: HighlightedText
  },
  props: {
    previewConfig: {
      type: Object,
      default: null
    }
  },
  data() {
    return {
      loading: false,
      errorMessage: "",
      model: null,
      searchInput: "",
      debouncedSearchInput: "",
      searchDebounceTimer: null,
      activeSearchResultIndex: -1,
      activePreviewConfig: null,
      exportBusy: false,
      pdfBusy: false,
      skippedRecords: []
    };
  },
  computed: {
    labels() {
      return RO_CRATE_PREVIEW_LABELS;
    },
    canExportPreview() {
      const identifiers = this.previewIdentifierValues(
        this.activePreviewConfig
      );
      return identifiers.barcodes.length > 0 || identifiers.requests.length > 0;
    },
    searchTokens() {
      return uniqueSearchTokens(
        String(this.debouncedSearchInput || "").split(/\s+/)
      );
    },
    searchMatchRecords() {
      if (!this.searchTokens.length) return [];
      return this.visibleRequestGroups.flatMap((request) =>
        request.records.map((record) => ({
          requestId: request.id,
          recordId: record.id
        }))
      );
    },
    activeSearchResultLabel() {
      if (!this.searchMatchRecords.length) return "";
      const activePosition =
        this.activeSearchResultIndex >= 0
          ? this.activeSearchResultIndex + 1
          : "–";
      return `${activePosition} / ${this.searchMatchRecords.length}`;
    },
    searchResultSummary() {
      if (!this.searchTokens.length) {
        return "Search visible requests, records, barcodes, and values.";
      }
      const requestCount = this.visibleRequestGroups.length;
      const requestLabel = requestCount === 1 ? "request" : "requests";
      const recordCount = this.searchMatchRecords.length;
      const recordLabel = recordCount === 1 ? "record" : "records";
      return (
        `${recordCount} ${recordLabel} in ${requestCount} ${requestLabel} ` +
        `match "${this.debouncedSearchInput.trim()}"`
      );
    },
    rootEntity() {
      return this.entityById(RO_CRATE_ENTITY_IDS.rootDataset);
    },
    requestGroups() {
      if (!this.model) return [];
      const studies = this.previewStudies();
      const groups = studies.map((study, index) =>
        this.buildRequestGroup(study, index)
      );
      if (groups.length) return groups;
      return [this.buildFallbackRequestGroup()];
    },
    visibleRequestGroups() {
      if (!this.searchTokens.length) return this.requestGroups;
      return this.requestGroups
        .map((request) => ({
          ...request,
          records: request.records.filter((record) =>
            this.matchesSearch([
              request.name,
              record.name,
              record.barcode,
              ...record.sections.flatMap((section) =>
                section.rows.map((row) => row.value)
              )
            ])
          ),
          requestRows: request.requestRows.filter((row) =>
            this.matchesSearch([request.name, row.value])
          ),
          attachments: request.attachments.filter((file) =>
            this.matchesSearch([request.name, file.name, file.contentUrl])
          )
        }))
        .filter(
          (request) =>
            this.matchesSearch([request.name]) ||
            request.records.length ||
            request.requestRows.length ||
            request.attachments.length
        );
    }
  },
  watch: {
    searchInput(newValue) {
      window.clearTimeout(this.searchDebounceTimer);

      if (!newValue) {
        this.debouncedSearchInput = "";
        this.activeSearchResultIndex = -1;
        return;
      }

      this.searchDebounceTimer = window.setTimeout(() => {
        this.debouncedSearchInput = newValue.trim();
        this.activeSearchResultIndex = -1;
      }, RO_CRATE_SEARCH_DEBOUNCE_MS);
    },
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
  beforeUnmount() {
    window.clearTimeout(this.searchDebounceTimer);
  },
  methods: {
    clearSearch() {
      window.clearTimeout(this.searchDebounceTimer);
      this.searchInput = "";
      this.debouncedSearchInput = "";
      this.activeSearchResultIndex = -1;
      this.$nextTick(() => this.$refs.previewSearchInput?.focus());
    },
    navigateSearchResults(direction = 1) {
      const pendingSearch = this.searchInput.trim();
      if (pendingSearch !== this.debouncedSearchInput) {
        window.clearTimeout(this.searchDebounceTimer);
        this.debouncedSearchInput = pendingSearch;
        this.activeSearchResultIndex = -1;
        this.$nextTick(() => this.navigateSearchResults(direction));
        return;
      }

      const matches = this.searchMatchRecords;
      if (!matches.length) return;
      const nextIndex =
        this.activeSearchResultIndex < 0
          ? direction < 0
            ? matches.length - 1
            : 0
          : (this.activeSearchResultIndex + direction + matches.length) %
            matches.length;
      this.activeSearchResultIndex = nextIndex;
      const match = matches[nextIndex];
      this.scrollToRecord(match.requestId, match.recordId);
    },
    recordAnchorId(requestId, recordId) {
      const anchorKey = `${requestId}-${recordId}`
        .replace(/[^a-z0-9_-]+/gi, "-")
        .replace(/^-+|-+$/g, "");
      return `ro-crate-record-${anchorKey}`;
    },
    scrollToRecord(requestId, recordId) {
      this.$nextTick(() => {
        const recordElement = document.getElementById(
          this.recordAnchorId(requestId, recordId)
        );
        if (!recordElement) return;
        const searchPanel = this.$el.querySelector(".preview-search-panel");
        const searchPanelOffset = searchPanel
          ? Math.ceil(searchPanel.getBoundingClientRect().height) + 18
          : 96;
        recordElement.style.scrollMarginTop = `${searchPanelOffset}px`;
        recordElement.scrollIntoView({
          behavior: "smooth",
          block: "start"
        });
        recordElement.focus({ preventScroll: true });
      });
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
      const identifiers = this.previewIdentifierValues(
        this.activePreviewConfig
      );
      const params = { ...extra };
      if (identifiers.barcodes.length)
        params.barcodes = identifiers.barcodes.join(",");
      if (identifiers.requests.length)
        params.requests = identifiers.requests.join(",");
      return params;
    },
    async loadPreviewFromConfig(previewConfig) {
      const identifiers = this.previewIdentifierValues(previewConfig);
      if (!identifiers.barcodes.length && !identifiers.requests.length) {
        this.errorMessage =
          "Select at least one library or sample before previewing an RO-Crate.";
        return;
      }

      this.activePreviewConfig = { ...previewConfig };
      this.loading = true;
      this.errorMessage = "";
      this.model = null;

      try {
        const response = await axiosRef.get(
          `${urlStringStart}${RO_CRATE_ENDPOINT}`,
          {
            params: this.roCrateRequestParams({ preview: "true" })
          }
        );
        const payload = response?.data || {};
        this.skippedRecords = Array.isArray(payload.skipped_records)
          ? payload.skipped_records
          : [];
        if (!payload.ro_crate) {
          throw new Error(
            "The RO-Crate preview response did not include ro_crate."
          );
        }
        if (!payload.archive_name) {
          throw new Error(
            "The RO-Crate preview response did not include archive_name."
          );
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
        const response = await axiosRef.get(
          `${urlStringStart}${RO_CRATE_ENDPOINT}`,
          {
            params: this.roCrateRequestParams(),
            responseType: "blob"
          }
        );
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
      if (!this.canExportPreview) {
        showNotification(
          "Open a Parkour RO-Crate preview before exporting the PDF.",
          "warning"
        );
        return;
      }
      try {
        this.pdfBusy = true;
        const response = await axiosRef.get(
          `${urlStringStart}${RO_CRATE_ENDPOINT}`,
          {
            params: this.roCrateRequestParams({ pdf: "true" }),
            responseType: "blob"
          }
        );
        const filename =
          this.parseContentDispositionFilename(
            this.responseHeader(response?.headers, "content-disposition")
          ) || this.fallbackPdfFilename();
        saveAs(response?.data, filename);
        showNotification("PDF exported successfully.", "success");
      } catch (error) {
        handleError(error);
      } finally {
        this.pdfBusy = false;
      }
    },
    fallbackArchiveFilename() {
      const previewName = this.model?.source?.name || "";
      if (previewName.toLowerCase().endsWith(".zip")) {
        return this.boundedExportFilename(
          this.sanitizeFilenamePart(previewName).replace(/\.zip$/i, ""),
          ".zip"
        );
      }
      const requestIds = this.previewRequestIds();
      if (requestIds.length) {
        return this.boundedExportFilename(
          `${requestIds.join("_")}_ro_crate`,
          ".zip"
        );
      }
      return this.boundedExportFilename("parkour_ro_crate", ".zip");
    },
    fallbackPdfFilename() {
      const archiveName = this.fallbackArchiveFilename();
      const archiveBase = archiveName
        .replace(/\.(zip|pdf)$/i, "")
        .replace(/_ro_crate$/i, "");
      return this.boundedExportFilenameWithSuffix(
        archiveBase,
        "ro_crate_preview",
        ".pdf"
      );
    },
    boundedExportFilenameWithSuffix(baseName, semanticSuffix, extension) {
      const suffix = extension.startsWith(".") ? extension : `.${extension}`;
      const safeSemanticSuffix = this.sanitizeFilenamePart(semanticSuffix);
      const separator = "_";
      const maxBaseLength = Math.max(
        1,
        RO_CRATE_EXPORT_FILENAME_MAX_LENGTH -
          separator.length -
          safeSemanticSuffix.length -
          suffix.length
      );
      const safeBase =
        this.sanitizeFilenamePart(baseName)
          .slice(0, maxBaseLength)
          .replace(/[._-]+$/g, "") || "parkour";
      return `${safeBase}${separator}${safeSemanticSuffix}${suffix}`;
    },
    boundedExportFilename(baseName, extension) {
      const suffix = extension.startsWith(".") ? extension : `.${extension}`;
      const maxBaseLength = Math.max(
        1,
        RO_CRATE_EXPORT_FILENAME_MAX_LENGTH - suffix.length
      );
      const safeBase =
        this.sanitizeFilenamePart(baseName)
          .slice(0, maxBaseLength)
          .replace(/[._-]+$/g, "") || "parkour_ro_crate";
      return `${safeBase}${suffix}`;
    },
    previewRequestIds() {
      const configuredIds = Array.isArray(this.activePreviewConfig?.requestIds)
        ? this.activePreviewConfig.requestIds
        : [];
      const graphIds = this.requestGroups
        .map((request) => request.requestNumber)
        .filter(Boolean);
      return [
        ...new Set([...configuredIds, ...graphIds].map(String).filter(Boolean))
      ];
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
    previewStudies() {
      if (!this.model) return [];
      return this.model.graph.filter((entity) =>
        String(entity?.[fieldKeys.id] || "").startsWith(
          RO_CRATE_ENTITY_PREFIXES.study
        )
      );
    },
    buildRequestGroup(study, index) {
      const studyId = study?.[fieldKeys.id] || `request-${index + 1}`;
      const requestNumber = this.idSuffix(studyId);
      const requestEntity = this.entityById(
        `${RO_CRATE_ENTITY_PREFIXES.requestContext}${requestNumber}`
      );
      const recordIds = this.previewRecordIds(this.studyRecordIds(study));
      const records = recordIds
        .map((recordId, recordIndex) => this.buildRecord(recordId, recordIndex))
        .filter(Boolean)
        .sort((left, right) => left.name.localeCompare(right.name));

      return {
        id: studyId,
        requestNumber,
        name:
          requestEntity?.[fieldKeys.name] ||
          study?.[fieldKeys.name] ||
          `${RO_CRATE_PREVIEW_LABELS.unnamedRequest} ${index + 1}`,
        requestRows: this.requestDetailRows(requestEntity),
        records,
        attachments: this.attachmentsForRequest(requestEntity?.[fieldKeys.id])
      };
    },
    buildFallbackRequestGroup() {
      const records = this.model.graph
        .filter((entity) => this.isRecordEntity(entity))
        .sort((left, right) =>
          this.recordSortLabel(left[fieldKeys.id]).localeCompare(
            this.recordSortLabel(right[fieldKeys.id])
          )
        )
        .map((entity, recordIndex) =>
          this.buildRecord(entity[fieldKeys.id], recordIndex)
        )
        .filter(Boolean)
        .sort((left, right) => left.name.localeCompare(right.name));
      return {
        id: "fallback-request",
        requestNumber: "",
        name:
          this.rootEntity?.[fieldKeys.name] ||
          this.activePreviewConfig?.requestName ||
          RO_CRATE_PREVIEW_LABELS.unnamedRequest,
        requestRows: this.requestDetailRows(this.rootEntity),
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
      return this.referenceIds(study?.hasPart).filter((id) =>
        this.isRecordId(id)
      );
    },
    previewRecordIds(recordIds) {
      return [...new Set(recordIds)].sort((left, right) =>
        this.recordSortLabel(left).localeCompare(this.recordSortLabel(right))
      );
    },
    recordSortLabel(recordId) {
      const entity = this.entityById(recordId);
      return String(
        entity?.[fieldKeys.identifier] ||
          entity?.[fieldKeys.name] ||
          recordId ||
          ""
      );
    },
    buildRecord(recordId, recordIndex = 0) {
      const entity = this.entityById(recordId);
      if (!entity) return null;
      const type = this.recordType(entity);
      const recordName =
        entity[fieldKeys.name] ||
        entity[fieldKeys.identifier] ||
        RO_CRATE_PREVIEW_LABELS.unnamedRecord;
      const metadata = this.recordMaterializedViewMetadata(
        recordId,
        entity,
        type
      );
      const cardContext = {
        entity,
        metadata,
        type,
        recordIndex
      };

      return {
        id: recordId,
        type,
        name: recordName,
        barcode: this.formattedBarcode(entity[fieldKeys.identifier], type, ""),
        sections: [
          {
            title: "Preparation",
            rows: this.recordCardRows(
              RO_CRATE_PREPARATION_CARD_FIELDS,
              cardContext
            )
          },
          {
            title: "Sequencing",
            rows: this.recordCardRows(
              RO_CRATE_SEQUENCING_CARD_FIELDS,
              cardContext
            )
          }
        ]
      };
    },
    recordMaterializedViewMetadata(recordId, entity, type) {
      const prefix =
        type === RO_CRATE_RECORD_TYPES.library ? "library_mv_" : "sample_mv_";
      const metadata = new Map();
      [entity, ...this.recordProcessEntities(recordId)].forEach(
        (sourceEntity) => {
          const properties = [
            ...this.referenceValues(
              sourceEntity?.[fieldKeys.additionalProperty]
            ),
            ...this.referenceValues(sourceEntity?.[fieldKeys.parameterValue])
          ]
            .map((reference) => this.resolveReference(reference))
            .filter(Boolean);
          properties.forEach((property) => {
            const name = String(property?.[fieldKeys.name] || "");
            if (!name.startsWith(prefix) || metadata.has(name)) return;
            metadata.set(name, property?.[fieldKeys.value]);
          });
        }
      );
      return {
        prefix,
        values: metadata
      };
    },
    recordCardRows(fields, context) {
      return fields.map((field) => ({
        key: field.label,
        value: this.recordCardValue(field.key, context)
      }));
    },
    recordCardValue(field, context) {
      const { entity, metadata, type, recordIndex } = context;
      const readValue = (key) =>
        metadata.values.get(`${metadata.prefix}${key}`);
      const rawValue = readValue(field);

      if (field === "name") {
        return entity?.[fieldKeys.name] || "-";
      }
      if (field === "barcode") {
        return this.formattedBarcode(entity?.[fieldKeys.identifier], type);
      }
      if (field === "well_position") {
        return this.plateCoordinate(recordIndex);
      }
      if (field === "gmo") {
        if (type === RO_CRATE_RECORD_TYPES.library) return "No";
        if (rawValue === true) return "Yes";
        if (rawValue === false) return "No";
        return "-";
      }
      if (field === "nucleic_acid_type_name" && this.isEmpty(rawValue)) {
        return "No Input Type";
      }
      if (field === "library_protocol_name" && this.isEmpty(rawValue)) {
        return "No Protocol";
      }
      if (field === "analysis_type_name" && this.isEmpty(rawValue)) {
        return "No Analysis Type";
      }
      if (field === "input") {
        return this.inputCardValue(
          readValue("measured_value"),
          readValue("measuring_unit")
        );
      }
      if (field === "create_time") {
        return this.formatDate(rawValue) || this.cardDisplayValue(rawValue);
      }
      if (field === "starting_amount") {
        return this.fixedCardNumber(rawValue, 1);
      }
      if (field === "concentration_library") {
        return this.fixedCardNumber(rawValue, Number(rawValue) === 0 ? 1 : 3);
      }
      if (
        ["pcr_cycles", "average_fragment_size", "sequencing_depth"].includes(
          field
        )
      ) {
        return this.roundedCardNumber(rawValue);
      }
      return this.cardDisplayValue(rawValue);
    },
    inputCardValue(value, unit) {
      if (Number(value) === -1 && unit === "Unknown") return "Unknown";
      const displayedValue = this.cardDisplayValue(value, "");
      const displayedUnit = this.cardDisplayValue(unit, "");
      if (!displayedValue && !displayedUnit) return "-";
      if (!displayedValue) return displayedUnit;
      if (!displayedUnit) return displayedValue;
      return `${displayedValue} ${displayedUnit}`;
    },
    formattedBarcode(value, recordType, emptyValue = "-") {
      const barcode = String(value || "");
      if (!barcode) return emptyValue;
      return recordType === RO_CRATE_RECORD_TYPES.sample && barcode[2] === "L"
        ? `${barcode}*`
        : barcode;
    },
    fixedCardNumber(value, decimalPlaces) {
      const number = Number(value);
      if (this.isEmpty(value) || !Number.isFinite(number)) return "-";
      return number.toFixed(decimalPlaces);
    },
    roundedCardNumber(value) {
      const number = Number(value);
      if (this.isEmpty(value) || !Number.isFinite(number)) return "-";
      return String(Math.round(number));
    },
    cardDisplayValue(value, emptyValue = "-") {
      if (this.isEmpty(value)) return emptyValue;
      if (Array.isArray(value)) {
        return value.length ? value.join(", ") : emptyValue;
      }
      if (value === true) return "Yes";
      if (value === false) return "No";
      return String(value);
    },
    plateCoordinate(recordIndex) {
      const index = Number(recordIndex) % 96;
      const row = String.fromCharCode(65 + (index % 8));
      const column = Math.floor(index / 8) + 1;
      return `${row}${column}`;
    },
    requestDetailRows(entity) {
      if (!entity) return [];
      const refs = [
        ...this.referenceValues(entity?.[fieldKeys.additionalProperty]),
        ...this.referenceValues(entity?.[fieldKeys.parameterValue])
      ];
      const propertiesByName = new Map(
        refs
          .map((ref) => this.resolveReference(ref))
          .filter((property) => property?.[fieldKeys.name])
          .map((property) => [property[fieldKeys.name], property])
      );
      return RO_CRATE_REQUEST_DETAIL_FIELDS.map(({ key, label }) => {
        const rawValue = ["name", "description"].includes(key)
          ? entity[key]
          : propertiesByName.get(key)?.[fieldKeys.value];
        const value = this.displayValue(rawValue);
        if (this.isEmpty(value)) return null;
        return {
          key: label,
          value,
          wide: key.endsWith("paths")
        };
      }).filter(Boolean);
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
        }));
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
    isProcessEntity(entity) {
      return this.entityTypes(entity).includes("CreateAction");
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
          return this.entityLabel(
            this.entityById(value[fieldKeys.id]) || value
          );
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
      return value === null || value === undefined || value === ""
        ? ""
        : String(value);
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
      return String(field || "")
        .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
        .replace(/[_-]+/g, " ")
        .replace(/\s+/g, " ")
        .trim()
        .replace(/\b\w/g, (char) => char.toUpperCase());
    },
    isEmpty(value) {
      return (
        value === "" ||
        value === null ||
        value === undefined ||
        (Array.isArray(value) && value.length === 0) ||
        (value &&
          typeof value === "object" &&
          !Array.isArray(value) &&
          !Object.keys(value).length)
      );
    },
    valueClassForRow(row) {
      const key = String(row?.key || "").toLowerCase();
      return {
        "path-value": key.includes("path")
      };
    },
    matchesSearch(values) {
      if (!this.searchTokens.length) return true;
      const searchableText = values
        .map((value) => JSON.stringify(value ?? ""))
        .join(" ")
        .toLowerCase();
      return this.searchTokens.every((token) => searchableText.includes(token));
    },
    idSuffix(entityId) {
      return String(entityId || "").match(/(\d+)$/)?.[1] || "";
    },
    formatDate(value) {
      const text = String(value || "").trim();
      const match = text.match(/^(\d{4})-(\d{2})-(\d{2})/);
      return match ? `${match[3]}.${match[2]}.${match[1]}` : "";
    }
  }
};
</script>

<style scoped>
.rocrate-preview-page {
  height: 100%;
  min-height: 100%;
  overflow: auto;
  background: #f5f7f8;
  color: #263b45;
}

.rocrate-preview-shell {
  max-width: none;
  margin: 0 auto;
  padding: 12px;
}

.detail-card {
  background: #ffffff;
  border: 1px solid #d9e0e3;
}

.preview-action-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 10px;
  padding: 12px 14px;
  background: #ffffff;
  border: 1px solid #d9e0e3;
  border-radius: 8px;
}

.preview-action-copy {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 180px;
}

.preview-action-title {
  color: #244a60;
  font-size: 15px;
  font-weight: 700;
}

.preview-action-subtitle {
  color: #61747d;
  font-size: 12px;
  line-height: 1.4;
}

.preview-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
  align-items: center;
}

.preview-output-file {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  max-width: min(360px, 100%);
  min-height: 38px;
  padding: 0 11px;
  border: 1px solid #dde5e8;
  border-radius: 8px;
  background: #f5f8f9;
  color: #294856;
  font-size: 12px;
  cursor: default;
}

.preview-output-file-label {
  color: #667b85;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.03em;
  text-transform: uppercase;
  white-space: nowrap;
}

.preview-output-file-name {
  min-width: 0;
  overflow: hidden;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.preview-action-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  min-height: 38px;
  border-radius: 8px;
  padding: 0 13px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  text-decoration: none;
  transition:
    background-color 0.18s ease,
    border-color 0.18s ease;
}

.preview-action-button.primary {
  border: 1px solid #075f5a;
  background: #006c66;
  color: #ffffff;
}

.preview-action-button.primary:hover {
  background: #005b59;
}

.preview-action-button.secondary {
  border: 1px solid #cbd7dc;
  background: #ffffff;
  color: #244a60;
}

.preview-action-button.secondary:hover {
  border-color: #9eafb7;
  background: #f4f8f8;
}

.preview-action-button:disabled {
  opacity: 0.62;
  cursor: not-allowed;
}

.preview-feedback {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 42px;
  border: 1px solid #d7e1e4;
  border-radius: 8px;
  padding: 10px 12px;
  margin-bottom: 10px;
  background: #ffffff;
  font-size: 13px;
  font-weight: 600;
}

.preview-feedback.loading {
  background: #f5f9f9;
}

.preview-feedback.error {
  border-color: #e2b7b7;
  background: #fff5f5;
  color: #7c2020;
}

.preview-feedback.warning {
  border-color: #e5d49a;
  background: #fff9e8;
  color: #755300;
}

.loading-spinner {
  width: 18px;
  height: 18px;
  border: 3px solid rgba(0, 108, 102, 0.14);
  border-top-color: #006c66;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.preview-search-panel {
  position: sticky;
  top: 0;
  z-index: 3;
  display: grid;
  grid-template-columns: minmax(180px, 280px) minmax(0, 1fr);
  gap: 12px;
  align-items: center;
  margin-bottom: 10px;
  padding: 10px 14px;
  border: 1px solid #c8d8dc;
  border-top-color: #e3e8ea;
  border-radius: 0 0 8px 8px;
  background: rgba(247, 250, 250, 0.98);
  box-shadow: 0 4px 10px rgba(26, 58, 74, 0.06);
}

.preview-search-title {
  color: #244a60;
  font-size: 13px;
  font-weight: 700;
}

.preview-search-meta {
  margin-top: 2px;
  color: #637b86;
  font-size: 12px;
  line-height: 1.35;
}

.preview-search-controls {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.table-search-input-wrap {
  position: relative;
  flex: 1 1 auto;
  min-width: 0;
}

.table-search-input {
  width: 100%;
  height: 38px;
  border: 1px solid rgba(0, 0, 0, 0.18);
  border-radius: 8px;
  padding: 0 68px 0 12px;
  font-size: 14px;
  color: #333333;
  background: #ffffff;
  transition:
    border-color 0.18s ease,
    background-color 0.18s ease;
}

.table-search-input:hover {
  border-color: rgba(0, 0, 0, 0.3);
  background: #f9fbfb;
}

.table-search-input:focus {
  outline: none;
  border-color: #0b7f78;
  box-shadow: 0 0 0 2px rgba(11, 127, 120, 0.12);
}

.table-search-input::-webkit-search-cancel-button {
  appearance: none;
}

.table-search-icon {
  position: absolute;
  top: 50%;
  right: 12px;
  transform: translateY(-50%);
  color: #6f858e;
  pointer-events: none;
}

.table-search-clear {
  position: absolute;
  top: 50%;
  right: 34px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  padding: 0;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: #607985;
  cursor: pointer;
  transform: translateY(-50%);
}

.table-search-clear:hover,
.table-search-clear:focus-visible {
  background: #e8eff0;
  color: #244a60;
  outline: none;
}

.preview-search-navigation {
  display: inline-flex;
  align-items: center;
  flex: 0 0 auto;
  height: 38px;
  overflow: hidden;
  border: 1px solid #cbd7dc;
  border-radius: 8px;
  background: #ffffff;
  color: #294856;
  font-size: 12px;
}

.preview-search-navigation button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 100%;
  padding: 0;
  border: 0;
  background: transparent;
  color: #0b746e;
  cursor: pointer;
}

.preview-search-navigation button:hover,
.preview-search-navigation button:focus-visible {
  background: #eef5f5;
  outline: none;
}

.preview-search-navigation span {
  min-width: 50px;
  padding: 0 6px;
  text-align: center;
  white-space: nowrap;
}

.rocrate-preview-page :deep(.search-match-highlight) {
  border-radius: 2px;
  padding: 0 1px;
  background: #fff0a8;
  color: inherit;
  font-size: inherit;
  font-weight: inherit;
}

.detail-card {
  border-radius: 8px;
  padding: 14px;
  margin-bottom: 10px;
}

.detail-kicker {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  margin-bottom: 6px;
  font-size: 15px;
  font-weight: 700;
  color: #244a60;
}

.detail-kicker-icon {
  color: #0b7f78;
  font-size: 0.9em;
}

.request-overview-list,
.record-table-list,
.attachment-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 10px;
}

.request-overview-card .request-overview-list {
  margin-top: 4px;
}

.request-overview-card {
  margin-bottom: 0;
  padding-bottom: 12px;
  border-bottom: 0;
  border-radius: 8px 8px 0 0;
  box-shadow: none;
}

.request-card > .detail-header {
  margin: -2px -2px 0;
  padding: 0 2px 8px;
  border-bottom: 1px solid #e3e8ea;
}

.request-overview-item,
.record-table-block,
.attachment-item {
  min-width: 0;
  padding: 10px 12px;
  border-radius: 8px;
  background: #f9fbfb;
  border: 1px solid #e0e6e8;
}

.record-table-block {
  scroll-margin-top: 80px;
}

.record-table-header {
  padding-bottom: 8px;
  border-bottom: 1px solid #e3e8ea;
}

.record-table-block:focus {
  outline: 2px solid rgba(13, 127, 119, 0.45);
  outline-offset: 2px;
}

.request-overview-title {
  color: #244a60;
  font-size: 13px;
  font-weight: 700;
}

.record-table-heading {
  display: inline-flex;
  align-items: flex-start;
  gap: 7px;
}

.record-table-title {
  color: #244a60;
  font-size: 14px;
  font-weight: 700;
}

.record-table-title-icon {
  color: #0b7f78;
  font-size: 0.9em;
  margin-top: 4px;
}

.record-table-subtitle {
  margin-top: 2px;
  color: #667d87;
  font-size: 12px;
}

.record-chip-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 7px;
}

.record-chip {
  display: inline-flex;
  border: 1px solid #d8e4e6;
  max-width: 100%;
  border-radius: 7px;
  padding: 4px 7px;
  background: #eef5f5;
  color: #0b746e;
  cursor: pointer;
  font-family: inherit;
  font-size: 12px;
  font-weight: 600;
  line-height: 1.35;
  overflow-wrap: anywhere;
  text-align: left;
}

.record-chip:hover,
.record-chip:focus-visible {
  border-color: #9fc2bf;
  background: #e3f0ef;
}

.record-chip:focus-visible {
  outline: 2px solid rgba(13, 127, 119, 0.45);
  outline-offset: 2px;
}

.record-chip-barcode,
.record-chip-separator {
  color: #294856;
}

.record-chip-separator {
  margin-right: 3px;
}

.record-group {
  margin-top: 12px;
}

.record-group.nested {
  margin-top: 12px;
}

.record-group-title,
.quick-summary-key {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: #607985;
}

.record-group-title {
  margin-bottom: 6px;
  color: #2c6076;
}

.quick-summary-table {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.record-card-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}

.quick-summary-row,
.record-data-card {
  display: grid;
  grid-template-columns: 104px minmax(0, 1fr);
  gap: 10px;
  align-items: start;
  min-height: 48px;
  padding: 9px 11px;
  border-radius: 8px;
  background: #ffffff;
  border: 1px solid #dfe5e7;
}

.quick-summary-row.wide-row {
  grid-column: 1 / -1;
  grid-template-columns: 104px minmax(0, 1fr);
}

.record-data-key {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.03em;
  text-transform: uppercase;
  color: #607985;
}

.quick-summary-value,
.record-data-value {
  color: #294856;
  font-size: 13px;
  line-height: 1.4;
  overflow-wrap: anywhere;
}

.quick-summary-value.path-value,
.record-data-value.path-value {
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
  font-size: 12px;
}

.quick-summary-value :deep(.structured-value-table th),
.quick-summary-value :deep(.structured-value-table td) {
  border: 1px solid rgba(16, 36, 47, 0.12);
  padding: 6px 8px;
  text-align: left;
  vertical-align: top;
  background: #ffffff;
}

.quick-summary-value :deep(.structured-value-table th) {
  width: 180px;
  background: #eef3f4;
  color: #244858;
  font-weight: 700;
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

.attachment-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.attachment-item svg {
  margin-top: 2px;
  color: #0b7f78;
  flex-shrink: 0;
}

.empty-inline {
  color: #667d87;
  font-size: 13px;
  line-height: 1.4;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 1200px) {
  .preview-action-bar {
    align-items: flex-start;
  }

  .preview-actions {
    max-width: 70%;
  }

  .record-card-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 760px) {
  .rocrate-preview-shell {
    padding: 10px;
  }

  .preview-action-bar {
    align-items: stretch;
    flex-direction: column;
  }

  .preview-actions {
    justify-content: flex-start;
    max-width: none;
  }

  .preview-output-file {
    flex: 1 1 100%;
    max-width: 100%;
  }

  .quick-summary-table,
  .record-card-grid,
  .preview-search-panel {
    grid-template-columns: 1fr;
  }

  .preview-action-button {
    flex: 1 1 auto;
  }

  .preview-search-controls {
    align-items: stretch;
    flex-direction: column;
  }

  .preview-search-navigation {
    align-self: flex-end;
  }

  .quick-summary-row,
  .quick-summary-row.wide-row,
  .record-data-card {
    grid-template-columns: 1fr;
  }
}
</style>

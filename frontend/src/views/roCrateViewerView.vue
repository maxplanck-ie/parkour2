<template>
  <div class="rocrate-viewer-page">
    <div class="rocrate-viewer-shell">
      <header class="rocrate-hero">
        <div class="rocrate-hero-copy">
          <span class="rocrate-kicker">Parkour RO-Crate Viewer</span>
          <h1>Open a Parkour ISA RO-Crate and inspect everything inside it.</h1>
          <p>
            Upload the RO-Crate ZIP that Parkour exports. The viewer reads
            <strong>ro-crate-metadata.json</strong>, maps the JSON-LD graph into
            a browsable layout, and keeps the raw metadata available when you
            need it.
          </p>
          <div class="rocrate-hero-actions">
            <button class="hero-button primary" type="button" @click="triggerUpload">
              <font-awesome-icon icon="fa-solid fa-cloud-arrow-up" />
              Upload RO-Crate
            </button>
            <router-link class="hero-button secondary" to="/libraries_and_samples">
              <font-awesome-icon icon="fa-solid fa-angle-left" />
              Back to Libraries &amp; Samples
            </router-link>
          </div>
        </div>

        <div class="rocrate-hero-panel">
          <div class="hero-panel-card">
            <div class="hero-panel-title">What this viewer shows</div>
            <ul>
              <li>Root investigation and study structure</li>
              <li>Samples, libraries, pooling, processes, and protocols</li>
              <li>Request files and other embedded archive content</li>
              <li>Linked relationships and raw JSON-LD for every entity</li>
            </ul>
          </div>
          <div class="hero-panel-card hero-panel-note">
            Best with Parkour-generated ISA RO-Crates, including attached docs
            and request files bundled in the ZIP.
          </div>
        </div>
      </header>

      <section
        class="upload-stage"
        :class="{ active: isDragOver }"
        @dragover.prevent="handleDragOver"
        @dragenter.prevent="handleDragOver"
        @dragleave.prevent="handleDragLeave"
        @drop.prevent="handleDrop"
      >
        <input
          ref="uploadInput"
          class="hidden-upload"
          type="file"
          accept=".zip,.json,.jsonld,application/zip,application/json"
          @change="handleFileSelection"
        />
        <div class="upload-illustration">
          <font-awesome-icon icon="fa-solid fa-folder-open" />
        </div>
        <div class="upload-content">
          <div class="upload-title">Drop an RO-Crate ZIP here</div>
          <div class="upload-subtitle">
            You can also load <code>ro-crate-metadata.json</code> directly, but
            ZIP upload enables archive file previews.
          </div>
          <div class="upload-actions">
            <button class="hero-button primary" type="button" @click="triggerUpload">
              Choose File
            </button>
            <a
              class="hero-button tertiary"
              href="https://www.researchobject.org/ro-crate/specification/1.2/introduction.html"
              target="_blank"
              rel="noopener noreferrer"
            >
              <font-awesome-icon icon="fa-solid fa-file-lines" />
              RO-Crate Docs
            </a>
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
        <div class="summary-strip">
          <article class="summary-card glow">
            <span class="summary-label">Crate</span>
            <strong>{{ model.stats.rootName }}</strong>
            <p>{{ model.stats.description || "No root description available." }}</p>
          </article>
          <article class="summary-card">
            <span class="summary-label">Entities</span>
            <strong>{{ model.stats.entityCount }}</strong>
            <p>JSON-LD entities indexed across {{ model.stats.sectionCount }} sections.</p>
          </article>
          <article class="summary-card">
            <span class="summary-label">Archive Files</span>
            <strong>{{ model.stats.archiveFileCount }}</strong>
            <p>{{ model.stats.referencedFileCount }} files are explicitly described in the graph.</p>
          </article>
          <article class="summary-card">
            <span class="summary-label">Source</span>
            <strong>{{ model.source.name }}</strong>
            <p>{{ model.source.sizeLabel }}</p>
          </article>
        </div>

        <div class="workspace-grid">
          <aside class="workspace-sidebar">
            <div class="sidebar-card">
              <div class="sidebar-header">
                <span>Browse the crate</span>
                <input
                  v-model.trim="searchTerm"
                  class="sidebar-search"
                  type="search"
                  placeholder="Filter entities"
                />
              </div>
              <div class="section-list">
                <button
                  v-for="section in filteredSections"
                  :key="section.id"
                  class="section-button"
                  :class="{ active: activeSectionId === section.id }"
                  type="button"
                  @click="selectSection(section.id)"
                >
                  <span>{{ section.label }}</span>
                  <strong>{{ section.entityIds.length }}</strong>
                </button>
              </div>
            </div>

            <div class="sidebar-card entity-list-card">
              <div class="entity-list-header">
                <div>{{ activeSection?.label || "Entities" }}</div>
                <small>{{ filteredEntityCards.length }} shown</small>
              </div>
              <div class="entity-list">
                <button
                  v-for="entityCard in filteredEntityCards"
                  :key="entityCard.id"
                  class="entity-list-item"
                  :class="{ active: activeEntityId === entityCard.id }"
                  type="button"
                  @click="selectEntity(entityCard.id)"
                >
                  <span class="entity-list-title">{{ entityCard.label }}</span>
                  <span class="entity-list-id">{{ entityCard.id }}</span>
                </button>
              </div>
            </div>
          </aside>

          <main class="workspace-main">
            <section v-if="selectedEntityCard" class="detail-card">
              <div class="detail-header">
                <div>
                  <div class="detail-kicker">Selected Entity</div>
                  <h2>{{ selectedEntityCard.label }}</h2>
                  <div class="detail-id">{{ selectedEntityCard.id }}</div>
                </div>
                <div class="detail-type-list">
                  <span
                    v-for="entityType in selectedEntityCard.types"
                    :key="entityType"
                    class="type-chip"
                  >
                    {{ entityType }}
                  </span>
                </div>
              </div>

              <p v-if="selectedEntityCard.description" class="detail-description">
                {{ selectedEntityCard.description }}
              </p>

              <div class="detail-sections">
                <article class="detail-block">
                  <div class="detail-block-title">Properties</div>
                  <div v-if="selectedEntityCard.properties.length" class="property-table">
                    <div
                      v-for="property in selectedEntityCard.properties"
                      :key="property.key"
                      class="property-row"
                    >
                      <div class="property-key">{{ property.key }}</div>
                      <div class="property-value">
                        <template v-if="property.kind === 'scalar'">
                          {{ property.value }}
                        </template>
                        <template v-else-if="property.kind === 'list'">
                          {{ property.value.join(", ") }}
                        </template>
                        <template v-else-if="property.kind === 'reference'">
                          <button
                            v-for="reference in property.value"
                            :key="reference.id"
                            class="reference-pill"
                            type="button"
                            @click="selectEntity(reference.id)"
                          >
                            {{ reference.label }}
                          </button>
                        </template>
                        <template v-else-if="property.kind === 'reference-list'">
                          <div class="reference-pill-list">
                            <button
                              v-for="reference in property.value"
                              :key="reference.id"
                              class="reference-pill"
                              type="button"
                              @click="selectEntity(reference.id)"
                            >
                              {{ reference.label }}
                            </button>
                          </div>
                        </template>
                        <template v-else>
                          <pre>{{ stringifyValue(property.value) }}</pre>
                        </template>
                      </div>
                    </div>
                  </div>
                  <div v-else class="empty-inline">No additional properties.</div>
                </article>

                <article class="detail-block">
                  <div class="detail-block-title">Linked from elsewhere</div>
                  <div v-if="incomingLinks.length" class="relationship-list">
                    <button
                      v-for="link in incomingLinks"
                      :key="`${link.sourceId}:${link.property}`"
                      class="relationship-item"
                      type="button"
                      @click="selectEntity(link.sourceId)"
                    >
                      <span>{{ entityLabelById(link.sourceId) }}</span>
                      <small>{{ link.property }}</small>
                    </button>
                  </div>
                  <div v-else class="empty-inline">No incoming references.</div>
                </article>

                <article class="detail-block">
                  <div class="detail-block-title">Archive file</div>
                  <template v-if="selectedEntityCard.fileEntry">
                    <div class="file-preview-meta">
                      <span>{{ selectedEntityCard.fileEntry.path }}</span>
                      <small>
                        {{ selectedEntityCard.fileEntry.mimeType }} |
                        {{ selectedEntityCard.fileEntry.sizeLabel }}
                      </small>
                    </div>
                    <div class="file-preview-actions">
                      <button
                        class="hero-button secondary"
                        type="button"
                        @click="previewArchiveFile(selectedEntityCard.fileEntry.id)"
                      >
                        Preview file
                      </button>
                    </div>
                  </template>
                  <div v-else class="empty-inline">
                    This entity is metadata-only or the archive file is not available in the uploaded source.
                  </div>
                </article>
              </div>
            </section>

            <section v-if="previewState" class="detail-card preview-card">
              <div class="detail-header preview-header">
                <div>
                  <div class="detail-kicker">Archive Preview</div>
                  <h2>{{ previewState.name }}</h2>
                </div>
                <button class="hero-button tertiary" type="button" @click="clearPreview">
                  <font-awesome-icon icon="fa-solid fa-xmark" />
                  Close Preview
                </button>
              </div>

              <div v-if="previewState.mode === 'image'" class="preview-frame image">
                <img :src="previewState.objectUrl" :alt="previewState.name" />
              </div>
              <iframe
                v-else-if="previewState.mode === 'pdf'"
                class="preview-frame pdf"
                :src="previewState.objectUrl"
                title="PDF preview"
              ></iframe>
              <pre v-else-if="previewState.mode === 'text'" class="preview-frame text">{{
                previewState.text
              }}</pre>
              <div v-else class="empty-inline">
                This file type is not previewed inline. Download the RO-Crate and open the file locally if needed.
              </div>
            </section>

            <section class="detail-card raw-card">
              <div class="detail-header">
                <div>
                  <div class="detail-kicker">Raw Metadata</div>
                  <h2>{{ selectedEntityCard ? "Selected entity JSON-LD" : "RO-Crate JSON-LD" }}</h2>
                </div>
              </div>
              <pre class="raw-json">{{ rawJson }}</pre>
            </section>
          </main>
        </div>
      </section>
    </div>
  </div>
</template>

<script>
import {
  cleanupArchivePreview,
  loadArchivePreview,
  parseRoCrateSource
} from "../utilities/roCrateViewer";
import { showNotification } from "../utilities/utilityFunctions";

export default {
  name: "ROCrateViewerView",
  data() {
    return {
      loading: false,
      errorMessage: "",
      model: null,
      searchTerm: "",
      activeSectionId: "",
      activeEntityId: "",
      isDragOver: false,
      previewState: null
    };
  },
  computed: {
    filteredSections() {
      if (!this.model) return [];
      const searchValue = this.searchTerm.trim().toLowerCase();
      if (!searchValue) return this.model.sections;
      return this.model.sections
        .map((section) => ({
          ...section,
          entityIds: section.entityIds.filter((entityId) => {
            const card = this.lookupEntityCard(entityId);
            return (
              card?.label?.toLowerCase().includes(searchValue) ||
              card?.id?.toLowerCase().includes(searchValue) ||
              card?.types?.some((type) =>
                String(type).toLowerCase().includes(searchValue)
              )
            );
          })
        }))
        .filter((section) => section.entityIds.length > 0);
    },
    activeSection() {
      return this.filteredSections.find(
        (section) => section.id === this.activeSectionId
      );
    },
    filteredEntityCards() {
      const section = this.activeSection;
      if (!section) return [];
      return section.entityIds
        .map((entityId) => this.lookupEntityCard(entityId))
        .filter(Boolean);
    },
    selectedEntityCard() {
      if (!this.activeEntityId) return null;
      return this.lookupEntityCard(this.activeEntityId);
    },
    incomingLinks() {
      if (!this.selectedEntityCard || !this.model) return [];
      return this.model.backlinkMap[this.selectedEntityCard.id] || [];
    },
    rawJson() {
      let payload = this.model?.roCrate || {};
      if (this.selectedEntityCard) {
        payload =
          this.model?.entityMap?.[this.selectedEntityCard.id] ||
          this.model?.archive?.byId?.[this.selectedEntityCard.id] ||
          {};
      }
      return JSON.stringify(payload, null, 2);
    }
  },
  beforeUnmount() {
    this.clearPreview();
  },
  watch: {
    filteredSections(newSections) {
      if (!newSections.length) {
        this.activeSectionId = "";
        this.activeEntityId = "";
        return;
      }

      const currentSection = newSections.find(
        (section) => section.id === this.activeSectionId
      );
      if (!currentSection) {
        this.activeSectionId = newSections[0].id;
        this.activeEntityId = newSections[0].entityIds[0] || "";
        return;
      }

      if (!currentSection.entityIds.includes(this.activeEntityId)) {
        this.activeEntityId = currentSection.entityIds[0] || "";
      }
    }
  },
  methods: {
    triggerUpload() {
      this.$refs.uploadInput?.click?.();
    },
    handleDragOver() {
      this.isDragOver = true;
    },
    handleDragLeave(event) {
      if (!event.currentTarget.contains(event.relatedTarget)) {
        this.isDragOver = false;
      }
    },
    handleDrop(event) {
      this.isDragOver = false;
      const file = event.dataTransfer?.files?.[0];
      if (file) {
        this.loadSource(file);
      }
    },
    handleFileSelection(event) {
      const file = event.target.files?.[0];
      if (file) {
        this.loadSource(file);
      }
      event.target.value = "";
    },
    async loadSource(file) {
      this.loading = true;
      this.errorMessage = "";
      this.clearPreview();

      try {
        const parsedModel = await parseRoCrateSource(file);
        this.model = parsedModel;
        this.searchTerm = "";
        this.activeSectionId = parsedModel.sections[0]?.id || "";
        this.activeEntityId =
          parsedModel.stats.rootDatasetId ||
          parsedModel.sections[0]?.entityIds?.[0] ||
          "";
        if (
          this.activeSectionId &&
          !parsedModel.sections.some((section) => section.id === this.activeSectionId)
        ) {
          this.activeSectionId = parsedModel.sections[0]?.id || "";
        }
        showNotification("RO-Crate loaded successfully.", "success");
      } catch (error) {
        this.model = null;
        this.errorMessage =
          error?.message || "The selected file could not be read as an RO-Crate.";
      } finally {
        this.loading = false;
      }
    },
    lookupEntityCard(entityId) {
      if (!this.model) return null;
      if (this.model.entityCards[entityId]) {
        return this.model.entityCards[entityId];
      }
      const archiveEntry = this.model.archive?.byId?.[entityId];
      if (!archiveEntry) return null;
      return {
        id: archiveEntry.id,
        label: archiveEntry.name,
        description: archiveEntry.path,
        types: ["ArchiveFile"],
        fileEntry: archiveEntry,
        properties: [
          { key: "path", kind: "scalar", value: archiveEntry.path },
          { key: "mimeType", kind: "scalar", value: archiveEntry.mimeType },
          { key: "size", kind: "scalar", value: archiveEntry.sizeLabel }
        ]
      };
    },
    selectSection(sectionId) {
      this.activeSectionId = sectionId;
      const section = this.filteredSections.find((entry) => entry.id === sectionId);
      if (!section?.entityIds?.length) {
        this.activeEntityId = "";
        return;
      }
      if (!section.entityIds.includes(this.activeEntityId)) {
        this.activeEntityId = section.entityIds[0];
      }
    },
    selectEntity(entityId) {
      const entityCard = this.lookupEntityCard(entityId);
      if (!entityCard) return;

      const containingSection = this.filteredSections.find((section) =>
        section.entityIds.includes(entityId)
      );
      if (containingSection) {
        this.activeSectionId = containingSection.id;
      }
      this.activeEntityId = entityId;
    },
    entityLabelById(entityId) {
      return this.lookupEntityCard(entityId)?.label || entityId;
    },
    stringifyValue(value) {
      return JSON.stringify(value, null, 2);
    },
    async previewArchiveFile(archiveId) {
      if (!this.model) return;
      this.clearPreview();
      try {
        this.previewState = await loadArchivePreview(this.model, archiveId);
      } catch (error) {
        showNotification(error?.message || "Could not preview archive file.", "warning");
      }
    },
    clearPreview() {
      if (this.previewState) {
        cleanupArchivePreview(this.previewState);
      }
      this.previewState = null;
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

.rocrate-viewer-shell {
  max-width: 1520px;
  margin: 0 auto;
  padding: 32px 24px 56px;
}

.rocrate-hero {
  display: grid;
  grid-template-columns: minmax(0, 1.8fr) minmax(280px, 1fr);
  gap: 24px;
  margin-bottom: 28px;
}

.rocrate-hero-copy,
.rocrate-hero-panel,
.upload-stage,
.summary-card,
.sidebar-card,
.detail-card {
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(16, 36, 47, 0.08);
  box-shadow: 0 20px 40px rgba(26, 58, 74, 0.08);
  backdrop-filter: blur(12px);
}

.rocrate-hero-copy {
  border-radius: 28px;
  padding: 36px;
  animation: rise-in 0.45s ease-out;
}

.rocrate-kicker {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(3, 121, 98, 0.1);
  color: #066954;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.rocrate-hero-copy h1 {
  margin: 16px 0 12px;
  font-size: clamp(2rem, 4vw, 3.6rem);
  line-height: 0.98;
  letter-spacing: -0.05em;
}

.rocrate-hero-copy p {
  max-width: 760px;
  margin: 0;
  color: #46606d;
  font-size: 16px;
  line-height: 1.6;
}

.rocrate-hero-actions,
.upload-actions,
.detail-type-list,
.reference-pill-list,
.file-preview-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.rocrate-hero-actions {
  margin-top: 24px;
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
  background: #e4f0f3;
  color: #163746;
}

.hero-button.tertiary {
  background: transparent;
  color: #1d5f78;
  border: 1px solid rgba(29, 95, 120, 0.18);
}

.rocrate-hero-panel {
  border-radius: 28px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  animation: rise-in 0.58s ease-out;
}

.hero-panel-card {
  border-radius: 22px;
  padding: 20px;
  background: linear-gradient(180deg, rgba(240, 249, 250, 0.92), rgba(255, 255, 255, 0.9));
  border: 1px solid rgba(16, 36, 47, 0.06);
}

.hero-panel-title {
  margin-bottom: 12px;
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #1d5f78;
}

.hero-panel-card ul {
  margin: 0;
  padding-left: 18px;
  color: #45616d;
  line-height: 1.6;
}

.hero-panel-note {
  color: #2f5665;
  font-weight: 600;
}

.upload-stage {
  display: grid;
  grid-template-columns: 120px minmax(0, 1fr);
  gap: 20px;
  align-items: center;
  border-radius: 24px;
  padding: 24px;
  margin-bottom: 24px;
  border-style: dashed;
  transition:
    transform 0.2s ease,
    border-color 0.2s ease,
    background-color 0.2s ease;
}

.upload-stage.active {
  transform: scale(1.005);
  border-color: rgba(13, 111, 115, 0.35);
  background: rgba(241, 252, 249, 0.95);
}

.upload-illustration {
  display: grid;
  place-items: center;
  width: 100px;
  height: 100px;
  border-radius: 26px;
  background: linear-gradient(135deg, rgba(13, 111, 115, 0.14), rgba(27, 156, 124, 0.12));
  color: #137c70;
  font-size: 40px;
}

.upload-title {
  font-size: 24px;
  font-weight: 800;
  letter-spacing: -0.03em;
}

.upload-subtitle {
  margin-top: 8px;
  color: #4d6671;
  line-height: 1.6;
}

.upload-actions {
  margin-top: 16px;
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

.summary-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 18px;
}

.summary-card {
  border-radius: 22px;
  padding: 18px;
  animation: rise-in 0.35s ease-out;
}

.summary-card.glow {
  background: linear-gradient(135deg, rgba(7, 117, 113, 0.94), rgba(38, 145, 108, 0.88));
  color: #fff;
}

.summary-label,
.detail-kicker {
  display: inline-block;
  margin-bottom: 8px;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #5d7682;
}

.summary-card.glow .summary-label {
  color: rgba(255, 255, 255, 0.78);
}

.summary-card strong {
  display: block;
  font-size: 24px;
  letter-spacing: -0.04em;
}

.summary-card p {
  margin: 8px 0 0;
  color: inherit;
  opacity: 0.8;
  line-height: 1.5;
}

.workspace-grid {
  display: grid;
  grid-template-columns: 340px minmax(0, 1fr);
  gap: 18px;
}

.workspace-sidebar {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.sidebar-card,
.detail-card {
  border-radius: 22px;
  padding: 18px;
}

.sidebar-header,
.entity-list-header,
.detail-header,
.preview-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
}

.sidebar-header {
  flex-direction: column;
}

.sidebar-search {
  width: 100%;
  border: 1px solid rgba(16, 36, 47, 0.12);
  border-radius: 12px;
  padding: 10px 12px;
  font-size: 14px;
}

.section-list,
.entity-list,
.relationship-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.section-list {
  margin-top: 14px;
}

.section-button,
.entity-list-item,
.relationship-item {
  width: 100%;
  border: 1px solid rgba(16, 36, 47, 0.08);
  border-radius: 16px;
  padding: 12px 14px;
  background: #fff;
  cursor: pointer;
  transition:
    transform 0.16s ease,
    border-color 0.16s ease,
    box-shadow 0.16s ease;
}

.section-button,
.relationship-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.section-button.active,
.entity-list-item.active {
  border-color: rgba(13, 111, 115, 0.3);
  background: linear-gradient(135deg, rgba(13, 111, 115, 0.07), rgba(27, 156, 124, 0.05));
  box-shadow: 0 10px 20px rgba(20, 84, 99, 0.08);
}

.section-button:hover,
.entity-list-item:hover,
.relationship-item:hover {
  transform: translateY(-1px);
}

.entity-list-card {
  min-height: 480px;
}

.entity-list-header {
  margin-bottom: 12px;
}

.entity-list {
  max-height: 720px;
  overflow: auto;
}

.entity-list-item {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
  text-align: left;
}

.entity-list-title {
  font-weight: 700;
  color: #173948;
}

.entity-list-id,
.detail-id {
  font-size: 12px;
  color: #62808f;
  word-break: break-all;
}

.workspace-main {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.detail-header h2 {
  margin: 0;
  font-size: 28px;
  letter-spacing: -0.04em;
}

.detail-description {
  margin: 12px 0 0;
  color: #48616d;
  line-height: 1.7;
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
}

.detail-sections {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  margin-top: 18px;
}

.detail-block {
  border-radius: 18px;
  padding: 16px;
  background: linear-gradient(180deg, rgba(248, 251, 252, 0.96), rgba(255, 255, 255, 0.96));
  border: 1px solid rgba(16, 36, 47, 0.06);
}

.detail-block-title {
  margin-bottom: 14px;
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #1d5f78;
}

.property-table {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.property-row {
  display: grid;
  grid-template-columns: 120px minmax(0, 1fr);
  gap: 10px;
  align-items: start;
}

.property-key {
  font-size: 12px;
  font-weight: 700;
  color: #5e7884;
  word-break: break-word;
}

.property-value {
  color: #143644;
  line-height: 1.55;
  word-break: break-word;
}

.property-value pre,
.raw-json,
.preview-frame.text {
  margin: 0;
  padding: 14px;
  border-radius: 16px;
  background: #10242f;
  color: #d6ecf1;
  overflow: auto;
  font-size: 12px;
  line-height: 1.6;
}

.reference-pill {
  border: 0;
  border-radius: 999px;
  padding: 8px 12px;
  background: rgba(29, 95, 120, 0.08);
  color: #1d5f78;
  font-weight: 700;
  cursor: pointer;
}

.relationship-item {
  text-align: left;
}

.relationship-item span {
  font-weight: 700;
}

.relationship-item small,
.file-preview-meta small {
  color: #5f7784;
}

.empty-inline {
  color: #65818c;
  line-height: 1.6;
}

.preview-card .detail-header {
  margin-bottom: 14px;
}

.preview-frame {
  width: 100%;
  border-radius: 18px;
  border: 1px solid rgba(16, 36, 47, 0.08);
  background: #fff;
}

.preview-frame.image {
  display: grid;
  place-items: center;
  overflow: hidden;
  padding: 16px;
}

.preview-frame.image img {
  max-width: 100%;
  border-radius: 12px;
}

.preview-frame.pdf {
  min-height: 680px;
}

.raw-card {
  overflow: hidden;
}

.file-preview-meta {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@keyframes rise-in {
  from {
    opacity: 0;
    transform: translateY(10px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 1180px) {
  .summary-strip,
  .detail-sections {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .workspace-grid,
  .rocrate-hero {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .rocrate-viewer-shell {
    padding: 20px 14px 40px;
  }

  .rocrate-hero-copy,
  .rocrate-hero-panel,
  .sidebar-card,
  .detail-card,
  .summary-card,
  .upload-stage {
    border-radius: 20px;
    padding: 16px;
  }

  .upload-stage,
  .summary-strip,
  .detail-sections {
    grid-template-columns: 1fr;
  }

  .upload-illustration {
    width: 72px;
    height: 72px;
    font-size: 28px;
  }

  .property-row {
    grid-template-columns: 1fr;
  }
}
</style>

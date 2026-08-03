<template>
  <div
    v-if="show"
    class="request-editor-overlay popup-overlay"
    :class="{ 'drag-over': isDragOver }"
    @dragover.prevent="handleDragOver"
    @dragenter.prevent="handleDragEnter"
    @dragleave.prevent="handleDragLeave"
    @drop.prevent="handleDrop"
  >
    <div v-if="canEditRequest" class="drag-drop-indicator">
      <div
        style="
          display: flex;
          justify-content: center;
          align-items: center;
          height: 200px;
        "
      >
        <p>
          Drop
          <span style="font-weight: bold">request related documents</span> here
          to upload
        </p>
      </div>
    </div>
    <div class="request-editor-modal">
      <div
        v-if="fakeLoading"
        class="request-editor-loading-overlay"
        aria-hidden="true"
      ></div>
      <div
        v-if="isEditMode && !requestDataReady"
        class="request-editor-loading-overlay"
        aria-live="polite"
        aria-busy="true"
      >
        <div class="spinner"></div>
        <p>Loading <span style="font-weight: bold">request details</span>...</p>
      </div>
      <div
        class="request-editor-content"
        :class="{ collapsed: isFormPanelCollapsed }"
      >
        <div
          class="request-editor-header-left"
          :class="{ collapsed: isFormPanelCollapsed }"
        >
          <span class="title-with-icon">
            <font-awesome-icon
              icon="fa-solid fa-file-lines"
              class="header-icon"
            />
            <span
              class="header-title-text"
              :title="headerTitle"
              data-testid="request-editor-title"
              >{{ headerTitle }}</span
            >
          </span>
        </div>
        <button
          class="panel-toggle-button vertical-toggle"
          type="button"
          @click="toggleFormPanel"
          :aria-label="
            isFormPanelCollapsed
              ? 'Expand details panel'
              : 'Collapse details panel'
          "
        >
          <font-awesome-icon
            :icon="
              isFormPanelCollapsed
                ? 'fa-solid fa-angle-right'
                : 'fa-solid fa-angle-left'
            "
          />
        </button>
        <div class="request-editor-header-right">
          <div class="header-table-actions">
            <div class="controls-group record-type-toggle-group">
              <label
                class="record-type-switch"
                title="Switch between Library and Sample entry modes"
              >
                <input
                  type="checkbox"
                  :checked="requestEditorMode === 'sample'"
                  :disabled="!canEditRequest"
                  @change="requestRecordTypeSwitch($event)"
                />
                <span class="slider">
                  <span
                    class="option"
                    :class="{ active: requestEditorMode === 'library' }"
                  >
                    Library
                  </span>
                  <span
                    class="option"
                    :class="{ active: requestEditorMode === 'sample' }"
                  >
                    Sample
                  </span>
                </span>
              </label>
            </div>
            <div class="add-count-group">
              <input
                id="add-count-input"
                v-model.number="addRowCount"
                type="number"
                min="0"
                :class="[
                  'add-count-input',
                  { 'input-error': hasEditedAddCount && !addRowCount }
                ]"
                :disabled="!canEditRequest"
                @input="hasEditedAddCount = true"
                @blur="hasEditedAddCount = true"
              />
              <button
                class="icon-button text-button add-count-button"
                type="button"
                data-testid="add-records-button"
                :title="addButtonTitle"
                :disabled="!canEditRequest"
                @click="addDraftRow(addRowCount)"
              >
                <font-awesome-icon icon="fa-solid fa-square-plus" />
                <span>{{ addButtonLabel }}</span>
              </button>
            </div>
            <button
              class="icon-button text-button"
              type="button"
              :title="deleteButtonTitle"
              :disabled="!canEditRequest || !selectedDraftRowIds.length"
              @click="requestDeleteSelectedDraftRows"
            >
              <font-awesome-icon icon="fa-solid fa-trash" />
              <span>Delete Selected</span>
            </button>
          </div>
          <div
            class="header-table-actions utility-actions"
            :class="{ hidden: !canEditRequest }"
            title="Clipboard Actions"
          >
            <button
              class="icon-button text-button clipboard-button"
              type="button"
              title="Cut the selected range to the clipboard"
              :disabled="!canEditRequest || !hasEditableRangeSelection"
              @click="triggerTableCut"
            >
              <font-awesome-icon icon="fa-solid fa-scissors" />
              <span>Cut</span>
            </button>
            <button
              class="icon-button text-button clipboard-button"
              type="button"
              title="Copy the selected range to the clipboard"
              :disabled="!requestEditorDraftRows.length || !hasRangeSelection"
              @click="triggerTableCopy"
            >
              <font-awesome-icon icon="fa-solid fa-copy" />
              <span>Copy</span>
            </button>
            <button
              class="icon-button text-button clipboard-button"
              type="button"
              title="Paste clipboard data into the selected range"
              :disabled="!canEditRequest || !hasEditableRangeSelection"
              @click="triggerTablePaste"
            >
              <font-awesome-icon icon="fa-solid fa-paste" />
              <span>Paste</span>
            </button>
            <button
              class="icon-button text-button clipboard-button"
              type="button"
              title="Clear values in the selected range"
              :disabled="!canEditRequest || !hasEditableRangeSelection"
              @click="triggerTableClear"
            >
              <font-awesome-icon icon="fa-solid fa-eraser" />
              <span>Clear</span>
            </button>
            <button
              class="icon-button text-button clipboard-button"
              type="button"
              title="Apply the selected cell value to this column for all rows in this request"
              :disabled="!canEditRequest || !isSingleCellSelected"
              @click="triggerApplyToAll"
            >
              <font-awesome-icon icon="fa-solid fa-wand-magic-sparkles" />
              <span>Apply to All</span>
            </button>
          </div>
          <div class="header-actions">
            <div
              class="shortcut-help"
              @mouseenter="openShortcutHelp"
              @mouseleave="scheduleShortcutHelpClose"
            >
              <button
                class="help-button shortcut-help-button"
                type="button"
                :aria-expanded="showShortcutHelp.toString()"
                aria-controls="shortcut-help-panel"
                aria-haspopup="dialog"
                @focus="openShortcutHelp"
              >
                <font-awesome-icon icon="fa-solid fa-keyboard" />
              </button>
              <div
                v-if="showShortcutHelp"
                id="shortcut-help-panel"
                class="shortcut-help-panel"
                role="dialog"
                aria-label="Keyboard shortcuts"
                @mouseenter="cancelShortcutHelpClose"
                @mouseleave="scheduleShortcutHelpClose"
              >
                <div class="shortcut-help-title">Keyboard Shortcuts</div>
                <ul class="shortcut-help-list">
                  <li>
                    <span>Select everything in the current table</span>
                    <span class="shortcut-keys">
                      <kbd>Ctrl</kbd>
                      <span class="shortcut-plus">+</span>
                      <kbd>A</kbd>
                    </span>
                  </li>
                  <li>
                    <span>Copy the selected cells</span>
                    <span class="shortcut-keys">
                      <kbd>Ctrl</kbd>
                      <span class="shortcut-plus">+</span>
                      <kbd>C</kbd>
                    </span>
                  </li>
                  <li>
                    <span>Paste into the selected cells</span>
                    <span class="shortcut-keys">
                      <kbd>Ctrl</kbd>
                      <span class="shortcut-plus">+</span>
                      <kbd>V</kbd>
                    </span>
                  </li>
                  <li>
                    <span>Cut the selected cells</span>
                    <span class="shortcut-keys">
                      <kbd>Ctrl</kbd>
                      <span class="shortcut-plus">+</span>
                      <kbd>X</kbd>
                    </span>
                  </li>
                  <li>
                    <span>Clear the selected cells</span>
                    <span class="shortcut-keys">
                      <kbd>Del</kbd>
                      <span class="shortcut-plus">/</span>
                      <kbd>Backspace</kbd>
                    </span>
                  </li>
                </ul>
              </div>
            </div>
            <div
              class="feature-help"
              @mouseenter="openFeatureHelp"
              @mouseleave="scheduleFeatureHelpClose"
            >
              <button
                class="help-button"
                type="button"
                :aria-expanded="showFeatureHelp.toString()"
                aria-controls="feature-help-panel"
                aria-haspopup="dialog"
                @focus="openFeatureHelp"
              >
                ?
              </button>
              <div
                v-if="showFeatureHelp"
                id="feature-help-panel"
                class="feature-help-panel"
                role="dialog"
                aria-label="Request editor help"
                @mouseenter="cancelFeatureHelpClose"
                @mouseleave="scheduleFeatureHelpClose"
              >
                <div class="feature-help-scroll">
                  <div class="feature-help-header">
                    <div>
                      <div>
                        <div class="feature-help-title">
                          Request Editor Guide
                        </div>
                        <p>
                          This window helps you create or update a request from
                          start to finish. Fill in the basic request details,
                          add your libraries or samples, attach any needed
                          files, then save everything together.
                        </p>
                      </div>
                    </div>
                  </div>

                  <div class="feature-help-grid">
                    <section class="feature-help-section">
                      <div class="feature-help-section-head">
                        <font-awesome-icon icon="fa-solid fa-folder-open" />
                        <span>Request Details and Files</span>
                      </div>
                      <ul class="feature-help-points">
                        <li>
                          Start on the left side. Choose a Cost Unit and write a
                          short Description of the request.
                        </li>
                        <li>
                          New requests are assigned automatically. In edit mode,
                          staff users can change the Request Owner without
                          changing the Cost Unit.
                        </li>
                        <li>
                          Use <strong>Related Project(s)</strong> to link this
                          request to other requests that belong to the same
                          project context.
                        </li>
                        <li>
                          Add request files with <strong>Add Files</strong>, or
                          drag files into this window.
                        </li>
                        <li>
                          After upload, you can check the file list, download a
                          file again, or remove a file before saving.
                        </li>
                        <li>
                          If you are working with Samples, this area also shows
                          helpful sample forms you can download.
                        </li>
                      </ul>
                      <div class="feature-help-visual file-help-visual">
                        <div class="visual-header">Request Files</div>
                        <div class="visual-dropzone">
                          <font-awesome-icon
                            icon="fa-solid fa-cloud-arrow-up"
                          />
                          <span>Drag files here</span>
                        </div>
                        <div class="visual-file-row">
                          <span class="visual-file-name"
                            >project_notes.pdf</span
                          >
                          <font-awesome-icon icon="fa-solid fa-download" />
                        </div>
                      </div>
                    </section>

                    <section class="feature-help-section">
                      <div class="feature-help-section-head">
                        <font-awesome-icon icon="fa-solid fa-table-cells" />
                        <span>Mode Switch and Row Setup</span>
                      </div>
                      <ul class="feature-help-points">
                        <li>
                          At the top, choose whether you are entering
                          <strong>Libraries</strong> or
                          <strong>Samples</strong>.
                        </li>
                        <li>
                          Type how many rows you want to add, then click
                          <strong>Add Libraries</strong> or
                          <strong>Add Samples</strong>.
                        </li>
                        <li>
                          If you no longer need some rows, select them and click
                          <strong>Delete Selected</strong>.
                        </li>
                        <li>
                          If you switch between Library and Sample while
                          creating a new request, the current draft rows will be
                          cleared after confirmation.
                        </li>
                      </ul>
                      <div class="feature-help-visual toggle-help-visual">
                        <div class="visual-toggle">
                          <span class="visual-toggle-active">Library</span>
                          <span>Sample</span>
                        </div>
                        <div class="visual-add-strip">
                          <span class="visual-count-box">3</span>
                          <span class="visual-add-button">+ Add Rows</span>
                        </div>
                      </div>
                    </section>

                    <section class="feature-help-section">
                      <div class="feature-help-section-head">
                        <font-awesome-icon icon="fa-solid fa-pen-to-square" />
                        <span>Table Editing</span>
                      </div>
                      <ul class="feature-help-points">
                        <li>
                          Enter information directly in the table on the right.
                          The columns change depending on whether you selected
                          Libraries or Samples.
                        </li>
                        <li>
                          Some cells let you type, some give you a dropdown
                          list, and some update automatically based on what you
                          chose earlier.
                        </li>
                        <li>
                          Required or incorrect values are highlighted so you
                          can see what still needs attention.
                        </li>
                        <li>
                          Some fields are read-only until other required choices
                          are filled in.
                        </li>
                      </ul>
                      <div class="feature-help-visual table-help-visual">
                        <div class="visual-table-row visual-table-head">
                          <span>Name</span>
                          <span>Protocol</span>
                          <span>Depth</span>
                        </div>
                        <div class="visual-table-row">
                          <span>Lib_01</span>
                          <span>RNA</span>
                          <span class="visual-valid-cell">20</span>
                        </div>
                        <div class="visual-table-row">
                          <span class="visual-invalid-cell">Required</span>
                          <span>DNA</span>
                          <span>10</span>
                        </div>
                      </div>
                    </section>

                    <section class="feature-help-section">
                      <div class="feature-help-section-head">
                        <font-awesome-icon icon="fa-solid fa-copy" />
                        <span>Range Selection and Clipboard</span>
                      </div>
                      <ul class="feature-help-points">
                        <li>
                          You can select a block of cells and then
                          <strong>Cut</strong>, <strong>Copy</strong>,
                          <strong>Paste</strong>, or <strong>Clear</strong> many
                          values at once.
                        </li>
                        <li>
                          <strong>Apply to All</strong> takes one value from the
                          current cell and fills the same column for all rows in
                          the request.
                        </li>
                        <li>
                          When you paste, the editor tries to keep the data in
                          the correct place and follow the field rules.
                        </li>
                        <li>
                          Use the keyboard icon for a quick list of shortcuts.
                        </li>
                      </ul>
                      <div class="feature-help-visual range-help-visual">
                        <div class="visual-table-row visual-table-head">
                          <span>Name</span>
                          <span>Type</span>
                          <span>Depth</span>
                        </div>
                        <div class="visual-table-row">
                          <span>Row 1</span>
                          <span class="visual-range-cell">RNA</span>
                          <span class="visual-range-cell">15</span>
                        </div>
                        <div class="visual-table-row">
                          <span>Row 2</span>
                          <span class="visual-range-cell">RNA</span>
                          <span class="visual-range-cell">15</span>
                        </div>
                        <div class="visual-shortcuts-inline">
                          <kbd>Ctrl</kbd><span>+</span><kbd>C</kbd>
                          <kbd>Ctrl</kbd><span>+</span><kbd>V</kbd>
                        </div>
                      </div>
                    </section>

                    <section class="feature-help-section">
                      <div class="feature-help-section-head">
                        <font-awesome-icon
                          icon="fa-solid fa-wand-magic-sparkles"
                        />
                        <span>Auto-Population and Smart Fill</span>
                      </div>
                      <ul class="feature-help-points">
                        <li>
                          Some fields depend on earlier choices. For example,
                          selecting an <strong>Input Type</strong> can narrow
                          the protocol options to the ones that fit that input.
                        </li>
                        <li>
                          <strong>Index Type</strong> controls related index
                          fields. When a valid <strong>Index I7</strong> is
                          selected or pasted, the editor can automatically fill
                          the paired <strong>Index I5</strong> and keep the
                          index combination consistent.
                        </li>
                        <li>
                          Paste actions are handled intelligently. The editor
                          tries to place values in the correct columns, keep row
                          alignment, and apply the same validation rules as
                          manual entry.
                        </li>
                        <li>
                          Some values are reformatted or completed
                          automatically, while other cells stay read-only until
                          the required upstream fields have been filled in.
                        </li>
                      </ul>
                    </section>

                    <section class="feature-help-section">
                      <div class="feature-help-section-head">
                        <font-awesome-icon icon="fa-solid fa-circle-check" />
                        <span>Save Flow and Validation</span>
                      </div>
                      <ul class="feature-help-points">
                        <li>
                          You can save only after the required request details
                          and required table values are filled in correctly.
                        </li>
                        <li>
                          In edit mode, the system checks all changed Library
                          and Sample data before updating the request.
                        </li>
                        <li>
                          Your table changes, file changes, and request details
                          are saved together as one update.
                        </li>
                        <li>
                          The keyboard icon next to this help button shows only
                          the shortcut list if you want a faster reference.
                        </li>
                      </ul>
                      <div class="feature-help-callout">
                        <font-awesome-icon icon="fa-solid fa-lightbulb" />
                        <span>
                          Tip: keep the left side open while you work on request
                          details and files. Collapse it when you want more
                          space for the table.
                        </span>
                      </div>
                    </section>
                  </div>
                </div>
              </div>
            </div>
            <button
              class="popup-close-button"
              type="button"
              data-testid="close-request-editor-button"
              @click="requestCloseModal"
              :disabled="saving"
            >
              &times;
            </button>
          </div>
        </div>

        <div class="request-editor-body-left">
          <div
            class="request-panel-container"
            :class="{ collapsed: isFormPanelCollapsed }"
          >
            <section
              ref="requestFormPanel"
              class="request-form-panel"
              :class="{ collapsed: isFormPanelCollapsed }"
            >
              <div
                v-if="requestEditorMode === 'sample' && !isEditMode"
                class="request-form-actions"
              >
                <div class="request-form-actions-title">Sample Forms</div>
                <div class="download-buttons">
                  <a
                    class="download-button"
                    :href="gmoFormUrl"
                    target="_blank"
                    rel="noopener"
                    title="Download Formblatt S1 (GMO)"
                  >
                    <font-awesome-icon icon="fa-solid fa-download" />
                    <span>Formblatt S1</span>
                  </a>
                  <a
                    class="download-button"
                    :href="relacsDownloadUrl"
                    target="_blank"
                    rel="noopener"
                    title="Download RELACS Pellets Abs form"
                  >
                    <font-awesome-icon icon="fa-solid fa-download" />
                    <span>RELACS Pellets Abs</span>
                  </a>
                </div>
              </div>

              <label class="field-block">
                <span>
                  Cost Unit<span v-if="!isStaffUser" class="required">*</span>
                </span>
                <select
                  v-model="newRequest.cost_unit"
                  :disabled="!canEditRequest"
                  :class="[
                    costUnitError ? 'input-error' : '',
                    !newRequest.cost_unit ? 'placeholder' : ''
                  ]"
                >
                  <option value="" disabled>Select Cost Unit</option>
                  <option v-for="cu in costUnits" :key="cu.id" :value="cu.id">
                    {{ cu.name }}
                  </option>
                </select>
                <div v-if="costUnitError" class="field-error">
                  {{ costUnitError }}
                </div>
              </label>

              <label class="field-block">
                <span>Request Owner</span>
                <div
                  v-if="isStaffUser && isEditMode"
                  class="autocomplete-field"
                >
                  <input
                    type="text"
                    v-model="requestOwnerQuery"
                    @input="handleRequestOwnerInput"
                    @blur="closeRequestOwnerSuggestions"
                    @keydown.down.prevent="moveRequestOwnerHighlight(1)"
                    @keydown.up.prevent="moveRequestOwnerHighlight(-1)"
                    @keydown.enter.prevent="selectHighlightedRequestOwner"
                    :disabled="!canEditRequest"
                    placeholder="Search users by name or PI"
                    :class="['', !requestOwnerId ? 'placeholder' : '']"
                  />
                  <ul
                    v-if="showRequestOwnerSuggestions"
                    class="autocomplete-suggestions"
                  >
                    <li
                      v-for="(user, index) in requestOwnerSuggestions"
                      :key="`owner-${user.id}`"
                      class="autocomplete-suggestion"
                      :class="{
                        highlighted:
                          index === highlightedRequestOwnerSuggestionIndex
                      }"
                      @mousedown.prevent="selectRequestOwner(user)"
                    >
                      <strong
                        >{{ user.first_name }} {{ user.last_name }}</strong
                      >
                      <span v-if="user.pi_name"> - {{ user.pi_name }}</span>
                    </li>
                    <li
                      v-if="!requestOwnerSuggestions.length"
                      class="autocomplete-empty"
                    >
                      No users found.
                    </li>
                  </ul>
                </div>
                <div v-else class="disabled-field-value">
                  {{ requestOwnerDisplayValue }}
                </div>
                <small v-if="isStaffUser">
                  Changing the owner does not change Cost Unit.
                </small>
              </label>

              <label class="field-block">
                <span> Description<span class="required">*</span> </span>
                <textarea
                  v-model="newRequest.description"
                  class="description-textarea"
                  data-testid="request-description-input"
                  rows="6"
                  :placeholder="
                    isEditMode
                      ? 'Description not provided'
                      : 'Provide a brief description of your project, including any details important for handling and documentation. Indicate whether you have a backup of your study material (Yes/No).'
                  "
                  :class="{ 'input-error': descriptionError }"
                  :readonly="!canEditRequest"
                ></textarea>
                <div v-if="descriptionError" class="field-error">
                  {{ descriptionError }}
                </div>
              </label>

              <label class="field-block">
                <span>Related Project(s)</span>
                <div
                  class="related-projects-field"
                  :class="{ focused: showRelatedProjectSuggestions }"
                >
                  <div class="autocomplete-field related-project-search">
                    <input
                      type="text"
                      v-model="relatedProjectQuery"
                      @input="handleRelatedProjectInput"
                      @focus="openRelatedProjectSuggestions"
                      @blur="closeRelatedProjectSuggestions"
                      @keydown.down.prevent="moveRelatedProjectHighlight(1)"
                      @keydown.up.prevent="moveRelatedProjectHighlight(-1)"
                      @keydown.enter.prevent="selectHighlightedRelatedProject"
                      :disabled="!canEditRelatedProjects"
                      placeholder="Search by Request ID or name"
                    />
                    <font-awesome-icon
                      class="related-project-search-icon"
                      icon="fa-solid fa-magnifying-glass"
                    />
                    <ul
                      v-if="showRelatedProjectSuggestions"
                      class="autocomplete-suggestions"
                    >
                      <li
                        v-for="(project, index) in relatedProjectSuggestions"
                        :key="`related-${project.id}`"
                        class="autocomplete-suggestion"
                        :class="{
                          highlighted:
                            index === highlightedRelatedProjectSuggestionIndex
                        }"
                        @mousedown.prevent="selectRelatedProject(project)"
                      >
                        <strong>#{{ project.id }}</strong>
                        <span v-if="project.name"> - {{ project.name }}</span>
                      </li>
                      <li
                        v-if="!relatedProjectSuggestions.length"
                        class="autocomplete-empty"
                      >
                        No projects found.
                      </li>
                    </ul>
                  </div>
                  <div
                    v-if="relatedProjectsSelection.length"
                    class="related-projects-selected"
                  >
                    <span
                      v-for="project in relatedProjectsSelection"
                      :key="`selected-related-${project.id}`"
                      class="related-project-chip"
                      :class="{ disabled: !canEditRelatedProjects }"
                    >
                      <span>#{{ project.id }}</span>
                      <button
                        v-if="canEditRelatedProjects"
                        type="button"
                        class="related-project-remove"
                        :aria-label="`Remove related project #${project.id}`"
                        @click="removeRelatedProject(project.id)"
                      >
                        <font-awesome-icon icon="fa-solid fa-xmark" />
                      </button>
                    </span>
                  </div>
                </div>
              </label>

              <div class="files-section">
                <div class="files-header">
                  <div>
                    <span>Files</span>
                    <small>Upload request related documents.</small>
                  </div>
                  <button
                    v-if="canEditRequest"
                    class="header-button ghost request-file-add-button"
                    type="button"
                    :disabled="!canEditRequest"
                    @click="triggerRequestFileUpload"
                  >
                    <font-awesome-icon
                      icon="fa-solid fa-square-plus"
                      style="color: white"
                    />
                    <span>Add Files</span>
                  </button>
                  <input
                    ref="requestFileInput"
                    type="file"
                    multiple
                    @change="handleRequestFileUpload"
                    style="display: none"
                  />
                </div>
                <div class="files-table-wrapper">
                  <table
                    class="files-table"
                    :class="{
                      'files-table-empty': !uploadedRequestFiles.length
                    }"
                  >
                    <thead>
                      <tr>
                        <th class="file-col-name">Name</th>
                        <th class="file-col-type">File Type</th>
                        <th class="file-col-size">Size</th>
                        <th class="file-col-actions"></th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-if="!uploadedRequestFiles.length">
                        <td colspan="4" class="empty-cell">
                          No files uploaded yet.
                        </td>
                      </tr>
                      <tr v-for="file in uploadedRequestFiles" :key="file.id">
                        <td class="file-name-cell">
                          <span class="file-name-text" :title="file.name">{{
                            file.name
                          }}</span>
                        </td>
                        <td class="file-type-cell">
                          <select
                            v-model="file.fileTypeChoice"
                            class="file-type-select"
                            :disabled="!canEditRequest"
                            :aria-label="`File type for ${file.name}`"
                            @change="handleRequestFileTypeChoice(file)"
                          >
                            <option
                              v-for="option in requestFileTypeOptions"
                              :key="option"
                              :value="option"
                            >
                              {{ option }}
                            </option>
                          </select>
                          <input
                            v-if="file.fileTypeChoice === requestFileTypeOther"
                            :value="file.customFileType"
                            class="file-type-custom-input"
                            :class="{
                              invalid:
                                file.customFileType &&
                                !isValidRequestFileType(file.customFileType)
                            }"
                            :disabled="!canEditRequest"
                            maxlength="100"
                            placeholder="Custom_File_Type"
                            :aria-label="`Custom file type for ${file.name}`"
                            @input="handleCustomRequestFileType(file, $event)"
                          />
                        </td>
                        <td
                          class="file-size-cell"
                          :title="formatFileSize(file.size)"
                        >
                          {{ formatFileSize(file.size) }}
                        </td>
                        <td class="actions-cell">
                          <button
                            type="button"
                            class="icon-action"
                            :title="
                              file.path
                                ? `Download ${file.name}`
                                : 'Download unavailable'
                            "
                            :disabled="!file.path"
                            @click="downloadUploadedFile(file)"
                          >
                            <font-awesome-icon icon="fa-solid fa-download" />
                          </button>
                          <button
                            v-if="canEditRequest"
                            type="button"
                            class="icon-action danger"
                            :title="`Remove ${file.name}`"
                            :disabled="!canEditRequest"
                            @click="requestRemoveUploadedFile(file)"
                          >
                            <font-awesome-icon icon="fa-solid fa-xmark" />
                          </button>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </section>
          </div>
        </div>

        <div class="request-editor-body-right">
          <section
            class="records-panel"
            :class="{ expanded: isFormPanelCollapsed }"
          >
            <div class="draft-table" ref="draftTableWrapper">
              <TabulatorTable
                ref="requestEditorDraftTableRef"
                tableId="requestEditorDraftTable"
                :rowData="requestEditorDraftRows"
                :columnDefs="requestEditorColumns"
                :tableOptions="requestEditorDraftTableOptions"
                :groupBy="null"
                :groupSort="null"
                :groupStartOpen="false"
                :enableDefaultFilters="false"
              />
            </div>
          </section>
        </div>

        <div class="request-editor-footer">
          <div class="footer-summary">
            <span>{{ footerLabel }}</span>
          </div>
          <div class="footer-actions">
            <button
              class="popup-button secondary"
              type="button"
              @click="requestCloseModal"
              :disabled="saving"
            >
              Cancel
            </button>
            <button
              class="popup-button yes-button"
              type="button"
              :disabled="
                isRequestSaving ||
                (isEditMode && isRequestLoading) ||
                (!canEditRequest && !relatedProjectsChanged)
              "
              @click="saveRequest"
            >
              <span v-if="isRequestSaving">Saving...</span>
              <span v-else>{{ primaryActionLabel }}</span>
            </button>
          </div>
        </div>
      </div>
      <div
        v-if="saving"
        class="saving-overlay"
        aria-live="polite"
        aria-busy="true"
      >
        <div class="saving-card">
          <div class="spinner"></div>
          <p>Saving request, please wait...</p>
        </div>
      </div>
    </div>
    <div
      v-if="showToggleConfirm"
      class="confirm-overlay"
      @keydown="handleConfirmKeydown"
      tabindex="0"
    >
      <div class="confirm-modal">
        <div class="confirm-header">
          <span class="confirm-title">Switch record type?</span>
          <button
            class="popup-close-button"
            type="button"
            @click="cancelToggleSwitch"
          >
            &times;
          </button>
        </div>
        <div class="confirm-body">
          Switching between Library and Sample will clear all
          {{ switchClearLabel }} you have added. Do you want to continue?
        </div>
        <div class="confirm-footer">
          <button
            class="popup-button"
            type="button"
            @click="cancelToggleSwitch"
          >
            Cancel
          </button>
          <button
            class="popup-button yes-button"
            type="button"
            @click="confirmToggleSwitch"
          >
            OK
          </button>
        </div>
      </div>
    </div>
    <div
      v-if="showDeleteConfirm"
      class="confirm-overlay"
      @keydown="handleDeleteConfirmKeydown"
      tabindex="0"
    >
      <div class="confirm-modal">
        <div class="confirm-header">
          <span class="confirm-title">{{ deleteConfirmTitle }}</span>
          <button
            class="popup-close-button"
            type="button"
            @click="cancelDeleteSelectedRows"
          >
            &times;
          </button>
        </div>
        <div class="confirm-body">
          This will permanently remove {{ selectedDraftRowIds.length }}
          {{ deleteConfirmNoun }}. Do you want to continue?
        </div>
        <div class="confirm-footer">
          <button
            class="popup-button"
            type="button"
            @click="cancelDeleteSelectedRows"
          >
            Cancel
          </button>
          <button
            class="popup-button yes-button"
            type="button"
            @click="confirmDeleteSelectedRows"
          >
            OK
          </button>
        </div>
      </div>
    </div>
    <div
      v-if="showCloseConfirm"
      class="confirm-overlay"
      @keydown="handleCloseConfirmKeydown"
      tabindex="0"
    >
      <div class="confirm-modal">
        <div class="confirm-header">
          <span class="confirm-title">Discard new request?</span>
          <button
            class="popup-close-button"
            type="button"
            @click="cancelCloseModal"
          >
            &times;
          </button>
        </div>
        <div class="confirm-body">
          Closing now will discard your entered data. Do you want to continue?
        </div>
        <div class="confirm-footer">
          <button class="popup-button" type="button" @click="cancelCloseModal">
            Cancel
          </button>
          <button
            class="popup-button yes-button"
            type="button"
            @click="confirmCloseModal"
          >
            OK
          </button>
        </div>
      </div>
    </div>
    <div
      v-if="showFileDeleteConfirm"
      class="confirm-overlay"
      @keydown="handleFileDeleteConfirmKeydown"
      tabindex="0"
    >
      <div class="confirm-modal">
        <div class="confirm-header">
          <span class="confirm-title">Delete file?</span>
          <button
            class="popup-close-button"
            type="button"
            @click="cancelFileDelete"
          >
            &times;
          </button>
        </div>
        <div class="confirm-body">
          Are you sure you want to remove "{{ pendingFileDelete?.name }}" from
          this request?
        </div>
        <div class="confirm-footer">
          <button
            class="popup-button secondary"
            type="button"
            @click="cancelFileDelete"
          >
            Cancel
          </button>
          <button
            class="popup-button yes-button"
            type="button"
            @click="confirmFileDelete"
          >
            Remove
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import TabulatorTable from "../components/TabulatorTableFull.vue";
import {
  applyValueToAllRows,
  showNotification,
  handleError,
  createAxiosObject,
  urlStringStartsWith
} from "../utilities/utilityFunctions";
import {
  getRequestEditorLibraryColumns,
  getRequestEditorSampleColumns,
  LIBRARY_REQUIRED_FIELDS,
  SAMPLE_REQUIRED_FIELDS
} from "../constants/requestEditorConsts";
import {
  REQUEST_FILE_TYPE_OPTIONS,
  REQUEST_FILE_TYPE_OTHER,
  isValidRequestFileType,
  normaliseRequestFile,
  requestFileTypesPayload,
  resolveRequestFileType
} from "../utilities/requestFileTypes";

const axiosRef = createAxiosObject();
const urlStringStart = urlStringStartsWith();
const AUTOCOMPLETE_SEARCH_DEBOUNCE_MS = 250;
const AUTOCOMPLETE_BLUR_CLOSE_DELAY_MS = 150;

export default {
  name: "RequestEditorView",
  components: {
    TabulatorTable
  },
  props: {
    show: {
      type: Boolean,
      default: false
    },
    saving: {
      type: Boolean,
      default: false
    },
    closeOnSave: {
      type: Boolean,
      default: true
    },
    notifyOnSave: {
      type: Boolean,
      default: true
    },
    mode: {
      type: String,
      default: "create"
    },
    requestId: {
      type: [Number, String],
      default: null
    },
    isStaffUser: {
      type: Boolean,
      default: false
    },
    userId: {
      type: [Number, String],
      default: null
    },
    requestMeta: {
      type: Object,
      default: null
    }
  },
  data() {
    return {
      requestEditorMode: "library",
      isFormPanelCollapsed: false,
      requestEditorDraftRows: [],
      selectedDraftRowIds: [],
      draftValidationState: {},
      validDraftCount: 0,
      isRequestSaving: false,
      draftRowCounter: 0,
      libraryMeasuringUnits: [
        { value: "ng/µl", label: "ng/µl (Concentration)" },
        { value: "Unknown", label: "Unknown" }
      ],
      sampleMeasuringUnits: [
        { value: "ng/µl", label: "ng/µl (Concentration)" },
        { value: "Cells", label: "Cells" },
        { value: "k", label: "k (Cells)" },
        { value: "M", label: "M (Cells)" },
        { value: "Unknown", label: "Unknown" }
      ],
      biosafetyLevelsOptions: [
        { value: "bsl1", label: "BSL1" },
        { value: "bsl2", label: "BSL2" }
      ],
      gmoOptions: [
        { value: true, label: "Yes" },
        { value: false, label: "No" }
      ],
      gmoFormUrl: `${urlStringStart}/static/docs/S1.docx`,
      relacsDownloadUrl: `${urlStringStart}/api/requests/download_RELACS_Pellets_Abs_form`,
      indexI7OptionsByType: {},
      indexI5OptionsByType: {},
      indexPairsByType: {},
      indexOptionsLoading: {},
      hasEditedAddCount: false,
      allowDirtyTracking: false,
      suppressNextDirtyBatch: false,
      pendingDirtyTrackingResume: false,
      isProcessingRangeClear: false,
      dirtyFieldsByRowId: {},
      validationFieldsByRowId: {},
      showToggleConfirm: false,
      showDeleteConfirm: false,
      showCloseConfirm: false,
      showFileDeleteConfirm: false,
      showShortcutHelp: false,
      showFeatureHelp: false,
      pendingToggleMode: null,
      existingRecords: [],
      isDragOver: false,
      editRecordsByType: {
        library: [],
        sample: []
      },
      editRecordTypesAvailable: {
        library: false,
        sample: false
      },
      shortcutHelpCloseTimer: null,
      featureHelpCloseTimer: null,
      pendingFileDelete: null,
      editSnapshot: {
        cost_unit: "",
        description: "",
        fileIds: [],
        fileTypes: {},
        related_request_ids: []
      },
      requestName: "",
      restrictPermissions: false,
      isRequestLoading: false,
      newRequest: {
        cost_unit: "",
        description: ""
      },
      costUnits: [],
      costUnitError: "",
      descriptionError: "",
      requestOwnerId: null,
      originalRequestOwnerId: null,
      requestOwnerQuery: "",
      originalRequestOwnerQuery: "",
      requestOwnerSuggestions: [],
      showRequestOwnerSuggestions: false,
      highlightedRequestOwnerSuggestionIndex: -1,
      requestOwnerSearchTimer: null,
      relatedProjectQuery: "",
      relatedProjectSuggestions: [],
      showRelatedProjectSuggestions: false,
      highlightedRelatedProjectSuggestionIndex: -1,
      relatedProjectSearchTimer: null,
      relatedProjectsSelection: [],
      requestUsers: [],
      uploadedRequestFiles: [],
      uploadedRequestFileIds: [],
      requestFileTypeOptions: REQUEST_FILE_TYPE_OPTIONS,
      requestFileTypeOther: REQUEST_FILE_TYPE_OTHER,
      protocolsList: [],
      analysisTypesList: [],
      readLengthsList: [],
      nucleicAcidTypesList: [],
      organismsList: [],
      filterOptionsLoaded: false,
      indexTypesLoaded: false,
      nucleicAcidTypesLoaded: false,
      organismsLoaded: false,
      costUnitsLoadedForUser: null,
      prepareTimer: null,
      isPreparingModal: false,
      indexTypesList: [],
      fakeLoading: false,
      fakeLoadingTimer: null,
      requestDataReady: false,
      addRowCount: 1,
      hasRangeSelection: false,
      hasEditableRangeSelection: false,
      isSingleCellSelected: false,
      rangeListenersAttached: false,
      rangeSelectionHandler: null,
      rangeSelectionElement: null
    };
  },
  watch: {
    show(newVal) {
      if (newVal) {
        if (this.isEditMode) {
          this.isRequestLoading = true;
          this.requestDataReady = false;
        }
        this.addRowCount = this.isEditMode ? 0 : 1;
        this.schedulePrepareRequestEditorModal();
      } else {
        if (this.prepareTimer) {
          clearTimeout(this.prepareTimer);
          this.prepareTimer = null;
        }
        this.resetState();
      }
    },
    mode() {
      if (this.show) {
        this.schedulePrepareRequestEditorModal();
      }
    },
    requestId() {
      if (this.show && this.isEditMode) {
        this.schedulePrepareRequestEditorModal();
      }
    },
    showToggleConfirm(newVal) {
      if (newVal) {
        this.$nextTick(() => {
          const overlay = this.$el?.querySelector?.(".confirm-overlay");
          overlay?.focus?.();
        });
      }
    },
    showDeleteConfirm(newVal) {
      if (newVal) {
        this.$nextTick(() => {
          const overlays = this.$el?.querySelectorAll?.(".confirm-overlay");
          const overlay = overlays?.[overlays.length - 1];
          overlay?.focus?.();
        });
      }
    },
    showCloseConfirm(newVal) {
      if (newVal) {
        this.$nextTick(() => {
          const overlays = this.$el?.querySelectorAll?.(".confirm-overlay");
          const overlay = overlays?.[overlays.length - 1];
          overlay?.focus?.();
        });
      }
    },
    showFileDeleteConfirm(newVal) {
      if (newVal) {
        this.$nextTick(() => {
          const overlays = this.$el?.querySelectorAll?.(".confirm-overlay");
          const overlay = overlays?.[overlays.length - 1];
          overlay?.focus?.();
        });
      }
    },
    "newRequest.cost_unit"(newValue) {
      if (newValue) {
        this.costUnitError = "";
      }
    },
    "newRequest.description"(newValue) {
      if ((newValue || "").trim()) {
        this.descriptionError = "";
      }
    }
  },
  mounted() {
    if (this.show) {
      this.schedulePrepareRequestEditorModal();
    }
    document.addEventListener("keydown", this.handleKeyDown);
    document.addEventListener("click", this.handleShortcutHelpOutsideClick);
    document.addEventListener("click", this.handleFeatureHelpOutsideClick);
  },
  beforeUnmount() {
    this.unbindRangeSelectionListeners();
    document.removeEventListener("keydown", this.handleKeyDown);
    document.removeEventListener("click", this.handleShortcutHelpOutsideClick);
    document.removeEventListener("click", this.handleFeatureHelpOutsideClick);
    this.cancelShortcutHelpClose();
    this.cancelFeatureHelpClose();
  },
  computed: {
    isEditMode() {
      return this.mode === "edit";
    },
    headerTitle() {
      if (!this.isEditMode) return "New Request";
      return this.requestName || "Request";
    },
    primaryActionLabel() {
      return this.isEditMode ? "Update Request" : "Save Request";
    },
    requestOwnerDisplayValue() {
      if (!this.isEditMode) return "Automatically assigned";
      return this.requestOwnerQuery || "Not assigned";
    },
    canEditRequest() {
      if (!this.isEditMode) return true;
      if (this.isStaffUser) return true;
      return !this.restrictPermissions;
    },
    canEditRelatedProjects() {
      // Related projects stay editable even when restrict_permissions
      // locks the rest of the request: staff have unrestricted access,
      // and normal users can only link requests the backend lets them
      // see (their own, plus PI-group requests for is_pi users).
      return true;
    },
    relatedProjectsChanged() {
      if (!this.isEditMode) return false;
      const current = (this.relatedProjectsSelection || [])
        .map((project) => String(project.id))
        .sort();
      const base = (this.editSnapshot?.related_request_ids || [])
        .map(String)
        .sort();
      return (
        current.length !== base.length ||
        current.some((id, index) => id !== base[index])
      );
    },
    requestEditorModeLabel() {
      return this.requestEditorMode === "library" ? "Library" : "Sample";
    },
    recordLabelSet() {
      return this.requestEditorMode === "library"
        ? { singular: "library", plural: "libraries" }
        : { singular: "sample", plural: "samples" };
    },
    addButtonLabel() {
      return this.requestEditorMode === "library"
        ? "Add Libraries"
        : "Add Samples";
    },
    addButtonTitle() {
      return this.requestEditorMode === "library"
        ? "Add new libraries"
        : "Add new samples";
    },
    deleteButtonTitle() {
      return this.requestEditorMode === "library"
        ? "Delete selected libraries"
        : "Delete selected samples";
    },
    deleteConfirmTitle() {
      return this.requestEditorMode === "library"
        ? "Delete selected libraries?"
        : "Delete selected samples?";
    },
    deleteConfirmNoun() {
      const count = this.selectedDraftRowIds.length;
      return count === 1
        ? this.recordLabelSet.singular
        : this.recordLabelSet.plural;
    },
    switchClearLabel() {
      return this.recordLabelSet.plural;
    },
    requestEditorColumns() {
      const normalizeOptions = (list = []) =>
        list.map((item) => ({
          value: item.id ?? item.value ?? item.pk ?? item.name,
          label: item.name ?? item.label ?? item.text ?? item.value ?? "",
          type: item.type,
          library_protocol: item.library_protocol
        }));

      const getInstance = () => this;
      const onSelectionChange = (table) => this.syncSelectedDraftRows(table);
      const applyReadOnly = (columns = []) =>
        columns.map((column) => {
          const next = { ...column };
          if (Array.isArray(next.columns)) {
            next.columns = applyReadOnly(next.columns);
          }
          if (next.field === "selected") {
            next.cellClick = null;
            next.contextMenu = () => [];
            next.formatter = (cell) => {
              const rowData = cell?.getRow?.().getData?.() || {};
              const checked = rowData.selected ? "checked" : "";
              return `<input type="checkbox" title="Select" disabled ${checked} />`;
            };
          }
          next.editable = false;
          next.editor = false;
          return next;
        });

      const libraryEditors = {
        protocols: normalizeOptions(this.protocolsList),
        analysisTypes: normalizeOptions(this.analysisTypesList),
        measuringUnits: this.libraryMeasuringUnits,
        readLengths: normalizeOptions(this.readLengthsList),
        indexTypes: normalizeOptions(this.indexTypesList),
        organisms: normalizeOptions(this.organismsList),
        getIndexReadsCount: (row) => this.getIndexReadsCount(row),
        getIndexI7Options: (row) => this.getLibraryIndexI7Options(row),
        getIndexI5Options: (row) => this.getLibraryIndexI5Options(row),
        isOtherIndexType: (row) => this.isOtherIndexType(row),
        showBarcode: this.isEditMode
      };

      const sampleEditors = {
        protocols: normalizeOptions(this.protocolsList),
        analysisTypes: normalizeOptions(this.analysisTypesList),
        measuringUnits: this.sampleMeasuringUnits,
        readLengths: normalizeOptions(this.readLengthsList),
        organisms: normalizeOptions(this.organismsList),
        nucleicAcidTypes: normalizeOptions(this.nucleicAcidTypesList),
        biosafetyLevels: this.biosafetyLevelsOptions,
        gmoOptions: this.gmoOptions,
        showBarcode: this.isEditMode
      };

      const columns =
        this.requestEditorMode === "library"
          ? getRequestEditorLibraryColumns(
              getInstance,
              libraryEditors,
              onSelectionChange
            )
          : getRequestEditorSampleColumns(
              getInstance,
              sampleEditors,
              onSelectionChange
            );

      if (!this.canEditRequest) {
        return applyReadOnly(columns);
      }

      return columns;
    },
    requestEditorDraftTableOptions() {
      const vm = this;
      const getPlaceholder = () =>
        "Use the + button to create libraries/samples.";

      const handleSelection = () => this.syncSelectedDraftRows();

      return {
        index: "tempId",
        placeholder: getPlaceholder(),
        selectable: vm.canEditRequest,
        layout: "fitColumns",
        persistenceMode: false,
        showPasteErrorRowNumber: true,
        editTriggerEvent: vm.canEditRequest ? "dblclick" : "manual",
        clipboard: vm.canEditRequest,
        enableSelectAllRange: true,
        rowFormatter: (row) => vm.applyRowStyling(row),
        rowSelectionChanged: () => handleSelection(),
        dataChanged: () => {
          if (this.isProcessingRangeClear) return;
          handleSelection();
          this.revalidateDraftRows();
        },
        onBatchCellValueChanged: (changes) => {
          this.handleDraftBatchChanges(changes);
        },
        handlePasteApplied: (rows) => vm.handlePasteApplied(rows),
        handleDeleteApplied: () => {
          const table =
            this.$refs.requestEditorDraftTableRef?.tabulatorInstance;
          const rows = table?.getRows?.() || [];
          rows.forEach((row) => row.reformat?.());
          this.revalidateDraftRows();
        },
        handleRangeCleared: (payload = []) => {
          if (!Array.isArray(payload)) return;
          const table =
            this.$refs.requestEditorDraftTableRef?.tabulatorInstance;
          const tableComponent = this.$refs.requestEditorDraftTableRef;
          const indexTypesToFetch = new Set();
          tableComponent?.beginBulkMutation?.();
          try {
            payload.forEach((entry) => {
              const rowData = entry?.rowData || {};
              const fields = entry?.fields || [];
              if (!fields.length) return;
              const rowComp =
                table?.getRow?.(rowData?.tempId) ||
                (rowData?.pk !== undefined && rowData?.pk !== null
                  ? table?.getRow?.(rowData.pk)
                  : null) ||
                null;
              if (rowComp) {
                const liveRowData = rowComp?.getData?.() || {};
                if (this.isEditMode && liveRowData?.tempId && liveRowData?.pk) {
                  this.markDirtyFields(liveRowData.tempId, fields);
                }
                const resetResult = this.applyDependentResetsForChangedFields(
                  rowComp,
                  fields
                );
                if (resetResult?.indexTypeId) {
                  indexTypesToFetch.add(String(resetResult.indexTypeId));
                }
              }
            });
          } finally {
            tableComponent?.endBulkMutation?.();
          }
          if (this.requestEditorMode === "library" && indexTypesToFetch.size) {
            indexTypesToFetch.forEach((typeId) => {
              this.fetchIndexOptionsForType(typeId);
            });
          }
          this.$nextTick(() => this.revalidateDraftRows());
        },
        handleRangeClearStart: () => {
          this.isProcessingRangeClear = true;
        },
        handleRangeClearEnd: () => {
          this.$nextTick(() => {
            this.isProcessingRangeClear = false;
          });
        },
        cellEditing: (cell) => vm.handleCellEditing(cell),
        handleCellEdited: (cell) => vm.handleCellEdited(cell),
        handleRenderComplete: () => {
          this.applyValidationStyling();
          this.bindRangeSelectionListeners();
          this.updateRangeSelectionState();
          if (this.isEditMode && this.pendingDirtyTrackingResume) {
            this.pendingDirtyTrackingResume = false;
            this.resumeDirtyTracking();
          }
        },
        fakeLoadingStart: () => this.fakeLoadingStart(),
        fakeLoadingStop: () => this.fakeLoadingStop()
      };
    },
    footerLabel() {
      if (this.isEditMode) {
        const count =
          this.editRecordsByType?.[this.requestEditorMode]?.length || 0;
        const labels =
          this.requestEditorMode === "library"
            ? { singular: "library", plural: "libraries" }
            : { singular: "sample", plural: "samples" };
        const noun = count === 1 ? labels.singular : labels.plural;
        return `${count} ${noun} in this request.`;
      }
      const count = this.validDraftCount;
      const labels =
        this.requestEditorMode === "library"
          ? { singular: "library", plural: "libraries" }
          : { singular: "sample", plural: "samples" };
      const noun = count === 1 ? labels.singular : labels.plural;
      return `${count} valid ${noun} ready for this request.`;
    }
  },
  methods: {
    getTable() {
      return this.$refs.requestEditorDraftTableRef?.tabulatorInstance || null;
    },
    triggerClipboardPaste() {
      this.$refs.requestEditorDraftTableRef?.triggerClipboardPaste?.();
    },
    schedulePrepareRequestEditorModal() {
      if (this.prepareTimer) {
        clearTimeout(this.prepareTimer);
      }
      if (this.isEditMode) {
        this.isRequestLoading = true;
      }
      this.prepareTimer = setTimeout(() => {
        this.prepareTimer = null;
        this.prepareRequestEditorModal();
      }, 0);
    },
    findIndexOptionByValue(options = [], value) {
      if (value === "" || value === undefined || value === null) return null;
      const match = String(value);
      return options.find((option) => String(option.value) === match) || null;
    },
    fieldHasValue(value) {
      if (value === null || value === undefined) return false;
      if (typeof value === "string") return value.trim() !== "";
      return value !== "";
    },
    refreshRowFormatting(row) {
      if (row?.reformat) {
        row.reformat();
        return;
      }
      const table = row?.getTable?.();
      table?.redraw?.();
    },
    refreshRowsForIndexType(typeKey) {
      const table = this.$refs.requestEditorDraftTableRef?.tabulatorInstance;
      const rows = table?.getRows?.() || [];
      rows.forEach((row) => {
        const rowData = row?.getData?.() || {};
        if (String(rowData.index_type || "") !== String(typeKey)) return;
        row?.reformat?.();
      });
    },
    handlePasteApplied(rows = []) {
      if (!this.canEditRequest) return;
      const table = this.$refs.requestEditorDraftTableRef?.tabulatorInstance;
      const list = Array.isArray(rows) ? rows : [];
      list.forEach((row) => {
        const rowRef = row?.getData
          ? row
          : table?.getRow?.(row?.tempId) || null;
        const rowData = rowRef?.getData ? rowRef.getData() : row;
        if (
          !rowData?.index_type ||
          (!rowData?.index_i7 && !rowData?.index_i5)
        ) {
          return;
        }
        const typeKey = String(rowData.index_type);
        const reads = this.getIndexReadsCount(rowData);
        if (reads >= 2) {
          const hasI7 = this.fieldHasValue(rowData.index_i7);
          const hasI5 = this.fieldHasValue(rowData.index_i5);
          const optionsReady =
            this.indexI7OptionsByType[typeKey] &&
            this.indexI5OptionsByType[typeKey] &&
            this.indexPairsByType[typeKey];

          if (optionsReady && rowRef) {
            if (hasI7) {
              this.tryAutoSelectI5(rowRef, rowData);
            } else if (hasI5) {
              this.tryAutoSelectI7(rowRef, rowData);
            }
          } else if (rowData.index_type) {
            this.fetchIndexOptionsForType(rowData.index_type, {
              row: rowRef,
              selectedI7: hasI7 ? rowData.index_i7 : null,
              selectedI5: !hasI7 && hasI5 ? rowData.index_i5 : null
            });
          }
        }
        if (rowData.index_type) {
          const hasI7 = Boolean(this.indexI7OptionsByType[typeKey]);
          const hasI5 = Boolean(this.indexI5OptionsByType[typeKey]);
          if (hasI7 && hasI5) {
            this.refreshRowsForIndexType(typeKey);
          } else {
            this.fetchIndexOptionsForType(rowData.index_type);
          }
        }
      });
      this.$nextTick(() => {
        this.revalidateDraftRows();
        this.applyValidationStyling();
      });
    },
    fakeLoadingStart() {
      if (this.fakeLoadingTimer) {
        clearTimeout(this.fakeLoadingTimer);
        this.fakeLoadingTimer = null;
      }
      this.fakeLoading = true;
    },
    fakeLoadingStop() {
      if (this.fakeLoadingTimer) {
        clearTimeout(this.fakeLoadingTimer);
      }
      this.fakeLoadingTimer = setTimeout(() => {
        this.fakeLoading = false;
        this.fakeLoadingTimer = null;
      }, 300);
    },
    hasMeasuredValueUnit(rowData) {
      const unit = rowData?.measuring_unit;
      return Boolean(unit) && unit !== "Unknown";
    },
    isLibraryFieldEditable(field, rowData) {
      if (field === "library_type") return Boolean(rowData.library_protocol);
      if (field === "index_i7") return this.getIndexReadsCount(rowData) >= 1;
      if (field === "index_i5") return this.getIndexReadsCount(rowData) >= 2;
      if (field === "measured_value") return this.hasMeasuredValueUnit(rowData);
      return true;
    },
    isSampleFieldEditable(field, rowData) {
      if (field === "library_protocol")
        return Boolean(rowData.nucleic_acid_type);
      if (field === "library_type") return Boolean(rowData.library_protocol);
      if (field === "measured_value") return this.hasMeasuredValueUnit(rowData);
      if (field === "gmo")
        return this.isGmoAllowedInputType(rowData.nucleic_acid_type);
      return true;
    },
    isFieldEditable(field, rowData) {
      if (this.requestEditorMode === "library") {
        return this.isLibraryFieldEditable(field, rowData);
      }
      return this.isSampleFieldEditable(field, rowData);
    },
    isFieldRequired(field, rowData) {
      if (field === "index_i7") {
        return this.requestEditorMode === "library"
          ? this.getIndexReadsCount(rowData) >= 1
          : false;
      }
      if (field === "index_i5") {
        return this.requestEditorMode === "library"
          ? this.getIndexReadsCount(rowData) >= 2
          : false;
      }
      if (field === "measured_value") {
        return this.hasMeasuredValueUnit(rowData);
      }
      if (field === "gmo") {
        return this.isGmoAllowedInputType(rowData.nucleic_acid_type);
      }
      return this.requestEditorMode === "library"
        ? LIBRARY_REQUIRED_FIELDS.has(field)
        : SAMPLE_REQUIRED_FIELDS.has(field);
    },
    toggleFormPanel() {
      this.isFormPanelCollapsed = !this.isFormPanelCollapsed;
    },
    openShortcutHelp() {
      this.cancelShortcutHelpClose();
      this.showShortcutHelp = true;
    },
    scheduleShortcutHelpClose() {
      this.cancelShortcutHelpClose();
      this.shortcutHelpCloseTimer = setTimeout(() => {
        this.showShortcutHelp = false;
        this.shortcutHelpCloseTimer = null;
      }, 120);
    },
    cancelShortcutHelpClose() {
      if (!this.shortcutHelpCloseTimer) return;
      clearTimeout(this.shortcutHelpCloseTimer);
      this.shortcutHelpCloseTimer = null;
    },
    openFeatureHelp() {
      this.cancelFeatureHelpClose();
      this.showFeatureHelp = true;
    },
    scheduleFeatureHelpClose() {
      this.cancelFeatureHelpClose();
      this.featureHelpCloseTimer = setTimeout(() => {
        this.showFeatureHelp = false;
        this.featureHelpCloseTimer = null;
      }, 120);
    },
    cancelFeatureHelpClose() {
      if (!this.featureHelpCloseTimer) return;
      clearTimeout(this.featureHelpCloseTimer);
      this.featureHelpCloseTimer = null;
    },
    handleShortcutHelpOutsideClick(event) {
      if (!this.showShortcutHelp) return;
      const container = this.$el?.querySelector?.(".shortcut-help");
      if (container && container.contains(event.target)) return;
      this.cancelShortcutHelpClose();
      this.showShortcutHelp = false;
    },
    handleFeatureHelpOutsideClick(event) {
      if (!this.showFeatureHelp) return;
      const container = this.$el?.querySelector?.(".feature-help");
      if (container && container.contains(event.target)) return;
      this.cancelFeatureHelpClose();
      this.showFeatureHelp = false;
    },
    emitClose() {
      this.$emit("close");
    },
    requestCloseModal() {
      if (this.saving) return;
      if (!this.hasUnsavedChanges()) {
        this.emitClose();
        return;
      }
      this.showCloseConfirm = true;
    },
    confirmCloseModal() {
      this.showCloseConfirm = false;
      this.emitClose();
    },
    cancelCloseModal() {
      this.showCloseConfirm = false;
    },
    handleCloseConfirmKeydown(event) {
      if (!this.showCloseConfirm) return;
      if (event.key === "Escape") {
        event.preventDefault();
        this.cancelCloseModal();
        return;
      }
      if (event.key === "Enter") {
        event.preventDefault();
        this.confirmCloseModal();
      }
    },
    hasUnsavedChanges() {
      const costUnitRaw = this.newRequest.cost_unit || "";
      const description = (this.newRequest.description || "").trim();
      if (this.isEditMode) {
        const hasDirtyTableEdits = Object.values(
          this.dirtyFieldsByRowId || {}
        ).some((fields) =>
          fields instanceof Set ? fields.size > 0 : Boolean(fields)
        );
        if (hasDirtyTableEdits) {
          return true;
        }
        const snapshot = this.editSnapshot || {};
        const baseCostUnitRaw = snapshot.cost_unit || "";
        const costUnit = costUnitRaw === "" ? "" : String(costUnitRaw);
        const baseCostUnit =
          baseCostUnitRaw === "" ? "" : String(baseCostUnitRaw);
        const baseDescription = (snapshot.description || "").trim();
        const currentRelatedRequestIds = (this.relatedProjectsSelection || [])
          .map((project) => String(project.id))
          .sort();
        const baseRelatedRequestIds = (snapshot.related_request_ids || [])
          .map(String)
          .sort();
        const currentFileIds = (this.uploadedRequestFileIds || []).map(String);
        const baseFileIds = (snapshot.fileIds || []).map(String);
        const filesChanged =
          currentFileIds.length !== baseFileIds.length ||
          currentFileIds.some((id) => !baseFileIds.includes(id));
        const currentFileTypes = this.requestFileTypesPayload();
        const baseFileTypes = snapshot.fileTypes || {};
        const fileTypesChanged =
          JSON.stringify(currentFileTypes) !== JSON.stringify(baseFileTypes);
        const relatedRequestsChanged =
          currentRelatedRequestIds.length !== baseRelatedRequestIds.length ||
          currentRelatedRequestIds.some(
            (id, index) => id !== baseRelatedRequestIds[index]
          );
        return (
          costUnit !== baseCostUnit ||
          description !== baseDescription ||
          relatedRequestsChanged ||
          filesChanged ||
          fileTypesChanged
        );
      }
      if (costUnitRaw || description) return true;
      if (
        this.uploadedRequestFiles.length ||
        this.uploadedRequestFileIds.length
      )
        return true;
      return this.getDraftTableRows().length > 0;
    },
    handleApplyToAllIndexPairs(rows = []) {
      if (!this.canEditRequest || !Array.isArray(rows)) return;
      const table = this.$refs.requestEditorDraftTableRef?.tabulatorInstance;
      rows.forEach((row) => {
        let rowRef = row?.getData ? row : null;
        if (!rowRef && table) {
          const rowKey = row?.tempId ?? row?.pk;
          if (rowKey !== undefined && rowKey !== null) {
            rowRef = table.getRow?.(rowKey) || null;
          }
        }
        const rowData = rowRef?.getData ? rowRef.getData() : row;
        if (!rowData?.index_type) return;
        const typeKey = String(rowData.index_type);
        const reads = this.getIndexReadsCount(rowData);
        if (reads >= 2) {
          const hasI7 = this.fieldHasValue(rowData.index_i7);
          const hasI5 = this.fieldHasValue(rowData.index_i5);
          const optionsReady =
            this.indexI7OptionsByType[typeKey] &&
            this.indexI5OptionsByType[typeKey] &&
            this.indexPairsByType[typeKey];
          if (optionsReady && rowRef) {
            if (hasI7) {
              this.tryAutoSelectI5(rowRef, rowData);
            } else if (hasI5) {
              this.tryAutoSelectI7(rowRef, rowData);
            }
          } else if (rowData.index_type) {
            this.fetchIndexOptionsForType(rowData.index_type, {
              row: rowRef,
              selectedI7: hasI7 ? rowData.index_i7 : null,
              selectedI5: !hasI7 && hasI5 ? rowData.index_i5 : null
            });
          }
        }
        if (rowData.index_type) {
          const hasI7 = Boolean(this.indexI7OptionsByType[typeKey]);
          const hasI5 = Boolean(this.indexI5OptionsByType[typeKey]);
          if (hasI7 && hasI5) {
            this.refreshRowsForIndexType(typeKey);
          } else {
            this.fetchIndexOptionsForType(rowData.index_type);
          }
        }
      });
    },
    handleApplyToAllIndexPairing(cell, tableRef) {
      if (!this.canEditRequest || this.requestEditorMode !== "library") return;
      const field = cell?.getField?.();
      if (field !== "index_i7" && field !== "index_i5") return;
      const rows = tableRef?.getRows?.() || [];
      this.handleApplyToAllIndexPairs(rows);
    },
    applyToAllFromCell(cell, { tableRef, tabulatorInstance } = {}) {
      if (!cell) return;
      this.fakeLoadingStart();
      const changedField = cell.getField?.() || null;
      const sourceValue = cell.getValue?.();
      const table =
        tabulatorInstance?.getTable?.() ||
        tabulatorInstance?.tabulatorInstance ||
        tabulatorInstance ||
        tableRef?.getTable?.() ||
        tableRef ||
        this.$refs.requestEditorDraftTableRef?.tabulatorInstance ||
        null;
      if (!table) {
        this.fakeLoadingStop();
        return;
      }
      const rows = table?.getRows?.() || [];
      const previousValueByRowId = new Map();
      if (changedField) {
        rows.forEach((rowComp) => {
          const rowData = rowComp?.getData?.() || {};
          const rowKey = rowData?.tempId ?? rowData?.pk ?? rowComp;
          previousValueByRowId.set(rowKey, rowData?.[changedField]);
        });
      }
      let skippedIncompatibleRows = 0;
      if (changedField) {
        rows.forEach((rowComp) => {
          const targetCell = rowComp?.getCell?.(changedField);
          if (!targetCell || !this.isEditableRangeCell(targetCell)) return;
          const rowData = rowComp?.getData?.() || {};
          const isAllowed = this.isValueAllowedForApplyAll(
            targetCell,
            changedField,
            rowData,
            sourceValue
          );
          if (!isAllowed) {
            skippedIncompatibleRows += 1;
            return;
          }
          if (rowData?.[changedField] !== sourceValue) {
            rowComp.update({ ...rowData, [changedField]: sourceValue });
          }
        });
      } else {
        applyValueToAllRows(cell, () => table, {
          blockActionsOnDisabledCells: true
        });
      }
      const indexTypesToFetch = new Set();
      if (changedField) {
        rows.forEach((rowComp) => {
          const rowData = rowComp?.getData?.() || {};
          const rowKey = rowData?.tempId ?? rowData?.pk ?? rowComp;
          const before = previousValueByRowId.get(rowKey);
          const after = rowData?.[changedField];
          if (before === after) return;
          const resetResult = this.applyDependentResetsForChangedFields(
            rowComp,
            [changedField]
          );
          if (resetResult?.indexTypeId) {
            indexTypesToFetch.add(String(resetResult.indexTypeId));
          }
        });
      }
      if (this.requestEditorMode === "library" && indexTypesToFetch.size) {
        indexTypesToFetch.forEach((typeId) => {
          this.fetchIndexOptionsForType(typeId);
        });
      }
      if (skippedIncompatibleRows > 0) {
        showNotification(
          `${skippedIncompatibleRows} row(s) skipped: value is not valid for their current dependent selections.`,
          "warning"
        );
      }
      rows.forEach((rowComp) => this.refreshRowFormatting(rowComp));
      this.handleApplyToAllIndexPairing(cell, table);
      this.$nextTick(() => {
        this.revalidateDraftRows();
        this.applyValidationStyling();
        this.fakeLoadingStop();
        this.restoreDraftTableFocus();
      });
    },
    handleApplyToAllFromContext(payload = {}) {
      this.applyToAllFromCell(payload?.cell, {
        tableRef: payload?.tableRef,
        tabulatorInstance: payload?.tabulatorInstance
      });
    },
    emitSaved(payload) {
      this.$emit("saved", payload);
    },
    resetState() {
      this.requestEditorMode = "library";
      this.isFormPanelCollapsed = false;
      this.requestEditorDraftRows = [];
      this.selectedDraftRowIds = [];
      this.draftValidationState = {};
      this.validDraftCount = 0;
      this.isRequestSaving = false;
      this.draftRowCounter = 0;
      this.newRequest = {
        cost_unit: "",
        description: ""
      };
      this.costUnitError = "";
      this.uploadedRequestFiles = [];
      this.uploadedRequestFileIds = [];
      this.showToggleConfirm = false;
      this.showDeleteConfirm = false;
      this.showCloseConfirm = false;
      this.showFileDeleteConfirm = false;
      this.showShortcutHelp = false;
      this.showFeatureHelp = false;
      this.pendingToggleMode = null;
      this.existingRecords = [];
      this.editSnapshot = {
        cost_unit: "",
        description: "",
        fileIds: [],
        fileTypes: {},
        related_request_ids: []
      };
      this.requestName = "";
      this.restrictPermissions = false;
      this.isRequestLoading = false;
      this.requestOwnerId = null;
      this.originalRequestOwnerId = null;
      this.requestOwnerQuery = "";
      this.requestOwnerSuggestions = [];
      this.resetRequestOwnerAutocomplete();
      this.relatedProjectQuery = "";
      this.relatedProjectSuggestions = [];
      this.resetRelatedProjectAutocomplete();
      this.relatedProjectsSelection = [];
      this.clearAutocompleteTimer("requestOwnerSearchTimer");
      this.clearAutocompleteTimer("relatedProjectSearchTimer");
      this.resetDirtyTracking();
      this.editRecordsByType = {
        library: [],
        sample: []
      };
      this.editRecordTypesAvailable = {
        library: false,
        sample: false
      };
      this.pendingFileDelete = null;
      this.addRowCount = this.isEditMode ? 0 : 1;
      this.hasRangeSelection = false;
      this.unbindRangeSelectionListeners();
      if (this.$refs.requestFileInput) {
        this.$refs.requestFileInput.value = "";
      }
      this.$nextTick(() => this.applyValidationStyling());
    },
    resetDirtyTracking() {
      this.allowDirtyTracking = false;
      this.suppressNextDirtyBatch = false;
      this.pendingDirtyTrackingResume = false;
      this.dirtyFieldsByRowId = {};
      this.validationFieldsByRowId = {};
    },
    pauseDirtyTracking({ suppressNextBatch = false } = {}) {
      this.allowDirtyTracking = false;
      if (suppressNextBatch) {
        this.suppressNextDirtyBatch = true;
      }
    },
    resumeDirtyTracking() {
      this.allowDirtyTracking = true;
    },
    handleKeyDown(event) {
      if (!this.show) return;
      if (this.showShortcutHelp && event.key === "Escape") {
        this.cancelShortcutHelpClose();
        this.showShortcutHelp = false;
        return;
      }
      if (this.showFeatureHelp && event.key === "Escape") {
        this.cancelFeatureHelpClose();
        this.showFeatureHelp = false;
        return;
      }
      const key = event.key?.toLowerCase?.();
      const isCtrl = event.ctrlKey || event.metaKey;
      if (!isCtrl || key !== "x") return;
      const target = event.target;
      const isInput =
        target &&
        (target.tagName === "INPUT" ||
          target.tagName === "TEXTAREA" ||
          target.isContentEditable);
      if (isInput) return;
      if (!this.hasEditableRangeSelection || !this.canEditRequest) return;
      event.preventDefault();
      this.triggerTableCut();
    },
    async prepareRequestEditorModal() {
      if (this.isPreparingModal) return;
      this.isPreparingModal = true;
      this.resetState();
      await this.ensureModalOptionsLoaded();
      if (this.isEditMode) {
        await this.prepareEditRequestModal();
      }
      await this.fetchCostUnits();
      this.isPreparingModal = false;
    },
    async prepareEditRequestModal() {
      if (!this.requestId) {
        showNotification("Request ID is missing.", "error");
        return;
      }
      this.isRequestLoading = true;
      try {
        const meta = this.requestMeta || null;
        const fetchRequest = true;
        const metaFiles = Array.isArray(meta?.files) ? meta.files : [];
        const needsFileDetails =
          !metaFiles.length ||
          metaFiles.some(
            (file) =>
              !file?.path || file?.size === undefined || file?.size === null
          );
        const fetchFiles = needsFileDetails;

        const results = await Promise.allSettled([
          fetchRequest
            ? axiosRef.get(`${urlStringStart}/api/requests/${this.requestId}/`)
            : Promise.resolve({ data: meta }),
          fetchFiles
            ? axiosRef.get(
                `${urlStringStart}/api/requests/${this.requestId}/get_files/`
              )
            : Promise.resolve({ data: meta?.files || [] }),
          axiosRef.get(`${urlStringStart}/api/libraries/`, {
            params: { request_id: this.requestId }
          }),
          axiosRef.get(`${urlStringStart}/api/samples/`, {
            params: { request_id: this.requestId }
          })
        ]);

        const requestRes =
          results[0].status === "fulfilled" ? results[0].value : null;
        const filesRes =
          results[1].status === "fulfilled" ? results[1].value : null;
        const librariesRes =
          results[2].status === "fulfilled" ? results[2].value : null;
        const samplesRes =
          results[3].status === "fulfilled" ? results[3].value : null;

        if (!requestRes) {
          showNotification("Request details failed to load.", "error");
          return;
        }

        const requestData = requestRes?.data || {};
        this.requestName = requestData.name || "";
        this.restrictPermissions = Boolean(requestData.restrict_permissions);
        this.requestOwnerId = requestData.user || null;
        this.originalRequestOwnerId = requestData.user || null;
        this.originalRequestOwnerQuery = requestData.user_full_name
          ? `${requestData.user_full_name}${requestData.owner_pi_name ? ` (${requestData.owner_pi_name})` : ""}`
          : "";
        this.requestOwnerQuery = this.originalRequestOwnerQuery;
        const relatedRequestIds = Array.isArray(requestData.related_requests)
          ? requestData.related_requests
              .map((id) => Number(id))
              .filter((id) => Number.isInteger(id) && id > 0)
          : [];
        this.relatedProjectsSelection = relatedRequestIds.map((id) => ({
          id,
          name: `Request ${id}`
        }));
        if (relatedRequestIds.length) {
          await this.fetchRelatedProjects({ ids: relatedRequestIds });
        }
        this.newRequest.cost_unit = requestData.cost_unit || "";
        this.newRequest.description = requestData.description || "";

        if (this.isStaffUser) {
          await this.fetchRequestUsers(this.requestOwnerQuery);
        }

        const libraries = Array.isArray(librariesRes?.data?.data)
          ? librariesRes.data.data
          : [];
        const samples = Array.isArray(samplesRes?.data?.data)
          ? samplesRes.data.data
          : [];

        this.editRecordsByType = {
          library: libraries,
          sample: samples
        };
        this.editRecordTypesAvailable = {
          library: libraries.length > 0,
          sample: samples.length > 0
        };
        const initialMode = this.editRecordTypesAvailable.library
          ? "library"
          : this.editRecordTypesAvailable.sample
            ? "sample"
            : "library";
        this.requestEditorMode = initialMode;
        this.loadEditRecordsForMode(initialMode);
        const indexTypes = [
          ...new Set(
            libraries
              .map((record) => record?.index_type)
              .filter(
                (value) => value !== null && value !== undefined && value !== ""
              )
              .map((value) => String(value))
          )
        ];
        await Promise.all(
          indexTypes.map((typeId) => this.fetchIndexOptionsForType(typeId))
        );
        indexTypes.forEach((typeId) => this.refreshRowsForIndexType(typeId));

        this.existingRecords = [
          ...libraries.map((record) => ({
            pk: record.pk,
            record_type: "Library",
            name: record.name,
            barcode: record.barcode
          })),
          ...samples.map((record) => ({
            pk: record.pk,
            record_type: "Sample",
            name: record.name,
            barcode: record.barcode
          }))
        ];

        const files = Array.isArray(filesRes?.data)
          ? filesRes.data
          : requestData.files || [];
        this.uploadedRequestFiles = files.map((file) =>
          normaliseRequestFile({
            id: file.id ?? file.pk,
            name: file.name,
            size: file.size ?? null,
            path: file.path ?? file.file_path ?? "",
            file_type: file.file_type
          })
        );
        this.uploadedRequestFileIds = this.uploadedRequestFiles
          .map((file) => file.id)
          .filter((id) => id !== undefined && id !== null);
        this.editSnapshot = {
          cost_unit: this.newRequest.cost_unit || "",
          description: this.newRequest.description || "",
          fileIds: [...this.uploadedRequestFileIds],
          fileTypes: requestFileTypesPayload(this.uploadedRequestFiles),
          related_request_ids: this.relatedProjectsSelection.map(
            (project) => project.id
          )
        };
      } catch (error) {
        handleError(error);
      } finally {
        this.isRequestLoading = false;
        this.requestDataReady = true;
      }
    },
    async ensureModalOptionsLoaded() {
      await Promise.all([
        this.fetchFilterOptions(),
        this.fetchIndexTypesList(),
        this.fetchNucleicAcidTypes(),
        this.fetchOrganismsList()
      ]);
    },
    loadEditRecordsForMode(mode) {
      const normalized = mode === "sample" ? "sample" : "library";
      this.pauseDirtyTracking({ suppressNextBatch: true });
      this.pendingDirtyTrackingResume = true;
      const source =
        normalized === "library"
          ? this.editRecordsByType.library
          : this.editRecordsByType.sample;
      const mapped = source.map((record) => {
        if (normalized === "library") {
          return {
            tempId: `edit-${record.pk}`,
            pk: record.pk,
            selected: false,
            record_type: "Library",
            barcode: record.barcode || "",
            barcode_original: record.barcode || "",
            name: record.name || "",
            library_protocol: record.library_protocol || null,
            library_type: record.library_type || null,
            measuring_unit: record.measuring_unit || null,
            measured_value: record.measured_value ?? null,
            mean_fragment_size: record.mean_fragment_size ?? null,
            volume: record.volume ?? null,
            read_length: record.read_length || null,
            sequencing_depth: record.sequencing_depth ?? null,
            index_type: record.index_type || null,
            index_reads: record.index_reads ?? null,
            index_i7: record.index_i7 || null,
            index_i5: record.index_i5 || null,
            organism: record.organism || null,
            comments: record.comments || ""
          };
        }
        return {
          tempId: `edit-${record.pk}`,
          pk: record.pk,
          selected: false,
          record_type: "Sample",
          barcode: record.barcode || "",
          barcode_original: record.barcode || "",
          name: record.name || "",
          nucleic_acid_type: record.nucleic_acid_type || null,
          library_protocol: record.library_protocol || null,
          library_type: record.library_type || null,
          measuring_unit: record.measuring_unit || null,
          measured_value: record.measured_value ?? null,
          volume: record.volume ?? null,
          read_length: record.read_length || null,
          sequencing_depth: record.sequencing_depth ?? null,
          organism: record.organism || null,
          comments: record.comments || "",
          biosafety_level: record.biosafety_level || null,
          gmo: record.gmo
        };
      });
      this.requestEditorDraftRows = mapped;
      this.selectedDraftRowIds = [];
      this.draftRowCounter = mapped.length;
      this.$nextTick(() => {
        this.revalidateDraftRows();
      });
    },
    persistDraftRowsToEditRecords(mode) {
      const normalized = mode === "sample" ? "sample" : "library";
      const rows = this.getDraftTableRows();
      if (normalized === "library") {
        this.editRecordsByType.library = rows;
      } else {
        this.editRecordsByType.sample = rows;
      }
    },
    triggerRequestFileUpload() {
      if (!this.canEditRequest) return;
      this.$refs.requestFileInput?.click?.();
    },
    triggerApplyToAll() {
      const table = this.$refs.requestEditorDraftTableRef?.tabulatorInstance;
      const cell = table?.getRanges?.()?.[0]?.getCells?.()?.[0]?.[0];
      this.applyToAllFromCell(cell, { tabulatorInstance: table });
    },
    restoreDraftTableFocus() {
      const tableComponent = this.$refs.requestEditorDraftTableRef;
      if (!tableComponent) return;
      this.$nextTick(() => {
        tableComponent.restoreLastFocusedCell?.();
      });
    },

    triggerTableCopy() {
      const table = this.$refs.requestEditorDraftTableRef?.tabulatorInstance;
      const element = document.activeElement;
      if (
        element &&
        (element.tagName === "INPUT" || element.tagName === "TEXTAREA")
      ) {
        element.blur();
      }
      table?.copyToClipboard?.();
      this.restoreDraftTableFocus();
    },
    triggerTableCut() {
      if (!this.hasEditableRangeSelection || !this.canEditRequest) return;
      this.triggerTableCopy();
      this.triggerTableClear();
    },
    triggerTablePaste() {
      const tableComponent = this.$refs.requestEditorDraftTableRef;
      const element = document.activeElement;
      if (
        element &&
        (element.tagName === "INPUT" || element.tagName === "TEXTAREA")
      ) {
        element.blur();
      }
      tableComponent?.triggerClipboardPaste?.();
      this.restoreDraftTableFocus();
    },
    triggerTableClear() {
      const table = this.$refs.requestEditorDraftTableRef?.tabulatorInstance;
      const element = document.activeElement;
      if (
        element &&
        (element.tagName === "INPUT" || element.tagName === "TEXTAREA")
      ) {
        element.blur();
      }
      const keyEvent = new KeyboardEvent("keydown", {
        key: "Delete",
        bubbles: true
      });
      table?.element?.dispatchEvent?.(keyEvent);
      this.restoreDraftTableFocus();
    },
    updateRangeSelectionState() {
      const table = this.$refs.requestEditorDraftTableRef?.tabulatorInstance;
      const ranges = table?.getRanges?.() || [];
      let hasSelection = false;
      let singleCell = false;
      let hasEditableCell = false;
      let singleCellEditable = false;
      if (ranges.length) {
        const cells = ranges[0]?.getCells?.() || [];
        hasSelection = cells.length > 0 && (cells[0]?.length || 0) > 0;
        singleCell = cells.length === 1 && (cells[0]?.length || 0) === 1;
        cells.forEach((row) => {
          row.forEach((cell) => {
            if (this.isEditableRangeCell(cell)) {
              hasEditableCell = true;
            }
          });
        });
        if (singleCell) {
          const cell = cells[0]?.[0] || null;
          singleCellEditable = this.isEditableRangeCell(cell);
        }
      }
      this.hasRangeSelection = hasSelection;
      this.hasEditableRangeSelection = hasSelection && hasEditableCell;
      this.isSingleCellSelected =
        hasSelection && singleCell && singleCellEditable;
    },
    isEditableRangeCell(cell) {
      if (!cell) return false;
      const field = cell.getField?.();
      if (!field || field === "selected") return false;
      const columnDef = cell.getColumn?.().getDefinition?.() || {};
      if (columnDef.editor === false) return false;
      if (typeof columnDef.editable === "function") {
        const rowData = cell.getRow?.().getData?.() || {};
        return columnDef.editable({
          getRow: () => ({ getData: () => rowData })
        });
      }
      if (typeof columnDef.editable === "boolean") {
        return columnDef.editable;
      }
      return true;
    },
    bindRangeSelectionListeners() {
      const element = document.getElementById("requestEditorDraftTable");
      if (!element || this.rangeListenersAttached) {
        return;
      }
      this.rangeSelectionHandler = () => {
        requestAnimationFrame(() => this.updateRangeSelectionState());
      };
      element.addEventListener("mouseup", this.rangeSelectionHandler, true);
      element.addEventListener("keyup", this.rangeSelectionHandler, true);
      element.addEventListener("keydown", this.rangeSelectionHandler, true);
      element.addEventListener("click", this.rangeSelectionHandler, true);
      this.rangeSelectionElement = element;
      this.rangeListenersAttached = true;
    },
    unbindRangeSelectionListeners() {
      if (
        !this.rangeListenersAttached ||
        !this.rangeSelectionElement ||
        !this.rangeSelectionHandler
      ) {
        this.rangeListenersAttached = false;
        return;
      }
      const element = this.rangeSelectionElement;
      const handler = this.rangeSelectionHandler;
      element.removeEventListener("mouseup", handler, true);
      element.removeEventListener("keyup", handler, true);
      element.removeEventListener("keydown", handler, true);
      element.removeEventListener("click", handler, true);
      this.rangeSelectionElement = null;
      this.rangeSelectionHandler = null;
      this.rangeListenersAttached = false;
    },
    addDraftRow(count = 1) {
      if (this.isEditMode && !this.canEditRequest) return;
      const total = Number(count);
      if (!Number.isFinite(total) || total <= 0) return;
      const newRows = [];
      for (let i = 0; i < total; i += 1) {
        this.draftRowCounter += 1;
        const tempId = `draft-${Date.now()}-${this.draftRowCounter}-${i}`;
        const baseRow = {
          tempId,
          selected: false,
          name: ""
        };
        const row =
          this.requestEditorMode === "sample"
            ? { ...baseRow, gmo: null }
            : baseRow;
        newRows.push(row);
      }
      this.requestEditorDraftRows = [
        ...this.requestEditorDraftRows,
        ...newRows
      ];
      this.$nextTick(() => this.revalidateDraftRows());
      if (total > 5) {
        this.addRowCount = 0;
      }
    },
    requestDeleteSelectedDraftRows() {
      if (this.isEditMode && !this.canEditRequest) return;
      if (!this.selectedDraftRowIds.length) return;
      this.showDeleteConfirm = true;
    },
    confirmDeleteSelectedRows() {
      this.showDeleteConfirm = false;
      this.deleteSelectedDraftRows();
    },
    cancelDeleteSelectedRows() {
      this.showDeleteConfirm = false;
    },
    handleDeleteConfirmKeydown(event) {
      if (!this.showDeleteConfirm) return;
      if (event.key === "Escape") {
        event.preventDefault();
        this.cancelDeleteSelectedRows();
        return;
      }
      if (event.key === "Enter") {
        event.preventDefault();
        this.confirmDeleteSelectedRows();
      }
    },
    deleteSelectedDraftRows() {
      if (!this.selectedDraftRowIds.length) return;
      if (this.isEditMode) {
        this.deleteSelectedEditRows();
        return;
      }
      const ids = new Set(this.selectedDraftRowIds);
      this.requestEditorDraftRows = this.requestEditorDraftRows.filter(
        (row) => !ids.has(row.tempId)
      );
      this.selectedDraftRowIds = [];
      this.$nextTick(() => this.revalidateDraftRows());
    },
    handleRecordTypeSwitch(mode) {
      const normalized = mode === "sample" ? "sample" : "library";
      if (this.requestEditorMode === normalized) return;
      this.requestEditorMode = normalized;
      if (this.isEditMode) {
        this.loadEditRecordsForMode(normalized);
        this.$nextTick(() => this.scrollRequestFormPanelToTop());
      } else {
        this.requestEditorDraftRows = [];
        this.selectedDraftRowIds = [];
        this.draftValidationState = {};
        this.validDraftCount = 0;
        this.draftRowCounter = 0;
        this.$nextTick(() => {
          const table =
            this.$refs.requestEditorDraftTableRef?.tabulatorInstance;
          table?.clearData?.();
          this.applyValidationStyling();
          this.scrollRequestFormPanelToTop();
        });
      }
    },
    scrollRequestFormPanelToTop() {
      const panel = this.$refs.requestFormPanel;
      if (!panel) return;
      panel.scrollTo?.({ top: 0, behavior: "auto" });
      panel.scrollTop = 0;
    },
    requestRecordTypeSwitch(event) {
      if (!this.canEditRequest) return;
      if (this.isEditMode) {
        const nextMode = event?.target?.checked ? "sample" : "library";
        const normalized = nextMode === "sample" ? "sample" : "library";
        const isAvailable =
          normalized === "library"
            ? this.editRecordTypesAvailable.library
            : this.editRecordTypesAvailable.sample;
        if (!isAvailable) {
          showNotification(
            `Switching library/sample mode is not available in edit mode.`,
            "warning"
          );
          if (event?.target) {
            event.target.checked = this.requestEditorMode === "sample";
          }
          return;
        }
        this.persistDraftRowsToEditRecords(this.requestEditorMode);
        this.handleRecordTypeSwitch(normalized);
        return;
      }
      const nextMode = event?.target?.checked ? "sample" : "library";
      const normalized = nextMode === "sample" ? "sample" : "library";
      if (this.requestEditorMode === normalized) return;
      if (this.requestEditorDraftRows.length > 0) {
        this.pendingToggleMode = normalized;
        this.showToggleConfirm = true;
        if (event?.target) {
          event.target.checked = this.requestEditorMode === "sample";
        }
        return;
      }
      this.handleRecordTypeSwitch(normalized);
    },
    confirmToggleSwitch() {
      if (!this.pendingToggleMode) {
        this.showToggleConfirm = false;
        return;
      }
      const nextMode = this.pendingToggleMode;
      this.pendingToggleMode = null;
      this.showToggleConfirm = false;
      this.handleRecordTypeSwitch(nextMode);
    },
    cancelToggleSwitch() {
      this.pendingToggleMode = null;
      this.showToggleConfirm = false;
    },
    handleConfirmKeydown(event) {
      if (!this.showToggleConfirm) return;
      if (event.key === "Escape") {
        event.preventDefault();
        this.cancelToggleSwitch();
        return;
      }
      if (event.key === "Enter") {
        event.preventDefault();
        this.confirmToggleSwitch();
      }
    },
    formatFileSize(size) {
      if (size === undefined || size === null) return "-";
      const value = Number(size);
      if (Number.isNaN(value)) return "-";
      if (value >= 1024 * 1024) {
        return `${(value / (1024 * 1024)).toFixed(1)} MB`;
      }
      if (value >= 1024) {
        return `${(value / 1024).toFixed(1)} KB`;
      }
      return `${value} B`;
    },
    syncSelectedDraftRows(tableOverride = null) {
      const table =
        tableOverride ||
        this.$refs.requestEditorDraftTableRef?.tabulatorInstance ||
        null;
      const rows = table?.getData?.() || this.requestEditorDraftRows || [];
      const ids = rows
        .filter((row) => row?.selected)
        .map((row) => row?.tempId)
        .filter((id) => id !== undefined && id !== null);
      this.selectedDraftRowIds = ids;
    },
    handleDraftBatchChanges(batchChanges = []) {
      if (!Array.isArray(batchChanges)) {
        return;
      }
      if (this.isProcessingRangeClear) {
        return;
      }
      if (this.suppressNextDirtyBatch) {
        this.suppressNextDirtyBatch = false;
        return;
      }
      const table = this.$refs.requestEditorDraftTableRef?.tabulatorInstance;
      const rowComponents = table?.getRows?.() || [];
      const rowByTempId = new Map();
      const rowByPk = new Map();
      rowComponents.forEach((rowComp) => {
        const rowData = rowComp?.getData?.() || {};
        if (rowData?.tempId) {
          rowByTempId.set(String(rowData.tempId), rowComp);
        }
        if (rowData?.pk !== undefined && rowData?.pk !== null) {
          rowByPk.set(String(rowData.pk), rowComp);
        }
      });
      let hasAnyUpdates = false;
      const indexTypesToFetch = new Set();
      batchChanges.forEach((change) => {
        const fields = Object.keys(change || {}).filter(
          (key) => !["pk", "record_type", "tempId"].includes(key)
        );
        if (!fields.length) return;
        const rowComp =
          (change?.tempId && rowByTempId.get(String(change.tempId))) ||
          (change?.pk !== undefined && change?.pk !== null
            ? rowByPk.get(String(change.pk))
            : null) ||
          null;
        if (!rowComp) return;
        const rowData = rowComp.getData?.() || {};
        const rowId = rowData?.tempId || null;
        if (
          this.isEditMode &&
          this.allowDirtyTracking &&
          rowId &&
          rowData?.pk
        ) {
          this.markDirtyFields(rowId, fields);
          hasAnyUpdates = true;
        }
        const resetResult = this.applyDependentResetsForChangedFields(
          rowComp,
          fields
        );
        if (resetResult?.updated) {
          hasAnyUpdates = true;
        }
        if (resetResult?.indexTypeId) {
          indexTypesToFetch.add(String(resetResult.indexTypeId));
        }
      });
      if (this.requestEditorMode === "library" && indexTypesToFetch.size) {
        indexTypesToFetch.forEach((typeId) => {
          this.fetchIndexOptionsForType(typeId);
        });
      }
      if (hasAnyUpdates) {
        this.$nextTick(() => this.revalidateDraftRows());
      }
    },
    applyDependentResetsForChangedFields(rowComp, changedFields = []) {
      if (!rowComp || !Array.isArray(changedFields) || !changedFields.length) {
        return { updated: false, indexTypeId: null };
      }
      const rowData = rowComp.getData?.() || {};
      const rowId = rowData?.tempId || null;
      const normalizedFields = new Set(changedFields);
      const updates = {};
      const dependentFields = [];
      let indexTypeId = null;
      const shouldResetDependent = (field) => !normalizedFields.has(field);
      const assignIfChanged = (field, value) => {
        if (rowData?.[field] !== value) {
          updates[field] = value;
          dependentFields.push(field);
        }
      };

      if (this.requestEditorMode === "library") {
        if (normalizedFields.has("index_type")) {
          if (shouldResetDependent("index_i7")) assignIfChanged("index_i7", "");
          if (shouldResetDependent("index_i5")) assignIfChanged("index_i5", "");
          if (rowData?.index_type) {
            indexTypeId = rowData.index_type;
          }
        }
        if (normalizedFields.has("library_protocol")) {
          if (shouldResetDependent("library_type")) {
            assignIfChanged("library_type", "");
          }
        }
      } else {
        if (normalizedFields.has("nucleic_acid_type")) {
          if (shouldResetDependent("library_protocol")) {
            assignIfChanged("library_protocol", "");
          }
          if (shouldResetDependent("library_type")) {
            assignIfChanged("library_type", "");
          }
          if (shouldResetDependent("gmo")) {
            assignIfChanged("gmo", null);
          }
        }
        if (normalizedFields.has("library_protocol")) {
          if (shouldResetDependent("library_type")) {
            assignIfChanged("library_type", "");
          }
        }
      }

      if (normalizedFields.has("measuring_unit")) {
        const working = { ...rowData, ...updates };
        this.applyMeasuringUnitSideEffects(working);
        if (working.measured_value !== rowData.measured_value) {
          updates.measured_value = working.measured_value;
          dependentFields.push("measured_value");
        }
      } else if (
        normalizedFields.has("measured_value") &&
        rowData.measuring_unit === "Unknown" &&
        rowData.measured_value !== -1
      ) {
        updates.measured_value = -1;
        dependentFields.push("measured_value");
      }

      if (!Object.keys(updates).length) {
        return { updated: false, indexTypeId };
      }
      rowComp.update({ ...rowData, ...updates });
      this.refreshRowFormatting(rowComp);
      if (this.isEditMode && this.allowDirtyTracking && rowId && rowData?.pk) {
        this.markDirtyFields(rowId, dependentFields);
      }
      return { updated: true, indexTypeId };
    },
    markDirtyFields(rowId, fields = []) {
      if (!rowId) return;
      if (!this.dirtyFieldsByRowId[rowId]) {
        this.dirtyFieldsByRowId[rowId] = new Set();
      }
      const target = this.dirtyFieldsByRowId[rowId];
      fields.forEach((field) => {
        if (field) target.add(field);
      });
    },
    getValidationFieldsForRow(rowData, dirtyFields, mode) {
      const fields = new Set(dirtyFields || []);
      const normalizedMode = mode === "sample" ? "sample" : "library";
      if (normalizedMode === "library") {
        if (fields.has("library_protocol")) fields.add("library_type");
        if (fields.has("library_type")) fields.add("library_protocol");
        if (fields.has("index_type")) {
          const reads = this.getIndexReadsCount(rowData);
          if (reads >= 1) fields.add("index_i7");
          if (reads >= 2) fields.add("index_i5");
        }
        if (fields.has("index_i7") || fields.has("index_i5")) {
          fields.add("index_type");
        }
        if (fields.has("measuring_unit") || fields.has("measured_value")) {
          fields.add("measured_value");
        }
      } else {
        if (fields.has("nucleic_acid_type")) fields.add("library_protocol");
        if (fields.has("library_protocol")) {
          fields.add("library_type");
          fields.add("nucleic_acid_type");
        }
        if (fields.has("library_type")) fields.add("library_protocol");
        if (fields.has("measuring_unit") || fields.has("measured_value")) {
          fields.add("measured_value");
        }
      }
      return fields;
    },
    computeValidationState(rows = [], mode, options = {}) {
      const validations = {};
      const validationFieldsByRowId = {};
      const nameCounts = {};
      const normalizedMode = mode === "sample" ? "sample" : "library";
      const useDirtyValidation = options.useDirtyValidation === true;

      rows.forEach((row) => {
        const name = (row?.name || "").trim();
        if (!name) return;
        nameCounts[name] = (nameCounts[name] || 0) + 1;
      });

      let validCount = 0;
      rows.forEach((row, index) => {
        if (!row.tempId) {
          row.tempId = `row-${index + 1}-${Date.now()}`;
        }
        const rowId = row.tempId || `row-${index}`;
        const isNewRow = useDirtyValidation && !row.pk;
        let validationFields = null;
        if (useDirtyValidation && !isNewRow) {
          const dirtyFields = this.dirtyFieldsByRowId[rowId];
          if (!dirtyFields || dirtyFields.size === 0) {
            validations[rowId] = {};
            validationFieldsByRowId[rowId] = new Set();
            validCount += 1;
            return;
          }
          validationFields = this.getValidationFieldsForRow(
            row,
            dirtyFields,
            normalizedMode
          );
          validationFieldsByRowId[rowId] = validationFields;
        }

        const allErrors =
          normalizedMode === "library"
            ? this.validateLibraryRow(row, index, nameCounts)
            : this.validateSampleRow(row, index, nameCounts);
        let filteredErrors = allErrors;
        if (useDirtyValidation && validationFields instanceof Set) {
          filteredErrors = {};
          validationFields.forEach((field) => {
            if (allErrors[field]) {
              filteredErrors[field] = allErrors[field];
            }
          });
        }
        validations[rowId] = filteredErrors;
        if (!Object.keys(filteredErrors).length) {
          validCount += 1;
        }
      });

      return { validations, validationFieldsByRowId, validCount };
    },
    revalidateDraftRows() {
      const table = this.$refs.requestEditorDraftTableRef?.tabulatorInstance;
      const tableRows = table?.getRows?.() || [];
      const rows = tableRows.length
        ? tableRows.map((row) => row.getData())
        : this.requestEditorDraftRows || [];
      const { validations, validationFieldsByRowId, validCount } =
        this.computeValidationState(rows, this.requestEditorMode, {
          useDirtyValidation: this.isEditMode
        });
      this.draftValidationState = validations;
      if (this.isEditMode) {
        this.validationFieldsByRowId = {
          ...this.validationFieldsByRowId,
          ...validationFieldsByRowId
        };
      }
      this.validDraftCount = validCount;
      this.$nextTick(() => this.applyValidationStyling());
      const result = {
        hasErrors: validCount !== rows.length,
        rowCount: rows.length
      };
      return result;
    },
    applyCellStyling(cell) {
      const el = cell?.getElement?.();
      if (!el) return;
      el.classList.remove(
        "cell-valid",
        "cell-invalid",
        "required-empty",
        "required-filled"
      );
      el.removeAttribute("title");
      el.removeAttribute("data-tooltip-original");
      const tooltipNodes = el.querySelectorAll(
        "[data-tooltip-original],[title]"
      );
      tooltipNodes.forEach((node) => {
        if (node !== el) {
          node.removeAttribute("title");
          node.removeAttribute("data-tooltip-original");
        }
      });
      const rowData = cell.getRow?.()?.getData?.();
      const field = cell.getField?.();
      if (!rowData || !field || field === "selected") return;
      const rowId = rowData.tempId;
      const isExistingRow = this.isEditMode && rowData?.pk;
      const dirtyFields = rowId ? this.dirtyFieldsByRowId[rowId] : null;
      const hasDirtyFields =
        dirtyFields instanceof Set
          ? dirtyFields.size > 0
          : Boolean(dirtyFields);
      const hasScope =
        this.isEditMode &&
        rowId &&
        Object.prototype.hasOwnProperty.call(
          this.validationFieldsByRowId,
          rowId
        );
      const scope =
        hasScope && rowId ? this.validationFieldsByRowId[rowId] : null;
      const shouldValidateField =
        (!hasScope || !(scope instanceof Set) || scope.has(field)) &&
        !(isExistingRow && !hasDirtyFields);
      const errors = this.draftValidationState[rowData.tempId] || {};
      const cellValue = cell.getValue?.();
      const valuePresent = this.fieldHasValue(cellValue);
      const required = this.isFieldRequired(field, rowData);
      const disabledTooltip = el.getAttribute("data-disabled-tooltip");
      const isDisabled = el.classList.contains("disable-editing");
      const displayText = (el.textContent || "").trim();
      const setTooltipText = (text) => {
        const tooltipText = String(text || "").trim();
        el.removeAttribute("title");
        el.removeAttribute("data-tooltip-original");
        if (tooltipText) {
          el.setAttribute("data-tooltip-original", tooltipText);
        }
      };
      if (!shouldValidateField) {
        if (valuePresent) {
          el.classList.add("cell-valid");
        }
        setTooltipText(displayText || disabledTooltip);
        return;
      }
      if (required) {
        el.classList.add(valuePresent ? "required-filled" : "required-empty");
      }
      if (errors[field]) {
        el.classList.add("cell-invalid");
        setTooltipText(errors[field]);
      } else if (valuePresent) {
        el.classList.add("cell-valid");
        setTooltipText(displayText || disabledTooltip);
      } else if (isDisabled && disabledTooltip) {
        setTooltipText(disabledTooltip);
      } else {
        setTooltipText(displayText);
      }
    },
    applyRowStyling(row) {
      const rowData = row?.getData?.();
      const rowId = rowData?.tempId;
      const isExistingRow = this.isEditMode && rowData?.pk;
      const dirtyFields = rowId ? this.dirtyFieldsByRowId[rowId] : null;
      const hasDirtyFields =
        dirtyFields instanceof Set
          ? dirtyFields.size > 0
          : Boolean(dirtyFields);
      const rowErrors = (rowId && this.draftValidationState[rowId]) || {};
      const hasErrors =
        !(isExistingRow && !hasDirtyFields) &&
        Object.keys(rowErrors).length > 0;
      const rowEl = row?.getElement?.();
      if (rowEl) {
        rowEl.classList.toggle("row-has-errors", hasErrors);
        rowEl.classList.toggle("row-all-valid", !hasErrors);
      }
      const cells = row?.getCells?.() || [];
      cells.forEach((cell) => this.applyCellStyling(cell));
    },
    applyValidationStyling() {
      const table = this.$refs.requestEditorDraftTableRef?.tabulatorInstance;
      if (!table) return;
      const rows = table.getRows?.() || [];
      rows.forEach((row) => this.applyRowStyling(row));
    },
    getDraftTableRows() {
      const table = this.$refs.requestEditorDraftTableRef?.tabulatorInstance;
      if (table?.getData) {
        return table.getData();
      }
      return this.requestEditorDraftRows;
    },
    handleCellEditing(cell) {
      if (!this.canEditRequest) return false;
      if (!cell) return true;
      const field = cell.getField?.();
      const rowData = cell.getRow?.()?.getData?.() || {};
      if (!field) return true;
      if (field === "barcode") {
        showNotification("Barcode is read-only.", "warning");
        return false;
      }

      if (field === "measured_value") {
        if (!rowData.measuring_unit) {
          showNotification("Select a measuring unit first.", "warning");
          return false;
        }
        if (rowData.measuring_unit === "Unknown") {
          showNotification(
            "Measured value auto-filled for Unknown units.",
            "warning"
          );
          return false;
        }
      }

      if (this.requestEditorMode === "library") {
        if (field === "index_i7") {
          if (this.getIndexReadsCount(rowData) < 1) {
            return false;
          }
        }
        if (field === "index_i5") {
          if (this.getIndexReadsCount(rowData) < 2) {
            return false;
          }
        }
        if (field === "library_type" && !rowData.library_protocol) {
          showNotification("Select a protocol first.", "warning");
          return false;
        }
        return true;
      }

      if (field === "library_protocol" && !rowData.nucleic_acid_type) {
        showNotification("Select an input type first.", "warning");
        return false;
      }
      if (field === "library_type" && !rowData.library_protocol) {
        showNotification("Select a protocol first.", "warning");
        return false;
      }
      if (
        field === "gmo" &&
        !this.isGmoAllowedInputType(rowData.nucleic_acid_type)
      ) {
        showNotification("GMO only editable for Cell Suspension.", "warning");
        return false;
      }
      return true;
    },
    handleCellEdited(cell) {
      if (!cell) {
        this.revalidateDraftRows();
        return;
      }
      const field = cell.getField?.();
      const row = cell.getRow?.();
      if (!row) {
        this.revalidateDraftRows();
        return;
      }
      if (this.isEditMode && this.allowDirtyTracking && field) {
        const rowData = row.getData?.() || {};
        if (rowData?.tempId && rowData?.pk) {
          this.markDirtyFields(rowData.tempId, [field]);
        }
      }
      if (this.requestEditorMode === "library" && field) {
        this.handleLibraryCellEdited(field, row);
      } else if (this.requestEditorMode === "sample" && field) {
        this.handleSampleCellEdited(field, row);
      }
      this.revalidateDraftRows();
      this.applyRowStyling(row);
    },
    handleLibraryCellEdited(field, row) {
      const data = { ...row.getData() };
      if (field === "index_type") {
        const typeId = data.index_type;
        data.index_i7 = "";
        data.index_i5 = "";
        row.update(data);
        this.refreshRowFormatting(row);
        if (typeId) {
          this.fetchIndexOptionsForType(typeId);
        }
        return;
      }
      if (field === "library_protocol") {
        data.library_type = "";
        row.update(data);
        this.refreshRowFormatting(row);
        return;
      }
      if (field === "measuring_unit") {
        this.applyMeasuringUnitSideEffects(data);
        row.update(data);
        this.refreshRowFormatting(row);
        return;
      }
      if (field === "measured_value") {
        if (data.measuring_unit === "Unknown") {
          data.measured_value = -1;
          row.update(data);
        }
        return;
      }
      if (field === "index_i7") {
        if (!this.isValidIndexSequence(data.index_i7)) {
          data.index_i7 = "";
          row.update(data);
          this.refreshRowFormatting(row);
          showNotification(
            "Only uppercase A/T/C/G indices with length 6, 8, 10, 12, or 24 are allowed.",
            "warning"
          );
          return;
        }
        if (!this.isIndexValueAllowedForType("index_i7", data, data.index_i7)) {
          data.index_i7 = "";
          row.update(data);
          this.refreshRowFormatting(row);
          showNotification(
            'Index I7 does not belong to selected Index Type. Select "Other" Index Type for custom indices.',
            "warning"
          );
          return;
        }
        const reads = this.getIndexReadsCount(data);
        if (reads >= 2) {
          const matched = this.tryAutoSelectI5(row, data);
          if (!matched && data.index_type) {
            this.fetchIndexOptionsForType(data.index_type, {
              row,
              selectedI7: data.index_i7
            });
          }
        }
      }
      if (field === "index_i5") {
        if (!this.isValidIndexSequence(data.index_i5)) {
          data.index_i5 = "";
          row.update(data);
          this.refreshRowFormatting(row);
          showNotification(
            "Only uppercase A/T/C/G indices with length 6, 8, 10, 12, or 24 are allowed.",
            "warning"
          );
          return;
        }
        if (!this.isIndexValueAllowedForType("index_i5", data, data.index_i5)) {
          data.index_i5 = "";
          row.update(data);
          this.refreshRowFormatting(row);
          showNotification(
            'Index I5 does not belong to selected Index Type. Select "Other" Index Type for custom indices.',
            "warning"
          );
          return;
        }
        const reads = this.getIndexReadsCount(data);
        if (reads >= 2) {
          const matched = this.tryAutoSelectI7(row, data);
          if (!matched && data.index_type) {
            this.fetchIndexOptionsForType(data.index_type, {
              row,
              selectedI5: data.index_i5
            });
          }
        }
      }
    },
    handleSampleCellEdited(field, row) {
      const data = { ...row.getData() };
      if (field === "nucleic_acid_type") {
        data.library_protocol = "";
        data.library_type = "";
        data.gmo = null;
        row.update(data);
        this.refreshRowFormatting(row);
        return;
      }
      if (field === "library_protocol") {
        data.library_type = "";
        row.update(data);
        this.refreshRowFormatting(row);
        return;
      }
      if (field === "measuring_unit") {
        this.applyMeasuringUnitSideEffects(data);
        row.update(data);
        this.refreshRowFormatting(row);
        return;
      }
      if (field === "measured_value") {
        if (data.measuring_unit === "Unknown") {
          data.measured_value = -1;
          row.update(data);
        }
      }
    },
    getIndexReadsCount(rowData = {}) {
      const typeId = rowData?.index_type;
      if (!typeId) return 0;
      const typeKey = String(typeId);
      const match = this.indexTypesList.find((item) => {
        const key =
          item?.id ?? item?.value ?? item?.pk ?? item?.name ?? item?.label;
        return String(key) === typeKey;
      });
      const maxReads = Number(match?.index_reads);
      if (!Number.isFinite(maxReads) || maxReads < 0) return 0;
      return maxReads;
    },
    getLibraryIndexI7Options(rowData = {}) {
      const typeKey = rowData?.index_type ? String(rowData.index_type) : "";
      if (!typeKey) return [];
      return this.indexI7OptionsByType[typeKey] || [];
    },
    getLibraryIndexI5Options(rowData = {}) {
      const typeKey = rowData?.index_type ? String(rowData.index_type) : "";
      if (!typeKey) return [];
      return this.indexI5OptionsByType[typeKey] || [];
    },
    isOtherIndexType(rowData = {}) {
      const typeId = rowData?.index_type;
      if (typeId === null || typeId === undefined || typeId === "")
        return false;
      const typeKey = String(typeId);
      const match = this.indexTypesList.find((item) => {
        const key =
          item?.id ?? item?.value ?? item?.pk ?? item?.name ?? item?.label;
        return String(key) === typeKey;
      });
      const typeName = String(match?.name ?? match?.label ?? "")
        .trim()
        .toLowerCase();
      return typeName === "other";
    },
    isIndexValueAllowedForType(field, rowData = {}, value) {
      if (value === null || value === undefined || value === "") return true;
      if (this.isOtherIndexType(rowData)) return true;
      const options =
        field === "index_i5"
          ? this.getLibraryIndexI5Options(rowData)
          : this.getLibraryIndexI7Options(rowData);
      const target = String(value);
      return options.some((option) => String(option?.value) === target);
    },
    isListValueAllowedForRow(targetCell, rowData = {}, value) {
      if (!targetCell) return false;
      if (value === null || value === undefined || value === "") return true;
      const columnDef = targetCell.getColumn?.().getDefinition?.() || {};
      if (columnDef.editor !== "list") return true;
      const editorParams =
        typeof columnDef.editorParams === "function"
          ? columnDef.editorParams({
              getRow: () => ({ getData: () => rowData })
            })
          : columnDef.editorParams || {};
      let options = [];
      if (Array.isArray(editorParams?.values)) {
        options = editorParams.values.map((opt) =>
          opt && typeof opt === "object" ? opt.value : opt
        );
      } else if (
        editorParams?.values &&
        typeof editorParams.values === "object"
      ) {
        options = Object.keys(editorParams.values);
      }
      if (!options.length) return false;
      const target = String(value);
      return options.some((option) => String(option) === target);
    },
    isValueAllowedForApplyAll(targetCell, field, rowData = {}, value) {
      if (value === null || value === undefined || value === "") return true;
      if (field === "index_i7" || field === "index_i5") {
        if (!this.isValidIndexSequence(value)) return false;
        if (this.isOtherIndexType(rowData)) return true;
        return this.isIndexValueAllowedForType(field, rowData, value);
      }
      return this.isListValueAllowedForRow(targetCell, rowData, value);
    },
    isValidIndexSequence(value) {
      if (value === null || value === undefined || value === "") return true;
      const text = String(value);
      const validPattern = /^[ATCG]{6,}$/;
      const validLengths = new Set([6, 8, 10, 12, 24]);
      return validPattern.test(text) && validLengths.has(text.length);
    },
    async fetchIndexOptionsForType(typeId, autoSelect = null) {
      if (!typeId) return;
      const key = String(typeId);
      if (
        this.indexOptionsLoading[key] ||
        (this.indexI7OptionsByType[key] &&
          this.indexI5OptionsByType[key] &&
          this.indexPairsByType[key])
      ) {
        return;
      }
      this.indexOptionsLoading = { ...this.indexOptionsLoading, [key]: true };
      try {
        const [i7Res, i5Res, pairsRes] = await Promise.all([
          axiosRef.get(`${urlStringStart}/api/indices/i7/`, {
            params: { index_type_id: key }
          }),
          axiosRef.get(`${urlStringStart}/api/indices/i5/`, {
            params: { index_type_id: key }
          }),
          axiosRef.get(`${urlStringStart}/api/indices/pairs/`, {
            params: { index_type_id: key }
          })
        ]);
        const formatOptions = (response) => {
          const list = response?.data?.data || response?.data || [];
          return list.map((item) => ({
            value: item.index ?? item.value ?? item.id ?? item.name ?? "",
            label: item.name ?? item.index ?? item.index_id ?? "",
            index_id: item.index_id ?? "",
            index: item.index ?? ""
          }));
        };
        const i7Options = formatOptions(i7Res).sort((a, b) =>
          String(a.label || "").localeCompare(
            String(b.label || ""),
            undefined,
            {
              sensitivity: "base"
            }
          )
        );
        const i5Options = formatOptions(i5Res).sort((a, b) =>
          String(a.label || "").localeCompare(
            String(b.label || ""),
            undefined,
            {
              sensitivity: "base"
            }
          )
        );
        const pairsList = pairsRes?.data?.data || pairsRes?.data || [];
        const pairsMap = {};
        pairsList.forEach((pair) => {
          const i7Id = pair?.index1_id || "";
          const i5Id = pair?.index2_id || "";
          if (i7Id && i5Id) {
            pairsMap[i7Id] = i5Id;
          }
        });
        this.indexI7OptionsByType = {
          ...this.indexI7OptionsByType,
          [key]: i7Options
        };
        this.indexI5OptionsByType = {
          ...this.indexI5OptionsByType,
          [key]: i5Options
        };
        this.indexPairsByType = {
          ...this.indexPairsByType,
          [key]: pairsMap
        };
        if (autoSelect?.row && autoSelect?.selectedI7) {
          const rowData = {
            ...autoSelect.row.getData(),
            index_i7: autoSelect.selectedI7
          };
          this.tryAutoSelectI5(autoSelect.row, rowData);
        }
        if (autoSelect?.row && autoSelect?.selectedI5) {
          const rowData = {
            ...autoSelect.row.getData(),
            index_i5: autoSelect.selectedI5
          };
          this.tryAutoSelectI7(autoSelect.row, rowData);
        }
        this.$nextTick(() => {
          this.refreshRowsForIndexType(key);
          this.revalidateDraftRows();
          this.applyValidationStyling();
        });
      } catch (error) {
        handleError(error);
      } finally {
        const loadingState = { ...this.indexOptionsLoading };
        delete loadingState[key];
        this.indexOptionsLoading = loadingState;
      }
    },
    tryAutoSelectI5(row, rowData) {
      if (!row || !rowData) return false;
      if (!rowData.index_type || !rowData.index_i7) {
        return false;
      }
      const reads = this.getIndexReadsCount(rowData);
      if (reads < 2) return false;
      const typeKey = String(rowData.index_type);
      const i7Options = this.indexI7OptionsByType[typeKey] || [];
      const i5Options = this.indexI5OptionsByType[typeKey] || [];
      const pairsMap = this.indexPairsByType[typeKey] || null;
      if (!i7Options.length || !i5Options.length || !pairsMap) return false;
      const selectedI7 = this.findIndexOptionByValue(
        i7Options,
        rowData.index_i7
      );
      if (!selectedI7 || !selectedI7.index_id) return false;
      const i5IndexId = pairsMap[selectedI7.index_id];
      if (!i5IndexId) return false;
      const match = i5Options.find(
        (option) => option.index_id && option.index_id === i5IndexId
      );
      if (!match) return false;
      if (rowData.index_i5 === match.value) return true;
      const updated = { ...rowData, index_i5: match.value };
      row.update(updated);
      this.refreshRowFormatting(row);
      return true;
    },
    tryAutoSelectI7(row, rowData) {
      if (!row || !rowData) return false;
      if (!rowData.index_type || !rowData.index_i5) {
        return false;
      }
      const reads = this.getIndexReadsCount(rowData);
      if (reads < 2) return false;
      const typeKey = String(rowData.index_type);
      const i7Options = this.indexI7OptionsByType[typeKey] || [];
      const i5Options = this.indexI5OptionsByType[typeKey] || [];
      const pairsMap = this.indexPairsByType[typeKey] || null;
      if (!i7Options.length || !i5Options.length || !pairsMap) return false;
      const selectedI5 = this.findIndexOptionByValue(
        i5Options,
        rowData.index_i5
      );
      if (!selectedI5 || !selectedI5.index_id) return false;
      const i7IndexId = Object.keys(pairsMap).find(
        (key) => pairsMap[key] === selectedI5.index_id
      );
      if (!i7IndexId) return false;
      const match = i7Options.find(
        (option) => option.index_id && option.index_id === i7IndexId
      );
      if (!match) return false;
      if (rowData.index_i7 === match.value) return true;
      const updated = { ...rowData, index_i7: match.value };
      row.update(updated);
      this.refreshRowFormatting(row);
      return true;
    },
    redrawDraftTable() {
      const table = this.$refs.requestEditorDraftTableRef?.tabulatorInstance;
      table?.redraw?.();
    },
    normalizeNumber(value) {
      if (value === "" || value === undefined || value === null) return null;
      const num = Number(value);
      return Number.isNaN(num) ? null : num;
    },
    normalizeId(value) {
      if (value === "" || value === undefined || value === null) {
        return null;
      }
      const numeric = Number(value);
      return Number.isNaN(numeric) ? value : numeric;
    },
    getNucleicAcidMeta(value) {
      if (value === null || value === undefined || value === "") return null;
      const target = String(value);
      return (
        this.nucleicAcidTypesList.find((item) => {
          const key =
            item?.id ?? item?.value ?? item?.pk ?? item?.name ?? item?.label;
          return String(key) === target;
        }) || null
      );
    },
    isGmoAllowedInputType(value) {
      const meta = this.getNucleicAcidMeta(value);
      if (!meta || typeof meta.name !== "string") {
        return true;
      }
      const name = meta.name.trim().toLowerCase();
      if (!name) return true;
      return !(name.includes("dna") || name.includes("rna"));
    },
    applyMeasuringUnitSideEffects(rowData) {
      if (!rowData) return;
      const unit = rowData.measuring_unit;
      if (!unit) {
        rowData.measured_value = null;
        return;
      }
      if (unit === "Unknown") {
        rowData.measured_value = -1;
        return;
      }
      if (rowData.measured_value === null || rowData.measured_value === -1) {
        rowData.measured_value = null;
      }
    },
    coerceMeasuredValue(row) {
      if (row.measuring_unit === "Unknown") {
        return -1;
      }
      return this.normalizeNumber(row.measured_value);
    },
    validateLibraryRow(row, index, nameCounts = {}) {
      const prefix = `Row ${index + 1}`;
      const errors = {};
      const isEditable = (field) => this.isLibraryFieldEditable(field, row);
      const name = (row.name || "").trim();
      if (!name) {
        errors.name = `${prefix}: Name is a required field.`;
      } else if (!/^[A-Za-z0-9_-]+$/.test(name)) {
        errors.name = `${prefix}: Name must contain only letters, numbers, _ or -.`;
      } else if ((nameCounts[name] || 0) > 1) {
        errors.name = `${prefix}: Name must be unique.`;
      }
      if (isEditable("measuring_unit") && !row.measuring_unit) {
        errors.measuring_unit = `${prefix}: Measuring Unit is a required field.`;
      }
      if (isEditable("library_protocol") && !row.library_protocol) {
        errors.library_protocol = `${prefix}: Protocol is a required field.`;
      }
      if (isEditable("library_type") && !row.library_type) {
        errors.library_type = `${prefix}: Analysis Type is a required field.`;
      }
      if (isEditable("read_length") && !row.read_length) {
        errors.read_length = `${prefix}: Read Length is a required field.`;
      }
      const depth = this.normalizeNumber(row.sequencing_depth);
      if (isEditable("sequencing_depth") && (depth === null || depth <= 0)) {
        errors.sequencing_depth = `${prefix}: Sequencing Depth must be greater than 0.`;
      }
      if (isEditable("organism") && !row.organism) {
        errors.organism = `${prefix}: Organism is a required field.`;
      }
      const volume = this.normalizeNumber(row.volume);
      if (isEditable("volume") && (volume === null || volume < 10)) {
        errors.volume = `${prefix}: Volume must be at least 10.`;
      }
      const fragmentSize = this.normalizeNumber(row.mean_fragment_size);
      if (
        isEditable("mean_fragment_size") &&
        (fragmentSize === null || fragmentSize <= 0)
      ) {
        errors.mean_fragment_size = `${prefix}: Size (bp) must be greater than 0.`;
      }
      if (isEditable("index_type") && !row.index_type) {
        errors.index_type = `${prefix}: Index Type is a required field.`;
      }
      const reads = this.getIndexReadsCount(row);
      if (isEditable("index_i7") && reads >= 1 && !row.index_i7) {
        errors.index_i7 = `${prefix}: Index I7 is required for this index type.`;
      }
      if (isEditable("index_i5") && reads >= 2 && !row.index_i5) {
        errors.index_i5 = `${prefix}: Index I5 is required for this index type.`;
      }
      if (
        isEditable("measured_value") &&
        row.measuring_unit &&
        row.measuring_unit !== "Unknown" &&
        this.normalizeNumber(row.measured_value) === null
      ) {
        errors.measured_value = `${prefix}: Value is required when a measuring unit is selected.`;
      }
      return errors;
    },
    validateSampleRow(row, index, nameCounts = {}) {
      const prefix = `Row ${index + 1}`;
      const errors = {};
      const isEditable = (field) => this.isSampleFieldEditable(field, row);
      const name = (row.name || "").trim();
      if (!name) {
        errors.name = `${prefix}: Name is a required field.`;
      } else if (!/^[A-Za-z0-9_-]+$/.test(name)) {
        errors.name = `${prefix}: Name must contain only letters, numbers, _ or -.`;
      } else if ((nameCounts[name] || 0) > 1) {
        errors.name = `${prefix}: Name must be unique.`;
      }
      if (isEditable("nucleic_acid_type") && !row.nucleic_acid_type) {
        errors.nucleic_acid_type = `${prefix}: Input Type is a required field.`;
      }
      if (isEditable("measuring_unit") && !row.measuring_unit) {
        errors.measuring_unit = `${prefix}: Measuring Unit is a required field.`;
      }
      if (isEditable("library_protocol") && !row.library_protocol) {
        errors.library_protocol = `${prefix}: Protocol is a required field.`;
      }
      if (isEditable("library_type") && !row.library_type) {
        errors.library_type = `${prefix}: Analysis Type is a required field.`;
      }
      if (isEditable("read_length") && !row.read_length) {
        errors.read_length = `${prefix}: Read Length is a required field.`;
      }
      const depth = this.normalizeNumber(row.sequencing_depth);
      if (isEditable("sequencing_depth") && (depth === null || depth <= 0)) {
        errors.sequencing_depth = `${prefix}: Sequencing Depth must be greater than 0.`;
      }
      if (isEditable("organism") && !row.organism) {
        errors.organism = `${prefix}: Organism is a required field.`;
      }
      const volume = this.normalizeNumber(row.volume);
      if (isEditable("volume") && (volume === null || volume < 10)) {
        errors.volume = `${prefix}: Volume must be at least 10.`;
      }
      if (isEditable("biosafety_level") && !row.biosafety_level) {
        errors.biosafety_level = `${prefix}: Biosafety Level is a required field.`;
      }
      if (
        isEditable("gmo") &&
        row.gmo !== true &&
        row.gmo !== false &&
        row.gmo !== "true" &&
        row.gmo !== "false"
      ) {
        errors.gmo = `${prefix}: Propagable & GMO is a required field.`;
      }
      if (
        isEditable("measured_value") &&
        row.measuring_unit &&
        row.measuring_unit !== "Unknown" &&
        this.normalizeNumber(row.measured_value) === null
      ) {
        errors.measured_value = `${prefix}: Measured Value is required when a unit is selected.`;
      }
      return errors;
    },
    buildLibraryPayload(row) {
      return {
        name: (row.name || "").trim(),
        library_protocol: this.normalizeId(row.library_protocol),
        library_type: this.normalizeId(row.library_type),
        measuring_unit: row.measuring_unit || null,
        measured_value: this.coerceMeasuredValue(row),
        mean_fragment_size: this.normalizeNumber(row.mean_fragment_size),
        volume: this.normalizeNumber(row.volume),
        read_length: this.normalizeId(row.read_length),
        sequencing_depth: this.normalizeNumber(row.sequencing_depth),
        index_type: this.normalizeId(row.index_type),
        index_reads: this.getIndexReadsCount(row),
        index_i7: row.index_i7 || null,
        index_i5: row.index_i5 || null,
        organism: this.normalizeId(row.organism),
        comments: row.comments || ""
      };
    },
    buildSamplePayload(row) {
      const gmoValue = (() => {
        const value = row.gmo;
        if (value === true || value === "true") return true;
        if (value === false || value === "false") return false;
        if (typeof value === "string") {
          const normalized = value.trim().toLowerCase();
          if (normalized === "yes") return true;
          if (normalized === "no") return false;
        }
        return null;
      })();
      return {
        name: (row.name || "").trim(),
        nucleic_acid_type: this.normalizeId(row.nucleic_acid_type),
        library_protocol: this.normalizeId(row.library_protocol),
        library_type: this.normalizeId(row.library_type),
        measuring_unit: row.measuring_unit || null,
        measured_value: this.coerceMeasuredValue(row),
        volume: this.normalizeNumber(row.volume),
        read_length: this.normalizeId(row.read_length),
        sequencing_depth: this.normalizeNumber(row.sequencing_depth),
        organism: this.normalizeId(row.organism),
        comments: row.comments || "",
        biosafety_level: row.biosafety_level || null,
        gmo: gmoValue
      };
    },
    async handleRequestFileUpload(event) {
      const files = Array.from(event.target.files || []);
      try {
        await this.uploadRequestFiles(files);
      } catch (error) {
        handleError(error);
      } finally {
        if (event?.target) {
          event.target.value = "";
        }
      }
    },
    async fetchUploadedFilesDetails() {
      if (!this.uploadedRequestFileIds.length) {
        this.uploadedRequestFiles = [];
        return;
      }
      try {
        const response = await axiosRef.get(
          `${urlStringStart}/api/requests/get_files_after_upload/`,
          {
            params: {
              file_ids: JSON.stringify(this.uploadedRequestFileIds)
            }
          }
        );
        if (response?.data?.success) {
          const currentFiles = new Map(
            this.uploadedRequestFiles.map((file) => [String(file.id), file])
          );
          this.uploadedRequestFiles = (response.data.data || []).map((file) => {
            const current = currentFiles.get(String(file.id));
            return current || normaliseRequestFile(file);
          });
        }
      } catch (error) {
        handleError(error);
      }
    },
    removeUploadedFile(fileId) {
      this.uploadedRequestFileIds = this.uploadedRequestFileIds.filter(
        (id) => id !== fileId
      );
      this.uploadedRequestFiles = this.uploadedRequestFiles.filter(
        (f) => f.id !== fileId
      );
    },
    isValidRequestFileType,
    handleRequestFileTypeChoice(file) {
      file.file_type = resolveRequestFileType(file);
    },
    handleCustomRequestFileType(file, event) {
      const value = String(event?.target?.value || "").replace(
        /[^A-Za-z0-9_]/g,
        ""
      );
      file.customFileType = value;
      file.file_type = value || REQUEST_FILE_TYPE_OTHER;
      if (event?.target && event.target.value !== value) {
        event.target.value = value;
      }
    },
    requestFileTypesAreValid() {
      const invalidFile = this.uploadedRequestFiles.find(
        (file) =>
          file.fileTypeChoice === REQUEST_FILE_TYPE_OTHER &&
          file.customFileType &&
          !isValidRequestFileType(file.customFileType)
      );
      if (!invalidFile) return true;
      showNotification(
        `File type for "${invalidFile.name}" must use words separated by single underscores.`,
        "warning"
      );
      return false;
    },
    requestFileTypesPayload() {
      return requestFileTypesPayload(this.uploadedRequestFiles);
    },
    requestRemoveUploadedFile(file) {
      if (!file?.id) return;
      if (!this.canEditRequest) return;
      this.pendingFileDelete = file;
      this.showFileDeleteConfirm = true;
    },
    cancelFileDelete() {
      this.showFileDeleteConfirm = false;
      this.pendingFileDelete = null;
    },
    confirmFileDelete() {
      if (this.pendingFileDelete?.id) {
        this.removeUploadedFile(this.pendingFileDelete.id);
      }
      this.showFileDeleteConfirm = false;
      this.pendingFileDelete = null;
    },
    handleFileDeleteConfirmKeydown(event) {
      if (event.key === "Escape") {
        event.preventDefault();
        this.cancelFileDelete();
      } else if (event.key === "Enter") {
        event.preventDefault();
        this.confirmFileDelete();
      }
    },
    downloadUploadedFile(file) {
      if (!file?.path) {
        showNotification("Download link unavailable for this file.", "warning");
        return;
      }
      const path = String(file.path || "");
      const url = path.startsWith("http") ? path : `${urlStringStart}${path}`;
      axiosRef
        .get(url, { responseType: "blob" })
        .then((response) => {
          const blob = response?.data;
          if (!blob || blob.size === 0) {
            showNotification("Downloaded file is empty.", "warning");
            return;
          }
          const objectUrl = URL.createObjectURL(blob);
          const link = document.createElement("a");
          link.href = objectUrl;
          link.download = file.name || "request-file";
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          URL.revokeObjectURL(objectUrl);
        })
        .catch((error) => {
          handleError(error);
        });
    },
    handleDragOver() {
      if (!this.canEditRequest) {
        this.isDragOver = false;
        return;
      }
      this.isDragOver = true;
    },
    handleDragEnter() {
      if (!this.canEditRequest) {
        this.isDragOver = false;
        return;
      }
      this.isDragOver = true;
    },
    handleDragLeave(event) {
      if (!this.canEditRequest) {
        this.isDragOver = false;
        return;
      }
      if (!event.currentTarget.contains(event.relatedTarget)) {
        this.isDragOver = false;
      }
    },
    handleDrop(event) {
      this.isDragOver = false;
      if (!this.canEditRequest) {
        showNotification("You lack permission to upload files.", "warning");
        return;
      }
      const files = Array.from(event.dataTransfer?.files || []);
      if (!files.length) {
        showNotification("No files selected.", "warning");
        return;
      }
      this.uploadRequestFiles(files);
    },
    async uploadRequestFiles(files = []) {
      if (!files.length) {
        showNotification("No files selected.", "warning");
        return;
      }
      const formData = new FormData();
      files.forEach((file) => formData.append("files", file));
      try {
        const response = await axiosRef.post(
          `${urlStringStart}/api/requests/upload_files/`,
          formData,
          {
            headers: { "Content-Type": "multipart/form-data" }
          }
        );
        if (response?.data?.success) {
          const ids = response.data.fileIds || [];
          this.uploadedRequestFileIds = [
            ...this.uploadedRequestFileIds,
            ...ids
          ];
          await this.fetchUploadedFilesDetails();
          showNotification("Files uploaded successfully.", "success");
        } else {
          showNotification("File upload failed.", "error");
        }
      } catch (error) {
        handleError(error);
      }
    },
    async fetchCostUnits() {
      const targetUserId = this.isEditMode
        ? this.originalRequestOwnerId || this.requestOwnerId
        : this.userId;
      if (!targetUserId && !this.isEditMode) return;
      if (!this.isEditMode) {
        if (
          this.costUnitsLoadedForUser === targetUserId &&
          this.costUnits.length
        ) {
          return;
        }
      }
      try {
        const params = {};
        if (targetUserId) {
          params.user_id = targetUserId;
        }
        const response = await axiosRef.get(
          `${urlStringStart}/api/cost_units/`,
          {
            params
          }
        );
        let loadedCostUnits = (response.data || []).sort((a, b) =>
          String(a.name || "").localeCompare(String(b.name || ""), undefined, {
            sensitivity: "base"
          })
        );
        if (
          this.isEditMode &&
          this.newRequest.cost_unit &&
          !loadedCostUnits.some(
            (cu) => String(cu.id) === String(this.newRequest.cost_unit)
          )
        ) {
          try {
            const detailRes = await axiosRef.get(
              `${urlStringStart}/api/cost_units/${this.newRequest.cost_unit}/`
            );
            const detail = detailRes?.data;
            if (detail && detail.id) {
              loadedCostUnits = [...loadedCostUnits, detail].sort((a, b) =>
                String(a.name || "").localeCompare(
                  String(b.name || ""),
                  undefined,
                  {
                    sensitivity: "base"
                  }
                )
              );
            }
          } catch {
            // Ignore missing detail; keep the fetched list as-is.
          }
        }
        this.costUnits = loadedCostUnits;
        if (!this.isEditMode) {
          this.costUnitsLoadedForUser = targetUserId;
        }
      } catch (error) {
        handleError(error);
      }
    },
    async fetchRequestUsers(query = "") {
      if (!this.isStaffUser) return;
      try {
        const response = await axiosRef.get(
          `${urlStringStart}/api/requests/search_users/`,
          {
            params: { query }
          }
        );
        this.requestOwnerSuggestions = Array.isArray(response.data)
          ? response.data
          : [];
        this.setAutocompleteHighlight(
          "highlightedRequestOwnerSuggestionIndex",
          this.requestOwnerSuggestions
        );
      } catch (error) {
        handleError(error);
      }
    },
    async fetchRelatedProjects({ query = "", ids = [] } = {}) {
      if (!this.canEditRelatedProjects) return;
      try {
        const normalizedIds = (Array.isArray(ids) ? ids : [])
          .map((id) => Number(id))
          .filter((id) => Number.isInteger(id) && id > 0);
        const params = {
          exclude_request_id: this.requestId || ""
        };
        if (normalizedIds.length) {
          params.ids = normalizedIds.join(",");
        } else if ((query || "").trim()) {
          params.query = String(query).trim();
        } else {
          this.relatedProjectSuggestions = [];
          this.resetRelatedProjectHighlight();
          return;
        }

        const response = await axiosRef.get(
          `${urlStringStart}/api/requests/search_related_requests/`,
          { params }
        );
        const items = Array.isArray(response.data) ? response.data : [];
        if (normalizedIds.length) {
          const byId = new Map(
            items
              .map((item) => ({
                id: Number(item?.id),
                name: item?.name || `Request ${item?.id}`
              }))
              .filter((item) => Number.isInteger(item.id) && item.id > 0)
              .map((item) => [item.id, item])
          );
          this.relatedProjectsSelection = this.relatedProjectsSelection.map(
            (project) => byId.get(project.id) || project
          );
          return;
        }
        this.relatedProjectSuggestions = items
          .map((item) => ({
            id: Number(item?.id),
            name: item?.name || `Request ${item?.id}`
          }))
          .filter(
            (item) =>
              Number.isInteger(item.id) &&
              item.id > 0 &&
              !this.relatedProjectsSelection.some(
                (selected) => selected.id === item.id
              )
          );
        this.setAutocompleteHighlight(
          "highlightedRelatedProjectSuggestionIndex",
          this.relatedProjectSuggestions
        );
      } catch (error) {
        handleError(error);
      }
    },
    handleRequestOwnerInput(event) {
      if (!this.isStaffUser || !this.isEditMode || !this.canEditRequest) return;
      const query = String(event.target.value || "");
      this.requestOwnerQuery = query;
      this.requestOwnerId = null;
      this.showRequestOwnerSuggestions = !!query;
      this.resetRequestOwnerHighlight();
      this.clearAutocompleteTimer("requestOwnerSearchTimer");
      if (!query.trim()) {
        this.requestOwnerSuggestions = [];
        return;
      }
      this.requestOwnerSearchTimer = this.scheduleAutocompleteSearch(() => {
        this.fetchRequestUsers(query);
      });
    },
    selectRequestOwner(user) {
      this.requestOwnerId = user.id;
      this.requestOwnerQuery = `${user.first_name} ${user.last_name}${user.pi_name ? ` (${user.pi_name})` : ""}`;
      this.resetRequestOwnerAutocomplete();
      this.requestOwnerSuggestions = [user];
    },
    openRequestOwnerSuggestions() {
      this.showRequestOwnerSuggestions =
        !!this.requestOwnerQuery && !!this.requestOwnerSuggestions.length;
      if (
        this.showRequestOwnerSuggestions &&
        this.highlightedRequestOwnerSuggestionIndex < 0
      ) {
        this.setAutocompleteHighlight(
          "highlightedRequestOwnerSuggestionIndex",
          this.requestOwnerSuggestions
        );
      }
    },
    moveRequestOwnerHighlight(direction) {
      if (!this.isStaffUser || !this.isEditMode || !this.canEditRequest) return;
      this.openRequestOwnerSuggestions();
      this.moveAutocompleteHighlight(
        "highlightedRequestOwnerSuggestionIndex",
        this.requestOwnerSuggestions,
        direction
      );
    },
    selectHighlightedRequestOwner() {
      if (!this.showRequestOwnerSuggestions) return;
      const user = this.getHighlightedAutocompleteItem(
        this.requestOwnerSuggestions,
        this.highlightedRequestOwnerSuggestionIndex
      );
      if (user) {
        this.selectRequestOwner(user);
      }
    },
    handleRelatedProjectInput(event) {
      if (!this.canEditRelatedProjects) return;
      const query = String(event.target.value || "");
      this.relatedProjectQuery = query;
      this.showRelatedProjectSuggestions = !!query;
      this.resetRelatedProjectHighlight();
      this.clearAutocompleteTimer("relatedProjectSearchTimer");
      if (!query.trim()) {
        this.relatedProjectSuggestions = [];
        return;
      }
      this.relatedProjectSearchTimer = this.scheduleAutocompleteSearch(() => {
        this.fetchRelatedProjects({ query });
      });
    },
    selectRelatedProject(project) {
      const id = Number(project?.id);
      if (!Number.isInteger(id) || id <= 0) return;
      if (this.relatedProjectsSelection.some((item) => item.id === id)) {
        this.relatedProjectQuery = "";
        this.resetRelatedProjectAutocomplete();
        return;
      }
      this.relatedProjectsSelection = [
        ...this.relatedProjectsSelection,
        {
          id,
          name: project?.name || `Request ${id}`
        }
      ];
      this.relatedProjectQuery = "";
      this.resetRelatedProjectAutocomplete({ clearSuggestions: true });
    },
    openRelatedProjectSuggestions() {
      this.showRelatedProjectSuggestions = !!this.relatedProjectQuery;
      if (
        this.showRelatedProjectSuggestions &&
        this.highlightedRelatedProjectSuggestionIndex < 0
      ) {
        this.setAutocompleteHighlight(
          "highlightedRelatedProjectSuggestionIndex",
          this.relatedProjectSuggestions
        );
      }
    },
    moveRelatedProjectHighlight(direction) {
      if (!this.canEditRelatedProjects) return;
      this.openRelatedProjectSuggestions();
      this.moveAutocompleteHighlight(
        "highlightedRelatedProjectSuggestionIndex",
        this.relatedProjectSuggestions,
        direction
      );
    },
    selectHighlightedRelatedProject() {
      if (!this.showRelatedProjectSuggestions) return;
      const project = this.getHighlightedAutocompleteItem(
        this.relatedProjectSuggestions,
        this.highlightedRelatedProjectSuggestionIndex
      );
      if (project) {
        this.selectRelatedProject(project);
      }
    },
    removeRelatedProject(projectId) {
      if (!this.canEditRelatedProjects) return;
      const id = Number(projectId);
      this.relatedProjectsSelection = this.relatedProjectsSelection.filter(
        (project) => project.id !== id
      );
    },
    closeRelatedProjectSuggestions() {
      setTimeout(() => {
        this.resetRelatedProjectAutocomplete();
      }, AUTOCOMPLETE_BLUR_CLOSE_DELAY_MS);
    },
    closeRequestOwnerSuggestions() {
      setTimeout(() => {
        this.resetRequestOwnerAutocomplete();
      }, AUTOCOMPLETE_BLUR_CLOSE_DELAY_MS);
    },
    resetRequestOwnerAutocomplete() {
      this.showRequestOwnerSuggestions = false;
      this.resetRequestOwnerHighlight();
    },
    resetRelatedProjectAutocomplete({ clearSuggestions = false } = {}) {
      this.showRelatedProjectSuggestions = false;
      this.resetRelatedProjectHighlight();
      if (clearSuggestions) {
        this.relatedProjectSuggestions = [];
      }
    },
    resetRequestOwnerHighlight() {
      this.highlightedRequestOwnerSuggestionIndex = -1;
    },
    resetRelatedProjectHighlight() {
      this.highlightedRelatedProjectSuggestionIndex = -1;
    },
    clearAutocompleteTimer(timerKey) {
      if (this[timerKey]) {
        clearTimeout(this[timerKey]);
        this[timerKey] = null;
      }
    },
    scheduleAutocompleteSearch(callback) {
      return setTimeout(callback, AUTOCOMPLETE_SEARCH_DEBOUNCE_MS);
    },
    setAutocompleteHighlight(indexKey, items) {
      this[indexKey] = this.getInitialAutocompleteIndex(items);
    },
    getInitialAutocompleteIndex(items) {
      return Array.isArray(items) && items.length ? 0 : -1;
    },
    moveAutocompleteHighlight(indexKey, items, direction) {
      this[indexKey] = this.getNextAutocompleteIndex(
        this[indexKey],
        Array.isArray(items) ? items.length : 0,
        direction
      );
    },
    getNextAutocompleteIndex(currentIndex, itemCount, direction) {
      if (!itemCount) return -1;
      if (currentIndex < 0) {
        return direction > 0 ? 0 : itemCount - 1;
      }
      return (currentIndex + direction + itemCount) % itemCount;
    },
    getHighlightedAutocompleteItem(items, highlightedIndex) {
      if (!Array.isArray(items) || !items.length) return null;
      const index =
        highlightedIndex >= 0 && highlightedIndex < items.length
          ? highlightedIndex
          : 0;
      return items[index];
    },
    saveRequest() {
      if (this.isEditMode) {
        return this.saveExistingRequest();
      }
      return this.saveNewRequest();
    },
    validateEditRecordsForSave() {
      const results = {};
      ["library", "sample"].forEach((mode) => {
        const rows =
          mode === "library"
            ? this.editRecordsByType.library || []
            : this.editRecordsByType.sample || [];
        if (!rows.length) return;
        results[mode] = {
          rows,
          ...this.computeValidationState(rows, mode, {
            useDirtyValidation: true
          })
        };
      });

      const currentMode =
        this.requestEditorMode === "sample" ? "sample" : "library";
      const currentResult = results[currentMode];
      if (currentResult) {
        this.draftValidationState = currentResult.validations;
        this.validationFieldsByRowId = {
          ...this.validationFieldsByRowId,
          ...currentResult.validationFieldsByRowId
        };
        this.validDraftCount = currentResult.validCount;
        this.$nextTick(() => this.applyValidationStyling());
      }

      const modeHasErrors = (mode) => {
        const result = results[mode];
        if (!result) return false;
        return result.validCount !== result.rows.length;
      };

      return {
        hasErrors: modeHasErrors("library") || modeHasErrors("sample"),
        currentModeHasErrors: modeHasErrors(currentMode),
        otherModeHasErrors:
          currentMode === "library"
            ? modeHasErrors("sample")
            : modeHasErrors("library")
      };
    },
    async saveExistingRequest() {
      if (!this.canEditRequest) {
        if (this.relatedProjectsChanged) {
          return this.saveRelatedProjectsOnly();
        }
        showNotification("You lack permission to edit requests.", "warning");
        return;
      }
      this.persistDraftRowsToEditRecords(this.requestEditorMode);
      if (this.isRequestSaving) return;
      if (!this.requestId) {
        showNotification("Request ID is missing.", "error");
        return;
      }
      const description = (this.newRequest.description || "").trim();
      const descriptionValid = !!description;
      if (!descriptionValid) {
        this.descriptionError = "Description is a required field.";
      }
      if (!this.isStaffUser && !this.newRequest.cost_unit) {
        this.costUnitError = "Cost unit is a required field.";
      }
      if (this.descriptionError || this.costUnitError) {
        showNotification("Required fields are missing.", "warning");
        return;
      }
      const totalRecords =
        (this.editRecordsByType.library || []).length +
        (this.editRecordsByType.sample || []).length;
      if (!totalRecords) {
        showNotification("Request has no libraries or samples.", "warning");
        return;
      }
      if (!this.requestFileTypesAreValid()) return;
      const validationStatus = this.validateEditRecordsForSave();
      if (validationStatus.currentModeHasErrors) {
        showNotification(
          "Resolve validation errors before updating this request.",
          "warning"
        );
        return;
      }
      if (validationStatus.otherModeHasErrors) {
        const otherModeLabel =
          this.requestEditorMode === "library" ? "Sample" : "Library";
        showNotification(
          `Resolve validation errors in ${otherModeLabel} records before updating.`,
          "warning"
        );
        return;
      }
      try {
        this.isRequestSaving = true;
        const updateType = async (mode) => {
          const endpoint = mode === "sample" ? "samples" : "libraries";
          const rows =
            mode === "sample"
              ? this.editRecordsByType.sample || []
              : this.editRecordsByType.library || [];

          const existingRows = rows.filter((row) => row.pk);
          const newRows = rows.filter((row) => !row.pk);

          if (existingRows.length) {
            const payloads = existingRows.map((row) => ({
              pk: row.pk,
              ...(mode === "sample"
                ? this.buildSamplePayload(row)
                : this.buildLibraryPayload(row))
            }));
            const formData = new FormData();
            formData.append("data", JSON.stringify(payloads));
            await axiosRef.post(
              `${urlStringStart}/api/${endpoint}/edit/`,
              formData,
              {
                headers: { "Content-Type": "multipart/form-data" }
              }
            );
          }

          if (newRows.length) {
            const payloads = newRows.map((row) =>
              mode === "sample"
                ? this.buildSamplePayload(row)
                : this.buildLibraryPayload(row)
            );
            const created = await this.submitRequestEditor(endpoint, payloads);
            created.forEach((record, index) => {
              const row = newRows[index];
              if (row) {
                row.pk = record.pk;
                row.record_type =
                  record.record_type ||
                  (mode === "sample" ? "Sample" : "Library");
                row.barcode = record.barcode;
              }
            });
          }
        };

        if (this.editRecordsByType.library?.length) {
          await updateType("library");
        }
        if (this.editRecordsByType.sample?.length) {
          await updateType("sample");
        }

        const allRecords = [
          ...(this.editRecordsByType.library || []).map((record) => ({
            pk: record.pk,
            record_type: "Library"
          })),
          ...(this.editRecordsByType.sample || []).map((record) => ({
            pk: record.pk,
            record_type: "Sample"
          }))
        ];

        const payload = {
          cost_unit: this.newRequest.cost_unit || null,
          description,
          related_requests: this.relatedProjectsSelection.map(
            (project) => project.id
          ),
          records: allRecords,
          files: this.uploadedRequestFileIds,
          file_types: this.requestFileTypesPayload()
        };
        if (this.isStaffUser && this.requestOwnerId) {
          payload.user = this.requestOwnerId;
        }
        const formData = new FormData();
        formData.append("data", JSON.stringify(payload));
        const response = await axiosRef.post(
          `${urlStringStart}/api/requests/${this.requestId}/edit/`,
          formData,
          {
            headers: { "Content-Type": "multipart/form-data" }
          }
        );
        if (response?.data?.success) {
          if (this.notifyOnSave) {
            showNotification("Request updated successfully.", "success");
          }
          this.emitSaved({
            success: true,
            mode: "edit",
            request_id: this.requestId,
            name: response.data.name,
            user: response.data.user,
            cost_unit: this.newRequest.cost_unit || null,
            description,
            related_requests: this.relatedProjectsSelection.map(
              (project) => project.id
            ),
            files: this.uploadedRequestFiles || [],
            fileIds: this.uploadedRequestFileIds || [],
            records: {
              library: this.editRecordsByType.library || [],
              sample: this.editRecordsByType.sample || []
            }
          });
          if (this.closeOnSave) {
            this.emitClose();
          }
        } else {
          showNotification("Request update failed.", "error");
        }
      } catch (error) {
        handleError(error);
      } finally {
        this.isRequestSaving = false;
      }
    },
    async saveRelatedProjectsOnly() {
      // Limited save path for locked (restrict_permissions) requests:
      // only related_requests may change; every other field is resubmitted
      // from the load-time snapshot so nothing else is modified.
      if (this.isRequestSaving) return;
      if (!this.requestId) {
        showNotification("Request ID is missing.", "error");
        return;
      }
      try {
        this.isRequestSaving = true;
        const relatedRequestIds = this.relatedProjectsSelection.map(
          (project) => project.id
        );
        const payload = {
          cost_unit: this.editSnapshot.cost_unit || null,
          description: this.editSnapshot.description || "",
          related_requests: relatedRequestIds,
          records: this.existingRecords.map((record) => ({
            pk: record.pk,
            record_type: record.record_type
          })),
          files: this.editSnapshot.fileIds || [],
          file_types: this.editSnapshot.fileTypes || {}
        };
        const formData = new FormData();
        formData.append("data", JSON.stringify(payload));
        const response = await axiosRef.post(
          `${urlStringStart}/api/requests/${this.requestId}/edit/`,
          formData,
          {
            headers: { "Content-Type": "multipart/form-data" }
          }
        );
        if (response?.data?.success) {
          this.editSnapshot.related_request_ids = [...relatedRequestIds];
          if (this.notifyOnSave) {
            showNotification(
              "Related projects updated successfully.",
              "success"
            );
          }
          this.emitSaved({
            success: true,
            mode: "edit",
            request_id: this.requestId,
            name: response.data.name,
            user: response.data.user,
            cost_unit: this.editSnapshot.cost_unit || null,
            description: this.editSnapshot.description || "",
            related_requests: relatedRequestIds,
            files: this.uploadedRequestFiles || [],
            fileIds: this.uploadedRequestFileIds || [],
            records: {
              library: this.editRecordsByType.library || [],
              sample: this.editRecordsByType.sample || []
            }
          });
          if (this.closeOnSave) {
            this.emitClose();
          }
        } else {
          showNotification("Request update failed.", "error");
        }
      } catch (error) {
        handleError(error);
      } finally {
        this.isRequestSaving = false;
      }
    },
    async saveNewRequest() {
      if (this.isRequestSaving) return;
      const description = (this.newRequest.description || "").trim();
      const descriptionValid = !!description;
      if (!descriptionValid) {
        this.descriptionError = "Description is a required field.";
      }
      if (!this.isStaffUser && !this.newRequest.cost_unit) {
        this.costUnitError = "Cost unit is a required field.";
      }
      if (this.descriptionError || this.costUnitError) {
        showNotification("Required fields are missing.", "warning");
        return;
      }
      if (!this.requestFileTypesAreValid()) return;
      const { rowCount } = this.revalidateDraftRows();
      if (!rowCount) {
        showNotification("Add at least one record before saving.", "warning");
        return;
      }
      if (this.validDraftCount !== rowCount) {
        showNotification(
          "Resolve all validation errors before saving.",
          "warning"
        );
        return;
      }
      const drafts = this.getDraftTableRows();
      const payloads =
        this.requestEditorMode === "library"
          ? drafts.map((row) => this.buildLibraryPayload(row))
          : drafts.map((row) => this.buildSamplePayload(row));
      const recordTypeLabel = this.requestEditorModeLabel;
      const payload = {
        cost_unit: this.newRequest.cost_unit || null,
        description,
        related_requests: this.relatedProjectsSelection.map(
          (project) => project.id
        ),
        records: [],
        files: this.uploadedRequestFileIds,
        file_types: this.requestFileTypesPayload()
      };
      try {
        this.isRequestSaving = true;
        const endpoint =
          this.requestEditorMode === "library" ? "libraries" : "samples";
        const created = await this.submitRequestEditor(endpoint, payloads);
        if (!created.length) {
          const emptyLabel =
            this.requestEditorMode === "library"
              ? "No libraries were created."
              : "No samples were created.";
          showNotification(emptyLabel, "error");
          return;
        }
        payload.records = created.map((record, index) => ({
          pk: record.pk,
          record_type: record.record_type || recordTypeLabel,
          name: record.name,
          barcode: record.barcode,
          id: record.id || `Record-${record.pk || index + 1}`,
          status: record.status ?? null,
          is_converted: record.is_converted ?? false,
          selected: false
        }));
        const formData = new FormData();
        formData.append("data", JSON.stringify(payload));
        const response = await axiosRef.post(
          `${urlStringStart}/api/requests/`,
          formData,
          {
            headers: { "Content-Type": "multipart/form-data" }
          }
        );
        if (response?.data?.success) {
          if (this.notifyOnSave) {
            showNotification("Request created successfully.", "success");
          }
          this.emitSaved(response.data);
          if (this.closeOnSave) {
            this.emitClose();
          }
        } else {
          showNotification("Request creation failed.", "error");
        }
      } catch (error) {
        handleError(error);
      } finally {
        this.isRequestSaving = false;
      }
    },
    async submitRequestEditor(endpoint, payloads) {
      const formData = new FormData();
      formData.append("data", JSON.stringify(payloads));
      const response = await axiosRef.post(
        `${urlStringStart}/api/${endpoint}/`,
        formData,
        {
          headers: { "Content-Type": "multipart/form-data" }
        }
      );
      const success =
        response?.data?.success === undefined
          ? true
          : Boolean(response.data.success);
      if (!success) {
        throw new Error("Server rejected the request.");
      }
      return response?.data?.data || [];
    },
    async deleteSelectedEditRows() {
      const ids = new Set(this.selectedDraftRowIds);
      const rowsToDelete = this.requestEditorDraftRows.filter((row) =>
        ids.has(row.tempId)
      );
      if (!rowsToDelete.length) return;
      const remaining = this.requestEditorDraftRows.filter(
        (row) => !ids.has(row.tempId)
      );
      this.requestEditorDraftRows = remaining;
      this.selectedDraftRowIds = [];
      this.persistDraftRowsToEditRecords(this.requestEditorMode);
      this.$nextTick(() => this.revalidateDraftRows());
    },
    async fetchFilterOptions() {
      if (this.filterOptionsLoaded) return;
      try {
        const protocolsRes = await axiosRef.get(
          `${urlStringStart}/api/library_protocols/`
        );
        this.protocolsList = protocolsRes.data.sort((a, b) =>
          a.name.localeCompare(b.name, undefined, { sensitivity: "base" })
        );
        const readLengthsRes = await axiosRef.get(
          `${urlStringStart}/api/read_lengths/`
        );
        this.readLengthsList = readLengthsRes.data.sort((a, b) => {
          const getVal = (str) => str.match(/\d+/g)?.map(Number)[1] ?? Infinity;
          return getVal(a.name) - getVal(b.name);
        });
        const analysisRes = await axiosRef.get(
          `${urlStringStart}/api/library_types/`
        );
        this.analysisTypesList = analysisRes.data.sort((a, b) =>
          a.name.localeCompare(b.name, undefined, { sensitivity: "base" })
        );
        this.filterOptionsLoaded = true;
      } catch (error) {
        handleError(error);
      }
    },
    async fetchIndexTypesList() {
      if (this.indexTypesLoaded) return;
      try {
        const response = await axiosRef.get(
          `${urlStringStart}/api/index_types/`
        );
        this.indexTypesList = (response.data || []).sort((a, b) =>
          a.name.localeCompare(b.name, undefined, { sensitivity: "base" })
        );
        this.indexTypesLoaded = true;
      } catch (error) {
        handleError(error);
      }
    },
    async fetchNucleicAcidTypes() {
      if (this.nucleicAcidTypesLoaded) return;
      try {
        const response = await axiosRef.get(
          `${urlStringStart}/api/nucleic_acid_types/`
        );
        this.nucleicAcidTypesList = (response.data || []).sort((a, b) =>
          a.name.localeCompare(b.name, undefined, { sensitivity: "base" })
        );
        this.nucleicAcidTypesLoaded = true;
      } catch (error) {
        handleError(error);
      }
    },
    async fetchOrganismsList() {
      if (this.organismsLoaded) return;
      try {
        const response = await axiosRef.get(`${urlStringStart}/api/organisms/`);
        this.organismsList = (response.data || []).sort((a, b) =>
          a.name.localeCompare(b.name, undefined, { sensitivity: "base" })
        );
        this.organismsLoaded = true;
      } catch (error) {
        handleError(error);
      }
    }
  }
};
</script>

<style scoped>
.request-editor-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  z-index: 999;
  animation: request-editor-fade-in 0.18s ease-out;
  overflow: hidden;
}

.request-editor-overlay.drag-over {
  border: none;
}

.request-editor-overlay.drag-over::after {
  content: "";
  position: absolute;
  inset: 0;
  background-color: #00bfff36;
  border: 2px dashed #2196f3;
  pointer-events: none;
  z-index: 2;
}

.request-editor-overlay.drag-over .request-editor-modal {
  transform: scale(1.02);
  transition: transform 0.2s ease;
}

.request-editor-modal {
  background: white;
  border-radius: 8px;
  width: calc(100% - 20px);
  height: calc(100% - 20px);
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.2);
  transform: scale(0.98);
  opacity: 0;
  animation: request-editor-pop-in 0.22s ease-out forwards;
  overflow: hidden;
  position: relative;
  z-index: 1;
}

.request-editor-loading-overlay {
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, 0.8);
  z-index: 4;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  animation: fade-in 0.15s ease-out forwards;
}

.request-editor-loading-overlay p {
  margin-top: 10px;
  margin-left: 10px;
  font-size: 15px;
  color: #555;
}

.saving-overlay {
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 5;
}

.saving-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 20px 24px;
  background: #ffffff;
  border: 1px solid #d0d0d0;
  border-radius: 10px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  font-size: 14px;
  color: #333;
}

.confirm-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1001;
}

.confirm-modal {
  background: #ffffff;
  border-radius: 8px;
  width: 460px;
  max-width: calc(100% - 40px);
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.25);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.owner-change-modal {
  width: 560px;
}

.owner-change-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.description-textarea {
  width: 100%;
  min-height: 120px;
  resize: vertical;
  padding: 11px 12px;
  border: 1px solid #d0d0d0;
  border-radius: 8px;
  font-size: 14px;
  font-family: inherit;
  color: #232323;
  background: #f4f6f8;
  line-height: 1.5;
  box-sizing: border-box;
}

.related-projects-field {
  border: 1px solid #d0d0d0;
  border-radius: 8px;
  background: #f6f8fa;
  padding: 12px;
  overflow: visible;
}

.related-projects-field.focused {
  border-color: #9aa6b2;
}

.related-projects-field .related-project-search input {
  background: #ffffff;
  font-size: 13px;
  padding-right: 36px;
}

.related-projects-field .related-project-search input:focus {
  outline: none;
}

.related-project-search-icon {
  position: absolute;
  right: 12px;
  top: 50%;
  color: darkgrey;
  font-size: 13px;
  pointer-events: none;
  transform: translateY(-50%);
}

.related-projects-selected {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}

.related-project-chip {
  border: 1px solid #b8c6d1;
  border-radius: 8px;
  background: #eef3f7;
  color: #16364a;
  font-size: 14px;
  padding: 4px 8px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  line-height: 1.2;
}

.related-project-chip.disabled {
  opacity: 0.7;
}

.related-project-remove {
  width: 16px;
  height: 20px;
  border: none;
  border-radius: 50%;
  background: transparent;
  color: inherit;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  cursor: pointer;
  font-size: 14px;
}

.related-project-remove:hover,
.related-project-remove:focus-visible {
  background: rgba(22, 54, 74, 0.12);
  outline: none;
}

.confirm-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #0b5f5a;
  background: #006c64;
}

.confirm-title {
  font-size: 14px;
  font-weight: 600;
  color: #ffffff;
}

.confirm-body {
  padding: 16px;
  font-size: 13px;
  color: #333;
  line-height: 1.5;
}

.confirm-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  padding: 12px 16px 16px;
}

.confirm-modal .popup-close-button {
  color: #ffffff;
}

.confirm-modal .popup-close-button:hover {
  color: #cfe9e6;
}

.confirm-modal .popup-button {
  background: #006c64;
  border: 1px solid #0b5f5a;
  color: #ffffff;
  border-radius: 6px;
  padding: 6px 16px;
  font-weight: 600;
}

.confirm-modal .popup-button:hover {
  background: #0a5d56;
}

.confirm-modal .popup-button:not(.yes-button) {
  background: #ffffff;
  color: #006c64;
}

.confirm-modal .popup-button:not(.yes-button):hover {
  background: #e8f2f1;
}

.request-editor-content {
  height: 100%;
  display: grid;
  grid-template-columns: var(--left-panel-width) var(--panel-toggle-width) 1fr;
  grid-template-rows: auto 1fr auto;
  --left-panel-width: 320px;
  --panel-toggle-width: 34px;
}

.request-editor-content.collapsed {
  --left-panel-width: 0px;
}

.request-editor-header-left {
  grid-column: 1;
  grid-row: 1;
  display: flex;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid #e5e7eb;
  font-size: 20px;
  font-weight: 600;
  color: #13415b;
  overflow: hidden;
  min-width: 0;
}

.request-editor-header-left.collapsed {
  padding: 0;
  opacity: 0;
  pointer-events: none;
}

.title-with-icon {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.header-icon {
  font-size: 20px;
  color: #13415b;
}

.header-title-text {
  display: block;
  min-width: 0;
  max-width: 100%;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.request-editor-header-right {
  grid-column: 3;
  grid-row: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 16px 24px 16px 12px;
  border-bottom: 1px solid #e5e7eb;
  font-size: 20px;
  font-weight: 600;
  color: #13415b;
}

.header-actions {
  display: inline-flex;
  align-items: center;
  gap: 12px;
}

.owner-change-button {
  height: 36px;
  padding: 0 16px;
  border-radius: 8px;
  font-size: 12px;
}

.header-table-actions {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  padding: 7px 9px;
  border: 1px solid #d0d0d0;
  border-radius: 10px;
  background: #f8fafb;
  box-shadow: inset 0 1px 0 #ffffff;
}

.header-table-actions.utility-actions {
  padding: 6px 8px;
  margin-right: auto;
  border: 1px solid #d7dee3;
  background: #f3f6f7;
  box-shadow: inset 0 1px 0 #ffffff;
  border-radius: 10px;
}

.clipboard-button {
  padding-left: 10px;
  padding-right: 10px;
}

.add-count-group {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px;
  height: 40px;
  box-sizing: border-box;
  border-radius: 8px;
  background: #eef2f3;
  border: 1px solid #d7dee3;
}

.add-count-input {
  width: 46px;
  height: 30px;
  border: 1px solid #0f766e;
  border-radius: 8px;
  padding: 2px 8px;
  font-size: 13px;
  text-align: right;
}

.add-count-input:focus {
  outline: none;
  box-shadow: 0 0 0 2px rgba(15, 118, 110, 0.2);
}

.add-count-input.input-error {
  border-color: #d14343;
}

.add-count-input.input-error:focus {
  box-shadow: 0 0 0 2px rgba(209, 67, 67, 0.2);
}

.add-count-button {
  height: 30px !important;
  border-radius: 8px !important;
  padding-left: 14px;
  padding-right: 16px;
}

.add-count-input::-webkit-outer-spin-button,
.add-count-input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.add-count-input[type="number"] {
  appearance: textfield;
  -moz-appearance: textfield;
}

.header-table-actions .icon-button.text-button {
  height: 40px;
  padding: 0 16px;
  border-radius: 8px;
  font-size: 13px;
}

.header-table-actions.hidden {
  visibility: hidden;
  pointer-events: none;
}

.request-editor-header-right .popup-close-button {
  color: #13415b;
  font-size: 24px;
}

.request-editor-header-right .popup-close-button:hover {
  color: #0f5c84;
}

.request-editor-header-right .popup-close-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.help-button {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: none;
  background: transparent;
  color: #13415b;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 600;
}

.help-button:hover {
  color: #0f5c84;
}

.shortcut-help {
  position: relative;
  display: inline-flex;
  align-items: center;
}

.feature-help {
  position: relative;
  display: inline-flex;
  align-items: center;
}

.shortcut-help-button {
  font-size: 14px;
}

.shortcut-help-panel {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 290px;
  max-width: min(290px, calc(100vw - 24px));
  background: #ffffff;
  border: 1px solid #d7dee3;
  border-radius: 10px;
  padding: 12px 14px;
  box-shadow: 0 12px 26px rgba(0, 0, 0, 0.16);
  z-index: 6;
}

.shortcut-help-panel::before {
  content: "";
  position: absolute;
  top: -6px;
  right: 12px;
  width: 12px;
  height: 12px;
  background: #ffffff;
  border-left: 1px solid #d7dee3;
  border-top: 1px solid #d7dee3;
  transform: rotate(45deg);
}

.shortcut-help-title {
  font-size: 12px;
  font-weight: 600;
  color: #13415b;
  margin-bottom: 8px;
}

.shortcut-help-list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 8px;
  font-size: 12px;
  color: #4b5563;
}

.shortcut-help-list li {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  column-gap: 14px;
  row-gap: 4px;
}

.shortcut-keys {
  display: inline-flex;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
  min-width: 96px;
  white-space: nowrap;
}

.shortcut-plus {
  font-size: 11px;
  color: #94a3b8;
  margin: 0 2px;
}

.shortcut-help-list kbd {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 22px;
  height: 22px;
  padding: 0 6px;
  border-radius: 6px;
  border: 1px solid #d0d0d0;
  background: #f3f6f7;
  font-size: 11px;
  font-weight: 600;
  color: #1f2937;
  box-shadow: inset 0 -1px 0 #e5e7eb;
}

.feature-help-panel {
  position: absolute;
  top: calc(100% + 10px);
  right: -28px;
  width: min(760px, calc(100vw - 72px));
  max-height: min(72vh, 760px);
  overflow: hidden;
  background: #ffffff;
  border: 1px solid #d7dee3;
  border-radius: 14px;
  box-shadow: 0 18px 42px rgba(0, 0, 0, 0.18);
  z-index: 8;
}

.feature-help-panel::before {
  content: "";
  position: absolute;
  top: -7px;
  right: 36px;
  width: 14px;
  height: 14px;
  background: #ffffff;
  border-left: 1px solid #d7dee3;
  border-top: 1px solid #d7dee3;
  transform: rotate(45deg);
}

.feature-help-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.feature-help-scroll {
  max-height: min(72vh, 760px);
  overflow-y: auto;
  overflow-x: hidden;
  padding: 18px;
  scrollbar-gutter: stable;
}

.feature-help-title {
  font-size: 16px;
  font-weight: 700;
  color: #13415b;
  margin-bottom: 4px;
}

.feature-help-header p {
  margin: 0;
  font-size: 13px;
  line-height: 1.5;
  color: #4b5563;
}

.feature-help-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.feature-help-section {
  border: 1px solid #dbe4ea;
  border-radius: 12px;
  background: linear-gradient(180deg, #f9fbfc 0%, #f4f7f8 100%);
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.feature-help-section-wide {
  grid-column: 1 / -1;
}

.feature-help-section-head {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 700;
  color: #13415b;
}

.feature-help-points {
  margin: 0;
  padding-left: 18px;
  display: grid;
  gap: 6px;
  font-size: 12px;
  line-height: 1.5;
  color: #44505f;
}

.feature-help-points strong {
  color: #13415b;
}

.feature-help-visual {
  border: 1px solid #d5dde4;
  border-radius: 10px;
  background: #ffffff;
  padding: 10px;
  display: grid;
  gap: 8px;
  min-height: 118px;
}

.visual-header {
  font-size: 11px;
  font-weight: 700;
  color: #5b6878;
}

.visual-dropzone {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 42px;
  border: 1px dashed #7fa8c0;
  border-radius: 8px;
  background: #eef7fb;
  color: #0f5c84;
  font-size: 12px;
  font-weight: 600;
}

.visual-file-row,
.visual-table-row,
.visual-add-strip {
  display: grid;
  align-items: center;
  gap: 8px;
}

.visual-file-row {
  grid-template-columns: 1fr auto;
  font-size: 11px;
  color: #44505f;
  padding: 8px 10px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #fafbfc;
}

.visual-file-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.visual-toggle {
  display: grid;
  grid-template-columns: 1fr 1fr;
  border: 1px solid #d5dde4;
  border-radius: 9px;
  background: #e8edf1;
  overflow: hidden;
  font-size: 11px;
  font-weight: 700;
  color: #556171;
}

.visual-toggle span {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 36px;
}

.visual-toggle-active {
  background: #0f766e;
  color: #ffffff;
}

.visual-add-strip {
  grid-template-columns: 46px 1fr;
}

.visual-count-box,
.visual-add-button {
  min-height: 32px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  font-size: 11px;
  font-weight: 700;
}

.visual-count-box {
  border: 1px solid #0f766e;
  color: #13415b;
  background: #ffffff;
}

.visual-add-button {
  background: #0f766e;
  color: #ffffff;
}

.visual-table-row {
  grid-template-columns: repeat(3, minmax(0, 1fr));
  font-size: 11px;
  color: #44505f;
}

.visual-table-row span {
  min-height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #e5e7eb;
  background: #fbfcfd;
}

.visual-table-head span {
  background: #eef2f5;
  color: #44505f;
  font-weight: 700;
}

.visual-valid-cell {
  background: #edf9f4 !important;
  border-color: #a7d7bf !important;
}

.visual-invalid-cell {
  background: #fff3f2 !important;
  border-color: #efb6b0 !important;
  color: #b42318;
}

.visual-range-cell {
  background: #edf5ff !important;
  border-color: #95bdf6 !important;
}

.visual-shortcuts-inline {
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 5px;
  font-size: 11px;
  color: #64748b;
}

.visual-shortcuts-inline kbd {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 22px;
  height: 22px;
  padding: 0 6px;
  border-radius: 6px;
  border: 1px solid #d0d0d0;
  background: #f3f6f7;
  font-size: 11px;
  font-weight: 700;
  color: #1f2937;
}

.feature-help-callout {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  background: #eef7f6;
  border: 1px solid #c7e2de;
  color: #275c56;
  font-size: 12px;
  line-height: 1.5;
}

.request-editor-body-left {
  grid-column: 1;
  grid-row: 2;
  padding: 20px 12px 20px 24px;
  overflow: hidden;
  min-width: 0;
}

.request-editor-content.collapsed .request-editor-body-left {
  padding: 0;
  pointer-events: none;
}

.request-editor-body-right {
  grid-column: 3;
  grid-row: 2;
  padding: 20px 24px 20px 12px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.request-form-panel {
  width: 320px;
  min-width: 290px;
  border-right: 1px solid #e5e7eb;
  padding-right: 12px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
  overflow-x: hidden;
  height: 100%;
  transition:
    width 0.25s ease,
    padding 0.25s ease,
    opacity 0.25s ease;
}

.request-panel-container {
  display: flex;
  align-items: stretch;
  position: relative;
  height: 100%;
}

.request-panel-container.collapsed {
  border-right: none;
}

.request-form-panel.collapsed {
  width: 0;
  min-width: 0;
  padding-right: 0;
  opacity: 0;
  pointer-events: none;
  border-right: none;
}

.field-block {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 13px;
  color: #333;
}

.field-block select {
  padding: 11px 8px;
  border: 1px solid #d0d0d0;
  border-radius: 8px;
  font-size: 14px;
  font-family: inherit;
  color: #232323;
  background: #f4f6f8;
  line-height: 1.5;
  box-sizing: border-box;
}

.field-block textarea {
  padding: 11px 12px;
  border: 1px solid #d0d0d0;
  border-radius: 8px;
  font-size: 14px;
  font-family: inherit;
  color: #232323;
  background: #f4f6f8;
  line-height: 1.5;
  box-sizing: border-box;
}

.field-block input {
  padding: 11px 12px;
  border: 1px solid #d0d0d0;
  border-radius: 8px;
  font-size: 14px;
  font-family: inherit;
  color: #232323;
  background: #f4f6f8;
  line-height: 1.5;
  box-sizing: border-box;
}

.disabled-field-value {
  padding: 11px 12px;
  border: 1px solid #d0d0d0;
  border-radius: 8px;
  font-size: 14px;
  font-family: inherit;
  color: #9ba3af;
  background: #f4f6f8;
  line-height: 1.5;
  box-sizing: border-box;
  cursor: not-allowed;
  user-select: none;
}

.field-block select.placeholder {
  color: #9ba3af;
}

.field-block input::placeholder {
  color: #9ba3af;
  opacity: 1;
}

.field-block select.placeholder option {
  color: #232323;
}

.description-textarea {
  width: 100%;
  min-height: 300px;
  resize: none;
  line-height: 1.5;
}

.description-textarea::placeholder {
  color: #9ba3af;
}

.input-error {
  border-color: #d14343 !important;
}

.field-error {
  margin-top: 4px;
  font-size: 12px;
  color: #b42318;
}

.required {
  color: #b42318;
  margin-left: 1px;
}

.files-section {
  border: 1px solid #d0d0d0;
  background: #f6f8fa;
  border-radius: 8px;
  padding: 12px;
  flex: 0 0 auto;
  display: flex;
  flex-direction: column;
  min-height: 320px;
}

.files-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}

.files-header > div {
  flex: 1 1 150px;
  min-width: 0;
}

.files-header small {
  display: block;
  font-size: 11px;
  color: #6b7280;
}

.request-file-add-button {
  display: inline-flex;
  flex: 0 0 auto;
  width: auto;
  min-width: 112px;
  max-width: none;
  height: 32px;
  min-height: 32px;
  margin-left: auto;
  gap: 7px;
  padding: 0 14px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  line-height: 1;
}

.request-file-add-button span {
  overflow: visible;
  text-overflow: clip;
  line-height: 1;
}

.request-file-add-button svg {
  width: 13px;
  height: 13px;
}

.files-table-wrapper {
  width: 100%;
  border: 1px solid #d0d0d0;
  border-radius: 8px;
  overflow-y: auto;
  overflow-x: auto;
  margin-top: 8px;
  flex: 1 1 auto;
  min-height: 220px;
  display: flex;
  flex-direction: column;
  background: white;
}

.files-table {
  width: 100%;
  min-width: 720px;
  border-collapse: separate;
  border-spacing: 0;
  table-layout: fixed;
  font-size: 12px;
}
.files-table .file-col-name {
  width: 30%;
}
.files-table .file-col-type {
  width: 38%;
}
.files-table .file-col-size {
  width: 14%;
}
.files-table .file-col-actions {
  width: 18%;
}

.files-table.files-table-empty {
  height: 100%;
}

.files-table th,
.files-table td {
  padding: 8px 12px;
  text-align: left;
  vertical-align: middle;
  line-height: 1.4;
}
.files-table th {
  padding-top: 5px;
  padding-bottom: 5px;
  white-space: nowrap;
  font-size: 12px;
  line-height: 1.2;
  font-weight: 600;
}

.files-table th {
  border-bottom: 1px solid #d0d0d0;
}

.files-table .empty-cell {
  text-align: center;
  color: #7b7f89;
}

.files-table td.actions-cell {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 3px;
}
.owner-change-action-container {
  display: flex;
  justify-content: center;
  align-items: center;
  padding-top: 4px;
}

.files-table td.actions-cell button + button {
  margin-left: 4px;
}

.file-name-cell {
  max-width: 220px;
  display: flex;
  align-items: center;
}

.file-name-text {
  display: inline-block;
  max-width: 100%;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-size-cell {
  max-width: 140px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-type-cell {
  min-width: 250px;
}

.file-type-select,
.file-type-custom-input {
  width: 100%;
  min-height: 30px;
  border: 1px solid #c9d2d6;
  border-radius: 6px;
  background: #ffffff;
  color: #173f53;
  font-size: 11px;
  padding: 5px 7px;
}

.file-type-custom-input {
  margin-top: 5px;
}

.file-type-custom-input.invalid {
  border-color: #c43d43;
  box-shadow: 0 0 0 1px rgba(196, 61, 67, 0.12);
}

.icon-action {
  border: none;
  background: #e6eaef;
  color: #13415b;
  width: 24px;
  height: 24px;
  border-radius: 6px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.icon-action:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.icon-action.danger {
  background: #f3d6d6;
  color: #a3272b;
}

.download-buttons {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px;
  border: 1px solid #d0d0d0;
  border-radius: 6px;
  background: #f6f8fa;
  width: 100%;
  min-height: 42px;
  box-sizing: border-box;
  min-width: 0;
}

.download-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-height: 32px;
  padding: 4px 10px;
  border: 1px solid #0f5c84;
  border-radius: 6px;
  background: #ffffff;
  color: #0f5c84;
  font-size: 11px;
  font-weight: 600;
  text-decoration: none;
  white-space: nowrap;
  transition:
    background 0.2s ease,
    color 0.2s ease,
    border-color 0.2s ease;
  flex: 1 1 0;
  min-width: 0;
  max-width: 100%;
  overflow: hidden;
}

.download-button:hover {
  background: #e8f2f7;
  border-color: #0a4a6a;
  color: #0a4a6a;
}

.download-button span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 100%;
}

.records-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow: hidden;
}

.records-panel.expanded {
  flex-basis: calc(100% - 34px);
}

.panel-toggle-button {
  width: var(--panel-toggle-width);
  border: none;
  background: #f6f8fa;
  color: #0f5c84;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s ease;
}

.panel-toggle-button:hover {
  background: #e2e7ea;
}

.panel-toggle-button.vertical-toggle {
  grid-column: 2;
  grid-row: 1 / span 2;
  align-self: stretch;
  border-left: 1px solid #e5e7eb;
  border-right: 1px solid #e5e7eb;
  z-index: 3;
}

.request-form-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 4px;
}

.request-form-actions-title {
  font-size: 13px;
  font-weight: 400;
  color: #333;
  line-height: 1.4;
}

.controls-group {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px;
  border: 1px solid #d0d0d0;
  border-radius: 6px;
  background: #f6f8fa;
}

.record-type-toggle-group {
  padding: 0;
  border: none;
  background: transparent;
  min-width: 188px;
}

.record-type-switch {
  position: relative;
  width: 188px;
  height: 40px;
  border-radius: 8px;
  background: #e1e6ea;
  border: 1px solid #d0d0d0;
  cursor: pointer;
  padding: 0;
}

.record-type-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.record-type-switch .slider {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 12px;
  font-weight: 600;
  color: #4b5563;
}

.record-type-switch .slider::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  width: 50%;
  height: 100%;
  border-radius: 7px;
  background: #0f766e;
  transition: transform 0.25s ease;
  z-index: 0;
}

.record-type-switch input:checked + .slider::before {
  transform: translateX(100%);
}

.record-type-switch .option {
  flex: 1 1 50%;
  text-align: center;
  z-index: 1;
  transition: color 0.2s ease;
}

.record-type-switch .option.active {
  color: white;
}

.icon-button {
  width: 34px;
  height: 34px;
  border-radius: 8px;
  border: none;
  background: #0f766e;
  color: white;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.icon-button.text-button {
  width: auto;
  padding: 0 10px;
  gap: 6px;
  font-size: 12px;
}

.icon-button:disabled {
  background: #e1e6ea;
  color: #707b8d;
  cursor: not-allowed;
}

.draft-table {
  flex: 1;
  min-height: 260px;
}

.request-editor-footer {
  grid-column: 1 / -1;
  grid-row: 3;
  border-top: 1px solid #e5e7eb;
  padding: 12px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.footer-summary {
  font-size: 13px;
  color: #374151;
  display: flex;
  gap: 6px;
  align-items: center;
}

.footer-actions {
  display: flex;
  gap: 10px;
}

.footer-actions .popup-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.header-button.ghost {
  background: #0f766e;
}

@keyframes request-editor-fade-in {
  from {
    opacity: 0;
  }

  to {
    opacity: 1;
  }
}

@keyframes request-editor-pop-in {
  from {
    opacity: 0;
    transform: scale(0.98);
  }

  to {
    opacity: 1;
    transform: scale(1);
  }
}

@media (max-width: 1180px) {
  .feature-help-panel {
    right: -96px;
    width: min(700px, calc(100vw - 40px));
  }
}

@media (max-width: 920px) {
  .feature-help-panel {
    right: -140px;
    width: min(640px, calc(100vw - 28px));
  }

  .feature-help-grid {
    grid-template-columns: 1fr;
  }

  .feature-help-section-wide {
    grid-column: auto;
  }
  .files-section {
    min-height: 280px;
  }
  .files-table-wrapper {
    min-height: 190px;
  }
  .owner-change-button {
    width: 100%;
    justify-content: center;
  }
}

.autocomplete-field {
  position: relative;
}

.autocomplete-field input {
  width: 100%;
  box-sizing: border-box;
  padding: 11px 12px;
  border: 1px solid #d0d0d0;
  border-radius: 8px;
  font-size: 14px;
  font-family: inherit;
  color: #232323;
  background: #f4f6f8;
  line-height: 1.5;
}

.autocomplete-suggestions {
  position: absolute;
  z-index: 10;
  width: 100%;
  max-height: 220px;
  margin: 4px 0 0;
  padding: 0;
  list-style: none;
  overflow-y: auto;
  border: 1px solid #d7dee3;
  border-radius: 8px;
  background: #ffffff;
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.08);
}

.autocomplete-suggestion {
  padding: 10px 12px;
  cursor: pointer;
  font-size: 13px;
  color: #1f2937;
}

.autocomplete-suggestion:hover {
  background: #f3f6f8;
}

.autocomplete-suggestion.highlighted {
  background: #e8f1f5;
}

.autocomplete-empty {
  padding: 10px 12px;
  color: #6b7280;
  font-size: 13px;
}
</style>
<!--
refactor/simplify all the files
unit test all the pages
DEL/Backspace test everywhere

lag usability check for opening request editor with large requests, and expanding request by clicking on the header
table edit performance for large requests
-->

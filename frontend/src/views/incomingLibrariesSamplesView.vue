<template>
  <div class="parent-container">
    <!-- Loading overlay -->
    <div v-if="loading || fakeLoading" class="loading-overlay">
      <div v-if="!fakeLoading" class="spinner"></div>
      <p v-if="!fakeLoading">
        Loading <span style="font-weight: bold">Incoming Libraries</span> and
        <span style="font-weight: bold">Samples</span>...
      </p>
    </div>

    <!-- Header -->
    <div class="header">
      <div class="header-logo" style="display: inline; margin-right: 10px">
        <svg
          style="display: block"
          fill="none"
          width="42px"
          height="42px"
          version="1.1"
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
        >
          <g>
            <path
              opacity="0.3"
              d="M3 12C3 4.5885 4.5885 3 12 3C19.4115 3 21 4.5885 21 12C21 19.4115 19.4115 21 12 21C4.5885 21 3 19.4115 3 12Z"
              fill="#333333"
            />
            <path
              d="M3 12C3 4.5885 4.5885 3 12 3C19.4115 3 21 4.5885 21 12C21 19.4115 19.4115 21 12 21C4.5885 21 3 19.4115 3 12Z"
              stroke="white"
              stroke-width="1.5"
            />
            <path
              d="M14.5 14.5L9 9"
              stroke="white"
              stroke-width="1.5"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
            <path
              d="M10 15H14.6717C14.853 15 15 14.853 15 14.6716V10"
              stroke="white"
              stroke-width="1.5"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </g>
        </svg>
      </div>
      <div class="header-title" style="display: inline">
        Incoming Libraries and Samples
      </div>

      <!-- Sticky right section for search, advanced filters, and select columns -->
      <div class="sticky-actions">
        <div class="search-bar">
          <input
            ref="searchInput"
            v-model="searchQuery"
            type="text"
            placeholder="Search"
          />
          <font-awesome-icon
            icon="fa-solid fa-magnifying-glass"
            style="color: darkgrey"
          />
        </div>
        <div class="button-popup-wrapper">
          <button
            class="header-button"
            id="toggleAdvancedFiltersButton"
            @click="toggleAdvancedFilters"
          >
            <font-awesome-icon icon="fa-solid fa-filter" style="color: white" />
            <span> Advanced Filters </span>
          </button>
          <div
            id="advancedFiltersPopup"
            v-if="showAdvancedFilters"
            class="button-popup-container"
            style="width: 250px; left: -50px"
          >
            <label>
              <div
                style="
                  display: flex;
                  justify-content: center;
                  text-align: center;
                "
              >
                <input type="checkbox" v-model="filters.showLibraries" />
              </div>
              <div><span style="font-weight: bold">Show</span> Libraries</div>
            </label>
            <label>
              <div
                style="
                  display: flex;
                  justify-content: center;
                  text-align: center;
                "
              >
                <input type="checkbox" v-model="filters.showSamples" />
              </div>
              <div><span style="font-weight: bold">Show</span> Samples</div>
            </label>
            <label>
              <div
                style="
                  display: flex;
                  justify-content: center;
                  text-align: center;
                "
              >
                <input type="checkbox" v-model="filters.onlySamplesSubmitted" />
              </div>
              <div>
                <span style="font-weight: bold">Filter Requests</span> with
                Samples Submitted
              </div>
            </label>
            <label>
              <div
                style="
                  display: flex;
                  justify-content: center;
                  text-align: center;
                "
              >
                <input type="checkbox" v-model="filters.onlyGmo" />
              </div>
              <div>
                <span style="font-weight: bold">Filter Requests</span> with GMO
                ➜ Yes
              </div>
            </label>
          </div>
        </div>
        <div class="button-popup-wrapper">
          <button
            class="header-button"
            id="toggleSelectColumnsButton"
            @click="toggleSelectColumns"
          >
            <font-awesome-icon
              icon="fa-solid fa-columns"
              style="color: white"
            />
            <span> Select Columns </span>
          </button>
          <div
            id="selectColumnsPopup"
            v-if="showSelectColumns"
            class="button-popup-container"
            style="
              left: -50px;
              width: 250px;
              max-height: 473px;
              display: flex;
              flex-direction: column;
              padding: 10px 10px 5px 10px;
            "
          >
            <ul
              style="
                padding: 5px 7px 7px;
                margin: 0;
                flex-grow: 1;
                overflow-y: auto;
              "
            >
              <li
                v-for="(column, index) in columnsList"
                :key="index"
                style="list-style: none"
              >
                <template
                  v-if="
                    column.field !== 'selected' ||
                    (column.field === 'selected' && column.visible == false)
                  "
                >
                  <label
                    :style="{
                      backgroundColor: column.columns ? '#33333320' : 'white',
                      cursor: column.columns ? 'default' : 'pointer'
                    }"
                  >
                    <input
                      v-if="!column.columns"
                      type="checkbox"
                      v-model="column.visible"
                      @change="toggleColumnVisibility(column)"
                    />
                    <font-awesome-icon
                      v-if="column.columns"
                      icon="fa-solid fa-caret-down"
                      style="
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        border: 2px solid black;
                        height: 14px;
                        width: 14px;
                        border-radius: 4px;
                        text-align: center;
                        background-color: orange;
                        color: white;
                      "
                    />
                    <span>{{ column.title }}</span>
                  </label>
                  <ul v-if="column.columns" style="padding-left: 0px">
                    <li
                      v-for="(subColumn, subIndex) in column.columns"
                      :key="subIndex"
                      style="list-style: none"
                    >
                      <label>
                        <input
                          type="checkbox"
                          style="width: 20px !important"
                          :checked="subColumn.visible"
                          @change="toggleColumnVisibility(subColumn)"
                        />
                        <span style="width: 100%">{{ subColumn.title }}</span>
                      </label>
                    </li>
                  </ul>
                </template>
              </li>
            </ul>
            <div
              style="
                padding-top: 8px;
                border-top: 1px solid #eee;
                display: flex;
                flex-direction: column;
              "
            >
              <button @click="resetColumnVisibility" class="reset-button">
                Reset Visibility Settings
              </button>
              <button
                style="margin-bottom: 5px"
                @click="resetColumnWidths"
                class="reset-button"
              >
                Reset Width Settings
              </button>
            </div>
          </div>
        </div>
        <div class="button-popup-wrapper">
          <button class="header-button" @click="toggleGroups">
            <font-awesome-icon
              icon="fa-solid fa-layer-group"
              style="color: white"
            />
            <span> Toggle Views </span>
          </button>
        </div>
        <button
          class="header-button"
          id="openExportPopupButton"
          @click="handleExportClick"
        >
          <font-awesome-icon
            icon="fa-solid fa-file-excel"
            style="color: white"
          />
          <span> Export to Excel </span>
        </button>
      </div>
    </div>

    <!-- Main content section with table -->
    <div class="table-container">
      <TabulatorTable
        v-if="!loading"
        ref="tabulatorTableRef"
        :rowData="librariesSamplesList"
        :columnDefs="columnsList"
        groupBy="request_name"
        :groupSort="{ field: 'request_name', order: 'desc' }"
        :groupStartOpen="true"
        :tableOptions="{
          ...tableOptions,
          onBatchCellValueChanged,
          fakeLoadingStart,
          fakeLoadingStop,
          handleColumnResized,
          handleColumnVisibilityChanged
        }"
      />
    </div>

    <!-- Popup window -->
    <div v-if="showPopupWindow" class="popup-overlay">
      <div
        class="popup-container confirmation-popup"
        :style="{
          height: popupContents.popupHeight + 'px',
          width: popupContents.popupWidth + 'px'
        }"
      >
        <div class="popup-header">
          <svg
            style="display: block"
            fill="none"
            width="42px"
            height="42px"
            version="1.1"
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
          >
            <g>
              <path
                opacity="0.3"
                d="M3 9.22843V14.7716C3 15.302 3.21071 15.8107 3.58579 16.1858L7.81421 20.4142C8.18929 20.7893 8.69799 21 9.22843 21H14.7716C15.302 21 15.8107 20.7893 16.1858 20.4142L20.4142 16.1858C20.7893 15.8107 21 15.302 21 14.7716V9.22843C21 8.69799 20.7893 8.18929 20.4142 7.81421L16.1858 3.58579C15.8107 3.21071 15.302 3 14.7716 3H9.22843C8.69799 3 8.18929 3.21071 7.81421 3.58579L3.58579 7.81421C3.21071 8.18929 3 8.69799 3 9.22843Z"
                fill="#323232"
              />
              <path
                d="M3 9.22843V14.7716C3 15.302 3.21071 15.8107 3.58579 16.1858L7.81421 20.4142C8.18929 20.7893 8.69799 21 9.22843 21H14.7716C15.302 21 15.8107 20.7893 16.1858 20.4142L20.4142 16.1858C20.7893 15.8107 21 15.302 21 14.7716V9.22843C21 8.69799 20.7893 8.18929 20.4142 7.81421L16.1858 3.58579C15.8107 3.21071 15.302 3 14.7716 3H9.22843C8.69799 3 8.18929 3.21071 7.81421 3.58579L3.58579 7.81421C3.21071 8.18929 3 8.69799 3 9.22843Z"
                stroke="white"
                stroke-width="1.5"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
              <path
                d="M12 8V13"
                stroke="white"
                stroke-width="1.5"
                stroke-linecap="round"
              />
              <path
                d="M12 16V15.9888"
                stroke="white"
                stroke-width="1.5"
                stroke-linecap="round"
              />
            </g>
          </svg>
          <span class="popup-title">{{ popupContents.popupTitle }}</span>
          <button class="popup-close-button" @click="showPopupWindow = false">
            &times;
          </button>
        </div>
        <div class="popup-body">
          <div v-html="popupContents.popupDescription"></div>
          <div
            v-if="popupContents.popupList && popupContents.popupList.length > 0"
            class="popup-scrollable-content"
          >
            <ol style="padding-left: 25px">
              <li v-for="item in popupContents.popupList" :key="item">
                <span style="font-weight: bold">{{ item.barcode }}</span>
                <span>{{ " - " + item.name }}</span>
              </li>
            </ol>
          </div>
        </div>
        <div class="popup-footer">
          <button class="popup-button yes-button" @click="popupContents.onYes">
            Yes
          </button>
          <button class="popup-button" @click="popupContents.onNo">No</button>
        </div>
      </div>
    </div>

    <!-- Popup for Export Options -->
    <div
      v-if="showExportPopup"
      class="popup-overlay"
      @dragover.prevent="handleDragOver"
      @drop="handleDrop"
      @dragenter="handleDragEnter"
      @dragleave="handleDragLeave"
      :class="{ 'drag-over': isDragOver }"
    >
      <div class="drag-drop-indicator">
        <div
          style="
            display: flex;
            justify-content: center;
            align-items: center;
            height: 200px;
          "
        >
          <p>
            Drop <span style="font-weight: bold">XLSX file</span> here to upload
            as <span style="font-weight: bold">template</span>
          </p>
        </div>
      </div>
      <div
        v-if="!isDragOver"
        class="popup-container export-popup"
        :style="{ width: '670px', height: '500px' }"
      >
        <div class="popup-header">
          <span class="popup-title">Export Options</span>
          <span
            class="popup-info-button"
            @mouseover="showExportHelpTooltip = true"
            @mouseleave="showExportHelpTooltip = false"
          >
            ?
            <div v-if="showExportHelpTooltip" class="tooltip-box">
              <span style="font-weight: bold">INSTRUCTIONS:</span>
              <ol>
                <li>
                  To create custom templates, export the original sheet named
                  <span style="font-weight: bold">'Parkour'</span> by selecting
                  the
                  <span style="font-weight: bold"
                    >'Export without any additional sheets'</span
                  >
                  option.
                </li>
                <li>
                  Add new custom sheets to this exported file, which will serve
                  as templates.
                </li>
                <li>
                  Upload the modified file, containing both the original
                  <span style="font-weight: bold">'Parkour'</span> sheet and
                  newly added
                  <span style="font-weight: bold">custom sheets</span>. After
                  uploading the file will appear in the list.
                </li>
                <li>
                  The template is now ready! When you select this modified file
                  from the list, the system will replace the
                  <span style="font-weight: bold">'Parkour'</span> sheet with
                  updated data while keeping all additional sheets intact.
                </li>
              </ol>
            </div>
          </span>
          <button class="popup-close-button" @click="showExportPopup = false">
            &times;
          </button>
        </div>
        <div class="popup-body">
          <div class="export-section">
            <div style="font-weight: bold; margin-bottom: 8px">
              Export Options:
            </div>
            <div class="export-selection-radio-option">
              <input
                type="radio"
                id="export-selected"
                value="selected"
                v-model="exportSelection"
                :disabled="!hasSelectedRows"
              />
              <label
                for="export-selected"
                :class="{ disabled: !hasSelectedRows }"
              >
                Export selected libraries & samples
              </label>
            </div>
            <div class="export-selection-radio-option">
              <input
                type="radio"
                id="export-all"
                value="all"
                v-model="exportSelection"
              />
              <label for="export-all"> Export all libraries & samples </label>
            </div>
          </div>
          <div class="export-section" style="height: 100%">
            <div style="font-weight: bold; margin-bottom: 8px">
              Upload additional excel sheet templates to append:
            </div>
            <div class="file-list-section">
              <div class="file-item">
                <div class="file-info">
                  <svg
                    style="display: block"
                    fill="none"
                    width="24px"
                    height="24px"
                    version="1.1"
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 24 24"
                  >
                    <g>
                      <path
                        opacity="0.1"
                        d="M17.8284 6.82843C18.4065 7.40649 18.6955 7.69552 18.8478 8.06306C19 8.4306 19 8.83935 19 9.65685L19 17C19 18.8856 19 19.8284 18.4142 20.4142C17.8284 21 16.8856 21 15 21H9C7.11438 21 6.17157 21 5.58579 20.4142C5 19.8284 5 18.8856 5 17L5 7C5 5.11438 5 4.17157 5.58579 3.58579C6.17157 3 7.11438 3 9 3H12.3431C13.1606 3 13.5694 3 13.9369 3.15224C14.3045 3.30448 14.5935 3.59351 15.1716 4.17157L17.8284 6.82843Z"
                        fill="#323232"
                      />
                      <path
                        d="M17.8284 6.82843C18.4065 7.40649 18.6955 7.69552 18.8478 8.06306C19 8.4306 19 8.83935 19 9.65685L19 17C19 18.8856 19 19.8284 18.4142 20.4142C17.8284 21 16.8856 21 15 21H9C7.11438 21 6.17157 21 5.58579 20.4142C5 19.8284 5 18.8856 5 17L5 7C5 5.11438 5 4.17157 5.58579 3.58579C6.17157 3 7.11438 3 9 3H12.3431C13.1606 3 13.5694 3 13.9369 3.15224C14.3045 3.30448 14.5935 3.59351 15.1716 4.17157L17.8284 6.82843Z"
                        stroke="#323232"
                        stroke-width="2"
                        stroke-linejoin="round"
                      />
                    </g>
                  </svg>
                  <span>Export without any additional sheets</span>
                </div>
                <div class="file-actions">
                  <div
                    class="file-actions-radio-button"
                    style="border: none; margin-right: 5px"
                  >
                    <input
                      type="radio"
                      title="Select"
                      id="without-file"
                      value="without-file"
                      v-model="selectedFile"
                    />
                  </div>
                </div>
              </div>
              <div
                v-for="(
                  file, index
                ) in fetchedIncomingLibrariesAndSamplesTemplates"
                :key="index"
                class="file-item"
              >
                <div class="file-info">
                  <svg
                    style="display: block"
                    fill="none"
                    width="24px"
                    height="24px"
                    version="1.1"
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 24 24"
                  >
                    <g>
                      <path
                        opacity="0.1"
                        d="M17.8284 6.82843C18.4065 7.40649 18.6955 7.69552 18.8478 8.06306C19 8.4306 19 8.83935 19 9.65685L19 17C19 18.8856 19 19.8284 18.4142 20.4142C17.8284 21 16.8856 21 15 21H9C7.11438 21 6.17157 21 5.58579 20.4142C5 19.8284 5 18.8856 5 17L5 7C5 5.11438 5 4.17157 5.58579 3.58579C6.17157 3 7.11438 3 9 3H12.3431C13.1606 3 13.5694 3 13.9369 3.15224C14.3045 3.30448 14.5935 3.59351 15.1716 4.17157L17.8284 6.82843Z"
                        fill="#323232"
                      />
                      <path
                        d="M17.8284 6.82843C18.4065 7.40649 18.6955 7.69552 18.8478 8.06306C19 8.4306 19 8.83935 19 9.65685L19 17C19 18.8856 19 19.8284 18.4142 20.4142C17.8284 21 16.8856 21 15 21H9C7.11438 21 6.17157 21 5.58579 20.4142C5 19.8284 5 18.8856 5 17L5 7C5 5.11438 5 4.17157 5.58579 3.58579C6.17157 3 7.11438 3 9 3H12.3431C13.1606 3 13.5694 3 13.9369 3.15224C14.3045 3.30448 14.5935 3.59351 15.1716 4.17157L17.8284 6.82843Z"
                        stroke="#323232"
                        stroke-width="2"
                        stroke-linejoin="round"
                      />
                      <path
                        d="M9 6L11 6"
                        stroke="#323232"
                        stroke-width="2"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                      />
                      <path
                        d="M10 9L12 9"
                        stroke="#323232"
                        stroke-width="2"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                      />
                      <path
                        d="M9 12L11 12"
                        stroke="#323232"
                        stroke-width="2"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                      />
                      <path
                        d="M10 15L12 15"
                        stroke="#323232"
                        stroke-width="2"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                      />
                    </g>
                  </svg>
                  <span>{{ file.name }}</span>
                </div>
                <div class="file-actions">
                  <button
                    @click="downloadExportTemplate(file)"
                    class="download-button"
                    title="Download Original File"
                  >
                    <svg
                      style="display: block"
                      fill="none"
                      width="24px"
                      height="24px"
                      version="1.1"
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 24 24"
                    >
                      <g>
                        <path
                          opacity="0.1"
                          d="M17.8284 6.82843C18.4065 7.40649 18.6955 7.69552 18.8478 8.06306C19 8.4306 19 8.83935 19 9.65685L19 17C19 18.8856 19 19.8284 18.4142 20.4142C17.8284 21 16.8856 21 15 21H9C7.11438 21 6.17157 21 5.58579 20.4142C5 19.8284 5 18.8856 5 17L5 7C5 5.11438 5 4.17157 5.58579 3.58579C6.17157 3 7.11438 3 9 3H12.3431C13.1606 3 13.5694 3 13.9369 3.15224C14.3045 3.30448 14.5935 3.59351 15.1716 4.17157L17.8284 6.82843Z"
                          fill="#323232"
                        />
                        <path
                          d="M17.8284 6.82843C18.4065 7.40649 18.6955 7.69552 18.8478 8.06306C19 8.4306 19 8.83935 19 9.65685L19 17C19 18.8856 19 19.8284 18.4142 20.4142C17.8284 21 16.8856 21 15 21H9C7.11438 21 6.17157 21 5.58579 20.4142C5 19.8284 5 18.8856 5 17L5 7C5 5.11438 5 4.17157 5.58579 3.58579C6.17157 3 7.11438 3 9 3H12.3431C13.1606 3 13.5694 3 13.9369 3.15224C14.3045 3.30448 14.5935 3.59351 15.1716 4.17157L17.8284 6.82843Z"
                          stroke="#323232"
                          stroke-width="2"
                          stroke-linejoin="round"
                        />
                        <path
                          d="M12 16L12 11"
                          stroke="#323232"
                          stroke-width="2"
                          stroke-linecap="round"
                          stroke-linejoin="round"
                        />
                        <path
                          d="M9.5 14L11.5 16V16C11.7761 16.2761 12.2239 16.2761 12.5 16V16L14.5 14"
                          stroke="#323232"
                          stroke-width="2"
                          stroke-linecap="round"
                          stroke-linejoin="round"
                        />
                      </g>
                    </svg>
                  </button>
                  <button
                    @click="removeExportTemplate(index)"
                    class="remove-button"
                    title="Remove File"
                  >
                    <svg
                      style="display: block"
                      fill="none"
                      width="24px"
                      height="24px"
                      version="1.1"
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 24 24"
                    >
                      <g>
                        <path
                          opacity="0.1"
                          d="M5.02322 5.37683C5 5.82377 5 6.35711 5 7.00006V17.0001C5 18.8857 5 19.8285 5.58579 20.4143C6.17157 21.0001 7.11438 21.0001 9 21.0001H15C16.8856 21.0001 17.8284 21.0001 18.4142 20.4143C18.6935 20.135 18.8396 19.7746 18.9161 19.2697L5.02322 5.37683Z"
                          fill="#323232"
                        />
                        <path
                          d="M8 3H12.3431C13.1606 3 13.5694 3 13.9369 3.15224C14.3045 3.30448 14.5935 3.59351 15.1716 4.17157L17.8284 6.82843C18.4065 7.40649 18.6955 7.69552 18.8478 8.06306C19 8.4306 19 8.83935 19 9.65685L19 14"
                          stroke="#323232"
                          stroke-width="2"
                          stroke-linecap="round"
                          stroke-linejoin="round"
                        />
                        <path
                          d="M5 5V17C5 18.8856 5 19.8284 5.58579 20.4142C6.17157 21 7.11438 21 9 21H17C17 21 17 21 17 21C18.1046 21 19 20.1046 19 19C19 19 19 19 19 19V19"
                          stroke="#323232"
                          stroke-width="2"
                          stroke-linejoin="round"
                        />
                        <path
                          d="M3 3L21 21"
                          stroke="#323232"
                          stroke-width="2"
                          stroke-linecap="round"
                          stroke-linejoin="round"
                        />
                      </g>
                    </svg>
                  </button>
                  <div class="file-actions-radio-button">
                    <input
                      type="radio"
                      title="Select File"
                      :id="'file-radio-' + index"
                      :value="file"
                      v-model="selectedFile"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="popup-footer">
          <div class="file-upload-section">
            <label
              for="file-upload"
              class="file-upload-label"
              title="Upload additional sheet to append to the exported sheet."
            >
              <svg
                style="display: block; margin-right: 4px"
                fill="none"
                width="24px"
                height="24px"
                version="1.1"
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
              >
                <g>
                  <path
                    opacity="0.1"
                    d="M17.8284 6.82843C18.4065 7.40649 18.6955 7.69552 18.8478 8.06306C19 8.4306 19 8.83935 19 9.65685L19 17C19 18.8856 19 19.8284 18.4142 20.4142C17.8284 21 16.8856 21 15 21H9C7.11438 21 6.17157 21 5.58579 20.4142C5 19.8284 5 18.8856 5 17L5 7C5 5.11438 5 4.17157 5.58579 3.58579C6.17157 3 7.11438 3 9 3H12.3431C13.1606 3 13.5694 3 13.9369 3.15224C14.3045 3.30448 14.5935 3.59351 15.1716 4.17157L17.8284 6.82843Z"
                    fill="#323232"
                  />
                  <path
                    d="M17.8284 6.82843C18.4065 7.40649 18.6955 7.69552 18.8478 8.06306C19 8.4306 19 8.83935 19 9.65685L19 17C19 18.8856 19 19.8284 18.4142 20.4142C17.8284 21 16.8856 21 15 21H9C7.11438 21 6.17157 21 5.58579 20.4142C5 19.8284 5 18.8856 5 17L5 7C5 5.11438 5 4.17157 5.58579 3.58579C6.17157 3 7.11438 3 9 3H12.3431C13.1606 3 13.5694 3 13.9369 3.15224C14.3045 3.30448 14.5935 3.59351 15.1716 4.17157L17.8284 6.82843Z"
                    stroke="#323232"
                    stroke-width="2"
                    stroke-linejoin="round"
                  />
                  <path
                    d="M12 11L12 16"
                    stroke="#323232"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  />
                  <path
                    d="M14.5 13.5L9.5 13.5"
                    stroke="#323232"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  />
                </g>
              </svg>
              <span>Upload</span>
            </label>
            <input
              id="file-upload"
              type="file"
              accept=".xlsx"
              @change="uploadExportTemplate"
              style="display: none"
            />
          </div>
          <button class="popup-button yes-button" @click="handleExport">
            OK
          </button>
          <button
            class="popup-button"
            @click="
              showExportPopup = false;
              selectedFile = 'without-file';
            "
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="jsx">
import TabulatorTable from "../components/TabulatorTable.vue";
import { saveAs } from "file-saver";
import {
  showNotification,
  handleError,
  createAxiosObject,
  urlStringStartsWith,
  createExcelExportBlob
} from "../utilities/utilityFunctions";
import {
  incomingLibrariesSamplesGroupHeader,
  incomingLibrariesSamplesColumnDefs,
  incomingLibrariesSamplesExportColumns
} from "../constants/incomingLibrariesSamplesConsts";
const axiosRef = createAxiosObject();
const urlStringStart = urlStringStartsWith();

export default {
  name: "IncomingLibrariesAndSamples",
  components: {
    TabulatorTable
  },
  data() {
    return {
      tabulatorInstance: null,
      loading: true,
      fakeLoading: false,
      isDragOver: false,
      librariesSamplesList: [],
      columnsList: [],
      showExportPopup: false,
      showPopupWindow: false,
      showExportHelpTooltip: false,
      fetchedIncomingLibrariesAndSamplesTemplates: [],
      selectedFile: "without-file",
      exportSelection: "selected",
      hasSelectedRows: false,
      popupContents: {
        popupTitle: "Are you sure?",
        popupDescription: "",
        popupList: [],
        onYes: null,
        onNo: null,
        popupHeight: 220,
        popupWidth: 600
      },
      tableOptions: {
        index: "barcode",
        placeholder: "No Libraries and Samples to show.",
        initialSort: [
          { column: "barcode", dir: "asc" },
          { column: "name", dir: "desc" }
        ],
        groupHeader: (value, count, data) => {
          const samplesSubmitted = data.some(
            (item) => item.samples_submitted === true
          );
          const gmo = data.some((item) => item.gmo === true);
          let totalDepth = data.reduce(
            (sum, row) => sum + (row.sequencing_depth || 0),
            0
          );
          totalDepth = Number(totalDepth.toFixed(1));
          let totalReadLength = data.reduce((sum, row) => {
            const readLength = Number(row.read_length);
            return sum + (isNaN(readLength) ? 0 : readLength);
          }, 0);
          totalReadLength = Number(totalReadLength.toFixed(1));
          const biosafetyLevel =
            [...new Set(data.map((item) => item.biosafety_level))]
              .map((level) => level && level.toUpperCase())
              .join(" and ") || "No BSL";
          return incomingLibrariesSamplesGroupHeader(
            value,
            count,
            samplesSubmitted,
            gmo,
            totalDepth,
            totalReadLength,
            biosafetyLevel
          );
        }
      },
      searchQuery: "",
      filters: {
        showLibraries: true,
        showSamples: true,
        onlySamplesSubmitted: false,
        onlyGmo: false
      },
      showAdvancedFilters: false,
      showSelectColumns: false
    };
  },
  mounted() {
    this.getLibrariesSamples();
    this.setColumns();
    this.fetchExportTemplates();

    document.addEventListener("click", this.handleOutsideClick);
    document.addEventListener("keydown", this.handleKeyDown);
    window.handleGroupButtonClick = this.handleGroupButtonClick.bind(this);
  },
  updated() {
    this.tabulatorInstance = this.$refs.tabulatorTableRef;
  },
  beforeDestroy() {
    document.removeEventListener("click", this.handleOutsideClick);
    document.removeEventListener("keydown", this.handleKeyDown);
  },
  watch: {
    searchQuery(newValue, oldValue) {
      if (newValue !== oldValue) {
        this.tabulatorInstance.filterTableData(
          "search_incoming_libraries_and_samples",
          newValue === null ? "" : newValue
        );
      }
    },
    "filters.showLibraries"(newValue, oldValue) {
      if (newValue !== oldValue) {
        this.tabulatorInstance.filterTableData("showLibraries", newValue);
      }
    },
    "filters.showSamples"(newValue, oldValue) {
      if (newValue !== oldValue) {
        this.tabulatorInstance.filterTableData("showSamples", newValue);
      }
    },
    "filters.onlySamplesSubmitted"(newValue, oldValue) {
      if (newValue !== oldValue) {
        this.tabulatorInstance.filterTableData(
          "onlySamplesSubmitted",
          newValue
        );
      }
    },
    "filters.onlyGmo"(newValue, oldValue) {
      if (newValue !== oldValue) {
        this.tabulatorInstance.filterTableData("onlyGmo", newValue);
      }
    },
    showPopupWindow(newVal) {
      if (newVal) {
        this.$nextTick(() => {
          const yesButton = document.querySelector(".popup-button.yes-button");
          yesButton.focus();
        });
      } else {
        document.getElementsByClassName("tabulator-cell")[1]?.click();
      }
    }
  },
  methods: {
    async getLibrariesSamples() {
      this.loading = true;
      try {
        let response = await axiosRef.get(
          urlStringStart + "/api/incoming_libraries/"
        );
        let fetchedRows = response.data.map((element) => ({
          pk: element.pk || "",
          record_type: element.record_type || "",
          request_id: element.request || "",
          request_name: element.request_name || "",
          name: element.name || "",
          type: element.barcode[2] || "",
          barcode: element.barcode || "",
          samples_submitted: element.samples_submitted || "",
          nucleic_acid_type_name: element.nucleic_acid_type_name || "",
          library_protocol_name: element.library_protocol_name || "",
          biosafety_level: element.biosafety_level || "",
          percent_total:
            element.percent_total === 0 ? 0 : element.percent_total || "",
          measuring_unit: element.measuring_unit || "",
          measured_value:
            element.measured_value === 0 ? 0 : element.measured_value || "",
          input: (({ measured_value: mv, measuring_unit: mu }) => {
            const isEmpty = (v) => v === null || v === undefined || v === "";
            if (mv === -1 && mu === "Unknown") return "Unknown";
            if (isEmpty(mv) && isEmpty(mu)) return "";
            const val = mv === 0 ? 0 : mv || "";
            const unit = mu || "";
            if (isEmpty(mv) && !isEmpty(mu)) {
              return unit;
            }
            if (unit !== "") return `${val} ${unit}`;
            return `${val}`;
          })(element),
          volume: element.volume === 0 ? 0 : element.volume || "",
          mean_fragment_size:
            element.mean_fragment_size === 0
              ? 0
              : element.mean_fragment_size || "",
          comments: element.comments || "",
          measuring_unit_facility: element.measuring_unit_facility || "",
          measured_value_facility:
            element.measured_value_facility === 0
              ? 0
              : element.measured_value_facility || "",
          sample_volume_facility:
            element.sample_volume_facility === 0
              ? 0
              : element.sample_volume_facility || "",
          size_distribution_facility:
            element.size_distribution_facility === 0
              ? 0
              : element.size_distribution_facility || "",
          sequencing_depth:
            element.sequencing_depth === 0 ? 0 : element.sequencing_depth || "",
          read_length:
            element.read_length === 0 ? 0 : element.read_length || "",
          rna_quality_facility:
            element.rna_quality_facility === 0
              ? 0
              : element.rna_quality_facility || "",
          gmo: element.gmo === null ? "" : element.gmo,
          gmo_facility:
            element.gmo_facility === null
              ? ""
              : element.gmo_facility === true
                ? "Risk Assessment Done"
                : "Not Needed",
          comments_facility: element.comments_facility || ""
        }));
        this.librariesSamplesList = fetchedRows;
      } catch (error) {
        handleError(error);
      } finally {
        this.loading = false;
      }
    },
    setColumns() {
      const storedVisibility = JSON.parse(
        localStorage.getItem("incomingLibrariesAndSamplesColumnVisibility") ||
          "{}"
      );
      const storedWidths = JSON.parse(
        localStorage.getItem("incomingLibrariesAndSamplesColumnWidths") || "{}"
      );

      const applySettings = (columns) => {
        return columns.map((column) => {
          if (column.field) {
            if (storedWidths[column.field]) {
              column.width = storedWidths[column.field];
              if (column.minWidth && column.width < column.minWidth) {
                column.width = column.minWidth;
              }
            }
            column.visible =
              storedVisibility[column.field] ?? column.visible ?? true;
          }
          if (column.columns) {
            column.columns = applySettings(column.columns);
          }
          return column;
        });
      };

      let columnDefs = incomingLibrariesSamplesColumnDefs(
        () => this.tabulatorInstance
      );

      this.columnsList = applySettings(columnDefs);
    },
    handleOutsideClick(event) {
      const advancedFiltersPopup = this.$el.querySelector(
        "#advancedFiltersPopup"
      );
      const advancedFiltersButton = this.$el.querySelector(
        "#toggleAdvancedFiltersButton"
      );
      const selectColumnsPopup = this.$el.querySelector("#selectColumnsPopup");
      const selectColumnsButton = this.$el.querySelector(
        "#toggleSelectColumnsButton"
      );
      const exportPopup = this.$el.querySelector(".export-popup");
      const exportButton = this.$el.querySelector("#openExportPopupButton");
      const confirmationPopup = this.$el.querySelector(".confirmation-popup");
      const clickOnExportButton =
        exportButton &&
        (exportButton === event.target || exportButton.contains(event.target));

      if (
        this.showAdvancedFilters &&
        advancedFiltersPopup &&
        !advancedFiltersPopup.contains(event.target) &&
        advancedFiltersButton !== event.target &&
        !advancedFiltersButton.contains(event.target)
      ) {
        this.showAdvancedFilters = false;
      }

      if (
        this.showSelectColumns &&
        selectColumnsPopup &&
        !selectColumnsPopup.contains(event.target) &&
        selectColumnsButton !== event.target &&
        !selectColumnsButton.contains(event.target)
      ) {
        this.showSelectColumns = false;
      }

      if (
        this.showExportPopup &&
        exportPopup &&
        !exportPopup.contains(event.target) &&
        !clickOnExportButton
      ) {
        this.showExportPopup = false;
      }

      if (
        this.showPopupWindow &&
        confirmationPopup &&
        !confirmationPopup.contains(event.target)
      ) {
        this.showPopupWindow = false;
      }
    },
    handleKeyDown(event) {
      const isEscape = event.key === "Escape";
      if (isEscape && (this.showPopupWindow || this.showExportPopup)) {
        this.showPopupWindow = false;
        this.showExportPopup = false;
        return;
      }
      if (isEscape && this.showAdvancedFilters) {
        this.showAdvancedFilters = false;
        return;
      }
      if (isEscape && this.showSelectColumns) {
        this.showSelectColumns = false;
        return;
      }
    },
    fakeLoadingStart() {
      this.fakeLoading = true;
    },
    fakeLoadingStop() {
      setTimeout(() => {
        this.fakeLoading = false;
      }, 300);
    },
    toggleGroups(goToInitial) {
      this.fakeLoadingStart();
      this.tabulatorInstance.toggleGroups(goToInitial);
      this.fakeLoadingStop();
    },
    toggleAdvancedFilters() {
      this.showAdvancedFilters = !this.showAdvancedFilters;
      if (this.showAdvancedFilters) {
        this.showSelectColumns = false;
      }
    },
    toggleSelectColumns() {
      this.showSelectColumns = !this.showSelectColumns;
      if (this.showSelectColumns) {
        this.showAdvancedFilters = false;
      }
    },
    handleColumnResized(column) {
      const field = column.getField();
      const width = column.getWidth();
      const storedWidths = JSON.parse(
        localStorage.getItem("incomingLibrariesAndSamplesColumnWidths") || "{}"
      );
      const newWidths = {
        ...storedWidths,
        [field]: width
      };
      localStorage.setItem(
        "incomingLibrariesAndSamplesColumnWidths",
        JSON.stringify(newWidths)
      );
      this.fakeLoadingStart();
      setTimeout(() => this.fakeLoadingStop(), 50);
    },
    handleColumnVisibilityChanged(field, visible) {
      if (field !== "from_user" && field !== "from_facility") {
        const storedVisibility = JSON.parse(
          localStorage.getItem("incomingLibrariesAndSamplesColumnVisibility") ||
            "{}"
        );

        const newVisibility = {
          ...storedVisibility,
          [field]: visible
        };

        localStorage.setItem(
          "incomingLibrariesAndSamplesColumnVisibility",
          JSON.stringify(newVisibility)
        );

        this.fakeLoadingStart();
        setTimeout(() => this.fakeLoadingStop(), 50);
      }
    },
    toggleColumnVisibility(column) {
      if (this.tabulatorInstance) {
        this.tabulatorInstance.getTable().toggleColumn(column.field);
      }
    },
    resetColumnWidths() {
      localStorage.removeItem("incomingLibrariesAndSamplesColumnWidths");
      this.setColumns();
      this.fakeLoadingStart();
      setTimeout(() => this.fakeLoadingStop(), 300);
    },
    resetColumnVisibility() {
      localStorage.removeItem("incomingLibrariesAndSamplesColumnVisibility");
      this.setColumns();
      this.fakeLoadingStart();
      setTimeout(() => this.fakeLoadingStop(), 300);
    },
    handleGroupButtonClick(event, groupValue, action) {
      event.stopPropagation();

      const group = this.tabulatorInstance
        .getTable()
        .getGroups()
        .find((g) => g.getKey() === groupValue);
      const groupRows = group.getRows();
      const groupElement = group.getElement();
      const selectedRows = groupRows.filter((row) => row.getData().selected);
      const type = selectedRows[0] && selectedRows[0].getData().type;
      const requestId = groupRows[0].getData().request_id;
      const requestName = group._group.key;
      const selectedNamesList = selectedRows.map((item) => {
        return { barcode: item.getData().barcode, name: item.getData().name };
      });
      const popupHeight = Math.min(420, 260 + selectedNamesList.length * 22);

      switch (action) {
        case "selectAll":
          groupRows.forEach((row) => {
            row.getData().selected = true;
            row.update({});
            const rowElement = row.getElement();
            const checkbox = rowElement.querySelector('input[type="checkbox"]');
            if (checkbox) {
              checkbox.checked = true;
            }
          });
          if (!group._group.visible) groupElement.click();
          break;

        case "deselectAll":
          groupRows.forEach((row) => {
            row.getData().selected = false;
            row.update({});
            const rowElement = row.getElement();
            const checkbox = rowElement.querySelector('input[type="checkbox"]');
            if (checkbox) {
              checkbox.checked = false;
            }
          });
          if (!group._group.visible) groupElement.click();
          break;

        case "samplesSubmitted":
          let newSamplesSubmittedState = groupRows[0].getData()
            .samples_submitted
            ? !groupRows[0].getData().samples_submitted
            : true;
          try {
            this.fakeLoadingStart();
            const payload = {
              data: JSON.stringify({
                result: newSamplesSubmittedState
              })
            };
            const url = `${urlStringStart}/api/requests/${requestId}/samples_submitted/`;
            axiosRef.post(url, payload);
            showNotification(
              "Request successfully marked as 'Samples Submitted'.",
              "success"
            );
            groupRows.forEach((row) => {
              let rowData = row.getData();
              rowData.samples_submitted = rowData.samples_submitted
                ? !rowData.samples_submitted
                : true;
              row.update(rowData);
            });
            const table = this.tabulatorInstance.getTable();
            table?.blockRedraw();
            group._group.generateGroupHeaderContents();
            table?.restoreRedraw();
          } catch (error) {
            handleError(error);
          } finally {
            this.fakeLoadingStop();
          }
          break;

        case "qualityPassed":
          if (selectedRows.length === 0) {
            showNotification(
              "Please select libraries/samples in the request first.",
              "warning"
            );
            break;
          }
          let popupTitleQP = `Are you sure?`;
          let popupDescriptionQP = `Marking the following ${
            type === "L" ? "libraries" : "samples"
          } from the request <span style="font-weight: bold">'${requestName}'</span> as <span style="font-weight: bold">Quality Check: Passed</span>. Confirm your action by pressing the <span style="font-weight: bold">Yes</span> button.`;
          let popupListQP = [...selectedNamesList];
          let onYesQP = () => {
            this.qualityCheckChange(selectedRows, "passed");
            this.showPopupWindow = false;
          };
          let onNoQP = () => {
            this.showPopupWindow = false;
          };
          this.createPopupWindow(
            popupTitleQP,
            popupDescriptionQP,
            popupListQP,
            onYesQP,
            onNoQP,
            popupHeight,
            700
          );
          break;

        case "qualityCompromised":
          if (selectedRows.length === 0) {
            showNotification(
              "Please select libraries/samples in the request first.",
              "warning"
            );
            break;
          }
          let popupTitleQC = `Are you sure?`;
          let popupDescriptionQC = `Marking the following ${
            type === "L" ? "libraries" : "samples"
          } from the request <span style="font-weight: bold">'${requestName}'</span> as <span style="font-weight: bold">Quality Check: Compromised</span>. Confirm your action by pressing the <span style="font-weight: bold">Yes</span> button.`;
          let popupListQC = [...selectedNamesList];
          let onYesQC = () => {
            this.qualityCheckChange(selectedRows, "compromised");
            this.showPopupWindow = false;
          };
          let onNoQC = () => {
            this.showPopupWindow = false;
          };
          this.createPopupWindow(
            popupTitleQC,
            popupDescriptionQC,
            popupListQC,
            onYesQC,
            onNoQC,
            popupHeight,
            700
          );
          break;

        case "qualityFailed":
          if (selectedRows.length === 0) {
            showNotification(
              "Please select libraries/samples in the request first.",
              "warning"
            );
            break;
          }
          let popupTitleQF = `Are you sure?`;
          let popupDescriptionQF = `Marking the following ${
            type === "L" ? "libraries" : "samples"
          } from the request <span style="font-weight: bold">'${requestName}'</span> as <span style="font-weight: bold">Quality Check: Failed</span>. Confirm your action by pressing the <span style="font-weight: bold">Yes</span> button.`;
          let popupListQF = [...selectedNamesList];
          let onYesQF = () => {
            this.qualityCheckChange(selectedRows, "failed");
            this.showPopupWindow = false;
          };
          let onNoQF = () => {
            this.showPopupWindow = false;
          };
          this.createPopupWindow(
            popupTitleQF,
            popupDescriptionQF,
            popupListQF,
            onYesQF,
            onNoQF,
            popupHeight,
            700
          );
          break;
      }
    },
    async onBatchCellValueChanged(batchChanges) {
      try {
        const payload = {
          data: JSON.stringify(batchChanges)
        };
        await axiosRef.post(
          `${urlStringStart}/api/incoming_libraries/edit/`,
          payload
        );
      } catch (error) {
        handleError(error);
      }
    },
    async qualityCheckChange(groupRows, qualityCheck) {
      this.fakeLoadingStart();
      const payload = {
        data: JSON.stringify(
          groupRows.map((row) => ({
            pk: row.getData().pk,
            record_type: row.getData().record_type,
            quality_check: qualityCheck
          }))
        )
      };
      try {
        await axiosRef.post(
          `${urlStringStart}/api/incoming_libraries/edit/`,
          payload
        );
        showNotification(
          "Quality check status updated successfully.",
          "success"
        );
        await this.getLibrariesSamples();
      } catch (error) {
        handleError(error);
      } finally {
        this.fakeLoadingStop();
      }
    },
    async fetchExportTemplates() {
      try {
        const response = await axiosRef.get(
          `${urlStringStart}/api/incoming-libraries-samples-templates/`
        );
        this.fetchedIncomingLibrariesAndSamplesTemplates = response.data;
      } catch (error) {
        handleError(error);
      }
    },
    async uploadExportTemplate(event) {
      const file = event.target.files[0];
      if (
        file &&
        file.type ===
          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
      ) {
        const formData = new FormData();
        formData.append("file", file);
        try {
          await axiosRef.post(
            `${urlStringStart}/api/incoming-libraries-samples-templates/upload/`,
            formData,
            {
              headers: {
                "Content-Type": "multipart/form-data"
              }
            }
          );
          showNotification("File uploaded successfully.", "success");
          this.fetchExportTemplates();
        } catch (error) {
          showNotification("Error uploading file: " + error, "error");
        } finally {
          this.selectedFile = "without-file";
        }
      } else {
        showNotification("Please upload a valid XLSX file.", "error");
      }
    },
    async downloadExportTemplate(file) {
      try {
        const response = await axiosRef.get(
          `${urlStringStart}/api/incoming-libraries-samples-templates/${file.id}/download/`,
          {
            responseType: "blob"
          }
        );
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement("a");
        link.href = url;
        link.setAttribute(
          "download",
          file.name || "IncomingLibrariesAndSamples.xlsx"
        );
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
      } catch (error) {
        showNotification("Error downloading file: " + error, "error");
      }
    },
    async removeExportTemplate(index) {
      const file = this.fetchedIncomingLibrariesAndSamplesTemplates[index];
      try {
        await axiosRef.delete(
          `${urlStringStart}/api/incoming-libraries-samples-templates/${file.id}/remove/`
        );
        this.fetchedIncomingLibrariesAndSamplesTemplates.splice(index, 1);
        showNotification("File removed successfully.", "success");
      } catch (error) {
        showNotification("Error removing file: " + error, "error");
      } finally {
        this.selectedFile = "without-file";
      }
    },
    handleExportClick() {
      this.hasSelectedRows = this.librariesSamplesList.some(
        (row) => row.selected
      );
      this.exportSelection = this.hasSelectedRows ? "selected" : "all";
      this.showExportPopup = true;
    },
    async handleExport() {
      try {
        this.fakeLoadingStart();
        const today = new Date();
        const formattedDate = `${today.getFullYear()}${String(
          today.getMonth() + 1
        ).padStart(2, "0")}${String(today.getDate()).padStart(2, "0")}`;

        let exportRows = [];
        if (this.exportSelection === "selected") {
          exportRows = this.librariesSamplesList.filter((row) => row.selected);
        } else {
          exportRows = this.librariesSamplesList;
        }

        const sortedExportRows = [...exportRows].sort((a, b) => {
          const getRequestNum = (str) => {
            const match = String(str).match(/^(\d+)_/);
            return match ? parseInt(match[1], 10) : 0;
          };
          const aNum = getRequestNum(a.request_name);
          const bNum = getRequestNum(b.request_name);
          if (aNum !== bNum) return aNum - bNum;
          return a.barcode?.localeCompare(b.barcode);
        });

        const uniqueRequestIDs = [
          ...new Set(
            sortedExportRows.map((row) => {
              const match = row.request_name.match(/^(\d+)_/);
              return match ? match[1] : row.request_name;
            })
          )
        ]
          .sort()
          .join("_");

        let filename = "";
        if (this.exportSelection === "selected") {
          filename = `${formattedDate}_${uniqueRequestIDs}_incoming`;
        } else {
          filename = `${formattedDate}_incoming`;
        }

        const exportColumns = incomingLibrariesSamplesExportColumns();

        const templateDownloadUrl =
          this.selectedFile !== "without-file"
            ? `${urlStringStart}/api/incoming-libraries-samples-templates/${this.selectedFile.id}/download/`
            : null;

        const blob = await createExcelExportBlob({
          rows: sortedExportRows,
          exportColumns,
          axiosInstance: axiosRef,
          templateDownloadUrl
        });
        saveAs(blob, filename);
      } catch (error) {
        showNotification(
          "Error during export. Please try again.\n" + error,
          "error"
        );
      } finally {
        this.fakeLoadingStop();
        this.showExportPopup = false;
        this.selectedFile = "without-file";
      }
    },
    handleDragOver(e) {
      e.preventDefault();
      this.isDragOver = true;
    },
    handleDragEnter(e) {
      e.preventDefault();
      this.isDragOver = true;
    },
    handleDragLeave(e) {
      if (!e.currentTarget.contains(e.relatedTarget)) {
        this.isDragOver = false;
      }
    },
    handleDrop(e) {
      e.preventDefault();
      this.isDragOver = false;

      const files = e.dataTransfer.files;
      if (files.length > 1) {
        showNotification(
          "Please upload only one XLSX file at a time.",
          "error"
        );
      } else this.processUploadedFile(files[0]);
    },
    processUploadedFile(file) {
      if (
        file &&
        file.type ===
          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
      ) {
        const event = {
          target: {
            files: [file]
          }
        };
        this.uploadExportTemplate(event);
      } else {
        showNotification("Please upload a valid XLSX file.", "error");
      }
    },
    createPopupWindow(
      popupTitle,
      popupDescription,
      popupList,
      onYes,
      onNo,
      popupHeight,
      popupWidth
    ) {
      this.popupContents.popupTitle = popupTitle;
      this.popupContents.popupDescription = popupDescription;
      this.popupContents.popupList = popupList;
      this.popupContents.onYes = onYes;
      this.popupContents.onNo = onNo;
      if (popupWidth && popupHeight) {
        this.popupContents.popupHeight = popupHeight;
        this.popupContents.popupWidth = popupWidth;
      }
      this.showPopupWindow = true;
    }
  }
};
</script>

<style>
html,
body,
#app {
  height: 100%;
  margin: 0;
  padding: 0;
}

.parent-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 10px;
}

.table-container {
  flex: 1;
  overflow: auto;
  position: relative;
}

@media (max-width: 1400px) {
  .header-title {
    min-width: 80px;
  }

  .search-bar {
    width: 280px;
  }

  .search-bar input {
    padding: 8px;
  }

  .header-button {
    padding: 8px 12px;
  }
}

@media (max-width: 1100px) {
  .search-bar {
    width: 250px;
  }

  .search-bar input {
    padding: 6px;
  }

  .header-button span {
    display: none;
  }
}

@media (max-width: 700px) {
  .header-title {
    font-size: 16px;
  }

  .search-bar {
    width: 130px;
  }

  .search-bar input {
    width: 85px;
  }
}

@media (max-width: 550px) {
  .header-logo {
    display: none !important;
  }

  .search-bar {
    display: none;
  }

  .header-button {
    display: none;
  }
}
</style>

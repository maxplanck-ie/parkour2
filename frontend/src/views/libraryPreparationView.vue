<template>
  <div class="parent-container">
    <!-- Loading overlay -->
    <div v-if="loading || fakeLoading" class="loading-overlay">
      <div v-if="!fakeLoading" class="spinner"></div>
      <p v-if="!fakeLoading">
        Loading <span style="font-weight: bold">Libraries & Samples</span>...
      </p>
    </div>

    <!-- Header -->
    <div class="header">
      <div class="header-logo" style="display: inline; margin-right: 10px">
        <svg style="display: block" fill="none" width="42px" height="42px" version="1.1"
          xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
          <path opacity="0.3"
            d="M14 17.5C14 16.0955 14 15.3933 14.3371 14.8889C14.483 14.6705 14.6705 14.483 14.8889 14.3371C15.3933 14 16.0955 14 17.5 14V14V14C18.9045 14 19.6067 14 20.1111 14.3371C20.3295 14.483 20.517 14.6705 20.6629 14.8889C21 15.3933 21 16.0955 21 17.5V17.5V17.5C21 18.9045 21 19.6067 20.6629 20.1111C20.517 20.3295 20.3295 20.517 20.1111 20.6629C19.6067 21 18.9045 21 17.5 21V21V21C16.0955 21 15.3933 21 14.8889 20.6629C14.6705 20.517 14.483 20.3295 14.3371 20.1111C14 19.6067 14 18.9045 14 17.5V17.5V17.5Z"
            fill="#333333" />
          <path opacity="0.3"
            d="M3 17.5C3 16.0955 3 15.3933 3.33706 14.8889C3.48298 14.6705 3.67048 14.483 3.88886 14.3371C4.39331 14 5.09554 14 6.5 14V14V14C7.90446 14 8.60669 14 9.11114 14.3371C9.32952 14.483 9.51702 14.6705 9.66294 14.8889C10 15.3933 10 16.0955 10 17.5V17.5V17.5C10 18.9045 10 19.6067 9.66294 20.1111C9.51702 20.3295 9.32952 20.517 9.11114 20.6629C8.60669 21 7.90446 21 6.5 21V21V21C5.09554 21 4.39331 21 3.88886 20.6629C3.67048 20.517 3.48298 20.3295 3.33706 20.1111C3 19.6067 3 18.9045 3 17.5V17.5V17.5Z"
            fill="#333333" />
          <path opacity="0.3"
            d="M3 6.5C3 5.09554 3 4.39331 3.33706 3.88886C3.48298 3.67048 3.67048 3.48298 3.88886 3.33706C4.39331 3 5.09554 3 6.5 3V3V3C7.90446 3 8.60669 3 9.11114 3.33706C9.32952 3.48298 9.51702 3.67048 9.66294 3.88886C10 4.39331 10 5.09554 10 6.5V6.5V6.5C10 7.90446 10 8.60669 9.66294 9.11114C9.51702 9.32952 9.32952 9.51702 9.11114 9.66294C8.60669 10 7.90446 10 6.5 10V10V10C5.09554 10 4.39331 10 3.88886 9.66294C3.67048 9.51702 3.48298 9.32952 3.33706 9.11114C3 8.60669 3 7.90446 3 6.5V6.5V6.5Z"
            fill="#333333" />
          <path
            d="M14 17.5C14 16.0955 14 15.3933 14.3371 14.8889C14.483 14.6705 14.6705 14.483 14.8889 14.3371C15.3933 14 16.0955 14 17.5 14V14V14C18.9045 14 19.6067 14 20.1111 14.3371C20.3295 14.483 20.517 14.6705 20.6629 14.8889C21 15.3933 21 16.0955 21 17.5V17.5V17.5C21 18.9045 21 19.6067 20.6629 20.1111C20.517 20.3295 20.3295 20.517 20.1111 20.6629C19.6067 21 18.9045 21 17.5 21V21V21C16.0955 21 15.3933 21 14.8889 20.6629C14.6705 20.517 14.483 20.3295 14.3371 20.1111C14 19.6067 14 18.9045 14 17.5V17.5V17.5Z"
            stroke="white" stroke-width="1.5" />
          <path
            d="M3 17.5C3 16.0955 3 15.3933 3.33706 14.8889C3.48298 14.6705 3.67048 14.483 3.88886 14.3371C4.39331 14 5.09554 14 6.5 14V14V14C7.90446 14 8.60669 14 9.11114 14.3371C9.32952 14.483 9.51702 14.6705 9.66294 14.8889C10 15.3933 10 16.0955 10 17.5V17.5V17.5C10 18.9045 10 19.6067 9.66294 20.1111C9.51702 20.3295 9.32952 20.517 9.11114 20.6629C8.60669 21 7.90446 21 6.5 21V21V21C5.09554 21 4.39331 21 3.88886 20.6629C3.67048 20.517 3.48298 20.3295 3.33706 20.1111C3 19.6067 3 18.9045 3 17.5V17.5V17.5Z"
            stroke="white" stroke-width="1.5" />
          <path
            d="M3 6.5C3 5.09554 3 4.39331 3.33706 3.88886C3.48298 3.67048 3.67048 3.48298 3.88886 3.33706C4.39331 3 5.09554 3 6.5 3V3V3C7.90446 3 8.60669 3 9.11114 3.33706C9.32952 3.48298 9.51702 3.67048 9.66294 3.88886C10 4.39331 10 5.09554 10 6.5V6.5V6.5C10 7.90446 10 8.60669 9.66294 9.11114C9.51702 9.32952 9.32952 9.51702 9.11114 9.66294C8.60669 10 7.90446 10 6.5 10V10V10C5.09554 10 4.39331 10 3.88886 9.66294C3.67048 9.51702 3.48298 9.32952 3.33706 9.11114C3 8.60669 3 7.90446 3 6.5V6.5V6.5Z"
            stroke="white" stroke-width="1.5" />
          <path d="M14 6.5H21" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
          <path d="M17.5 3V10" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </div>
      <div class="header-title" style="display: inline">
        Library Preparation
      </div>

      <!-- Sticky right section for search, and select columns -->
      <div class="sticky-actions">
        <div class="search-bar">
          <input ref="searchInput" v-model="searchQuery" type="text" placeholder="Search" />
          <font-awesome-icon icon="fa-solid fa-magnifying-glass" style="color: darkgrey" />
        </div>
        <div class="button-popup-wrapper">
          <button class="header-button" id="toggleSelectColumnsButton" @click="toggleSelectColumns">
            <font-awesome-icon icon="fa-solid fa-columns" style="color: white" />
            <span> Select Columns </span>
          </button>
          <div id="selectColumnsPopup" v-if="showSelectColumns" class="button-popup-container" style="
              left: -50px;
              width: 250px;
              max-height: 473px;
              display: flex;
              flex-direction: column;
              padding: 10px 10px 5px 10px;
            ">
            <ul style="
                padding: 5px 7px 7px;
                margin: 0;
                flex-grow: 1;
                overflow-y: auto;
              ">
              <li v-for="(column, index) in columnsList" :key="index" style="list-style: none">
                <template v-if="
                  column.field !== 'selected' ||
                  (column.field === 'selected' && column.visible == false)
                ">
                  <label :style="{
                    backgroundColor: column.columns ? '#33333310' : 'white',
                    cursor: column.columns ? 'default' : 'pointer'
                  }">
                    <input v-if="!column.columns" type="checkbox" v-model="column.visible"
                      @change="toggleColumnVisibility(column)" />
                    <font-awesome-icon v-if="column.columns" icon="fa-solid fa-caret-down" style="
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        border: 2px solid black;
                        height: 18px;
                        width: 18px;
                        border-radius: 4px;
                        text-align: center;
                        background-color: orange;
                        color: white;
                      " />
                    <span>{{ column.title }}</span>
                  </label>
                </template>
              </li>
            </ul>
            <div style="
                padding-top: 8px;
                border-top: 1px solid #eee;
                display: flex;
                flex-direction: column;
              ">
              <button @click="resetColumnVisibility" class="reset-button">
                Reset Visibility Settings
              </button>
              <button style="margin-bottom: 5px" @click="resetColumnWidths" class="reset-button">
                Reset Width Settings
              </button>
            </div>
          </div>
        </div>
        <div class="button-popup-wrapper">
          <button class="header-button" @click="toggleGroups">
            <font-awesome-icon icon="fa-solid fa-layer-group" style="color: white" />
            <span> Toggle Views </span>
          </button>
        </div>
        <button class="header-button" @click="handleExportClick">
          <font-awesome-icon icon="fa-solid fa-file-excel" style="color: white" />
          <span> Export to Excel </span>
        </button>
      </div>
    </div>

    <!-- Main content section with table -->
    <div class="table-container">
      <TabulatorTable v-if="!loading" ref="tabulatorTableRef" :rowData="librariesSamplesList" :columnDefs="columnsList"
        groupBy="library_protocol_name" :groupSort="{ field: 'library_protocol_name', order: 'asc' }" :tableOptions="{
          ...tableOptions,
          onBatchCellValueChanged,
          fakeLoadingStart,
          fakeLoadingStop,
          handleColumnResized,
          handleColumnVisibilityChanged
        }" />
    </div>

    <!-- Popup window -->
    <div v-if="showPopupWindow" class="popup-overlay">
      <div class="popup-container" :style="{
        height: popupContents.popupHeight + 'px',
        width: popupContents.popupWidth + 'px'
      }">
        <div class="popup-header">
          <svg style="display: block" fill="none" width="42px" height="42px" version="1.1"
            xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
            <g>
              <path opacity="0.3"
                d="M3 9.22843V14.7716C3 15.302 3.21071 15.8107 3.58579 16.1858L7.81421 20.4142C8.18929 20.7893 8.69799 21 9.22843 21H14.7716C15.302 21 15.8107 20.7893 16.1858 20.4142L20.4142 16.1858C20.7893 15.8107 21 15.302 21 14.7716V9.22843C21 8.69799 20.7893 8.18929 20.4142 7.81421L16.1858 3.58579C15.8107 3.21071 15.302 3 14.7716 3H9.22843C8.69799 3 8.18929 3.21071 7.81421 3.58579L3.58579 7.81421C3.21071 8.18929 3 8.69799 3 9.22843Z"
                fill="#323232" />
              <path
                d="M3 9.22843V14.7716C3 15.302 3.21071 15.8107 3.58579 16.1858L7.81421 20.4142C8.18929 20.7893 8.69799 21 9.22843 21H14.7716C15.302 21 15.8107 20.7893 16.1858 20.4142L20.4142 16.1858C20.7893 15.8107 21 15.302 21 14.7716V9.22843C21 8.69799 20.7893 8.18929 20.4142 7.81421L16.1858 3.58579C15.8107 3.21071 15.302 3 14.7716 3H9.22843C8.69799 3 8.18929 3.21071 7.81421 3.58579L3.58579 7.81421C3.21071 8.18929 3 8.69799 3 9.22843Z"
                stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
              <path d="M12 8V13" stroke="white" stroke-width="1.5" stroke-linecap="round" />
              <path d="M12 16V15.9888" stroke="white" stroke-width="1.5" stroke-linecap="round" />
            </g>
          </svg>
          <span class="popup-title">{{ popupContents.popupTitle }}</span>
          <button class="popup-close-button" @click="showPopupWindow = false">
            &times;
          </button>
        </div>
        <div class="popup-body">
          <div v-html="popupContents.popupDescription"></div>
          <div v-if="popupContents.popupList && popupContents.popupList.length > 0" class="popup-scrollable-content">
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
    <div v-if="showExportPopup" class="popup-overlay" @dragover.prevent="handleDragOver" @drop="handleDrop"
      @dragenter="handleDragEnter" @dragleave="handleDragLeave" :class="{ 'drag-over': isDragOver }">

      <div class="drag-drop-indicator">
        <div style="
          display: flex;
          justify-content: center; 
          align-items: center; 
          height: 200px; 
        ">
          <p>Drop <span style="font-weight: bold">XLSX file</span> here to upload as <span
              style="font-weight: bold">template</span></p>
        </div>
      </div>
      <div v-if="!isDragOver" class="popup-container" :style="{ width: '670px', height: '500px' }">
        <div class="popup-header">
          <span class="popup-title">Export Options</span>
          <span class="popup-info-button" @mouseover="showExportHelpTooltip = true"
            @mouseleave="showExportHelpTooltip = false">
            ?
            <div v-if="showExportHelpTooltip" class="tooltip-box">
              <span style="font-weight: bold">INSTRUCTIONS:</span>
              <ol>
                <li>
                  To create custom templates, export the original sheet named
                  <span style="font-weight: bold">'Parkour'</span> by selecting
                  the
                  <span style="font-weight: bold">'Export without any additional sheets'</span>
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
          <div class="export-section" style="height: 100%">
            <div style="font-weight: bold; margin-bottom: 8px;">
              Upload additional excel sheet templates to append:
            </div>
            <div class="file-list-section" style="height: 280px;">
              <div class="file-item">
                <div class="file-info">
                  <svg style="display: block" fill="none" width="24px" height="24px" version="1.1"
                    xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                    <g>
                      <path opacity="0.1"
                        d="M17.8284 6.82843C18.4065 7.40649 18.6955 7.69552 18.8478 8.06306C19 8.4306 19 8.83935 19 9.65685L19 17C19 18.8856 19 19.8284 18.4142 20.4142C17.8284 21 16.8856 21 15 21H9C7.11438 21 6.17157 21 5.58579 20.4142C5 19.8284 5 18.8856 5 17L5 7C5 5.11438 5 4.17157 5.58579 3.58579C6.17157 3 7.11438 3 9 3H12.3431C13.1606 3 13.5694 3 13.9369 3.15224C14.3045 3.30448 14.5935 3.59351 15.1716 4.17157L17.8284 6.82843Z"
                        fill="#323232" />
                      <path
                        d="M17.8284 6.82843C18.4065 7.40649 18.6955 7.69552 18.8478 8.06306C19 8.4306 19 8.83935 19 9.65685L19 17C19 18.8856 19 19.8284 18.4142 20.4142C17.8284 21 16.8856 21 15 21H9C7.11438 21 6.17157 21 5.58579 20.4142C5 19.8284 5 18.8856 5 17L5 7C5 5.11438 5 4.17157 5.58579 3.58579C6.17157 3 7.11438 3 9 3H12.3431C13.1606 3 13.5694 3 13.9369 3.15224C14.3045 3.30448 14.5935 3.59351 15.1716 4.17157L17.8284 6.82843Z"
                        stroke="#323232" stroke-width="2" stroke-linejoin="round" />
                    </g>
                  </svg>
                  <span>Export without any additional sheets</span>
                </div>
                <div class="file-actions">
                  <div class="file-actions-radio-button" style="border: none; margin-right: 5px">
                    <input type="radio" title="Select" id="without-file" value="without-file" v-model="selectedFile" />
                  </div>
                </div>
              </div>
              <div v-for="(file, index) in fetchedLibrariesAndSamplesTemplates" :key="index" class="file-item">
                <div class="file-info">
                  <svg style="display: block" fill="none" width="24px" height="24px" version="1.1"
                    xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                    <g>
                      <path opacity="0.1"
                        d="M17.8284 6.82843C18.4065 7.40649 18.6955 7.69552 18.8478 8.06306C19 8.4306 19 8.83935 19 9.65685L19 17C19 18.8856 19 19.8284 18.4142 20.4142C17.8284 21 16.8856 21 15 21H9C7.11438 21 6.17157 21 5.58579 20.4142C5 19.8284 5 18.8856 5 17L5 7C5 5.11438 5 4.17157 5.58579 3.58579C6.17157 3 7.11438 3 9 3H12.3431C13.1606 3 13.5694 3 13.9369 3.15224C14.3045 3.30448 14.5935 3.59351 15.1716 4.17157L17.8284 6.82843Z"
                        fill="#323232" />
                      <path
                        d="M17.8284 6.82843C18.4065 7.40649 18.6955 7.69552 18.8478 8.06306C19 8.4306 19 8.83935 19 9.65685L19 17C19 18.8856 19 19.8284 18.4142 20.4142C17.8284 21 16.8856 21 15 21H9C7.11438 21 6.17157 21 5.58579 20.4142C5 19.8284 5 18.8856 5 17L5 7C5 5.11438 5 4.17157 5.58579 3.58579C6.17157 3 7.11438 3 9 3H12.3431C13.1606 3 13.5694 3 13.9369 3.15224C14.3045 3.30448 14.5935 3.59351 15.1716 4.17157L17.8284 6.82843Z"
                        stroke="#323232" stroke-width="2" stroke-linejoin="round" />
                      <path d="M9 6L11 6" stroke="#323232" stroke-width="2" stroke-linecap="round"
                        stroke-linejoin="round" />
                      <path d="M10 9L12 9" stroke="#323232" stroke-width="2" stroke-linecap="round"
                        stroke-linejoin="round" />
                      <path d="M9 12L11 12" stroke="#323232" stroke-width="2" stroke-linecap="round"
                        stroke-linejoin="round" />
                      <path d="M10 15L12 15" stroke="#323232" stroke-width="2" stroke-linecap="round"
                        stroke-linejoin="round" />
                    </g>
                  </svg>
                  <span>{{ file.name }}</span>
                </div>
                <div class="file-actions">
                  <button @click="downloadExportTemplate(file)" class="download-button" title="Download Original File">
                    <svg style="display: block" fill="none" width="24px" height="24px" version="1.1"
                      xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                      <g>
                        <path opacity="0.1"
                          d="M17.8284 6.82843C18.4065 7.40649 18.6955 7.69552 18.8478 8.06306C19 8.4306 19 8.83935 19 9.65685L19 17C19 18.8856 19 19.8284 18.4142 20.4142C17.8284 21 16.8856 21 15 21H9C7.11438 21 6.17157 21 5.58579 20.4142C5 19.8284 5 18.8856 5 17L5 7C5 5.11438 5 4.17157 5.58579 3.58579C6.17157 3 7.11438 3 9 3H12.3431C13.1606 3 13.5694 3 13.9369 3.15224C14.3045 3.30448 14.5935 3.59351 15.1716 4.17157L17.8284 6.82843Z"
                          fill="#323232" />
                        <path
                          d="M17.8284 6.82843C18.4065 7.40649 18.6955 7.69552 18.8478 8.06306C19 8.4306 19 8.83935 19 9.65685L19 17C19 18.8856 19 19.8284 18.4142 20.4142C17.8284 21 16.8856 21 15 21H9C7.11438 21 6.17157 21 5.58579 20.4142C5 19.8284 5 18.8856 5 17L5 7C5 5.11438 5 4.17157 5.58579 3.58579C6.17157 3 7.11438 3 9 3H12.3431C13.1606 3 13.5694 3 13.9369 3.15224C14.3045 3.30448 14.5935 3.59351 15.1716 4.17157L17.8284 6.82843Z"
                          stroke="#323232" stroke-width="2" stroke-linejoin="round" />
                        <path d="M12 16L12 11" stroke="#323232" stroke-width="2" stroke-linecap="round"
                          stroke-linejoin="round" />
                        <path d="M9.5 14L11.5 16V16C11.7761 16.2761 12.2239 16.2761 12.5 16V16L14.5 14" stroke="#323232"
                          stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                      </g>
                    </svg>
                  </button>
                  <button @click="removeExportTemplate(index)" class="remove-button" title="Remove File">
                    <svg style="display: block" fill="none" width="24px" height="24px" version="1.1"
                      xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                      <g>
                        <path opacity="0.1"
                          d="M5.02322 5.37683C5 5.82377 5 6.35711 5 7.00006V17.0001C5 18.8857 5 19.8285 5.58579 20.4143C6.17157 21.0001 7.11438 21.0001 9 21.0001H15C16.8856 21.0001 17.8284 21.0001 18.4142 20.4143C18.6935 20.135 18.8396 19.7746 18.9161 19.2697L5.02322 5.37683Z"
                          fill="#323232" />
                        <path
                          d="M8 3H12.3431C13.1606 3 13.5694 3 13.9369 3.15224C14.3045 3.30448 14.5935 3.59351 15.1716 4.17157L17.8284 6.82843C18.4065 7.40649 18.6955 7.69552 18.8478 8.06306C19 8.4306 19 8.83935 19 9.65685L19 14"
                          stroke="#323232" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                        <path
                          d="M5 5V17C5 18.8856 5 19.8284 5.58579 20.4142C6.17157 21 7.11438 21 9 21H17C17 21 17 21 17 21C18.1046 21 19 20.1046 19 19C19 19 19 19 19 19V19"
                          stroke="#323232" stroke-width="2" stroke-linejoin="round" />
                        <path d="M3 3L21 21" stroke="#323232" stroke-width="2" stroke-linecap="round"
                          stroke-linejoin="round" />
                      </g>
                    </svg>
                  </button>
                  <div class="file-actions-radio-button">
                    <input type="radio" title="Select File" :id="'file-radio-' + index" :value="file"
                      v-model="selectedFile" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="popup-footer">
          <div class="file-upload-section">
            <label for="file-upload" class="file-upload-label"
              title="Upload additional sheet to append to the exported sheet.">
              <svg style="display: block; margin-right: 4px" fill="none" width="24px" height="24px" version="1.1"
                xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                <g>
                  <path opacity="0.1"
                    d="M17.8284 6.82843C18.4065 7.40649 18.6955 7.69552 18.8478 8.06306C19 8.4306 19 8.83935 19 9.65685L19 17C19 18.8856 19 19.8284 18.4142 20.4142C17.8284 21 16.8856 21 15 21H9C7.11438 21 6.17157 21 5.58579 20.4142C5 19.8284 5 18.8856 5 17L5 7C5 5.11438 5 4.17157 5.58579 3.58579C6.17157 3 7.11438 3 9 3H12.3431C13.1606 3 13.5694 3 13.9369 3.15224C14.3045 3.30448 14.5935 3.59351 15.1716 4.17157L17.8284 6.82843Z"
                    fill="#323232" />
                  <path
                    d="M17.8284 6.82843C18.4065 7.40649 18.6955 7.69552 18.8478 8.06306C19 8.4306 19 8.83935 19 9.65685L19 17C19 18.8856 19 19.8284 18.4142 20.4142C17.8284 21 16.8856 21 15 21H9C7.11438 21 6.17157 21 5.58579 20.4142C5 19.8284 5 18.8856 5 17L5 7C5 5.11438 5 4.17157 5.58579 3.58579C6.17157 3 7.11438 3 9 3H12.3431C13.1606 3 13.5694 3 13.9369 3.15224C14.3045 3.30448 14.5935 3.59351 15.1716 4.17157L17.8284 6.82843Z"
                    stroke="#323232" stroke-width="2" stroke-linejoin="round" />
                  <path d="M12 11L12 16" stroke="#323232" stroke-width="2" stroke-linecap="round"
                    stroke-linejoin="round" />
                  <path d="M14.5 13.5L9.5 13.5" stroke="#323232" stroke-width="2" stroke-linecap="round"
                    stroke-linejoin="round" />
                </g>
              </svg>
              <span>Upload</span>
            </label>
            <input id="file-upload" type="file" accept=".xlsx" @change="uploadExportTemplate" style="display: none" />
          </div>
          <button class="popup-button yes-button" @click="handleExport">
            OK
          </button>
          <button class="popup-button" @click="
            showExportPopup = false;
          selectedFile = 'without-file';
          ">
            Cancel
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="jsx">
import TabulatorTable from "../components/TabulatorTable.vue";
import ExcelJS from "exceljs";
import { saveAs } from "file-saver";
import {
  showNotification,
  handleError,
  createAxiosObject,
  urlStringStartsWith
} from "../utilities/utilityFunctions";
import { libraryPreparationColumnDefs, libraryPreparationGroupHeader } from "../constants/libraryPreparationConsts";
const axiosRef = createAxiosObject();
const urlStringStart = urlStringStartsWith();

export default {
  name: "LibraryPreparation",
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
      showPopupWindow: false,
      showExportPopup: false,
      showExportHelpTooltip: false,
      fetchedLibraryPreparationTemplates: [],
      selectedFile: "without-file",
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
          { column: "library_protocol_name", dir: "asc" },
          { column: "barcode", dir: "asc" },
          {
            column: "request_name",
            dir: "asc",
            sorter: (a, b) => {
              const getNum = (str) => {
                const match = String(str).match(/^(\d+)_/);
                return match ? parseInt(match[1], 10) : 0;
              };
              return getNum(a) - getNum(b);
            }
          }
        ],
        groupHeader: (value, count, data) => {
          return libraryPreparationGroupHeader(value, count);
        }
      },
      searchQuery: "",
      showSelectColumns: false
    };
  },
  mounted() {
    this.getLibrariesSamples();
    // this.getROCrateData();
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
          "search_library_preparation",
          newValue === null ? "" : newValue
        );
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
          urlStringStart + "/api/library_preparation/"
        );
        let fetchedRows = response.data.map((element) => ({
          pk: element.pk || "",
          name: element.name || "",
          type: element.barcode[2] || "",
          barcode: element.barcode + "*" || "",
          is_converted:
            element.is_converted === null ? "" : element.is_converted,
          request_name: element.request_name || "",
          pool_name: element.pool_name || "",
          library_protocol:
            element.library_protocol === 0 ? 0 : element.library_protocol || "",
          library_protocol_name: element.library_protocol_name || "",
          concentration_sample:
            element.concentration_sample === 0
              ? 0
              : element.concentration_sample || "",
          concentration_library:
            element.concentration_library === 0
              ? 0
              : element.concentration_library || "",
          starting_amount:
            element.starting_amount === 0 ? 0 : element.starting_amount || "",
          pcr_cycles: element.pcr_cycles === 0 ? 0 : element.pcr_cycles || "",
          mean_fragment_size:
            element.mean_fragment_size === 0
              ? 0
              : element.mean_fragment_size || "",
          smear_analysis:
            element.smear_analysis === 0 ? 0 : element.smear_analysis || "",
          comments: element.comments || "",
          comments_facility: element.comments_facility || "",
          comments_library_sample: element.comments_library_sample || "",
          coordinate: element.coordinate || "",
          index_type: element.index_type || "",
          index_i7_id: element.index_i7_id || "",
          index_i5_id: element.index_i5_id || "",
          create_time: element.create_time
            ? (() => {
              const date = new Date(element.create_time);
              if (isNaN(date)) return "";
              const day = String(date.getDate()).padStart(2, "0");
              const month = String(date.getMonth() + 1).padStart(2, "0");
              const year = date.getFullYear();
              return `${day}.${month}.${year}`;
            })()
            : "",
          measuring_unit_facility: element.measuring_unit_facility || "",
          measured_value_facility:
            element.measured_value_facility === 0
              ? 0
              : element.measured_value_facility || "",
          size_distribution_facility:
            element.size_distribution_facility === 0
              ? 0
              : element.size_distribution_facility || ""
        }));
        this.librariesSamplesList = fetchedRows;
      } catch (error) {
        handleError(error);
      } finally {
        this.loading = false;
      }
    },
    async getROCrateData() {
      try {
        const response = await axiosRef.get(
          urlStringStart + "/api/generate_ro_crate/?barcodes=25L005612"
        );

        console.log(response.data);

        const dataStr = JSON.stringify(response.data, null, 2);
        const blob = new Blob([dataStr], { type: "application/ld+json" });
        const url = URL.createObjectURL(blob);

        const link = document.createElement("a");
        link.href = url;
        link.download = "ro_crate.jsonld";
        document.body.appendChild(link);
        link.click();

        document.body.removeChild(link);
        URL.revokeObjectURL(url);
      } catch (error) {
        handleError(error);
      }
    },
    setColumns() {
      const storedVisibility = JSON.parse(
        localStorage.getItem("libraryPreparationColumnVisibility") || "{}"
      );
      const storedWidths = JSON.parse(
        localStorage.getItem("libraryPreparationColumnWidths") || "{}"
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

      let columnDefs = libraryPreparationColumnDefs(() => this.tabulatorInstance);

      this.columnsList = applySettings(columnDefs);
    },
    handleOutsideClick(event) {
      const selectColumnsPopup = this.$el.querySelector("#selectColumnsPopup");
      const selectColumnsButton = this.$el.querySelector(
        "#toggleSelectColumnsButton"
      );

      if (
        this.showSelectColumns &&
        selectColumnsPopup &&
        !selectColumnsPopup.contains(event.target) &&
        selectColumnsButton !== event.target &&
        !selectColumnsButton.contains(event.target)
      ) {
        this.showSelectColumns = false;
      }
    },
    handleKeyDown(event) {
      const isEscape = event.key === "Escape";
      if (isEscape && (this.showPopupWindow || this.showExportPopup)) {
        this.showPopupWindow = false;
        this.showExportPopup = false;
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
    toggleSelectColumns() {
      this.showSelectColumns = !this.showSelectColumns;
    },
    handleColumnResized(column) {
      const field = column.getField();
      const width = column.getWidth();
      const storedWidths = JSON.parse(
        localStorage.getItem("libraryPreparationColumnWidths") || "{}"
      );
      const newWidths = {
        ...storedWidths,
        [field]: width
      };
      localStorage.setItem(
        "libraryPreparationColumnWidths",
        JSON.stringify(newWidths)
      );
      this.fakeLoadingStart();
      setTimeout(() => this.fakeLoadingStop(), 50);
    },
    handleColumnVisibilityChanged(field, visible) {
      const storedVisibility = JSON.parse(
        localStorage.getItem("libraryPreparationColumnVisibility") || "{}"
      );

      const newVisibility = {
        ...storedVisibility,
        [field]: visible
      };

      localStorage.setItem(
        "libraryPreparationColumnVisibility",
        JSON.stringify(newVisibility)
      );

      this.fakeLoadingStart();
      setTimeout(() => this.fakeLoadingStop(), 50);
    },
    toggleColumnVisibility(column) {
      if (this.tabulatorInstance) {
        this.tabulatorInstance.getTable().toggleColumn(column.field);
      }
    },
    resetColumnWidths() {
      localStorage.removeItem("libraryPreparationColumnWidths");
      this.setColumns();
      this.fakeLoadingStart();
      setTimeout(() => this.fakeLoadingStop(), 300);
    },
    resetColumnVisibility() {
      localStorage.removeItem("libraryPreparationColumnVisibility");
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

        case "qualityPassed":
          if (selectedRows.length === 0) {
            showNotification(
              "Please select libraries/samples in the request first.",
              "warning"
            );
            break;
          }
          let popupTitleQP = `Are you sure?`;
          let popupDescriptionQP = `Marking the following ${type === "L" ? "libraries" : "samples"
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

        case "qualityFailed":
          if (selectedRows.length === 0) {
            showNotification(
              "Please select libraries/samples in the request first.",
              "warning"
            );
            break;
          }
          let popupTitleQF = `Are you sure?`;
          let popupDescriptionQF = `Marking the following ${type === "L" ? "libraries" : "samples"
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
          `${urlStringStart}/api/library_preparation/edit/`,
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
          `${urlStringStart}/api/library_preparation/edit/`,
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
          `${urlStringStart}/api/library-preparation-templates/`
        );
        this.fetchedLibraryPreparationTemplates = response.data;
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
            `${urlStringStart}/api/library-preparation-templates/upload/`,
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
          `${urlStringStart}/api/library-preparation-templates/${file.id}/download/`,
          {
            responseType: "blob"
          }
        );
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement("a");
        link.href = url;
        link.setAttribute("download", file.name || "Library_Preparation.xlsx");
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
      } catch (error) {
        showNotification("Error downloading file: " + error, "error");
      }
    },
    async removeExportTemplate(index) {
      const file = this.fetchedLibraryPreparationTemplates[index];
      try {
        await axiosRef.delete(
          `${urlStringStart}/api/library-preparation-templates/${file.id}/remove/`
        );
        this.fetchedLibraryPreparationTemplates.splice(index, 1);
        showNotification("File removed successfully.", "success");
      } catch (error) {
        showNotification("Error removing file: " + error, "error");
      } finally {
        this.selectedFile = "without-file";
      }
    },
    handleExportClick() {
      // let requestIdsSet = new Set();
      //   [...this.librariesSamplesList].filter((row) => row.selected).forEach((row) => {
      //     const match = row.request_name?.match(/^(\d+)_/);
      //     if (match) {
      //       requestIdsSet.add(match[1]);
      //     }
      //   });
      // if (requestIdsSet.length === 0) {
      //   showNotification("Please select at least one request to export.", "warning")
      //   return;
      // }
      // else if (requestIdsSet.length > 1) {
      //   showNotification("Please select at least one request to export.", "warning")
      //   return;
      // }
      // else
      this.showExportPopup = true;
    },
    async handleExport() {
      this.fakeLoadingStart();
      try {
        const today = new Date();
        const formattedDate = `${today.getFullYear()}${String(
          today.getMonth() + 1
        ).padStart(2, "0")}${String(today.getDate()).padStart(2, "0")}`;

        const sortedRows = [...this.librariesSamplesList].sort((a, b) => {
          const getRequestNum = (str) => {
            const match = String(str).match(/^(\d+)_/);
            return match ? parseInt(match[1], 10) : 0;
          };
          const protocolCompare = b.library_protocol_name?.localeCompare(
            a.library_protocol_name
          );
          if (protocolCompare !== 0) return protocolCompare;
          const aNum = getRequestNum(a.request_name);
          const bNum = getRequestNum(b.request_name);
          if (aNum !== bNum) return aNum - bNum;
          return a.barcode?.localeCompare(b.barcode);
        });

        let exportRows = sortedRows.filter((row) => row.selected);
        const requestIdsSet = new Set();
        exportRows.forEach((row) => {
          const match = row.request_name?.match(/^(\d+)_/);
          if (match) {
            requestIdsSet.add(match[1]);
          }
        });
        const requestIds = Array.from(requestIdsSet)
          .map((id) => parseInt(id, 10))
          .sort((a, b) => a - b)
          .slice(0, 40)
          .join("_");
        const filename = `${formattedDate}_${requestIds}_preparation.xlsx`;
        const wb = new ExcelJS.Workbook();
        if (this.selectedFile !== "without-file") {
          const response = await axiosRef.get(
            `${urlStringStart}/api/library-preparation-templates/${this.selectedFile.id}/download/`,
            { responseType: "arraybuffer" }
          );
          await wb.xlsx.load(response.data);
        }

        let parkourSheet = wb.getWorksheet("Parkour");
        if (parkourSheet) {
          parkourSheet.eachRow((row, rowNumber) => {
            parkourSheet.spliceRows(rowNumber, 1);
          });
          parkourSheet.columns = [];
        } else {
          parkourSheet = wb.addWorksheet("Parkour");
        }

        parkourSheet.columns = [
          { header: "Request", key: "request_name", width: 25 },
          { header: "Barcode", key: "barcode", width: 15 },
          { header: "Name", key: "name", width: 20 },
          { header: "Date", key: "create_time", width: 15 },
          { header: "Protocol", key: "library_protocol_name", width: 20 },
          {
            header: "Comment Library/Sample",
            key: "comments_library_sample",
            width: 25
          },
          { header: "Pool", key: "pool_name", width: 10 },
          { header: "Index Type", key: "index_type", width: 20 },
          { header: "I7 ID", key: "index_i7_id", width: 20 },
          { header: "I5 ID", key: "index_i5_id", width: 20 },
          { header: "Coordinate", key: "coordinate", width: 10 },
          { header: "Value", key: "measured_value_facility", width: 15 },
          { header: "Unit", key: "measuring_unit_facility", width: 15 },
          { header: "bp Sample", key: "size_distribution_facility", width: 15 }
        ];

        exportRows.forEach((row) => {
          parkourSheet.addRow(row);
        });

        const sortedSheets = [...wb.worksheets].sort(
          (a, b) => a.orderNo - b.orderNo
        );
        const otherSheets = sortedSheets.filter(
          (sheet) => sheet !== parkourSheet
        );

        parkourSheet.orderNo = 0;
        otherSheets.forEach((sheet, index) => {
          sheet.orderNo = index + 1;
        });

        wb.views = [{ activeTab: 0, firstSheet: 0 }];

        wb.worksheets.forEach((sheet) => {
          sheet.eachRow((row) => {
            row.eachCell((cell) => {
              if (cell.formula) {
                cell.model.result = undefined;
              }
            });
          });
        });

        const buffer = await wb.xlsx.writeBuffer();
        const blob = new Blob([buffer], {
          type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
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
    ellipsisContainer(text, boldText) {
      return `<div title='${text}' style="overflow: hidden; white-space: nowrap; text-overflow: ellipsis; padding: 12px 8px 12px 12px; font-weight: ${boldText === true ? "bold" : "normal"
        }">
                ${text}
              </div>`;
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

<!--
bp Sample: delete gives error
add validations according to old component: deleting, right click operations, copy paste on ctrl operations
export formulas don't refresh the values after concat

modify the admin panel
-->

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
          <path opacity="0.3" fill-rule="evenodd" clip-rule="evenodd"
            d="M5 15L3.58579 16.4142C3.21071 16.7893 3 17.298 3 17.8284V18C3 19.1046 3.89543 20 5 20H19C20.1046 20 21 19.1046 21 18V17.8284C21 17.298 20.7893 16.7893 20.4142 16.4142L19 15H5Z"
            fill="#323232" />
          <path
            d="M15.0486 4H8.95137C8.46527 4 8.31058 4.65529 8.74536 4.87268C8.90142 4.95071 9 5.11022 9 5.2847V10.1716C9 10.702 8.78929 11.2107 8.41421 11.5858L3.58579 16.4142C3.21071 16.7893 3 17.298 3 17.8284V18C3 19.1046 3.89543 20 5 20H19C20.1046 20 21 19.1046 21 18V17.8284C21 17.298 20.7893 16.7893 20.4142 16.4142L15.5858 11.5858C15.2107 11.2107 15 10.702 15 10.1716V5.2847C15 5.11022 15.0986 4.95071 15.2546 4.87268C15.6894 4.65529 15.5347 4 15.0486 4Z"
            stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
          <path d="M5 15H19" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </div>
      <div class="header-title" style="display: inline">
        Libraries & Samples
      </div>

      <!-- Sticky right section for search, date range, advanced filters, select columns and export-->
      <div class="sticky-actions">
        <div class="search-bar">
          <input ref="searchInput" v-model="searchQuery" type="text" placeholder="Search" />
          <font-awesome-icon icon="fa-solid fa-magnifying-glass" style="color: darkgrey" />
        </div>
        <div class="date-filters">
          <div class="date-filter">
            <label for="startDate">From</label>
            <input type="date" id="startDate" v-model="startDateFormatted" @change="handleDateFilterChange">
          </div>
          <div class="date-filter">
            <label for="endDate">To</label>
            <input type="date" id="endDate" v-model="endDateFormatted" @change="handleDateFilterChange">
          </div>
        </div>
        <div class="button-popup-wrapper">
          <button class="header-button" id="toggleAdvancedFiltersButton" @click="toggleAdvancedFilters">
            <font-awesome-icon icon="fa-solid fa-filter" style="color: white" />
            <span> Advanced Filters </span>
          </button>
          <div id="advancedFiltersPopup" v-if="showAdvancedFilters" class="button-popup-container"
            style="width: 250px; left: -50px">
            <div class="filter-item">
              <label>Protocol</label>
              <select v-model="filters.protocol"
                @change="tabulatorInstance.filterTableData('protocol', filters.protocol)">
                <option :value="null">All Protocols</option>
                <option v-for="protocol in protocolsList" :key="protocol.id" :value="protocol.name">
                  {{ protocol.name }}
                </option>
              </select>
            </div>

            <div class="filter-item">
              <label>Analysis Type</label>
              <select v-model="filters.analysisType"
                @change="tabulatorInstance.filterTableData('analysisType', filters.analysisType)">
                <option :value="null">All Analysis Types</option>
                <option v-for="type in analysisTypesList" :key="type.id" :value="type.name">
                  {{ type.name }}
                </option>
              </select>
            </div>

            <div class="filter-item">
              <label>Sequencer</label>
              <select v-model="filters.sequencer"
                @change="tabulatorInstance.filterTableData('sequencer', filters.sequencer)">
                <option :value="null">All Sequencers</option>
                <option v-for="sequencer in sequencersList" :key="sequencer.id" :value="sequencer.name">
                  {{ sequencer.name }}
                </option>
              </select>
            </div>

            <div class="filter-item">
              <label>Read Length</label>
              <select v-model="filters.readLength"
                @change="tabulatorInstance.filterTableData('readLength', filters.readLength)">
                <option :value="null">All Read Lengths</option>
                <option v-for="length in readLengthsList" :key="length.id" :value="length.name">
                  {{ length.name }}
                </option>
              </select>
            </div>
            <button @click="resetAdvancedFilters" class="reset-button">
              Reset Filters
            </button>
          </div>
        </div>
        <div class="button-popup-wrapper">
          <button class="header-button" id="toggleSelectColumnsButton" @click="toggleSelectColumns">
            <font-awesome-icon icon="fa-solid fa-columns" style="color: white" />
            <span> Select Columns </span>
          </button>
          <div id="selectColumnsPopup" v-if="showSelectColumns" class="button-popup-container" style="
              left: -50px;
              width: 250px;
              padding-right: 8px;
              padding-top: 10px;
              padding-bottom: 10px;
            ">
            <ul style="
                padding-left: 0px;
                padding-right: 10px;
                max-height: 300px;
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
                    <input v-if="!column.columns" type="checkbox" :checked="column.visible"
                      @change="toggleColumnVisibility(column, true)" />
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
                    <span style="font-weight: bold">{{ column.title }}</span>
                  </label>
                  <ul v-if="column.columns" style="padding-left: 15px">
                    <li v-for="(subColumn, subIndex) in column.columns" :key="subIndex" style="list-style: none">
                      <label>
                        <input type="checkbox" style="width: 20px !important" :checked="subColumn.visible"
                          @change="toggleColumnVisibility(subColumn, false)" />
                        <span style="width: 100%">{{ subColumn.title }}</span>
                      </label>
                    </li>
                  </ul>
                </template>
              </li>
            </ul>
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
        groupBy="request_name" :groupSort="{ field: 'request_name', order: 'desc' }" :groupStartOpen="false"
        :tableOptions="{
          ...tableOptions,
          fakeLoadingStart,
          fakeLoadingStop
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
    <div v-if="showExportPopup" class="popup-overlay">
      <div class="popup-container" :style="{ width: '670px', height: '500px' }">
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
          <div>
            Select or upload additional excel sheet templates to append:
          </div>
          <div class="file-list-section">
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
} from "../utils/utilities";
const axiosRef = createAxiosObject();
const urlStringStart = urlStringStartsWith();

export default {
  name: "LibrariesAndSamples",
  components: {
    TabulatorTable
  },
  data() {
    const today = new Date();
    const sixMonthsAgo = new Date();
    sixMonthsAgo.setMonth(today.getMonth() - 6);
    return {
      tabulatorInstance: null,
      loading: true,
      fakeLoading: false,
      librariesSamplesList: [],
      columnsList: [],
      showPopupWindow: false,
      showExportPopup: false,
      showExportHelpTooltip: false,
      fetchedLibrariesAndSamplesTemplates: [],
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
          { column: "name", dir: "asc" },
          { column: "barcode", dir: "asc" }
        ],
        groupHeader: (value, count, data) => {
          const totalDepth = data.reduce(
            (sum, row) => sum + (row.sequencing_depth || 0),
            0
          );

          return `
  <div style="display: flex; justify-content: space-between; align-items: center; padding: 5px;">
<div style="display: flex; justify-content: space-between; align-items: center;">
  <div>
    <span style="font-weight: bold; font-size: 12px; color: #333;">${value}</span>
    <span style="font-weight: normal; font-size: 12px; margin-left: 2px; color: black;">
      (#: ${count}, Total Depth: ${totalDepth}M)
    </span>
  </div>
</div>
    <div class="group-action-buttons-container" style="position: sticky; gap: 5px;">
      <div title="Select All" class="group-action-button" onclick="handleGroupButtonClick(event, '${value}', 'selectAll')">
        <svg fill="none" width="24px" height="24px" version="1.1" xmlns="http://www.w3.org/2000/svg">
          <g>
            <path opacity="0.5" d="M21 12H12V3H15.024C19.9452 3 21 4.05476 21 8.976V12Z" fill="lightblue"/>
            <path opacity="0.5" d="M3 15.024V12H12V21H8.976C4.05476 21 3 19.9452 3 15.024Z" fill="lightblue"/>
            <path d="M3 8.976C3 4.05476 4.05476 3 8.976 3H15.024C19.9452 3 21 4.05476 21 8.976V15.024C21 19.9452 19.9452 21 15.024 21H8.976C4.05476 21 3 19.9452 3 15.024V8.976Z" stroke="#323232" stroke-width="1.8"/>
            <path d="M12 3V21" stroke="#323232" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M21 12L3 12" stroke="#323232" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
          </g>
        </svg>
      </div>
      <div title="Deselect All" class="group-action-button" onclick="handleGroupButtonClick(event, '${value}', 'deselectAll')">
        <svg fill="none" width="24px" height="24px" version="1.1" xmlns="http://www.w3.org/2000/svg">
          <g>
            <path opacity="0.5" d="M3 12C3 4.5885 4.5885 3 12 3C19.4115 3 21 4.5885 21 12C21 19.4115 19.4115 21 12 21C4.5885 21 3 19.4115 3 12Z" fill="lightblue"/>
            <path d="M3 12C3 4.5885 4.5885 3 12 3C19.4115 3 21 4.5885 21 12C21 19.4115 19.4115 21 12 21C4.5885 21 3 19.4115 3 12Z" stroke="#323232" stroke-width="1.8"/>
          </g>
        </svg>
      </div>
    </div>
  </div>
`;
        }
      },
      searchQuery: "",
      filters: {
        protocol: null,
        analysisType: null,
        sequencer: null,
        readLength: null
      },
      protocolsList: [],
      analysisTypesList: [],
      sequencersList: [],
      readLengthsList: [],
      startDate: sixMonthsAgo,
      endDate: today,
      showAdvancedFilters: false,
      showSelectColumns: false,
    };
  },
  computed: {
    startDateFormatted: {
      get() {
        return this.formatDateForInput(this.startDate);
      },
      set(value) {
        this.startDate = value ? new Date(value) : null;
      }
    },
    endDateFormatted: {
      get() {
        return this.formatDateForInput(this.endDate);
      },
      set(value) {
        this.endDate = value ? new Date(value) : null;
      }
    }
  },
  mounted() {
    this.getLibrariesSamples();
    this.setColumns();
    // this.fetchFilterOptions();
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
          "search_libraries_and_samples",
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
        // const params = {
        //   start_date: this.formatDisplayDate(this.startDate),
        //   end_date: this.formatDisplayDate(this.endDate)
        // };

        // let response = await axiosRef.get(
        //   urlStringStart + "/api/libraries_and_samples/",
        //   { params }
        // );
        // let response = await axiosRef.get(
        //   urlStringStart + "/api/libraries_and_samples/"
        // );
        // let fetchedRows = response.data?.children.map((element) => ({
        //   pk: element.pk || "",
        //   record_type: element.record_type || "",
        //   request_id: element.request || "",
        //   request_name: element.request_name || "",
        //   name: element.name || "",
        //   type: element.barcode ? element.barcode[2] || "" : "",
        //   barcode: element.record_type === "Sample" && element.barcode[2] === "L" ? element.barcode + "*" : element.barcode || "",
        //   nucleic_acid_type_name: element.nucleic_acid_type_name || "",
        //   library_protocol_name: element.library_protocol_name || "",
        //   analysis_type: element.analysis_type || "",
        //   measuring_unit: element.measuring_unit || "",
        //   measured_value: element.measured_value === 0 ? 0 : element.measured_value || "",
        //   starting_amount: element.starting_amount === 0 ? 0 : element.starting_amount || "",
        //   pcr_cycles: element.pcr_cycles === 0 ? 0 : element.pcr_cycles || "",
        //   input: element.measuring_value == null && element.measured_element == null
        //     ? "-"
        //     : element.measuring_unit === "concentration"
        //       ? `${element.measured_value === 0 ? 0 : element.measured_value || ""} ng/µl`
        //       : element.measuring_unit === "m"
        //         ? `${element.measured_value === 0 ? 0 : element.measured_value || ""} M`
        //         : element.measuring_unit !== "-"
        //           ? `${element.measured_value === 0 ? 0 : element.measured_value || ""} ${element.measuring_unit || "-"}`
        //           : `${element.measured_value === 0 ? 0 : element.measured_value || ""}`,
        //   mean_fragment_size: element.mean_fragment_size === 0 ? 0 : element.mean_fragment_size || "",
        //   sequencing_depth: element.sequencing_depth === 0 ? 0 : element.sequencing_depth || "",
        //   read_length: element.read_length === 0 ? 0 : element.read_length || "",
        //   gmo: element.gmo === null ? "" : element.gmo,
        //   pool: element.pool || "",
        //   pool_name: element.pool_name || "",
        //   status: element.status || "",
        //   status_text: {
        //     "-1": "Quality check failed",
        //     "-2": "Quality check compromised",
        //     "0": "Pending submission",
        //     "1": "Submission completed",
        //     "2": "Quality check approved",
        //     "3": "Library prepared",
        //     "4": "Library pooled",
        //     "5": "Sequencing",
        //     "6": "Delivered"
        //   }[element.status] || "-",
        //   concentration_library: element.concentration_library === 0 ? 0 : element.concentration_library || "",
        //   create_time: element.create_time
        //     ? (() => {
        //       const date = new Date(element.create_time);
        //       if (isNaN(date)) return "";
        //       const day = String(date.getDate()).padStart(2, "0");
        //       const month = String(date.getMonth() + 1).padStart(2, "0");
        //       const year = date.getFullYear();
        //       return `${day}.${month}.${year}`;
        //     })()
        //     : "",
        //   index_type: element.index_type || "",
        //   coordinate: element.coordinate || "",
        //   index_i7_id: element.index_i7_id || "",
        //   index_i5_id: element.index_i5_id || "",
        //   index_i7: element.index_i7 || "",
        //   index_i5: element.index_i5 || "",
        // }));
        let fetchedRows = [
          {
            "request_id": 3644,
            "request_name": "3644_Yoo_Cissé",
            "name": "H3K27ac",
            "type": "S",
            "barcode": "25S007986",
            "status": 1,
            "create_time": "2025-06-18T15:18:56.586777+02:00",
            "library_protocol": 22,
            "library_protocol_name": "ChIP RELACS high-throughput",
            "library_type": 3,
            "library_type_name": "ChIP-Seq",
            "organism": 14,
            "equal_representation_nucleotides": false,
            "concentration": 0,
            "concentration_method": 4,
            "read_length": 8,
            "read_length_name": "2x100",
            "sequencing_depth": 16,
            "comments": "",
            "amplification_cycles": 0,
            "organism_name": "M. musculus (GRCm39)",
            "pk": 25160,
            "record_type": "Sample",
            "is_converted": false,
            "rna_quality": null,
            "nucleic_acid_type": 10,
            "nucleic_acid_type_name": "fixed cell pellets",
            "leaf": true,
            "id": 29166
          },
          {
            "request_id": 3644,
            "request_name": "3644_Yoo_Cissé",
            "name": "Pol2_Ser2ph",
            "barcode": "25S007987",
            "type": "S",
            "status": 1,
            "create_time": "2025-06-18T15:18:56.593921+02:00",
            "library_protocol": 22,
            "library_protocol_name": "ChIP RELACS high-throughput",
            "library_type": 3,
            "library_type_name": "ChIP-Seq",
            "organism": 14,
            "equal_representation_nucleotides": false,
            "concentration": 0,
            "concentration_method": 4,
            "read_length": 8,
            "read_length_name": "2x100",
            "sequencing_depth": 16,
            "comments": "",
            "amplification_cycles": 0,
            "organism_name": "M. musculus (GRCm39)",
            "pk": 25161,
            "record_type": "Sample",
            "is_converted": false,
            "rna_quality": null,
            "nucleic_acid_type": 10,
            "nucleic_acid_type_name": "fixed cell pellets",
            "leaf": true,
            "id": 29167
          },
          {
            "request_id": 3644,
            "request_name": "3644_Yoo_Cissé",
            "name": "Pol2_Ser5ph",
            "barcode": "25S007988",
            "type": "S",
            "status": 1,
            "create_time": "2025-06-18T15:18:56.597499+02:00",
            "library_protocol": 22,
            "library_protocol_name": "ChIP RELACS high-throughput",
            "library_type": 3,
            "library_type_name": "ChIP-Seq",
            "organism": 14,
            "equal_representation_nucleotides": false,
            "concentration": 0,
            "concentration_method": 4,
            "read_length": 8,
            "read_length_name": "2x100",
            "sequencing_depth": 16,
            "comments": "",
            "amplification_cycles": 0,
            "organism_name": "M. musculus (GRCm39)",
            "pk": 25162,
            "record_type": "Sample",
            "is_converted": false,
            "rna_quality": null,
            "nucleic_acid_type": 10,
            "nucleic_acid_type_name": "fixed cell pellets",
            "leaf": true,
            "id": 29168
          },
          {
            "request_id": 3644,
            "request_name": "3644_Yoo_Cissé",
            "name": "CTCF",
            "barcode": "25S007989",
            "type": "S",
            "status": 1,
            "create_time": "2025-06-18T15:18:56.601884+02:00",
            "library_protocol": 22,
            "library_protocol_name": "ChIP RELACS high-throughput",
            "library_type": 3,
            "library_type_name": "ChIP-Seq",
            "organism": 14,
            "equal_representation_nucleotides": false,
            "concentration": 0,
            "concentration_method": 4,
            "read_length": 8,
            "read_length_name": "2x100",
            "sequencing_depth": 16,
            "comments": "",
            "amplification_cycles": 0,
            "organism_name": "M. musculus (GRCm39)",
            "pk": 25163,
            "record_type": "Sample",
            "is_converted": false,
            "rna_quality": null,
            "nucleic_acid_type": 10,
            "nucleic_acid_type_name": "fixed cell pellets",
            "leaf": true,
            "id": 29169
          },
          {
            "request_id": 3644,
            "request_name": "3644_Yoo_Cissé",
            "name": "Med1_poly",
            "type": "S",
            "barcode": "25S007990",
            "status": 1,
            "create_time": "2025-06-18T15:18:56.606885+02:00",
            "library_protocol": 22,
            "library_protocol_name": "ChIP RELACS high-throughput",
            "library_type": 3,
            "library_type_name": "ChIP-Seq",
            "organism": 14,
            "equal_representation_nucleotides": false,
            "concentration": 0,
            "concentration_method": 4,
            "read_length": 8,
            "read_length_name": "2x100",
            "sequencing_depth": 16,
            "comments": "",
            "amplification_cycles": 0,
            "organism_name": "M. musculus (GRCm39)",
            "pk": 25164,
            "record_type": "Sample",
            "is_converted": false,
            "rna_quality": null,
            "nucleic_acid_type": 10,
            "nucleic_acid_type_name": "fixed cell pellets",
            "leaf": true,
            "id": 29170
          },
          {
            "request_id": 3630,
            "request_name": "3630_Daviti_Denboba",
            "name": "Gen1_250327_18m",
            "barcode": "25L007475",
            "status": 5,
            "type": "L",
            "create_time": "2025-06-03T11:21:54.679276+02:00",
            "library_protocol": 69,
            "library_protocol_name": "Nanopore 16S Barcoding Kit (SQK-16S114)",
            "library_type": 29,
            "library_type_name": "Nanopore 16s Library",
            "organism": 14,
            "equal_representation_nucleotides": false,
            "concentration": 248.407,
            "concentration_method": 4,
            "read_length": 17,
            "read_length_name": "Oxford Nanopore",
            "sequencing_depth": 20,
            "comments": "",
            "amplification_cycles": 0,
            "organism_name": "M. musculus (GRCm39)",
            "pk": 24669,
            "record_type": "Sample",
            "is_converted": true,
            "rna_quality": null,
            "nucleic_acid_type": 16,
            "nucleic_acid_type_name": "DNA (genomic)",
            "leaf": true,
            "id": 28599
          },
          {
            "request_id": 3630,
            "request_name": "3630_Daviti_Denboba",
            "name": "Gen2_250327_18m",
            "barcode": "25L007476",
            "status": 5,
            "type": "L",
            "create_time": "2025-06-03T11:21:54.683927+02:00",
            "library_protocol": 69,
            "library_protocol_name": "Nanopore 16S Barcoding Kit (SQK-16S114)",
            "library_type": 29,
            "library_type_name": "Nanopore 16s Library",
            "organism": 14,
            "equal_representation_nucleotides": false,
            "concentration": 273.165,
            "concentration_method": 4,
            "read_length": 17,
            "read_length_name": "Oxford Nanopore",
            "sequencing_depth": 20,
            "comments": "",
            "amplification_cycles": 0,
            "organism_name": "M. musculus (GRCm39)",
            "pk": 24670,
            "record_type": "Sample",
            "is_converted": true,
            "rna_quality": null,
            "nucleic_acid_type": 16,
            "nucleic_acid_type_name": "DNA (genomic)",
            "leaf": true,
            "id": 28600
          },
          {
            "request_id": 3630,
            "request_name": "3630_Daviti_Denboba",
            "name": "Gen3_250327_18m",
            "barcode": "25L007477",
            "status": 5,
            "type": "L",
            "create_time": "2025-06-03T11:21:54.687225+02:00",
            "library_protocol": 69,
            "library_protocol_name": "Nanopore 16S Barcoding Kit (SQK-16S114)",
            "library_type": 29,
            "library_type_name": "Nanopore 16s Library",
            "organism": 14,
            "equal_representation_nucleotides": false,
            "concentration": 364.264,
            "concentration_method": 4,
            "read_length": 17,
            "read_length_name": "Oxford Nanopore",
            "sequencing_depth": 20,
            "comments": "",
            "amplification_cycles": 0,
            "organism_name": "M. musculus (GRCm39)",
            "pk": 24671,
            "record_type": "Sample",
            "is_converted": true,
            "rna_quality": null,
            "nucleic_acid_type": 16,
            "nucleic_acid_type_name": "DNA (genomic)",
            "leaf": true,
            "id": 28601
          },
          {
            "request_id": 3630,
            "request_name": "3630_Daviti_Denboba",
            "name": "Gen4_250327_18m",
            "barcode": "25L007478",
            "status": 5,
            "type": "L",
            "create_time": "2025-06-03T11:21:54.690452+02:00",
            "library_protocol": 69,
            "library_protocol_name": "Nanopore 16S Barcoding Kit (SQK-16S114)",
            "library_type": 29,
            "library_type_name": "Nanopore 16s Library",
            "organism": 14,
            "equal_representation_nucleotides": false,
            "concentration": 132.662,
            "concentration_method": 4,
            "read_length": 17,
            "read_length_name": "Oxford Nanopore",
            "sequencing_depth": 20,
            "comments": "",
            "amplification_cycles": 0,
            "organism_name": "M. musculus (GRCm39)",
            "pk": 24672,
            "record_type": "Sample",
            "is_converted": true,
            "rna_quality": null,
            "nucleic_acid_type": 16,
            "nucleic_acid_type_name": "DNA (genomic)",
            "leaf": true,
            "id": 28602
          },
          {
            "request_id": 3630,
            "request_name": "3630_Daviti_Denboba",
            "name": "Gen5_250327_18m",
            "barcode": "25L007479",
            "status": 5,
            "type": "L",
            "create_time": "2025-06-03T11:21:54.693696+02:00",
            "library_protocol": 69,
            "library_protocol_name": "Nanopore 16S Barcoding Kit (SQK-16S114)",
            "library_type": 29,
            "library_type_name": "Nanopore 16s Library",
            "organism": 14,
            "equal_representation_nucleotides": false,
            "concentration": 196.321,
            "concentration_method": 4,
            "read_length": 17,
            "read_length_name": "Oxford Nanopore",
            "sequencing_depth": 20,
            "comments": "",
            "amplification_cycles": 0,
            "organism_name": "M. musculus (GRCm39)",
            "pk": 24673,
            "record_type": "Sample",
            "is_converted": true,
            "rna_quality": null,
            "nucleic_acid_type": 16,
            "nucleic_acid_type_name": "DNA (genomic)",
            "leaf": true,
            "id": 28603
          },
          {
            "request_id": 3630,
            "request_name": "3630_Daviti_Denboba",
            "name": "Control1_250327_18m",
            "barcode": "25L007480",
            "status": 5,
            "type": "L",
            "create_time": "2025-06-03T11:21:54.696946+02:00",
            "library_protocol": 69,
            "library_protocol_name": "Nanopore 16S Barcoding Kit (SQK-16S114)",
            "library_type": 29,
            "library_type_name": "Nanopore 16s Library",
            "organism": 14,
            "equal_representation_nucleotides": false,
            "concentration": 312.388,
            "concentration_method": 4,
            "read_length": 17,
            "read_length_name": "Oxford Nanopore",
            "sequencing_depth": 20,
            "comments": "",
            "amplification_cycles": 0,
            "organism_name": "M. musculus (GRCm39)",
            "pk": 24674,
            "record_type": "Sample",
            "is_converted": true,
            "rna_quality": null,
            "nucleic_acid_type": 16,
            "nucleic_acid_type_name": "DNA (genomic)",
            "leaf": true,
            "id": 28604
          },
          {
            "request_id": 3630,
            "request_name": "3630_Daviti_Denboba",
            "name": "Control2_250327_18m",
            "barcode": "25L007481",
            "status": 5,
            "type": "L",
            "create_time": "2025-06-03T11:21:54.700724+02:00",
            "library_protocol": 69,
            "library_protocol_name": "Nanopore 16S Barcoding Kit (SQK-16S114)",
            "library_type": 29,
            "library_type_name": "Nanopore 16s Library",
            "organism": 14,
            "equal_representation_nucleotides": false,
            "concentration": 138.357,
            "concentration_method": 4,
            "read_length": 17,
            "read_length_name": "Oxford Nanopore",
            "sequencing_depth": 20,
            "comments": "",
            "amplification_cycles": 0,
            "organism_name": "M. musculus (GRCm39)",
            "pk": 24675,
            "record_type": "Sample",
            "is_converted": true,
            "rna_quality": null,
            "nucleic_acid_type": 16,
            "nucleic_acid_type_name": "DNA (genomic)",
            "leaf": true,
            "id": 28605
          },
          {
            "request_id": 3630,
            "request_name": "3630_Daviti_Denboba",
            "name": "Control3_250328_18m",
            "barcode": "25L007482",
            "status": 5,
            "type": "L",
            "create_time": "2025-06-03T11:21:54.704316+02:00",
            "library_protocol": 69,
            "library_protocol_name": "Nanopore 16S Barcoding Kit (SQK-16S114)",
            "library_type": 29,
            "library_type_name": "Nanopore 16s Library",
            "organism": 14,
            "equal_representation_nucleotides": false,
            "concentration": 143.656,
            "concentration_method": 4,
            "read_length": 17,
            "read_length_name": "Oxford Nanopore",
            "sequencing_depth": 20,
            "comments": "",
            "amplification_cycles": 0,
            "organism_name": "M. musculus (GRCm39)",
            "pk": 24676,
            "record_type": "Sample",
            "is_converted": true,
            "rna_quality": null,
            "nucleic_acid_type": 16,
            "nucleic_acid_type_name": "DNA (genomic)",
            "leaf": true,
            "id": 28606
          },
          {
            "request_id": 3630,
            "request_name": "3630_Daviti_Denboba",
            "name": "Control4_250329_18m",
            "barcode": "25L007483",
            "status": 5,
            "type": "L",
            "create_time": "2025-06-03T11:21:54.707901+02:00",
            "library_protocol": 69,
            "library_protocol_name": "Nanopore 16S Barcoding Kit (SQK-16S114)",
            "library_type": 29,
            "library_type_name": "Nanopore 16s Library",
            "organism": 14,
            "equal_representation_nucleotides": false,
            "concentration": 213.534,
            "concentration_method": 4,
            "read_length": 17,
            "read_length_name": "Oxford Nanopore",
            "sequencing_depth": 20,
            "comments": "",
            "amplification_cycles": 0,
            "organism_name": "M. musculus (GRCm39)",
            "pk": 24677,
            "record_type": "Sample",
            "is_converted": true,
            "rna_quality": null,
            "nucleic_acid_type": 16,
            "nucleic_acid_type_name": "DNA (genomic)",
            "leaf": true,
            "id": 28607
          },
          {
            "request_id": 3630,
            "request_name": "3630_Daviti_Denboba",
            "name": "Control5_250330_18m",
            "barcode": "25L007484",
            "status": 5,
            "type": "L",
            "create_time": "2025-06-03T11:21:54.711273+02:00",
            "library_protocol": 69,
            "library_protocol_name": "Nanopore 16S Barcoding Kit (SQK-16S114)",
            "library_type": 29,
            "library_type_name": "Nanopore 16s Library",
            "organism": 14,
            "equal_representation_nucleotides": false,
            "concentration": 134.454,
            "concentration_method": 4,
            "read_length": 17,
            "read_length_name": "Oxford Nanopore",
            "sequencing_depth": 20,
            "comments": "",
            "amplification_cycles": 0,
            "organism_name": "M. musculus (GRCm39)",
            "pk": 24678,
            "record_type": "Sample",
            "is_converted": true,
            "rna_quality": null,
            "nucleic_acid_type": 16,
            "nucleic_acid_type_name": "DNA (genomic)",
            "leaf": true,
            "id": 28608
          },
          {
            "request_id": 3630,
            "request_name": "3630_Daviti_Denboba",
            "name": "Old1_250327",
            "barcode": "25L007485",
            "status": 5,
            "type": "L",
            "create_time": "2025-06-03T11:21:54.714763+02:00",
            "library_protocol": 69,
            "library_protocol_name": "Nanopore 16S Barcoding Kit (SQK-16S114)",
            "library_type": 29,
            "library_type_name": "Nanopore 16s Library",
            "organism": 14,
            "equal_representation_nucleotides": false,
            "concentration": 307.688,
            "concentration_method": 4,
            "read_length": 17,
            "read_length_name": "Oxford Nanopore",
            "sequencing_depth": 20,
            "comments": "",
            "amplification_cycles": 0,
            "organism_name": "M. musculus (GRCm39)",
            "pk": 24679,
            "record_type": "Sample",
            "is_converted": true,
            "rna_quality": null,
            "nucleic_acid_type": 16,
            "nucleic_acid_type_name": "DNA (genomic)",
            "leaf": true,
            "id": 28609
          },
          {
            "request_id": 3630,
            "request_name": "3630_Daviti_Denboba",
            "name": "Old2_250327",
            "barcode": "25L007486",
            "status": 5,
            "type": "L",
            "create_time": "2025-06-03T11:21:54.718175+02:00",
            "library_protocol": 69,
            "library_protocol_name": "Nanopore 16S Barcoding Kit (SQK-16S114)",
            "library_type": 29,
            "library_type_name": "Nanopore 16s Library",
            "organism": 14,
            "equal_representation_nucleotides": false,
            "concentration": 249.771,
            "concentration_method": 4,
            "read_length": 17,
            "read_length_name": "Oxford Nanopore",
            "sequencing_depth": 20,
            "comments": "",
            "amplification_cycles": 0,
            "organism_name": "M. musculus (GRCm39)",
            "pk": 24680,
            "record_type": "Sample",
            "is_converted": true,
            "rna_quality": null,
            "nucleic_acid_type": 16,
            "nucleic_acid_type_name": "DNA (genomic)",
            "leaf": true,
            "id": 28610
          },
          {
            "request_id": 3630,
            "request_name": "3630_Daviti_Denboba",
            "name": "Old3_250327",
            "barcode": "25L007487",
            "status": 5,
            "type": "L",
            "create_time": "2025-06-03T11:21:54.721364+02:00",
            "library_protocol": 69,
            "library_protocol_name": "Nanopore 16S Barcoding Kit (SQK-16S114)",
            "library_type": 29,
            "library_type_name": "Nanopore 16s Library",
            "organism": 14,
            "equal_representation_nucleotides": false,
            "concentration": 237.768,
            "concentration_method": 4,
            "read_length": 17,
            "read_length_name": "Oxford Nanopore",
            "sequencing_depth": 20,
            "comments": "",
            "amplification_cycles": 0,
            "organism_name": "M. musculus (GRCm39)",
            "pk": 24681,
            "record_type": "Sample",
            "is_converted": true,
            "rna_quality": null,
            "nucleic_acid_type": 16,
            "nucleic_acid_type_name": "DNA (genomic)",
            "leaf": true,
            "id": 28611
          },
          {
            "request_id": 3630,
            "request_name": "3630_Daviti_Denboba",
            "name": "Young1_250327",
            "barcode": "25L007488",
            "status": 5,
            "type": "L",
            "create_time": "2025-06-03T11:21:54.724565+02:00",
            "library_protocol": 69,
            "library_protocol_name": "Nanopore 16S Barcoding Kit (SQK-16S114)",
            "library_type": 29,
            "library_type_name": "Nanopore 16s Library",
            "organism": 14,
            "equal_representation_nucleotides": false,
            "concentration": 322.585,
            "concentration_method": 4,
            "read_length": 17,
            "read_length_name": "Oxford Nanopore",
            "sequencing_depth": 20,
            "comments": "",
            "amplification_cycles": 0,
            "organism_name": "M. musculus (GRCm39)",
            "pk": 24682,
            "record_type": "Sample",
            "is_converted": true,
            "rna_quality": null,
            "nucleic_acid_type": 16,
            "nucleic_acid_type_name": "DNA (genomic)",
            "leaf": true,
            "id": 28612
          },
          {
            "request_id": 3630,
            "request_name": "3630_Daviti_Denboba",
            "name": "Young2_250327",
            "barcode": "25L007489",
            "status": 5,
            "type": "L",
            "create_time": "2025-06-03T11:21:54.728066+02:00",
            "library_protocol": 69,
            "library_protocol_name": "Nanopore 16S Barcoding Kit (SQK-16S114)",
            "library_type": 29,
            "library_type_name": "Nanopore 16s Library",
            "organism": 14,
            "equal_representation_nucleotides": false,
            "concentration": 302.513,
            "concentration_method": 4,
            "read_length": 17,
            "read_length_name": "Oxford Nanopore",
            "sequencing_depth": 20,
            "comments": "",
            "amplification_cycles": 0,
            "organism_name": "M. musculus (GRCm39)",
            "pk": 24683,
            "record_type": "Sample",
            "is_converted": true,
            "rna_quality": null,
            "nucleic_acid_type": 16,
            "nucleic_acid_type_name": "DNA (genomic)",
            "leaf": true,
            "id": 28613
          }
        ];
        this.librariesSamplesList = fetchedRows;
      } catch (error) {
        handleError(error);
      } finally {
        this.loading = false;
      }
    },
    async fetchFilterOptions() {
      try {
        const protocolsRes = await axiosRef.get(`${urlStringStart}/api/library_protocols/`);
        this.protocolsList = protocolsRes.data;
        const analysisRes = await axiosRef.get(`${urlStringStart}/api/analysis_types/`);
        this.analysisTypesList = analysisRes.data;
        const sequencersRes = await axiosRef.get(`${urlStringStart}/api/sequencers/`);
        this.sequencersList = sequencersRes.data;
        const readLengthsRes = await axiosRef.get(`${urlStringStart}/api/read_lengths/`);
        this.readLengthsList = readLengthsRes.data;
      } catch (error) {
        handleError(error);
      }
    },
    resetAdvancedFilters() {
      this.filters = {
        protocol: null,
        analysisType: null,
        sequencer: null,
        readLength: null
      };
      this.tabulatorInstance.filterTableData("resetAdvancedFilters", true);
    },
    setColumns() {
      const storedColumnState = JSON.parse(
        localStorage.getItem("librariesAndSamplesColumnSettings")
      );

      let columnList = [
        {
          field: "selected",
          visible: true,
          headerVertical: false,
          frozen: true,
          resizable: false,
          formatter: (cell) => {
            const rowData = cell.getRow().getData();
            const checkbox = `
              <input
                type="checkbox"
                title="Select"
                style="top:-4px"
                ${rowData.selected ? "checked" : ""}
              />
            `;
            return checkbox;
          },
          hozAlign: "center",
          width: 30,
          minWidth: 30,
          cssClass: "checkbox-column right-border",
          contextMenu: () => this.cellContextMenu(false, false, false),
          cellClick: function (e, cell) {
            const row = cell.getRow();
            const rowData = row.getData();
            const checkbox = e.target;
            if (checkbox && checkbox.type === "checkbox") {
              rowData.selected = checkbox.checked;
            }
          }
        },
        {
          title: "Name",
          field: "name",
          minWidth: 140,
          headerFilter: true,
          headerTooltip: "Name",
          visible: true,
          frozen: true,
          cssClass: "right-border",
          contextMenu: () => this.cellContextMenu(true, false, false),
          cellDblClick: function (e, cell) {
            showNotification("This field is not editable.", "warning");
          },
          formatter: (cell) => {
            const request_name = cell.getRow().getData().request_name;
            const name = cell.getValue();
            const tableGroupsToggleState =
              this.tabulatorInstance.getTableGroupsToggleState();
            return `
                        <div style="padding: 4px 12px; display: flex; align-items: center;">
                          <span title="${name}" style="padding: 8px 0px; overflow: hidden; white-space: nowrap; text-overflow: ellipsis;">${(tableGroupsToggleState == 2
                ? request_name + " ➜ "
                : "") + name
              }</span>
                        </div>
                      `;
          }
        },
        {
          title: "Status",
          field: "status",
          width: 50,
          headerFilter: true,
          headerTooltip: "Status",
          visible: true,
          frozen: true,
          cssClass: "right-border",
          contextMenu: () => this.cellContextMenu(true, false, false),
          cellDblClick: function (e, cell) {
            showNotification("This field is not editable.", "warning");
          },
          formatter: (cell) => {
            const value = cell.getValue();
            let statusClass = "status ";
            let tooltip = "";

            switch (value) {
              case -1:
                statusClass += "quality-check-failed";
                tooltip = "Quality check failed";
                break;
              case -2:
                statusClass += "quality-check-compromised";
                tooltip = "Quality check compromised";
                break;
              case 0:
                statusClass += "pending-submission";
                tooltip = "Pending submission";
                break;
              case 1:
                statusClass += "submission-completed";
                tooltip = "Submission completed";
                break;
              case 2:
                statusClass += "quality-check-approved";
                tooltip = "Quality check approved";
                break;
              case 3:
                statusClass += "library-prepared";
                tooltip = "Library prepared";
                break;
              case 4:
                statusClass += "library-pooled";
                tooltip = "Library pooled";
                break;
              case 5:
                statusClass += "sequencing";
                tooltip = "Sequencing";
                break;
              case 6:
                statusClass += "delivered";
                tooltip = "Delivered";
                break;
              default:
                return "";
            }

            return `<div class="${statusClass}" title="${tooltip}"></div>`;
          }
        },
        {
          title: "S/L",
          field: "type",
          width: 30,
          minWidth: 30,
          headerFilter: true,
          headerTooltip: "Type",
          visible: true,
          frozen: true,
          cssClass: "right-border",
          contextMenu: () => this.cellContextMenu(true, false, false),
          cellDblClick: function (e, cell) {
            showNotification("This field is not editable.", "warning");
          },
          formatter: (cell) => {
            const value = cell.getValue();
            const finalString = value || "-";
            return this.ellipsisContainer(finalString, false);
          }
        },
        {
          title: "Barcode",
          field: "barcode",
          width: 90,
          minWidth: 60,
          headerFilter: true,
          headerTooltip: "Barcode",
          visible: true,
          frozen: true,
          cssClass: "right-border",
          contextMenu: () => this.cellContextMenu(true, false, false),
          cellDblClick: function (e, cell) {
            showNotification("This field is not editable.", "warning");
          },
          formatter: (cell) => {
            const value = cell.getValue();
            const finalString = value || "-";
            return this.ellipsisContainer(finalString, false);
          }
        },
        {
          title: "Pool Paths",
          field: "pool_paths",
          width: 85,
          minWidth: 60,
          headerFilter: true,
          headerTooltip: "Pool Paths",
          visible: true,
          cssClass: "regular-column",
          contextMenu: () => this.cellContextMenu(true, false, false),
          cellDblClick: function (e, cell) {
            showNotification("This field is not editable.", "warning");
          },
          formatter: (cell) => {
            const value = cell.getValue();
            const finalString = value || "-";
            return this.ellipsisContainer(finalString, false);
          }
        },
        {
          title: "GMO",
          field: "gmo",
          width: 85,
          minWidth: 60,
          headerFilter: true,
          headerTooltip: "Genetically Modified Organism",
          visible: true,
          cssClass: "regular-column",
          contextMenu: () => this.cellContextMenu(true, false, false),
          cellDblClick: function (e, cell) {
            showNotification("This field is not editable.", "warning");
          },
          formatter: (cell) => {
            const value = cell.getValue();
            const options = {
              false: "Not Needed",
              true: "Risk Assessment Done"
            };
            const finalString = options[value] || value || "-";
            return this.ellipsisContainer(finalString);
          }
        },
        {
          title: "Date",
          field: "create_time",
          width: 90,
          minWidth: 60,
          headerFilter: true,
          headerTooltip: "Date",
          visible: true,
          cssClass: "regular-column",
          contextMenu: () => this.cellContextMenu(true, false, false),
          cellDblClick: function (e, cell) {
            showNotification("This field is not editable.", "warning");
          },
          formatter: (cell) => {
            const value = cell.getValue();
            const finalString = value || "-";
            return this.ellipsisContainer(finalString);
          }
        },
        {
          title: "Input Type",
          field: "nucleic_acid_type_name",
          minWidth: 80,
          width: "5%",
          headerVertical: false,
          headerFilter: true,
          headerTooltip: "Input Type",
          visible: true,
          cssClass: "regular-column",
          contextMenu: () => this.cellContextMenu(true, false, false),
          formatter: (cell) => {
            const value = cell.getValue();
            const finalString = value || "No Input Type";
            return this.ellipsisContainer(finalString);
          },
          cellDblClick: function (e, cell) {
            showNotification("This field is not editable.", "warning");
          }
        },
        {
          title: "Protocol",
          field: "library_protocol_name",
          minWidth: 80,
          width: "5%",
          visible: true,
          headerFilter: true,
          cssClass: "regular-column",
          headerTooltip: "Library Preparation Protocol",
          contextMenu: () => this.cellContextMenu(true, false, false),
          cellDblClick: function (e, cell) {
            showNotification("This field is not editable.", "warning");
          },
          formatter: (cell) => {
            const value = cell.getValue();
            const finalString = value || "No Protocol";
            return this.ellipsisContainer(finalString);
          }
        },
        {
          title: "Analysis Type",
          field: "analysis_type",
          minWidth: 80,
          width: "5%",
          visible: true,
          headerFilter: true,
          cssClass: "regular-column",
          headerTooltip: "Analysis Type",
          contextMenu: () => this.cellContextMenu(true, false, false),
          cellDblClick: function (e, cell) {
            showNotification("This field is not editable.", "warning");
          },
          formatter: (cell) => {
            const value = cell.getValue();
            const finalString = value || "No Analysis Type";
            return this.ellipsisContainer(finalString);
          }
        },
        {
          title: "Input",
          field: "input",
          minWidth: 60,
          width: "3.5%",
          headerVertical: false,
          headerFilter: true,
          headerTooltip: "Measured Amount with Unit",
          visible: true,
          cssClass: "regular-column",
          contextMenu: () => this.cellContextMenu(true, false, false),
          cellDblClick: function (e, cell) {
            showNotification("This field is not editable.", "warning");
          },
          formatter: (cell) => {
            const value = cell.getValue();
            const finalString = value || "-";
            return this.ellipsisContainer(finalString);
          }
        },
        {
          title: "Starting Amount",
          field: "starting_amount",
          minWidth: 60,
          width: "3.5%",
          headerVertical: false,
          headerTooltip: "Starting Amount (ng or fmol)",
          visible: true,
          cssClass: "regular-column",
          contextMenu: () => this.cellContextMenu(true, false, false),
          cellDblClick: function (e, cell) {
            showNotification("This field is not editable.", "warning");
          },
          formatter: (cell) => {
            const rawValue = cell.getValue();
            const value = Number(rawValue);
            const finalString =
              rawValue === "" || rawValue === undefined || isNaN(value)
                ? "-"
                : value === 0
                  ? "0.0"
                  : value.toFixed(1);
            return this.ellipsisContainer(finalString);
          }
        },
        {
          title: "Cycles",
          field: "pcr_cycles",
          minWidth: 60,
          width: "3.5%",
          headerVertical: false,
          headerTooltip: "PCR Cycles",
          visible: true,
          cssClass: "regular-column",
          contextMenu: () => this.cellContextMenu(true, false, false),
          cellDblClick: function (e, cell) {
            showNotification("This field is not editable.", "warning");
          },
          formatter: (cell) => {
            const rawValue = cell.getValue();
            const value = Number(rawValue);
            let finalString;

            if (rawValue === "" || rawValue === undefined || isNaN(value)) {
              finalString = "-";
            } else {
              finalString = Math.round(value).toString();
            }

            return this.ellipsisContainer(finalString);
          }
        },
        {
          title: "ng/µl",
          field: "concentration_library",
          minWidth: 60,
          width: "3.5%",
          headerVertical: false,
          headerTooltip: "Concentration Library (ng/µl)",
          visible: true,
          cssClass: "regular-column",
          contextMenu: () => this.cellContextMenu(true, false, false),
          formatter: (cell) => {
            const rawValue = cell.getValue();
            const value = Number(rawValue);
            const finalString =
              rawValue === "" || rawValue === undefined || isNaN(value)
                ? "-"
                : value === 0
                  ? "0.0"
                  : value.toFixed(1);
            return this.ellipsisContainer(finalString);
          }
        },
        {
          title: "bp",
          field: "mean_fragment_size",
          minWidth: 60,
          width: "3.5%",
          headerVertical: false,
          headerTooltip: "Library Average Fragment Size",
          visible: true,
          cssClass: "regular-column",
          contextMenu: () => this.cellContextMenu(true, false, false),
          formatter: (cell) => {
            const rawValue = cell.getValue();
            const value = Number(rawValue);
            let finalString;

            if (rawValue === "" || rawValue === undefined || isNaN(value)) {
              finalString = "-";
            } else {
              finalString = Math.round(value).toString();
            }

            return this.ellipsisContainer(finalString);
          },
          cellDblClick: function (e, cell) {
            showNotification("This field is not editable.", "warning");
          }
        },
        {
          title: "Index Type",
          field: "index_type",
          minWidth: 60,
          width: "4%",
          headerVertical: false,
          headerTooltip: "Index Type",
          visible: true,
          cssClass: "regular-column",
          contextMenu: () => this.cellContextMenu(true, false, false),
          formatter: (cell) => {
            const finalString = cell.getValue() || "-";
            return this.ellipsisContainer(finalString);
          },
          cellDblClick: function (e, cell) {
            showNotification("This field is not editable.", "warning");
          }
        },
        {
          title: "Coord",
          field: "coordinate",
          minWidth: 60,
          width: "3.5%",
          headerVertical: false,
          headerTooltip: "Index Pair Coordinate",
          visible: true,
          cssClass: "regular-column",
          contextMenu: () => this.cellContextMenu(true, false, false),
          formatter: (cell) => {
            const finalString = cell.getValue() || "-";
            return this.ellipsisContainer(finalString);
          },
          cellDblClick: function (e, cell) {
            showNotification("This field is not editable.", "warning");
          }
        },
        {
          title: "I7 ID",
          field: "index_i7_id",
          minWidth: 60,
          width: "3.5%",
          headerVertical: false,
          headerTooltip: "Index I7 ID",
          visible: true,
          cssClass: "regular-column",
          contextMenu: () => this.cellContextMenu(true, false, false),
          formatter: (cell) => {
            const finalString = cell.getValue() || "-";
            return this.ellipsisContainer(finalString);
          },
          cellDblClick: function (e, cell) {
            showNotification("This field is not editable.", "warning");
          }
        },
        {
          title: "Index I7",
          field: "index_i7",
          minWidth: 60,
          width: "3.5%",
          headerVertical: false,
          headerTooltip: "Index I7 ID",
          visible: true,
          cssClass: "regular-column",
          contextMenu: () => this.cellContextMenu(true, false, false),
          formatter: (cell) => {
            const finalString = cell.getValue() || "-";
            return this.ellipsisContainer(finalString);
          },
          cellDblClick: function (e, cell) {
            showNotification("This field is not editable.", "warning");
          }
        },
        {
          title: "I5 ID",
          field: "index_i5_id",
          minWidth: 60,
          width: "3.5%",
          headerVertical: false,
          headerTooltip: "Index I5 ID",
          visible: true,
          cssClass: "regular-column",
          contextMenu: () => this.cellContextMenu(true, false, false),
          formatter: (cell) => {
            const finalString = cell.getValue() || "-";
            return this.ellipsisContainer(finalString);
          },
          cellDblClick: function (e, cell) {
            showNotification("This field is not editable.", "warning");
          }
        },
        {
          title: "Index I5",
          field: "index_i5",
          minWidth: 60,
          width: "3.5%",
          headerVertical: false,
          headerTooltip: "Index I5 ID",
          visible: true,
          cssClass: "regular-column",
          contextMenu: () => this.cellContextMenu(true, false, false),
          formatter: (cell) => {
            const finalString = cell.getValue() || "-";
            return this.ellipsisContainer(finalString);
          },
          cellDblClick: function (e, cell) {
            showNotification("This field is not editable.", "warning");
          }
        },
        {
          title: "Length",
          field: "read_length",
          minWidth: 60,
          width: "3.5%",
          headerVertical: false,
          headerTooltip: "Read Length",
          visible: true,
          cssClass: "regular-column",
          contextMenu: () => this.cellContextMenu(true, false, false),
          formatter: (cell) => {
            const rawValue = cell.getValue();
            const value = Number(rawValue);
            let finalString;
            if (rawValue === "" || rawValue === undefined || isNaN(value)) {
              finalString = "-";
            } else {
              finalString = Math.round(value).toString();
            }
            return this.ellipsisContainer(finalString);
          }
        },
        {
          title: "Depth (M)",
          field: "sequencing_depth",
          minWidth: 60,
          width: "3.5%",
          headerVertical: false,
          headerTooltip: "Sequencing Depth (M)",
          visible: true,
          cssClass: "regular-column",
          contextMenu: () => this.cellContextMenu(true, false, false),
          formatter: (cell) => {
            const rawValue = cell.getValue();
            const value = Number(rawValue);
            let finalString;
            if (rawValue === "" || rawValue === undefined || isNaN(value)) {
              finalString = "-";
            } else {
              finalString = Math.round(value).toString();
            }
            return this.ellipsisContainer(finalString);
          }
        },
      ];

      // if (storedColumnState) {
      //   storedColumnState.forEach((column, index) => {
      //     if (columnList[index]) columnList[index].visible = column.visible;
      //     if (column.columns) {
      //       column.columns.forEach((subColumn, subIndex) => {
      //         if (columnList[index])
      //           columnList[index].columns[subIndex].visible = subColumn.visible;
      //       });
      //     }
      //   });
      // }

      this.columnsList = columnList;
    },
    cellContextMenu(allowCopy, allowPaste, allowApplyToAll) {
      const operations = [];
      let isRangeSelected = false;
      let selectedRangesData = this.tabulatorInstance
        .getTable()
        .getRangesData();
      if (selectedRangesData.length > 0) {
        let firstRangeFields = Object.keys(selectedRangesData[0][0]);
        isRangeSelected =
          selectedRangesData[0].length > 1 || firstRangeFields.length > 1;
      }

      if (isRangeSelected) {
        showNotification(
          "Please use Ctrl+C to copy, and Ctrl+V to paste in a range selection.",
          "info"
        );
      } else {
        if (allowApplyToAll) {
          operations.push({
            label: "Apply to All",
            action: (e, cell) => {
              const value = cell.getValue();
              const field = cell.getField();
              const libraryProtocolName = cell
                .getRow()
                .getData().library_protocol_name;
              this.tabulatorInstance
                .getTable()
                .getRows()
                .forEach((row) => {
                  if (
                    row.getData().library_protocol_name === libraryProtocolName
                  ) {
                    const targetCell = row.getCell(field);
                    if (
                      !targetCell
                        .getElement()
                        .classList.contains("disable-editing")
                    ) {
                      targetCell.setValue(value);
                    }
                  }
                });
            }
          });
        }

        if (allowCopy) {
          operations.push({
            label: "Copy",
            action: (e, cell) => {
              const value = cell.getValue();
              navigator.clipboard.writeText(value);
            }
          });
        }

        if (allowPaste) {
          operations.push({
            label: "Paste",
            action: (e, cell) => {
              if (cell.getElement().classList.contains("disable-editing")) {
                return;
              }
              navigator.clipboard.readText().then((text) => {
                try {
                  const columnDef = cell.getColumn().getDefinition();
                  const rowData = cell.getRow().getData();
                  const validatedValue =
                    this.tabulatorInstance.validateCellValue(
                      text,
                      columnDef,
                      rowData
                    );
                  cell.setValue(validatedValue);
                } catch (error) {
                  showNotification(error.message, "error");
                }
              });
            }
          });
        }
      }

      return operations.length ? operations : [];
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
    },
    handleKeyDown(event) {
      const isEscape = event.key === "Escape";
      if (isEscape && this.showPopupWindow) {
        this.showPopupWindow = false;
        return;
      }
      if (isEscape && this.showExportPopup) {
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
    formatDateForInput(date) {
      if (!date) return '';
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      return `${year}-${month}-${day}`;
    },

    formatDisplayDate(date) {
      if (!date) return '';
      const day = String(date.getDate()).padStart(2, '0');
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const year = date.getFullYear();
      return `${day}.${month}.${year}`;
    },

    handleDateFilterChange() {
      if (this.startDate && this.endDate && this.startDate > this.endDate) {
        showNotification("Please enter a valid date range.", "warning");
        const temp = this.startDate;
        this.startDate = this.endDate;
        this.endDate = temp;
        return;
      }
      else
        this.getLibrariesSamples();
    },
    toggleAdvancedFilters() {
      this.showAdvancedFilters = !this.showAdvancedFilters;
      if (this.showAdvancedFilters) {
        this.showSelectColumns = false;
      }
    },
    toggleSelectColumns() {
      this.showSelectColumns = !this.showSelectColumns;
    },
    toggleColumnVisibility(column, isMainColumn) {
      this.fakeLoadingStart();
      let updatedColumns;

      if (isMainColumn) {
        updatedColumns = this.columnsList.map((col) => {
          return {
            ...col,
            visible: col === column ? !col.visible : col.visible
          };
        });
      } else {
        updatedColumns = this.columnsList.map((col) => {
          if (col.columns) {
            return {
              ...col,
              columns: col.columns.map((subCol) => ({
                ...subCol,
                visible: subCol === column ? !subCol.visible : subCol.visible
              }))
            };
          } else return col;
        });
      }

      localStorage.setItem(
        "librariesAndSamplesColumnSettings",
        JSON.stringify(updatedColumns)
      );
      this.columnsList = updatedColumns;
      this.fakeLoadingStop();
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
            const data = row.getData();
            if (
              data.record_type === "Sample" &&
              (data.status === 2 || data.status === -2)
            ) {
              return;
            }
            data.selected = true;
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
            const data = row.getData();
            if (
              data.record_type === "Sample" &&
              (data.status === 2 || data.status === -2)
            ) {
              return;
            }
            data.selected = false;
            row.update({});
            const rowElement = row.getElement();
            const checkbox = rowElement.querySelector('input[type="checkbox"]');
            if (checkbox) {
              checkbox.checked = false;
            }
          });
          if (!group._group.visible) groupElement.click();
          break;
      }
    },
    async fetchExportTemplates() {
      try {
        const response = await axiosRef.get(
          `${urlStringStart}/api/libraries-and-samples-templates/`
        );
        this.fetchedLibrariesAndSamplesTemplates = response.data;
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
            `${urlStringStart}/api/libraries-and-samples-templates/upload/`,
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
          `${urlStringStart}/api/libraries-and-samples-templates/${file.id}/download/`,
          {
            responseType: "blob"
          }
        );
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement("a");
        link.href = url;
        link.setAttribute("download", file.name || "LibrariesAndSamples.xlsx");
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
      } catch (error) {
        showNotification("Error downloading file: " + error, "error");
      }
    },
    async removeExportTemplate(index) {
      const file = this.fetchedLibrariesAndSamplesTemplates[index];
      try {
        await axiosRef.delete(
          `${urlStringStart}/api/libraries-and-samples-templates/${file.id}/remove/`
        );
        this.fetchedLibrariesAndSamplesTemplates.splice(index, 1);
        showNotification("File removed successfully.", "success");
      } catch (error) {
        showNotification("Error removing file: " + error, "error");
      } finally {
        this.selectedFile = "without-file";
      }
    },
    handleExportClick() {
      const selectedRows = this.librariesSamplesList.filter(
        (row) => row.selected
      );
      if (selectedRows.length === 0) {
        showNotification(
          "Please select at least one library/sample to export.",
          "warning"
        );
      } else {
        this.showExportPopup = true;
      }
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
          const aNum = getRequestNum(a.request_name);
          const bNum = getRequestNum(b.request_name);
          if (aNum !== bNum) return aNum - bNum;
          return a.barcode?.localeCompare(b.barcode);
        });
        const uniqueRequestIDs = [
          ...new Set(
            sortedRows.map((row) => {
              const match = row.request_name.match(/^(\d+)_/);
              return match ? match[1] : row.request_name;
            })
          )
        ]
          .sort()
          .join("_");

        let exportRows = sortedRows.filter((row) => row.selected);
        if (exportRows.length === 0) exportRows = sortedRows;
        const filename = `${formattedDate}_${uniqueRequestIDs}_libraries_and_samples`;
        const wb = new ExcelJS.Workbook();
        if (this.selectedFile !== "without-file") {
          const response = await axiosRef.get(
            `${urlStringStart}/api/libraries-and-samples-templates/${this.selectedFile.id}/download/`,
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
          { header: "Request Name", key: "request_name", width: 25 },
          { header: "Name", key: "name", width: 25 },
          { header: "Status", key: "status_text", width: 15 },
          { header: "S/L", key: "type", width: 10 },
          { header: "Barcode", key: "barcode", width: 15 },
          { header: "Pool Paths", key: "pool_paths", width: 20 },
          { header: "GMO", key: "gmo", width: 20 },
          { header: "Date", key: "create_time", width: 15 },
          { header: "Input Type", key: "nucleic_acid_type_name", width: 20 },
          { header: "Protocol", key: "library_protocol_name", width: 20 },
          { header: "Analysis Type", key: "analysis_type", width: 20 },
          { header: "Input", key: "input", width: 15 },
          { header: "Starting Amount", key: "starting_amount", width: 18 },
          { header: "Cycles", key: "pcr_cycles", width: 12 },
          { header: "ng/µl", key: "concentration_library", width: 15 },
          { header: "bp", key: "mean_fragment_size", width: 12 },
          { header: "Index Type", key: "index_type", width: 15 },
          { header: "Coord", key: "coordinate", width: 12 },
          { header: "I7 ID", key: "index_i7_id", width: 15 },
          { header: "Index I7", key: "index_i7", width: 15 },
          { header: "I5 ID", key: "index_i5_id", width: 15 },
          { header: "Index I5", key: "index_i5", width: 15 },
          { header: "Length", key: "read_length", width: 12 },
          { header: "Depth (M)", key: "sequencing_depth", width: 15 },
        ];

        exportRows.forEach((row) => {
          parkourSheet.addRow(row);
        });

        const sortedSheets = [...wb.worksheets].sort((a, b) => a.orderNo - b.orderNo);
        const otherSheets = sortedSheets.filter(sheet => sheet !== parkourSheet);

        parkourSheet.orderNo = 0;
        otherSheets.forEach((sheet, index) => {
          sheet.orderNo = index + 1;
        });

        wb.views = [{ activeTab: 0, firstSheet: 0 }];

        const buffer = await wb.xlsx.writeBuffer();
        const blob = new Blob([buffer], {
          type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
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

.search-bar {
  width: 400px;
}

@media (max-width: 1500px) {
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

@media (max-width: 1400px) {
  .search-bar {
    width: 250px;
  }

  .search-bar input {
    padding: 6px;
  }

  .date-filter {
    padding: 2px;
  }

  .date-filters label {
    display: none;
  }

  .header-button span {
    display: none;
  }
}

@media (max-width: 900px) {
  .header-title {
    font-size: 16px;
  }

  .search-bar {
    width: 130px;
  }

  .search-bar input {
    width: 85px;
  }

  .date-filters {
    display: none;
  }
}

@media (max-width: 550px) {
  .header-logo {
    display: none !important;
  }

  .search-bar {
    display: none;
  }

  .date-filters {
    display: none;
  }

  .header-button {
    display: none;
  }
}
</style>

<!--
sorting order: 3rd sheet
-->

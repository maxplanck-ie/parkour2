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
        <svg style="display: block" fill="none" width="42px" height="42px" version="1.1"
          xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
          <g>
            <path opacity="0.3"
              d="M3 12C3 4.5885 4.5885 3 12 3C19.4115 3 21 4.5885 21 12C21 19.4115 19.4115 21 12 21C4.5885 21 3 19.4115 3 12Z"
              fill="#333333" />
            <path
              d="M3 12C3 4.5885 4.5885 3 12 3C19.4115 3 21 4.5885 21 12C21 19.4115 19.4115 21 12 21C4.5885 21 3 19.4115 3 12Z"
              stroke="white" stroke-width="1.5" />
            <path d="M14.5 14.5L9 9" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
            <path d="M10 15H14.6717C14.853 15 15 14.853 15 14.6716V10" stroke="white" stroke-width="1.5"
              stroke-linecap="round" stroke-linejoin="round" />
          </g>
        </svg>
      </div>
      <div class="header-title" style="display: inline">
        Incoming Libraries and Samples
      </div>

      <!-- Sticky right section for search, advanced filters, and select columns -->
      <div class="sticky-actions">
        <div class="search-bar">
          <input ref="searchInput" v-model="searchQuery" type="text" placeholder="Search" />
          <font-awesome-icon icon="fa-solid fa-magnifying-glass" style="color: darkgrey" />
        </div>
        <div class="button-popup-wrapper">
          <button class="header-button" id="toggleAdvancedFiltersButton" @click="toggleAdvancedFilters">
            <font-awesome-icon icon="fa-solid fa-filter" style="color: white" />
            <span> Advanced Filters </span>
          </button>
          <div id="advancedFiltersPopup" v-if="showAdvancedFilters" class="button-popup-container"
            style="width: 250px; left: -50px">
            <label>
              <div style="
                  display: flex;
                  justify-content: center;
                  text-align: center;
                ">
                <input type="checkbox" v-model="filters.showLibraries" />
              </div>
              <div><span style="font-weight: bold">Show</span> Libraries</div>
            </label>
            <label>
              <div style="
                  display: flex;
                  justify-content: center;
                  text-align: center;
                ">
                <input type="checkbox" v-model="filters.showSamples" />
              </div>
              <div><span style="font-weight: bold">Show</span> Samples</div>
            </label>
            <label>
              <div style="
                  display: flex;
                  justify-content: center;
                  text-align: center;
                ">
                <input type="checkbox" v-model="filters.onlySamplesSubmitted" />
              </div>
              <div>
                <span style="font-weight: bold">Filter Requests</span> with
                Samples Submitted
              </div>
            </label>
            <label>
              <div style="
                  display: flex;
                  justify-content: center;
                  text-align: center;
                ">
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
        <button class="header-button" @click="exportToExcel">
          <font-awesome-icon icon="fa-solid fa-file-excel" style="color: white" />
          <span> Export to Excel </span>
        </button>
      </div>
    </div>

    <!-- Main content section with table -->
    <div class="table-container">
      <TabulatorTable v-if="!loading" ref="tabulatorTableRef" :rowData="librariesSamplesList" :columnDefs="columnsList"
        groupBy="request_name" :groupSort="{ field: 'request_name', order: 'desc' }" :tableOptions="{
          ...tableOptions,
          onBatchCellValueChanged,
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
  </div>
</template>

<script lang="jsx">
import TabulatorTable from "../components/TabulatorTable.vue";
import { TabulatorFull as Tabulator } from "tabulator-tables";
import * as XLSX from "xlsx";
import {
  showNotification,
  handleError,
  createAxiosObject,
  urlStringStartsWith
} from "../utils/utilities";
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
      librariesSamplesList: [],
      columnsList: [],
      showPopupWindow: false,
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
          return `
    <div style="display: flex; justify-content: space-between; align-items: center;">
      <div style="display: flex; justify-content: space-between; align-items: center;">
        ${samplesSubmitted
              ? `<div title="Samples Submitted" style="display: flex; align-items: center; cursor: pointer;" onclick="handleGroupButtonClick(event, '${value}', 'samplesSubmitted')">
                <svg fill="none" width="24px" height="24px" style="cursor: pointer;" version="1.1" xmlns="http://www.w3.org/2000/svg">
                  <g>
                    <path opacity="0.3" d="M13.8179 4.54512L13.6275 4.27845C12.8298 3.16176 11.1702 3.16176 10.3725 4.27845L10.1821 4.54512C9.76092 5.13471 9.05384 5.45043 8.33373 5.37041L7.48471 5.27608C6.21088 5.13454 5.13454 6.21088 5.27608 7.48471L5.37041 8.33373C5.45043 9.05384 5.13471 9.76092 4.54512 10.1821L4.27845 10.3725C3.16176 11.1702 3.16176 12.8298 4.27845 13.6275L4.54512 13.8179C5.13471 14.2391 5.45043 14.9462 5.37041 15.6663L5.27608 16.5153C5.13454 17.7891 6.21088 18.8655 7.48471 18.7239L8.33373 18.6296C9.05384 18.5496 9.76092 18.8653 10.1821 19.4549L10.3725 19.7215C11.1702 20.8382 12.8298 20.8382 13.6275 19.7215L13.8179 19.4549C14.2391 18.8653 14.9462 18.5496 15.6663 18.6296L16.5153 18.7239C17.7891 18.8655 18.8655 17.7891 18.7239 16.5153L18.6296 15.6663C18.5496 14.9462 18.8653 14.2391 19.4549 13.8179L19.7215 13.6275C20.8382 12.8298 20.8382 11.1702 19.7215 10.3725L19.4549 10.1821C18.8653 9.76092 18.5496 9.05384 18.6296 8.33373L18.7239 7.48471C18.8655 6.21088 17.7891 5.13454 16.5153 5.27608L15.6663 5.37041C14.9462 5.45043 14.2391 5.13471 13.8179 4.54512Z" fill="green"/>
                    <path d="M13.8179 4.54512L13.6275 4.27845C12.8298 3.16176 11.1702 3.16176 10.3725 4.27845L10.1821 4.54512C9.76092 5.13471 9.05384 5.45043 8.33373 5.37041L7.48471 5.27608C6.21088 5.13454 5.13454 6.21088 5.27608 7.48471L5.37041 8.33373C5.45043 9.05384 5.13471 9.76092 4.54512 10.1821L4.27845 10.3725C3.16176 11.1702 3.16176 12.8298 4.27845 13.6275L4.54512 13.8179C5.13471 14.2391 5.45043 14.9462 5.37041 15.6663L5.27608 16.5153C5.13454 17.7891 6.21088 18.8655 7.48471 18.7239L8.33373 18.6296C9.05384 18.5496 9.76092 18.8653 10.1821 19.4549L10.3725 19.7215C11.1702 20.8382 12.8298 20.8382 13.6275 19.7215L13.8179 19.4549C14.2391 18.8653 14.9462 18.5496 15.6663 18.6296L16.5153 18.7239C17.7891 18.8655 18.8655 17.7891 18.7239 16.5153L18.6296 15.6663C18.5496 14.9462 18.8653 14.2391 19.4549 13.8179L19.7215 13.6275C20.8382 12.8298 20.8382 11.1702 19.7215 10.3725L19.4549 10.1821C18.8653 9.76092 18.5496 9.05384 18.6296 8.33373L18.7239 7.48471C18.8655 6.21088 17.7891 5.13454 16.5153 5.27608L15.6663 5.37041C14.9462 5.45043 14.2391 5.13471 13.8179 4.54512Z" stroke="#323232" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M9 12L10.8189 13.8189V13.8189C10.9189 13.9189 11.0811 13.9189 11.1811 13.8189V13.8189L15 10" stroke="#323232" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
                  </g>
                </svg>
              </div>`
              : `<div title="Samples not Submitted" style="display: flex; align-items: center; cursor: pointer;" onclick="handleGroupButtonClick(event, '${value}', 'samplesSubmitted')">
                <svg fill="none" width="24px" height="24px" style="cursor: pointer;" version="1.1" xmlns="http://www.w3.org/2000/svg">
                  <g>
                    <path opacity="0.1" d="M13.8179 4.54512L13.6275 4.27845C12.8298 3.16176 11.1702 3.16176 10.3725 4.27845L10.1821 4.54512C9.76092 5.13471 9.05384 5.45043 8.33373 5.37041L7.48471 5.27608C6.21088 5.13454 5.13454 6.21088 5.27608 7.48471L5.37041 8.33373C5.45043 9.05384 5.13471 9.76092 4.54512 10.1821L4.27845 10.3725C3.16176 11.1702 3.16176 12.8298 4.27845 13.6275L4.54512 13.8179C5.13471 14.2391 5.45043 14.9462 5.37041 15.6663L5.27608 16.5153C5.13454 17.7891 6.21088 18.8655 7.48471 18.7239L8.33373 18.6296C9.05384 18.5496 9.76092 18.8653 10.1821 19.4549L10.3725 19.7215C11.1702 20.8382 12.8298 20.8382 13.6275 19.7215L13.8179 19.4549C14.2391 18.8653 14.9462 18.5496 15.6663 18.6296L16.5153 18.7239C17.7891 18.8655 18.8655 17.7891 18.7239 16.5153L18.6296 15.6663C18.5496 14.9462 18.8653 14.2391 19.4549 13.8179L19.7215 13.6275C20.8382 12.8298 20.8382 11.1702 19.7215 10.3725L19.4549 10.1821C18.8653 9.76092 18.5496 9.05384 18.6296 8.33373L18.7239 7.48471C18.8655 6.21088 17.7891 5.13454 16.5153 5.27608L15.6663 5.37041C14.9462 5.45043 14.2391 5.13471 13.8179 4.54512Z" fill="#323232"/>
                    <path d="M13.8179 4.54512L13.6275 4.27845C12.8298 3.16176 11.1702 3.16176 10.3725 4.27845L10.1821 4.54512C9.76092 5.13471 9.05384 5.45043 8.33373 5.37041L7.48471 5.27608C6.21088 5.13454 5.13454 6.21088 5.27608 7.48471L5.37041 8.33373C5.45043 9.05384 5.13471 9.76092 4.54512 10.1821L4.27845 10.3725C3.16176 11.1702 3.16176 12.8298 4.27845 13.6275L4.54512 13.8179C5.13471 14.2391 5.45043 14.9462 5.37041 15.6663L5.27608 16.5153C5.13454 17.7891 6.21088 18.8655 7.48471 18.7239L8.33373 18.6296C9.05384 18.5496 9.76092 18.8653 10.1821 19.4549L10.3725 19.7215C11.1702 20.8382 12.8298 20.8382 13.6275 19.7215L13.8179 19.4549C14.2391 18.8653 14.9462 18.5496 15.6663 18.6296L16.5153 18.7239C17.7891 18.8655 18.8655 17.7891 18.7239 16.5153L18.6296 15.6663C18.5496 14.9462 18.8653 14.2391 19.4549 13.8179L19.7215 13.6275C20.8382 12.8298 20.8382 11.1702 19.7215 10.3725L19.4549 10.1821C18.8653 9.76092 18.5496 9.05384 18.6296 8.33373L18.7239 7.48471C18.8655 6.21088 17.7891 5.13454 16.5153 5.27608L15.6663 5.37041C14.9462 5.45043 14.2391 5.13471 13.8179 4.54512Z" stroke="#323232" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
                  </g>
                </svg>
              </div>`
            }
    ${gmo
              ? `<div title="GMO: Yes" style="display: flex; align-items: center;">
                <svg fill="none" width="24px" height="24px" style="cursor: auto;" version="1.1" xmlns="http://www.w3.org/2000/svg">
                  <g>
                    <path d="M21 12 L18.36 18.36 L12 21 L5.64 18.36 L3 12 L5.64 5.64 L12 3 L18.36 5.64 Z" fill="#FFB6C1" stroke="#323232" stroke-width="1.8" stroke-linejoin="round" transform="rotate(-22.5 12 12)"/>
                    <text x="12" y="13" text-anchor="middle" fill="#333333" font-size="10.5" font-family="Arial, sans-serif" dominant-baseline="middle" stroke="#323232" stroke-width="0.8" paint-order="stroke">G</text>
                  </g>
                </svg>
              </div>`
              : `<div title="GMO: No" style="display: flex; align-items: center;">
                  <svg fill="none" width="24px" height="24px" style="cursor: auto;" version="1.1" xmlns="http://www.w3.org/2000/svg">
                    <g>
                      <path d="M21 12 L18.36 18.36 L12 21 L5.64 18.36 L3 12 L5.64 5.64 L12 3 L18.36 5.64 Z" fill="#B2D8B2" stroke="#323232" stroke-width="1.8" stroke-linejoin="round" transform="rotate(-22.5 12 12)"/>
                      <text x="12" y="13" text-anchor="middle" fill="#333333" font-size="10.5" font-family="Arial, sans-serif" dominant-baseline="middle" stroke="#323232" stroke-width="0.8" paint-order="stroke">G</text>
                    </g>
                  </svg>
              </div>`
            }
  <div>
    <span style="font-weight: bold; font-size: 12px; color: #333;">${value}</span>
    <span style="font-weight: normal; font-size: 12px; margin-left: 2px; color: black;">
      (#: ${count}, Total Depth: ${totalDepth}M, Length: ${totalReadLength}, ${biosafetyLevel})
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
      <div title="Mark selected as Quality Checked: Passed" class="group-action-button" onclick="handleGroupButtonClick(event, '${value}', 'qualityPassed')">
        <svg fill="none" width="24px" height="24px" version="1.1" xmlns="http://www.w3.org/2000/svg">
          <g>
            <path opacity="0.3" d="M3 12C3 4.5885 4.5885 3 12 3C19.4115 3 21 4.5885 21 12C21 19.4115 19.4115 21 12 21C4.5885 21 3 19.4115 3 12Z" fill="green"/>
            <path d="M3 12C3 4.5885 4.5885 3 12 3C19.4115 3 21 4.5885 21 12C21 19.4115 19.4115 21 12 21C4.5885 21 3 19.4115 3 12Z" stroke="#323232" stroke-width="1.8"/>
            <path d="M9 12L10.6828 13.6828V13.6828C10.858 13.858 11.142 13.858 11.3172 13.6828V13.6828L15 10" stroke="#323232" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
          </g>
        </svg>
      </div>
      <div title="Mark selected as Quality Checked: Failed" class="group-action-button" onclick="handleGroupButtonClick(event, '${value}', 'qualityFailed')">
        <svg fill="none" width="24px" height="24px" version="1.1" xmlns="http://www.w3.org/2000/svg">
          <g>
            <path opacity="0.3" d="M3 12C3 4.5885 4.5885 3 12 3C19.4115 3 21 4.5885 21 12C21 19.4115 19.4115 21 12 21C4.5885 21 3 19.4115 3 12Z" fill="red"/>
            <path d="M9 9L15 15" stroke="#323232" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M15 9L9 15" stroke="#323232" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M3 12C3 4.5885 4.5885 3 12 3C19.4115 3 21 4.5885 21 12C21 19.4115 19.4115 21 12 21C4.5885 21 3 19.4115 3 12Z" stroke="#323232" stroke-width="1.8"/>
          </g>
        </svg>
      </div>
      <div title="Mark selected as Quality Checked: Compromised" class="group-action-button" onclick="handleGroupButtonClick(event, '${value}', 'qualityCompromised')">
        <svg fill="none" width="40px" height="40px" version="1.1" xmlns="http://www.w3.org/2000/svg">
          <g>
            <path opacity="0.3" d="M3 12C3 4.5885 4.5885 3 12 3C19.4115 3 21 4.5885 21 12C21 19.4115 19.4115 21 12 21C4.5885 21 3 19.4115 3 12Z" fill="orange"/>
            <path d="M12 8L12 13" stroke="#323232" stroke-width="1.8" stroke-linecap="round"/>
            <path d="M12 16V15.9888" stroke="#323232" stroke-width="1.8" stroke-linecap="round"/>
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
        showLibraries: true,
        showSamples: true,
        onlySamplesSubmitted: false,
        onlyGmo: false
      },
      showAdvancedFilters: false,
      showSelectColumns: false,
    };
  },
  mounted() {
    this.getLibrariesSamples();
    this.setColumns();

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
          input:
            element.measuring_value == null && element.measured_element == null
              ? "-"
              : element.measuring_unit === "concentration"
                ? `${String(
                  element.measured_value === 0
                    ? 0
                    : element.measured_value || ""
                )} ng/µl`
                : element.measuring_unit === "m"
                  ? `${String(
                    element.measured_value === 0
                      ? 0
                      : element.measured_value || ""
                  )} M`
                  : element.measuring_unit !== "-"
                    ? `${String(
                      element.measured_value === 0
                        ? 0
                        : element.measured_value || ""
                    )} ${String(element.measuring_unit || "-")}`
                    : `${String(
                      element.measured_value === 0
                        ? 0
                        : element.measured_value || ""
                    )}`,
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
          rna_quality:
            element.rna_quality === 0 ? 0 : element.rna_quality || "",
          gmo: element.gmo === null ? "" : element.gmo,
          gmo_facility:
            element.gmo_facility === null ? "" : element.gmo_facility,
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
      const storedColumnState = JSON.parse(
        localStorage.getItem("incomingLibrariesAndSamplesColumnSettings")
      );

      let columnList = [
        {
          field: "selected",
          visible: true,
          headerVertical: false,
          frozen: true,
          resizable: false,
          formatter: (cell) => {
            const row = cell.getRow();
            const rowData = row.getData();
            const checkbox = `<input type="checkbox" title="Select" style="top:-4px" ${rowData.selected ? "checked" : ""
              } />`;

            return checkbox;
          },
          hozAlign: "center",
          width: 30,
          minWidth: 30,
          cssClass: "checkbox-column right-border",
          contextMenu: () => this.cellContextMenu(false, false, false),
          cellClick: function (e, cell) {
            const clickedRow = cell.getRow();
            const rowData = clickedRow.getData();
            const checkbox = e.target;
            rowData.selected = checkbox.checked;
          }
        },
        {
          title: "Name",
          field: "name",
          minWidth: 100,
          headerFilter: true,
          headerTooltip: "Sample Name",
          visible: true,
          frozen: true,
          cssClass: "name-column right-border",
          sorter: (a, b, aRow, bRow) => {
            return aRow
              .getData()
              .request_name.localeCompare(bRow.getData().request_name);
          },
          contextMenu: () => this.cellContextMenu(true, false, false),
          formatter: (cell) => {
            const type = cell.getRow().getData().type;
            const request_name = cell.getRow().getData().request_name;
            const name = cell.getValue();
            const tableGroupsToggleState =
              this.tabulatorInstance.getTableGroupsToggleState();
            return `
                        <div style="padding: 4px 8px; display: flex; align-items: center;">
                          <span title="${type === "S" ? "Sample" : "Library"}" 
                            style="
                              display: inline-block;
                              font-size: 10px;
                              font-weight: bold;
                              padding: 4px;
                              border: 2px solid #333;
                              border-radius: 4px;
                              margin-right: 8px;
                            ">
                            ${type}
                          </span>
                          <span title="${name}" style="padding: 8px 0px; overflow: hidden; white-space: nowrap; text-overflow: ellipsis;">${(tableGroupsToggleState == 2
                ? request_name + " ➜ "
                : "") + name
              }</span>
                        </div>
                      `;
          },
          contextMenu: () => this.cellContextMenu(true, false, false),
          cellDblClick: function (e, cell) {
            showNotification("This field is not editable.", "warning");
          }
        },
        {
          title: "Barcode",
          field: "barcode",
          width: 95,
          minWidth: 95,
          headerFilter: true,
          headerTooltip: "Barcode",
          visible: true,
          frozen: true,
          cssClass: "details-column barcode-column right-border",
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
          title: "From Users",
          headerHozAlign: "left",
          visible: true,
          cssClass: "title-field-group",
          columns: [
            {
              title: "Input Type",
              field: "nucleic_acid_type_name",
              minWidth: 80,
              width: "6%",
              headerVertical: false,
              headerTooltip: "Input Type",
              visible: true,
              cssClass: "user-entry-column",
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
              width: "6%",
              headerVertical: false,
              headerTooltip: "Library Preparation Protocol",
              visible: true,
              cssClass: "user-entry-column",
              contextMenu: () => this.cellContextMenu(true, false, false),
              formatter: (cell) => {
                const value = cell.getValue();
                const finalString = value || "No Protocol";
                return this.ellipsisContainer(finalString);
              },
              cellDblClick: function (e, cell) {
                showNotification("This field is not editable.", "warning");
              }
            },
            {
              title: "Comment Library/Input",
              field: "comments",
              minWidth: 100,
              headerVertical: false,
              headerTooltip: "Comment (User)",
              visible: true,
              cssClass: "user-entry-column",
              contextMenu: () => this.cellContextMenu(true, false, false),
              formatter: (cell) => {
                const finalString = cell.getValue() || "Empty";
                return this.ellipsisContainer(finalString);
              },
              cellDblClick: function (e, cell) {
                showNotification("This field is not editable.", "warning");
              }
            },
            {
              title: "Input",
              field: "input",
              minWidth: 60,
              width: "4%",
              headerVertical: false,
              headerTooltip: "Input (User)",
              visible: true,
              cssClass: "user-entry-column",
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
              title: "µl",
              field: "volume",
              minWidth: 60,
              width: "4%",
              headerVertical: false,
              headerTooltip: "Volume (User)",
              visible: true,
              cssClass: "user-entry-column",
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
              },
              cellDblClick: function (e, cell) {
                showNotification("This field is not editable.", "warning");
              }
            },
            {
              title: "bp",
              field: "mean_fragment_size",
              minWidth: 60,
              width: "4%",
              headerVertical: false,
              headerTooltip: "Size Distribution (User)",
              visible: true,
              cssClass: "user-entry-column",
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
            }
          ]
        },
        {
          title: "From Facility",
          headerHozAlign: "left",
          visible: true,
          cssClass: "title-field-group",
          columns: [
            {
              title: "Unit",
              field: "measuring_unit_facility",
              minWidth: 80,
              width: "6%",
              editor: "list",
              editorParams: (cell) => {
                const row = cell.getRow().getData();
                const options = [
                  { label: "ng/µl (Concentration)", value: "concentration" },
                  { label: "M (Cells)", value: "m" },
                  { label: "k (Cells)", value: "k" },
                  { label: "Unknown", value: "-" }
                ];
                if (row.type === "L") {
                  return {
                    values: options.filter(
                      (option) => option.value !== "m" && option.value !== "k"
                    )
                  };
                }
                return { values: options };
              },
              headerVertical: false,
              headerTooltip: "Measurement Unit",
              visible: true,
              cssClass: "facility-entry-column",
              contextMenu: () => this.cellContextMenu(true, true, true),
              formatter: (cell) => {
                const value = cell.getValue();
                const options = {
                  concentration: "ng/µl (Concentration)",
                  m: "M (Cells)",
                  k: "k (Cells)",
                  "-": "Unknown"
                };
                const finalString = options[value] || value || "Select";
                return this.ellipsisContainer(finalString);
              }
            },
            {
              title: "Amount",
              field: "measured_value_facility",
              minWidth: 60,
              width: "4%",
              editor: "number",
              headerVertical: false,
              headerTooltip: "Measured Value",
              visible: true,
              cssClass: "facility-entry-column",
              contextMenu: () => this.cellContextMenu(true, true, true),
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
              title: "µl",
              field: "sample_volume_facility",
              minWidth: 60,
              width: "4%",
              editor: "number",
              headerVertical: false,
              headerTooltip: "Volume (Facility)",
              visible: true,
              cssClass: "facility-entry-column",
              editorParams: {
                min: 0,
                max: 2147483647,
                step: 1
              },
              validator: ["integer", "min:0", "max:2147483647"],
              contextMenu: () => this.cellContextMenu(true, true, true),
              formatter: (cell) => {
                const rawValue = cell.getValue();
                const value = parseInt(rawValue, 10);
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
              field: "size_distribution_facility",
              minWidth: 60,
              width: "4%",
              editor: "number",
              headerVertical: false,
              headerTooltip: "Size Distribution (Facility)",
              visible: true,
              cssClass: "facility-entry-column",
              contextMenu: () => this.cellContextMenu(true, true, true),
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
              title: "% Total",
              field: "percent_total",
              minWidth: 60,
              width: "4%",
              editor: "number",
              headerVertical: false,
              headerTooltip: "Smear Analysis (% Total)",
              visible: true,
              cssClass: "facility-entry-column",
              editorParams: {
                min: 0,
                max: 100,
                step: 0.1
              },
              validator: ["min:0", "max:100"],
              contextMenu: () => this.cellContextMenu(true, true, true),
              cellEditing: (cell) => {
                const rowData = cell.getRow().getData();
                if (rowData.type === "S") {
                  showNotification(
                    "This field is not available for samples.",
                    "warning"
                  );
                }
                if (rowData.type === "S") {
                  cell.getTable().modules.edit.currentCell = null;
                }
              },
              formatter: (cell) => {
                const rowData = cell.getRow().getData();
                const rawValue = cell.getValue();
                const value = Number(rawValue);
                const finalString =
                  rawValue === "" || rawValue === undefined || isNaN(value)
                    ? "-"
                    : value === 0
                      ? "0.0"
                      : value.toFixed(1);
                const cellElement = cell.getElement();
                if (rowData.type === "S") {
                  cellElement.classList.add("disable-editing");
                } else {
                  cellElement.classList.remove("disable-editing");
                }
                return this.ellipsisContainer(finalString);
              }
            },
            {
              title: "RQN",
              field: "rna_quality",
              minWidth: 60,
              width: "4%",
              headerVertical: false,
              headerTooltip: "RNA Quality",
              visible: true,
              editor: "number",
              editorParams: {
                min: 0,
                max: 11,
                step: 0.1
              },
              validator: ["min:0", "max:11"],
              cssClass: "facility-entry-column",
              contextMenu: () => this.cellContextMenu(true, true, true),
              cellEditing: (cell) => {
                const rowData = cell.getRow().getData();
                if (rowData.type === "L") {
                  showNotification(
                    "This field is not available for libraries.",
                    "warning"
                  );
                  cell.getTable().modules.edit.currentCell = null;
                }
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
                const rowData = cell.getRow().getData();
                const cellElement = cell.getElement();
                if (rowData.type === "L") {
                  cellElement.classList.add("disable-editing");
                } else {
                  cellElement.classList.remove("disable-editing");
                }
                return this.ellipsisContainer(finalString);
              }
            },
            {
              title: "GMO",
              field: "gmo_facility",
              minWidth: 60,
              width: "6%",
              editor: "list",
              headerTooltip: "GMO Documentation",
              editorParams: {
                values: [
                  { label: "Not Needed", value: "false" },
                  { label: "Risk Assessment Done", value: "true" }
                ]
              },
              cssClass: "facility-entry-column",
              contextMenu: () => this.cellContextMenu(true, true, true),
              cellEditing: (cell) => {
                const rowData = cell.getRow().getData();
                if (rowData.type === "L") {
                  showNotification(
                    "This field is not available for libraries.",
                    "warning"
                  );
                }
                if (rowData.gmo === false || rowData.gmo === "") {
                  showNotification(
                    "GMO is marked as 'NO' for this sample and cannot be edited.",
                    "warning"
                  );
                }
                if (
                  rowData.type === "L" ||
                  rowData.gmo == false ||
                  rowData.gmo == ""
                ) {
                  cell.getTable().modules.edit.currentCell = null;
                }
              },
              headerFilter: false,
              headerVertical: false,
              visible: true,
              formatter: (cell) => {
                const value = cell.getValue();
                const options = {
                  false: "Not Needed",
                  true: "Risk Assessment Done"
                };
                const finalString = options[value] || value || "Select";
                const rowData = cell.getRow().getData();
                const cellElement = cell.getElement();
                if (
                  rowData.type === "L" ||
                  rowData.gmo === false ||
                  rowData.gmo === ""
                ) {
                  cellElement.classList.add("disable-editing");
                } else {
                  cellElement.classList.remove("disable-editing");
                }
                return this.ellipsisContainer(finalString);
              }
            },
            {
              title: "Comment",
              field: "comments_facility",
              minWidth: 100,
              editor: "input",
              headerVertical: false,
              headerTooltip: "Comment (Facility)",
              visible: true,
              cssClass: "facility-entry-column no-right-border",
              contextMenu: () => this.cellContextMenu(true, true, true),
              formatter: (cell) => {
                const value = cell.getValue() || "Empty";
                return this.ellipsisContainer(value);
              }
            }
          ]
        }
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
              const requestName = cell.getRow().getData().request_name;
              this.tabulatorInstance
                .getTable()
                .getRows()
                .forEach((row) => {
                  if (row.getData().request_name === requestName) {
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
        "incomingLibrariesAndSamplesColumnSettings",
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
            this.tabulatorInstance.recreateTable();
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

        case "qualityCompromised":
          if (selectedRows.length === 0) {
            showNotification(
              "Please select libraries/samples in the request first.",
              "warning"
            );
            break;
          }
          let popupTitleQC = `Are you sure?`;
          let popupDescriptionQC = `Marking the following ${type === "L" ? "libraries" : "samples"
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
    exportToExcel() {
      const tempContainer = document.createElement("div");
      const exportColumns = this.columnsList
        .filter((col) => col.field !== "selected")
        .map((col) => ({ ...col }));
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
        if (aNum !== bNum) return bNum - aNum;
        return a.barcode?.localeCompare(b.barcode);
      });
      let exportRows = sortedRows.filter((row) => row.selected);
      if (exportRows.length === 0) exportRows = sortedRows;
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
      const filename = `${formattedDate}_${requestIds}_incoming.xlsx`;
      this.fakeLoadingStart();
      exportColumns.unshift({
        title: "Request Name",
        field: "request_name",
        visible: true
      });
      if (exportRows.length === 0) {
        exportRows = this.librariesSamplesList;
      }
      document.body.appendChild(tempContainer);
      const tempTabulator = new Tabulator(tempContainer, {
        data: exportRows,
        columns: exportColumns,
        placeholder: "No Libraries and Samples to show.",
        dependencies: {
          XLSX: XLSX
        },
        downloadConfig: {
          columnHeaders: true,
          columnGroups: true,
          rowGroups: true,
          columnCalcs: true,
          dataTree: true
        }
      });
      this.fakeLoadingStop();
      setTimeout(() => {
        try {
          tempTabulator.download("xlsx", filename, {
            sheetName: "Incoming Libraries & Samples"
          });
        } catch (error) {
          showNotification(
            "Failed to export the data, please try again.",
            "error"
          );
        } finally {
          tempTabulator.destroy();
          document.body.removeChild(tempContainer);
        }
      }, 300);
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
add export just like preparation
clicking on export button resets the width of columns
-->

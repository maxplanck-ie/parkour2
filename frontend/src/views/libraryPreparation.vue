<template>
  <div class="parent-container">
    <!-- Loading overlay -->
    <div v-if="loading || fakeLoading" class="loading-overlay">
      <div v-if="!fakeLoading" class="spinner"></div>
      <p v-if="!fakeLoading">
        Loading <span style="font-weight: bold">Library Preparation</span>...
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
                        height: 20px;
                        width: 20px;
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
                        <input type="checkbox" :checked="subColumn.visible"
                          @change="toggleColumnVisibility(subColumn, false)" />
                        {{ subColumn.title }}
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
        groupBy="library_protocol_name" :tableOptions="{
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
                {{ item.barcode + " ➜ " }}
                <span style="font-weight: bold">{{ item.name }}</span>
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
  name: "LibraryPreparation",
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
        groupHeader: (value, count, data) => {
          return `
  <div style="display: flex; justify-content: space-between; align-items: center;">
<div style="display: flex; justify-content: space-between; align-items: center;">
  <div>
    <span style="font-weight: bold; font-size: 14px;">Protocol ➜ ${value}</span>
    <span style="font-weight: normal; font-size: 12px; margin-left: 2px;">
      (# of libraries: ${count})
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
    </div>
  </div>
`;
        }
      },
      searchQuery: "",
      filters: {
        showLibraries: true,
        showSamples: true,
      },
      showAdvancedFilters: false,
      showSelectColumns: false,
      libraryProtocols: []
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
          "search",
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
        document.getElementsByClassName("tabulator-range-selected")[0]?.click();
      }
    }
  },
  methods: {
    async getLibrariesSamples() {
      this.loading = true;
      try {
        // let response = await axiosRef.get(
        //   urlStringStart + "/api/library_preparation/"
        // );

        let response = {
          data: [
            {
              pk: 20234,
              name: "COLO205_SMADWT_TGFb_18hr_1",
              barcode: "25L005573",
              type: "L",
              is_converted: true,
              request_name: "3491_Chan_A07_Timmers",
              pool_name: "Pool_2705",
              library_protocol: 43,
              library_protocol_name: "Illumina Stranded mRNA Prep, Ligation",
              concentration_sample: 129.974,
              starting_amount: 200.0,
              pcr_cycles: 12,
              mean_fragment_size: null,
              smear_analysis: 100.0,
              comments: null,
              concentration_library: null,
              comments_facility: null,
              comments_library_sample: "",
              coordinate: "D10",
              index_type: "",
              index_i7_id: "NXTR_i7_0172",
              index_i5_id: "NXTR_i5_0172",
              create_time: "2025-02-24T15:52:00.867845+01:00",
              measuring_unit_facility: "",
              measured_value_facility: "",
              size_distribution_facility: "",
            },
            {
              pk: 20235,
              name: "COLO205_SMADKO_TGFb_18hr_2",
              barcode: "25L005574",
              type: "L",
              is_converted: false,
              request_name: "3492_Chan_B08_Timmers",
              pool_name: "Pool_2706",
              library_protocol: 44,
              library_protocol_name: "NEBNext Ultra II Directional RNA",
              concentration_sample: 110.5,
              starting_amount: 150.0,
              pcr_cycles: 10,
              mean_fragment_size: 350,
              smear_analysis: 98.5,
              comments: "Sample processed successfully",
              concentration_library: 50.2,
              comments_facility: "No issues detected",
              comments_library_sample: "Quality control passed",
              coordinate: "E12",
              index_type: "Dual",
              index_i7_id: "NXTR_i7_0173",
              index_i5_id: "NXTR_i5_0173",
              create_time: "2025-02-24T16:00:00.867845+01:00",
              measuring_unit_facility: "ng/μL",
              measured_value_facility: 52.1,
              size_distribution_facility: 320,
            },
            {
              pk: 20236,
              name: "COLO205_Control_TGFb_6hr_3",
              barcode: "25L005575",
              is_converted: true,
              type: "L",
              request_name: "3493_Chan_C09_Timmers",
              pool_name: "Pool_2707",
              library_protocol: 45,
              library_protocol_name: "SMARTer Stranded Total RNA-Seq",
              concentration_sample: 95.3,
              starting_amount: 180.0,
              pcr_cycles: 14,
              mean_fragment_size: 400,
              smear_analysis: 97.2,
              comments: "Low RNA yield",
              concentration_library: 45.8,
              comments_facility: "",
              comments_library_sample: "",
              coordinate: "F06",
              index_type: "Single",
              index_i7_id: "NXTR_i7_0174",
              index_i5_id: "NXTR_i5_0174",
              create_time: "2025-02-24T16:30:00.867845+01:00",
              measuring_unit_facility: "ng/μL",
              measured_value_facility: 48.7,
              size_distribution_facility: 360,
            },
            {
              pk: 20237,
              name: "COLO205_SMADKO_TGFb_24hr_4",
              barcode: "25L005576",
              type: "L",
              is_converted: false,
              request_name: "3494_Chan_D10_Timmers",
              pool_name: "Pool_2708",
              library_protocol: 46,
              library_protocol_name: "TruSeq Stranded Total RNA Library Prep",
              concentration_sample: 105.7,
              starting_amount: 175.0,
              pcr_cycles: 11,
              mean_fragment_size: 380,
              smear_analysis: 96.9,
              comments: null,
              concentration_library: 48.3,
              comments_facility: "Potential contamination detected",
              comments_library_sample: "Requires re-evaluation",
              coordinate: "G08",
              index_type: "Dual",
              index_i7_id: "NXTR_i7_0175",
              index_i5_id: "NXTR_i5_0175",
              create_time: "2025-02-24T17:00:00.867845+01:00",
              measuring_unit_facility: "ng/μL",
              measured_value_facility: 50.4,
              size_distribution_facility: 340,
            },
          ],
        };

        let fetchedRows = response.data.map((element) => ({
          pk: element.pk || "",
          name: element.name || "",
          type: element.barcode[2] || "",
          barcode: element.barcode || "",
          is_converted: element.is_converted === null ? "" : element.is_converted,
          request_name: element.request_name || "",
          pool_name: element.pool_name || "",
          library_protocol: element.library_protocol === 0 ? 0 : element.library_protocol || "",
          library_protocol_name: element.library_protocol_name || "",
          concentration_sample: element.concentration_sample === 0 ? 0 : element.concentration_sample || "",
          concentration_library: element.concentration_library === 0 ? 0 : element.concentration_library || "",
          starting_amount: element.starting_amount === 0 ? 0 : element.starting_amount || "",
          pcr_cycles: element.pcr_cycles === 0 ? 0 : element.pcr_cycles || "",
          mean_fragment_size:
            element.mean_fragment_size === 0
              ? 0
              : element.mean_fragment_size || "",
          smear_analysis: element.smear_analysis === 0 ? 0 : element.smear_analysis || "",
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
              : element.size_distribution_facility || "",
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
        localStorage.getItem("libraryPreparationColumnSettings")
      );

      let columnList = [
        {
          title: "Select",
          field: "selected",
          visible: true,
          headerSort: false,
          headerVertical: true,
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
          width: 36,
          cssClass: "checkbox-column",
          contextMenu: () => this.cellContextMenu(false, false, false),
          cellClick: function (e, cell) {
            const clickedRow = cell.getRow();
            const rowData = clickedRow.getData();
            const checkbox = e.target;
            rowData.selected = checkbox.checked;
          }
        },
        {
          title: "Request",
          field: "request_name",
          minWidth: 220,
          headerFilter: true,
          visible: true,
          frozen: true,
          cssClass: "details-column blue-background",
          contextMenu: () => this.cellContextMenu(true, false, false),
          cellDblClick: function (e, cell) {
            showNotification("This field is not editable.", "warning");
          },
          formatter: (cell) => {
            const type = cell.getRow().getData().type;
            const library_protocol_name = cell.getRow().getData().library_protocol_name;
            const name = cell.getValue();
            const tableGroupsToggleState =
              this.tabulatorInstance.getTableGroupsToggleState();
            const bgColor = type === "S" ? "#00800080" : "lightblue";
            return `
                        <div style="padding: 4px 8px; display: flex; align-items: center;">
                          <span title="${type === "S" ? "Sample" : "Library"}" 
                            style="
                              display: inline-block;
                              background-color: ${bgColor};
                              color: white;
                              font-size: 10px;
                              font-weight: bold;
                              padding: 4px;
                              border: 2px solid #333;
                              border-radius: 4px;
                              margin-right: 8px;
                            ">
                            ${type}
                          </span>
                          <span title="${name}" style="padding: 8px 0px; font-weight:bold; overflow: hidden; white-space: nowrap; text-overflow: ellipsis;">${(tableGroupsToggleState == 2 ? library_protocol_name + " ➜ " : "") + name
              }</span>
                        </div>
                      `;
          },
        },
        {
          title: "Name",
          field: "name",
          minWidth: 220,
          headerFilter: true,
          visible: true,
          frozen: true,
          cssClass: "details-column blue-background",
          contextMenu: () => this.cellContextMenu(true, false, false),
          cellDblClick: function (e, cell) {
            showNotification("This field is not editable.", "warning");
          },
          formatter: (cell) => {
            const value = cell.getValue();
            const finalString = value || "-";
            return this.ellipsisContainer(finalString, true);
          },
        },
        {
          title: "Barcode",
          field: "barcode",
          width: 94,
          headerFilter: true,
          visible: true,
          frozen: true,
          cssClass: "details-column barcode-column blue-background",
          contextMenu: () => this.cellContextMenu(true, false, false),
          cellDblClick: function (e, cell) {
            showNotification("This field is not editable.", "warning");
          },
          formatter: (cell) => {
            const value = cell.getValue();
            const finalString = value || "-";
            return this.ellipsisContainer(finalString, true);
          }
        },
        {
          title: "Date",
          field: "create_time",
          width: 90,
          headerFilter: true,
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
          title: "Comment Library/Input",
          field: "comments_library_sample",
          minWidth: 150,
          headerVertical: true,
          visible: true,
          cssClass: "regular-column",
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
          title: "Pool",
          field: "pool_name",
          width: 84,
          headerVertical: true,
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
          title: "Index Type",
          field: "index_type",
          width: 96,
          headerVertical: true,
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
          title: "Index I5 ID",
          field: "index_i5_id",
          width: 105,
          headerVertical: true,
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
          title: "Index I7 ID",
          field: "index_i7_id",
          width: 105,
          headerVertical: true,
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
          title: "Coordinate",
          field: "coordinate",
          width: 50,
          headerVertical: true,
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
          title: "Measuring Unit",
          field: "measuring_unit_facility",
          minWidth: 80,
          width: "6%",
          editor: "list",
          editorParams: (cell) => {
            const row = cell.getRow().getData();
            const options = [
              { label: "ng/µl (Concentration)", value: "concentration" },
              { label: "M (Cells)", value: "m" },
              { label: "Unknown", value: "-" }
            ];
            if (row.type === "L") {
              return {
                values: options.filter((option) => option.value !== "m")
              };
            }
            return { values: options };
          },
          headerVertical: true,
          visible: true,
          cssClass: "regular-column",
          contextMenu: () => this.cellContextMenu(true, true, true),
          formatter: (cell) => {
            const value = cell.getValue();
            const options = {
              concentration: "ng/µl (Concentration)",
              m: "M (Cells)",
              "-": "Unknown"
            };
            const finalString = options[value] || value || "Select";
            return this.ellipsisContainer(finalString);
          }
        },
        {
          title: "Measured Value",
          field: "measured_value_facility",
          minWidth: 60,
          width: "4%",
          editor: "number",
          headerVertical: true,
          visible: true,
          cssClass: "regular-column",
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
          title: "Size",
          field: "size_distribution_facility",
          minWidth: 60,
          width: "4%",
          editor: "number",
          headerVertical: true,
          visible: true,
          cssClass: "regular-column",
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
          title: "Starting Amount (ng/fmol)",
          field: "starting_amount",
          minWidth: 60,
          width: "4%",
          editor: "number",
          headerVertical: true,
          visible: true,
          cssClass: "regular-column",
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
          title: "PCR Cycles",
          field: "pcr_cycles",
          minWidth: 60,
          width: "4%",
          editor: "number",
          headerVertical: true,
          visible: true,
          cssClass: "regular-column",
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
          title: "Concentration Library (ng/µl)",
          field: "concentration_library",
          minWidth: 60,
          width: "4%",
          editor: "number",
          headerVertical: true,
          visible: true,
          cssClass: "regular-column",
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
          title: "Size (bp)",
          field: "mean_fragment_size",
          minWidth: 60,
          width: "4%",
          editor: "number",
          headerVertical: true,
          visible: true,
          cssClass: "regular-column",
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
          title: "Smear Analysis",
          field: "smear_analysis",
          minWidth: 60,
          width: "4%",
          editor: "number",
          headerVertical: true,
          visible: true,
          cssClass: "regular-column",
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
          title: "QC Comment",
          field: "comments_facility",
          minWidth: 150,
          editor: "input",
          headerVertical: true,
          visible: true,
          cssClass: "regular-column",
          contextMenu: () => this.cellContextMenu(true, true, true),
          formatter: (cell) => {
            const value = cell.getValue() || "Empty";
            return this.ellipsisContainer(value);
          }
        },
        {
          title: "Comment",
          field: "comments",
          minWidth: 150,
          editor: "input",
          headerVertical: true,
          visible: true,
          cssClass: "regular-column no-right-border",
          contextMenu: () => this.cellContextMenu(true, true, true),
          formatter: (cell) => {
            const value = cell.getValue() || "Empty";
            return this.ellipsisContainer(value);
          }
        }
      ];

      if (false) {
        storedColumnState.forEach((column, index) => {
          if (columnList[index]) columnList[index].visible = column.visible;
          if (column.columns) {
            column.columns.forEach((subColumn, subIndex) => {
              if (columnList[index])
                columnList[index].columns[subIndex].visible = subColumn.visible;
            });
          }
        });
      }

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

        if (allowApplyToAll) {
          operations.push({
            label: "Apply to All",
            action: (e, cell) => {
              const value = cell.getValue();
              const field = cell.getField();
              const libraryProtocolName = cell.getRow().getData().library_protocol_name;
              this.tabulatorInstance
                .getTable()
                .getRows()
                .forEach((row) => {
                  if (row.getData().library_protocol_name === libraryProtocolName) {
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

      localStorage.setItem("libraryPreparationColumnSettings", JSON.stringify(updatedColumns));
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
    exportToExcel() {
      const today = new Date();
      const day = String(today.getDate()).padStart(2, "0");
      const month = String(today.getMonth() + 1).padStart(2, "0");
      const year = today.getFullYear();
      const formattedDate = `${day}_${month}_${year}`;
      const filename = `Library_Preparation_${formattedDate}.xlsx`;
      const tempContainer = document.createElement("div");
      const exportColumns = this.columnsList
        .filter((col) => col.field !== "selected")
        .map((col) => ({ ...col }));
      let exportRows = this.librariesSamplesList.filter(
        (row) => row.selected === true
      );
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
            sheetName: "Library Preparation"
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

.group-action-buttons-container {
  display: none;
  align-items: center;
  height: 15px;
  margin-left: 10px;
  padding: 0 10px;
  border-left: 1px solid grey;
}

.group-action-button {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 16px;
  padding: 0px;
  height: 24px;
  width: 22px;
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
Admin Panel refactor
Export customization
Add validations according to old component
Make filters and search specific to the components


What kind of filters to use here
We are grouping by Protocol, then why do we need a column of it
Combine comments meaning
Any group header for editable fields
What fields should be searchable
Some columns which are removed are still part of the export file

filters line is commented in the table component
storedcolumns line is set to false
-->

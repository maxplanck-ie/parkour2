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
              padding-right: 8px;
              padding-top: 10px;
              padding-bottom: 10px;
            "
          >
            <ul
              style="
                padding-left: 0px;
                padding-right: 10px;
                max-height: 300px;
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
                      backgroundColor: column.columns ? '#33333310' : 'white',
                      cursor: column.columns ? 'default' : 'pointer'
                    }"
                  >
                    <input
                      v-if="!column.columns"
                      type="checkbox"
                      :checked="column.visible"
                      @change="toggleColumnVisibility(column, true)"
                    />
                    <font-awesome-icon
                      v-if="column.columns"
                      icon="fa-solid fa-caret-down"
                      style="
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
                      "
                    />
                    <span style="font-weight: bold">{{ column.title }}</span>
                  </label>
                  <ul v-if="column.columns" style="padding-left: 15px">
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
                          @change="toggleColumnVisibility(subColumn, false)"
                        />
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
            <font-awesome-icon
              icon="fa-solid fa-layer-group"
              style="color: white"
            />
            <span> Toggle Views </span>
          </button>
        </div>
        <button class="header-button" @click="exportToExcel">
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
          fakeLoadingStop
        }"
      />
    </div>

    <!-- Popup window -->
    <div v-if="showPopupWindow" class="popup-overlay">
      <div
        class="popup-container"
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
} from "../utilities/utilityFunctions";
import {
  incomingLibrariesSamplesGroupHeader,
  incomingLibrariesSamplesColumnDefs
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
            if (mv === -1 && mu === "-") return "Unknown";
            if (isEmpty(mv) && isEmpty(mu)) return "";
            const val = mv === 0 ? 0 : mv || "";
            const unit = mu || "";
            if (isEmpty(mv) && !isEmpty(mu)) {
              if (unit === "concentration") return "ng/µl";
              if (unit === "m") return "M";
              if (unit === "k") return "k";
              if (unit === "-") return "x";
              return unit;
            }
            if (unit === "concentration") return `${val} ng/µl`;
            if (unit === "m") return `${val} M`;
            if (unit === "k") return `${val} k`;
            if (unit === "-") return `${val} x`;
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
      const storedVisibility = JSON.parse(
        localStorage.getItem("incomingLibrariesSamplesColumnVisibility") || "{}"
      );
      const storedWidths = JSON.parse(
        localStorage.getItem("incomingLibrariesSamplesColumnWidths") || "{}"
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
      return `<div title='${text}' style="overflow: hidden; white-space: nowrap; text-overflow: ellipsis; padding: 12px 8px 12px 12px; font-weight: ${
        boldText === true ? "bold" : "normal"
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
Export!
-->

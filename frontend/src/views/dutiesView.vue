<template>
  <div class="parent-container">
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
              fill-rule="evenodd"
              clip-rule="evenodd"
              d="M3 12C3 4.5885 4.5885 3 12 3C19.4115 3 21 4.5885 21 12C21 16.3106 20.4627 18.6515 18.5549 19.8557L18.2395 18.878C17.9043 17.6699 17.2931 16.8681 16.262 16.3834C15.2532 15.9092 13.8644 15.75 12 15.75C10.134 15.75 8.74481 15.922 7.73554 16.4097C6.70593 16.9073 6.09582 17.7207 5.7608 18.927L5.45019 19.8589C3.53829 18.6556 3 16.3144 3 12ZM8.75 10C8.75 8.20507 10.2051 6.75 12 6.75C13.7949 6.75 15.25 8.20507 15.25 10C15.25 11.7949 13.7949 13.25 12 13.25C10.2051 13.25 8.75 11.7949 8.75 10Z"
              fill="#333333"
            />
            <path
              d="M3 12C3 4.5885 4.5885 3 12 3C19.4115 3 21 4.5885 21 12C21 19.4115 19.4115 21 12 21C4.5885 21 3 19.4115 3 12Z"
              stroke="white"
              stroke-width="1.5"
            />
            <path
              d="M15 10C15 11.6569 13.6569 13 12 13C10.3431 13 9 11.6569 9 10C9 8.34315 10.3431 7 12 7C13.6569 7 15 8.34315 15 10Z"
              stroke="white"
              stroke-width="1.5"
            />
            <path
              d="M6 19C6.63819 16.6928 8.27998 16 12 16C15.72 16 17.3618 16.6425 18 18.9497"
              stroke="white"
              stroke-width="1.5"
              stroke-linecap="round"
            />
          </g>
        </svg>
      </div>
      <div class="header-title" style="display: inline">Manage Duties</div>
    </div>
    <div style="width: 100%; display: flex; flex-direction: row">
      <div class="table-container" style="width: 100%">
        <div
          style="
            margin-right: 12px;
            border: 1px solid black;
            border-radius: 4px;
          "
        >
          <div
            style="
              padding: 7px 15px;
              height: 70px;
              background: #ecebe5;
              display: flex;
              border-radius: 4px;
              align-items: center;
            "
          >
            <div
              style="
                display: flex;
                align-items: center;
                flex-grow: 1;
                overflow: hidden;
                white-space: nowrap;
              "
            >
              <div
                style="
                  background: grey;
                  width: 35px;
                  height: 35px;
                  text-align: center;
                  border-top-left-radius: 4px;
                  border-bottom-left-radius: 4px;
                "
              >
                <font-awesome-icon
                  icon="fa-solid fa-magnifying-glass"
                  style="color: white; margin-top: 10px"
                ></font-awesome-icon>
              </div>
              <input
                id="search-bar"
                style="outline: none; width: 450px; font-size: 14px"
                class="styled-box"
                type="text"
                placeholder="Search..."
                @input="searchDuties"
              />
            </div>

            <div style="display: flex; align-items: center; margin-left: 10px">
              <div
                style="
                  background: grey;
                  width: 35px;
                  height: 35px;
                  text-align: center;
                  border-top-left-radius: 4px;
                  border-bottom-left-radius: 4px;
                "
              >
                <font-awesome-icon
                  icon="fa-regular fa-calendar-days"
                  style="color: white; margin-top: 10px"
                ></font-awesome-icon>
              </div>
              <select
                id="period-filter"
                class="styled-box"
                style="width: 200px; font-size: 14px"
                v-model="selectedFilter"
              >
                <option value="all">All</option>
                <option value="ongoing">Ongoing</option>
                <option value="upcoming">Upcoming</option>
                <option value="past-1-month">Past 1 Month</option>
                <option value="past-3-months">Past 3 Months</option>
                <option value="past-6-months">Past 6 Months</option>
                <option value="past-1-year">Past 1 Year</option>
              </select>
            </div>
          </div>
          <ag-grid-vue
            ref="dutiesGrid"
            class="ag-theme-alpine"
            style="margin: 15px; height: 669px"
            rowSelection="multiple"
            animateRows="true"
            rowDragManaged="true"
            stopEditingWhenCellsLoseFocus="true"
            :columnDefs="columnsList"
            :rowData="dutiesList"
            :gridOptions="gridOptions"
            @cellValueChanged="editDuty"
            @first-data-rendered="updateGridDataObject"
          />
        </div>
      </div>
      <div
        class="add-duty-container"
        style="
          background: #ecebe5;
          width: 100%;
          height: 771px;
          max-width: 20%;
          border: 1px solid #006c66;
          border-radius: 4px;
        "
      >
        <div
          style="
            background: #006c66;
            padding: 10px;
            color: white;
            margin-bottom: 8px;
            height: 42px;
          "
        >
          <font-awesome-icon
            icon="fa-regular fa-calendar-plus"
            style="height: 18px; width: 18px"
          />
          <span class="text-medium" style="margin-left: 8px; font-size: 16px"
            >Add Duty</span
          >
        </div>
        <div style="padding-top: 6px">
          <div class="text-medium" style="padding-left: 8px; font-weight: bold">
            Facility:
          </div>
          <div style="padding-left: 30px; padding-right: 30px">
            <select
              class="dropdown-select"
              name="facility"
              id="facility"
              @change="updateDutyObject"
            >
              <option value="">Select</option>
              <option value="Bioinfo">Bioinfo</option>
              <option value="DeepSeq">DeepSeq</option>
            </select>
          </div>
        </div>
        <div style="padding-top: 6px">
          <div class="text-medium" style="padding-left: 8px; font-weight: bold">
            Responsible Person:
          </div>
          <div style="padding-left: 30px; padding-right: 30px">
            <select
              class="dropdown-select"
              name="main_name"
              id="main_name"
              disabled="true"
              @change="updateDutyObject"
            >
              <option value="">Select</option>
              <option v-for="user in userListFiltered" :value="user.id">
                {{ user.first_name }}
              </option>
            </select>
          </div>
        </div>
        <div style="padding-top: 6px">
          <div class="text-medium" style="padding-left: 8px; font-weight: bold">
            Backup Person:
          </div>
          <div style="padding-left: 30px; padding-right: 30px">
            <select
              class="dropdown-select"
              name="backup_name"
              id="backup_name"
              disabled="true"
              @change="updateDutyObject"
            >
              <option value="">Select</option>
              <option v-for="user in userListFiltered" :value="user.id">
                {{ user.first_name }}
              </option>
            </select>
          </div>
        </div>
        <div style="padding-top: 6px">
          <div class="text-medium" style="padding-left: 8px; font-weight: bold">
            Start Date:
          </div>
          <div style="padding-left: 30px; padding-right: 30px">
            <input
              class="date-selector"
              type="date"
              id="start_date"
              name="start_date"
              value=""
              min="2015-01-01"
              max="2099-12-31"
              @change="updateDutyObject"
            />
          </div>
        </div>
        <div style="padding-top: 6px">
          <div class="text-medium" style="padding-left: 8px; font-weight: bold">
            End Date:
          </div>
          <div style="padding-left: 30px; padding-right: 30px">
            <input
              class="date-selector"
              type="date"
              id="end_date"
              name="end_date"
              value=""
              min="2015-01-01"
              max="2099-12-31"
              @change="updateDutyObject"
            />
          </div>
        </div>
        <div style="padding-top: 6px">
          <div class="text-medium" style="padding-left: 8px; font-weight: bold">
            Platform:
          </div>
          <div style="padding-left: 30px; padding-right: 30px">
            <select
              class="dropdown-select"
              name="platform"
              id="platform"
              @change="updateDutyObject"
            >
              <option value="">Select</option>
              <option value="short">Short</option>
              <option value="long">Long</option>
              <option value="shortlong">Short + Long</option>
            </select>
          </div>
        </div>
        <div style="padding-top: 6px">
          <div class="text-medium" style="padding-left: 8px; font-weight: bold">
            Comments:
          </div>
          <div
            style="padding-left: 30px; padding-right: 30px; padding-right: 30px"
          >
            <textarea
              class="comment-textarea"
              id="comment"
              @input="updateDutyObject"
            />
          </div>
        </div>
        <button
          class="text-medium green-button"
          style="margin: 15px"
          @click="saveDuty()"
        >
          Save
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { AgGridVue } from "ag-grid-vue3";
import {
  showNotification,
  handleError,
  getProp,
  urlStringStartsWith
} from "../utils/utilities";
import { toRaw } from "vue";
import axios from "axios";
import moment from "moment";
import Cookies from "js-cookie";

const axiosRef = axios.create({
  withCredentials: true,
  headers: {
    "content-type": "application/json",
    "X-CSRFToken": Cookies.get("csrftoken")
  }
});

const urlStringStart = urlStringStartsWith();

export default {
  name: "Duties",
  components: {
    AgGridVue
  },
  data() {
    return {
      dutiesList: null,
      dutiesListBackup: null,
      newDuty: {},
      userList: [],
      userListFiltered: [],
      columnsList: [],
      gridOptions: {},
      gridData: [],
      selectedFilter: "ongoing"
    };
  },
  setup() {},
  beforeMount() {
    this.getUsers();
  },
  mounted() {},
  created() {},
  watch: {
    selectedFilter(value) {
      this.getFilteredDuties(true, value);
    }
  },
  computed: {},
  methods: {
    updateDutyObject(event) {
      let newDuty = toRaw(this.newDuty);
      if (event.target.id === "facility") {
        this.newDuty.main_name = "";
        this.newDuty.backup_name = "";
        document.getElementById("main_name").value = "";
        document.getElementById("backup_name").value = "";
        document.getElementById("main_name").disabled =
          event.target.value == "";
        document.getElementById("backup_name").disabled =
          event.target.value == "";
        this.userListFiltered = toRaw(this.userList).filter(
          (element) =>
            element.facility === document.getElementById("facility").value
        );
        newDuty[event.target.id] = event.target.value;
        this.newDuty = newDuty;
      } else if (
        event.target.id === "start_date" ||
        event.target.id === "end_date"
      ) {
        newDuty[event.target.id] = moment(event.target.value);
        this.newDuty = newDuty;
      } else {
        newDuty[event.target.id] = event.target.value;
        this.newDuty = newDuty;
      }
    },
    async saveDuty() {
      let newDuty = toRaw(this.newDuty);
      if (
        !newDuty.main_name ||
        !newDuty.main_name ||
        !newDuty.backup_name ||
        !newDuty.start_date ||
        !newDuty.platform
      ) {
        showNotification(
          "Please check all the necessary fields: \n 1. Facility \n 2. Responsible Person \n 3. Backup Person \n 4. Start Date \n 5. Platform",
          "error"
        );
      } else {
        await axiosRef
          .post(urlStringStart + "/api/duties/", newDuty)
          .then(() => {
            this.newDuty = {};
            document.getElementById("facility").value = "";
            document.getElementById("main_name").value = "";
            document.getElementById("backup_name").value = "";
            document.getElementById("start_date").value = "";
            document.getElementById("end_date").value = "";
            document.getElementById("platform").value = "";
            document.getElementById("comment").value = "";

            if (this.selectedFilter == "all")
              this.getFilteredDuties(true, "all");
            else this.selectedFilter = "all";
            showNotification("Duty added successfully.", "success");
          })
          .catch((error) => {
            this.getFilteredDuties(true, this.selectedFilter);
            handleError(error);
          });
      }
    },
    async getDuties(refresh = false, additionalUrl = "") {
      try {
        const response = await axiosRef.get(
          urlStringStart +
            "/api/duties/" +
            (additionalUrl !== "" ? "?" + additionalUrl : "")
        );
        let fetchedRows = [];
        let userList = this.userList;
        getProp(response, "data", []).forEach((element) => {
          fetchedRows.push({
            duty_id: element.id,
            facility: getProp(
              userList.find(
                (matcherElement) =>
                  getProp(matcherElement, "id", 0) ==
                  getProp(element, "main_name", 0)
              ) || {},
              "facility",
              "-"
            ),
            main_name: getProp(
              userList.find(
                (matcherElement_1) =>
                  getProp(matcherElement_1, "id", 0) ==
                  getProp(element, "main_name", 0)
              ) || {},
              "first_name",
              "-"
            ),
            backup_name: getProp(
              userList.find(
                (matcherElement_2) =>
                  getProp(matcherElement_2, "id", 0) ==
                  getProp(element, "backup_name", 0)
              ) || {},
              "first_name",
              "-"
            ),
            start_date:
              getProp(element, "start_date", "") &&
              moment(getProp(element, "start_date", "")).format("YYYY-MM-DD"),
            end_date:
              getProp(element, "end_date", "") &&
              moment(getProp(element, "end_date", "")).format("YYYY-MM-DD"),
            platform:
              String(getProp(element, "platform", "-")) === "shortlong"
                ? "Short + Long"
                : String(getProp(element, "platform", "-"))[0].toUpperCase() +
                  String(getProp(element, "platform", "-")).slice(1),
            comment: getProp(element, "comment", "")
          });
        });
        if (refresh == true) {
          this.dutiesList = fetchedRows;
        }
        this.dutiesListBackup = fetchedRows;
      } catch (error) {
        handleError(error);
      } finally {
      }
    },
    getFilteredDuties(refresh = false, selectedFilter) {
      let additionalUrl = "";
      let start_date = "";
      let end_date = "";
      if (selectedFilter === "all") {
        additionalUrl = "";
      } else if (selectedFilter === "ongoing") {
        additionalUrl = "ongoing=TRUE";
      } else if (selectedFilter === "upcoming") {
        additionalUrl = "upcoming=TRUE";
      } else if (selectedFilter === "past-1-month") {
        end_date = moment().format("YYYY-MM-DD");
        start_date = moment(end_date)
          .subtract(1, "months")
          .format("YYYY-MM-DD");
        additionalUrl = "start_date=" + start_date + "&end_date=" + end_date;
      } else if (selectedFilter === "past-3-months") {
        end_date = moment().format("YYYY-MM-DD");
        start_date = moment(end_date)
          .subtract(3, "months")
          .format("YYYY-MM-DD");
        additionalUrl = "start_date=" + start_date + "&end_date=" + end_date;
      } else if (selectedFilter === "past-6-months") {
        end_date = moment().format("YYYY-MM-DD");
        start_date = moment(end_date)
          .subtract(6, "months")
          .format("YYYY-MM-DD");
        additionalUrl = "start_date=" + start_date + "&end_date=" + end_date;
      } else if (selectedFilter === "past-1-year") {
        end_date = moment().format("YYYY-MM-DD");
        start_date = moment(end_date)
          .subtract(12, "months")
          .format("YYYY-MM-DD");
        additionalUrl = "start_date=" + start_date + "&end_date=" + end_date;
      }
      this.getDuties(refresh, additionalUrl);
    },
    async editDuty(rowData) {
      let dutyId = rowData.data.duty_id;
      let columnName = rowData.column.colId;
      let oldValue = String(rowData.oldValue);
      let newValue = String(rowData.newValue);

      if (
        (columnName !== "platform" && newValue.trim() !== oldValue.trim()) ||
        (columnName === "platform" &&
          newValue.toLowerCase() !== oldValue.toLowerCase())
      ) {
        switch (columnName) {
          case "main_name":
            newValue = getProp(
              toRaw(this.userList).find(
                (user) => user["first_name"] === newValue
              ),
              "id",
              0
            );
            break;
          case "backup_name":
            newValue = getProp(
              toRaw(this.userList).find(
                (user) => user["first_name"] === newValue
              ),
              "id",
              0
            );
            break;
          case "start_date":
            newValue = moment(newValue);
            break;
          case "end_date":
            newValue = moment(newValue);
            break;
          case "platform":
            newValue =
              newValue === "Short + Long"
                ? "shortlong"
                : String(newValue).toLowerCase();
            break;
          case "comment":
            newValue = newValue.trim();
            break;
        }
        await axiosRef
          .patch(urlStringStart + "/api/duties/" + String(dutyId) + "/", {
            [columnName]: newValue
          })
          .then(() => {
            this.getFilteredDuties(false, this.selectedFilter);
            showNotification("Duty edited successfully.", "success");
          })
          .catch((error) => {
            this.getFilteredDuties(true, this.selectedFilter);
            handleError(error);
          });
        this.updateGridDataObject();
      }
    },
    searchDuties(event) {
      if (event.target.value === "") this.dutiesList = this.dutiesListBackup;
      else {
        this.dutiesList = this.dutiesListBackup.filter(
          (element) =>
            (element.main_name &&
              element.main_name
                .toLowerCase()
                .includes(event.target.value.toLowerCase())) ||
            (element.backup_name &&
              element.backup_name
                .toLowerCase()
                .includes(event.target.value.toLowerCase())) ||
            (element.start_date &&
              element.start_date
                .toLowerCase()
                .replace(/[^a-zA-Z0-9 ]/g, "")
                .includes(
                  event.target.value.toLowerCase().replace(/[^a-zA-Z0-9 ]/g, "")
                )) ||
            (element.end_date &&
              element.end_date
                .toLowerCase()
                .replace(/[^a-zA-Z0-9 ]/g, "")
                .includes(
                  event.target.value.toLowerCase().replace(/[^a-zA-Z0-9 ]/g, "")
                )) ||
            (element.facility &&
              element.facility
                .toLowerCase()
                .includes(event.target.value.toLowerCase())) ||
            (element.platform &&
              element.platform
                .toLowerCase()
                .includes(event.target.value.toLowerCase())) ||
            (element.comment &&
              element.comment
                .toLowerCase()
                .includes(event.target.value.toLowerCase()))
        );
      }
    },
    async getUsers() {
      await axiosRef
        .get(urlStringStart + "/api/duties/responsibles/")
        .then((response) => {
          let userList = getProp(response, "data", []);
          this.userList = userList;
          this.getFilteredDuties(true, this.selectedFilter);
          this.setColumns(userList);
        })
        .catch((error) => handleError(error));
    },
    setColumns(userList) {
      this.columnsList = [
        // {
        //   headerName: "Select",
        //   field: "select",
        //   cellEditor: "agCheckboxCellEditor",
        //   editable: true,
        // },
        {
          headerName: "Responsible Person",
          field: "main_name",
          minWidth: 200,
          flex: 3,
          filter: true,
          sortable: true,
          resizable: true,
          editable: true,
          cellEditor: "agSelectCellEditor",
          cellEditorParams: (params) => {
            return {
              values: userList
                .filter((element) => element.facility === params.data.facility)
                .map((element) => element.first_name),
              valueListGap: 0
            };
          },
          rowDrag: true
        },
        {
          headerName: "Backup Person",
          field: "backup_name",
          minWidth: 150,
          flex: 3,
          filter: true,
          sortable: true,
          resizable: true,
          editable: true,
          cellEditor: "agSelectCellEditor",
          cellEditorParams: (params) => {
            return {
              values: userList
                .filter((element) => element.facility === params.data.facility)
                .map((element) => element.first_name),
              valueListGap: 0
            };
          }
        },
        {
          headerName: "Start Date",
          field: "start_date",
          cellEditor: "agDateStringCellEditor",
          cellEditorParams: {
            min: "2015-01-01",
            max: "2099-12-31"
          },
          cellRenderer: (data) => {
            return data.value ? moment(data.value).format("MM/DD/YYYY") : "-";
          },
          minWidth: 120,
          flex: 2,
          filter: true,
          sortable: true,
          resizable: true,
          editable: true,
          sort: "asc"
        },
        {
          headerName: "End Date",
          field: "end_date",
          cellEditor: "agDateStringCellEditor",
          cellEditorParams: {
            min: "2015-01-01",
            max: "2099-12-31"
          },
          cellRenderer: (data) => {
            return data.value ? moment(data.value).format("MM/DD/YYYY") : "-";
          },
          minWidth: 120,
          flex: 2,
          filter: true,
          sortable: true,
          resizable: true,
          editable: true
        },
        {
          headerName: "Facility",
          field: "facility",
          minWidth: 150,
          flex: 2,
          filter: true,
          sortable: true,
          resizable: true
        },
        {
          headerName: "Platform",
          field: "platform",
          minWidth: 150,
          flex: 2,
          filter: true,
          sortable: true,
          resizable: true,
          editable: true,
          cellEditor: "agSelectCellEditor",
          cellEditorParams: {
            values: ["Short", "Long", "Short + Long"],
            valueListGap: 0
          },
          cellRenderer: (data) => {
            if (data.value === "shortlong") return "Short + Long";
            else return data.value[0].toUpperCase() + data.value.slice(1);
          }
        },
        {
          headerName: "Comments",
          field: "comment",
          minWidth: 300,
          flex: 4,
          resizable: true,
          editable: true,
          cellEditor: "agLargeTextCellEditor",
          cellEditorPopup: true,
          cellEditorParams: {
            maxLength: 100,
            rows: 10,
            cols: 50
          }
        }
      ];
    },
    updateGridDataObject() {
      let gridData = [];
      this.gridOptions.api.forEachNode((rowNode, index) => {
        gridData.push(rowNode.data);
      });
      this.gridData = gridData;
    }
  }
};
</script>

<style>
.parent-container {
  width: 100%;
  display: flex;
  flex-direction: column;
  padding: 10px;
}

.styled-box {
  height: 35px;
  padding: 0px 8px;
  border: 1px solid grey;
  background: whitesmoke;
  outline: none;
  border-top-right-radius: 4px;
  border-bottom-right-radius: 4px;
}

.dropdown-select,
.date-selector {
  width: 100%;
  height: 30px;
  background: whitesmoke;
  padding: 4px;
  font-size: 14px !important;
}

.comment-textarea {
  width: 100%;
  height: 250px;
  background: whitesmoke;
}

.dropdown-select,
.date-selector,
.comment-textarea {
  border: 1px solid grey;
  border-radius: 4px;
  font-size: 12px;
  outline: none;
  font-size: 14px;
}

select:disabled {
  background: #dddddd;
}

@media (max-width: 1000px) {
  .add-duty-container {
    display: none;
  }
}

@media (max-width: 800px) {
  #search-bar {
    width: 200px !important;
  }

  #period-filter {
    width: 120px !important;
  }
}
</style>

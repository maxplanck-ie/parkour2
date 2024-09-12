<template>
  <div class="header">
    <font-awesome-icon
      style="font-size: 28px"
      icon="fa-solid fa-chalkboard-user"
      size="xl"
    />
    <span
      class="text-large"
      style="font-size: 20px; font-weight: bold; margin-left: 5px"
    >
      Manage Duties</span
    >
  </div>
  <div
    class="parent-container"
    style="
      padding: 15px;
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
    "
  >
    <div class="table-container" style="flex: 1; margin-bottom: 20px">
      <div style="margin: 15px; border: 1px solid #006c66">
        <div
          style="
            padding: 7px 15px;
            height: 42px;
            background: #ecebe5;
            display: flex;
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
                background: rgb(105, 105, 105);
                width: 28px;
                height: 28px;
                text-align: center;
              "
            >
              <font-awesome-icon
                icon="fa-solid fa-magnifying-glass"
                style="color: white; margin-top: 6px"
              ></font-awesome-icon>
            </div>
            <input
              id="search-bar"
              style="outline: none"
              class="styled-box"
              type="text"
              placeholder="Search..."
              @input="searchDuties"
            />
          </div>

          <div style="display: flex; align-items: center; margin-left: 10px">
            <div
              style="
                background: rgb(105, 105, 105);
                width: 28px;
                height: 28px;
                text-align: center;
              "
            >
              <font-awesome-icon
                icon="fa-regular fa-calendar-days"
                style="color: white; margin-top: 6px"
              ></font-awesome-icon>
            </div>
            <select
              id="period-filter"
              class="styled-box"
              style="flex-shrink: 0"
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
        <div style="padding: 15px">
          <ag-grid-vue
            ref="dutiesGrid"
            class="ag-theme-alpine"
            style="height: 723px"
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
    </div>
    <div
      class="add-duty-container"
      style="
        margin: 13px;
        background: #ecebe5;
        width: 100%;
        max-width: 320px;
        height: 800px;
        border: 1px solid #006c66;
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
        <font-awesome-icon icon="fa-regular fa-calendar-plus" />
        <span class="text-medium" style="margin-left: 4px">Add Duty</span>
      </div>
      <div style="padding-top: 6px">
        <div class="text-medium" style="padding-left: 8px; font-weight: bold">
          Facility:
        </div>
        <div style="padding-left: 30px">
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
        <div style="padding-left: 30px">
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
        <div style="padding-left: 30px">
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
        <div style="padding-left: 30px">
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
        <div style="padding-left: 30px">
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
        <div style="padding-left: 30px">
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
        <div style="padding-left: 30px; padding-right: 30px">
          <textarea
            class="comment-textarea"
            id="comment"
            @input="updateDutyObject"
          />
        </div>
      </div>
      <button
        class="text-medium save-button"
        style="margin: 15px"
        @click="saveDuty()"
      >
        Save
      </button>
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
.header {
  color: white;
  background: #006c66;
  padding: 16px 20px;
  width: 100% !important;
}

.styled-box {
  height: 28px;
  padding: 0px 8px;
  border: 1px solid rgb(105, 105, 105);
  background: whitesmoke;
  outline: none;
}

.dropdown-select,
.date-selector {
  width: 165px;
  height: 24px;
  background: whitesmoke;
  max-width: 80%;
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
  border-radius: 5px;
  font-size: 12px;
  outline: none;
}

.save-button {
  background: #006c66;
  border: none;
  outline: none;
  color: white;
  padding: 6px 10px;
}

.save-button:hover {
  cursor: pointer;
}

select:disabled {
  background: #dddddd;
}

@media (max-width: 767px) {
  .parent-container {
    flex-direction: column;
  }

  .table-container,
  .add-duty-container {
    width: 95% !important;
    max-width: none !important;
    margin: 10px !important;
  }
  .table-container > div {
    margin: 0px !important;
  }
}
</style>

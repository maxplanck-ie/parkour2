<template>
  <div class="parent-container">
    <div class="header">
      <div class="header-logo" style="display: inline; margin-right: 10px">
        <img
          :src="iconDutiesHeader"
          alt="Manage Duties"
          width="42"
          height="42"
          style="display: block"
        />
      </div>
      <div class="header-title" style="display: inline">Manage Duties</div>
    </div>
    <div class="duties-body">
      <div class="table-container duties-table-panel">
        <div class="duties-card">
          <div class="duties-toolbar">
            <div class="duties-search">
              <div class="duties-icon-box">
                <font-awesome-icon
                  icon="fa-solid fa-magnifying-glass"
                  class="duties-icon"
                />
              </div>
              <input
                id="search-bar"
                class="duties-input"
                type="text"
                placeholder="Search..."
                @input="searchDuties"
              />
            </div>

            <div class="duties-filter">
              <div class="duties-icon-box">
                <font-awesome-icon
                  icon="fa-regular fa-calendar-days"
                  class="duties-icon"
                />
              </div>
              <select
                id="period-filter"
                class="duties-select"
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
          <div class="duties-grid-wrapper">
            <LiteTabulatorTable
              ref="dutiesTableRef"
              tableId="dutiesTable"
              :rowData="dutiesList"
              :columnDefs="columnsList"
              :tableOptions="{
                handleCellEdited: editDuty,
                movableRows: true,
                initialSort: [{ column: 'start_date', dir: 'asc' }]
              }"
            />
          </div>
        </div>
      </div>
      <div class="add-duty-container">
        <div class="add-duty-header">
          <font-awesome-icon
            icon="fa-regular fa-calendar-plus"
            class="add-duty-icon"
          />
          <span class="add-duty-title">Add Duty</span>
        </div>
        <div class="add-duty-body">
          <div class="duty-field">
            <div class="text-medium duty-label">Facility:</div>
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
          <div class="duty-field">
            <div class="text-medium duty-label">Responsible Person:</div>
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
          <div class="duty-field">
            <div class="text-medium duty-label">Backup Person:</div>
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
          <div class="duty-field">
            <div class="text-medium duty-label">Start Date:</div>
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
          <div class="duty-field">
            <div class="text-medium duty-label">End Date:</div>
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
          <div class="duty-field">
            <div class="text-medium duty-label">Platform:</div>
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
          <div class="duty-field">
            <div class="text-medium duty-label">Comments:</div>
            <textarea
              class="comment-textarea"
              id="comment"
              @input="updateDutyObject"
            />
          </div>
        </div>
        <button class="text-medium green-button duty-save" @click="saveDuty()">
          Save
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import LiteTabulatorTable from "../components/TabulatorTableLite.vue";
import {
  showNotification,
  handleError,
  getProp,
  urlStringStartsWith
} from "../utilities/utilityFunctions";
import { toRaw } from "vue";
import axios from "axios";
import moment from "moment";
import Cookies from "js-cookie";
import iconDutiesHeader from "../assets/icons/header_duties.svg";

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
    LiteTabulatorTable
  },
  data() {
    return {
      iconDutiesHeader,
      dutiesList: null,
      dutiesListBackup: null,
      newDuty: {},
      userList: [],
      userListFiltered: [],
      columnsList: [],
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
    async editDuty(cell) {
      const rowData = cell.getRow().getData();
      const dutyId = rowData.duty_id;
      const columnName = cell.getField();
      const oldValue = String(cell.getOldValue());
      let newValue = String(cell.getValue());

      if (
        (columnName !== "platform" && newValue.trim() !== oldValue.trim()) ||
        (columnName === "platform" &&
          newValue.toLowerCase() !== oldValue.toLowerCase())
      ) {
        let valueToSend = newValue;
        switch (columnName) {
          case "main_name":
            valueToSend = getProp(
              toRaw(this.userList).find(
                (user) => user["first_name"] === newValue
              ),
              "id",
              0
            );
            break;
          case "backup_name":
            valueToSend = getProp(
              toRaw(this.userList).find(
                (user) => user["first_name"] === newValue
              ),
              "id",
              0
            );
            break;
          case "start_date":
            valueToSend = moment(newValue);
            break;
          case "end_date":
            valueToSend = moment(newValue);
            break;
          case "platform":
            valueToSend =
              newValue === "Short + Long"
                ? "shortlong"
                : String(newValue).toLowerCase();
            break;
          case "comment":
            valueToSend = newValue.trim();
            break;
        }
        await axiosRef
          .patch(urlStringStart + "/api/duties/" + String(dutyId) + "/", {
            [columnName]: valueToSend
          })
          .then(() => {
            this.getFilteredDuties(false, this.selectedFilter);
            showNotification("Duty edited successfully.", "success");
          })
          .catch((error) => {
            this.getFilteredDuties(true, this.selectedFilter);
            handleError(error);
          });
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
        {
          title: "Responsible Person",
          field: "main_name",
          minWidth: 150,
          widthGrow: 3,
          headerFilter: true,
          headerSort: true,
          editor: "list",
          editorParams: (cell) => ({
            values: userList
              .filter(
                (element) =>
                  element.facility === cell.getRow().getData().facility
              )
              .map((element) => element.first_name),
            emptyValue: ""
          }),
          rowHandle: true
        },
        {
          title: "Backup Person",
          field: "backup_name",
          minWidth: 150,
          widthGrow: 3,
          headerFilter: true,
          headerSort: true,
          editor: "list",
          editorParams: (cell) => ({
            values: userList
              .filter(
                (element) =>
                  element.facility === cell.getRow().getData().facility
              )
              .map((element) => element.first_name),
            emptyValue: ""
          })
        },
        {
          title: "Start Date",
          field: "start_date",
          minWidth: 120,
          widthGrow: 2,
          headerFilter: true,
          headerSort: true,
          editor: "date",
          editorParams: {
            min: "2015-01-01",
            max: "2099-12-31"
          },
          formatter: (cell) => {
            const v = cell.getValue();
            return v ? moment(v).format("MM/DD/YYYY") : "-";
          }
        },
        {
          title: "End Date",
          field: "end_date",
          minWidth: 120,
          widthGrow: 2,
          headerFilter: true,
          headerSort: true,
          editor: "date",
          editorParams: {
            min: "2015-01-01",
            max: "2099-12-31"
          },
          formatter: (cell) => {
            const v = cell.getValue();
            return v ? moment(v).format("MM/DD/YYYY") : "-";
          }
        },
        {
          title: "Facility",
          field: "facility",
          minWidth: 120,
          widthGrow: 2,
          headerFilter: true,
          headerSort: true
        },
        {
          title: "Platform",
          field: "platform",
          minWidth: 120,
          widthGrow: 2,
          headerFilter: true,
          headerSort: true,
          editor: "list",
          editorParams: {
            values: ["Short", "Long", "Short + Long"]
          },
          formatter: (cell) => {
            const v = cell.getValue();
            if (!v) return "-";
            if (v === "shortlong") return "Short + Long";
            return v.charAt(0).toUpperCase() + v.slice(1);
          }
        },
        {
          title: "Comments",
          field: "comment",
          minWidth: 200,
          widthGrow: 4,
          editor: "textarea"
        }
      ];
    }
  }
};
</script>

<style>
.parent-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 10px;
}

.duties-body {
  display: flex;
  gap: 12px;
  flex: 1;
  min-height: 0;
}

.duties-table-panel {
  flex: 1;
  min-width: 0;
  height: 100%;
}

.duties-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  border: 1px solid #c7cbd1;
  border-radius: 8px;
  background: #ffffff;
}

.duties-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 12px;
  background: #f3f1e9;
  border-bottom: 1px solid #d9d6cc;
  border-top-left-radius: 8px;
  border-top-right-radius: 8px;
}

.duties-search,
.duties-filter {
  display: flex;
  align-items: center;
  gap: 0;
  background: #ffffff;
  border: 1px solid #c7cbd1;
  border-radius: 8px;
  overflow: hidden;
}

.duties-search {
  flex: 1;
  max-width: 460px;
}

.duties-filter {
  width: 220px;
}

.duties-icon-box {
  width: 34px;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #6b7280;
}

.duties-icon {
  color: #ffffff;
}

.duties-input,
.duties-select {
  border: none;
  outline: none;
  font-size: 14px;
  padding: 6px 10px;
  background: #ffffff;
  color: #333;
  width: 100%;
}

.duties-grid-wrapper {
  flex: 1;
  min-height: 0;
  margin: 12px;
}

.dropdown-select,
.date-selector {
  width: 100%;
  height: 30px;
  background: whitesmoke;
}

.comment-textarea {
  width: 100%;
  height: 220px;
  background: whitesmoke;
}

.dropdown-select,
.date-selector,
.comment-textarea {
  border: 1px solid grey;
  border-radius: 8px;
  font-size: 14px;
  outline: none;
  padding: 4px;
  font-family: var(--app-font-family);
}

.date-selector {
  text-transform: uppercase;
  padding: 7px;
  font-size: 13px;
}

.comment-textarea {
  padding: 7px;
  resize: none;
}

.add-duty-container {
  width: 360px;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f1efe8;
  border: 1px solid #006c66;
  border-radius: 8px;
  overflow: hidden;
}

.add-duty-header {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #006c66;
  color: white;
  padding: 10px 12px;
  border-bottom: 1px solid #0b5f59;
}

.add-duty-icon {
  height: 18px;
  width: 18px;
}

.add-duty-title {
  font-size: 16px;
  font-weight: 600;
}

.add-duty-body {
  padding: 8px 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow-y: auto;
}

.duty-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.duty-label {
  padding-left: 0;
  font-weight: 600;
}

.duty-save {
  margin: 12px 14px 14px;
  align-self: flex-start;
}

select:disabled {
  background: #dddddd;
}
</style>

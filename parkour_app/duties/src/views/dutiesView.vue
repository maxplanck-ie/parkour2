<template>
  <div class="header" style="padding: 5px, margin: 5px">Manage Duties</div>
  <div style="padding: 15px">
    <div style="float: left; width: 78%">
      <div style="margin: 15px; border: 1px solid #006c66">
        <div
          style="
            padding: 7px 14px;
            height: 42px;
            background: #ecebe5;
            overflow-y: auto;
          "
        >
          <div>
            <span class="icon"><i class="fa fa-search"></i></span>
            <input
              class="search-bar"
              type="text"
              placeholder="Search..."
              @input="searchDuty"
            />
          </div>
        </div>
        <div style="padding: 15px">
          <ag-grid-vue
            class="ag-theme-alpine"
            style="height: 723px"
            rowSelection="multiple"
            animateRows="true"
            rowDragManaged="true"
            :columnDefs="columns"
            :rowData="dutiesList"
            @cellValueChanged="editDuty"
          />
        </div>
      </div>
    </div>
    <div
      style="
        margin: 15px;
        float: right;
        background: #ecebe5;
        width: 18%;
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
        Add Duty
      </div>
      <div style="padding-top: 6px">
        <div style="padding-left: 8px; font-weight: bold">Facility:</div>
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
        <div style="padding-left: 8px; font-weight: bold">
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
        <div style="padding-left: 8px; font-weight: bold">Backup Person:</div>
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
        <div style="padding-left: 8px; font-weight: bold">Start Date:</div>
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
        <div style="padding-left: 8px; font-weight: bold">End Date:</div>
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
        <div style="padding-left: 8px; font-weight: bold">Platform:</div>
        <div style="padding-left: 30px">
          <select
            class="dropdown-select"
            name="platform"
            id="platform"
            @change="updateDutyObject"
          >
            <option value="">Select</option>
            <option value="long">Long</option>
            <option value="short">Short</option>
          </select>
        </div>
      </div>
      <div style="padding-top: 6px">
        <div style="padding-left: 8px; font-weight: bold">Comments:</div>
        <div style="padding-left: 30px; padding-right: 30px">
          <textarea
            class="comment-textarea"
            id="comment"
            @input="updateDutyObject"
          />
        </div>
      </div>
      <button class="save-button" style="margin: 15px" @click="saveDuty()">
        Save
      </button>
    </div>
  </div>
</template>

<script>
import { AgGridVue } from "ag-grid-vue3";
import { showNotification, handleError, getProp } from "../utils/utilities";
import { toRaw } from "vue";
import axios from "axios";
import moment from "moment";
import "ag-grid-community/styles/ag-grid.css";
import "ag-grid-community/styles/ag-theme-alpine.css";

var axiosRef = axios.create({
  withCredentials: true,
  xsrfCookieName: "csrftoken",
  xsrfHeaderName: "X-CSRFTOKEN",
});

export default {
  name: "Duties",
  components: {
    AgGridVue,
  },
  data() {
    return {
      dutiesList: [],
      dutiesListBackup: [],
      newDuty: {},
      userList: [],
      userListFiltered: [],
      columns: [],
      loading: false,
    };
  },
  beforeMount() {
    this.getUsers();
  },
  created() {},
  watch: {},
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
    saveDuty() {
      let newDuty = toRaw(this.newDuty);
      if (
        !newDuty.main_name ||
        !newDuty.main_name ||
        !newDuty.backup_name ||
        !newDuty.start_date ||
        !newDuty.end_date ||
        !newDuty.platform
      ) {
        showNotification("Please check all the necessary fields.", "Error");
      } else {
        axiosRef
          .post("http://localhost:9980/api/duties/", newDuty)
          .then(this.getDuty(this.userList))
          .catch((error) => handleError(error))
          .finally(() => (this.loading = false));
      }
    },
    getDuty(userList) {
      axiosRef
        .get("http://localhost:9980/api/duties/")
        .then((response) => {
          let fetchedRows = [];
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
                  (matcherElement) =>
                    getProp(matcherElement, "id", 0) ==
                    getProp(element, "main_name", 0)
                ) || {},
                "first_name",
                "-"
              ),
              backup_name: getProp(
                userList.find(
                  (matcherElement) =>
                    getProp(matcherElement, "id", 0) ==
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
              platform: String(getProp(element, "platform", "-")).toLowerCase(),
              comment: getProp(element, "comment", ""),
            });
          });

          this.dutiesList = fetchedRows;
          this.dutiesListBackup = fetchedRows;
        })
        .finally(() => (this.loading = false));
    },
    editDuty(rowData) {
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
            newValue = newValue[0].toLowerCase() + newValue.slice(1);
            break;
          case "comment":
            newValue = newValue.trim();
            break;
        }
        axiosRef
          .patch("http://localhost:9980/api/duties/" + String(dutyId) + "/", {
            [columnName]: newValue,
          })
          .then()
          .catch((error) => handleError(error))
          .finally(() => (this.loading = false));
      }
    },
    searchDuty(event) {
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
                .includes(event.target.value.toLowerCase())) ||
            (element.end_date &&
              element.end_date
                .toLowerCase()
                .includes(event.target.value.toLowerCase())) ||
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
    getUsers() {
      axiosRef
        .get("http://localhost:9980/api/duties/responsibles")
        .then((response) => {
          let userList = getProp(response, "data", []);
          this.userList = userList;
          this.getDuty(userList);
          this.setColumns(userList);
        })
        .catch((error) => handleError(error))
        .finally(() => (this.loading = false));
    },
    setColumns(userList) {
      this.columns = [
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
          cellEditorParams: {
            values: userList.map((element) => element.first_name),
            valueListGap: 0,
          },
          rowDrag: true,
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
          cellEditorParams: {
            values: userList.map((element) => element.first_name),
            valueListGap: 0,
          },
        },
        {
          headerName: "Start Date",
          field: "start_date",
          cellEditor: "agDateStringCellEditor",
          cellEditorParams: {
            min: "2015-01-01",
            max: "2099-12-31",
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
          sort: "asc",
        },
        {
          headerName: "End Date",
          field: "end_date",
          cellEditor: "agDateStringCellEditor",
          cellEditorParams: {
            min: "2015-01-01",
            max: "2099-12-31",
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
        },
        {
          headerName: "Facility",
          field: "facility",
          minWidth: 150,
          flex: 2,
          filter: true,
          sortable: true,
          resizable: true,
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
            values: ["Long", "Short"],
            valueListGap: 0,
          },
          cellRenderer: (data) => {
            return data
              ? data.value[0].toUpperCase() + data.value.slice(1)
              : "-";
          },
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
            cols: 50,
          },
        },
      ];
    },
  },
};
</script>

<style>
.header {
  color: white;
  font-size: 20px;
  font-weight: bold;
  background: #006c66;
  padding: 16px 20px;
  max-height: 100vh;
}

.search-bar {
  height: 28px;
  width: 25%;
  padding: 0px 8px;
  border: 1px solid grey;
}

.dropdown-select,
.date-selector {
  width: 150px;
  height: 24px;
  background: whitesmoke;
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
</style>

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
      <div class="header-title" data-testid="duties-page-title">
        Manage Duties
      </div>

      <div class="sticky-actions">
        <div class="search-bar">
          <input
            id="search-bar"
            v-model="searchQuery"
            type="text"
            placeholder="Search"
          />
          <font-awesome-icon
            icon="fa-solid fa-magnifying-glass"
            style="color: darkgrey"
          />
        </div>

        <div class="duties-period-filter">
          <font-awesome-icon
            icon="fa-regular fa-calendar-days"
            style="color: darkgrey"
          />
          <select id="period-filter" v-model="selectedFilter">
            <option value="all">All</option>
            <option value="ongoing">Ongoing</option>
            <option value="upcoming">Upcoming</option>
            <option value="past-1-month">Past 1 Month</option>
            <option value="past-3-months">Past 3 Months</option>
            <option value="past-6-months">Past 6 Months</option>
            <option value="past-1-year">Past 1 Year</option>
          </select>
        </div>

        <button
          id="openAddDutyButton"
          class="header-button"
          type="button"
          aria-haspopup="dialog"
          :aria-expanded="showAddDutyDialog"
          @click="openAddDutyDialog"
        >
          <font-awesome-icon
            icon="fa-regular fa-calendar-plus"
            style="color: white"
          />
          <span>Add Duty</span>
        </button>
      </div>
    </div>

    <div class="table-container">
      <TabulatorTable
        v-if="dutiesList !== null && columnsList.length"
        ref="dutiesTable"
        tableId="dutiesTable"
        :rowData="dutiesList"
        :columnDefs="columnsList"
        :enableDefaultFilters="false"
        :tableOptions="tableOptions"
      />
    </div>

    <div
      v-if="showAddDutyDialog"
      class="popup-overlay"
      @click.self="closeAddDutyDialog"
    >
      <div
        ref="addDutyDialog"
        class="popup-container add-duty-popup"
        role="dialog"
        aria-modal="true"
        aria-labelledby="add-duty-title"
        tabindex="-1"
      >
        <div class="popup-header">
          <span id="add-duty-title" class="popup-title">Add Duty</span>
          <button
            class="popup-close-button"
            type="button"
            aria-label="Close add duty"
            @click="closeAddDutyDialog"
          >
            &times;
          </button>
        </div>
        <div class="popup-body">
          <div class="duty-field">
            <div class="text-medium duty-label">Facility:</div>
            <select
              class="dropdown-select"
              name="facility"
              id="facility"
              v-model="newDuty.facility"
              @change="onFacilityChange"
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
              v-model="newDuty.main_name"
              :disabled="!newDuty.facility"
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
              v-model="newDuty.backup_name"
              :disabled="!newDuty.facility"
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
              v-model="newDuty.start_date"
              min="2015-01-01"
              max="2099-12-31"
            />
          </div>
          <div class="duty-field">
            <div class="text-medium duty-label">End Date:</div>
            <input
              class="date-selector"
              type="date"
              id="end_date"
              name="end_date"
              v-model="newDuty.end_date"
              min="2015-01-01"
              max="2099-12-31"
            />
          </div>
          <div class="duty-field">
            <div class="text-medium duty-label">Platform:</div>
            <select
              class="dropdown-select"
              name="platform"
              id="platform"
              v-model="newDuty.platform"
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
              v-model="newDuty.comment"
            />
          </div>
        </div>
        <div class="popup-footer">
          <button
            id="cancelAddDutyButton"
            class="popup-button secondary"
            @click="closeAddDutyDialog"
          >
            Cancel
          </button>
          <button
            id="saveAddDutyButton"
            class="popup-button"
            @click="saveDuty()"
          >
            Save
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import TabulatorTable from "../components/TabulatorTableFull.vue";
import {
  showNotification,
  handleError,
  getProp,
  urlStringStartsWith,
  createAxiosObject,
  focusFirstElement,
  trapFocus
} from "../utilities/utilityFunctions";
import { toRaw } from "vue";
import moment from "moment";
import iconDutiesHeader from "../assets/icons/header_duties.svg";
import {
  dutiesColumnDefs,
  dutiesRowMatchesSearch
} from "../constants/dutiesConsts";

const axiosRef = createAxiosObject();

const urlStringStart = urlStringStartsWith();

export default {
  name: "Duties",
  components: {
    TabulatorTable
  },
  data() {
    return {
      iconDutiesHeader,
      dutiesList: null,
      dutiesListBackup: null,
      newDuty: {
        facility: "",
        main_name: "",
        backup_name: "",
        start_date: "",
        end_date: "",
        platform: "",
        comment: ""
      },
      userList: [],
      userListFiltered: [],
      columnsList: [],
      tableOptions: {
        index: "duty_id",
        placeholder: "No duties to show.",
        initialSort: [{ column: "start_date", dir: "asc" }],
        handleCellEdited: (cell) => this.editDuty(cell)
      },
      selectedFilter: "ongoing",
      searchQuery: "",
      showAddDutyDialog: false,
      addDutyPreviouslyFocusedElement: null
    };
  },
  setup() {},
  beforeMount() {
    this.getUsers();
  },
  mounted() {
    document.addEventListener("click", this.handleOutsideClick);
    document.addEventListener("keydown", this.handleKeyDown);
  },
  beforeUnmount() {
    document.removeEventListener("click", this.handleOutsideClick);
    document.removeEventListener("keydown", this.handleKeyDown);
  },
  created() {},
  watch: {
    selectedFilter(value) {
      this.getFilteredDuties(true, value);
    },
    searchQuery(value) {
      this.dutiesList = (this.dutiesListBackup || []).filter((row) =>
        dutiesRowMatchesSearch(row, value)
      );
    }
  },
  computed: {},
  methods: {
    openAddDutyDialog() {
      this.addDutyPreviouslyFocusedElement = document.activeElement;
      this.showAddDutyDialog = true;
      this.$nextTick(() => focusFirstElement(this.$refs.addDutyDialog));
    },
    closeAddDutyDialog() {
      if (!this.showAddDutyDialog) return;
      this.showAddDutyDialog = false;
      this.resetNewDuty();
      const returnFocusTo = this.addDutyPreviouslyFocusedElement;
      this.addDutyPreviouslyFocusedElement = null;
      this.$nextTick(() => returnFocusTo?.focus?.());
    },
    handleOutsideClick(event) {
      const dialog = this.$refs.addDutyDialog;
      const button = this.$el.querySelector?.("#openAddDutyButton");
      if (
        this.showAddDutyDialog &&
        dialog &&
        !dialog.contains(event.target) &&
        !button?.contains(event.target)
      ) {
        this.closeAddDutyDialog();
      }
    },
    handleKeyDown(event) {
      if (!this.showAddDutyDialog) return;
      if (event.key === "Escape") {
        event.preventDefault();
        this.closeAddDutyDialog();
        return;
      }
      trapFocus(event, this.$refs.addDutyDialog);
    },
    resetNewDuty() {
      this.newDuty = {
        facility: "",
        main_name: "",
        backup_name: "",
        start_date: "",
        end_date: "",
        platform: "",
        comment: ""
      };
      this.userListFiltered = [];
    },
    onFacilityChange() {
      this.newDuty.main_name = "";
      this.newDuty.backup_name = "";
      this.userListFiltered = toRaw(this.userList).filter(
        (element) => element.facility === this.newDuty.facility
      );
    },
    async saveDuty() {
      let newDuty = toRaw(this.newDuty);
      if (
        !newDuty.facility ||
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
            this.closeAddDutyDialog();

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
      const oldValue = String(cell.getOldValue() ?? "");
      let newValue = String(cell.getValue() ?? "");

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
          case "end_date":
            newValue = moment(newValue).format("YYYY-MM-DD");
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
      this.columnsList = dutiesColumnDefs(userList);
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

.styled-box {
  height: 35px;
  padding: 0px 8px;
  border: 1px solid grey;
  background: whitesmoke;
  outline: none;
  border-top-right-radius: 8px;
  border-bottom-right-radius: 8px;
}

/* Header: title-left, search/filter/add-duty-right, matching the other
   Tabulator views (see e.g. librariesAndSamplesView.vue, invoicingView.vue). */
.header {
  justify-content: flex-start;
  gap: 10px;
}

.header-title {
  width: auto;
  flex: 1 1 220px;
  min-width: 0;
  margin-right: 16px;
}

.sticky-actions {
  margin-left: auto;
}

.duties-period-filter {
  display: flex;
  align-items: center;
  gap: 8px;
  height: var(--header-control-height);
  min-height: var(--header-control-height);
  box-sizing: border-box;
  padding: 0 12px;
  border: 1px solid rgba(0, 0, 0, 0.18);
  border-radius: 8px;
  background-color: #ffffff;
}

.duties-period-filter select {
  border: none;
  outline: none;
  font-size: var(--header-control-font-size);
  color: #333;
  background: none;
}

.table-container {
  flex: 1;
  min-height: 0;
}

.add-duty-popup {
  width: min(420px, 92vw);
  max-height: 85vh;
  overflow: hidden;
}

.add-duty-popup .popup-body {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
}

.add-duty-popup .comment-textarea {
  height: 120px;
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
  font-size: 12px;
  outline: none;
  font-size: 14px;
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

.duty-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.duty-label {
  padding-left: 0;
  font-weight: 600;
}

select:disabled {
  background: #dddddd;
}
</style>

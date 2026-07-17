<template>
  <div class="parent-container">
    <!-- Loading overlay -->
    <div v-if="loading || fakeLoading" class="loading-overlay">
      <div v-if="!fakeLoading" class="spinner"></div>
      <p v-if="!fakeLoading">
        Loading <span style="font-weight: bold">Invoicing</span>...
      </p>
    </div>

    <!-- Header -->
    <div class="header">
      <div class="header-logo" style="display: inline; margin-right: 10px">
        <img
          :src="iconHeader"
          alt="Invoicing"
          width="42"
          height="42"
          style="display: block"
        />
      </div>
      <div class="header-title" style="display: inline">Invoicing</div>

      <!-- Sticky right section for filters and report actions -->
      <div class="sticky-actions">
        <div class="search-bar">
          <input v-model="searchQuery" type="text" placeholder="Search" />
          <font-awesome-icon
            icon="fa-solid fa-magnifying-glass"
            style="color: darkgrey"
          />
        </div>

        <!-- Date range filter (billing months derived from the picked date) -->
        <div class="date-filters">
          <div class="date-filter">
            <label for="invoicingStart">From</label>
            <input
              id="invoicingStart"
              v-model="startDate"
              type="date"
              :class="{ 'invalid-date': !startDateValid }"
            />
          </div>
          <div class="date-filter">
            <label for="invoicingEnd">To</label>
            <input
              id="invoicingEnd"
              v-model="endDate"
              type="date"
              :class="{ 'invalid-date': !endDateValid }"
            />
          </div>
        </div>

        <!-- Report actions -->
        <button class="header-button" @click="downloadReport">
          <font-awesome-icon icon="fa-solid fa-download" style="color: white" />
          <span> Download Report </span>
        </button>
        <button class="header-button" @click="showUploadPopup = true">
          <font-awesome-icon icon="fa-solid fa-upload" style="color: white" />
          <span> Upload Reports </span>
        </button>
        <button class="header-button" @click="openViewReports">
          <font-awesome-icon
            icon="fa-solid fa-folder-open"
            style="color: white"
          />
          <span> View Uploaded Reports </span>
        </button>
      </div>
    </div>

    <!-- Main content section with table -->
    <div class="table-container">
      <TabulatorTable
        v-if="!loading"
        ref="tabulatorTableRef"
        :rowData="filteredRows"
        :columnDefs="columnsList"
        :enableDefaultFilters="false"
        :tableOptions="tableOptions"
      />
    </div>

    <!-- Upload Reports popup -->
    <div v-if="showUploadPopup" class="popup-overlay">
      <div class="popup-container" :style="{ width: '500px', height: '260px' }">
        <div class="popup-header">
          <span class="popup-title">Upload Reports</span>
          <button class="popup-close-button" @click="showUploadPopup = false">
            &times;
          </button>
        </div>
        <div class="popup-body">
          <div class="invoicing-form-row">
            <label>Select Month</label>
            <input v-model="uploadDate" type="date" />
          </div>
          <div class="invoicing-form-row">
            <label>Browse Report</label>
            <input ref="uploadFileInput" type="file" />
          </div>
        </div>
        <div class="popup-footer">
          <button class="popup-button yes-button" @click="uploadReport">
            Upload
          </button>
          <button
            class="popup-button secondary"
            @click="showUploadPopup = false"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>

    <!-- View Uploaded Reports popup: lists everything in the invoicing media dir -->
    <div v-if="showViewReportsPopup" class="popup-overlay">
      <div class="popup-container" :style="{ width: '640px', height: '520px' }">
        <div class="popup-header">
          <span class="popup-title">View Uploaded Reports</span>
          <button
            class="popup-close-button"
            @click="showViewReportsPopup = false"
          >
            &times;
          </button>
        </div>
        <div class="popup-body">
          <div
            v-if="uploadedReports.length === 0"
            style="text-align: center; padding: 30px; color: #888"
          >
            No uploaded reports found in the invoicing media directory.
          </div>
          <div v-else class="uploaded-reports-list" @scroll="onReportsScroll">
            <div
              v-for="file in visibleReports"
              :key="file.path"
              class="uploaded-report-item"
            >
              <div class="uploaded-report-info">
                <font-awesome-icon
                  icon="fa-solid fa-file-excel"
                  style="color: #1d6f42; margin-right: 8px"
                />
                <div>
                  <div class="uploaded-report-name">{{ file.name }}</div>
                  <div class="uploaded-report-meta">
                    {{ file.path }} · {{ formatSize(file.size) }} ·
                    {{ file.modified }}
                  </div>
                </div>
              </div>
              <a
                class="popup-button yes-button uploaded-report-download"
                :href="file.url"
                :download="file.name"
              >
                Download
              </a>
            </div>
          </div>
        </div>
        <div class="popup-footer">
          <span
            v-if="uploadedReports.length > 0"
            class="uploaded-report-meta"
            style="margin-right: auto"
          >
            Showing {{ visibleReports.length }} of
            {{ uploadedReports.length }}
          </span>
          <button
            class="popup-button secondary"
            @click="showViewReportsPopup = false"
          >
            Close
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
  createAxiosObject,
  urlStringStartsWith
} from "../utilities/utilityFunctions";
import { invoicingColumnDefs } from "../constants/invoicingConsts";
import { isValidDate, formatDateForInput } from "../utilities/dateUtils";
import iconHeader from "../assets/icons/header_statistics.svg";

const axiosRef = createAxiosObject();
const urlStringStart = urlStringStartsWith();
const REPORTS_PAGE_SIZE = 20;

function todayString() {
  return formatDateForInput(new Date());
}

function monthOf(dateString) {
  return (dateString || "").slice(0, 7);
}

export default {
  name: "InvoicingView",
  components: {
    TabulatorTable
  },
  data() {
    return {
      iconHeader,
      loading: true,
      fakeLoading: false,
      invoicingList: [],
      columnsList: [],
      readLengthNames: {},
      libraryProtocolNames: {},
      searchQuery: "",
      startDate: todayString(),
      endDate: todayString(),
      startDateValid: true,
      endDateValid: true,
      dateChangeTimer: null,
      showUploadPopup: false,
      showViewReportsPopup: false,
      uploadDate: todayString(),
      uploadedReports: [],
      visibleReportsCount: REPORTS_PAGE_SIZE,
      tableOptions: {
        index: "request",
        placeholder: "No invoicing items to show."
      }
    };
  },
  computed: {
    filteredRows() {
      const query = this.searchQuery.trim().toLowerCase();
      if (!query) return this.invoicingList;
      return this.invoicingList.filter((row) =>
        [row.request, row.cost_unit, row.sequencer, row.library_protocol]
          .join(" ")
          .toLowerCase()
          .includes(query)
      );
    },
    visibleReports() {
      return this.uploadedReports.slice(0, this.visibleReportsCount);
    }
  },
  watch: {
    startDate(newVal) {
      this.handleDateChange("start", newVal);
    },
    endDate(newVal) {
      this.handleDateChange("end", newVal);
    }
  },
  async mounted() {
    this.columnsList = invoicingColumnDefs();
    await this.fetchLookups();
    await this.getInvoicing();
  },
  beforeUnmount() {
    if (this.dateChangeTimer) {
      clearTimeout(this.dateChangeTimer);
    }
  },
  methods: {
    fakeLoadingStart() {
      this.fakeLoading = true;
    },
    fakeLoadingStop() {
      setTimeout(() => {
        this.fakeLoading = false;
      }, 300);
    },
    async fetchLookups() {
      try {
        const [readLengths, protocols] = await Promise.all([
          axiosRef.get(urlStringStart + "/api/read_lengths_invoicing/"),
          axiosRef.get(urlStringStart + "/api/library_protocols_invoicing/")
        ]);
        (readLengths.data || []).forEach((item) => {
          this.readLengthNames[item.id] = item.name;
        });
        (protocols.data || []).forEach((item) => {
          this.libraryProtocolNames[item.id] = item.name;
        });
      } catch (error) {
        handleError(error);
      }
    },
    handleDateChange(type, value) {
      clearTimeout(this.dateChangeTimer);
      this[`${type}DateValid`] = isValidDate(value);
      if (!this[`${type}DateValid`]) return;
      this.dateChangeTimer = setTimeout(() => {
        this.getInvoicing();
      }, 500);
    },
    async getInvoicing() {
      if (!isValidDate(this.startDate) || !isValidDate(this.endDate)) {
        return;
      }
      if (this.startDate > this.endDate) {
        this.startDateValid = false;
        this.endDateValid = false;
        showNotification(
          "The 'From' date cannot be later than the 'To' date.",
          "warning"
        );
        return;
      }
      this.startDateValid = true;
      this.endDateValid = true;
      this.loading = true;
      try {
        const response = await axiosRef.get(
          urlStringStart + "/api/invoicing/",
          {
            params: {
              start: monthOf(this.startDate),
              end: monthOf(this.endDate)
            }
          }
        );
        this.invoicingList = (response.data || [])
          .filter((element) => element.library_protocol !== "")
          .map((element) => {
            const sequencerList = [
              ...new Set((element.sequencer || []).map((x) => x.sequencer_name))
            ].sort();
            const percentage = (element.percentage || [])
              .map((flowcell) =>
                (flowcell.pools || []).map((p) => p.percentage).join(", ")
              )
              .join("; ");
            const readLength = [...(element.read_length || [])]
              .map((id) => this.readLengthNames[id] || id)
              .sort()
              .join("; ");
            // Each flowcell entry is "dd.mm.yyyy FLOWCELLID"; split into
            // separate Date and Flowcell ID columns.
            const flowcellEntries = element.flowcell || [];
            const flowcellDates = flowcellEntries.map(
              (entry) => entry.split(" ")[0]
            );
            const flowcellIds = flowcellEntries.map((entry) =>
              entry.split(" ").slice(1).join(" ")
            );
            return {
              request: element.request || "",
              cost_unit: element.cost_unit || "",
              sequencer: sequencerList.join("; "),
              flowcell_date: flowcellDates.join("; "),
              flowcell_id: flowcellIds.join("; "),
              pool: (element.pool || []).join("; "),
              percentage,
              read_length: readLength,
              num_libraries_samples_show:
                element.num_libraries_samples_show || "",
              library_protocol:
                this.libraryProtocolNames[element.library_protocol] ||
                element.library_protocol ||
                "",
              fixed_costs: element.fixed_costs,
              sequencing_costs: element.sequencing_costs,
              preparation_costs: element.preparation_costs,
              variable_costs: element.variable_costs,
              total_costs: element.total_costs
            };
          });
      } catch (error) {
        handleError(error);
      } finally {
        this.loading = false;
      }
    },
    downloadReport() {
      const params = new URLSearchParams({
        start: monthOf(this.startDate),
        end: monthOf(this.endDate)
      });
      window.open(
        `${urlStringStart}/api/invoicing/download/?${params.toString()}`,
        "_blank"
      );
    },
    async uploadReport() {
      const fileInput = this.$refs.uploadFileInput;
      const file = fileInput && fileInput.files && fileInput.files[0];
      if (!isValidDate(this.uploadDate)) {
        showNotification("Please select the month.", "warning");
        return;
      }
      if (!file) {
        showNotification("Please select the report file.", "warning");
        return;
      }
      const payload = new FormData();
      payload.append("report", file);
      payload.append("month", monthOf(this.uploadDate));
      try {
        await axiosRef.post(
          `${urlStringStart}/api/invoicing/upload/`,
          payload,
          { headers: { "Content-Type": "multipart/form-data" } }
        );
        showNotification("Report has been successfully uploaded.", "success");
        this.showUploadPopup = false;
      } catch (error) {
        showNotification("Error while uploading the report: " + error, "error");
      }
    },
    async openViewReports() {
      this.showViewReportsPopup = true;
      this.visibleReportsCount = REPORTS_PAGE_SIZE;
      try {
        const response = await axiosRef.get(
          `${urlStringStart}/api/invoicing/reports/`
        );
        this.uploadedReports = response.data || [];
      } catch (error) {
        handleError(error);
      }
    },
    onReportsScroll(event) {
      const el = event.target;
      const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 80;
      if (
        nearBottom &&
        this.visibleReportsCount < this.uploadedReports.length
      ) {
        this.visibleReportsCount += REPORTS_PAGE_SIZE;
      }
    },
    formatSize(bytes) {
      if (bytes === null || bytes === undefined) return "";
      if (bytes < 1024) return `${bytes} B`;
      if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
      return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
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

.invoicing-filter {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-right: 10px;
  color: white;
  font-size: 13px;
  white-space: nowrap;
}

.invoicing-filter input,
.invoicing-filter select {
  padding: 4px 6px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 13px;
}

.invoicing-form-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.invoicing-form-row label {
  width: 110px;
  font-weight: bold;
}

.invoicing-form-row input {
  flex: 1;
  padding: 5px 6px;
  border: 1px solid #ccc;
  border-radius: 4px;
}

.uploaded-reports-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 380px;
  overflow-y: auto;
}

.uploaded-report-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 10px;
  border: 1px solid #eee;
  border-radius: 6px;
}

.uploaded-report-info {
  display: flex;
  align-items: center;
  overflow: hidden;
}

.uploaded-report-name {
  font-weight: bold;
  font-size: 13px;
}

.uploaded-report-meta {
  font-size: 11px;
  color: #888;
}

.uploaded-report-download {
  text-decoration: none;
  white-space: nowrap;
  margin-left: 10px;
}
</style>

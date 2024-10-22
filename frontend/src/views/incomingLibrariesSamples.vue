<template>
  <div class="parent-container" style="padding: 15px; display: flex; flex-wrap: wrap; justify-content: space-between;">
    <div class="table-container" style="flex: 1; margin-bottom: 20px;">
      <div style="margin: 15px; border: 1px solid #006c66;">
        <TabulatorTable :rowData="LibrariesSamplesList" :columnDefs="columnsList"
          @cellValueChanged="onCellValueChanged" />
      </div>
    </div>
  </div>
</template>

<script>
import TabulatorTable from "../components/TabulatorTable.vue";
import { showNotification, handleError, createAxiosObject, urlStringStartsWith } from "../utils/utilities";

const axiosRef = createAxiosObject();
const urlStringStart = urlStringStartsWith();

export default {
  name: "LibrariesSamples",
  components: {
    TabulatorTable,
  },
  data() {
    return {
      LibrariesSamplesList: null,
      columnsList: [],
      selectedFilter: "all",
    };
  },
  beforeMount() {
    this.getLibrariesSamples();
    this.setColumns();
  },
  watch: {
    selectedFilter() {
      this.getLibrariesSamples();
    },
  },
  methods: {
    async getLibrariesSamples() {
      try {
        const response = await axiosRef.get(urlStringStart + "/api/incoming_libraries/");
        const fetchedRows = response.data.map((element) => ({
          request_id: element.id,
          name: element.name,
          type: element.barcode[2] === "L" ? "L" : "S",
          barcode: element.barcode,
          input_type: element.input_type || "-",
          library_protocol: element.library_protocol,
          concentration: element.concentration || "-",
          mean_fragment_size: element.mean_fragment_size || "-",
          rqn: element.rna_quality || "-",
        }));
        this.LibrariesSamplesList = fetchedRows;
      } catch (error) {
        handleError(error);
      }
    },

    setColumns() {
      this.columnsList = [
        { title: "Name", field: "name", minWidth: 200, width: "30%", editor: "input" },
        { title: "Type", field: "type", minWidth: 150, width: "20%" },
        { title: "Barcode", field: "barcode", minWidth: 150, width: "20%" },
        { title: "Input Type", field: "input_type", minWidth: 150, width: "20%", editor: "input" },
        { title: "Protocol", field: "library_protocol", minWidth: 150, width: "20%", editor: "input" },
        { title: "ng/ul", field: "concentration", minWidth: 100, width: "20%", editor: "input" },
        { title: "bp", field: "mean_fragment_size", minWidth: 100, width: "20%", editor: "input" },
        { title: "RQN", field: "rqn", minWidth: 100, width: "20%", editor: "input" },
      ];
    },

    async onCellValueChanged(updatedData) {
      try {
        await axiosRef.post(urlStringStart + "/api/incoming_libraries/", updatedData);
        showNotification("Update successful", "success");
      } catch (error) {
        handleError(error);
      }
    },
  },
};
</script>

<style scoped></style>

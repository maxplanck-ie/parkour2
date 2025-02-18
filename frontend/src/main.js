import "./assets/main.css";
import "ag-grid-community/styles/ag-grid.css";
import "ag-grid-community/styles/ag-theme-alpine.css";
import "vue-toastification/dist/index.css";

import { createApp } from "vue";
import vueApp from "./vueApp.vue";
import router from "./router/router.js";
import toast from "vue-toastification";
import { library } from "@fortawesome/fontawesome-svg-core";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import {
  faChalkboardUser,
  faMagnifyingGlass,
  faFilter,
  faColumns,
  faFileExcel,
  faLayerGroup
} from "@fortawesome/free-solid-svg-icons";
import {
  faCalendarPlus,
  faCalendarDays
} from "@fortawesome/free-regular-svg-icons";

const app = createApp(vueApp);

library.add(
  faChalkboardUser,
  faMagnifyingGlass,
  faCalendarPlus,
  faCalendarDays,
  faFilter,
  faColumns,
  faFileExcel,
  faLayerGroup
);

app.use(router);
app.use(toast);
app.component("font-awesome-icon", FontAwesomeIcon);
app.config.productionTip = false;
app.mount("#app");

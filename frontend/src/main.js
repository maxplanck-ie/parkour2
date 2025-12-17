import "./assets/css_main.css";
import "ag-grid-community/styles/ag-grid.css";
import "ag-grid-community/styles/ag-theme-alpine.css";
import "vue-toastification/dist/index.css";

import { createApp } from "vue";
import vueApp from "./vueApp.vue";
import router from "./router/appRoutes.js";
import toast from "vue-toastification";
import { library } from "@fortawesome/fontawesome-svg-core";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import {
  faChalkboardUser,
  faMagnifyingGlass,
  faFilter,
  faColumns,
  faFileExcel,
  faLayerGroup,
  faCaretDown,
  faSquarePlus,
  faTrash,
  faAngleLeft,
  faAngleRight,
  faCircleInfo,
  faCircleCheck,
  faCircleExclamation,
  faFileLines,
  faDownload,
  faXmark
} from "@fortawesome/free-solid-svg-icons";
import {
  faCalendarPlus,
  faCalendarDays
} from "@fortawesome/free-regular-svg-icons";
import { createPinia } from "pinia";
import { ModuleRegistry, AllCommunityModule } from "ag-grid-community";
import { initParentMessageBridge } from "./utilities/iframeMessaging";

ModuleRegistry.registerModules([AllCommunityModule]);

const app = createApp(vueApp);

library.add(
  faChalkboardUser,
  faMagnifyingGlass,
  faCalendarPlus,
  faCalendarDays,
  faFilter,
  faColumns,
  faFileExcel,
  faLayerGroup,
  faCaretDown,
  faSquarePlus,
  faTrash,
  faAngleLeft,
  faAngleRight,
  faCircleInfo,
  faCircleCheck,
  faCircleExclamation,
  faFileLines,
  faDownload,
  faXmark
);

app.use(router);
app.use(toast);
app.use(createPinia());
app.component("font-awesome-icon", FontAwesomeIcon);
app.config.productionTip = false;
initParentMessageBridge();
app.mount("#app");

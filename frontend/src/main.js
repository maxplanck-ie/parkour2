import "./assets/main.css";
import "ag-grid-community/styles/ag-grid.css";
import "ag-grid-community/styles/ag-theme-alpine.css";
import "vue-toastification/dist/index.css";
import "floating-vue/dist/style.css";

import { createApp } from "vue";
import vueApp from "./vueApp.vue";
import router from "./router/router.js";
import toast from "vue-toastification";
import { library } from "@fortawesome/fontawesome-svg-core";
import floatingVue from "floating-vue";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import {
  faChalkboardUser,
  faMagnifyingGlass,
  faFileText,
  faFlask,
  faArrowDown,
  faSortAmountDesc,
  faLevelDown,
  faPieChart,
  faLineChart,
  faCog,
  faBook,
  faCalendar,
  faSignOut,
  faCogs,
  faTable,
  faEur,
  faDna,
  faNavicon,
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
  faFileText,
  faFlask,
  faArrowDown,
  faCogs,
  faTable,
  faSortAmountDesc,
  faLevelDown,
  faEur,
  faPieChart,
  faLineChart,
  faCog,
  faBook,
  faCalendar,
  faSignOut,
  faDna,
  faNavicon
);

app.use(router);
app.use(toast);
app.use(floatingVue);
app.component("font-awesome-icon", FontAwesomeIcon);
app.config.productionTip = false;
app.mount("#app");

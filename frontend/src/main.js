import "./assets/css/css_main.css";
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
  faPaperPlane,
  faTrash,
  faPen,
  faAngleLeft,
  faAngleRight,
  faCircleInfo,
  faCircleCheck,
  faCircleExclamation,
  faEraser,
  faFileLines,
  faCopy,
  faDownload,
  faPaste,
  faScissors,
  faWandMagicSparkles,
  faXmark,
  faDesktop,
  faKeyboard,
  faFolderOpen,
  faTableCells,
  faPenToSquare,
  faCloudArrowUp,
  faLightbulb,
  faFlask,
  faFloppyDisk,
  faMoneyBill,
  faArrowDown,
  faCogs,
  faTable,
  faArrowDownWideShort,
  faTurnDown,
  faEuroSign,
  faChartBar,
  faChartLine,
  faGear,
  faRightFromBracket
} from "@fortawesome/free-solid-svg-icons";
import {
  faCalendarPlus,
  faCalendarDays
} from "@fortawesome/free-regular-svg-icons";
import { createPinia } from "pinia";
import { ModuleRegistry, AllCommunityModule } from "ag-grid-community";
import { initParentMessageBridge } from "./utilities/iframeMessagingUtils";

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
  faPaperPlane,
  faTrash,
  faPen,
  faAngleLeft,
  faAngleRight,
  faCircleInfo,
  faCircleCheck,
  faCircleExclamation,
  faEraser,
  faFileLines,
  faCopy,
  faDownload,
  faPaste,
  faScissors,
  faWandMagicSparkles,
  faXmark,
  faDesktop,
  faKeyboard,
  faFolderOpen,
  faTableCells,
  faPenToSquare,
  faCloudArrowUp,
  faLightbulb,
  faFlask,
  faFloppyDisk,
  faMoneyBill,
  faArrowDown,
  faCogs,
  faTable,
  faArrowDownWideShort,
  faTurnDown,
  faEuroSign,
  faChartBar,
  faChartLine,
  faGear,
  faRightFromBracket
);

app.use(router);
app.use(toast);
app.use(createPinia());
app.component("font-awesome-icon", FontAwesomeIcon);
app.config.productionTip = false;
initParentMessageBridge();
const tooltip = {
  el: null,
  active: null
};

function setupGlobalTooltips() {
  if (tooltip.el) return;
  const el = document.createElement("div");
  el.className = "app-tooltip";
  document.body.appendChild(el);
  tooltip.el = el;

  const hideTooltip = () => {
    if (!tooltip.el) return;
    tooltip.el.classList.remove("is-visible");
    tooltip.active = null;
  };

  const showTooltip = (text) => {
    if (!tooltip.el) return;
    tooltip.el.textContent = text;
    tooltip.el.classList.add("is-visible");
  };

  const findTooltipTarget = (start) => {
    let node = start;
    while (node && node !== document.body) {
      if (node.dataset?.tooltipDisabled === "true") return null;
      const stored = node.getAttribute("data-tooltip-original");
      if (stored) return { el: node, text: stored };
      const title = node.getAttribute("title");
      if (title) return { el: node, text: title };
      node = node.parentElement;
    }
    return null;
  };

  document.addEventListener(
    "mouseover",
    (event) => {
      const target = findTooltipTarget(event.target);
      if (!target) {
        hideTooltip();
        return;
      }
      if (
        tooltip.active?.el === target.el &&
        tooltip.active?.text === target.text
      )
        return;
      if (!target.el.getAttribute("data-tooltip-original")) {
        target.el.setAttribute("data-tooltip-original", target.text);
        target.el.removeAttribute("title");
      }
      tooltip.active = target;
      showTooltip(target.text);
    },
    true
  );

  document.addEventListener(
    "mouseout",
    (event) => {
      if (!tooltip.active) return;
      if (tooltip.active.el.contains(event.relatedTarget)) return;
      hideTooltip();
    },
    true
  );

  document.addEventListener(
    "mousemove",
    (event) => {
      if (!tooltip.active || !tooltip.el) return;
      const padding = 12;
      let left = event.clientX + padding;
      let top = event.clientY + padding;
      tooltip.el.style.left = `${left}px`;
      tooltip.el.style.top = `${top}px`;
      const rect = tooltip.el.getBoundingClientRect();
      if (rect.right > window.innerWidth - 8) {
        left = event.clientX - rect.width - padding;
        tooltip.el.style.left = `${left}px`;
      }
      if (rect.bottom > window.innerHeight - 8) {
        top = event.clientY - rect.height - padding;
        tooltip.el.style.top = `${top}px`;
      }
    },
    true
  );

  document.addEventListener(
    "scroll",
    () => {
      if (tooltip.active) hideTooltip();
    },
    true
  );
}

setupGlobalTooltips();
app.mount("#app");

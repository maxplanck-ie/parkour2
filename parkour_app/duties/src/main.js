import "./assets/main.css";

import { createApp } from "vue";
import { createPinia } from "pinia";

import vueApp from "./vueApp.vue";
import router from "./router/router.js";

const app = createApp(vueApp);
const store = createPinia();

app.use(store);
app.use(router);

app.mount("#app");

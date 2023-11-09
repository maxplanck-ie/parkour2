import { createRouter, createWebHistory } from "vue-router";
import dutiesView from "../views/dutiesView.vue";
import vueApp from "../vueApp.vue";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/",
      component: vueApp,
      children: [
        {
          path: "duties",
          name: "Duties List",
          component: dutiesView,
        },
      ],
    },
  ],
});

export default router;

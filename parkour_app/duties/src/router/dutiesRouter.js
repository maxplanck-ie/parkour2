import { createRouter, createWebHistory } from "vue-router";
import dutiesView from "../views/dutiesView.vue";
import ganttView from "../views/ganttView.vue";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/list",
      name: "Duties List",
      component: dutiesView,
    },
    {
      path: "/gantt",
      name: "Gantt View",
      component: ganttView,
    },
  ],
});

export default router;

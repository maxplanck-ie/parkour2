import { createRouter, createWebHistory } from "vue-router";
import dutiesView from "../views/dutiesView.vue";
import vueApp from "../vueApp.vue";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/vue/",
      component: vueApp,
      children: [
        {
          path: "duties",
          name: "Duties",
          component: dutiesView,
        },
      ],
    },
  ],
});

router.beforeEach((to, from, next) => {
  document.title = "Parkour LIMS | " + to.name;
  next();
});

export default router;

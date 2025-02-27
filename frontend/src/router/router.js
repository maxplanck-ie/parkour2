import { createRouter, createWebHistory } from "vue-router";
import dutiesView from "../views/dutiesView.vue";
import vueApp from "../vueApp.vue";
import IncomingLibrariesSamples from "../views/incomingLibrariesSamples.vue";
import libraryPreparation from "../views/libraryPreparation.vue";

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
          component: dutiesView
        },
        {
          path: "incoming_libraries_samples",
          name: "Incoming Libraries/Samples",
          component: IncomingLibrariesSamples
        },
        {
          path: "library_preparation",
          name: "Library Preparation",
          component: libraryPreparation
        }
      ]
    }
  ]
});

router.beforeEach((to, from, next) => {
  document.title = "Parkour LIMS | " + to.name;
  next();
});

export default router;

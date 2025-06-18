import { createRouter, createWebHistory } from "vue-router";
import dutiesView from "../views/dutiesView.vue";
import vueApp from "../vueApp.vue";
import librariesAndSamples from "../views/librariesAndSamples.vue";
import IncomingLibrariesSamples from "../views/incomingLibrariesSamples.vue";
import libraryPreparation from "../views/libraryPreparation.vue";
import pooling from "../views/pooling.vue";

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
        {
          path: "libraries_and_samples",
          name: "Libraries & Samples",
          component: librariesAndSamples,
        },
        {
          path: "incoming_libraries_samples",
          name: "Incoming Libraries/Samples",
          component: IncomingLibrariesSamples,
        },
        {
          path: "library_preparation",
          name: "Library Preparation",
          component: libraryPreparation,
        },
        {
          path: "Pooling",
          name: "Pooling",
          component: pooling,
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

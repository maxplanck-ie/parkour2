import { createRouter, createWebHistory } from "vue-router";
import dutiesView from "../views/dutiesView.vue";
import vueApp from "../vueApp.vue";
import librariesAndSamples from "../views/librariesAndSamplesView.vue";
import IncomingLibrariesSamples from "../views/incomingLibrariesSamplesView.vue";
import libraryPreparation from "../views/libraryPreparationView.vue";
import pooling from "../views/poolingView.vue";
import loadFlowcells from "../views/loadFlowcellsView.vue";
import IndexGeneratorView from "../views/indexGeneratorView.vue";
import notFoundView from "../views/notFoundView.vue";
import runStatisticsView from "../views/runStatisticsView.vue";
import invoicingView from "../views/invoicingView.vue";
import sequencesStatisticsView from "../views/sequencesStatisticsView.vue";
import usageView from "../views/usageView.vue";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/",
      component: vueApp,
      children: [
        {
          path: "",
          redirect: "/libraries_and_samples"
        },
        {
          path: "duties",
          name: "Duties",
          component: dutiesView
        },
        {
          path: "libraries_and_samples",
          name: "Libraries & Samples",
          component: librariesAndSamples
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
        },
        {
          path: "pooling",
          name: "Pooling",
          component: pooling
        },
        {
          path: "load_flowcells",
          name: "Load Flowcells",
          component: loadFlowcells
        },
        {
          path: "index_generator",
          name: "Index Generator",
          component: IndexGeneratorView
        },
        {
          path: "run_statistics",
          name: "Runs Statistics",
          component: runStatisticsView
        },
        {
          path: "invoicing",
          name: "Invoicing",
          component: invoicingView
        },
        {
          path: "sequences_statistics",
          name: "Sequenced Samples Statistics",
          component: sequencesStatisticsView
        },
        {
          path: "usage",
          name: "Usage",
          component: usageView
        },
        {
          path: "not_found",
          name: "Page Not Found",
          component: notFoundView
        },
        {
          path: ":pathMatch(.*)*",
          meta: {
            title: "Page Not Found"
          },
          component: notFoundView
        }
      ]
    }
  ]
});

router.beforeEach((to, from, next) => {
  document.title = "Parkour LIMS | " + (to.name || to.meta.title || "Page");
  next();
});

export default router;

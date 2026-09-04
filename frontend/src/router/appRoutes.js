import { createRouter, createWebHistory } from "vue-router";
import vueApp from "../vueApp.vue";

// Lazy-loaded per route so each view lands in its own chunk instead of one
// large bundle (see Vite's "chunks larger than 500 kB" build warning).
const dutiesView = () => import("../views/dutiesView.vue");
const librariesAndSamples = () =>
  import("../views/librariesAndSamplesView.vue");
const IncomingLibrariesSamples = () =>
  import("../views/incomingLibrariesSamplesView.vue");
const libraryPreparation = () => import("../views/libraryPreparationView.vue");
const pooling = () => import("../views/poolingView.vue");
const loadFlowcells = () => import("../views/loadFlowcellsView.vue");
const IndexGeneratorView = () => import("../views/indexGeneratorView.vue");
const notFoundView = () => import("../views/notFoundView.vue");
const runStatisticsView = () => import("../views/runStatisticsView.vue");
const invoicingView = () => import("../views/invoicingView.vue");
const sequencesStatisticsView = () =>
  import("../views/sequencesStatisticsView.vue");
const usageView = () => import("../views/usageView.vue");

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

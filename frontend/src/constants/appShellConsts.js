// Maps the `viewType` strings returned by GET /get_navigation_tree (still
// named after their ExtJS xtypes, e.g. "libraries-vue") to the Vue router
// path and FontAwesome icon each nav entry should use. Extend this table
// whenever a new top-level page is added to the navigation tree.
export const NAV_VIEW_TYPE_MAP = {
  "libraries-vue": {
    path: "/libraries_and_samples",
    icon: "fa-solid fa-flask"
  },
  "incoming-libraries-vue": {
    path: "/incoming_libraries_samples",
    icon: "fa-solid fa-arrow-down"
  },
  "index-generator-vue": { path: "/index_generator", icon: "fa-solid fa-cogs" },
  "library-preparation-vue": {
    path: "/library_preparation",
    icon: "fa-solid fa-table"
  },
  "pooling-vue": {
    path: "/pooling",
    icon: "fa-solid fa-arrow-down-wide-short"
  },
  "flowcells-vue": { path: "/load_flowcells", icon: "fa-solid fa-turn-down" },
  "invoicing-vue": { path: "/invoicing", icon: "fa-solid fa-euro-sign" },
  "usage-vue": { path: "/usage", icon: "fa-solid fa-chart-bar" },
  "run-statistics-vue": {
    path: "/run_statistics",
    icon: "fa-solid fa-chart-line"
  },
  "sequences-statistics-vue": {
    path: "/sequences_statistics",
    icon: "fa-solid fa-chart-line"
  }
};

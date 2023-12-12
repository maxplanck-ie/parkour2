Ext.define("MainHub.store.libraries.IndexPairs", {
  extend: "Ext.data.Store",
  storeId: "IndexPairs",

  requires: ["MainHub.model.libraries.IndexPair"],

  model: "MainHub.model.libraries.IndexPair",

  proxy: {
    type: "ajax",
    url: "api/index_pairs/",
    timeout: 1000000,
    pageParam: false, // to remove param "page"
    startParam: false, // to remove param "start"
    limitParam: false, // to remove param "limit"
    noCache: false, // to remove param "_dc",
    reader: {
      type: "json",
      rootProperty: "data",
      successProperty: "success",
    },
  },
});

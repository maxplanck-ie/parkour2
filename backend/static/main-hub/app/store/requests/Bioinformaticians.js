Ext.define("MainHub.store.requests.Bioinformaticians", {
  extend: "Ext.data.Store",
  storeId: "Bioinformaticians",

  requires: ["MainHub.model.requests.Bioinformatician"],

  model: "MainHub.model.requests.Bioinformatician",

  proxy: {
    url: "api/bioinformaticians/",
    type: "ajax",
    timeout: 1000000,
    pageParam: false, // to remove param "page"
    startParam: false, // to remove param "start"
    limitParam: false, // to remove param "limit"
    noCache: false, // to remove param "_dc"
  },
});

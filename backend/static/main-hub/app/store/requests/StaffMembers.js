Ext.define("MainHub.store.requests.StaffMembers", {
  extend: "Ext.data.Store",
  storeId: "StaffMembers",

  requires: ["MainHub.model.requests.StaffMember"],

  model: "MainHub.model.requests.StaffMember",

  proxy: {
    url: "api/staff_members/",
    type: "ajax",
    timeout: 1000000,
    pageParam: false, // to remove param "page"
    startParam: false, // to remove param "start"
    limitParam: false, // to remove param "limit"
    noCache: false, // to remove param "_dc"
  },
});

Ext.define('MainHub.store.usage.Organizations', {
  extend: 'Ext.data.Store',
  storeId: 'UsageOrganizations',

  requires: [
    'MainHub.model.usage.ChartPolar'
  ],

  model: 'MainHub.model.usage.ChartPolar',

  proxy: {
    type: 'ajax',
    url: 'api/usage/organizations/',
    timeout: 1000000,
    pageParam: false,   // to remove param "page"
    startParam: false,  // to remove param "start"
    limitParam: false,  // to remove param "limit"
    noCache: false      // to remove param "_dc",
  },

  getId: function () {
    return 'UsageOrganizations';
  }
});

Ext.define('MainHub.store.requests.CostUnits', {
  extend: 'Ext.data.Store',
  storeId: 'CostUnits',

  requires: [
    'MainHub.model.requests.CostUnit'
  ],

  model: 'MainHub.model.requests.CostUnit',

  proxy: {
    url: 'api/cost_units/',
    type: 'ajax',
    timeout: 1000000,
    pageParam: false,  // to remove param "page"
    startParam: false, // to remove param "start"
    limitParam: false, // to remove param "limit"
    noCache: false     // to remove param "_dc"
  }
});

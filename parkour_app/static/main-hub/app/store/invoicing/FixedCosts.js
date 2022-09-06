Ext.define('MainHub.store.invoicing.FixedCosts', {
  extend: 'Ext.data.Store',
  storeId: 'FixedCosts',

  requires: [
    'MainHub.model.invoicing.FixedCost'
  ],

  model: 'MainHub.model.invoicing.FixedCost',

  sorters: [{
    property: 'name',
    direction: 'ASC'
  }],

  proxy: {
    type: 'ajax',
    pageParam: false,   // to remove param "page"
    startParam: false,  // to remove param "start"
    limitParam: false,  // to remove param "limit"
    noCache: false,     // to remove param "_dc",
    actionMethods: {
      read: 'GET',
      update: 'PUT'
    },
    api: {
      read: 'api/fixed_costs/',
      update: ''
    }
  }
});

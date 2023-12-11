Ext.define('MainHub.store.invoicing.SequencingCosts', {
  extend: 'Ext.data.Store',
  storeId: 'SequencingCosts',

  requires: [
    'MainHub.model.invoicing.SequencingCost'
  ],

  model: 'MainHub.model.invoicing.SequencingCost',

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
      read: 'api/sequencing_costs/',
      update: ''
    }
  }
});

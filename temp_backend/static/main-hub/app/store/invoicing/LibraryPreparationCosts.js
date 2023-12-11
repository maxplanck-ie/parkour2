Ext.define('MainHub.store.invoicing.LibraryPreparationCosts', {
  extend: 'Ext.data.Store',
  storeId: 'LibraryPreparationCosts',

  requires: [
    'MainHub.model.invoicing.LibraryPreparationCost'
  ],

  model: 'MainHub.model.invoicing.LibraryPreparationCost',

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
      read: 'api/library_preparation_costs/',
      update: ''
    }
  }
});

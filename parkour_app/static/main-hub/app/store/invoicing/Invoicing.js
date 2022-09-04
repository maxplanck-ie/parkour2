Ext.define('MainHub.store.invoicing.Invoicing', {
  extend: 'Ext.data.Store',
  storeId: 'Invoicing',

  requires: [
    'MainHub.model.invoicing.Request'
  ],

  model: 'MainHub.model.invoicing.Request',

  proxy: {
    type: 'ajax',
    url: 'api/invoicing/',
    pageParam: false,   // to remove param "page"
    startParam: false,  // to remove param "start"
    limitParam: false,  // to remove param "limit"
    noCache: false      // to remove param "_dc"
  },

  getId: function () {
    return 'Invoicing';
  }
});

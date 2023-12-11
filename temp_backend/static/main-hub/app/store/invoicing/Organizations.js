Ext.define('MainHub.store.invoicing.Organizations', {
  extend: 'Ext.data.Store',
  storeId: 'Organizations',

  requires: [
    'MainHub.model.invoicing.Organizations'
  ],

  model: 'MainHub.model.invoicing.Organizations',

  proxy: {
    type: 'ajax',
    url: 'api/organizations/',
    pageParam: false,   // to remove param "page"
    startParam: false,  // to remove param "start"
    limitParam: false,  // to remove param "limit"
    noCache: false      // to remove param "_dc",
  }
});

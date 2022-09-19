Ext.define('MainHub.store.libraries.IndexTypes', {
  extend: 'Ext.data.Store',
  storeId: 'IndexTypes',

  requires: [
    'MainHub.model.libraries.IndexType'
  ],

  model: 'MainHub.model.libraries.IndexType',

  proxy: {
    type: 'ajax',
    url: 'api/index_types/',
    timeout: 1000000,
    pageParam: false,   // to remove param "page"
    startParam: false,  // to remove param "start"
    limitParam: false,  // to remove param "limit"
    noCache: false,     // to remove param "_dc",
    reader: {
      type: 'json',
      rootProperty: 'data',
      successProperty: 'success'
    }
  },

  autoLoad: true
});

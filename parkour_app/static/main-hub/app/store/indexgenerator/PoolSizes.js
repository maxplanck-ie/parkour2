Ext.define('MainHub.store.indexgenerator.PoolSizes', {
  extend: 'Ext.data.Store',
  storeId: 'PoolSizes',

  requires: [
    'MainHub.model.indexgenerator.PoolSize'
  ],

  model: 'MainHub.model.indexgenerator.PoolSize',

  proxy: {
    type: 'ajax',
    url: 'api/pool_sizes/',
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

  autoLoad: true,

  getId: function () {
    return 'PoolSizes';
  }
});

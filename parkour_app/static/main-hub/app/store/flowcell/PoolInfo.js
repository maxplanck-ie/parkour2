Ext.define('MainHub.store.flowcell.PoolInfo', {
  extend: 'Ext.data.Store',
  storeId: 'PoolInfo',

  requires: [
    'MainHub.model.flowcell.PoolInfo'
  ],

  model: 'MainHub.model.flowcell.PoolInfo',

  groupField: 'request_name',

  proxy: {
    type: 'ajax',
    pageParam: false,   // to remove param "page"
    startParam: false,  // to remove param "start"
    limitParam: false,  // to remove param "limit"
    noCache: false     // to remove param "_dc"
  }
});

Ext.define('MainHub.store.statistics.RunStatistics', {
  extend: 'Ext.data.Store',
  storeId: 'RunStatistics',

  requires: [
    'MainHub.model.statistics.RunStatistics'
  ],

  model: 'MainHub.model.statistics.RunStatistics',

  groupField: 'pk',
  groupDir: 'DESC',

  proxy: {
    type: 'ajax',
    url: 'api/run_statistics/',
    pageParam: false,   // to remove param "page"
    startParam: false,  // to remove param "start"
    limitParam: false,  // to remove param "limit"
    noCache: false     // to remove param "_dc",
  },

  getId: function () {
    return 'RunStatistics';
  }
});

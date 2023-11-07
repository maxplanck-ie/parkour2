Ext.define('MainHub.store.statistics.Sequences', {
  extend: 'Ext.data.Store',
  storeId: 'SequencesStatistics',

  requires: [
    'MainHub.model.statistics.Sequences'
  ],

  model: 'MainHub.model.statistics.Sequences',

  groupField: 'pk',
  groupDir: 'DESC',

  proxy: {
    type: 'ajax',
    url: 'api/sequences_statistics/',
    pageParam: false,   // to remove param "page"
    startParam: false,  // to remove param "start"
    limitParam: false,  // to remove param "limit"
    noCache: false      // to remove param "_dc",
  },

  getId: function () {
    return 'SequencesStatistics';
  }
});

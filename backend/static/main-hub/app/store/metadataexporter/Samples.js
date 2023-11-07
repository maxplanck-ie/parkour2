Ext.define('MainHub.store.metadataexporter.Samples', {
  extend: 'Ext.data.Store',
  storeId: 'ENASamples',

  requires: [
    'MainHub.model.metadataexporter.Sample'
  ],

  model: 'MainHub.model.metadataexporter.Sample',

  proxy: {
    type: 'ajax',
    pageParam: false, // to remove param "page"
    startParam: false, // to remove param "start"
    limitParam: false, // to remove param "limit"
    noCache: false // to remove param "_dc"
  },

  getId: function () {
    return 'ENASamples';
  }
});

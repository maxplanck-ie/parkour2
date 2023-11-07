Ext.define('MainHub.store.indexgenerator.IndexGenerator', {
  extend: 'Ext.data.Store',
  storeId: 'IndexGenerator',

  requires: [
    'MainHub.model.indexgenerator.Record'
  ],

  model: 'MainHub.model.indexgenerator.Record',

  groupField: 'request',
  groupDir: 'DESC',

  proxy: {
    type: 'ajax',
    timeout: 1000000,
    pageParam: false,   // to remove param "page"
    startParam: false,  // to remove param "start"
    limitParam: false,  // to remove param "limit"
    noCache: false,     // to remove param "_dc",
    api: {
      read: 'api/index_generator/',
      update: 'api/index_generator/edit/'
    },
    reader: {
      type: 'json',
      rootProperty: 'data',
      successProperty: 'success',
      messageProperty: 'error'
    },
    writer: {
      type: 'json',
      rootProperty: 'data',
      transform: {
        fn: function (data, request) {
          if (!(data instanceof Array)) {
            data = [data];
          }

          var store = Ext.getStore('IndexGenerator');
          var newData = _.map(data, function (item) {
            var record = store.findRecord('id', item.id, 0, false, true, true);
            if (record) {
              return Ext.Object.merge({
                pk: record.get('pk'),
                record_type: record.get('record_type')
              }, record.getChanges());
            }
          });
          return newData;
        },
        scope: this
      }
    }
  },

  getId: function () {
    return 'IndexGenerator';
  }
});

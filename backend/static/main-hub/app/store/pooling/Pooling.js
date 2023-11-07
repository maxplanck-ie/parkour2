Ext.define('MainHub.store.pooling.Pooling', {
  extend: 'Ext.data.Store',
  storeId: 'Pooling',

  requires: [
    'MainHub.model.pooling.Pooling'
  ],

  model: 'MainHub.model.pooling.Pooling',

  groupField: 'pool',
  groupDir: 'DESC',

  proxy: {
    type: 'ajax',
      // timeout: 1000000,
    pageParam: false,   // to remove param "page"
    startParam: false,  // to remove param "start"
    limitParam: false,  // to remove param "limit"
    noCache: false,     // to remove param "_dc",
    api: {
      read: 'api/pooling/',
      update: 'api/pooling/edit/'
    },
    reader: {
      type: 'json',
      rootProperty: 'data',
      successProperty: 'success',
      messageProperty: 'message'
    },
    writer: {
      type: 'json',
      rootProperty: 'data',
      transform: {
        fn: function (data, request) {
          if (!(data instanceof Array)) {
            data = [data];
          }

          var store = Ext.getStore('Pooling');
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

  listeners: {
    load: function (store, records, success, operation) {
      if (success) {
        // Remove 'Click to collapse' tooltip
        $('.x-grid-group-title').attr('data-qtip', '');
      }
    }
  },

  getId: function () {
    return 'Pooling';
  }
});

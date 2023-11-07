Ext.define('MainHub.store.flowcell.Flowcells', {
  extend: 'Ext.data.Store',
  storeId: 'Flowcells',

  requires: [
    'MainHub.model.flowcell.Flowcell'
  ],

  model: 'MainHub.model.flowcell.Flowcell',

  groupField: 'flowcell',
  groupDir: 'DESC',

  proxy: {
    type: 'ajax',
    timeout: 100000,
    pageParam: false,   // to remove param "page"
    startParam: false,  // to remove param "start"
    limitParam: false,  // to remove param "limit"
    noCache: false,     // to remove param "_dc",
    api: {
      read: 'api/flowcells/',
      update: 'api/flowcells/edit/'
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

          var store = Ext.getStore('Flowcells');
          var newData = _.map(data, function (item) {
            var record = store.findRecord('id', item.id, 0, false, true, true);
            if (record) {
              return Ext.Object.merge({
                pk: record.get('pk')
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
    return 'Flowcells';
  }
});

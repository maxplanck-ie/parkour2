Ext.define('MainHub.store.librarypreparation.LibraryPreparation', {
  extend: 'Ext.data.Store',
  storeId: 'LibraryPreparation',

  requires: [
    'MainHub.model.librarypreparation.LibraryPreparation'
  ],

  model: 'MainHub.model.librarypreparation.LibraryPreparation',

  groupField: 'library_protocol',
  groupDir: 'DESC',

  proxy: {
    type: 'ajax',
    timeout: 1000000,
    pageParam: false,   // to remove param "page"
    startParam: false,  // to remove param "start"
    limitParam: false,  // to remove param "limit"
    noCache: false,     // to remove param "_dc",
    api: {
      read: 'api/library_preparation/',
      update: 'api/library_preparation/edit/'
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

          var store = Ext.getStore('LibraryPreparation');
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
    return 'LibraryPreparation';
  }
});

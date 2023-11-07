Ext.define('MainHub.model.indexgenerator.Record', {
  extend: 'MainHub.model.Base',

  fields: [
    {
      name: 'pk',
      type: 'int'
    },
    {
      name: 'name',
      type: 'string'
    },
    {
      name: 'barcode',
      type: 'string'
    },
    {
      name: 'record_type',
      type: 'string'
    },
    {
      name: 'request',
      type: 'int'
    },
    {
      name: 'request_name',
      type: 'string'
    },
    {
      name: 'sequencing_depth',
      type: 'float'
    },
    {
      name: 'library_protocol_name',
      type: 'string'
    },
    {
      name: 'index_i7',
      type: 'string'
    },
    {
      name: 'index_i5',
      type: 'string'
    },
    {
      name: 'index_i7_id',
      type: 'string'
    },
    {
      name: 'index_i5_id',
      type: 'string'
    },
    {
      name: 'index_type',
      type: 'int'
    },
    {
      name: 'read_length',
      type: 'int'
    }
  ]
});

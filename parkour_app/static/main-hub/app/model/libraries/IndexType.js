Ext.define('MainHub.model.libraries.IndexType', {
  extend: 'MainHub.model.Base',

  fields: [
    {
      name: 'id',
      type: 'int'
    },
    {
      name: 'name',
      type: 'string'
    },
    {
      name: 'index_reads',
      type: 'int'
    },
    {
      name: 'is_dual',
      type: 'bool'
    },
    {
      name: 'index_length',
      type: 'int'
    },
    {
      name: 'format',
      type: 'string'
    },
    {
      name: 'obsolete',
      type: 'int'
    }
  ]
});

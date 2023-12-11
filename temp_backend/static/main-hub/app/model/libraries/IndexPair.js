Ext.define('MainHub.model.libraries.IndexPair', {
  extend: 'MainHub.model.Base',

  fields: [
    {
      name: 'index_type',
      type: 'int'
    },
    {
      name: 'index_1_id',
      type: 'int'
    },
    {
      name: 'index_2_id',
      type: 'int'
    },
    {
      name: 'char_coord',
      type: 'string'
    },
    {
      name: 'num_coord',
      type: 'int'
    },
    {
      name: 'archived',
      type: 'bool'
    }
  ]
});

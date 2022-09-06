Ext.define('MainHub.model.flowcell.PoolInfo', {
  extend: 'MainHub.model.Record',

  fields: [
    {
      name: 'protocol_name',
      type: 'string'
    },
    {
      name: 'request_name',
      type: 'string'
    }
  ]
});

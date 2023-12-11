Ext.define('MainHub.model.usage.ChartPolar', {
  extend: 'MainHub.model.Base',

  fields: [
    {
      name: 'name',
      type: 'string'
    },
    {
      name: 'data',
      type: 'int'
    },
    {
      name: 'libraries',
      type: 'int'
    },
    {
      name: 'samples',
      type: 'int'
    }
  ]
});

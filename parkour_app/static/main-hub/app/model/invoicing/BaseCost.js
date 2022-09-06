Ext.define('MainHub.model.invoicing.BaseCost', {
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
      name: 'price',
      type: 'float'
    }
  ]
});

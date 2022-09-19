Ext.define('MainHub.model.invoicing.BillingPeriod', {
  extend: 'MainHub.model.Base',

  fields: [
    {
      name: 'name',
      type: 'string'
    },
    {
      name: 'value',
      type: 'auto'
    },
    {
      name: 'report_url',
      type: 'string'
    }
  ]
});

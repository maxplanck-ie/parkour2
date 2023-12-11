Ext.define('MainHub.store.invoicing.BillingPeriods', {
  extend: 'Ext.data.Store',
  storeId: 'BillingPeriods',

  requires: [
    'MainHub.model.invoicing.BillingPeriod'
  ],

  model: 'MainHub.model.invoicing.BillingPeriod',

  proxy: {
    type: 'ajax',
    url: 'api/invoicing/billing_periods/',
    pageParam: false,   // to remove param "page"
    startParam: false,  // to remove param "start"
    limitParam: false,  // to remove param "limit"
    noCache: false      // to remove param "_dc",
  }
});

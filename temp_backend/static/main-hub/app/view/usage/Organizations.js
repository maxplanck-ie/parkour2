Ext.define('MainHub.view.usage.Organizations', {
  extend: 'MainHub.view.usage.ChartBase',
  xtype: 'usageorganizations',

  requires: [
    'MainHub.view.usage.ChartPolarBase'
  ],

  title: 'Organizations',

  items: [
    {
      itemId: 'empty-text',
      html: '<h2 style="color:#999;text-align:center;margin-top:150px">No Data</h2>',
      border: 0,
      hidden: true
    },
    {
      xtype: 'parkourpolar',
      store: 'UsageOrganizations',
      hidden: false
    }
  ]
});

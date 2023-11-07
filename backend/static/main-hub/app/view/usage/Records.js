Ext.define('MainHub.view.usage.Records', {
  extend: 'MainHub.view.usage.ChartBase',
  xtype: 'usagerecords',

  requires: [
    'MainHub.view.usage.ChartPolarBase'
  ],

  title: 'Libraries & Samples',
  // iconCls: 'x-fa fa-pie-chart',

  items: [
    {
      itemId: 'empty-text',
      html: '<h2 style="color:#999;text-align:center;margin-top:150px">No Data</h2>',
      border: 0,
      hidden: true
    },
    {
      xtype: 'parkourpolar',
      store: 'UsageRecords',
      hidden: false
    }
  ]
});

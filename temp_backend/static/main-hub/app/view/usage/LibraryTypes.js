Ext.define('MainHub.view.usage.LibraryTypes', {
  extend: 'MainHub.view.usage.ChartBase',
  xtype: 'usagelibrarytypes',

  requires: [
    'MainHub.view.usage.ChartPolarBase',
    'MainHub.view.usage.ChartCartesianBase'
  ],

  title: 'Library Types',

  layout: {
    type: 'vbox',
    align: 'center'
  },

  height: 800,

  items: [
    {
      itemId: 'empty-text',
      html: '<h2 style="color:#999;text-align:center;margin-top:150px">No Data</h2>',
      border: 0,
      hidden: true
    },
    {
      xtype: 'parkourpolar',
      store: 'UsageLibraryTypes',
      height: 365,
      hidden: false
    },
    {
      xtype: 'parkourcartesian',
      store: 'UsageLibraryTypes',
      height: 400,
      hidden: false
    }
  ]
});

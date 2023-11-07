Ext.define('MainHub.view.usage.PrincipalInvestigators', {
  extend: 'MainHub.view.usage.ChartBase',
  xtype: 'usageprincipalinvestigators',

  requires: [
    'MainHub.view.usage.ChartPolarBase',
    'MainHub.view.usage.ChartCartesianBase'
  ],

  title: 'Principal Investigators',

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
      store: 'UsagePrincipalInvestigators',
      height: 365,
      hidden: false
    },
    {
      xtype: 'parkourcartesian',
      store: 'UsagePrincipalInvestigators',
      height: 400,
      hidden: false
    }
  ]
});

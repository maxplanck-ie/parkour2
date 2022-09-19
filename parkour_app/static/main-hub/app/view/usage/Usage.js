Ext.define('MainHub.view.usage.Usage', {
  extend: 'Ext.container.Container',
  xtype: 'usage',

  requires: [
    'MainHub.view.usage.UsageController',
    'MainHub.view.usage.Records',
    'MainHub.view.usage.Organizations',
    'MainHub.view.usage.PrincipalInvestigators',
    'MainHub.view.usage.LibraryTypes',
    'Ext.ux.layout.ResponsiveColumn',
    'Ext.ux.DateRangePicker'
  ],

  controller: 'usage',

  layout: 'responsivecolumn',

  items: [
    {
      xtype: 'container',
      userCls: 'big-100',
      style: { textAlign: 'center' },
      items: [{
        xtype: 'daterangepicker',
        ui: 'header',
        cls: 'daterangepicker',
        padding: 0,
        drpDefaults: {
          showButtonTip: false,
          dateFormat: 'd.m.Y',
          mainBtnTextColor: '#999',
          mainBtnIconCls: 'x-fa fa-calendar',
          presetPeriodsBtnIconCls: 'x-fa fa-calendar-check-o',
          confirmBtnIconCls: 'x-fa fa-check'
        }
      }]
    },
    {
      xtype: 'usagerecords',
      userCls: 'big-50 small-100'
    },
    {
      xtype: 'usageorganizations',
      userCls: 'big-50 small-100'
    },
    {
      xtype: 'usageprincipalinvestigators',
      userCls: 'big-50 small-100'
    },
    {
      xtype: 'usagelibrarytypes',
      userCls: 'big-50 small-100'
    }
    // {
    //   xtype: 'container',
    //   userCls: 'big-100',
    //   html: '<hr style="border-top:1px solid #bdbdbd">',
    //   style: { background: 'transparent' },
    //   border: 0
    // }
  ]
});

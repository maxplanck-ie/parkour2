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
      items:[
      {
        xtype: 'button',
        id: 'download-report-button',
        itemId: 'download-report-button',
        cls: 'download-report-button',
        iconCls: 'fa fa-download fa-lg',
        text: 'Download Report'
      }]
    },
    {
      xtype: 'container',
      userCls: 'big-100',
      style: { textAlign: 'center' },
      layout: {
        type: "hbox",
        pack: "center",
        align: "center"
      },
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
      },
      {
        xtype: 'combobox',
        id: 'statusCb',
        itemId: 'statusCb',
        fieldLabel: 'Status',
        labelWidth: 45,
        width: 180,
        padding: "0 0 0 15px",
        store: Ext.create('Ext.data.Store', {
          fields: ['name', 'label'],
          data: [
            { status: 'submitted', label: 'Submitted' },
            { status: 'sequenced', label: 'Sequenced' }
          ],
          proxy: { type: 'memory' }
        }),
        queryMode: 'local',
        displayField: 'label',
        valueField: 'status',
        forceSelection: true,
        listeners: {
          afterrender: function () {
            // Set default value upon rendering
            this.setValue('submitted');
          }
        }
      }
      ]
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

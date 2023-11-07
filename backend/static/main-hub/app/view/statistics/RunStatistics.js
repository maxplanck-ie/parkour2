Ext.define('MainHub.view.statistics.RunStatistics', {
  extend: 'Ext.container.Container',
  xtype: 'run-statistics',

  requires: [
    'MainHub.components.BaseGrid',
    'MainHub.components.MonthPicker',
    'MainHub.components.SearchField',
    'MainHub.view.statistics.RunStatisticsController',
    'Ext.ux.DateRangePicker'
  ],

  controller: 'run-statistics',

  anchor: '100% -1',
  layout: 'fit',

  items: [{
    xtype: 'basegrid',
    id: 'run-statistics-grid',
    itemId: 'run-statistics-grid',
    store: 'RunStatistics',
    height: Ext.Element.getViewportHeight() - 64,

    header: {
      title: 'Run Statistics',
      items: [{
        xtype: 'parkoursearchfield',
        store: 'RunStatistics',
        emptyText: 'Search',
        paramName: 'pool',
        width: 200
      }]
    },

    columns: {
      defaults: {
        minWidth: 135,
        flex: 1
      },
      items: [
        {
          text: 'Lane',
          dataIndex: 'name'
        },
        {
          text: 'Pool',
          dataIndex: 'pool',
          filter: { type: 'string' }
        },
        {
          text: 'Request',
          dataIndex: 'request',
          filter: { type: 'string' }
        },
        {
          text: 'Prep. Method',
          dataIndex: 'library_preparation',
          tooltip: 'Preparation Method',
          filter: { type: 'list' }
        },
        {
          text: 'Library Type',
          dataIndex: 'library_type',
          filter: { type: 'list' }
        },
        {
          text: 'Loading Concentr.',
          dataIndex: 'loading_concentration',
          tooltip: 'Loading Concentration',
          filter: { type: 'number' }
        },
        {
          text: 'Cluster PF (%)',
          dataIndex: 'cluster_pf',
          filter: { type: 'number' }
        },
        {
          text: 'Reads PF (M)',
          dataIndex: 'reads_pf',
          filter: { type: 'number' },
          renderer: function (value) {
            if (value) {
              value = (value / 1000000).toFixed(1);
            }
            return value;
          }
        },
        {
          text: 'Undet. Indices (%)',
          dataIndex: 'undetermined_indices',
          tooltip: 'Undetermined Indices (%)',
          filter: { type: 'number' }
        },
        {
          text: '% Spike In',
          dataIndex: 'phix',
          filter: { type: 'number' }
        },
        {
          text: 'Read 1 % >=Q30',
          dataIndex: 'read_1',
          filter: { type: 'number' }
        },
        {
          text: 'Read 2 (I) % >=Q30',
          dataIndex: 'read_2',
          filter: { type: 'number' }
        }
      ]
    },

    plugins: [
      {
        ptype: 'bufferedrenderer',
        trailingBufferZone: 100,
        leadingBufferZone: 100
      },
      {
        ptype: 'gridfilters'
      }
    ],

    features: [{
      ftype: 'grouping',
      startCollapsed: true,
      enableGroupingMenu: false,
      groupHeaderTpl: [
        '<strong>{children:this.getFlowcellId} ' +
        '({children:this.getDate}, {children:this.getSequencer}, ' +
        '{children:this.getReadLength})</strong>',
        {
          getFlowcellId: function (children) {
            return children[0].get('flowcell_id');
          },
          getDate: function (children) {
            return Ext.util.Format.date(children[0].get('create_time'));
          },
          getSequencer: function (children) {
            return children[0].get('sequencer');
          },
          getReadLength: function (children) {
            return children[0].get('read_length');
          }
        }
      ]
    }],

    dockedItems: [{
      xtype: 'toolbar',
      dock: 'top',
      items: [{
        xtype: 'daterangepicker',
        ui: 'header',
        drpDefaults: {
          showButtonTip: false,
          dateFormat: 'd.m.Y',
          mainBtnTextColor: '#999',
          mainBtnIconCls: 'x-fa fa-calendar',
          presetPeriodsBtnIconCls: 'x-fa fa-calendar-check-o',
          confirmBtnIconCls: 'x-fa fa-check'
        }
      }]
    }]
  }]
});

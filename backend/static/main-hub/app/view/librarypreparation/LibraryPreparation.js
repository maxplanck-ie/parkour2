Ext.define('MainHub.view.librarypreparation.LibraryPreparation', {
  extend: 'Ext.container.Container',
  xtype: 'preparation',

  requires: [
    'MainHub.components.BaseGrid',
    'MainHub.view.librarypreparation.LibraryPreparationController'
  ],

  controller: 'library-preparation',

  anchor: '100% -1',
  layout: 'fit',

  items: [{
    xtype: 'basegrid',
    id: 'library-preparation-grid',
    itemId: 'library-preparation-grid',
    store: 'LibraryPreparation',

    header: {
      title: 'Preparation',
      items: [{
        xtype: 'textfield',
        itemId: 'search-field',
        emptyText: 'Search',
        width: 200
      }]
    },

    customConfig: {
      qualityCheckMenuOptions: ['passed', 'failed']
    },

    columns: {
      defaults: {
        width: 80
      },
      items: [
        {
          xtype: 'checkcolumn',
          itemId: 'check-column',
          dataIndex: 'selected',
          resizable: false,
          menuDisabled: true,
          hideable: false,
          // locked: true,
          tdCls: 'no-dirty',
          width: 35
        },
        {
          text: 'Request',
          tooltip: 'Request ID',
          dataIndex: 'request_name',
          // locked: true,
          width: 250
        },
        {
          text: 'Pool',
          tooltip: 'Pool ID',
          dataIndex: 'pool_name',
          width: 120
        },
        {
          text: 'Name',
          tooltip: 'Sample Name',
          dataIndex: 'name',
          minWidth: 200,
          flex: 1
        },
        {
          text: 'Barcode',
          dataIndex: 'barcode',
          resizable: false,
          renderer: 'barcodeRenderer',
          width: 95
        },
        {
          text: 'Date',
          dataIndex: 'create_time',
          renderer: Ext.util.Format.dateRenderer('d.m.Y'),
          width: 90
        },
        {
          text: 'Protocol',
          tooltip: 'Library Preparation Protocol',
          dataIndex: 'library_protocol_name',
          renderer: 'gridCellTooltipRenderer',
          minWidth: 150
        },
        {
          text: 'DF',
          tooltip: 'Dilution Factor',
          dataIndex: 'dilution_factor',
          width: 60
        },
        {
          text: 'ng/µl Sample',
          tooltip: 'Concentration Sample (ng/µl)',
          dataIndex: 'concentration_sample',
          width: 105,
          editor: {
            xtype: 'numberfield',
            decimalPrecision: 2,
            minValue: 0
          }
        },
        {
          text: 'ng Start',
          tooltip: 'Starting Amount (ng)',
          dataIndex: 'starting_amount',
          width: 100,
          editor: {
            xtype: 'numberfield',
            decimalPrecision: 1,
            minValue: 0
          }
        },
        {
          text: 'Spike-in',
          tooltip: 'Spike-in Description',
          dataIndex: 'spike_in_description',
          editor: { xtype: 'textfield' },
          width: 150
        },
        {
          text: 'µl Spike-in',
          tooltip: 'Spike-in Volume (µl)',
          dataIndex: 'spike_in_volume',
          width: 100,
          editor: {
            xtype: 'numberfield',
            decimalPrecision: 1,
            minValue: 0
          }
        },
        {
          text: 'Coord',
          dataIndex: 'coordinate',
          width: 65
        },
        {
          text: 'I7 ID',
          tooltip: 'Index I7 ID',
          dataIndex: 'index_i7_id',
          width: 90
        },
        {
          text: 'I5 ID',
          tooltip: 'Index I5 ID',
          dataIndex: 'index_i5_id',
          width: 90
        },
        {
          text: 'Cycles',
          tooltip: 'PCR Cycles',
          dataIndex: 'pcr_cycles',
          editor: {
            xtype: 'numberfield',
            allowDecimals: false,
            minValue: 0
          }
        },
        {
          text: 'ng/µl Library',
          tooltip: 'Concentration Library (ng/µl)',
          dataIndex: 'concentration_library',
          width: 100,
          editor: {
            xtype: 'numberfield',
            minValue: 0
          }
        },
        {
          text: 'qPCR (nM)',
          tooltip: 'qPCR Result (nM)',
          dataIndex: 'qpcr_result',
          width: 100,
          editor: {
            xtype: 'numberfield',
            minValue: 0
          }
        },
        {
          text: 'bp',
          tooltip: 'Mean Fragment Size (bp)',
          dataIndex: 'mean_fragment_size',
          editor: {
            xtype: 'numberfield',
            allowDecimals: false,
            minValue: 0
          }
        },
        {
          text: 'nM',
          tooltip: '(Concentration Library (ng/µl) / (650 * Size (bp))) * 10^6',
          dataIndex: 'nM',
          editor: {
            xtype: 'numberfield',
            minValue: 0
          }
        },
        {
          text: 'QC Comments',
          tooltip: 'Incoming Libraries/Samples QC Comments',
          dataIndex: 'comments_facility',
          renderer: 'gridCellTooltipRenderer',
          editor: { xtype: 'textfield' },
          width: 150
        },
        {
          text: 'Comments',
          dataIndex: 'comments',
          renderer: 'gridCellTooltipRenderer',
          editor: { xtype: 'textfield' },
          width: 150
        }
      ]
    },

    features: [{
      ftype: 'grouping',
      startCollapsed: true,
      enableGroupingMenu: false,
      groupHeaderTpl: [
        '<strong>Protocol: {children:this.getName} (# of libraries: {children.length})</strong>',
        {
          getName: function (children) {
            return children[0].get('library_protocol_name');
          }
        }
      ]
    }]
  }]
});

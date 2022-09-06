Ext.define('MainHub.view.indexgenerator.IndexGenerator', {
  extend: 'Ext.container.Container',
  xtype: 'index-generator',
  id: 'poolingContainer',

  requires: [
    'MainHub.components.BaseGrid',
    'MainHub.view.indexgenerator.IndexGeneratorController'
  ],

  controller: 'index-generator',

  layout: {
    type: 'hbox',
    align: 'stretch'
  },
  padding: 15,

  initComponent: function () {
    var me = this;
    me.items = [
      {
        xtype: 'basegrid',
        id: 'index-generator-grid',
        itemId: 'index-generator-grid',
        height: Ext.Element.getViewportHeight() - 94,
        padding: 0,
        margin: '0 15px 0 0',
        flex: 1,
        header: {
          title: 'Libraries and Samples for Pooling',
          items: [{
            xtype: 'combobox',
            id: 'poolSizeCb',
            itemId: 'poolSizeCb',
            store: 'PoolSizes',
            queryMode: 'local',
            displayField: 'name',
            valueField: 'id',
            forceSelection: true,
            cls: 'panel-header-combobox',
            fieldLabel: 'Pool Size',
            labelWidth: 65,
            width: 170
          }]
        },
        store: 'IndexGenerator',
        enableColumnHide: false,

        columns: [
          {
            xtype: 'checkcolumn',
            itemId: 'check-column',
            dataIndex: 'selected',
            resizable: false,
            tdCls: 'no-dirty',
            width: 35
          },
          {
            text: 'Name',
            dataIndex: 'name',
            minWidth: 200,
            flex: 1
          },
          {
            text: 'Barcode',
            dataIndex: 'barcode',
            resizable: false,
            width: 90
          },
          {
            text: '',
            dataIndex: 'record_type',
            resizable: false,
            width: 30,
            renderer: function (value) {
              return value.charAt(0);
            }
          },
          {
            text: 'Depth (M)',
            tooltip: 'Sequencing Depth',
            dataIndex: 'sequencing_depth',
            width: 85
          },
          {
            text: 'Length',
            tooltip: 'Read Length',
            dataIndex: 'read_length',
            width: 70,
            editor: {
              xtype: 'combobox',
              queryMode: 'local',
              valueField: 'id',
              displayField: 'name',
              store: 'readLengthsStore',
              matchFieldWidth: false,
              forceSelection: true
            },

            //tpl: Ext.create('Ext.XTemplate',
             //                  '<tpl for=".">',
              //                     '  <tpl if="obsolete==2">',
               //                    '    <div class="x-boundlist-item x-item-disabled"><em>{name}</em></div>',
                //                   '  <tpl else>',
                 //                  '    <div class="x-boundlist-item x-item-disabled"><em>{name}</em></div>',
                  //                 '  </tpl>',
                   //            '</tpl>'),
            renderer: function (value) {
             var store = Ext.getStore('readLengthsStore');
              var record = store.findRecord(
                    'id', value, 0, false, true, true
                );

              return (record) ? record.get('name') : '';
            },
            //listeners:{
              //beforeselect: function(combo, record, index) {
                  //if(record.get('obsolete') == 2 ){
                  //   return false;
                //  }
              //  }
            //}

          },

          {
            text: 'Protocol',
            tooltip: 'Library Preparation Protocol',
            dataIndex: 'library_protocol_name',
            renderer: 'gridCellTooltipRenderer',
            width: 150
          },
          {
            text: 'Index Type',
            dataIndex: 'index_type',
            width: 150,
            editor: {
              id: 'indexTypePoolingEditor',
              xtype: 'combobox',
              queryMode: 'local',
              displayField: 'name',
              valueField: 'id',
              //store: 'IndexTypes',
              store: 'GeneratorIndexTypes',
              matchFieldWidth: false,
              forceSelection: true
            },
            renderer: function (value, meta) {
              var record = Ext.getStore('GeneratorIndexTypes').findRecord(
                'id', value, 0, false, true, true
              );
              var val = '';

              if (record) {
                val = record.get('name');
                meta.tdAttr = Ext.String.format('data-qtip="{0}"', val);
              }

              return val;
            }
          },
          {
            text: 'Index I7',
            dataIndex: 'index_i7',
            width: 100
          },
          {
            text: 'Index I5',
            dataIndex: 'index_i5',
            width: 100
          }
        ],

        plugins: [
          {
            ptype: 'bufferedrenderer',
            trailingBufferZone: 100,
            leadingBufferZone: 100
          },
          {
            ptype: 'rowediting',
            clicksToEdit: 1
          }
        ],

        dockedItems: [],

        features: [{
          ftype: 'grouping',
          startCollapsed: true,
          groupHeaderTpl: [
            '<strong>Request: {children:this.getName}</strong> (Total Sequencing Depth: {children:this.getTotalDepth} M, No. Samples/Libraries: {children:this.getCount})',
            {
              getName: function (children) {
                return children[0].get('request_name');
              },
              getTotalDepth: function (children) {
                return Ext.sum(Ext.pluck(Ext.pluck(children, 'data'), 'sequencing_depth'));
              },
              getCount: function(children){
                return children.length
              }
            }
          ]
        }]
      },
      {
        xtype: 'grid',
        id: 'pool-grid',
        itemId: 'pool-grid',
        cls: 'pooling-grid',
        header: {
          title: 'Pool',
          height: 56,
          items: [
            {
              xtype: 'combobox',
              itemId: 'start-coordinate',
              store: 'StartCoordinates',
              queryMode: 'local',
              displayField: 'coordinate',
              valueField: 'coordinate',
              forceSelection: true,
              cls: 'panel-header-combobox',
              fieldLabel: 'Start Coordinate',
              labelWidth: 110,
              width: 550,
              margin: '0 15px 0 0',
              hidden: true
            },
            {
              xtype: 'combobox',
              itemId: 'direction',
              store: Ext.data.Store({
                data: [
                  { id: 1, value: 'right' },
                  { id: 2, value: 'down' },
                  { id: 3, value: 'diagonal' }
                ]
              }),
              queryMode: 'local',
              displayField: 'value',
              valueField: 'value',
              forceSelection: true,
              cls: 'panel-header-combobox',
              fieldLabel: 'Direction',
              labelWidth: 65,
              width: 160,
              hidden: true
            }
          ]
        },
        height: Ext.Element.getViewportHeight() - 94,
        flex: 1,
        features: [{ ftype: 'summary' }],
        viewConfig: {
          markDirty: false,
          stripeRows: false
        },
        multiSelect: true,
        sortableColumns: false,
        enableColumnMove: false,
        enableColumnResize: false,
        enableColumnHide: false,

        columns: [
          {
            text: 'Name',
            dataIndex: 'name',
            width: 200
          },
          {
            text: '',
            dataIndex: 'record_type',
            width: 30,
            renderer: function (value) {
              return value.charAt(0);
            }
          },
          {
            text: 'Depth (M)',
            dataIndex: 'sequencing_depth',
            width: 85,
            summaryType: 'sum',
            summaryRenderer: function (value) {
              return value > 0 ? value : '';
            }
          },
          {
            text: 'Coord',
            dataIndex: 'coordinate',
            width: 65
          },
          {
            text: 'Index I7 ID',
            dataIndex: 'index_i7_id',
            width: 90,
            summaryRenderer: function () {
              var totalSequencingDepth = Ext.getCmp('pool-grid').getStore().sum('sequencing_depth');
              return totalSequencingDepth > 0
                ? '<span class="summary-green">green:</span><br><span class="summary-red">red:</span>'
                : '';
            }
          },
          {
            text: '1',
            dataIndex: 'index_i7_1',
            cls: 'nucleotide-header',
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 55
          },
          {
            text: '2',
            dataIndex: 'index_i7_2',
            cls: 'nucleotide-header',
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 55
          },
          {
            text: '3',
            dataIndex: 'index_i7_3',
            cls: 'nucleotide-header',
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 55
          },
          {
            text: '4',
            dataIndex: 'index_i7_4',
            cls: 'nucleotide-header',
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 55
          },
          {
            text: '5',
            dataIndex: 'index_i7_5',
            cls: 'nucleotide-header',
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 55
          },
          {
            text: '6',
            dataIndex: 'index_i7_6',
            cls: 'nucleotide-header',
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 55
          },
          {
            text: '7',
            dataIndex: 'index_i7_7',
            cls: 'nucleotide-header',
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 55
          },
          {
            text: '8',
            dataIndex: 'index_i7_8',
            cls: 'nucleotide-header',
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 55
          },
          {
            text: '9',
            dataIndex: 'index_i7_9',
            cls: 'nucleotide-header',
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 55
          },
          {
            text: '10',
            dataIndex: 'index_i7_10',
            cls: 'nucleotide-header',
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 55
          },
          {
            text: '11',
            dataIndex: 'index_i7_11',
            cls: 'nucleotide-header',
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 55
          },
          {
            text: '12',
            dataIndex: 'index_i7_12',
            cls: 'nucleotide-header',
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 55
          },
          {
            text: 'Index I5 ID',
            dataIndex: 'index_i5_id',
            summaryRenderer: function () {
              var totalSequencingDepth = Ext.getCmp('pool-grid').getStore().sum('sequencingDepth');
              return totalSequencingDepth > 0
                ? '<span class="summary-green">green:</span><br><span class="summary-red">red:</span>'
                : '';
            },
            width: 90
          },
          {
            text: '1',
            dataIndex: 'index_i5_1',
            cls: 'nucleotide-header',
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 55
          },
          {
            text: '2',
            dataIndex: 'index_i5_2',
            cls: 'nucleotide-header',
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 55
          },
          {
            text: '3',
            dataIndex: 'index_i5_3',
            cls: 'nucleotide-header',
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 55
          },
          {
            text: '4',
            dataIndex: 'index_i5_4',
            cls: 'nucleotide-header',
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 55
          },
          {
            text: '5',
            dataIndex: 'index_i5_5',
            cls: 'nucleotide-header',
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 55
          },
          {
            text: '6',
            dataIndex: 'index_i5_6',
            cls: 'nucleotide-header',
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 55
          },
          {
            text: '7',
            dataIndex: 'index_i5_7',
            cls: 'nucleotide-header',
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 55
          },
          {
            text: '8',
            dataIndex: 'index_i5_8',
            cls: 'nucleotide-header',
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 55
          },
          {
            text: '9',
            dataIndex: 'index_i5_9',
            cls: 'nucleotide-header',
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 55
          },
          {
            text: '10',
            dataIndex: 'index_i5_10',
            cls: 'nucleotide-header',
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 55
          },
          {
            text: '11',
            dataIndex: 'index_i5_11',
            cls: 'nucleotide-header',
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 55
          },
          {
            text: '12',
            dataIndex: 'index_i5_12',
            cls: 'nucleotide-header',
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 55
          }
        ],
        store: [],
        bbar: [
          {
            xtype: 'button',
            id: 'generate-indices-button',
            itemId: 'generate-indices-button',
            iconCls: 'fa fa-cogs fa-lg',
            text: 'Generate Indices',
            disabled: true
          },
          /* for future:
          {
            xtype: 'button',
            itemId: 'download-index-list-button',
            text: 'Download Index List (csv)',
            iconCls: 'fa fa-file-excel-o fa-lg'
          },
          */
          '->',
          {
            xtype: 'button',
            id: 'save-pool-button',
            itemId: 'save-pool-button',
            iconCls: 'fa fa-floppy-o fa-lg',
            text: 'Save Pool',
            disabled: true
          }
        ]
      }
    ];

    me.callParent(arguments);
  },

  renderNucleotide: function (val, meta) {
    if (val === 'G' || val === 'T') {
      meta.tdStyle = 'background-color:#dcedc8';
    } else if (val === 'A' || val === 'C') {
      meta.tdStyle = 'background-color:#ef9a9a';
    }
    meta.tdCls = 'nucleotide';
    return val;
  },

  calculateColorDiversity: function (records, values) {
    var diversity = { green: 0, red: 0 };

    for (var i = 0; i < values.length; i++) {
      var nuc = values[i];
      if (nuc && nuc !== ' ') {
        if (nuc === 'G' || nuc === 'T') {
          diversity.green += records[i].get('sequencing_depth');
        } else if (nuc === 'A' || nuc === 'C') {
          diversity.red += records[i].get('sequencing_depth');
        }
      }
    }

    return diversity;
  },

  renderSummary: function (value, summaryData, dataIndex, meta) {
    var grid = Ext.getCmp('pool-grid');
    var store = grid.getStore();
    var result = '';
    var totalSequencingDepth = 0;

    if (store.getCount() > 1 && (value.green > 0 || value.red > 0)) {
      if (dataIndex.split('_')[1] === 'i7') {
        // Consider only non empty Index I7 indices
        store.each(function (record) {
          if (record.get('index_i7') !== '') {
            totalSequencingDepth += record.get('sequencing_depth');
          }
        });
      } else {
        // Consider only non empty Index I5 indices
        store.each(function (record) {
          if (record.get('index_i5') !== '') {
            totalSequencingDepth += record.get('sequencing_depth');
          }
        });
      }

      var green = parseInt(((value.green / totalSequencingDepth) * 100).toFixed(0));
      var red = parseInt(((value.red / totalSequencingDepth) * 100).toFixed(0));

      result = Ext.String.format('{0}%<br/>{1}%', green, red);

      if ((green < 20 && red > 80) || (red < 20 && green > 80)) {
        meta.tdCls = 'problematic-cycle';
        result += '<br/>!';
      }
    }

    return result;
  }
});

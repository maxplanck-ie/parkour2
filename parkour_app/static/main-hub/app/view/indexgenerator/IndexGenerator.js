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
    
    // Keep a record of the index types loaded in the relevant stores to speed
    // up the process of checking these values
    me.loadedIndexTypeIds = [];
    me.viewRefreshCounter = 0;
    
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
          items: [
            {
              xtype: 'checkbox',
              boxLabel: '<span data-qtip="Check, to show only the requests for which you are responsible">As Handler</span>',
              itemId: 'as-handler-index-generator-checkbox',
              margin: '0 15 0 0',
              cls: 'grid-header-checkbox',
              checked: false,
              listeners: {
                change: function (cb, newValue, oldValue, eOpts) {
                  var grid = cb.up('#index-generator-grid');
                  var gridGrouping = grid.view.getFeature('index-generator-grid-grouping');
                  if (newValue) {
                    grid.store.getProxy().extraParams.asHandler = 'True';
                    grid.store.load({
                      callback: function (records, operation, success) {
                        if (success) {
                          gridGrouping.expandAll();
                        }
                      }
                    })
                  } else {
                    grid.store.getProxy().extraParams.asHandler = 'False';
                    grid.store.load({
                      callback: function (records, operation, success) {
                        if (success) {
                          gridGrouping.collapseAll();
                        }
                      }
                    })
                  }
                }
              }
            },
            {
              xtype: 'combobox',
              id: 'poolSizeCb',
            itemId: 'poolSizeCb',
            store: 'PoolSizes',
            queryMode: 'local',
            displayField: 'name',
            valueField: 'id',
            forceSelection: true,
            cls: 'panel-header-combobox',
            fieldLabel: '<span data-qtip="Sequencing kit">Seq. Kit</span>',
            labelWidth: 50,
            width: 285
          }]
        },
        store: 'IndexGenerator',
        enableColumnHide: false,

        listeners: {

          boxready: function () {

            // Check if indices have already been added to the index stores before and
            // if so add them to loadedIndexTypeIds
            [Ext.getStore('indexI7Store'), Ext.getStore('indexI5Store')].forEach(function (s) {
              var indexTypeIds = Array.from(new Set(Ext.pluck(Ext.pluck(s.getRange(), 'data'), 'index_type').filter(function (e) { return e })));
              indexTypeIds.forEach(function (e) {
                me.loadedIndexTypeIds.indexOf(e) === -1 && me.loadedIndexTypeIds.push(e);
              })
            })
          },

          rowdblclick: function (grid, record, element, rowIndex, e, eOpts) {

            // Enable/Disable index boxes based on whether index type is set

            var indexTypeId = record.get('index_type');
            var indexI7Editor = Ext.getCmp('indexI7EditorIndexGenerator');
            var indexI5Editor = Ext.getCmp('indexI5EditorIndexGenerator');

            // Only filter index store if Index Type is set for the record
            if (indexTypeId) {

              // Enable index editors
              indexI7Editor.enable();
              indexI5Editor.enable();

              // Filter index stores
              var indexI7Store = Ext.getStore('indexI7Store');
              var indexI5Store = Ext.getStore('indexI5Store');
              [indexI7Store, indexI5Store].forEach(function(s){
                s.clearFilter(true);
                s.filter('index_type', indexTypeId, true);
              })

            } else {

              // Disable index stores
              indexI7Editor.disable();
              indexI5Editor.disable();
            }
          },

          groupexpand: function (view, node, group, e, eOpts) {

            // When opening a group, load in the index stores those indices 
            // that are present in the group, if not already added
            var records = view.getStore().getGroups().items.filter(function(e){return e._groupKey == group})[0].getRange();
            var indexTypeIds = Array.from(new Set(Ext.pluck(Ext.pluck(records, 'data'), 'index_type').filter(function (e) { return e })));
            var missingIndexTypeIds = indexTypeIds.filter(function(e) { return !me.loadedIndexTypeIds.includes(e)});
            if (missingIndexTypeIds.length > 0) {
              me.loadedIndexTypeIds = me.loadedIndexTypeIds.concat(missingIndexTypeIds);
              me.addToIndexStore(Ext.getStore('indexI7Store'), missingIndexTypeIds, true, me);
              me.addToIndexStore(Ext.getStore('indexI5Store'), missingIndexTypeIds, true, me);
              me.addToIndexPairStore(missingIndexTypeIds);
            }
          }
        },

        columns: [
          {
            xtype: 'checkcolumn',
            itemId: 'check-column',
            dataIndex: 'selected',
            resizable: false,
            tdCls: 'no-dirty',
            width: 36
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
              forceSelection: true,
              listeners: {
                change: function (cb, newValue, oldValue, eOpts) {

                  Ext.getCmp('index-generator-grid').fireEvent('reset');

                  // Reset index editors
                  var indexI7Editor = Ext.getCmp('indexI7EditorIndexGenerator');
                  var indexI5Editor = Ext.getCmp('indexI5EditorIndexGenerator');
                  indexI7Editor.setValue(null);
                  indexI5Editor.setValue(null);

                  if (newValue) {

                    // Enable index editors
                    indexI7Editor.enable();
                    indexI5Editor.enable();

                    var indexI7Store = Ext.getStore('indexI7Store');
                    var indexI5Store = Ext.getStore('indexI5Store');

                    // Check if Index Type has not been retrieved before
                    // If not add new records to store
                    var indexGeneratorStore = Ext.getStore('IndexGenerator'); 
                    var indexTypeIds = Array.from(new Set(Ext.pluck(Ext.pluck(indexGeneratorStore.getRange(), 'data'), 'index_type').filter(function (e) { return e })));
                    if (newValue && indexTypeIds.indexOf(newValue) === -1) {
                      me.addToIndexStore(indexI7Store, [newValue], false, me);
                      me.addToIndexStore(indexI5Store, [newValue], false, me);
                      me.addToIndexPairStore([newValue]);
                    }

                    // Filter index stores
                    [indexI7Store, indexI5Store].forEach(function (s) {
                      s.clearFilter(true);
                      s.filter('index_type', newValue, true);
                    })
                  } else {
                    // Disable index editors
                    indexI7Editor.disable();
                    indexI5Editor.disable();
                  }
                }
              }
            },
            renderer: function (value, meta) {
              var record = meta.column.getEditor().getStore().findRecord(
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
            width: 100,
            editor: {
              xtype: 'combobox',
              id: 'indexI7EditorIndexGenerator',
              itemId: 'indexI7EditorIndexGenerator',
              queryMode: 'local',
              displayField: 'name',
              displayTpl: Ext.create('Ext.XTemplate',
                '<tpl for=".">',
                '{index}',
                '</tpl>'
              ),
              valueField: 'index',
              store: 'indexI7Store',
              regex: new RegExp('^(?=(?:.{6}|.{8}|.{10}|.{12}|.{24})$)[ATCG]+$'),
              regexText: 'Only A, T, C and G (uppercase) are allowed. Index length must be 6, 8, 10, 12 or 24.',
              matchFieldWidth: false,
              listeners: {
                change: function (cb, newValue, oldValue, eOpts) {

                  if (newValue) {
                    // Get the index record
                    var indexTypeId = Ext.getCmp('indexTypePoolingEditor').getValue();
                    var store = cb.store;
                    store.clearFilter(true);
                    store.filter('index_type', indexTypeId, true);
                    var record = store.findRecord('index', newValue);

                    // If a record is found, try to get the corresponding
                    // i5 index and if present, set it in the i5 index cell
                    if (record) {
                      var indexPair = Ext.getStore('IndexPairs').findRecord('index1_id', record.id);
                      if (indexPair) {
                        var i5IndexStore = Ext.getStore('indexI5Store');
                        i5IndexStore.clearFilter(true);
                        var i5_index = i5IndexStore.findRecord('id', indexPair.get('index2_id'));
                        if (i5_index) {
                          Ext.getCmp('indexI5EditorIndexGenerator').setValue(i5_index.get('index'));
                        }
                      }
                    }
                  }
                },
              }
            },
            renderer: function (value, meta, record) {
              if (value) {
                var store = meta.column.getEditor().getStore();
                store.clearFilter(true);
                store.filter('index_type', record.get('index_type'), true);
                var index = store.findRecord('index', value, 0, false, true, true);
                if (index) {
                  value = index.get('name');
                }
              }
              return value;
            }
          },
          {
            text: 'Index I5',
            dataIndex: 'index_i5',
            width: 100,
            editor: {
              xtype: 'combobox',
              id: 'indexI5EditorIndexGenerator',
              itemId: 'indexI5EditorIndexGenerator',
              queryMode: 'local',
              displayField: 'name',
              displayTpl: Ext.create('Ext.XTemplate',
                '<tpl for=".">',
                '{index}',
                '</tpl>'
              ),
              valueField: 'index',
              store: 'indexI5Store',
              regex: new RegExp('^(?=(?:.{6}|.{8}|.{10}|.{12}|.{24})$)[ATCG]+$'),
              regexText: 'Only A, T, C and G (uppercase) are allowed. Index length must be 6, 8, 10, 12 or 24.',
              matchFieldWidth: false,
              listeners: {
                change: function (cb, newValue, oldValue, eOpts) {

                  if (newValue) {
                    // Get the index record
                    var indexTypeId = Ext.getCmp('indexTypePoolingEditor').getValue();
                    var store = cb.store;
                    store.clearFilter(true);
                    store.filter('index_type', indexTypeId, true);
                    var record = store.findRecord('index', newValue);

                    // If a record is found, try to get the corresponding
                    // i7 index and if present, set it in the i7 index cell
                    if (record) {
                      var indexPair = Ext.getStore('IndexPairs').findRecord('index2_id', record.id);
                      if (indexPair) {
                        var i7IndexStore = Ext.getStore('indexI7Store');
                        i7IndexStore.clearFilter(true);
                        var i7_index = i7IndexStore.findRecord('id', indexPair.get('index1_id'));
                        if (i7_index) {
                          Ext.getCmp('indexI7EditorIndexGenerator').setValue(i7_index.get('index'));
                        }
                      }
                    }
                  }
                },
              }
            },
            renderer: function (value, meta, record) {
              if (value) {
                var store = meta.column.getEditor().getStore();
                store.clearFilter(true);
                store.filter('index_type', record.get('index_type'), true);
                var index = store.findRecord('index', value, 0, false, true, true);
                if (index) {
                  value = index.get('name');
                }
              }
              return value;
            }
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
            clicksToEdit: 2
          }
        ],

        dockedItems: [],

        features: [{
          ftype: 'grouping',
          id: 'index-generator-grid-grouping',
          startCollapsed: true,
          groupHeaderTpl: [
            '<strong>Request: {children:this.getName}</strong> (#: {children:this.getCount}, {children:this.isPooled}Total Depth: {children:this.getTotalDepth} M, Seq. Kit: {children:this.getPoolSize})',
            {
              getName: function (children) {
                return children[0].get('request_name');
              },
              isPooled: function (children) {
                return children[0].get('pooled_libraries') ? 'Pool, ' : '';
              },
              getTotalDepth: function (children) {
                return Ext.sum(Ext.pluck(Ext.pluck(children, 'data'), 'sequencing_depth'));
              },
              getCount: function(children){
                return children.length
              },
              getPoolSize: function(children){
                return children[0].get('pool_size_user_name');
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
        baseColours: {
            sequencerChemistry: 0,
            green: [],
            red: [],
            black: []
          },
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
              width: 200,
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
              var grid = Ext.getCmp('pool-grid');
              var sequencerChemistry = grid.baseColours.sequencerChemistry;
              var labels = '';

              if (sequencerChemistry === 2) {
                labels = '<span class="summary-green">% green:</span><br><span class="summary-red">% red:</span><br><span class="summary-black">% black:</span>'
              } else if (sequencerChemistry === 4) {
                labels = '<span class="summary-green">% green:</span><br><span class="summary-red">% red:</span>'
              }
              var totalSequencingDepth = grid.getStore().sum('sequencing_depth');
              return totalSequencingDepth > 0
                ? labels
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
            width: 36
          },
          {
            text: '2',
            dataIndex: 'index_i7_2',
            cls: 'nucleotide-header',
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 36
          },
          {
            text: '3',
            dataIndex: 'index_i7_3',
            cls: 'nucleotide-header',
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 36
          },
          {
            text: '4',
            dataIndex: 'index_i7_4',
            cls: 'nucleotide-header',
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 36
          },
          {
            text: '5',
            dataIndex: 'index_i7_5',
            cls: 'nucleotide-header',
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 36
          },
          {
            text: '6',
            dataIndex: 'index_i7_6',
            cls: 'nucleotide-header',
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 36
          },
          {
            text: '7',
            dataIndex: 'index_i7_7',
            cls: 'nucleotide-header',
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 36
          },
          {
            text: '8',
            dataIndex: 'index_i7_8',
            cls: 'nucleotide-header',
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 36
          },
          {
            text: '9',
            dataIndex: 'index_i7_9',
            cls: 'nucleotide-header',
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 36
          },
          {
            text: '10',
            dataIndex: 'index_i7_10',
            cls: 'nucleotide-header',
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 36
          },
          {
            text: '11',
            dataIndex: 'index_i7_11',
            cls: 'nucleotide-header',
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 36
          },
          {
            text: '12',
            dataIndex: 'index_i7_12',
            cls: 'nucleotide-header',
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 36
          },
          {
            text: 'Index I5 ID',
            dataIndex: 'index_i5_id',
            summaryRenderer: function () {
              var grid = Ext.getCmp('pool-grid');
              var sequencerChemistry = grid.baseColours.sequencerChemistry;
              var labels = '';

              if (sequencerChemistry === 2) {
                labels = '<span class="summary-green">% green:</span><br><span class="summary-red">% red:</span><br><span class="summary-black">% black:</span>'
              } else if (sequencerChemistry === 4) {
                labels = '<span class="summary-green">% green:</span><br><span class="summary-red">% red:</span>'
              }
              var totalSequencingDepth = grid.getStore().sum('sequencing_depth');
              return totalSequencingDepth > 0
                ? labels
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
            width: 36
          },
          {
            text: '2',
            dataIndex: 'index_i5_2',
            cls: 'nucleotide-header',
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 36
          },
          {
            text: '3',
            dataIndex: 'index_i5_3',
            cls: 'nucleotide-header',
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 36
          },
          {
            text: '4',
            dataIndex: 'index_i5_4',
            cls: 'nucleotide-header',
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 36
          },
          {
            text: '5',
            dataIndex: 'index_i5_5',
            cls: 'nucleotide-header',
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 36
          },
          {
            text: '6',
            dataIndex: 'index_i5_6',
            cls: 'nucleotide-header',
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 36
          },
          {
            text: '7',
            dataIndex: 'index_i5_7',
            cls: 'nucleotide-header',
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 36
          },
          {
            text: '8',
            dataIndex: 'index_i5_8',
            cls: 'nucleotide-header',
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 36
          },
          {
            text: '9',
            dataIndex: 'index_i5_9',
            cls: 'nucleotide-header',
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 36
          },
          {
            text: '10',
            dataIndex: 'index_i5_10',
            cls: 'nucleotide-header',
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 36
          },
          {
            text: '11',
            dataIndex: 'index_i5_11',
            cls: 'nucleotide-header',
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 36
          },
          {
            text: '12',
            dataIndex: 'index_i5_12',
            cls: 'nucleotide-header',
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 36
          }
        ],
        store: [],
        dockedItems: [
          {
            xtype: 'toolbar',
            dock: 'top',
            items:
              [
                {
                  xtype: 'combobox',
                  id: 'sequencerChemistryCb',
                  store: Ext.create('Ext.data.Store', {
                    fields: ['sequencerChemistry', 'name'],
                    data: [{
                      sequencerChemistry: 0,
                      name: 'N/A',
                      tooltip: 'None'
                    },
                    {
                      sequencerChemistry: 2,
                      name: '2-ch',
                      tooltip: 'Illumina 2-channel SBS technology'
                    },
                    {
                      sequencerChemistry: 4,
                      name: '4-ch',
                      tooltip: 'Illumina 4-channel SBS technology'
                    }
                    ]
                  }),
                  queryMode: 'local',
                  displayField: 'name',
                  valueField: 'sequencerChemistry',
                  value: 0,
                  forceSelection: true,
                  allowBlank: false,
                  fieldLabel: 'Chemistry',
                  labelWidth: 65,
                  width: 150,
                  disabled: true,
                  listeners: {
                    change: function (cb, newValue, oldValue, eOpts) {
                      var poolGrid = Ext.getCmp('pool-grid');
                      poolGrid.baseColours = me.getBaseColours(newValue);
                      Ext.getCmp('index-generator-grid').fireEvent('reset');
                      poolGrid.getView().refresh();
                    }
                  },
                  listConfig: {
                    getInnerTpl: function () {
                      return '<span data-qtip="{tooltip}">{name}</span>';
                    }
                  }
                },
                {
                  xtype: 'tbseparator'
                },
                {
                  xtype: 'numberfield',
                  id: 'minHammingDistanceBox',
                  fieldLabel: '<span data-qtip="Minimum Hamming distance">Min. HD</span>',
                  allowBlank: false,
                  disabled: true,
                  minValue: 1,
                  maxValue: 5,
                  value: 3,
                  labelWidth: 55,
                  width: 125,
                  listeners: {
                    change: function (cb, newValue, oldValue, eOpts) {
                      var grid = Ext.getCmp('index-generator-grid');
                      grid.fireEvent('reset');
                      Ext.getCmp('pool-grid').getView().refresh();
                    }
                  }
                },
                '->',
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
              ]
          },
          {
            xtype: 'toolbar',
            dock: 'bottom',
            items:
              [
                {
                  xtype: 'textfield',
                  id: 'pool_name',
                  fieldLabel: 'Pool name',
                  itemId: 'pool-name',
                  text: 'Pool name',
                  labelWidth: 70,
                  width: 200,
                  maxLength: 5,
                  enforceMaxLength: true,
                  allowBlank: false,
                  regex: /^[A-Z]+$/,
                  regexText: 'Only A-Z are allowed',
                  msgTarget: 'side',
                  disabled: true
                },
                '->',
                {
                  xtype: 'button',
                  id: 'save-pool-button',
                  itemId: 'save-pool-button',
                  iconCls: 'fa fa-floppy-o fa-lg',
                  text: 'Save Pool',
                  disabled: true
                },
                {
                  xtype: 'button',
                  id: 'save-pool-ignore-errors-button',
                  itemId: 'save-pool-ignore-errors-button',
                  iconCls: 'fa fa-floppy-o fa-lg',
                  text: 'Ignore error(s) and Save Pool',
                  disabled: true,
                },
              ]
          },
        ]
      }
    ];

    me.callParent(arguments);
  },

  getBaseColours: function (sequencerChemistry) {
    sequencerChemistry = sequencerChemistry ? sequencerChemistry : 0;

    var baseColoursBySequencerChemistry = [
      {
        sequencerChemistry: 0,
        green: [],
        red: [],
        black: []
      },
      {
        sequencerChemistry: 2,
        green: ['A', 'T'],
        red: ['A', 'C'],
        black: ['G']
      },
      {
        sequencerChemistry: 4,
        green:  ['G', 'T'],
        red: ['A', 'C'],
        black: []
      },
    ];
    
    return baseColoursBySequencerChemistry.find(function (o) { return o.sequencerChemistry === sequencerChemistry });

  },

  renderNucleotide: function (val, meta) {

    var baseColours = this.baseColours;
    meta.tdCls = 'nucleotide';

    if (baseColours.green.includes(val) & baseColours.red.includes(val)) {
      meta.tdStyle += 'background-color:#fffacd;';
      return val;
    } else if (baseColours.green.includes(val)) {
      meta.tdStyle += 'background-color:#dcedc8;';
      return val;
    } else if (baseColours.red.includes(val)) {
      meta.tdStyle += 'background-color:#ef9a9a;';
      return val;
    }

    meta.tdStyle = '';
    return val
  },

  calculateColorDiversity: function (records, values) {

    var baseColours = Ext.getCmp('pool-grid').baseColours;
  
    var diversity = { green: 0, red: 0 , black: 0};

    for (var i = 0; i < values.length; i++) {
      var nuc = values[i];
      if (nuc && nuc !== ' ') {
        if (baseColours.green.includes(nuc)) {
          diversity.green += records[i].get('sequencing_depth');
        }
        if (baseColours.red.includes(nuc)) {
          diversity.red += records[i].get('sequencing_depth');
        }
        if (baseColours.black.includes(nuc)) {
          diversity.black += records[i].get('sequencing_depth');
        }
      }
    }
    return diversity;
  },

  renderSummary: function (value, summaryData, dataIndex, meta) {
    var grid = Ext.getCmp('pool-grid');
    var sequencerChemistry = grid.baseColours.sequencerChemistry;
    var store = grid.getStore();
    var result = '';
    var totalSequencingDepth = 0;
    meta.tdCls = 'summary-colours';

    if (store.getCount() > 1 && (value.green > 0 || value.red > 0 || value.black > 0)) {
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
      var black = parseInt(((value.black / totalSequencingDepth) * 100).toFixed(0));

      if (sequencerChemistry === 4) {
        result = Ext.String.format('{0}<br/>{1}', green, red);
      } else if (sequencerChemistry === 2) {
        result = Ext.String.format('{0}<br/>{1}<br/>{2}', green, red, black);
      }

      if (sequencerChemistry !== 0) {
        if ((green < 20 && red > 80) || (red < 20 && green > 80) || (black > 80)) {
          meta.tdCls = 'problematic-cycle';
          result += '<br/>!';
        }
      }
    }

    return result;
  },

  addToIndexStore: function (store, IndexTypeIds, refreshView, me) {

    var startViewCounter = me.viewRefreshCounter;
    IndexTypeIds.forEach(function (id) {
      Ext.Ajax.request({
        url: store.proxy.url,
        method: 'GET',
        timeout: 60000,
        scope: this,
        params: {
          index_type_id: id
        },

        success: function (response) {
          var obj = Ext.JSON.decode(response.responseText);
          if (obj) {
            // Add the id of the index type here rather than getting it via 
            // the API, it's 10x faster
            obj.map(function(e){e.index_type = id})
            store.suspendEvents(false);
            store.add(obj);
            store.resumeEvents();
            if (refreshView) {
              // Only refresh the view after the last request has been completed
              me.viewRefreshCounter++;
              if (me.viewRefreshCounter - startViewCounter === IndexTypeIds.length * 2) {
                Ext.getCmp('index-generator-grid').getView().refresh();
              }
            }
          } else {
            new Noty({ text: response.statusText, type: 'error' }).show();
          }
        },

        failure: function (response) {
          var error = response.statusText;
          try {
            error = Ext.JSON.decode(response.responseText).message;
          } catch (e) { }
          new Noty({ text: error, type: 'error' }).show();
          console.error(response);
        }
      })
    })

  },

  addToIndexPairStore: function (IndexTypeIds) {
    var store = Ext.getStore('IndexPairs');
    IndexTypeIds.forEach(function (id) {
      Ext.Ajax.request({
        url: store.proxy.url,
        method: 'GET',
        timeout: 60000,
        scope: this,
        params: {
          index_type_id: id
        },

        success: function (response) {
          var obj = Ext.JSON.decode(response.responseText);
          if (obj) {
            // Add the id of the index type here rather than getting it via 
            // the API, it's 10x faster
            store.suspendEvents(false);
            store.add(obj);
            store.resumeEvents();
          } else {
            new Noty({ text: response.statusText, type: 'error' }).show();
          }
        },

        failure: function (response) {
          var error = response.statusText;
          try {
            error = Ext.JSON.decode(response.responseText).message;
          } catch (e) { }
          new Noty({ text: error, type: 'error' }).show();
          console.error(response);
        }
      })
    })

  }

});

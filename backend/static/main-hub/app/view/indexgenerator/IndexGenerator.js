Ext.define("MainHub.view.indexgenerator.IndexGenerator", {
  extend: "Ext.container.Container",
  xtype: "index-generator",
  id: "poolingContainer",

  requires: [
    "MainHub.components.BaseGrid",
    "MainHub.view.indexgenerator.IndexGeneratorController"
  ],

  controller: "index-generator",

  layout: {
    type: "hbox",
    align: "stretch"
  },
  padding: 15,

  initComponent: function () {
    var me = this;

    me.items = [
      {
        xtype: "basegrid",
        id: "index-generator-grid",
        itemId: "index-generator-grid",
        height: Ext.Element.getViewportHeight() - 94,
        padding: 0,
        margin: "0 15px 0 0",
        flex: 1,
        header: {
          title: "Libraries and Samples for Pooling",
          items: [
            {
              xtype: "checkbox",
              boxLabel:
                '<span data-qtip="Check, to show only the requests for which you are responsible">As Handler</span>',
              itemId: "as-handler-index-generator-checkbox",
              margin: "0 15 0 0",
              cls: "grid-header-checkbox",
              checked: false,
            },
            {
              xtype: "combobox",
              id: "poolSizeCb",
              itemId: "poolSizeCb",
              store: "PoolSizes",
              queryMode: "local",
              displayField: "name",
              valueField: "id",
              forceSelection: true,
              cls: "panel-header-combobox",
              fieldLabel: '<span data-qtip="Sequencing kit">Seq. Kit</span>',
              labelWidth: 50,
              width: 285,
            },
          ],
        },
        store: "IndexGenerator",
        enableColumnHide: false,

        columns: [
          {
            xtype: "checkcolumn",
            itemId: "check-column",
            dataIndex: "selected",
            resizable: false,
            tdCls: "no-dirty",
            width: 36,
          },
          {
            text: "Name",
            dataIndex: "name",
            minWidth: 200,
            flex: 1
          },
          {
            text: "Barcode",
            dataIndex: "barcode",
            resizable: false,
            width: 90
          },
          {
            text: "",
            dataIndex: "record_type",
            resizable: false,
            width: 30,
            renderer: function (value) {
              return value.charAt(0);
            }
          },
          {
            text: "Depth (M)",
            tooltip: "Sequencing Depth",
            dataIndex: "sequencing_depth",
            width: 85
          },
          {
            text: "Length",
            tooltip: "Read Length",
            dataIndex: "read_length",
            width: 70,
            editor: {
              xtype: "combobox",
              queryMode: "local",
              valueField: "id",
              displayField: "name",
              store: "readLengthsStore",
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
              var store = Ext.getStore("readLengthsStore");
              var record = store.findRecord("id", value, 0, false, true, true);

              return record ? record.get("name") : "";
            }
            //listeners:{
            //beforeselect: function(combo, record, index) {
            //if(record.get('obsolete') == 2 ){
            //   return false;
            //  }
            //  }
            //}
          },

          {
            text: "Protocol",
            tooltip: "Library Preparation Protocol",
            dataIndex: "library_protocol_name",
            renderer: "gridCellTooltipRenderer",
            width: 150
          },
          {
            text: "Index Type",
            dataIndex: "index_type",
            width: 150,
            editor: {
              id: "indexTypePoolingEditor",
              xtype: "combobox",
              queryMode: "local",
              displayField: "name",
              valueField: "id",
              //store: 'IndexTypes',
              store: "GeneratorIndexTypes",
              matchFieldWidth: false,
              forceSelection: true
            },
            renderer: function (value, meta) {
              var record = meta.column
                .getEditor()
                .getStore()
                .findRecord("id", value, 0, false, true, true);
              var val = "";

              if (record) {
                val = record.get("name");
                meta.tdAttr = Ext.String.format('data-qtip="{0}"', val);
              }

              return val;
            },
          },
          {
            text: "# of Index Reads",
            dataIndex: "index_reads",
            tooltip: "Index Type",
            width: 130,
            editor: {
              xtype: "combobox",
              id: "indexReadsEditorIndexGenerator",
              itemId: "indexReadsEditorIndexGenerator",
              queryMode: "local",
              displayField: "label",
              valueField: "num",
              store: Ext.create("Ext.data.Store", {
                fields: [
                  { name: "num", type: "int" },
                  { name: "label", type: "string" },
                ],
                // sorters: [{property: 'num', direction: 'DESC'}],
                data: [
                  { num: 0, label: "None" },
                  { num: 7, label: "I7 only" },
                  { num: 5, label: "I5 only" },
                  { num: 75, label: "I7 + I5" },
                  { num: 752, label: "I7 + I5 (Pair/UDI)" },
                ],
              }),
              forceSelection: true,
            },
            renderer: function (value, meta, record) {
              var item = meta.column
                .getEditor()
                .getStore()
                .findRecord("num", value);
              return item ? item.get("label") : value;
            },
          },
          {
            text: "Index I7",
            dataIndex: "index_i7",
            width: 100,
            editor: {
              xtype: "combobox",
              id: "indexI7EditorIndexGenerator",
              itemId: "indexI7EditorIndexGenerator",
              queryMode: "local",
              displayField: "name",
              displayTpl: Ext.create(
                "Ext.XTemplate",
                '<tpl for=".">',
                "{index}",
                "</tpl>"
              ),
              valueField: "index",
              store: "indexI7Store",
              regex: new RegExp(
                "^(?=(?:.{6}|.{8}|.{10}|.{12}|.{24})$)[ATCG]+$"
              ),
              regexText:
                "Only A, T, C and G (uppercase) are allowed. Index length must be 6, 8, 10, 12 or 24.",
              matchFieldWidth: false,
            },
            renderer: function (value, meta, record) {
              if (value) {
                var store = meta.column.getEditor().getStore();
                store.clearFilter(true);
                store.filter("index_type", record.get("index_type"), true);
                var index = store.findRecord(
                  "index",
                  value,
                  0,
                  false,
                  true,
                  true
                );
                if (index) {
                  value = index.get("name");
                }
              }
              return value;
            },
          },
          {
            text: "Index I5",
            dataIndex: "index_i5",
            width: 100,
            editor: {
              xtype: "combobox",
              id: "indexI5EditorIndexGenerator",
              itemId: "indexI5EditorIndexGenerator",
              queryMode: "local",
              displayField: "name",
              displayTpl: Ext.create(
                "Ext.XTemplate",
                '<tpl for=".">',
                "{index}",
                "</tpl>"
              ),
              valueField: "index",
              store: "indexI5Store",
              regex: new RegExp(
                "^(?=(?:.{6}|.{8}|.{10}|.{12}|.{24})$)[ATCG]+$"
              ),
              regexText:
                "Only A, T, C and G (uppercase) are allowed. Index length must be 6, 8, 10, 12 or 24.",
              matchFieldWidth: false,
            },
            renderer: function (value, meta, record) {
              if (value) {
                var store = meta.column.getEditor().getStore();
                store.clearFilter(true);
                store.filter("index_type", record.get("index_type"), true);
                var index = store.findRecord(
                  "index",
                  value,
                  0,
                  false,
                  true,
                  true
                );
                if (index) {
                  value = index.get("name");
                }
              }
              return value;
            },
          },
        ],

        plugins: [
          {
            ptype: "bufferedrenderer",
            trailingBufferZone: 100,
            leadingBufferZone: 100
          },
          {
            ptype: "rowediting",
            clicksToEdit: 2,
          },
        ],

        dockedItems: [],

        features: [
          {
            ftype: "grouping",
            id: "index-generator-grid-grouping",
            startCollapsed: true,
            groupHeaderTpl: [
              "<strong>Request {children:this.getRequestId}: {children:this.getName}</strong> (#: {children:this.getCount}, {children:this.isPooled}Total Depth: {children:this.getTotalDepth} M, Seq. Kit: {children:this.getPoolSize})",
              {
                getName: function (children) {
                  return children[0].get("request_name");
                },
                getRequestId: function (children) {
                  return children[0].get("request");
                },
                isPooled: function (children) {
                  return children[0].get("pooled_libraries") ? "Pool, " : "";
                },
                getTotalDepth: function (children) {

                  var totalDepth = Ext.Array.sum(
                    Ext.Array.pluck(
                      Ext.Array.pluck(children, "data"),
                      "sequencing_depth"
                    )
                  );
                  // Check whether totalDepth is an integer
                  // and format accordingly, to avoid float 
                  // point rounding ugliness
                  if (!Number.isInteger(Number(totalDepth.toFixed(2)))){
                    totalDepth = Ext.util.Format.number(totalDepth, "0.00")
                  }
                  return totalDepth;
                },
                getCount: function (children) {
                  return children.length;
                },
                getPoolSize: function (children) {
                  return children[0].get("pool_size_user_name");
                },
              },
            ],
          },
        ],
      },
      {
        xtype: "grid",
        id: "pool-grid",
        itemId: "pool-grid",
        cls: "pooling-grid",
        baseColours: {
          sequencerChemistry: 0,
          green: [],
          red: [],
          black: [],
        },
        header: {
          title: "Pool",
          height: 56,
          items: [
            {
              xtype: "combobox",
              itemId: "start-coordinate",
              store: "StartCoordinates",
              queryMode: "local",
              displayField: "coordinate",
              valueField: "coordinate",
              forceSelection: true,
              cls: "panel-header-combobox",
              fieldLabel: "Start Coordinate",
              labelWidth: 110,
              width: 200,
              margin: "0 15px 0 0",
              hidden: true
            },
            {
              xtype: "combobox",
              itemId: "direction",
              store: Ext.data.Store({
                data: [
                  { id: 1, value: "right" },
                  { id: 2, value: "down" },
                  { id: 3, value: "diagonal" }
                ]
              }),
              queryMode: "local",
              displayField: "value",
              valueField: "value",
              forceSelection: true,
              cls: "panel-header-combobox",
              fieldLabel: "Direction",
              labelWidth: 65,
              width: 160,
              hidden: true
            }
          ]
        },
        height: Ext.Element.getViewportHeight() - 94,
        flex: 1,
        features: [{ ftype: "summary" }],
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
            text: "Name",
            dataIndex: "name",
            width: 200
          },
          {
            text: "",
            dataIndex: "record_type",
            width: 30,
            renderer: function (value) {
              return value.charAt(0);
            }
          },
          {
            text: "Depth (M)",
            dataIndex: "sequencing_depth",
            width: 85,
            summaryType: "sum",
            summaryRenderer: function (value) {
              return value > 0 ? value : "";
            }
          },
          {
            text: "Coord",
            dataIndex: "coordinate",
            width: 65
          },
          {
            text: "Index I7 ID",
            dataIndex: "index_i7_id",
            width: 90,
            summaryRenderer: function () {
              var grid = Ext.getCmp("pool-grid");
              var sequencerChemistry = grid.baseColours.sequencerChemistry;
              var labels = "";

              if (sequencerChemistry === 2) {
                labels =
                  '<span class="summary-green">% green:</span><br>' +
                  '<span class="summary-red">% red:</span><br>' +
                  '<span class="summary-black">% black:</span>';
              } 
              else if (sequencerChemistry === 20) {
                labels =
                '<span class="summary-green">% green:</span><br>' +
                '<span class="summary-blue">% blue:</span><br>' +
                '<span class="summary-black">% black:</span>';
              }
              else if (sequencerChemistry === 4) {
                labels =
                  '<span class="summary-green">% green:</span><br>' +
                  '<span class="summary-red">% red:</span>';
              }
              var totalSequencingDepth = grid
                .getStore()
                .sum("sequencing_depth");
              return totalSequencingDepth > 0 ? labels : "";
            },
          },
          {
            text: "1",
            dataIndex: "index_i7_1",
            cls: "nucleotide-header",
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 36,
          },
          {
            text: "2",
            dataIndex: "index_i7_2",
            cls: "nucleotide-header",
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 36,
          },
          {
            text: "3",
            dataIndex: "index_i7_3",
            cls: "nucleotide-header",
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 36,
          },
          {
            text: "4",
            dataIndex: "index_i7_4",
            cls: "nucleotide-header",
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 36,
          },
          {
            text: "5",
            dataIndex: "index_i7_5",
            cls: "nucleotide-header",
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 36,
          },
          {
            text: "6",
            dataIndex: "index_i7_6",
            cls: "nucleotide-header",
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 36,
          },
          {
            text: "7",
            dataIndex: "index_i7_7",
            cls: "nucleotide-header",
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 36,
          },
          {
            text: "8",
            dataIndex: "index_i7_8",
            cls: "nucleotide-header",
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 36,
          },
          {
            text: "9",
            dataIndex: "index_i7_9",
            cls: "nucleotide-header",
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 36,
          },
          {
            text: "10",
            dataIndex: "index_i7_10",
            cls: "nucleotide-header",
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 36,
          },
          {
            text: "11",
            dataIndex: "index_i7_11",
            cls: "nucleotide-header",
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 36,
          },
          {
            text: "12",
            dataIndex: "index_i7_12",
            cls: "nucleotide-header",
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 36,
          },
          {
            text: "Index I5 ID",
            dataIndex: "index_i5_id",
            summaryRenderer: function () {
              var grid = Ext.getCmp("pool-grid");
              var sequencerChemistry = grid.baseColours.sequencerChemistry;
              var labels = "";

              if (sequencerChemistry === 2) {
                labels =
                  '<span class="summary-green">% green:</span><br>' +
                  '<span class="summary-red">% red:</span><br>' +
                  '<span class="summary-black">% black:</span>';
              }   
              else if (sequencerChemistry === 20) {
                labels =
                '<span class="summary-green">% green:</span><br>' +
                '<span class="summary-blue">% blue:</span><br>' +
                '<span class="summary-black">% black:</span>';
              }
              else if (sequencerChemistry === 4) {
                labels =
                  '<span class="summary-green">% green:</span><br>' +
                  '<span class="summary-red">% red:</span>';
              }
              var totalSequencingDepth = grid
                .getStore()
                .sum("sequencing_depth");
              return totalSequencingDepth > 0 ? labels : "";
            },
            width: 90
          },
          {
            text: "1",
            dataIndex: "index_i5_1",
            cls: "nucleotide-header",
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 36,
          },
          {
            text: "2",
            dataIndex: "index_i5_2",
            cls: "nucleotide-header",
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 36,
          },
          {
            text: "3",
            dataIndex: "index_i5_3",
            cls: "nucleotide-header",
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 36,
          },
          {
            text: "4",
            dataIndex: "index_i5_4",
            cls: "nucleotide-header",
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 36,
          },
          {
            text: "5",
            dataIndex: "index_i5_5",
            cls: "nucleotide-header",
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 36,
          },
          {
            text: "6",
            dataIndex: "index_i5_6",
            cls: "nucleotide-header",
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 36,
          },
          {
            text: "7",
            dataIndex: "index_i5_7",
            cls: "nucleotide-header",
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 36,
          },
          {
            text: "8",
            dataIndex: "index_i5_8",
            cls: "nucleotide-header",
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 36,
          },
          {
            text: "9",
            dataIndex: "index_i5_9",
            cls: "nucleotide-header",
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 36,
          },
          {
            text: "10",
            dataIndex: "index_i5_10",
            cls: "nucleotide-header",
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 36,
          },
          {
            text: "11",
            dataIndex: "index_i5_11",
            cls: "nucleotide-header",
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 36,
          },
          {
            text: "12",
            dataIndex: "index_i5_12",
            cls: "nucleotide-header",
            renderer: me.renderNucleotide,
            summaryType: me.calculateColorDiversity,
            summaryRenderer: me.renderSummary,
            width: 36,
          },
        ],
        store: [],
        dockedItems: [
          {
            xtype: "toolbar",
            dock: "top",
            items: [
              {
                xtype: "combobox",
                id: "sequencerChemistryCb",
                store: Ext.create("Ext.data.Store", {
                  fields: ["sequencerChemistry", "name"],
                  data: [
                    {
                      sequencerChemistry: 0,
                      name: "N/A",
                      tooltip: "None",
                    },
                    {
                      sequencerChemistry: 2,
                      name: "2-ch",
                      tooltip: "Illumina 2-channel SBS technology",
                    },
                    {
                      sequencerChemistry: 20,
                      name: "2-ch XLEAP",
                      tooltip: "Illumina 2-channel XLEAP SBS technology",
                    },
                    {
                      sequencerChemistry: 4,
                      name: "4-ch",
                      tooltip: "Illumina 4-channel SBS technology",
                    },
                  ],
                }),
                queryMode: "local",
                displayField: "name",
                valueField: "sequencerChemistry",
                value: 0,
                forceSelection: true,
                allowBlank: false,
                fieldLabel: "Chemistry",
                labelWidth: 65,
                width: 190,
                disabled: true,
                listeners: {
                  change: function (cb, newValue, oldValue, eOpts) {
                    var poolGrid = Ext.getCmp("pool-grid");
                    poolGrid.baseColours = me.getBaseColours(newValue);
                    Ext.getCmp("index-generator-grid").fireEvent("reset");
                    poolGrid.getView().refresh();
                    // Trigger datachange event on poolGrid store,
                    // because the summary row is not updated by
                    // simply refreshing the view
                    poolGrid.store.fireEvent('datachanged');
                  },
                },
                listConfig: {
                  getInnerTpl: function () {
                    return '<span data-qtip="{tooltip}">{name}</span>';
                  },
                },
              },
              {
                xtype: "tbseparator",
              },
              {
                xtype: "numberfield",
                id: "minHammingDistanceBox",
                fieldLabel:
                  '<span data-qtip="Minimum Hamming distance">Min. HD</span>',
                allowBlank: false,
                disabled: true,
                minValue: 1,
                maxValue: 5,
                value: 3,
                labelWidth: 55,
                width: 125,
                listeners: {
                  change: function (cb, newValue, oldValue, eOpts) {
                    var grid = Ext.getCmp("index-generator-grid");
                    grid.fireEvent("reset");
                    Ext.getCmp("pool-grid").getView().refresh();
                  },
                },
              },
              "->",
              {
                xtype: "button",
                id: "generate-indices-button",
                itemId: "generate-indices-button",
                iconCls: "fa fa-cogs fa-lg",
                text: "Generate Indices",
                disabled: true,
              },

              /* for future:
                {
                  xtype: 'button',
                  itemId: 'download-index-list-button',
                  text: 'Download Index List (csv)',
                  iconCls: 'fa fa-file-excel-o fa-lg'
                },
                */
            ],
          },
          {
            xtype: "toolbar",
            dock: "bottom",
            items: [
              {
                xtype: "textfield",
                id: "pool_name",
                fieldLabel: "Pool name",
                itemId: "pool-name",
                text: "Pool name",
                labelWidth: 70,
                width: 200,
                maxLength: 12,
                enforceMaxLength: true,
                allowBlank: false,
                regex: /^[A-Za-z0-9_]+$/,
                regexText: "Only A-Z a-z 0-9 and _ are allowed",
                msgTarget: "side",
                disabled: true,
              },
              "->",
              {
                xtype: "button",
                id: "save-pool-button",
                itemId: "save-pool-button",
                iconCls: "fa fa-floppy-o fa-lg",
                text: "Save Pool",
                disabled: true,
              },
              {
                xtype: "button",
                id: "save-pool-ignore-errors-button",
                itemId: "save-pool-ignore-errors-button",
                iconCls: "fa fa-floppy-o fa-lg",
                text: "Ignore error(s) and Save Pool",
                disabled: true,
              },
            ],
          },
        ],
      },
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
        black: [],
      },
      {
        sequencerChemistry: 2,
        green: ["A", "T"],
        red: ["A", "C"],
        black: ["G"],
      },
      {
        sequencerChemistry: 20,
        green: ["T", "C"],
        // For XLEAP, red is actually blue, but it's
        // easier to keep using red "in the background"
        red: ["A", "C"],
        black: ["G"],
      },
      {
        sequencerChemistry: 4,
        green: ["G", "T"],
        red: ["A", "C"],
        black: [],
      },
    ];

    return baseColoursBySequencerChemistry.find(function (o) {
      return o.sequencerChemistry === sequencerChemistry;
    });
  },

  renderNucleotide: function (val, meta) {
    var baseColours = this.baseColours;
    meta.tdCls = "nucleotide";

    if (baseColours.green.includes(val) & baseColours.red.includes(val)) {
      meta.tdStyle += baseColours.sequencerChemistry === 20 ? // For XLEAP, it should be teal
                      "background-color:#b2d8d8;" : 
                      "background-color:#fffacd;";
      return val;
    } else if (baseColours.green.includes(val)) {
      meta.tdStyle += "background-color:#dcedc8;";
      return val;
    } else if (baseColours.red.includes(val)) {
      meta.tdStyle += baseColours.sequencerChemistry === 20 ? // For XLEAP, it should be blue
                      "background-color:#bfe6ff;" :
                      "background-color:#ef9a9a;";
      return val;
    }

    meta.tdStyle = "";
    return val;
  },

  calculateColorDiversity: function (records, values) {
    var baseColours = Ext.getCmp("pool-grid").baseColours;

    var diversity = { green: 0, red: 0, black: 0 };

    for (var i = 0; i < values.length; i++) {
      var nuc = values[i];
      if (nuc && nuc !== " ") {
        if (baseColours.green.includes(nuc)) {
          diversity.green += records[i].get("sequencing_depth");
        }
        if (baseColours.red.includes(nuc)) {
          diversity.red += records[i].get("sequencing_depth");
        }
        if (baseColours.black.includes(nuc)) {
          diversity.black += records[i].get("sequencing_depth");
        }
      }
    }
    return diversity;
  },

  renderSummary: function (value, summaryData, dataIndex, meta) {
    var grid = Ext.getCmp("pool-grid");
    var sequencerChemistry = grid.baseColours.sequencerChemistry;
    var store = grid.getStore();
    var result = "";
    var totalSequencingDepth = 0;
    meta.tdCls = "summary-colours";

    if (
      store.getCount() > 1 &&
      (value.green > 0 || value.red > 0 || value.black > 0)
    ) {
      if (dataIndex.split("_")[1] === "i7") {
        // Consider only non empty Index I7 indices
        store.each(function (record) {
          if (record.get("index_i7") !== "") {
            totalSequencingDepth += record.get("sequencing_depth");
          }
        });
      } else {
        // Consider only non empty Index I5 indices
        store.each(function (record) {
          if (record.get("index_i5") !== "") {
            totalSequencingDepth += record.get("sequencing_depth");
          }
        });
      }

      var green = parseInt(
        ((value.green / totalSequencingDepth) * 100).toFixed(0)
      );
      var red = parseInt(((value.red / totalSequencingDepth) * 100).toFixed(0));
      var black = parseInt(
        ((value.black / totalSequencingDepth) * 100).toFixed(0)
      );

      if (sequencerChemistry === 4) {
        result = Ext.String.format("{0}<br/>{1}", green, red);
      } else if (sequencerChemistry === 2 || sequencerChemistry === 20) {
        result = Ext.String.format("{0}<br/>{1}<br/>{2}", green, red, black);
      }

      if (sequencerChemistry !== 0) {
        if (
          (green < 20 && red > 80) ||
          (red < 20 && green > 80) ||
          black > 80
        ) {
          meta.tdCls = "problematic-cycle";
          result += "<br/>!";
        }
      }
    }

    return result;
  }
});

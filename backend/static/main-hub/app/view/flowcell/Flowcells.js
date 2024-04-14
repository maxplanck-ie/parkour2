Ext.define("MainHub.view.flowcell.Flowcells", {
  extend: "Ext.container.Container",
  xtype: "flowcells",

  requires: [
    "MainHub.components.BaseGrid",
    "MainHub.components.MonthPicker",
    "MainHub.view.flowcell.FlowcellsController"
  ],

  controller: "flowcells",

  anchor: "100% -1",
  layout: "fit",

  items: [
    {
      xtype: "basegrid",
      id: "flowcells-grid",
      itemId: "flowcells-grid",
      store: "Flowcells",

      header: {
        title: "Load Flowcells",
        items: [
          {
            xtype: "checkbox",
            boxLabel:
              '<span data-qtip="Check, to show only the requests for which you are responsible">As Handler</span>',
            itemId: "as-handler-flowcell-checkbox",
            margin: "0 15 0 0",
            cls: "grid-header-checkbox",
            checked: false,
          },
          {
            xtype: "parkourmonthpicker",
            itemId: "start-month-picker",
            fieldLabel: "From",
            labelWidth: 37,
            labelStyle: "color: white;",
            margin: "0 15px 0 0"
          },
          {
            xtype: "parkourmonthpicker",
            itemId: "end-month-picker",
            fieldLabel: "To",
            labelWidth: 20,
            labelStyle: "color: white;",
            margin: "0 15px 0 0"
          },
          {
            xtype: "parkoursearchfield",
            itemId: "search-field",
            emptyText: "Search",
            margin: "0 15px 0 0",
            width: 320
          },
          {
            xtype: "button",
            itemId: "load-button",
            text: "Load",
            iconCls: "x-fa fa-plus",
            style: {
              border: "1px solid #ffffffbe !important"
            }
          }
        ]
      },

      customConfig: {
        qualityCheckMenuOptions: ["completed"],
        listeners: {
          refresh: function (d) {
            Ext.each(d.panel.columns, function (col) {
              col.autoSize();
            });
          }
        }
      },

      columns: {
        defaults: {
          minWidth: 150,
          flex: 1
        },
        items: [
          {
            xtype: "checkcolumn",
            itemId: "check-column",
            dataIndex: "selected",
            resizable: false,
            menuDisabled: true,
            hideable: false,
            tdCls: "no-dirty",
            minWidth: 35,
            width: 35,
            flex: 0
          },
          {
            text: "Lane",
            dataIndex: "name",
            hideable: false,
            minWidth: 85,
            width: 85,
            filter: { type: "string" },
          },
          {
            text: "Pool",
            dataIndex: "pool_name",
            hideable: false,
            minWidth: 85,
            width: 85,
            filter: { type: "string" },
            renderer: function (value) {
              return Ext.String.format(
                '<a href="javascript:void(0)" class="pool-name">{0}</a>',
                value
              );
            }
          },
          {
            text: "Date",
            dataIndex: "create_time",
            renderer: Ext.util.Format.dateRenderer(),
            minWidth: 100,
            width: 100,
            filter: { type: "date" },
          },
          {
            text: "Request",
            dataIndex: "request",
            filter: { type: "string" }
          },
          {
            text: "Length",
            tooltip: "Read Length",
            dataIndex: "read_length_name",
            minWidth: 80,
            width: 80,
            filter: { type: "list" },
          },
          {
            text: "Index I7",
            dataIndex: "index_i7_show",
            minWidth: 80,
            width: 80,
            //renderer: 'yesNoRenderer',
            filter: { type: "string" }
          },
          {
            text: "Index I5",
            dataIndex: "index_i5_show",
            minWidth: 80,
            width: 80,
            //renderer: 'yesNoRenderer',
            filter: { type: "string" }
          },
          {
            text: "Sequencing kit",
            dataIndex: "pool_size_name",
            minWidth: 200,
            width: 200,
            filter: { type: "list" },
          },
          /*  {
          text: 'Equal nucl.',
          tooltip: 'Equal Representation of Nucleotides',
          dataIndex: 'equal_representation',
          renderer: 'yesNoRenderer',
          filter: { type: 'boolean' }
        },*/
          {
            text: "Run name",
            dataIndex: "run_name",
            filter: { type: "string" },
          },
          {
            text: "Cycles: R1, R2, I1, I2",
            renderer: function (val, meta, record, rowIndex) {
              console.log(record);
              return Ext.String.format(
                "{0}, {1}, {2}, {3}",
                record.get("read1_cycles"),
                record.get("read2_cycles"),
                record.get("index1_cycles"),
                record.get("index2_cycles")
              );
            },
          },
          {
            text: "Library protocol",
            dataIndex: "protocol",
            filter: { type: "string" }
          },
          {
            text: "Loading conc., pM",
            tooltip: "Loading Concentration of Pool in pM",
            dataIndex: "loading_concentration",
            filter: { type: "number" },
            editor: {
              xtype: "numberfield",
              decimalPrecision: 1,
              minValue: 0
            }
          },
          {
            text: "PhiX %",
            dataIndex: "phix",
            filter: { type: "number" },
            editor: {
              xtype: "numberfield",
              decimalPrecision: 1,
              minValue: 0
            }
          }
        ]
      },

      features: [
        {
          ftype: "grouping",
          id: "flowcells-grid-grouping",
          startCollapsed: true,
          enableGroupingMenu: false,
          groupHeaderTpl: [
            "<strong>{children:this.getFlowcellId} ({children:this.getDate})</strong>",
            {
              getFlowcellId: function (children) {
                return children[0].get("flowcell_id");
              },
              getDate: function (children) {
                return Ext.util.Format.date(children[0].get("create_time"));
              }
            }
          ]
        }
      ],

      dockedItems: [
        {
          xtype: "toolbar",
          dock: "bottom",
          items: [
            {
              itemId: "download-benchtop-protocol-button",
              text: "Download Benchtop Protocol",
              iconCls: "fa fa-file-excel-o fa-lg"
            },
            {
              itemId: "download-sample-sheet-button",
              text: "Download Sample Sheet (ILMN v2)",
              iconCls: "fa fa-file-excel-o fa-lg",
            },
            "->",
            {
              itemId: "cancel-button",
              iconCls: "fa fa-ban fa-lg",
              text: "Cancel"
            },
            {
              // xtype: 'button',
              itemId: "save-button",
              iconCls: "fa fa-floppy-o fa-lg",
              text: "Save"
            }
          ]
        }
      ]
    }
  ]
});

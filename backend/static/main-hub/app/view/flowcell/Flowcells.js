Ext.define("MainHub.view.flowcell.Flowcells", {
  extend: "Ext.container.Container",
  xtype: "flowcells",

  requires: [
    "MainHub.components.BaseGrid",
    "MainHub.components.MonthPicker",
    "MainHub.view.flowcell.FlowcellsController",
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
            xtype: "parkourmonthpicker",
            itemId: "start-month-picker",
            fieldLabel: "From",
            labelWidth: 37,
            labelStyle: "color: white;",
            margin: "0 15px 0 0",
          },
          {
            xtype: "parkourmonthpicker",
            itemId: "end-month-picker",
            fieldLabel: "To",
            labelWidth: 20,
            labelStyle: "color: white;",
            margin: "0 15px 0 0",
          },
          {
            xtype: "parkoursearchfield",
            itemId: "search-field",
            emptyText: "Search",
            margin: "0 15px 0 0",
            width: 320,
          },
          {
            xtype: "button",
            itemId: "load-button",
            text: "Load",
            iconCls: "x-fa fa-plus",
            style: {
              border: "1px solid #ffffffbe !important",
            },
          },
        ],
      },

      customConfig: {
        qualityCheckMenuOptions: ["completed"],
        listeners: {
          refresh: function (d) {
            Ext.each(d.panel.columns, function (col) {
              col.autoSize();
            });
          },
        },
      },

      columns: {
        defaults: {
          minWidth: 150,
          flex: 1,
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
            flex: 0,
          },
          {
            text: "Lane",
            dataIndex: "name",
            hideable: false,
            filter: { type: "string" },
          },
          {
            text: "Pool",
            dataIndex: "pool_name",
            hideable: false,
            filter: { type: "string" },
            renderer: function (value) {
              return Ext.String.format(
                '<a href="javascript:void(0)" class="pool-name">{0}</a>',
                value,
              );
            },
          },
          {
            text: "Date",
            dataIndex: "create_time",
            renderer: Ext.util.Format.dateRenderer(),
            filter: { type: "date" },
          },
          {
            text: "Request",
            dataIndex: "request",
            filter: { type: "string" },
          },
          {
            text: "Length",
            tooltip: "Read Length",
            dataIndex: "read_length_name",
            filter: { type: "list" },
          },
          {
            text: "Index I7",
            dataIndex: "index_i7_show",
            //renderer: 'yesNoRenderer',
            filter: { type: "string" },
          },
          {
            text: "Index I5",
            dataIndex: "index_i5_show",
            //renderer: 'yesNoRenderer',
            filter: { type: "string" },
          },
          {
            text: "Sequencer",
            dataIndex: "sequencer_name",
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
            text: "Library protocol",
            dataIndex: "protocol",
            filter: { type: "string" },
          },
          {
            text: "Loading Conc.",
            tooltip: "Loading Concentration",
            dataIndex: "loading_concentration",
            filter: { type: "number" },
            editor: {
              xtype: "numberfield",
              decimalPrecision: 1,
              minValue: 0,
            },
          },
          {
            text: "PhiX %",
            dataIndex: "phix",
            filter: { type: "number" },
            editor: {
              xtype: "numberfield",
              decimalPrecision: 1,
              minValue: 0,
            },
          },
        ],
      },

      features: [
        {
          ftype: "grouping",
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
              },
            },
          ],
        },
      ],

      dockedItems: [
        {
          xtype: "toolbar",
          dock: "bottom",
          items: [
            {
              itemId: "download-benchtop-protocol-button",
              text: "Download Benchtop Protocol",
              iconCls: "fa fa-file-excel-o fa-lg",
            },
            {
              itemId: "download-sample-sheet-button",
              text: "Download Sample Sheet",
              iconCls: "fa fa-file-excel-o fa-lg",
            },
            "->",
            {
              itemId: "cancel-button",
              iconCls: "fa fa-ban fa-lg",
              text: "Cancel",
            },
            {
              // xtype: 'button',
              itemId: "save-button",
              iconCls: "fa fa-floppy-o fa-lg",
              text: "Save",
            },
          ],
        },
      ],
    },
  ],
});

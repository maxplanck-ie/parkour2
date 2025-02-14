Ext.define("MainHub.view.incominglibraries.IncomingLibraries", {
  extend: "Ext.container.Container",
  xtype: "incoming-libraries",

  requires: [
    "MainHub.components.BaseGrid",
    "MainHub.view.incominglibraries.CheckboxGroupingFeature",
    "MainHub.view.incominglibraries.IncomingLibrariesController"
  ],

  controller: "incominglibraries-incominglibraries",

  anchor: "100% -1",
  layout: "fit",

  initComponent: function () {
    this.callParent(arguments);
    var style = document.createElement("style");
    style.type = "text/css";
    style.innerHTML =
      "td.userEntry.x-grid-cell-selected { color: #404040 !important; background-color: #ffefbb !important; }";
    document.getElementsByTagName("head")[0].appendChild(style);
  },

  items: [
    {
      xtype: "basegrid",
      id: "incoming-libraries-grid",
      itemId: "incoming-libraries-grid",
      store: "IncomingLibraries",
      customConfig: {
        qualityCheckMenuOptions: ["passed", "compromised", "failed"]
      },

      header: {
        title: "Incoming Libraries and Samples",
        items: [
          {
            xtype: "fieldcontainer",
            defaultType: "checkboxfield",
            layout: "hbox",
            margin: "0 20 0 0",
            items: [
              {
                boxLabel: "Show Libraries",
                itemId: "show-libraries-checkbox",
                margin: "0 15 0 0",
                cls: "grid-header-checkbox",
                boxLabelAlign: "before",
                checked: true
              },
              {
                boxLabel: "Show Samples",
                itemId: "show-samples-checkbox",
                cls: "grid-header-checkbox",
                boxLabelAlign: "before",
                checked: true
              }
            ]
          },
          {
            xtype: "parkoursearchfield",
            itemId: "search-field",
            emptyText: "Search",
            width: 320
          }
        ]
      },

      columns: {
        items: [
          {
            xtype: "checkcolumn",
            itemId: "check-column",
            dataIndex: "selected",
            resizable: false,
            menuDisabled: true,
            hideable: false,
            tdCls: "no-dirty userEntry",
            width: 35
          },
          {
            text: "Name",
            dataIndex: "name",
            minWidth: 250,
            hideable: false,
            flex: 1,
            tdCls: "userEntry",
            renderer: function (value, meta) {
              meta.tdStyle = "font-weight:bold";
              return value;
            }
          },
          {
            text: "",
            dataIndex: "barcode",
            resizable: false,
            hideable: false,
            tdCls: "userEntry",
            width: 30,
            renderer: function (value, meta) {
              return value.charAt(2);
            }
          },
          {
            text: "Barcode",
            dataIndex: "barcode",
            resizable: false,
            hideable: false,
            tdCls: "userEntry",
            width: 90
          },
          {
            text: "Input Type",
            tooltip: "Input Type",
            dataIndex: "nucleic_acid_type_name",
            tdCls: "userEntry",
            minWidth: 100,
            flex: 1,
            renderer: function (value, meta) {
              meta.tdAttr = 'data-qtip="' + value + '"';
              return value;
            }
          },
          {
            text: "Protocol",
            tooltip: "Library Preparation Protocol",
            dataIndex: "library_protocol_name",
            tdCls: "userEntry",
            minWidth: 100,
            flex: 1,
            renderer: function (value, meta) {
              meta.tdAttr = 'data-qtip="' + value + '"';
              return value;
            }
          },
          {
            text: "ng/µl",
            tooltip: "Concentration (user)",
            dataIndex: "concentration",
            tdCls: "userEntry",
            width: 70
          },
          {
            text: "F/S",
            tooltip: "Concentration Determined by (user)",
            dataIndex: "concentration_method",
            tdCls: "userEntry",
            width: 50,
            hidden: true
          },
          {
            text: "qPCR (nM)",
            tooltip: "qPCR Result (user)",
            dataIndex: "qpcr_result",
            tdCls: "userEntry",
            width: 85,
            hidden: true
          },
          {
            text: "bp",
            tooltip: "Mean Fragment Size (user)",
            dataIndex: "mean_fragment_size",
            tdCls: "userEntry",
            width: 45
          },
          {
            text: "RQN",
            tooltip: "RNA Quality (user)",
            dataIndex: "rna_quality",
            tdCls: "userEntry",
            width: 55,
            renderer: function (value) {
              return value === 11 ? "Determined by Facility" : value;
            }
          },

          // Facility
          {
            text: "DF",
            tooltip: "Dilution Factor (facility)",
            dataIndex: "dilution_factor",
            tdCls: "facilityEntry",
            width: 80,
            editor: {
              xtype: "numberfield",
              minValue: 1,
              allowDecimals: false
            },
            hidden: true
          },
          {
            text: "ng/µl",
            tooltip: "Concentration (facility)",
            dataIndex: "concentration_facility",
            tdCls: "facilityEntry",
            width: 90,
            editor: {
              xtype: "numberfield",
              minValue: 0
            }
          },
          {
            text: "µl",
            tooltip: "Sample Volume (facility)",
            dataIndex: "sample_volume_facility",
            tdCls: "facilityEntry",
            width: 80,
            editor: {
              xtype: "numberfield",
              minValue: 0,
              allowDecimals: false
            }
          },
          {
            text: "ng",
            tooltip: "Amount (facility): DF * ng/µl * µl",
            dataIndex: "amount_facility",
            tdCls: "facilityEntry",
            width: 80,
            editor: {
              xtype: "numberfield",
              minValue: 0
            }
          },
          {
            text: "F/S",
            tooltip: "Concentration Determined by (facility)",
            dataIndex: "concentration_method_facility",
            tdCls: "facilityEntry",
            width: 80,
            editor: {
              xtype: "combobox",
              queryMode: "local",
              displayField: "name",
              valueField: "id",
              store: "concentrationMethodsStore",
              matchFieldWidth: false,
              forceSelection: true
            },
            renderer: function (value, meta) {
              var store = Ext.getStore("concentrationMethodsStore");
              var record = store.findRecord("id", value);

              if (record) {
                meta.tdAttr = 'data-qtip="' + record.get("name") + '"';
              }

              return record ? record.getShortName() : "";
            },
            hidden: true
          },
          {
            text: "qPCR (nM)",
            tooltip: "qPCR Result (facility)",
            dataIndex: "qpcr_result_facility",
            tdCls: "facilityEntry",
            width: 85,
            editor: {
              xtype: "numberfield",
              id: "qPCRResultEditor",
              minValue: 0
            },
            hidden: true
          },
          {
            text: "bp",
            tooltip: "Size Distribution (facility)",
            dataIndex: "size_distribution_facility",
            tdCls: "facilityEntry",
            width: 80,
            editor: {
              xtype: "numberfield",
              minValue: 0
            }
          },
          {
            text: "RQN",
            tooltip: "RNA Quality (facility)",
            dataIndex: "rna_quality_facility",
            tdCls: "facilityEntry",
            width: 80,
            editor: {
              xtype: "combobox",
              id: "rnaQualityIncomingEditor",
              queryMode: "local",
              valueField: "value",
              displayField: "name",
              displayTpl: Ext.create(
                "Ext.XTemplate",
                '<tpl for=".">{value}</tpl>'
              ),
              store: "rnaQualityStore",
              regex: new RegExp("^(11|10|[1-9]?(.[0-9]+)?|.[0-9]+)$"),
              regexText: "Only values between 1 and 10 are allowed."
            },
            renderer: function (value) {
              return value === 11 ? "Determined by Facility" : value;
            }
          },
          {
            text: "Comments",
            tooltip: "Comments (facility)",
            dataIndex: "comments_facility",
            tdCls: "facilityEntry",
            width: 150,
            editor: {
              xtype: "textfield"
            },
            renderer: function (value, meta) {
              meta.tdAttr = 'data-qtip="' + value + '"';
              return value;
            }
          }
        ]
      },

      features: [
        {
          ftype: "checkboxgrouping",
          checkDataIndex: "samples_submitted",
          startCollapsed: true,
          enableGroupingMenu: false,
          groupHeaderTpl: [
            '<span data-qtip="Samples submitted" style="margin-right:5px">',
            '<input type="checkbox" class="group-checkbox" {children:this.getChecked}>',
            "</span>",
            "<strong>Request: {children:this.getName}</strong> ",
            "(#: {rows.length}, Total Depth: {children:this.getTotalDepth} M)",
            {
              getName: function (children) {
                return children[0].get("request_name");
              },
              getTotalDepth: function (children) {
                return Ext.Array.sum(
                  Ext.Array.pluck(
                    Ext.Array.pluck(children, "data"),
                    "sequencing_depth"
                  )
                );
              },
              getChecked: function (children) {
                return children[0].get(this.owner.checkDataIndex)
                  ? "checked"
                  : "";
              }
            }
          ]
        }
      ]
    }
  ]
});

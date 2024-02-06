Ext.define("MainHub.view.libraries.Libraries", {
  extend: "Ext.container.Container",
  xtype: "libraries",
  controller: "libraries-libraries",

  requires: [
    "MainHub.view.libraries.LibrariesController",
    "MainHub.view.libraries.LibraryWindow",
  ],

  anchor: "100% -1",
  layout: "fit",

  initComponent: function () {
    this.searchString = "";
    this.statusFilter = "all";
    this.libraryProtocolFilter = -1;

    this.callParent(arguments);
  },

  items: [
    {
      xtype: "treepanel",
      id: "librariesTable",
      itemId: "librariesTable",
      cls: "no-leaf-icons",
      height: Ext.Element.getViewportHeight() - 64,
      region: "center",
      padding: 15,
      sortableColumns: false,
      enableColumnMove: false,
      rowLines: true,
      listeners: {
        afteritemexpand: function (node, index, item, eOpts) {
          this.getView().mask("Loading...");
          var requestId = node.data.id;
          requestId !== null &&
            requestId !== "root" &&
            Ext.Ajax.request({
              url: Ext.String.format(
                "api/requests/" + requestId + "/get_poolpaths/",
              ),
              method: "GET",
              scope: this,
              disableCaching: false,
              success: function (response) {
                var librariesStore = Ext.getStore("librariesStore");
                var responseObject = Ext.JSON.decode(response.responseText);
                var parentNode = librariesStore.data.map[requestId];
                parentNode.childNodes.map(function (element) {
                  var pools = (
                    responseObject.poolpaths[element.data.barcode] || []
                  ).toString();
                  element.set("pool", pools);
                  element.commit();
                  return element;
                });
                this.getView().unmask();
              },
              failure: function (response) {
                new Noty({ text: response.statusText, type: "error" }).show();
                console.error(response);
                this.getView().unmask();
              },
            });
        },
      },
      viewConfig: {
        trackOver: false,
        stripeRows: false,
        getRowClass: function (record) {
          var rowClass = "";
          if (record.get("leaf")) {
            if (record.get("status") === -1) {
              rowClass = "invalid";
            } else if (record.get("status") === -2) {
              rowClass = "compromised";
            } else {
              rowClass =
                record.getRecordType() === "Library"
                  ? "library-row"
                  : "sample-row";
            }
          }
          return rowClass;
        },
      },

      header: {
        title: "Libraries and Samples",
        height: 56,
        items: [
          {
            xtype: "fieldcontainer",
            defaultType: "checkboxfield",
            layout: "hbox",
            margin: "0 20 0 0",
            items: [
              {
                name: "showAll",
                boxLabel: "Show All",
                boxLabelAlign: "before",
                checked: true,
                id: "showAlllr",
                margin: "0 15 0 0",
                cls: "grid-header-checkbox",
                hidden: false,
                listeners: {
                  change: function (checkbox, newValue, oldValue, eOpts) {
                    if (newValue) {
                      Ext.getStore(
                        "librariesStore",
                      ).getProxy().extraParams.showAll = "True";
                      Ext.getStore("librariesStore").load();
                    } else {
                      Ext.getStore(
                        "librariesStore",
                      ).getProxy().extraParams.showAll = "False";
                      Ext.getStore("librariesStore").load();
                    }
                  },
                },
              },
              {
                boxLabel: "Show Libraries",
                itemId: "showLibrariesCheckbox",
                margin: "0 15 0 0",
                cls: "grid-header-checkbox",
                boxLabelAlign: "before",
                checked: true,
                hidden: true,
              },
              {
                boxLabel: "Show Samples",
                itemId: "showSamplesCheckbox",
                cls: "grid-header-checkbox",
                boxLabelAlign: "before",
                checked: true,
                hidden: true,
              },
            ],
          },
          {
            xtype: "combobox",
            id: "statusCombobox",
            itemId: "statusCombobox",
            queryMode: "local",
            displayField: "name",
            valueField: "id",
            cls: "panel-header-combobox",
            emptyText: "Status",
            width: 100,
            matchFieldWidth: false,
            listConfig: {
              width: 220,
            },
            editable: false,
            style: { marginRight: "15px" },
            store: Ext.create("Ext.data.Store", {
              fields: ["id", "name"],
              data: [
                { id: "all", name: "All Statuses" },
                { id: "0", name: "Pending Submission" },
                { id: "1", name: "Submission Completed" },
                {
                  id: "2",
                  name: "Quality Check Approved",
                },
                { id: "3", name: "Library Prepared" },
                { id: "4", name: "Library Pooled" },
                { id: "5", name: "Sequencing" },
                { id: "6", name: "Delivered" },
                { id: "-1", name: "Quality Check Failed" },
                {
                  id: "-2",
                  name: "Quality Check Compromised",
                },
              ],
            }),
            listeners: {
              scope: this,
              change: function (combo, newValue, oldValue, eOpts) {
                var grid = combo.up("treepanel");
                grid.getView().mask("Loading...");
                this.statusFilter = newValue;
                var selectedRecord = combo.findRecordByValue(newValue);
                var textWidth = Ext.util.TextMetrics.measure(
                  combo.inputEl,
                  selectedRecord.get(combo.displayField),
                ).width;
                combo.setWidth(textWidth + 55);
                var librariesStore = Ext.getStore("librariesStore");
                var extraParams = {
                  showAll: "True",
                };
                if (this.statusFilter && this.statusFilter !== "all") {
                  extraParams.statusFilter = this.statusFilter;
                }
                if (
                  this.libraryProtocolFilter &&
                  this.libraryProtocolFilter !== -1
                ) {
                  extraParams.libraryProtocolFilter =
                    this.libraryProtocolFilter;
                }
                if (this.searchString) {
                  extraParams.searchString = this.searchString;
                }
                librariesStore.getProxy().setExtraParams(extraParams);
                librariesStore.load({
                  callback: function (records, operation, success) {
                    if (!success) {
                      new Noty({
                        text:
                          operation.getError() ||
                          "Error occurred while setting the filter.",
                        type: "error",
                      }).show();
                    }
                    grid.getView().unmask();
                  },
                });
              },
            },
          },
          {
            xtype: "combobox",
            id: "libraryProtocolCombobox",
            itemId: "libraryProtocolCombobox",
            queryMode: "local",
            displayField: "name",
            valueField: "id",
            cls: "panel-header-combobox",
            emptyText: "Library Protocol",
            width: 160,
            matchFieldWidth: false,
            listConfig: {
              width: 300,
            },
            editable: false,
            style: { marginRight: "15px" },
            store: "libraryProtocolsStore",
            listeners: {
              scope: this,
              expand: function (combo) {
                combo
                  .getStore()
                  .insert(0, { id: -1, name: "All Library Protocols" });
              },
              change: function (combo, newValue, oldValue, eOpts) {
                var grid = combo.up("treepanel");
                grid.getView().mask("Loading...");
                this.libraryProtocolFilter = newValue;
                var selectedRecord = combo.findRecordByValue(newValue);
                var textWidth = Ext.util.TextMetrics.measure(
                  combo.inputEl,
                  selectedRecord.get(combo.displayField),
                ).width;
                combo.setWidth(textWidth > 220 ? 220 : textWidth + 55);
                var librariesStore = Ext.getStore("librariesStore");
                var extraParams = {
                  showAll: "True",
                };
                if (this.statusFilter && this.statusFilter !== "all") {
                  extraParams.statusFilter = this.statusFilter;
                }
                if (
                  this.libraryProtocolFilter &&
                  this.libraryProtocolFilter !== -1
                ) {
                  extraParams.libraryProtocolFilter =
                    this.libraryProtocolFilter;
                }
                if (this.searchString) {
                  extraParams.searchString = this.searchString;
                }
                librariesStore.getProxy().setExtraParams(extraParams);
                librariesStore.load({
                  callback: function (records, operation, success) {
                    if (!success) {
                      new Noty({
                        text:
                          operation.getError() ||
                          "Error occurred while setting the filter.",
                        type: "error",
                      }).show();
                    }
                    grid.getView().unmask();
                  },
                });
              },
            },
          },
          {
            xtype: "parkoursearchfield",
            itemId: "search-field",
            emptyText: "Search",
            width: 320,
            listeners: {
              scope: this,
              change: Ext.Function.createBuffered(
                function (field, newValue, oldValue) {
                  var grid = field.up("treepanel");
                  grid.getView().mask("Loading...");
                  this.searchString = newValue;
                  var librariesStore = Ext.getStore("librariesStore");
                  var extraParams = {
                    showAll: "True",
                  };
                  if (this.statusFilter && this.statusFilter !== "all") {
                    extraParams.statusFilter = this.statusFilter;
                  }
                  if (
                    this.libraryProtocolFilter &&
                    this.libraryProtocolFilter !== -1
                  ) {
                    extraParams.libraryProtocolFilter =
                      this.libraryProtocolFilter;
                  }
                  if (this.searchString) {
                    extraParams.searchString = this.searchString;
                  }
                  librariesStore.getProxy().setExtraParams(extraParams);
                  librariesStore.load({
                    callback: function (records, operation, success) {
                      if (!success) {
                        new Noty({
                          text:
                            operation.getError() ||
                            "Error occurred while searching.",
                          type: "error",
                        }).show();
                      }
                      grid.getView().unmask();
                    },
                  });
                },
                500,
                this,
              ),
            },
          },
        ],
      },

      rootVisible: false,
      store: "librariesStore",

      columns: {
        defaults: {
          width: 100,
        },
        items: [
          {
            xtype: "treecolumn",
            text: "Name",
            dataIndex: "name",
            menuDisabled: true,
            hideable: false,
            minWidth: 250,
            flex: 1,
            renderer: function (value, meta, record) {
              if (record.get("leaf")) {
                meta.tdStyle = "font-weight:bold";
                return value;
              } else {
                return Ext.String.format(
                  "<strong>Request: {0}</strong> (#: {1}, Total Depth: {2})",
                  value,
                  record.get("total_records_count"),
                  record.get("total_sequencing_depth"),
                );
              }
            },
          },
          {
            text: "Status",
            dataIndex: "status",
            resizable: false,
            menuDisabled: true,
            hideable: false,
            width: 60,
            renderer: function (value, meta) {
              if (meta.record.get("leaf")) {
                var statusClass = "status ";

                // Draw a color circle depending on the status value
                if (value === -1) {
                  statusClass += "quality-check-failed";
                  meta.tdAttr = 'data-qtip="Quality check failed"';
                } else if (value === -2) {
                  statusClass += "quality-check-compromised";
                  meta.tdAttr = 'data-qtip="Quality check compromised"';
                } else if (value === 0) {
                  statusClass += "pending-submission";
                  meta.tdAttr = 'data-qtip="Pending submission"';
                } else if (value === 1) {
                  statusClass += "submission-completed";
                  meta.tdAttr = 'data-qtip="Submission completed"';
                } else if (value === 2) {
                  statusClass += "quality-check-approved";
                  meta.tdAttr = 'data-qtip="Quality check approved"';
                } else if (value === 3) {
                  statusClass += "library-prepared";
                  meta.tdAttr = 'data-qtip="Library prepared"';
                } else if (value === 4) {
                  statusClass += "library-pooled";
                  meta.tdAttr = 'data-qtip="Library pooled"';
                } else if (value === 5) {
                  statusClass += "sequencing";
                  meta.tdAttr = 'data-qtip="Sequencing"';
                } else if (value === 6) {
                  statusClass += "delivered";
                  meta.tdAttr = 'data-qtip="Delivered"';
                }
                return '<div class="' + statusClass + '"></div>';
              }
            },
          },
          {
            text: "",
            dataIndex: "record_type",
            resizable: false,
            menuDisabled: true,
            hideable: false,
            width: 30,
            renderer: function (value, meta) {
              return meta.record.getRecordType().charAt(0);
            },
          },
          {
            text: "Barcode",
            dataIndex: "barcode",
            resizable: false,
            menuDisabled: true,
            hideable: false,
            width: 95,
            renderer: function (value, meta) {
              return meta.record.getBarcode();
            },
          },
          {
            text: "Pool Paths",
            dataIndex: "pool",
            resizable: false,
            menuDisabled: true,
            hideable: false,
            width: 95,
            renderer: function (value, meta) {
              return meta.record.getPoolPaths();
            },
          },
          {
            text: "Date",
            dataIndex: "create_time",
            renderer: Ext.util.Format.dateRenderer("d.m.Y"),
          },
          {
            text: "Nuc. Type",
            tooltip: "Nucleic Acid Type",
            dataIndex: "nucleic_acid_type_name",
            renderer: "gridCellTooltipRenderer",
          },
          {
            text: "Protocol",
            tooltip: "Library Preparation Protocol",
            dataIndex: "library_protocol_name",
            renderer: "gridCellTooltipRenderer",
          },
          {
            text: "Lib. Type",
            tooltip: "Library Type",
            dataIndex: "library_type_name",
            renderer: "gridCellTooltipRenderer",
          },
          {
            text: "ng/μl",
            tooltip: "Concentration",
            dataIndex: "concentration",
          },
          {
            text: "RQN",
            tooltip: "RNA Quality",
            dataIndex: "rna_quality",
            width: 55,
            renderer: function (value) {
              return value === 11 ? "Determined by Facility" : value;
            },
          },
          {
            text: "bp",
            tooltip: "Mean Fragment Size",
            dataIndex: "mean_fragment_size",
          },
          {
            text: "Index Type",
            dataIndex: "index_type_name",
            renderer: "gridCellTooltipRenderer",
          },
          {
            text: "Index Reads",
            tooltip: "# of Index Reads",
            dataIndex: "index_reads",
          },
          {
            text: "I7",
            tooltip: "Index I7",
            dataIndex: "index_i7",
          },
          {
            text: "I5",
            tooltip: "Index I5",
            dataIndex: "index_i5",
          },
          {
            text: "Length",
            tooltip: "Read Length",
            dataIndex: "read_length_name",
          },
          {
            text: "Depth (M)",
            tooltip: "Sequencing Depth",
            dataIndex: "sequencing_depth",
          },
          // {
          //   text: 'Amplification',
          //   tooltip: 'Amplification Cycles',
          //   dataIndex: 'amplification_cycles'
          // },
          // {
          //   text: 'Equal nucl.',
          //   tooltip: 'Equal Representation of Nucleotides',
          //   dataIndex: 'equal_representation_nucleotides',
          //   width: 90,
          //   renderer: function (value, meta) {
          //     if (meta.record.get('leaf')) {
          //       return value ? 'Yes' : 'No';
          //     }
          //   }
          // },
          // {
          //   text: 'qPCR (nM)',
          //   tooltip: 'qPCR Result',
          //   dataIndex: 'qpcr_result'
          // },
          // {
          //   text: 'F/S',
          //   tooltip: 'Concentration Determined by',
          //   dataIndex: 'concentration_method',
          //   width: 50,
          //   renderer: function (value, meta) {
          //     if (meta.record.get('leaf')) {
          //       var store = Ext.getStore('concentrationMethodsStore');
          //       var record = store.findRecord('id', value);
          //       var name = record.get('name');
          //       meta.tdAttr = Ext.String.format('data-qtip="{0}"', name);
          //       return name.charAt(0);
          //     }
          //   }
          // },
          {
            text: "Organism",
            dataIndex: "organism_name",
            width: 150,
          },
          {
            text: "Comments",
            dataIndex: "comments",
            renderer: "gridCellTooltipRenderer",
            width: 150,
          },
        ],
      },
    },
  ],
});

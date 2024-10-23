Ext.define("MainHub.view.libraries.BatchAddWindowController", {
  extend: "Ext.app.ViewController",
  alias: "controller.libraries-batchaddwindow",

  config: {
    control: {
      "#": {
        boxready: "boxready"
      },
      "#library-card-button": {
        click: "selectCard"
      },
      "#sample-card-button": {
        click: "selectCard"
      },
      "#batch-add-grid": {
        itemcontextmenu: "showContextMenu",
        beforeedit: "toggleEditors",
        edit: "editRecord",
        validate: "validateAll"
      },
      "#create-empty-records-button": {
        click: "createEmptyRecords"
      },
      "#save-button": {
        click: "save"
      },
      "#download-sample-form": {
        click: "downloadSampleForm"
      },

      // Libraries only
      "#indexTypeEditor": {
        select: "selectIndexType"
      },
      "#indexReadsEditor": {
        select: "selectIndexReads"
      },

      // Samples only
      "#nucleicAcidTypeEditor": {
        select: "selectNucleicAcidType"
      },
      "#libraryProtocolEditor": {
        select: "selectLibraryProtocol"
      },

      // Both Libraries and Samples
      "#measuringUnitEditor": {
        select: "selectMeasuringUnit"
      }
    }
  },

  boxready: function (wnd) {
    if (wnd.mode === "edit") {
      if (wnd.type === "Library") {
        wnd.down("#library-card-button").click();
      } else {
        wnd.down("#sample-card-button").click();
      }
    }

    Ext.apply(Ext.tip.QuickTipManager.getQuickTip(), {
      dismissDelay: 10000 // Hide after 10 seconds
    });
  },

  selectCard: function (btn) {
    var me = this;
    var wnd = btn.up("window");
    var layout = btn.up("panel").getLayout();
    var configuration;

    wnd.setSize(1000, 650);
    wnd.center();
    wnd.getDockedItems('toolbar[dock="bottom"]')[0].show();
    if (wnd.mode === "add") {
      wnd.getDockedItems('toolbar[dock="top"]')[0].show();
    }
    layout.setActiveItem(1);

    if (btn.itemId === "library-card-button") {
      wnd.recordType = "Library";
      wnd.setTitle("Add Libraries");
      wnd
        .getComponent("create-empty-records")
        .getComponent("download-sample-form")
        .setVisible(false);
      configuration = this.getLibraryGridConfiguration(wnd.mode);
    } else {
      wnd.recordType = "Sample";
      wnd.setTitle("Add Samples");
      wnd
        .getComponent("create-empty-records")
        .getComponent("download-sample-form")
        .setVisible(true);
      configuration = this.getSampleGridConfiguration(wnd.mode);
    }

    // Add selected records for editing to the store
    if (wnd.mode === "edit") {
      configuration[0].add(wnd.records);
    }

    wnd.maximize(); // Auto fullscreen

    var grid = Ext.getCmp("batch-add-grid");
    grid.reconfigure(configuration[0], configuration[1]);

    // Flash hint text
    $("#edit-hint")
      .delay(100)
      .fadeIn(500)
      .fadeOut(500)
      .fadeIn(500)
      .fadeOut(500)
      .fadeIn(500);

    // Add empty records on enter
    var numEmptyRecords = wnd.down("#num-empty-records");
    numEmptyRecords.getEl().on("keypress", function (e, fld) {
      if (e.getKey() === e.ENTER) {
        me.createEmptyRecords(numEmptyRecords);
      }
    });
  },

  showContextMenu: function (gridView, record, item, index, e) {
    var me = this;
    e.stopEvent();
    Ext.create("Ext.menu.Menu", {
      plain: true,
      defaults: {
        margin: 5
      },
      items: [
        {
          text: "Apply to All",
          handler: function () {
            var dataIndex = MainHub.Utilities.getDataIndex(e, gridView);
            me.applyToAll(record, dataIndex);
          }
        },
        {
          text: "Delete",
          handler: function () {
            me.delete(record, gridView);
          }
        }
      ]
    }).showAt(e.getXY());
  },

  downloadSampleForm: function (btn) {
    console.log(btn.downloadUrl);
    var form = Ext.create("Ext.form.Panel", { standardSubmit: true });

    form.submit({
      url: btn.downloadUrl,
      method: "GET"
    });
  },

  applyToAll: function (record, dataIndex) {
    var store = record.store;

    if (dataIndex) {
      if (dataIndex === "name") {
        new Noty({ text: "Names must be unique.", type: "warning" }).show();
        return;
      }

      store.each(function (item) {
        if (item !== record) {
          if (dataIndex === "index_type") {
            // Reset Index reads, Index I7, and Index I5,
            // if index types don't match
            if (item.get("index_type") !== record.get("index_type")) {
              item.set({ index_reads: null, index_i7: "", index_i5: "" });
            }
            item.set("index_type", record.get("index_type"));
          }

          // If the # of Index Reads was selected, update Index Type too
          else if (dataIndex === "index_reads") {
            item.set({
              index_reads: record.get("index_reads"),
              index_type: record.get("index_type"),
              // Reset Index I7 and Index I5 for all other records
              index_i7: "",
              index_i5: ""
            });
          }

          // If Index I7 was selected, update the # of Index Reads and Index Types
          else if (dataIndex === "index_i7") {
            // Reset Index I5 for records with different Index Types and Index Reads
            if (
              item.get("index_type") !== record.get("index_type") &&
              item.get("index_reads") !== record.get("index_reads")
            ) {
              item.set("index_i5", "");
            }

            item.set({
              index_i7: "",
              index_reads: record.get("index_reads"),
              index_type: record.get("index_type")
            });
          }

          // If Index I5 was selected, update IndexI7, the # of Index Reads, and Index Types
          else if (dataIndex === "index_i5") {
            item.set({
              index_i5: record.get("index_i5"),
              index_i7: record.get("index_i7"),
              index_reads: record.get("index_reads"),
              index_type: record.get("index_type")
            });
          }

          // Update Input Type
          else if (dataIndex === "nucleic_acid_type") {
            // Reset Library Protocol and Library Type for records
            // with a different Input Type
            if (
              item.get("nucleic_acid_type") !== record.get("nucleic_acid_type")
            ) {
              item.set({
                library_protocol: null,
                library_type: null
              });
            }

            item.set("nucleic_acid_type", record.get("nucleic_acid_type"));
          }

          // If Library Protocol was selected, update Input Type too
          else if (dataIndex === "library_protocol") {
            // Libraries
            if (typeof item.get("nucleic_acid_type") === "undefined") {
              // Reset Library Type for records with a different Library Protocol
              if (
                item.get("library_protocol") !== record.get("library_protocol")
              ) {
                item.set("library_type", null);
              }
            }
            // Samples
            else {
              // Reset Library Type if Input Types Library Protocols
              // are different
              if (
                item.get("nucleic_acid_type") !==
                  record.get("nucleic_acid_type") ||
                (item.get("nucleic_acid_type") ===
                  record.get("nucleic_acid_type") &&
                  item.get("library_protocol") !==
                    record.get("library_protocol"))
              ) {
                item.set("library_type", null);
              }
              item.set("nucleic_acid_type", record.get("nucleic_acid_type"));
            }
            item.set("library_protocol", record.get("library_protocol"));
          }

          // If Library Type was selected, update Library Protocol and Input Type
          else if (dataIndex === "library_type") {
            item.set({
              library_type: record.get("library_type"),
              library_protocol: record.get("library_protocol"),
              nucleic_acid_type: record.get("nucleic_acid_type")
            });
          }

          item.commit();
        }
      });

      // Validate all records
      this.validateAll();
    }
  },

  toggleEditors: function (editor, context) {
    var wnd = this.getView();
    var indexTypeEditor = Ext.getCmp("indexTypeEditor");
    var indexReadsEditor = Ext.getCmp("indexReadsEditor");
    var indexI7Editor = Ext.getCmp("indexI7Editor");
    var indexI5Editor = Ext.getCmp("indexI5Editor");
    var nucleicAcidTypesStore = Ext.getStore("nucleicAcidTypesStore");
    var libraryProtocolEditor = Ext.getCmp("libraryProtocolEditor");
    var libraryProtocolsStore = Ext.getStore("libraryProtocolsStore");
    var libraryTypeEditor = Ext.getCmp("libraryTypeEditor");
    var measuringUnitEditor = Ext.getCmp("measuringUnitEditor");
    var measuredValueEditor = Ext.getCmp("measuredValueEditor");
    var record = context.record;

    // Toggle Library Type
    if (record.get("library_protocol") === null) {
      libraryTypeEditor.disable();
    } else {
      libraryTypeEditor.enable();

      // Filter Library Types store for currently selected Library Protocol
      this.filterLibraryTypes(record.get("library_protocol"));
    }

    // Libraries
    if (wnd.recordType === "Library") {
      // Toggle Index Reads, IndexI7, and IndexI5
      if (record.get("index_type") !== null) {
        if (record.get("index_reads") !== null) {
          indexTypeEditor.fireEvent(
            "select",
            indexTypeEditor,
            indexTypeEditor.findRecordByValue(record.get("index_type"))
          );

          // Toggle IndexI7 and IndexI5
          indexReadsEditor.fireEvent(
            "select",
            indexReadsEditor,
            indexReadsEditor.findRecordByValue(record.get("index_reads"))
          );
        } else {
          indexI7Editor.disable();
          indexI5Editor.disable();
        }
      } else {
        indexReadsEditor.disable();
        indexI7Editor.disable();
        indexI5Editor.disable();
      }

      // Reset Measured Value if Measuring Unit is changed
      if (!measuringUnitEditor.getValue()) {
        measuredValueEditor.setValue(null);
        measuredValueEditor.disable();
        record.set("measured_value", null);
      } else {
        if (measuringUnitEditor.getValue() === "-") {
          measuredValueEditor.setValue(null);
          measuredValueEditor.disable();
          record.set("measured_value", -1);
        } else {
          measuredValueEditor.setValue(null);
          measuredValueEditor.enable();
        }
      }
    }

    // Samples
    else if (wnd.recordType === "Sample") {
      // Toggle Library Protocol
      if (record.get("nucleic_acid_type") === null) {
        libraryProtocolEditor.disable();
      } else {
        libraryProtocolEditor.enable();

        // Filter Library Protocols store for currently selected Input Type
        if (record.get("library_protocol") !== 0) {
          var type = nucleicAcidTypesStore
            .findRecord("id", record.get("nucleic_acid_type"))
            .get("type");
          this.filterLibraryProtocols(libraryProtocolsStore, type);
        }
      }

      // Reset Measured Value if Measuring Unit is changed
      if (!measuringUnitEditor.getValue()) {
        measuredValueEditor.setValue(null);
        measuredValueEditor.disable();
        record.set("measured_value", null);
      } else {
        if (measuringUnitEditor.getValue() === "-") {
          measuredValueEditor.setValue(null);
          measuredValueEditor.disable();
          record.set("measured_value", -1);
        } else {
          measuredValueEditor.setValue(null);
          measuredValueEditor.enable();
        }
      }
    }
  },

  editRecord: function (editor, context) {
    var grid = Ext.getCmp("batch-add-grid");
    var record = context.record;
    var changes = record.getChanges();

    for (var dataIndex in changes) {
      if (changes.hasOwnProperty(dataIndex)) {
        record.set(dataIndex, changes[dataIndex]);
      }
    }

    // Reset Library Type if Library Protocol is empty
    if (
      record.get("library_protocol") === null &&
      record.get("library_type") !== null
    ) {
      record.set("library_type", null);
    }

    // Reset Index I7 and Index I5 if # Index reads is 1 or 0
    if (record.get("index_reads") === 1 && record.get("index_i5") !== "") {
      record.set("index_i5", "");
    } else if (
      record.get("index_reads") === 0 &&
      record.get("index_i7") !== "" &&
      record.get("index_i5") !== ""
    ) {
      record.set({ index_i7: "", index_i5: "" });
    }

    // Reset Measured Value if Measuring Unit is empty
    var measuringUnitEditor = Ext.getCmp("measuringUnitEditor");
    var measuredValueEditor = Ext.getCmp("measuredValueEditor");
    if (!measuringUnitEditor.getValue()) {
      measuredValueEditor.setValue(null);
      measuredValueEditor.disable();
      record.set("measured_value", null);
    } else {
      if (measuringUnitEditor.getValue() === "-") {
        measuredValueEditor.setValue(null);
        measuredValueEditor.disable();
        record.set("measured_value", -1);
      } else {
        measuredValueEditor.setValue(null);
        measuredValueEditor.enable();
      }
    }

    record.commit();

    this.validateRecord(record);
    grid.getView().refresh();
  },

  selectLibraryProtocol: function (fld, record) {
    var libraryTypeEditor = Ext.getCmp("libraryTypeEditor");
    libraryTypeEditor.setValue(null);
    libraryTypeEditor.enable();
    this.filterLibraryTypes(record.get("id"));
  },

  selectIndexType: function (fld, record) {
    var indexReadsEditor = Ext.getCmp("indexReadsEditor");
    var indexI7Editor = Ext.getCmp("indexI7Editor");
    var indexI5Editor = Ext.getCmp("indexI5Editor");
    var indexI7Store = Ext.getStore("indexI7Store");
    var indexI5Store = Ext.getStore("indexI5Store");

    indexReadsEditor.setValue(null);
    indexReadsEditor.getStore().removeAll();
    indexReadsEditor.enable();

    for (var i = 0; i <= record.get("index_reads"); i++) {
      indexReadsEditor.getStore().add({ num: i });
    }

    indexI7Editor.setValue(null);
    indexI5Editor.setValue(null);
    indexI7Editor.disable();
    indexI5Editor.disable();

    indexI7Store.reload({
      params: { index_type_id: record.get("id") }
    });
    indexI5Store.reload({
      params: { index_type_id: record.get("id") }
    });
  },

  selectIndexReads: function (fld, record) {
    var indexI7Editor = Ext.getCmp("indexI7Editor");
    var indexI5Editor = Ext.getCmp("indexI5Editor");

    if (record.get("num") === 1) {
      indexI7Editor.enable();
      indexI5Editor.disable();
      indexI5Editor.setValue(null);
    } else if (record.get("num") === 2) {
      indexI7Editor.enable();
      indexI5Editor.enable();
    } else {
      indexI7Editor.disable();
      indexI5Editor.disable();
      indexI7Editor.setValue(null);
      indexI5Editor.setValue(null);
    }
  },

  selectNucleicAcidType: function (fld, record) {
    var libraryProtocolEditor = Ext.getCmp("libraryProtocolEditor");
    var libraryProtocolsStore = Ext.getStore("libraryProtocolsStore");
    var libraryTypeEditor = Ext.getCmp("libraryTypeEditor");

    libraryTypeEditor.setValue(null);
    libraryTypeEditor.disable();

    this.filterLibraryProtocols(libraryProtocolsStore, record.get("type"));
    libraryProtocolEditor.enable();
  },

  selectMeasuringUnit: function (fld, record) {
    // Reset Measured Value if Measuring Unit is changed
    var measuringUnitEditor = Ext.getCmp("measuringUnitEditor");
    var measuredValueEditor = Ext.getCmp("measuredValueEditor");
    if (!measuringUnitEditor.getValue()) {
      measuredValueEditor.setValue(null);
      measuredValueEditor.disable();
      record.set("measured_value", null);
    } else {
      if (measuringUnitEditor.getValue() === "-") {
        measuredValueEditor.setValue(null);
        measuredValueEditor.disable();
        record.set("measured_value", -1);
      } else {
        measuredValueEditor.setValue(null);
        measuredValueEditor.enable();
      }
    }
  },

  filterLibraryProtocols: function (store, value) {
    store.clearFilter();
    store.filterBy(function (item) {
      return item.get("type") === value;
    });
  },

  filterLibraryTypes: function (libraryProtocolId) {
    var store = Ext.getStore("libraryTypesStore");
    store.clearFilter();
    store.filterBy(function (item) {
      return item.get("library_protocol").indexOf(libraryProtocolId) !== -1;
    });
  },

  getLibraryGridConfiguration: function (mode) {
    var store = Ext.create("Ext.data.Store", {
      model: "MainHub.model.libraries.BatchAdd.Library",
      data: []
    });

    var columns = Ext.Array.merge(this.getCommonColumns(mode), [
      {
        text: "Size (bp)",
        dataIndex: "mean_fragment_size",
        tooltip: "Mean Fragment Size",
        editor: {
          xtype: "numberfield",
          minValue: 0
        },
        renderer: this.errorRenderer,
        width: 100
      },
      {
        text: "Measuring Unit",
        dataIndex: "measuring_unit",
        tooltip: "Measuring Unit",
        width: 120,
        editor: {
          id: "measuringUnitEditor",
          itemId: "measuringUnitEditor",
          xtype: "combobox",
          queryMode: "local",
          valueField: "id",
          displayField: "name",
          store: {
            fields: ["id", "name"],
            data: [
              { id: "ng/µl", name: "ng/µl (Concentration)" },
              { id: "-", name: "Unknown" }
            ]
          },
          forceSelection: true,
          listConfig: {
            minWidth: 200
          }
        },
        renderer: this.comboboxErrorRenderer
      },
      {
        text: "Measured Value",
        dataIndex: "measured_value",
        tooltip: "Measured Value",
        width: 120,
        editor: {
          id: "measuredValueEditor",
          itemId: "measuredValueEditor",
          xtype: "numberfield",
          minValue: 0
        },
        renderer: this.errorRenderer
      },
      {
        text: "Index Type",
        dataIndex: "index_type",
        tooltip: "Index Type",
        width: 100,
        editor: {
          xtype: "combobox",
          id: "indexTypeEditor",
          itemId: "indexTypeEditor",
          queryMode: "local",
          displayField: "name",
          valueField: "id",
          store: "IndexTypes",
          matchFieldWidth: false,
          forceSelection: true
        },
        renderer: this.comboboxErrorRenderer
      },
      {
        text: "# of Index Reads",
        dataIndex: "index_reads",
        tooltip: "Number of Index Reads",
        width: 130,
        editor: {
          xtype: "combobox",
          id: "indexReadsEditor",
          itemId: "indexReadsEditor",
          queryMode: "local",
          displayField: "num",
          valueField: "num",
          store: Ext.create("Ext.data.Store", {
            fields: [{ name: "num", type: "int" }],
            data: []
          }),
          forceSelection: true
        },
        renderer: function (value, meta, record) {
          var item = meta.column
            .getEditor()
            .getStore()
            .findRecord("num", value);
          var dataIndex = meta.column.dataIndex;

          if (
            record &&
            Object.keys(record.get("errors")).indexOf(dataIndex) !== -1
          ) {
            meta.tdCls += " invalid-record";
            meta.tdAttr = 'data-qtip="' + record.get("errors")[dataIndex] + '"';
          }

          return item ? item.get("num") : value;
        }
      },
      {
        text: "Index I7",
        dataIndex: "index_i7",
        tooltip: "Index I7",
        width: 140,
        editor: {
          xtype: "combobox",
          id: "indexI7Editor",
          itemId: "indexI7Editor",
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
          regex: new RegExp("^(?=(?:.{6}|.{8}|.{10}|.{12}|.{24})$)[ATCG]+$"),
          regexText:
            "Only A, T, C, and G (uppercase) are allowed. Index length must be 6, 8, 10, 12, or 24.",
          matchFieldWidth: false
        },
        renderer: this.errorRenderer
      },
      {
        text: "Index I5",
        dataIndex: "index_i5",
        tooltip: "Index I5",
        width: 140,
        editor: {
          xtype: "combobox",
          id: "indexI5Editor",
          itemId: "indexI5Editor",
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
          regex: new RegExp("^(?=(?:.{6}|.{8}|.{10}|.{12}|.{24})$)[ATCG]+$"),
          regexText:
            "Only A, T, C, and G (uppercase) are allowed. Index length must be 6, 8, 10, 12, or 24.",
          matchFieldWidth: false
        },
        renderer: this.errorRenderer
      },
      {
        text: "Comment Library",
        dataIndex: "comments",
        tooltip: "Comments",
        width: 200,
        editor: {
          xtype: "textfield",
          allowBlank: true
        }
      }
    ]);

    // Sorting the columns
    var order = [
      "numberer",
      "name",
      "barcode",
      "library_protocol",
      "comments",
      "measuring_unit",
      "measured_value",
      "mean_fragment_size",
      "volume",
      "library_type",
      "read_length",
      "sequencing_depth",
      "index_type",
      "index_reads",
      "index_i7",
      "index_i5",
      "organism"
    ];
    columns = this.sortColumns(columns, order);

    return [store, columns];
  },

  getSampleGridConfiguration: function (mode) {
    var store = Ext.create("Ext.data.Store", {
      model: "MainHub.model.libraries.BatchAdd.Sample",
      data: []
    });

    var columns = Ext.Array.merge(this.getCommonColumns(mode), [
      {
        text: "Measuring Unit",
        dataIndex: "measuring_unit",
        tooltip: "Measuring Unit",
        width: 120,
        editor: {
          id: "measuringUnitEditor",
          itemId: "measuringUnitEditor",
          xtype: "combobox",
          queryMode: "local",
          valueField: "id",
          displayField: "name",
          store: {
            fields: ["id", "name"],
            data: [
              { id: "ng/µl", name: "ng/µl (Concentration)" },
              { id: "M", name: "M (Cells)" },
              { id: "-", name: "Unknown" }
            ]
          },
          forceSelection: true,
          listConfig: {
            minWidth: 200
          }
        },
        renderer: this.comboboxErrorRenderer
      },
      {
        text: "Measured Value",
        dataIndex: "measured_value",
        tooltip: "Measured Value",
        width: 120,
        editor: {
          id: "measuredValueEditor",
          itemId: "measuredValueEditor",
          xtype: "numberfield",
          minValue: 0
        },
        renderer: this.errorRenderer
      },
      {
        text: "Input Type",
        dataIndex: "nucleic_acid_type",
        tooltip: "Input Type",
        width: 200,
        editor: {
          xtype: "combobox",
          id: "nucleicAcidTypeEditor",
          itemId: "nucleicAcidTypeEditor",
          queryMode: "local",
          displayField: "name",
          valueField: "id",
          store: "nucleicAcidTypesStore",
          matchFieldWidth: false,
          forceSelection: true
        },
        renderer: this.comboboxErrorRenderer
      },
      {
        text: "GMO",
        dataIndex: "gmo",
        tooltip: "Genetically Modified Organism",
        width: 90,
        editor: {
          xtype: "combobox",
          queryMode: "local",
          valueField: "value",
          displayField: "name",
          store: {
            fields: ["id", "name"],
            data: [
              { value: true, name: "Yes" },
              { value: false, name: "No" }
            ]
          },
          forceSelection: true
        },
        renderer: this.comboboxErrorRenderer
      },
      {
        text: "Biosafety Level",
        dataIndex: "biosafety_level",
        tooltip: "Biosafety Level",
        width: 120,
        editor: {
          xtype: "combobox",
          queryMode: "local",
          valueField: "id",
          displayField: "name",
          store: {
            fields: ["id", "name"],
            data: [
              { id: "bsl1", name: "BSL1" },
              { id: "bsl2", name: "BSL2" }
            ]
          },
          forceSelection: true
        },
        renderer: this.comboboxErrorRenderer
      },
      {
        text: "Comment Input",
        dataIndex: "comments",
        tooltip: "Comments",
        width: 200,
        editor: {
          xtype: "textfield",
          allowBlank: true
        }
      }
    ]);

    // Sorting the columns
    var order = [
      "numberer",
      "name",
      "barcode",
      "comments",
      "measuring_unit",
      "measured_value",
      "volume",
      "library_protocol",
      "library_type",
      "nucleic_acid_type",
      "read_length",
      "sequencing_depth",
      "organism",
      "biosafety_level",
      "gmo"
    ];
    columns = this.sortColumns(columns, order);

    return [store, columns];
  },

  sortColumns: function (columns, order) {
    var orderMap = {};
    _.each(order, function (i) {
      orderMap[i] = _.indexOf(order, i);
    });

    return _.sortBy(columns, function (column) {
      return orderMap[column.dataIndex];
    });
  },

  getCommonColumns: function (mode) {
    var columns = [
      {
        xtype: "rownumberer",
        dataIndex: "numberer",
        width: 40
      },
      {
        text: "Name",
        dataIndex: "name",
        tooltip: "Name",
        minWidth: 200,
        flex: 1,
        editor: {
          xtype: "textfield",
          regex: new RegExp(/^[A-Za-z0-9_-]+$/),
          regexText: "Only A-Za-z0-9 as well as _ and - are allowed"
        },
        renderer: this.errorRenderer
      },
      {
        text: "Protocol",
        dataIndex: "library_protocol",
        tooltip: "Library Preparation Protocol",
        width: 200,
        editor: {
          xtype: "combobox",
          id: "libraryProtocolEditor",
          itemId: "libraryProtocolEditor",
          queryMode: "local",
          displayField: "name",
          valueField: "id",
          store: "libraryProtocolsStore",
          matchFieldWidth: false,
          forceSelection: true,
          listConfig: {
            getInnerTpl: function () {
              return (
                '<span data-qtip="' +
                "<strong>Provider</strong>: {provider}<br/>" +
                "<strong>Catalog</strong>: {catalog}<br/>" +
                "<strong>Explanation</strong>: {explanation}<br/>" +
                "<strong>Input Requirements</strong>: {inputRequirements}<br/>" +
                "<strong>Typical Application</strong>: {typicalApplication}<br/>" +
                "<strong>Comments</strong>: {comments}" +
                '">{name}</span>'
              );
            }
          }
        },
        renderer: this.comboboxErrorRenderer
      },
      {
        text: "Analysis Type",
        dataIndex: "library_type",
        tooltip: "Analysis Type",
        width: 200,
        editor: {
          xtype: "combobox",
          id: "libraryTypeEditor",
          itemId: "libraryTypeEditor",
          queryMode: "local",
          displayField: "name",
          valueField: "id",
          store: "libraryTypesStore",
          forceSelection: true
        },
        renderer: this.comboboxErrorRenderer
      },
      {
        text: "Volume (µl)",
        dataIndex: "volume",
        tooltip: "Volume",
        width: 90,
        editor: {
          xtype: "numberfield",
          minValue: 0,
          step: 10
        },
        renderer: this.errorRenderer
      },
      {
        text: "Read Length",
        dataIndex: "read_length",
        tooltip: "Read Length",
        width: 100,
        editor: {
          xtype: "combobox",
          queryMode: "local",
          valueField: "id",
          displayField: "name",
          store: "readLengthsStore",
          matchFieldWidth: false,
          forceSelection: true
        },
        renderer: this.comboboxErrorRenderer
      },
      {
        text: "Depth (M)",
        dataIndex: "sequencing_depth",
        tooltip: "Sequencing Depth",
        width: 90,
        editor: {
          xtype: "numberfield",
          minValue: 0,
          step: 10
        },
        renderer: this.errorRenderer
      },
      {
        text: "Organism",
        dataIndex: "organism",
        tooltip: "Organism",
        width: 120,
        editor: {
          xtype: "combobox",
          queryMode: "local",
          valueField: "id",
          displayField: "name",
          store: "organismsStore",
          forceSelection: true,
          listConfig: {
            minWidth: 200
          }
        },
        renderer: this.comboboxErrorRenderer
      }
    ];

    if (mode === "edit") {
      columns.push({
        text: "Barcode",
        dataIndex: "barcode",
        width: 95
      });
    }

    return columns;
  },

  autoSaveRequest: function () {
    var form = Ext.getCmp("request-form");
    var requestWnd = form.up("window");
    var store = Ext.getStore("librariesInRequestStore");
    var url;

    if (requestWnd.mode === "add") {
      url = "api/requests/";
    } else {
      url = Ext.String.format(
        "api/requests/{0}/edit/",
        requestWnd.record.get("pk")
      );
    }

    if (store.getCount() === 0) {
      new Noty({
        text: "No libraries/samples are added to the request.",
        type: "warning"
      }).show();
      return;
    }

    var data = form.getForm().getFieldValues();

    Ext.Ajax.request({
      url: url,
      method: "POST",
      scope: this,

      params: {
        data: Ext.JSON.encode({
          name: data.name,
          pi: data.pi,
          cost_unit: data.cost_unit,
          records: Ext.Array.pluck(store.data.items, "data"),
          files: form.down("filegridfield").getValue()
        })
      },

      success: function (response) {
        var obj = Ext.JSON.decode(response.responseText);

        if (obj.success) {
          var message;

          if (requestWnd.mode === "add") {
            message = "The request has been auto-saved.";
            requestWnd.mode = "edit";
            requestWnd.autoSaveRequestId = obj.pk;
            requestWnd.setTitle(this.requestName);
          } else {
            message = "The request has been saved successfully.";
          }

          new Noty({ text: message }).show();
          Ext.getStore("requestsStore").reload();
        } else {
          new Noty({ text: obj.message, type: "error" }).show();
          console.error(response);
        }
      },

      failure: function (response) {
        new Noty({ text: response.statusText, type: "error" }).show();
        console.error(response);
      }
    });
  },

  save: function (btn) {
    var wnd = btn.up("window");
    var store = Ext.getCmp("batch-add-grid").getStore();
    var url = wnd.recordType === "Library" ? "api/libraries/" : "api/samples/";

    if (wnd.mode === "edit") {
      url += "edit/";
    }

    if (store.getCount() === 0) {
      return;
    }

    this.validateAll(url);

    var numInvalidRecords = store.data.items.reduce(function (n, item) {
      return n + (item.get("invalid") === true);
    }, 0);

    if (numInvalidRecords !== 0) {
      new Noty({
        text: "Please check the record entries.",
        type: "warning"
      }).show();
      return;
    }

    wnd.setLoading("Saving...");
    Ext.Ajax.request({
      url: url,
      method: "POST",
      scope: this,
      params: {
        data: Ext.JSON.encode(Ext.Array.pluck(store.data.items, "data"))
      },

      success: function (response) {
        var obj = Ext.JSON.decode(response.responseText);

        if (obj.success) {
          var librariesInRequestGrid = Ext.getCmp("libraries-in-request-grid");
          if (wnd.mode === "add") {
            librariesInRequestGrid.getStore().add(obj.data);

            for (var i = 0; i < obj.data.length; i++) {
              var record = store.findRecord("name", obj.data[i].name);
              store.remove(record);
            }

            new Noty({ text: "Records have been added successfully." }).show();
            // If new libraries/samples are added, try to automatically save the request,
            // otherwise, if the request is not saved, such libraries/samples
            // are 'lost', or at least they don't have a request associated to them
            this.autoSaveRequest();
          } else {
            librariesInRequestGrid
              .down("#check-column")
              .fireEvent("unselectall");
            new Noty({ text: "Changes have been saved successfully." }).show();
          }
          wnd.close();
        } else {
          new Noty({ text: obj.message, type: "error" }).show();
        }

        wnd.setLoading(false);
      },

      failure: function (response) {
        wnd.setLoading(false);
        new Noty({ text: response.statusText, type: "error" }).show();
        console.error(response);
      }
    });
  },

  validateAll: function (url) {
    var me = this;
    var grid = Ext.getCmp("batch-add-grid");
    var store = grid.getStore();

    store.each(function (record) {
      me.validateRecord(record, url);
    });

    grid.getView().refresh();
  },

  validateRecord: function (record, url) {
    var grid = Ext.getCmp("batch-add-grid");
    var store = grid.getStore();
    var validation = record.getValidation(true).data;
    var invalid = false;
    var errors = {};

    for (var dataIndex in validation) {
      if (validation.hasOwnProperty(dataIndex)) {
        if (validation[dataIndex] !== true) {
          invalid = true;
          errors[dataIndex] = validation[dataIndex];
        }
      }
    }

    store.suspendEvents();
    record.set({ invalid: invalid, errors: errors });
    store.resumeEvents();

    return errors;
  },

  errorRenderer: function (value, meta, record) {
    var dataIndex = meta.column.dataIndex;
    var errors = record.get("errors");

    if (Object.keys(errors).indexOf(dataIndex) !== -1) {
      meta.tdCls += " invalid-record";
      meta.tdAttr = 'data-qtip="' + errors[dataIndex] + '"';
    }

    // Render indices as '{Index ID} - {Index}'
    if (
      (dataIndex === "index_i7" || dataIndex === "index_i5") &&
      value !== ""
    ) {
      var store = meta.column.getEditor().getStore();
      var index = store.findRecord("index", value);
      if (index) {
        value = index.get("name");
      }
    }

    if (dataIndex === "measured_value" && value === -1) {
      return "";
    }

    return value;
  },

  comboboxErrorRenderer: function (value, meta, record) {
    var dataIndex = meta.column.dataIndex;
    var store = meta.column.getEditor().getStore();

    if (record && Object.keys(record.get("errors")).indexOf(dataIndex) !== -1) {
      meta.tdCls += " invalid-record";
      meta.tdAttr = 'data-qtip="' + record.get("errors")[dataIndex] + '"';
    }

    if (dataIndex === "gmo") {
      var item = store.findRecord("value", value, 0, false, false, true);
      return item ? item.get("name") : "";
    }

    store.clearFilter();

    var item = store.findRecord("id", value, 0, false, false, true);
    return item ? item.get("name") : "";
  },

  createEmptyRecords: function (btn) {
    var grid = Ext.getCmp("batch-add-grid");
    var store = grid.getStore();
    var numRecords = btn.up().down("#num-empty-records").getValue();

    if (numRecords && numRecords > 0) {
      var data = [];
      for (var i = 0; i < numRecords; i++) {
        data.push({});
      }
      store.add(data);
    }
  },

  delete: function (record, gridView) {
    var store = record.store;
    store.remove(record);
    gridView.refresh();
  }
});

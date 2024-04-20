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

      // Libraries only
      "#indexTypeEditor": {
        select: "selectIndexType"
      },
      "#indexReadsEditor": {
        select: "selectIndexReads",
      },
      "#indexI7Editor": {
        beforequery: "filterIndexStoreChoices",
        select: "selectMatchingIndexInPair",
      },
      "#indexI5Editor": {
        beforequery: "filterIndexStoreChoices",
        select: "selectMatchingIndexInPair",
      },

      // Samples only
      "#nucleicAcidTypeEditor": {
        select: "selectNucleicAcidType"
      },
      "#libraryTypeEditor": {
        select: "selectLibraryType",
      },

      "#save-button": {
        click: "save"
      },

      // '#download-sample-form':{
      //   click: 'downloadSampleForm'
      // }

      "#reorder-columns": {
        click: "reorderColumns",
      },
    },
  },

  loadedIndexTypeIds: [],
  viewRefreshCounter: 0,

  boxready: function (wnd) {
    var me = this;

    // Bypass Selection (Library/Sample) dialog if editing
    if (wnd.mode === "edit") {
      if (wnd.type === "Library") {
        wnd.down("#library-card-button").click();
      } else {
        wnd.down("#sample-card-button").click();
      }
    } else {
      // When adding new records, check if at least one has already been added
      // and force addition of same
      var librariesInRequestStore = Ext.getStore("librariesInRequestStore");
      var records = librariesInRequestStore.getRange();
      if (librariesInRequestStore.data.length) {
        if (
          records.every(function (e) {
            return e.data.record_type === "Library";
          })
        ) {
          wnd.down("#library-card-button").click();
        } else {
          wnd.down("#sample-card-button").click();
        }
      }
    }

    var indexI7Store = Ext.getStore("indexI7Store");
    var indexI5Store = Ext.getStore("indexI5Store");

    // Check if indices are already present in the index stores
    // if so, add them to loadedIndexTypeIds
    [indexI7Store, indexI5Store].forEach(function (s) {
      s.clearFilter(true);
      var indexTypeIds = Array.from(
        new Set(
          Ext.pluck(Ext.pluck(s.getRange(), "data"), "index_type").filter(
            function (e) {
              return e;
            }
          )
        )
      );
      indexTypeIds.forEach(function (e) {
        me.loadedIndexTypeIds.indexOf(e) === -1 &&
          me.loadedIndexTypeIds.push(e);
      });
    });

    // If an index store is empty add one bogus entry. Without at least one entry in the
    // store, an index sequence is not shown when activating a row, even though
    // it is rendered correctly in the unactivated row. Maybe there is a better solution,
    // but for now it works.
    [Ext.getStore("indexI7Store"), Ext.getStore("indexI5Store")].forEach(function (s) {
      if (!Ext.isEmpty(s)) {
        s.add(new s.model())
      }
    })

    var records = wnd.down("grid").getStore().getRange();
    if (records.length > 0) {
      // If not already present, add indices and index pairs
      // for index types in the grid
      var indexTypeIds = Array.from(
        new Set(
          Ext.pluck(Ext.pluck(records, "data"), "index_type").filter(function (
            e
          ) {
            return e;
          })
        )
      );
      var missingIndexTypeIds = indexTypeIds.filter(function (e) {
        return !me.loadedIndexTypeIds.includes(e);
      });
      if (missingIndexTypeIds.length > 0) {
        me.loadedIndexTypeIds =
          me.loadedIndexTypeIds.concat(missingIndexTypeIds);
        me._addToIndexStore(indexI7Store, missingIndexTypeIds, true, me);
        me._addToIndexStore(indexI5Store, missingIndexTypeIds, true, me);
        me._addToIndexPairStore(missingIndexTypeIds, null, null);
      }
    }

    Ext.apply(Ext.tip.QuickTipManager.getQuickTip(), {
      dismissDelay: 10000 // hide after 10 seconds
    });
  },

  selectCard: function (btn) {
    var me = this;
    var wnd = btn.up("window");
    wnd.allowClose = false;
    var layout = btn.up("panel").getLayout();
    var configuration;
    this.requestName = Ext.getCmp("request-form")
      .getForm()
      .getFieldValues().name;

    wnd.setSize(1000, 650);
    wnd.center();
    wnd.getDockedItems('toolbar[dock="bottom"]')[0].show();
    if (wnd.mode === "add") {
      wnd.getDockedItems('toolbar[dock="top"]')[0].show();
    } else {
      // wnd.down('#cancel-button').show();
    }
    layout.setActiveItem(1);

    if (btn.itemId === "library-card-button") {
      wnd.recordType = "Library";
      wnd.setTitle(this.requestName + " - " + "Add Libraries");
      // wnd.getComponent('create-empty-records').getComponent('download-sample-form').setVisible(false);
      configuration = this.getLibraryGridConfiguration(wnd.mode);
    } else {
      wnd.recordType = "Sample";
      wnd.setTitle(this.requestName + " - " + "Add Samples");
      // wnd.getComponent('create-empty-records').getComponent('download-sample-form').setVisible(true);
      configuration = this.getSampleGridConfiguration(wnd.mode);
    }

    // Add selected records for editing to the store
    if (wnd.mode === "edit") {
      configuration[0].add(wnd.records);
      // Change the title of the Batch Window to Edit if editing
      wnd.setTitle(wnd.title.replace("Add", "Edit"));
    }

    wnd.maximize(); // auto fullscreen

    var grid = Ext.getCmp("batch-add-grid");
    grid.reconfigure(configuration[0], configuration[1]);

    // Load stores
    // Ext.getStore('libraryProtocolsStore').reload();
    // Ext.getStore('libraryTypesStore').reload();

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

  reorderColumns: function (btn) {
    var wnd = btn.up("window");
    var grid = Ext.getCmp("batch-add-grid");
    var columns = grid.headerCt.columnManager.getColumns();
    var columnOrderCurrent = columns.map(function (e) {
      return e.dataIndex;
    });

    // Check if columOrderOriginal exists and, if not, set it
    if (typeof this.columOrderOriginal === "undefined") {
      this.columOrderOriginal = null;
    }
    this.columOrderOriginal = this.columOrderOriginal
      ? this.columOrderOriginal
      : columns.map(function (e) {
        return e.dataIndex;
      });

    var newColumnOrder;

    if (wnd.recordType === "Library") {
      // Column order for library
      newColumnOrder = [
        "numberer",
        "barcode",
        "name",
        "source",
        "sample_volume_user",
        "concentration",
        "mean_fragment_size",
        "sequencing_depth",
        "amplification_cycles",
        "qpcr_result",
        "comments",
        "organism",
        "library_type",
        "library_protocol",
        "index_type",
        "index_reads",
        "index_i7",
        "index_i5",
        "read_length",
        "concentration_method",
      ];
    } else {
      // Column order for sample

      // Get all items to decide how to reorder columns
      var itemList = grid.store.data.items;

      // Check if all records are Single cell
      var natTypeIds = itemList.map(function (e) {
        return e.get("nucleic_acid_type");
      });
      var natStore = Ext.getStore("nucleicAcidTypesStore");
      var singleCell = natTypeIds.every(function (i) {
        var v = i ? natStore.findRecord("id", i).get("single_cell") : false;
        return v;
      });

      // Rearrange columns based on experiment type

      if (singleCell) {
        newColumnOrder = [
          "numberer",
          "barcode",
          "name",
          "source",
          "sample_volume_user",
          "cell_density",
          "cell_viability",
          "starting_number_cells",
          "number_targeted_cells",
          "sequencing_depth",
          "amplification_cycles",
          "comments",
          "organism",
          "concentration",
          "rna_quality",
          "read_length",
          "nucleic_acid_type",
          "library_type",
          "library_protocol",
          "concentration_method",
        ];
      } else {
        // Check if all records are for RNA, therefore RQN is needed
        rnaQuality = natTypeIds.every(function (i) {
          var v = i ? natStore.findRecord("id", i).get("type") == "RNA" : false;
          return v;
        });

        if (rnaQuality) {
          newColumnOrder = [
            "numberer",
            "barcode",
            "name",
            "source",
            "sample_volume_user",
            "concentration",
            "rna_quality",
            "sequencing_depth",
            "amplification_cycles",
            "comments",
            "organism",
            "cell_density",
            "cell_viability",
            "starting_number_cells",
            "number_targeted_cells",
            "read_length",
            "nucleic_acid_type",
            "library_type",
            "library_protocol",
            "concentration_method",
          ];
        } else {
          newColumnOrder = [
            "numberer",
            "barcode",
            "name",
            "source",
            "sample_volume_user",
            "concentration",
            "sequencing_depth",
            "amplification_cycles",
            "comments",
            "organism",
            "cell_density",
            "cell_viability",
            "starting_number_cells",
            "number_targeted_cells",
            "rna_quality",
            "read_length",
            "nucleic_acid_type",
            "library_type",
            "library_protocol",
            "concentration_method",
          ];
        }
      }
    }

    var isCommentsColumLast = columnOrderCurrent.at(-1) === "comments";
    newColumnOrder = isCommentsColumLast
      ? newColumnOrder
      : this.columOrderOriginal;

    // Sort columns as desired
    columns = this.sortColumns(columns, newColumnOrder);
    newColumnOrder = columns.map(function (e) {
      return e.dataIndex;
    });

    // Reorder columns
    grid.headerCt.suspendLayouts();
    for (var i = 0; i < columns.length; i++) {
      grid.headerCt.moveAfter(columns[i], columns[i - 1] || null);
    }
    grid.headerCt.resumeLayouts(true);

    // Add some formatting to highlight which multiple columns can be pasted in one go
    var limitLeftPastable = isCommentsColumLast
      ? newColumnOrder.indexOf("name")
      : 0;
    var limitRightPastable = isCommentsColumLast
      ? newColumnOrder.indexOf("comments") + 1
      : -1;

    if (limitRightPastable > 1) {
      grid.headerCt.columnManager
        .getColumns()
        .slice(limitLeftPastable, limitRightPastable)
        .forEach(function (e) {
          e.addCls("highlight-header-text-blue");
        });
      btn.addCls("highlight-shuffle-icon-blue");
    } else {
      grid.headerCt.columnManager.getColumns().forEach(function (e) {
        e.removeCls("highlight-header-text-blue");
      });
      btn.removeCls("highlight-shuffle-icon-blue");
    }

    grid.getView().refresh();
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

          // Update Nucleic Acid Type
          else if (dataIndex === "nucleic_acid_type") {
            // Reset Library Protocol and Library Type for records
            // with a different Nucleic Acid Type
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

          // If Library Type was selected, update Nuc. Type too
          else if (dataIndex === "library_type") {
            // Libraries
            if (typeof item.get("nucleic_acid_type") === "undefined") {
              // Reset Library Protocol for records with a different Library Type
              if (item.get("library_type") !== record.get("library_type")) {
                item.set("library_protocol", null);
              }
            }

            // Samples
            else {
              // Reset Library Protocol if Nucleic Acid Types Library Types
              // are different
              if (
                item.get("nucleic_acid_type") !==
                record.get("nucleic_acid_type") ||
                (item.get("nucleic_acid_type") ===
                  record.get("nucleic_acid_type") &&
                  item.get("library_type") !== record.get("library_type"))
              ) {
                item.set("library_protocol", null);
              }
              item.set("nucleic_acid_type", record.get("nucleic_acid_type"));
            }

            item.set("library_type", record.get("library_type"));
          }

          // If Library Protocol was selected, update Library Type and Nucleic Acid Type
          else if (dataIndex === "library_protocol") {
            item.set({
              library_protocol: record.get("library_protocol"),
              library_type: record.get("library_type"),
              nucleic_acid_type: record.get("nucleic_acid_type"),
            });
          }

          // RNA Quality should be applied only when Nucleic Acid Type is RNA
          else if (dataIndex === "rna_quality") {
            var nat = Ext.getStore("nucleicAcidTypesStore").findRecord(
              "id",
              item.get("nucleic_acid_type")
            );

            if (nat && nat.get("type") === "RNA") {
              item.set(dataIndex, record.get(dataIndex));
            }
          } else {
            item.set(dataIndex, record.get(dataIndex));
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
    var libraryTypeEditor = Ext.getCmp("libraryTypeEditor");
    var rnaQualityEditor = Ext.getCmp("rnaQualityEditor");
    var record = context.record;

    // Toggle Library Type
    if (record.get("library_type") === null) {
      libraryProtocolEditor.setValue(null);
      libraryProtocolEditor.disable();
    } else {
      libraryProtocolEditor.enable();

      // Filter Library Types store for currently selected Library Protocol
      this.filterLibraryTypes(record.get("nucleic_acid_type"));
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
      indexI7Editor.getStore().clearFilter(true);
      indexI5Editor.getStore().clearFilter(true);
    }

    // Samples
    else if (wnd.recordType === "Sample") {
      // Toggle Library Type
      if (record.get("nucleic_acid_type") === null) {
        libraryTypeEditor.setValue(null);
        libraryTypeEditor.disable();
      } else {
        libraryTypeEditor.enable();

        // Filter Library Types store for currently selected Nucleic Acid Type
        if (record.get("library_type") !== 0) {
          this.filterLibraryTypes(record.get("nucleic_acid_type"));
        }
      }

      var singleCell = this.toggleSingleCellFields(
        record.get("nucleic_acid_type")
      );

      // Toggle RNA Quality
      var nat = nucleicAcidTypesStore.findRecord(
        "id",
        record.get("nucleic_acid_type")
      );
      if (nat && !singleCell && nat.get("type") === "RNA") {
        rnaQualityEditor.enable();
      } else {
        rnaQualityEditor.disable();
      }
    }
  },

  toggleSingleCellFields: function (nucleicAcidType) {
    var cellDensityEditor = Ext.getCmp("cellDensityEditor"),
      cellViabilityEditor = Ext.getCmp("cellViabilityEditor"),
      startingNumberCellsEditor = Ext.getCmp("startingNumberCellsEditor"),
      numberCellsPoolingEditor = Ext.getCmp("numberCellsPoolingEditor"),
      concentrationEditor = Ext.getCmp("concentrationEditor"),
      concentrationMethodEditor = Ext.getCmp("concentrationMethodEditor");

    var nucleicAcidTypesStore = Ext.getStore("nucleicAcidTypesStore");
    var singleCell = nucleicAcidType
      ? nucleicAcidTypesStore
        .findRecord("id", nucleicAcidType)
        .get("single_cell")
      : null;

    // Toggle Single Cell fields and concentration
    // which is not necessary for this kind of project
    if (singleCell) {
      cellDensityEditor.enable();
      cellViabilityEditor.enable();
      startingNumberCellsEditor.enable();
      numberCellsPoolingEditor.enable();

      concentrationEditor.disable();
      concentrationMethodEditor.disable();
    } else {
      cellDensityEditor.disable();
      cellViabilityEditor.disable();
      startingNumberCellsEditor.disable();
      numberCellsPoolingEditor.disable();

      concentrationEditor.enable();
      concentrationMethodEditor.enable();
    }

    return singleCell;
  },

  filterIndexStoreChoices: function (queryPlan) {
    var store = queryPlan.combo.store;
    store.clearFilter(true);
    store.filter("index_type", Ext.getCmp("indexTypeEditor").getValue(), true);
    return true;
  },

  selectMatchingIndexInPair: function (cb, record) {
    // If an index pair is found, try to get the corresponding
    // i5 index and, if present, set it in the i7 index cell
    var indexReadsId = Ext.getCmp("indexReadsEditor").getValue();
    if (record && indexReadsId === 752) {
      var indexEditorId = cb.id;
      var corrIndexGenerator, indexFieldId, corrIndexFieldId;
      if (indexEditorId.startsWith("indexI7")) {
        corrIndexGenerator = Ext.getCmp("indexI5Editor");
        indexFieldId = "index1_id";
        corrIndexFieldId = "index2_id";
      } else {
        corrIndexGenerator = Ext.getCmp("indexI7Editor");
        indexFieldId = "index2_id";
        corrIndexFieldId = "index1_id";
      }
      var indexPairStore = Ext.getStore("IndexPairs");
      var indexTypeId = Ext.getCmp("indexTypeEditor").getValue();
      indexPairStore.clearFilter(true);
      indexPairStore.filter("index_type", indexTypeId, true);
      var indexPair = indexPairStore.findRecord(indexFieldId, record.id);
      if (indexPair) {
        var corrIndexStore = corrIndexGenerator.getStore();
        corrIndexStore.clearFilter(true);
        corrIndexStore.filter("index_type", indexTypeId, true);
        var coorIndex = corrIndexStore.findRecord(
          "id",
          indexPair.get(corrIndexFieldId)
        );
        if (coorIndex) {
          corrIndexGenerator.setValue(coorIndex.get("index"));
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

    // Reset Library Protocol if Library Type is empty
    if (
      record.get("library_type") === null &&
      record.get("library_protocol") !== null
    ) {
      record.set("library_protocol", null);
    }

    // Check if single cell, then set relevant fields to null accordingly
    var nucleicAcidTypesStore = Ext.getStore("nucleicAcidTypesStore");
    var singleCell = record.get("nucleic_acid_type")
      ? nucleicAcidTypesStore
        .findRecord("id", record.get("nucleic_acid_type"))
        .get("single_cell")
      : null;
    if (singleCell) {
      record.set("concentration", null);
      record.set("concentration_method", null);
    } else {
      record.set("cell_density", null);
      record.set("cell_viability", null);
      record.set("starting_number_cells", null);
      record.set("number_targeted_cells", null);
    }

    // Reset Index I7 and Index I5, as relevant
    if (record.get("index_reads") === 7) {
      record.set("index_i5", "");
    } else if (record.get("index_reads") === 5) {
      record.set("index_i7", "");
    } else if (record.get("index_reads") === 0) {
      record.set({ index_i7: "", index_i5: "" });
    }

    // Reset RNA Quality if Nucleic Acid Type has changed
    var nat = Ext.getStore("nucleicAcidTypesStore").findRecord(
      "id",
      record.get("nucleic_acid_type")
    );
    if (
      nat !== null &&
      nat.get("type") === "DNA" &&
      record.get("rna_quality") > 0
    ) {
      record.set("rna_quality", null);
    }

    record.commit();

    // Validate the record after editing and refresh the grid
    this.validateRecord(record);

    // Reset indexReadsStore, before refreshing view
    if (Ext.getCmp("indexReadsEditor")) {
      var indexReadsStore = Ext.getCmp("indexReadsEditor").getStore();
      indexReadsStore.removeAll();
      indexReadsStore.add([
        { num: 0, label: "None" },
        { num: 7, label: "I7 only" },
        { num: 5, label: "I5 only" },
        { num: 75, label: "I7 + I5" },
        { num: 752, label: "I7 + I5 (Pair/UDI)" },
      ]);
    }

    grid.getView().refresh();
  },

  selectLibraryType: function (fld, record) {
    var libraryProtocolEditor = Ext.getCmp("libraryProtocolEditor");
    var nucleicAcidTypeEditor = Ext.getCmp("nucleicAcidTypeEditor");
    libraryProtocolEditor.setValue(null);
    libraryProtocolEditor.enable();
    var libraryTypeId = record.get("id");
    var nucleicAcidTypeId = nucleicAcidTypeEditor
      ? nucleicAcidTypeEditor.getValue()
      : null;
    this.filterLibraryProtocols(libraryTypeId, nucleicAcidTypeId);
  },

  selectIndexType: function (fld, record) {
    var me = this;
    var indexReadsEditor = Ext.getCmp("indexReadsEditor");
    var indexI7Editor = Ext.getCmp("indexI7Editor");
    var indexI5Editor = Ext.getCmp("indexI5Editor");
    var indexI7Store = Ext.getStore("indexI7Store");
    var indexI5Store = Ext.getStore("indexI5Store");

    indexReadsEditor.setValue(null);
    indexReadsEditor.enable();

    var indexReadsStore = indexReadsEditor.getStore();
    indexReadsStore.removeAll();
    // All index types should have these
    indexReadsStore.add([
      { num: 0, label: "None" },
      { num: 7, label: "I7 only" },
    ]);

    // Only dual indexing
    if (record.get("index_reads") > 1) {
      indexReadsStore.add([
        { num: 5, label: "I5 only" },
        { num: 75, label: "I7 + I5" },
      ]);
    }

    // If indices and index pairs for selected Index Type
    // have not already been added to the relevant stores, do so
    // If pairs exist, add a new option for indexReadsStore
    var indexTypeId = record.get("id");

    if (me.loadedIndexTypeIds.indexOf(indexTypeId) === -1) {
      me.loadedIndexTypeIds.push(indexTypeId);
      me._addToIndexStore(indexI7Store, [indexTypeId], false, me);
      me._addToIndexStore(indexI5Store, [indexTypeId], false, me);
      me._addToIndexPairStore([indexTypeId], indexReadsStore);
    } else {
      var indexPairStore = Ext.getStore("IndexPairs");
      indexPairStore.clearFilter(true);
      indexPairStore.filter("index_type", indexTypeId, true);
      if (indexPairStore.getCount() > 0) {
        indexReadsStore.add({ num: 752, label: "I7 + I5 (Pair/UDI)" });
      }
    }

    // Remove values before loading new stores
    indexI7Editor.setValue(null);
    indexI5Editor.setValue(null);
    indexI7Editor.disable();
    indexI5Editor.disable();
  },

  selectIndexReads: function (fld, record) {
    var indexI7Editor = Ext.getCmp("indexI7Editor");
    var indexI5Editor = Ext.getCmp("indexI5Editor");

    if (record) {
      if (record.get("num") === 7) {
        indexI7Editor.enable();
        indexI5Editor.disable();
        indexI5Editor.setValue(null);
      } else if (record.get("num") === 5) {
        indexI5Editor.enable();
        indexI7Editor.disable();
        indexI7Editor.setValue(null);
      } else if (record.get("num") === 75) {
        indexI7Editor.enable();
        indexI5Editor.enable();
      } else if (record.get("num") === 752) {
        indexI7Editor.enable();
        indexI5Editor.enable();
        indexI7Editor.setValue(null);
        indexI5Editor.setValue(null);
      } else {
        indexI7Editor.setValue(null);
        indexI5Editor.setValue(null);
        indexI7Editor.disable();
        indexI5Editor.disable();
      }
    } else {
      var indexReadsEditor = Ext.getCmp("indexReadsEditorIndexGenerator");
      indexReadsEditor.fireEvent(
        "select",
        indexReadsEditor,
        indexReadsEditor.findRecordByValue(0)
      );
      indexI7Editor.setValue(null);
      indexI5Editor.setValue(null);
      indexI7Editor.disable();
      indexI5Editor.disable();
    }
  },

  selectNucleicAcidType: function (fld, record) {
    var libraryProtocolEditor = Ext.getCmp("libraryProtocolEditor");
    var libraryTypeEditor = Ext.getCmp("libraryTypeEditor");
    var rnaQualityEditor = Ext.getCmp("rnaQualityEditor");

    var nucleicAcidTypeId = record.get("id");
    this.filterLibraryTypes(nucleicAcidTypeId);
    libraryTypeEditor.setValue(null);
    libraryTypeEditor.enable();

    libraryProtocolEditor.setValue(null);

    // Toggle Single Cell fields
    var singleCell = this.toggleSingleCellFields(record.get("id"));

    // Toggle RQN
    if (!singleCell && record.get("type") === "RNA") {
      rnaQualityEditor.enable();
    } else {
      rnaQualityEditor.setValue(null);
      rnaQualityEditor.disable();
    }
  },

  filterLibraryProtocols: function (libraryTypeId, nucleicAcidTypeId) {
    var store = Ext.getStore("libraryProtocolsStore");
    store.clearFilter();

    // Filter by library type
    store.filterBy(function (item) {
      return item.get("library_type").indexOf(libraryTypeId) !== -1;
    });

    // Filter by nucleic acid type
    if (nucleicAcidTypeId) {
      store.filterBy(function (item) {
        return item.get("nucleic_acid_types").indexOf(nucleicAcidTypeId) !== -1;
      });
    }
  },

  filterLibraryTypes: function (nucleicAcidTypeId) {
    var store = Ext.getStore("libraryTypesStore");
    store.clearFilter();

    // Filter by nucleic acid
    if (nucleicAcidTypeId) {
      store.filterBy(function (item) {
        return item.get("nucleic_acid_type").indexOf(nucleicAcidTypeId) !== -1;
      });
    }
  },

  getLibraryGridConfiguration: function (mode) {
    var store = Ext.create("Ext.data.Store", {
      model: "MainHub.model.libraries.BatchAdd.Library",
      data: [],
      sorters: [
        {
          property: "barcode",
          direction: "ASC",
        },
      ],
    });

    var columns = Ext.Array.merge(this.getCommonColumns(mode), [
      {
        text: "size (bp)",
        dataIndex: "mean_fragment_size",
        tooltip: "Mean Fragment Size",
        width: 100,
        editor: {
          xtype: "numberfield",
          allowDecimals: false,
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
        tooltip: "Index Type",
        width: 130,
        editor: {
          xtype: "combobox",
          id: "indexReadsEditor",
          itemId: "indexReadsEditor",
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

          return item ? item.get("label") : value;
        },
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
            "Only A, T, C and G (uppercase) are allowed. Index length must be 6, 8, 10, 12 or 24.",
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
            "Only A, T, C and G (uppercase) are allowed. Index length must be 6, 8, 10, 12 or 24.",
          matchFieldWidth: false
        },
        renderer: this.errorRenderer,
      },
      {
        text: "qPCR (nM)",
        dataIndex: "qpcr_result",
        tooltip: "Concentration determined by qPCR (nM)",
        width: 85,
        editor: {
          xtype: "numberfield",
          decimalPrecision: 2,
          allowBlank: true,
          minValue: 0,
        },
      },
    ]);

    // Sort columns
    var order = [
      "numberer",
      "barcode",
      "name",
      "organism",
      "source",
      "library_type",
      "library_protocol",
      "sample_volume_user",
      "concentration",
      "mean_fragment_size",
      "index_type",
      "index_reads",
      "index_i7",
      "index_i5",
      "read_length",
      "sequencing_depth",
      "amplification_cycles",
      "qpcr_result",
      "concentration_method",
      "comments",
    ];
    columns = this.sortColumns(columns, order);

    return [store, columns];
  },

  getSampleGridConfiguration: function (mode) {
    var store = Ext.create("Ext.data.Store", {
      model: "MainHub.model.libraries.BatchAdd.Sample",
      data: [],
      sorters: [
        {
          property: "barcode",
          direction: "ASC",
        },
      ],
    });

    var columns = Ext.Array.merge(this.getCommonColumns(mode), [
      {
        text: "Submitted material",
        dataIndex: "nucleic_acid_type",
        tooltip:
          "Submitted sample material<br><br>Type <i>DNA</i>, <i>RNA</i> " +
          "or <i>Sin[gle cell]</i>, and select from choices.",
        width: 200,
        editor: {
          xtype: "combobox",
          id: "nucleicAcidTypeEditor",
          itemId: "nucleicAcidTypeEditor",
          emptyText: "DNA / RNA / Single Cell",
          queryMode: "local",
          displayField: "type",
          valueField: "id",
          store: "nucleicAcidTypesStore",
          matchFieldWidth: false,
          forceSelection: true,
          minChars: 3,
          hideTrigger: true,
          displayTpl: Ext.create("Ext.XTemplate", '<tpl for=".">{name}</tpl>'),
          listConfig: {
            getInnerTpl: function () {
              return "{name}";
            },
          },
          listeners: {
            beforequery: function (queryEvent) {
              // Set query text on the Editor object, so that it's accessible
              // to the expand listener
              this.searchQuery = queryEvent.query;
              return true;
            },
            expand: function (combo) {
              // Hide choice dropdown if search query is shorter than 3 chars
              if (!this.searchQuery || this.searchQuery.length < 3) {
                var element = combo.getPicker().el;
                combo.mouseLeaveMonitor = element.monitorMouseLeave(
                  0,
                  combo.collapse(),
                  combo
                );
              }
            },
          },
        },
        renderer: this.comboboxErrorRenderer
      },
      {
        text: "RQN",
        dataIndex: "rna_quality",
        tooltip: "RNA Quality",
        width: 80,
        editor: {
          xtype: "combobox",
          id: "rnaQualityEditor",
          queryMode: "local",
          valueField: "value",
          displayField: "name",
          displayTpl: Ext.create("Ext.XTemplate", '<tpl for=".">{value}</tpl>'),
          store: "rnaQualityStore",
          regex: new RegExp("^(11|10|[1-9]?(.[0-9]+)?|.[0-9]+)$"),
          regexText: "Only values between 1 and 10 are allowed."
        },
        renderer: this.errorRenderer,
      },
      {
        text: "µl",
        dataIndex: "sample_volume_user",
        tooltip: "Volume of submitted sample",
        width: 80,
        editor: {
          xtype: "numberfield",
          minValue: 0,
        },
        renderer: this.errorRenderer,
      },
      {
        text: "Cells/µl",
        dataIndex: "cell_density",
        tooltip: "Cell density",
        width: 70,
        editor: {
          xtype: "numberfield",
          id: "cellDensityEditor",
          minValue: 0,
        },
        renderer: this.errorRenderer,
      },
      {
        text: "% Viability",
        dataIndex: "cell_viability",
        tooltip: "% cell viability",
        width: 90,
        editor: {
          xtype: "numberfield",
          id: "cellViabilityEditor",
          minValue: 0,
          maxValue: 100,
        },
        renderer: this.errorRenderer,
      },
      {
        text: "Starting # Cells",
        dataIndex: "starting_number_cells",
        width: 115,
        editor: {
          xtype: "numberfield",
          id: "startingNumberCellsEditor",
          minValue: 0,
        },
        renderer: this.errorRenderer,
      },
      {
        text: "# Targeted Cells",
        dataIndex: "number_targeted_cells",
        tooltip: "Target number of cells per sample",
        regexText: "Only integers are allowed.",
        width: 125,
        editor: {
          xtype: "numberfield",
          id: "numberCellsPoolingEditor",
          minValue: 0,
        },
        renderer: this.errorRenderer,
      },
    ]);

    // Sort columns
    var order = [
      "numberer",
      "barcode",
      "name",
      "organism",
      "source",
      "nucleic_acid_type",
      "library_type",
      "library_protocol",
      "sample_volume_user",
      "concentration",
      "rna_quality",
      "cell_density",
      "cell_viability",
      "starting_number_cells",
      "number_targeted_cells",
      "read_length",
      "sequencing_depth",
      "amplification_cycles",
      "concentration_method",
      "comments",
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
          regex: new RegExp(/^[A-Za-z0-9_]+(?<![rR][1-4])$/),
          regexText:
            "Only A-Z a-z 0-9 and _ are allowed. " +
            "Any trailing combination of [rR][1-4], <i>e.g.</i> " +
            "r1, R2, <i>etc.</i> is NOT allowed",
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
        text: "Library Type",
        dataIndex: "library_type",
        tooltip: "Library Type",
        width: 200,
        editor: {
          xtype: "combobox",
          id: "libraryTypeEditor",
          itemId: "libraryTypeEditor",
          queryMode: "local",
          displayField: "name",
          valueField: "id",
          store: "libraryTypesStore",
          // matchFieldWidth: false,
          forceSelection: true
        },
        renderer: this.comboboxErrorRenderer
      },
      {
        text: "ng/μl",
        dataIndex: "concentration",
        tooltip: "Concentration",
        width: 90,
        editor: {
          xtype: "numberfield",
          id: "concentrationEditor",
          minValue: 0,
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
        width: 85,
        editor: {
          xtype: "numberfield",
          minValue: 0,
        },
        renderer: this.errorRenderer,
      },
      {
        text: "Amplification",
        tooltip: "Amplification cycles",
        dataIndex: "amplification_cycles",
        width: 105,
        editor: {
          xtype: "numberfield",
          minValue: 0,
          allowDecimals: false,
          allowBlank: true,
        },
        renderer: this.errorRenderer
      },
      // {
      //   xtype: 'checkcolumn',
      //   text: 'Equal nucl.',
      //   tooltip: 'Equal Representation of Nucleotides: check = Yes, no check = No',
      //   dataIndex: 'equal_representation_nucleotides',
      //   width: 95,
      //   editor: {
      //     xtype: 'checkbox',
      //     cls: 'x-grid-checkheader-editor'
      //   }
      // },
      {
        text: "F/S",
        dataIndex: "concentration_method",
        tooltip: "Concentration Determined by",
        width: 80,
        editor: {
          xtype: "combobox",
          queryMode: "local",
          id: "concentrationMethodEditor",
          itemId: "concentrationMethodEditor",
          valueField: "id",
          displayField: "name",
          store: "concentrationMethodsStore",
          matchFieldWidth: false,
          forceSelection: true,
        },
        renderer: this.comboboxErrorRenderer,
      },
      {
        text: "Organism",
        dataIndex: "organism",
        tooltip: "Organism",
        width: 200,
        editor: {
          xtype: "combobox",
          queryMode: "local",
          valueField: "id",
          displayField: "name",
          store: "organismsStore",
          // matchFieldWidth: false,
          forceSelection: true,
          listConfig: {
            getInnerTpl: function () {
              return (
                '<span data-qtip="' +
                "<strong>Scientific name</strong>: {scientific_name}<br/>" +
                "<strong>Taxon ID</strong>: {taxon_id}<br/>" +
                '">{name}</span>'
              );
            },
          },
        },
        renderer: this.comboboxErrorRenderer,
      },
      {
        text: "Source",
        dataIndex: "source",
        tooltip: "Cell line, cell type, tissue, etc.",
        width: 100,
        editor: {
          xtype: "textfield",
        },
        renderer: this.errorRenderer,
      },
      {
        text: "Comments",
        dataIndex: "comments",
        tooltip: "Comments",
        width: 200,
        editor: {
          xtype: "textfield",
          allowBlank: true
        }
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
    var handlerCb = requestWnd.down("#handler-cb");
    var invoiceDateBox = requestWnd.down("#invoice-date");
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
          bioinformatician: data.bioinformatician
            ? data.bioinformatician
            : null,
          handler: handlerCb.value ? handlerCb.value : null,
          invoice_date: invoiceDateBox.value
            ? new Date(
              invoiceDateBox.value.setTime(
                invoiceDateBox.value.getTime() -
                invoiceDateBox.value.getTimezoneOffset() * 60000
              )
            )
            : null,
          pool_size_user: data.pool_size_user ? data.pool_size_user : null,
          description: data.description,
          pooled_libraries: data.pooled_libraries,
          pooled_libraries_concentration_user:
            data.pooled_libraries_concentration_user,
          pooled_libraries_volume_user: data.pooled_libraries_volume_user,
          pooled_libraries_fragment_size_user:
            data.pooled_libraries_fragment_size_user,
          records: Ext.Array.pluck(store.data.items, "data"),
          files: form.down("requestfilegridfield").getValue(),
        }),
      },

      success: function (response) {
        var obj = Ext.JSON.decode(response.responseText);

        if (obj.success) {
          var message;

          if (requestWnd.mode === "add") {
            message = "Request has been saved.";
            requestWnd.mode = "edit";
            requestWnd.autoSaveRequestId = obj.pk;
            requestWnd.setTitle(this.requestName);
          } else {
            message = "The changes have been saved.";
          }

          new Noty({ text: message }).show();
          Ext.getStore("requestsStore").reload();
        } else {
          new Noty({ text: obj.message, type: "error" }).show();
          console.error(response);
        }
      },

      failure: function (response) {
        var responseText = response.responseText
          ? Ext.JSON.decode(response.responseText)
          : null;
        responseText = responseText.message
          ? responseText.message
          : "Unknown error.";
        responseText = response.statusText ? response.statusText : responseText;
        new Noty({ text: responseText, type: "error" }).show();
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
      new Noty({ text: "Check the records.", type: "warning" }).show();
      return;
    }

    wnd.setLoading("Saving...");
    Ext.Ajax.request({
      url: url,
      method: "POST",
      // timeout: 1000000,
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
            if (librariesInRequestGrid.getStore().getCount() > 0) {
              librariesInRequestGrid.getColumns()[0].show();
            }

            for (var i = 0; i < obj.data.length; i++) {
              var record = store.findRecord("name", obj.data[i].name);
              store.remove(record);
            }

            new Noty({ text: "Records have been added!" }).show();
            // If new libraries/samples are added, try to automatically save the request,
            // otherwise, if the request is not saved, such libraries/samples
            // are 'lost', or at least they don't have a request associated to them
            this.autoSaveRequest();
          } else {
            librariesInRequestGrid
              .down("#check-column")
              .fireEvent("unselectall");
            new Noty({ text: "The changes have been saved!" }).show();
          }
          wnd.allowClose = true;
          wnd.close();
        } else {
          new Noty({ text: obj.message, type: "error" }).show();
        }

        wnd.setLoading(false);
      },

      failure: function (response) {
        wnd.setLoading(false);
        var responseText = response.responseText
          ? Ext.JSON.decode(response.responseText)
          : null;
        responseText = responseText.message
          ? responseText.message
          : "Unknown error.";
        responseText = response.statusText ? response.statusText : responseText;
        new Noty({ text: responseText, type: "error" }).show();
        console.error(response);
      }
    });
  },

  validateAll: function (url) {
    var me = this;
    var grid = Ext.getCmp("batch-add-grid");
    var store = grid.getStore();

    // Validate all records
    store.each(function (record) {
      me.validateRecord(record, url);
    });

    // Refresh the grid
    grid.getView().refresh();
  },

  validateRecord: function (record, url) {
    var grid = Ext.getCmp("batch-add-grid");
    var store = grid.getStore();

    // Passing default values to the API for the removed variables which are still required in the request object
    // record.data.amplification_cycles = 0;
    // record.data.concentration_method = 4;
    record.data.equal_representation_nucleotides = false;
    // if(url == 'api/libraries/')
    //   record.data.qpcr_result = 0;

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
      store.clearFilter(true);
      store.filter("index_type", record.get("index_type"), true);
      var index = store.findRecord("index", value, 0, false, true, true);
      if (index) {
        value = index.get("name");
      }
    }

    if (dataIndex === "rna_quality" && value === 11) {
      return "Determined by Facility";
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

    store.clearFilter();

    // Exact match
    var item = store.findRecord("id", value, 0, false, false, true);

    return item ? item.get("name") : "";
  },

  createEmptyRecords: function (btn) {
    var grid = Ext.getCmp("batch-add-grid");
    var store = grid.getStore();
    var numStoredRecords =
      store.getCount() + Ext.getStore("librariesInRequestStore").getCount();
    var numRecords = btn.up().down("#num-empty-records").getValue();
    var numRecordsLen = numRecords.toString().length;
    numRecordsLen = numRecordsLen < 2 ? 2 : numRecordsLen;
    // Get the 'short' version of a typical request name from IMB, if possible
    var requestName =
      this.requestName.split("_").length > 3
        ? this.requestName.split("_").slice(0, 4).join("_")
        : this.requestName;

    // Left pad a number num with padString to a max length length
    var lpad = function (num, padString, length) {
      var str = String(num);
      while (str.length < length) str = padString + str;
      return str;
    };

    if (numRecords && numRecords > 0) {
      var data = [];
      for (var i = numStoredRecords; i < numRecords + numStoredRecords; i++) {
        data.push({
          // Set a base name for a library/sample based on the request name
          name: Ext.String.format(
            "{0}_{1}",
            requestName,
            lpad(i + 1, "0", numRecordsLen)
          ),
          concentration: 0,
        });
      }
      store.add(data);
    }
  },

  delete: function (record, gridView) {
    var store = record.store;
    store.remove(record);
    gridView.refresh();
  },

  _addToIndexStore: function (store, IndexTypeIds, refreshView, me) {
    // Add indices to store, rather than reloading it

    // Use a counter to decide when to refresh view, that is when all
    // new indices are loaded
    var startViewCounter = me.viewRefreshCounter;

    IndexTypeIds.forEach(function (id) {
      Ext.Ajax.request({
        url: store.proxy.url,
        method: "GET",
        timeout: 60000,
        scope: this,
        params: {
          index_type_id: id,
        },

        success: function (response) {
          var obj = Ext.JSON.decode(response.responseText);
          if (obj) {
            if (obj.length > 0) {
              // Add the id of the index type here rather than getting it via
              // the API, it's 10x faster
              obj.map(function (e) {
                e.index_type = id;
              });
              store.suspendEvents(false);
              store.add(obj);
              store.resumeEvents();
            }
          } else {
            new Noty({ text: response.statusText, type: "error" }).show();
          }
          if (refreshView) {
            // Only refresh the view after the last request has been completed
            me.viewRefreshCounter++;
            if (
              me.viewRefreshCounter - startViewCounter ===
              IndexTypeIds.length * 2
            ) {
              Ext.getCmp("batch-add-grid").getView().refresh();
            }
          }
        },

        failure: function (response) {
          var error = response.statusText;
          try {
            error = Ext.JSON.decode(response.responseText).message;
          } catch (e) { }
          new Noty({ text: error, type: "error" }).show();
          console.error(response);
        },
      });
    });
  },

  _addToIndexPairStore: function (IndexTypeIds, indexReadsStore) {
    // Add index pairs to store, rather than reloading it

    var store = Ext.getStore("IndexPairs");
    IndexTypeIds.forEach(function (id) {
      Ext.Ajax.request({
        url: store.proxy.url,
        method: "GET",
        timeout: 60000,
        scope: this,
        params: {
          index_type_id: id,
        },

        success: function (response) {
          var obj = Ext.JSON.decode(response.responseText);
          if (obj) {
            if (obj.length > 0) {
              store.suspendEvents(false);
              store.add(obj);
              store.resumeEvents();
              if (indexReadsStore) {
                // If pairs are retrived for the Index Type (= obj exists),
                // add Index Pair option to the indexReadsStore
                indexReadsStore.add({ num: 752, label: "I7 + I5 (Pair/UDI)" });
              }
            }
          } else {
            new Noty({ text: response.statusText, type: "error" }).show();
          }
        },

        failure: function (response) {
          var error = response.statusText;
          try {
            error = Ext.JSON.decode(response.responseText).message;
          } catch (e) { }
          new Noty({ text: error, type: "error" }).show();
          console.error(response);
        },
      });
    });
  },
});

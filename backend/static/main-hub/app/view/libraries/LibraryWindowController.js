Ext.define("MainHub.view.libraries.LibraryWindowController", {
  extend: "Ext.app.ViewController",
  alias: "controller.libraries-librarywindow",

  config: {
    control: {
      "#": {
        boxready: "boxready"
      },
      "#libraryCardBtn": {
        click: "selectCard"
      },
      "#sampleCardBtn": {
        click: "selectCard"
      },
      "#libraryCard": {
        activate: "showLibraryCard"
      },
      "#sampleCard": {
        activate: "showSampleCard"
      },
      "#libraryProtocolField": {
        select: "selectLibraryProtocol"
      },
      "#indexType": {
        select: "selectIndexType"
      },
      "#indexReadsField": {
        select: "enableIndicesFields"
      },
      "#nucleicAcidTypeField": {
        select: "selectNucleicAcidType"
      },
      "#sampleProtocolField": {
        select: "selectSampleProtocol"
      },
      "#saveAndAddWndBtn": {
        click: "saveAndAdd"
      },
      "#addWndBtn": {
        click: "saveAndClose"
      }
    }
  },

  boxready: function (wnd) {
    // Bypass Selection (Library/Sample) dialog if editing
    if (wnd.mode === "edit") {
      // if (wnd.record.get('recordType') == 'L') {
      if (wnd.record.getRecordType() === "L") {
        var libraryCardBtn = Ext.getCmp("libraryCardBtn");
        libraryCardBtn.fireEvent("click", libraryCardBtn);
      } else {
        var sampleCardBtn = Ext.getCmp("sampleCardBtn");
        sampleCardBtn.fireEvent("click", sampleCardBtn);
      }
    }
  },

  selectCard: function (btn) {
    var wnd = btn.up("window"),
      layout = btn.up("panel").getLayout();

    wnd.setSize(670, 700);
    wnd.center();
    wnd.getDockedItems('toolbar[dock="bottom"]')[0].show();

    if (btn.itemId == "libraryCardBtn") {
      layout.setActiveItem(1);
      if (wnd.mode == "add") {
        wnd.setTitle("Add Library");
        Ext.getCmp("libraryName").reset();
      }
    } else {
      layout.setActiveItem(2);
      if (wnd.mode == "add") {
        wnd.setTitle("Add Sample");
        Ext.getCmp("sampleName").reset();
      }
    }
  },

  showLibraryCard: function (card) {
    var wnd = card.up("window");

    Ext.getCmp("libraryProtocolInfo").hide();
    Ext.getCmp("addWndBtn").show();

    if (wnd.mode == "add") {
      Ext.getCmp("saveAndAddWndBtn").show();
      Ext.getStore("libraryProtocolsStore").reload();
    } else {
      var record = wnd.record.data,
        form = Ext.getCmp("libraryForm").getForm();

      // Show Library barcode
      Ext.getCmp("libraryBarcodeField").show().setHtml(record.barcode);

      // Set field values
      form.setValues(record);

      if (record.equalRepresentation == "False")
        Ext.getCmp("equalRepresentationRadio2").setValue(true);

      // Set library protocol
      Ext.getStore("libraryProtocolsStore").reload({
        callback: function (records, operation, success) {
          if (!success) {
            Ext.ux.ToastMessage("Cannot load Library Protocols", "error");
          } else {
            var libraryProtocolField = Ext.getCmp("libraryProtocolField");
            libraryProtocolField.select(record.library_protocol);
            libraryProtocolField.fireEvent(
              "select",
              libraryProtocolField,
              libraryProtocolField.findRecordByValue(record.library_protocol),
              true
            );
          }
        }
      });

      // Set Organism
      var organismField = Ext.getCmp("organismField");
      organismField.select(record.organism);
      organismField.fireEvent(
        "select",
        organismField,
        organismField.findRecordByValue(record.organism)
      );

      // Set Index Type
      var indexType = Ext.getCmp("indexType");
      indexType.select(record.index_type);
      indexType.fireEvent(
        "select",
        indexType,
        indexType.findRecordByValue(record.index_type),
        true
      );

      // Set Read Length
      var readLengthField = Ext.getCmp("readLengthField");
      readLengthField.select(record.readLengthId);
      readLengthField.fireEvent(
        "select",
        readLengthField,
        readLengthField.findRecordByValue(record.readLengthId)
      );

      Ext.getCmp("addWndBtn").setConfig("text", "Save");
    }

    this.initializeTooltips();
  },

  selectLibraryProtocol: function (fld, record, setInitialValues) {
    var wnd = fld.up("window"),
      libraryProtocolInfo = Ext.getCmp("libraryProtocolInfo"),
      libraryTypesStore = Ext.getStore("libraryTypesStore"),
      libraryTypeField = Ext.getCmp("libraryTypeField");

    if (record && record.get("name") != "Other") {
      libraryProtocolInfo.show();
      libraryProtocolInfo.setHtml(
        "<strong>Provider, Catalog: </strong>" +
          record.get("provider") +
          ", " +
          record.get("catalog") +
          "<br>" +
          "<strong>Explanation: </strong>" +
          record.get("explanation") +
          "<br>" +
          "<strong>Input Requirements: </strong>" +
          record.get("inputRequirements") +
          "<br>" +
          "<strong>Typical Application: </strong>" +
          record.get("typicalApplication") +
          "<br>" +
          "<strong>Comments: </strong>" +
          record.get("comments")
      );
    } else {
      libraryProtocolInfo.hide();
    }

    libraryTypeField.reset();

    libraryTypesStore.load({
      params: {
        library_protocol_id: record.data.id
      },
      callback: function (records, operation, success) {
        if (!success) {
          Ext.ux.ToastMessage("Cannot load Library Types", "error");
        } else {
          libraryTypeField.setDisabled(false);

          // Set Library Type
          if (wnd.mode == "edit" && setInitialValues === true) {
            var record = wnd.record.data;
            libraryTypeField.select(record.library_type);
            libraryTypeField.fireEvent(
              "select",
              libraryTypeField,
              libraryTypeField.findRecordByValue(record.library_type)
            );
          }
        }
      }
    });
  },

  selectIndexType: function (fld, record, setInitialValues) {
    var wnd = fld.up("window"),
      indexReadsField = Ext.getCmp("indexReadsField"),
      indexI7Store = Ext.getStore("indexI7Store"),
      indexI5Store = Ext.getStore("indexI5Store"),
      indexI7Field = Ext.getCmp("indexI7Field"),
      indexI5Field = Ext.getCmp("indexI5Field");

    indexReadsField.reset();
    indexReadsField.enable();
    indexI7Field.disable();
    indexI5Field.disable();

    for (var i = 0; i <= record.get("index_reads"); i++) {
      indexReadsField.getStore().add({
        num: i
      });
    }

    // Set the number of Index Reads
    if (wnd.mode == "edit" && setInitialValues === true) {
      var wndRecord = wnd.record.data;
      indexReadsField.select(wndRecord.index_reads);
      indexReadsField.fireEvent(
        "select",
        indexReadsField,
        indexReadsField.findRecordByValue(wndRecord.index_reads),
        setInitialValues
      );
    }

    // Remove values before loading new stores
    indexI7Field.reset();
    indexI5Field.reset();

    // Load Index I7
    indexI7Store.load({
      params: {
        index_type_id: record.data.id
      },
      callback: function (records, operation, success) {
        if (!success) Ext.ux.ToastMessage("Cannot load Index I7", "error");
        if (wnd.mode == "edit" && setInitialValues === true)
          indexI7Field.setValue(wndRecord.index_i7);
      }
    });

    // Load Index I5
    indexI5Store.load({
      params: {
        index_type_id: record.data.id
      },
      callback: function (records, operation, success) {
        if (!success) Ext.ux.ToastMessage("Cannot load Index I5", "error");
        if (wnd.mode == "edit" && setInitialValues === true)
          indexI5Field.setValue(wndRecord.index_i5);
      }
    });
  },

  enableIndicesFields: function (fld, record) {
    var indexI7Field = Ext.getCmp("indexI7Field"),
      indexI5Field = Ext.getCmp("indexI5Field");

    if (record.get("num") === 2) {
      indexI7Field.enable();
      indexI5Field.enable();
    } else if (record.get("num") === 1) {
      indexI7Field.enable();
      indexI5Field.disable();
    } else {
      indexI7Field.disable();
      indexI5Field.disable();
    }
  },

  showSampleCard: function (card) {
    var wnd = card.up("window");

    Ext.getCmp("sampleProtocolInfo").hide();
    Ext.getCmp("addWndBtn").show();
    Ext.getStore("libraryProtocolsStore").removeAll();

    if (wnd.mode == "add") {
      Ext.getCmp("saveAndAddWndBtn").show();
    } else {
      var record = wnd.record.data,
        form = Ext.getCmp("sampleForm").getForm();

      // Show Sample barcode
      Ext.getCmp("sampleBarcodeField").show().setHtml(record.barcode);

      // Set field values
      form.setValues(record);

      if (record.equalRepresentation == "False")
        Ext.getCmp("equalRepresentationRadio4").setValue(true);

      // Set nucleic acid type
      var nucleicAcidTypeField = Ext.getCmp("nucleicAcidTypeField");
      nucleicAcidTypeField.select(record.nucleic_acid_type);
      nucleicAcidTypeField.fireEvent(
        "select",
        nucleicAcidTypeField,
        nucleicAcidTypeField.findRecordByValue(record.nucleic_acid_type),
        true
      );

      // Set organism
      var organismSampleField = Ext.getCmp("organismSampleField");
      organismSampleField.select(record.organism);
      organismSampleField.fireEvent(
        "select",
        organismSampleField,
        organismSampleField.findRecordByValue(record.organism)
      );

      // Set read length
      var readLengthSampleField = Ext.getCmp("readLengthSampleField");
      readLengthSampleField.select(record.readLengthId);
      readLengthSampleField.fireEvent(
        "select",
        readLengthSampleField,
        readLengthSampleField.findRecordByValue(record.readLengthId)
      );

      Ext.getCmp("addWndBtn").setConfig("text", "Save");
    }

    this.initializeTooltips();
  },

  selectNucleicAcidType: function (fld, record, setInitialValues) {
    var wnd = fld.up("window"),
      sampleProtocolField = Ext.getCmp("sampleProtocolField"),
      sampleProtocolInfo = Ext.getCmp("sampleProtocolInfo"),
      sampleTypeField = Ext.getCmp("sampleTypeField"),
      rnaQualityField = Ext.getCmp("rnaQualityField");

    if (record.data.type == "RNA") {
      rnaQualityField.setDisabled(false);
    } else {
      rnaQualityField.setDisabled(true);
    }

    // Reset Sample Protocol and Sample Type
    sampleProtocolField.reset();
    sampleProtocolInfo.hide();
    sampleTypeField.reset();
    sampleTypeField.setDisabled();

    Ext.getStore("libraryProtocolsStore").load({
      params: {
        type: record.data.type
      },
      callback: function (records, operation, success) {
        if (!success) {
          Ext.ux.ToastMessage("Cannot load Library Protocols", "error");
        } else {
          sampleProtocolField.setDisabled(false);

          // Set Sample Protocol
          if (wnd.mode == "edit" && setInitialValues === true) {
            var libraryProtocolId = wnd.record.data.library_protocol;
            sampleProtocolField.select(libraryProtocolId);
            sampleProtocolField.fireEvent(
              "select",
              sampleProtocolField,
              sampleProtocolField.findRecordByValue(libraryProtocolId)
            );
          }
        }
      }
    });
  },

  selectSampleProtocol: function (fld, record) {
    var wnd = fld.up("window"),
      sampleProtocolInfo = Ext.getCmp("sampleProtocolInfo"),
      libraryTypesStore = Ext.getStore("libraryTypesStore"),
      sampleTypeField = Ext.getCmp("sampleTypeField");

    if (record && record.get("name") != "Other") {
      sampleProtocolInfo.show();
      sampleProtocolInfo.setHtml(
        "<strong>Provider, Catalog: </strong>" +
          record.get("provider") +
          ", " +
          record.get("catalog") +
          "<br>" +
          "<strong>Explanation: </strong>" +
          record.get("explanation") +
          "<br>" +
          "<strong>Input Requirements: </strong>" +
          record.get("inputRequirements") +
          "<br>" +
          "<strong>Typical Application: </strong>" +
          record.get("typicalApplication") +
          "<br>" +
          "<strong>Comments: </strong>" +
          record.get("comments")
      );
    } else {
      sampleProtocolInfo.hide();
    }

    sampleTypeField.reset();

    libraryTypesStore.load({
      params: {
        library_protocol_id: record.data.id
      },
      callback: function (records, operation, success) {
        if (!success) {
          Ext.ux.ToastMessage("Cannot load Library Types", "error");
        } else {
          sampleTypeField.setDisabled(false);

          // Set Sample Type
          if (wnd.mode == "edit") {
            var record = wnd.record.data;
            sampleTypeField.select(record.library_type);
            sampleTypeField.fireEvent(
              "select",
              sampleTypeField,
              sampleTypeField.findRecordByValue(record.library_type)
            );
          }
        }
      }
    });
  },

  save: function (btn, addAnother) {
    var form = null,
      url = "",
      data = {},
      params = {},
      nameFieldName = "",
      wnd = btn.up("window"),
      card = Ext.getCmp("librarySamplePanel").getLayout().getActiveItem().id;
    addAnother = addAnother || false;

    if (card == "libraryCard") {
      form = Ext.getCmp("libraryForm");
      url = "library/save/";
      nameFieldName = "libraryName";
      data = form.getForm().getFieldValues();
      params = $.extend(data, {
        library_id: wnd.record ? wnd.record.data.libraryId : ""
      });
    } else {
      form = Ext.getCmp("sampleForm");
      url = "sample/save/";
      nameFieldName = "sampleName";
      data = form.getForm().getFieldValues();
      params = $.extend(data, {
        sample_id: wnd.record ? wnd.record.data.sampleId : ""
      });
    }

    if (form.isValid()) {
      wnd.setLoading("Saving...");
      Ext.Ajax.request({
        url: url,
        method: "POST",
        timeout: 1000000,
        scope: this,
        params: {
          mode: wnd.mode,
          records: Ext.JSON.encode([params])
        },

        success: function (response) {
          var obj = Ext.JSON.decode(response.responseText);

          if (obj.success) {
            if (wnd.mode == "add") {
              var grid = Ext.getCmp("librariesInRequestTable");
              grid.getStore().add(obj.data);
              Ext.ux.ToastMessage("Record has been added!");
            } else {
              Ext.getStore("librariesInRequestStore").reload({
                params: {
                  request_id: wnd.record.get("requestId")
                }
              });
              // Ext.getStore('requestsStore').reload();
              Ext.getStore("librariesStore").reload();
              // MainHub.Utilities.reloadAllStores();
              Ext.ux.ToastMessage("Record has been updated!");
            }
            // Ext.getStore('PoolingTree').reload();

            // Preserve all fields except for Name, if 'Save and Add another' button was pressed
            if (addAnother) {
              Ext.getCmp(nameFieldName).reset();
              wnd.setLoading(false);
            } else {
              wnd.close();
            }
          } else {
            Ext.ux.ToastMessage(obj.error, "error");
            console.error("[ERROR]: " + url);
            console.error(response);
            wnd.setLoading(false);
          }
        },

        failure: function (response) {
          wnd.setLoading(false);
          Ext.ux.ToastMessage(response.statusText, "error");
          console.error("[ERROR]: " + url);
          console.error(response);
        }
      });
    } else {
      Ext.ux.ToastMessage("Check the form", "warning");
    }
  },

  saveAndAdd: function (btn) {
    this.save(btn, true);
  },

  saveAndClose: function (btn) {
    this.save(btn);
  },

  initializeTooltips: function () {
    $.each($(".field-tooltip"), function (idx, item) {
      Ext.create("Ext.tip.ToolTip", {
        title: "Help",
        target: item,
        html: $(item).attr("tooltip-text"),
        dismissDelay: 15000,
        maxWidth: 300
      });
    });
  }
});

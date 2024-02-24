Ext.define("MainHub.view.incominglibraries.IncomingLibrariesController", {
  extend: "MainHub.components.BaseGridController",
  alias: "controller.incominglibraries-incominglibraries",

  mixins: ["MainHub.mixins.grid.CheckboxesAndSearchInput"],

  config: {
    control: {
      "#": {
        activate: "activateView"
      },
      "#incoming-libraries-grid": {
        resize: "resize",
        itemcontextmenu: "showMenu",
        groupcontextmenu: "showGroupMenu",
        beforeedit: "toggleEditors",
        edit: "editRecord"
      },
      "#search-field": {
        change: "changeFilter"
      },
      "#show-libraries-checkbox": {
        change: "changeFilter"
      },
      "#show-samples-checkbox": {
        change: "changeFilter"
      },
      "#as-handler-incoming-checkbox": {
        change: "toggleAsHandler"
      },
      "#cancel-button": {
        click: "cancel"
      },
      "#save-button": {
        click: "save"
      }
    }
  },

  toggleEditors: function (editor, context) {
    var record = context.record;
    var qPCRResultEditor = Ext.getCmp("qPCRResultEditor");
    var rnaQualityEditor = Ext.getCmp("rnaQualityIncomingEditor");
    var nucleicAcidTypesStore = Ext.getStore("nucleicAcidTypesStore");

    // If pooled libraries disable row editing
    if (record.get("pooled_libraries")) {
      return false;
    }

    // Toggle qPCR Result and RNA Quality
    if (record.get("record_type") === "Library") {
      qPCRResultEditor.enable();
      rnaQualityEditor.disable();
    } else {
      qPCRResultEditor.disable();

      var nat = nucleicAcidTypesStore.findRecord(
        "id",
        record.get("nucleic_acid_type"),
        0,
        false,
        true,
        true
      );

      if (nat !== null && nat.get("type") === "RNA") {
        rnaQualityEditor.enable();
      } else {
        rnaQualityEditor.disable();
      }
    }
  },

  editRecord: function (editor, context) {
    var store = editor.grid.getStore();
    var record = context.record;
    var changes = record.getChanges();
    var values = context.newValues;
    var reload = Object.keys(changes).indexOf("quality_check") !== -1;

    // Compute Amount
    if (
      Object.keys(changes).indexOf("amount_facility") === -1 &&
      values.dilution_factor &&
      values.concentration_facility &&
      values.sample_volume_facility
    ) {
      var amountFacility = this._calculateAmount(
        values.dilution_factor,
        values.concentration_facility,
        values.sample_volume_facility
      );
      record.set("amount_facility", amountFacility);
    }

    // Send the changes to the server
    this.syncStore(store.getId(), reload);
  },

  applyToAll: function (gridView, record, dataIndex) {
    var self = this;
    var store = gridView.grid.getStore();
    var allowedColumns = [
      "dilution_factor",
      "concentration_facility",
      "concentration_method_facility",
      "sample_volume_facility",
      "amount_facility",
      "size_distribution_facility",
      "comments_facility",
      "qpcr_result_facility",
      "rna_quality_facility"
    ];
    var ngFormulaDataIndices = [
      "dilution_factor",
      "concentration_facility",
      "sample_volume_facility"
    ];

    if (
      typeof dataIndex !== "undefined" &&
      allowedColumns.indexOf(dataIndex) !== -1
    ) {
      store.each(function (item) {
        if (item.get("request") === record.get("request") && item !== record) {
          item.set(dataIndex, record.get(dataIndex));

          // Calculate Amount (facility)
          if (ngFormulaDataIndices.indexOf(dataIndex) !== -1) {
            var dilutionFactor = item.get("dilution_factor");
            var concentrationFacility = item.get("concentration_facility");
            var sampleVolumeFacility = item.get("sample_volume_facility");

            if (
              dilutionFactor &&
              concentrationFacility &&
              sampleVolumeFacility
            ) {
              var amountFacility = self._calculateAmount(
                dilutionFactor,
                concentrationFacility,
                sampleVolumeFacility
              );
              item.set("amount_facility", amountFacility);
            }
          }
        }
      });

      // Send the changes to the server
      self.syncStore(store.getId());
    } else {
      self._showEditableColumnsMessage(gridView, allowedColumns);
    }
  },

  toggleAsHandler: function (checkbox, newValue, oldValue, eOpts) {
    var grid = checkbox.up("#incoming-libraries-grid");
    var gridGrouping = grid.view.getFeature("incoming-libraries-grid-grouping");
    grid.store.getProxy().extraParams.asHandler = newValue ? "True" : "False";
    grid.store.reload({
      callback: function (records, operation, success) {
        if (success) {
          newValue ? gridGrouping.expandAll() : gridGrouping.collapseAll();
        }
      },
    });
  },

  _calculateAmount: function (dilutionFactor, concentration, sampleVolume) {
    return (
      parseFloat(dilutionFactor) *
      parseFloat(concentration) *
      parseFloat(sampleVolume)
    );
  }
});

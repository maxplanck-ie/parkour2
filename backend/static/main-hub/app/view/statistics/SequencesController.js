Ext.define("MainHub.view.statistics.SequencesController", {
  extend: "MainHub.components.BaseGridController",
  alias: "controller.sequences-statistics",

  config: {
    control: {
      "#": {
        activate: "activateView"
      },
      "#sequences-grid": {
        groupcontextmenu: "showGroupMenu"
      },
      daterangepicker: {
        select: "setRange"
      },
      "#download-report": {
        click: "downloadReport",
      },
      "#as-handler-sequences-checkbox": {
        change: "toggleHandler",
      },
      "#as-bioinformatician-sequences-checkbox": {
        change: "toggleBioinformatician",
      },
      "#merge-lanes-sequences-checkbox": {
        change: "toggleMergeLanes",
      },
    },
  },

  activateView: function (view) {
    var dateRange = view.down("daterangepicker");
    dateRange.fireEvent("select", dateRange, dateRange.getPickerValue());
  },

  setRange: function (drp, value) {
    var grid = drp.up("grid");

    grid.getStore().reload({
      params: {
        start: value.startDateObj,
        end: value.endDateObj
      },
      callback: function () {
        grid.getView().features[0].collapseAll();
      },
    });
  },

  toggleHandler: function (checkbox, newValue, oldValue, eOpts) {
    var grid = checkbox.up("#sequences-grid");
    var dateRange = grid.down("daterangepicker").getPickerValue();
    var gridGrouping = grid.view.getFeature("sequences-grid-grouping");
    grid.store.getProxy().extraParams.asHandler = newValue ? "True" : "False";
    grid.store.reload({
      params: {
        start: dateRange.startDateObj,
        end: dateRange.endDateObj,
      },
      callback: function (records, operation, success) {
        if (success) {
          newValue ? gridGrouping.expandAll() : gridGrouping.collapseAll();
        }
      },
    });
  },

  toggleBioinformatician: function (checkbox, newValue, oldValue, eOpts) {
    var grid = checkbox.up("#sequences-grid");
    var dateRange = grid.down("daterangepicker").getPickerValue();
    var gridGrouping = grid.view.getFeature("sequences-grid-grouping");
    grid.store.getProxy().extraParams.asBioinformatician = newValue ? "True" : "False";
    grid.store.reload({
      params: {
        start: dateRange.startDateObj,
        end: dateRange.endDateObj,
      },
      callback: function (records, operation, success) {
        if (success) {
          newValue ? gridGrouping.expandAll() : gridGrouping.collapseAll();
        }
      },
    });
  },

  toggleMergeLanes: function (checkbox, newValue, oldValue, eOpts) {
    var grid = checkbox.up("#sequences-grid");
    var dateRange = grid.down("daterangepicker").getPickerValue();
    grid.store.getProxy().extraParams.mergeLanes = newValue ? "True" : "False";
    grid.store.reload({
      params: {
        start: dateRange.startDateObj,
        end: dateRange.endDateObj,
      },
    });
  },

  downloadReport: function (btn) {
    var store = btn.up("grid").getStore();
    var selectedRecords = this._getSelectedRecords(store);
    var flowCellIds = this._getFlowCellIds(store);
    var mergeLanesCb = btn.up("grid").down('#merge-lanes-sequences-checkbox');

    if (selectedRecords.length === 0) {
      new Noty({
        text: "You did not select any items.",
        type: "warning"
      }).show();
      return;
    }

    var form = Ext.create("Ext.form.Panel", { standardSubmit: true });
    form.submit({
      url: "api/sequences_statistics/download_report/",
      params: {
        barcodes: Ext.JSON.encode(Ext.Array.pluck(selectedRecords, "barcode")),
        flowcell_ids: Ext.JSON.encode(flowCellIds),
        merge_lanes: mergeLanesCb.getValue() ? "True" : "False",
      }
    });
  },

  _getSelectedRecords: function (store) {
    var records = [];

    store.each(function (item) {
      if (item.get("selected")) {
        records.push({
          barcode: item.get("barcode")
        });
      }
    });

    return records;
  },

  _getFlowCellIds: function (store) {
    var records = [];

    store.each(function (item) {
      if (item.get("selected")) {
        records.push(item.get("flowcell_id"));
      }
    });

    return Array.from(new Set(records));
  }
});

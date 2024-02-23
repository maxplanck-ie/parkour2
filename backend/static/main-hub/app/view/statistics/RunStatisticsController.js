Ext.define("MainHub.view.statistics.RunStatisticsController", {
  extend: "MainHub.components.BaseGridController",
  alias: "controller.run-statistics",

  config: {
    control: {
      "#": {
        activate: "activateView",
      },
      daterangepicker: {
        select: "setRange",
      },
      "#as-handler-statistics-checkbox": {
        change: "toggleHandler",
      },
      "#as-bioinformatician-statistics-checkbox": {
        change: "toggleBioinformatician",
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
        end: value.endDateObj,
      },
      callback: function () {
        grid.getView().features[0].collapseAll();
      },
    });
  },

  toggleHandler: function (checkbox, newValue, oldValue, eOpts) {
    var grid = checkbox.up("#run-statistics-grid");
    var dateRange = grid.down("daterangepicker").getPickerValue();
    var gridGrouping = grid.view.getFeature("run-statistics-grid-grouping");
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
    var grid = checkbox.up("#run-statistics-grid");
    var dateRange = grid.down("daterangepicker").getPickerValue();
    var gridGrouping = grid.view.getFeature("run-statistics-grid-grouping");
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

});

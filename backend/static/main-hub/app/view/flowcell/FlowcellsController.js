Ext.define("MainHub.view.flowcell.FlowcellsController", {
  extend: "MainHub.components.BaseGridController",
  alias: "controller.flowcells",

  requires: [
    "MainHub.view.flowcell.FlowcellWindow",
    "MainHub.view.flowcell.PoolInfoWindow",
    "MainHub.view.flowcell.SampleSheetIlluminav2Window",
  ],

  mixins: ["MainHub.grid.SearchInputMixin"],

  config: {
    control: {
      "#": {
        activate: "activateView",
      },
      parkourmonthpicker: {
        select: "selectMonth",
      },
      "#flowcells-grid": {
        resize: "resize",
        itemcontextmenu: "showMenu",
        groupcontextmenu: "showGroupMenu",
        cellclick: "showPoolInfo",
        edit: "editRecord",
      },
      "#check-column": {
        beforecheckchange: "selectRecord",
      },
      "#load-button": {
        click: "onLoadBtnClick",
      },
      "#download-benchtop-protocol-button": {
        click: "downloadBenchtopProtocol",
      },
      "#download-sample-sheet-button": {
        click: "downloadSampleSheet",
      },
      "#search-field": {
        change: "changeFilter",
      },
      "#as-handler-flowcell-checkbox": {
        change: "toggleHandler",
      },
      "#cancel-button": {
        click: "cancel",
      },
      "#save-button": {
        click: "save",
      },
    },
  },

  activateView: function (view) {
    var startMonthPicker = view.down("#start-month-picker");
    var endMonthPicker = view.down("#end-month-picker");

    var currentDate = new Date();
    var defaultStartDate = Ext.Date.subtract(currentDate, Ext.Date.MONTH, 0);
    var defaultEndDate = currentDate;

    startMonthPicker.setValue(defaultStartDate);
    endMonthPicker.setValue(defaultEndDate);

    startMonthPicker.fireEvent(
      "select",
      startMonthPicker,
      defaultStartDate,
      "start"
    );
    endMonthPicker.fireEvent("select", endMonthPicker, defaultEndDate, "end");
  },

  selectMonth: function (df, value, criteria) {
    if (!criteria) {
      criteria = df.itemId === "start-month-picker" ? "start" : "end";
    }

    var grid = df.up("grid");
    var startMonthPicker = grid.down("#start-month-picker");
    var endMonthPicker = grid.down("#end-month-picker");

    var startOfMonth, endOfMonth;

    if (criteria === "start") {
      startOfMonth = Ext.Date.getFirstDateOfMonth(value);
      endOfMonth = Ext.Date.getLastDateOfMonth(endMonthPicker.getValue());
    } else if (criteria === "end") {
      startOfMonth = Ext.Date.getFirstDateOfMonth(startMonthPicker.getValue());
      endOfMonth = Ext.Date.getLastDateOfMonth(value);
    }

    var start = Ext.Date.format(startOfMonth, "d.m.Y");
    var end = Ext.Date.format(endOfMonth, "d.m.Y");

    var store = grid.getStore();
    store.getProxy().setExtraParam("start", start);
    store.getProxy().setExtraParam("end", end);

    store.reload({
      callback: function () {
        grid.getView().features[0].collapseAll();
      },
    });
  },

  selectRecord: function (cb, rowIndex, checked, record) {
    // Don't select lanes from a different flowcell
    var selectedLane = record.store.findRecord("selected", true);
    if (selectedLane) {
      if (record.get("flowcell") !== selectedLane.get("flowcell")) {
        new Noty({
          text: "You can only select lanes from the same flowcell.",
          type: "warning",
        }).show();
        return false;
      }
    }
  },

  selectUnselectAll: function (grid, groupId, selected) {
    var store = grid.getStore();
    var selectedRecords = this._getSelectedRecords(store);

    if (selectedRecords.length > 0 && selectedRecords[0].flowcell !== groupId) {
      new Noty({
        text: "You can only select lanes from the same flowcell.",
        type: "warning",
      }).show();
      return false;
    }

    store.each(function (item) {
      if (item.get(store.groupField) === groupId) {
        item.set("selected", selected);
      }
    });
  },

  editRecord: function (editor, context) {
    var store = editor.grid.getStore();
    this.syncStore(store.getId());
  },

  applyToAll: function (gridView, record, dataIndex) {
    var store = gridView.grid.getStore();
    var allowedColumns = ["loading_concentration", "phix"];

    if (dataIndex && allowedColumns.indexOf(dataIndex) !== -1) {
      store.each(function (item) {
        if (
          item.get(store.groupField) === record.get(store.groupField) &&
          item !== record
        ) {
          item.set(dataIndex, record.get(dataIndex));
        }
      });

      // Send the changes to the server
      this.syncStore(store.getId());
    } else {
      this._showEditableColumnsMessage(gridView, allowedColumns);
    }
  },

  onLoadBtnClick: function () {
    Ext.create("MainHub.view.flowcell.FlowcellWindow");
  },

  downloadBenchtopProtocol: function (btn) {
    var store = btn.up("grid").getStore();
    var selectedLanes = this._getSelectedRecords(store);

    if (selectedLanes.length === 0) {
      new Noty({
        text: "You did not select any lanes.",
        type: "warning",
      }).show();
      return;
    }

    var form = Ext.create("Ext.form.Panel", { standardSubmit: true });
    form.submit({
      url: "api/flowcells/download_benchtop_protocol/",
      params: {
        ids: Ext.JSON.encode(Ext.Array.pluck(selectedLanes, "pk")),
      },
    });
  },

  downloadSampleSheet: function (btn) {
    var store = btn.up("grid").getStore();
    var selectedLanes = this._getSelectedRecords(store);

    if (selectedLanes.length === 0) {
      new Noty({
        text: "You did not select any lanes.",
        type: "warning",
      }).show();
      return;
    }

    var form = Ext.create("Ext.form.Panel", { standardSubmit: true });
    form.submit({
      url: "api/flowcells/download_sample_sheet/",
      params: {
        ids: Ext.JSON.encode(Ext.Array.pluck(selectedLanes, "pk")),
        flowcell_id: selectedLanes[0].flowcell,
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
      },
    });
  },

  toggleHandler: function (checkbox, newValue, oldValue, eOpts) {
    var grid = checkbox.up("#flowcells-grid");
    var gridGrouping = grid.view.getFeature("flowcells-grid-grouping");
    grid.store.getProxy().extraParams.asHandler = newValue ? "True" : "False";
    grid.store.reload({
      callback: function (records, operation, success) {
        if (success) {
          newValue ? gridGrouping.expandAll() : gridGrouping.collapseAll();
        }
      },
    });
  },

  showPoolInfo: function (view, td, cellIndex, record, tr, rowIndex, e) {
    if (e.getTarget(".pool-name") !== null) {
      Ext.create("MainHub.view.flowcell.PoolInfoWindow", {
        title: record.get("pool_name"),
        pool: record.get("pool"),
      });
    }
  },

  _getSelectedRecords: function (store) {
    var records = [];

    store.each(function (item) {
      if (item.get("selected")) {
        records.push({
          pk: item.get("pk"),
          flowcell: item.get("flowcell"),
        });
      }
    });

    return records;
  },
});

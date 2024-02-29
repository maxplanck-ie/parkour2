Ext.define("MainHub.view.libraries.LibrariesController", {
  extend: "Ext.app.ViewController",
  alias: "controller.libraries-libraries",

  config: {
    control: {
      "#": {
        activate: "activateView"
      },
      "#librariesTable": {
        // boxready: 'refresh',
        // refresh: 'refresh',
        // itemcontextmenu: 'showContextMenu'
      },
      "#showLibrariesCheckbox": {
        change: "changeFilter"
      },
      "#showSamplesCheckbox": {
        change: "changeFilter"
      },
      "#searchField": {
        change: "changeFilter"
      },
      "#showAlllr": {
        change: "toggleShowAll"
      },
      "#as-handler-libraries-samples-checkbox": {
        change: "toggleHandler"
      },
      "#as-bioinformatician-libraries-samples-checkbox": {
        change: "toggleBioinformatician"
      },
      "#statusCombobox": {
        change: "changeStatus"
      },
      "#libraryProtocolCombobox": {
        change: "changeLibraryProtocol"
      },
      "#search-field": {
        change: "changeSearchField"
      }
    }
  },

  activateView: function () {
    Ext.getStore("librariesStore").reload();
  },

  refresh: function (grid) {
    Ext.getStore("librariesStore").reload();
  },

  showContextMenu: function (grid, record, item, index, e) {
    var me = this;

    // Don't edit records which have reached status 1 and higher
    if (!USER_IS_STAFF && record.get("status") !== 0) return false;

    e.stopEvent();
    Ext.create("Ext.menu.Menu", {
      items: [
        {
          text: "Edit",
          iconCls: "x-fa fa-pencil",
          handler: function () {
            me.editRecord(record);
          }
        }
      ]
    }).showAt(e.getXY());
  },

  editRecord: function (record) {
    Ext.create("MainHub.view.libraries.LibraryWindow", {
      title: record.data.recordType == "L" ? "Edit Library" : "Edit Sample",
      mode: "edit",
      record: record
    }).show();
  },

  changeFilter: function (el, value) {
    var grid = Ext.getCmp("librariesTable"),
      store = grid.getStore(),
      columns = Ext.pluck(grid.getColumns(), "dataIndex"),
      showLibraries = null,
      showSamples = null,
      searchQuery = null;

    if (el.itemId == "showLibrariesCheckbox") {
      showLibraries = value;
      showSamples = el.up().items.items[1].getValue();
      searchQuery = el.up("header").down("textfield").getValue();
    } else if (el.itemId == "showSamplesCheckbox") {
      showLibraries = el.up().items.items[0].getValue();
      showSamples = value;
      searchQuery = el.up("header").down("textfield").getValue();
    }

    var showFilter = Ext.util.Filter({
      filterFn: function (record) {
        var res = false;
        if (record.get("recordType") == "L") {
          res = res || showLibraries;
        } else {
          res = res || showSamples;
        }
        return res;
      }
    });

    var searchFilter = Ext.util.Filter({
      filterFn: function (record) {
        var res = false;
        if (searchQuery) {
          Ext.each(columns, function (column) {
            var value = record.get(column);
            if (
              value &&
              value
                .toString()
                .toLowerCase()
                .indexOf(searchQuery.toLowerCase()) > -1
            ) {
              res = res || true;
            }
          });
        } else {
          res = true;
        }
        return res;
      }
    });

    store.clearFilter();
    store.filter([showFilter, searchFilter]);
  },

  gridCellTooltipRenderer: function (value, meta) {
    meta.tdAttr = 'data-qtip="' + value + '"';
    return value;
  },

  toggleHandler: function (checkbox, newValue, oldValue, eOpts) {
    var grid = checkbox.up("treepanel");
    grid.getView().mask("Loading...");
    var store = Ext.getStore("librariesStore");
    store.getProxy().extraParams.asHandler = newValue ? "True" : "False";
    store.reload({
      callback: function (records, operation, success) {
      if (!success) {
        new Noty({
          text:
            operation.getError() ||
            "Error occurred while searching.",
          type: "error"
        }).show();
      }
      grid.getView().unmask();
    }});
  },

  toggleBioinformatician: function (checkbox, newValue, oldValue, eOpts) {
    var grid = checkbox.up("treepanel");
    grid.getView().mask("Loading...");
    var store = Ext.getStore("librariesStore");
    store.getProxy().extraParams.asBioinformatician = newValue ? "True" : "False";
    store.reload({
      callback: function (records, operation, success) {
      if (!success) {
        new Noty({
          text:
            operation.getError() ||
            "Error occurred while searching.",
          type: "error"
        }).show();
      }
      grid.getView().unmask();
    }});
  },

  toggleShowAll: function (checkbox, newValue, oldValue, eOpts) {
    var grid = checkbox.up("treepanel");
    grid.getView().mask("Loading...");
    var store = Ext.getStore("librariesStore");
    store.getProxy().extraParams.showAll = newValue ? "True" : "False";
    store.reload({
      callback: function (records, operation, success) {
      if (!success) {
        new Noty({
          text:
            operation.getError() ||
            "Error occurred while searching.",
          type: "error"
        }).show();
      }
      grid.getView().unmask();
    }});
  },

  changeStatus: function (combo, newValue, oldValue, eOpts) {
    if (newValue) {
      var grid = combo.up("treepanel");
      grid.getView().mask("Loading...");
      var selectedRecord = combo.findRecordByValue(newValue);
      var textWidth = Ext.util.TextMetrics.measure(
        combo.inputEl,
        selectedRecord.get(combo.displayField)
      ).width;
      combo.setWidth(textWidth + 55);

      var librariesStore = Ext.getStore("librariesStore");
      librariesStore.getProxy().extraParams.statusFilter = newValue !== "all" ? newValue : '';
      librariesStore.reload({
        callback: function (records, operation, success) {
          if (!success) {
            new Noty({
              text:
                operation.getError() ||
                "Error occurred while searching.",
              type: "error"
            }).show();
          }
          grid.getView().unmask();
        }
      });
    }
  },

  changeLibraryProtocol: function (combo, newValue, oldValue, eOpts) {
    if (newValue) {
      var grid = combo.up("treepanel");
      grid.getView().mask("Loading...");
      var selectedRecord = combo.findRecordByValue(newValue);
      var textWidth = Ext.util.TextMetrics.measure(
        combo.inputEl,
        selectedRecord.get(combo.displayField)
      ).width;
      combo.setWidth(textWidth > 220 ? 220 : textWidth + 55);

      var librariesStore = Ext.getStore("librariesStore");
      librariesStore.getProxy().extraParams.libraryProtocolFilter = newValue !== -1 ? newValue : '';
      librariesStore.reload({
        callback: function (records, operation, success) {
          if (!success) {
            new Noty({
              text:
                operation.getError() ||
                "Error occurred while searching.",
              type: "error"
            }).show();
          }
          grid.getView().unmask();
        }
      });
    }
  },

  changeSearchField: Ext.Function.createBuffered(
    function (field, newValue, oldValue) {
      var grid = field.up("treepanel");
      grid.getView().mask("Loading...");
      var librariesStore = Ext.getStore("librariesStore");
      librariesStore.getProxy().extraParams.searchString = newValue;
      librariesStore.reload({
        callback: function (records, operation, success) {
          if (!success) {
            new Noty({
              text:
                operation.getError() ||
                "Error occurred while searching.",
              type: "error"
            }).show();
          }
          grid.getView().unmask();
        }
      });
    },
    500,
    this
  )

});

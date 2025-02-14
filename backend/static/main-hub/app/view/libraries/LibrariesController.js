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
    if (value) {
      meta.tdAttr = 'data-qtip="' + value + '"';
    } else meta.tdAttr = "data-qtip=Empty";
    return value;
  }
});

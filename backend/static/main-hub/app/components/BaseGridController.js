Ext.define("MainHub.components.BaseGridController", {
  extend: "Ext.app.ViewController",
  alias: "controller.basegrid",

  activateView: function (view) {
    var store = view.down("grid").getStore();
    Ext.getStore(store.getId()).reload();
  },

  resize: function (el) {
    el.setHeight(Ext.Element.getViewportHeight() - 64);
  },

  showMenu: function (gridView, record, item, index, e) {
    var self = this;
    var customConfig = gridView.grid.initialConfig.customConfig;
    var qcMenuOptions = [];
    var menuItems = [
      {
        text: "Apply to All",
        margin: "5px 5px 2px 5px",
        handler: function () {
          var dataIndex = self._getDataIndex(e, gridView);
          self.applyToAll(gridView, record, dataIndex);
        }
      }
    ];

    if (customConfig && customConfig.qualityCheckMenuOptions) {
      qcMenuOptions = customConfig.qualityCheckMenuOptions;
    }

    if (qcMenuOptions.length > 0) {
      var qcMenu = {
        xtype: "container",
        items: [
          {
            xtype: "container",
            html: "Quality Check",
            margin: "10px 5px 5px 5px",
            style: {
              color: "#000"
            }
          },
          {
            xtype: "container",
            margin: 5,
            layout: {
              type: "hbox",
              pack: "center",
              align: "middle"
            },
            defaults: {
              xtype: "button",
              scale: "medium",
              margin: "5px 10px 10px"
            },
            items: []
          }
        ]
      };

      if (qcMenuOptions.indexOf("passed") !== -1) {
        qcMenu.items[1].items.push({
          ui: "menu-button-green",
          tooltip: "passed",
          iconCls: "fa fa-lg fa-check",
          handler: function () {
            self.qualityCheckSingle(record, "passed");
            this.up("menu").hide();
          }
        });
      }

      if (qcMenuOptions.indexOf("completed") !== -1) {
        qcMenu.items[1].items.push({
          ui: "menu-button-green",
          tooltip: "completed",
          iconCls: "fa fa-lg fa-check",
          handler: function () {
            self.qualityCheckSingle(record, "completed");
            this.up("menu").hide();
          }
        });
      }

      if (qcMenuOptions.indexOf("compromised") !== -1) {
        qcMenu.items[1].items.push({
          ui: "menu-button-yellow",
          tooltip: "compromised",
          iconCls: "fa fa-lg fa-exclamation-triangle",
          handler: function () {
            self.qualityCheckSingle(record, "compromised");
            this.up("menu").hide();
          }
        });
      }

      if (qcMenuOptions.indexOf("failed") !== -1) {
        qcMenu.items[1].items.push({
          ui: "menu-button-red",
          tooltip: "failed",
          iconCls: "fa fa-lg fa-times",
          handler: function () {
            self.qualityCheckSingle(record, "failed");
            this.up("menu").hide();
          }
        });
      }

      menuItems.push("-");
      menuItems.push(qcMenu);
    }

    e.stopEvent();
    Ext.create("Ext.menu.Menu", {
      plain: true,
      items: menuItems
    }).showAt(e.getXY());
  },

  showGroupMenu: function (gridView, node, groupId, e) {
    var self = this;
    var grid = gridView.grid;
    var customConfig = gridView.grid.initialConfig.customConfig;
    var qcMenuOptions = [];
    var menuItems = [
      {
        text: "Select All",
        margin: "5px 5px 0 5px",
        handler: function () {
          self.selectUnselectAll(grid, parseInt(groupId), true);
        }
      },
      {
        text: "Unselect All",
        margin: 5,
        handler: function () {
          self.selectUnselectAll(grid, parseInt(groupId), false);
        }
      }
    ];

    if (customConfig && customConfig.qualityCheckMenuOptions) {
      qcMenuOptions = customConfig.qualityCheckMenuOptions;
    }

    if (
      qcMenuOptions.length > 0 &&
      self._getSelectedRecords(grid.getStore(), parseInt(groupId)).length > 0
    ) {
      var qcMenu = {
        xtype: "container",
        items: [
          {
            xtype: "container",
            html: "Quality Check: Selected",
            margin: "10px 5px 5px 5px",
            style: {
              color: "#000"
            }
          },
          {
            xtype: "container",
            margin: 5,
            layout: {
              type: "hbox",
              pack: "center",
              align: "middle"
            },
            defaults: {
              xtype: "button",
              scale: "medium",
              margin: "5px 10px 10px"
            },
            items: []
          }
        ]
      };

      if (qcMenuOptions.indexOf("passed") !== -1) {
        qcMenu.items[1].items.push({
          ui: "menu-button-green",
          tooltip: "passed",
          iconCls: "fa fa-lg fa-check",
          handler: function () {
            self.qualityCheckSelected(grid, parseInt(groupId), "passed");
            this.up("menu").hide();
          }
        });
      }

      if (qcMenuOptions.indexOf("completed") !== -1) {
        qcMenu.items[1].items.push({
          ui: "menu-button-green",
          tooltip: "completed",
          iconCls: "fa fa-lg fa-check",
          handler: function () {
            self.qualityCheckSelected(grid, parseInt(groupId), "completed");
            this.up("menu").hide();
          }
        });
      }

      if (qcMenuOptions.indexOf("compromised") !== -1) {
        qcMenu.items[1].items.push({
          ui: "menu-button-yellow",
          tooltip: "compromised",
          iconCls: "fa fa-lg fa-exclamation-triangle",
          handler: function () {
            self.qualityCheckSelected(grid, parseInt(groupId), "compromised");
            this.up("menu").hide();
          }
        });
      }

      if (qcMenuOptions.indexOf("failed") !== -1) {
        qcMenu.items[1].items.push({
          ui: "menu-button-red",
          tooltip: "failed",
          iconCls: "fa fa-lg fa-times",
          handler: function () {
            self.qualityCheckSelected(grid, parseInt(groupId), "failed");
            this.up("menu").hide();
          }
        });
      }

      menuItems.push("-");
      menuItems.push(qcMenu);
    }

    e.stopEvent();
    Ext.create("Ext.menu.Menu", {
      plain: true,
      items: menuItems
    }).showAt(e.getXY());
  },

  syncStore: function (storeId, reload) {
    var reloadStore = reload || false;

    Ext.getStore(storeId).sync({
      success: function (batch) {
        var response = batch.operations[0].getResponse();
        var obj = Ext.JSON.decode(response.responseText);

        if (reloadStore) {
          Ext.getStore(storeId).reload();
        }

        if (obj.message && obj.message !== "") {
          new Noty({ text: obj.message, type: "warning" }).show();
        } else {
          new Noty({ text: "Changes have been saved successfully." }).show();
        }
      },

      failure: function (batch) {
        var error = batch.operations[0].getError();
        console.error(error);

        try {
          var obj = Ext.JSON.decode(error.response.responseText);
          if (!obj.success && obj.message && obj.message !== "") {
            error = obj.message;
          }
        } catch (e) {
          error = error.statusText;
        }

        new Noty({ text: error, type: "error" }).show();
      }
    });
  },

  selectUnselectAll: function (grid, groupId, selected) {
    var store = grid.getStore();

    store.each(function (item) {
      if (item.get(store.groupField) === groupId) {
        item.set("selected", selected);
      }
    });
  },

  qualityCheckSingle: function (record, result) {
    var store = record.store;
    record.set("quality_check", result);
    this.syncStore(store.getId(), true);
  },

  qualityCheckSelected: function (grid, groupId, result) {
    var store = grid.getStore();

    store.each(function (item) {
      if (item.get(store.groupField) === groupId && item.get("selected")) {
        item.set("quality_check", result);
      }
    });

    this.syncStore(store.getId(), true);
  },

  save: function (btn) {
    var store = btn.up("grid").getStore();
    this.syncStore(store.getId());
  },

  cancel: function (btn) {
    btn.up("grid").getStore().rejectChanges();
  },

  gridCellTooltipRenderer: function (value, meta) {
    if (value) {
      meta.tdAttr = 'data-qtip="' + value + '"';
    } else meta.tdAttr = "data-qtip=Empty";
    return value;
  },

  barcodeRenderer: function (value, meta) {
    var record = this.getView().getStore().findRecord("barcode", value);
    return record ? record.getBarcode() : value;
  },

  yesNoRenderer: function (value) {
    return value ? "Yes" : "No";
  },

  _getDataIndex: function (e, view) {
    var xPos = e.getXY()[0];
    var columns = view.getGridColumns();
    var dataIndex;

    for (var colIdx in columns) {
      var leftEdge = columns[colIdx].getPosition()[0];
      var rightEdge = columns[colIdx].getSize().width + leftEdge;

      if (xPos >= leftEdge && xPos <= rightEdge) {
        dataIndex = columns[colIdx].dataIndex;
        break;
      }
    }

    return dataIndex;
  },

  _getSelectedRecords: function (store, groupId) {
    var records = [];

    store.each(function (item) {
      if (item.get(store.groupField) === groupId && item.get("selected")) {
        records.push(item);
      }
    });

    return records;
  },

  _showEditableColumnsMessage: function (gridView, allowedColumns) {
    var columns = this._findColumnsByDataIndex(
      gridView.getGridColumns(),
      allowedColumns
    );
    var columnNames = Ext.Array.pluck(columns, "text")
      .map(function (name) {
        return "<li>" + name + "</li>";
      })
      .join("");

    if (columnNames === "") {
      return;
    }

    var message = Ext.String.format(
      "Only the following columns are editable:<br/><ul>{0}</ul>",
      columnNames
    );

    new Noty({ text: message, type: "warning" }).show();
  },

  _findColumnsByDataIndex: function (columns, allowedColumns) {
    var result = [];

    Ext.Array.each(columns, function (column) {
      Ext.Array.each(allowedColumns, function (allowedColumnDataIndex) {
        if (column.dataIndex === allowedColumnDataIndex) {
          result.push(column);
        }
      });
    });

    return result;
  }
});

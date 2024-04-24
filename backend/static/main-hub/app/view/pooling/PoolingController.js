Ext.define("MainHub.view.pooling.PoolingController", {
  extend: "MainHub.components.BaseGridController",
  alias: "controller.pooling",

  mixins: ["MainHub.grid.SearchInputMixin"],

  config: {
    control: {
      "#": {
        activate: "activateView"
      },
      "#pooling-grid": {
        resize: "resize",
        boxready: "addToolbarButtons",
        itemcontextmenu: "showMenu",
        groupcontextmenu: "showPoolingGroupMenu",
        beforeEdit: "toggleEditors",
        edit: "editRecord"
      },
      "#check-column": {
        beforecheckchange: "selectRecord"
      },
      "#download-benchtop-protocol-button": {
        click: "downloadBenchtopProtocol"
      },
      "#download-pooling-template-button": {
        click: "downloadPoolingTemplate"
      },
      "#search-field": {
        change: "changeFilter"
      },
      "#cancel-button": {
        click: "cancel"
      },
      "#save-button": {
        click: "save"
      }
    }
  },

  showPoolingGroupMenu: function (gridView, node, groupId, e) {
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
      },
      {
        text: "Edit comment",
        margin: "5px 5px 0 5px",
        handler: function () {
          var store = grid.getStore();
          var comment = "";
          var i = 0;
          store.each(function (item) {
            if (item.get(store.groupField) === parseInt(groupId)) {
              comment = item.get("comment");
            }
          });
          Ext.MessageBox.show({
            title: "Edit comment",
            width: 300,
            buttons: Ext.MessageBox.OKCANCEL,
            buttonText: {
              ok: "Save",
              cancel: "Don't save"
            },
            multiline: true,
            value: comment,
            fn: function (btn, text) {
              if (btn == "ok") {
                self.editComment(self, store, parseInt(groupId), text);
                //self.syncStore(store.getId());
              }
            }
          });
        }
      },
      {
        text: "Destroy Pool",
        margin: "5px",
        handler: function () {
          var store = grid.getStore();
          Ext.Msg.show({
            title: "Destroy Pool",
            message: Ext.String.format(
              'Are you sure you want to destroy the pool "Pool_{0}"?',
              groupId
            ),
            buttons: Ext.Msg.YESNO,
            icon: Ext.Msg.QUESTION,
            fn: function (btn) {
              if (btn === "yes") {
                Ext.Ajax.request({
                  url: Ext.String.format(
                    "api/pooling/{0}/destroy_pool/",
                    groupId
                  ),
                  method: "POST",
                  scope: this,
                  success: function (response) {
                    var obj = Ext.JSON.decode(response.responseText);
                    if (obj.success === true) {
                      Ext.getStore("Pooling").reload();
                      new Noty({
                        text: "The pool has been successfully destroyed."
                      }).show();
                    } else {
                      new Noty({
                        text: "An error occurred while destroying the pool.",
                        type: "error"
                      }).show();
                      console.error(response);
                    }
                  },
                  failure: function (response) {
                    new Noty({
                      text: "An error occurred while destroying the pool.",
                      type: "error"
                    }).show();
                    console.error(response);
                  }
                });
              }
            }
          });
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

  addToolbarButtons: function (grid) {
    var toolbar = grid.down('toolbar[dock="bottom"]');

    toolbar.insert(0, {
      type: "button",
      itemId: "download-benchtop-protocol-button",
      text: "Download Benchtop Protocol",
      iconCls: "fa fa-file-excel-o fa-lg"
    });

    toolbar.insert(1, {
      type: "button",
      itemId: "download-pooling-template-button",
      text: "Download Template QC Normalization and Pooling",
      iconCls: "fa fa-file-excel-o fa-lg"
    });
  },

  editComment: function (self, store, groupId, text) {
    Ext.Ajax.request({
      url: Ext.String.format("api/pooling/{0}/edit_comment/", groupId),
      method: "POST",
      scope: self,
      params: {
        data: Ext.JSON.encode({
          newComment: text
        })
      },
      success: function (response) {
        var obj = Ext.JSON.decode(response.responseText);
        if (obj.success) {
          Ext.getStore("Pooling").reload();
          new Noty({ text: "New comment has been saved successfully." }).show();
        } else {
          new Noty({ text: obj.message, type: "error" }).show();
        }
      },
      failure: function (response) {
        new Noty({ text: response.statusText, type: "error" }).show();
        console.error(response);
      }
    });
  },

  toggleEditors: function (editor, context) {
    var record = context.record;
    if (
      record.get("record_type") === "Sample" &&
      (record.get("status") === 2 || record.get("status") === -2)
    ) {
      return false;
    }
  },

  selectRecord: function (cb, rowIndex, checked, record) {
    // Don't select samples which aren't prepared yet
    if (!this._isPrepared(record)) {
      return false;
    }

    // Don't select records from a different pool
    var selectedRecord = record.store.findRecord("selected", true);
    if (selectedRecord) {
      if (record.get("pool") !== selectedRecord.get("pool")) {
        new Noty({
          text: "You can only select libraries from the same pool.",
          type: "warning"
        }).show();
        return false;
      }
    }
  },

  selectUnselectAll: function (grid, groupId, selected) {
    var self = this;
    var store = grid.getStore();
    var selectedRecords = this._getSelectedRecords(store);

    if (selectedRecords.length > 0 && selectedRecords[0].pool !== groupId) {
      new Noty({
        text: "You can only select libraries from the same pool.",
        type: "warning"
      }).show();
      return false;
    }

    store.each(function (item) {
      if (item.get(store.groupField) === groupId && self._isPrepared(item)) {
        item.set("selected", selected);
      }
    });
  },

  editRecord: function (editor, context) {
    var store = editor.grid.getStore();
    var record = context.record;
    var changes = record.getChanges();
    var values = context.newValues;

    // Set Concentration C1
    if (
      Object.keys(changes).indexOf("concentration_c1") === -1 &&
      values.concentration > 0 &&
      values.mean_fragment_size > 0
    ) {
      var concentrationC1 = (
        (values.concentration / (values.mean_fragment_size * 650)) *
        Math.pow(10, 6)
      ).toFixed(1);
      record.set("concentration_c1", concentrationC1);
    }

    // Send the changes to the server
    this.syncStore(store.getId());
  },

  applyToAll: function (gridView, record, dataIndex) {
    var self = this;
    var store = gridView.grid.getStore();
    var allowedColumns = ["concentration_c1"];

    if (dataIndex && allowedColumns.indexOf(dataIndex) !== -1) {
      store.each(function (item) {
        if (
          item.get(store.groupField) === record.get(store.groupField) &&
          item !== record &&
          self._isPrepared(item)
        ) {
          item.set(dataIndex, record.get(dataIndex));
        }
      });

      // Send the changes to the server
      self.syncStore(store.getId());
    } else {
      self._showEditableColumnsMessage(gridView, allowedColumns);
    }
  },

  downloadBenchtopProtocol: function (btn) {
    var store = btn.up("grid").getStore();
    var selectedRecords = this._getSelectedRecords(store);
    var libraries = selectedRecords.filter(function (item) {
      return item.record_type === "Library";
    });

    var samples = selectedRecords.filter(function (item) {
      return item.record_type === "Sample";
    });

    if (libraries.length === 0 && samples.length === 0) {
      new Noty({
        text: "You did not select any libraries.",
        type: "warning"
      }).show();
      return;
    }

    var form = Ext.create("Ext.form.Panel", { standardSubmit: true });
    form.submit({
      url: "api/pooling/download_benchtop_protocol/",
      params: {
        pool_id: selectedRecords[0].pool,
        samples: Ext.JSON.encode(Ext.Array.pluck(samples, "pk")),
        libraries: Ext.JSON.encode(Ext.Array.pluck(libraries, "pk")),
        bp: Ext.JSON.encode(Ext.Array.pluck(libraries, "bp"))
      }
    });
  },

  downloadPoolingTemplate: function (btn) {
    var store = btn.up("grid").getStore();
    var selectedRecords = this._getSelectedRecords(store);
    var libraries = selectedRecords.filter(function (item) {
      return item.record_type === "Library";
    });
    var samples = selectedRecords.filter(function (item) {
      return item.record_type === "Sample";
    });

    if (libraries.length === 0 && samples.length === 0) {
      new Noty({
        text: "You did not select any libraries.",
        type: "warning"
      }).show();
      return;
    }

    var form = Ext.create("Ext.form.Panel", { standardSubmit: true });
    form.submit({
      url: "api/pooling/download_pooling_template/",
      params: {
        samples: Ext.JSON.encode(Ext.Array.pluck(samples, "pk")),
        libraries: Ext.JSON.encode(Ext.Array.pluck(libraries, "pk"))
      }
    });
  },

  _isPrepared: function (item) {
    return (
      item.get("record_type") === "Library" ||
      (item.get("record_type") === "Sample" && item.get("status") === 3)
    );
  },

  _getSelectedRecords: function (store) {
    var records = [];

    store.each(function (item) {
      if (item.get("selected")) {
        records.push({
          pk: item.get("pk"),
          record_type: item.get("record_type"),
          pool: item.get("pool"),
          bp: item.get("mean_fragment_size")
        });
      }
    });

    return records;
  }
});

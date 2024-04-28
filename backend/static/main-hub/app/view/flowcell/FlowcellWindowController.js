Ext.define("MainHub.view.flowcell.FlowcellWindowController", {
  extend: "Ext.app.ViewController",
  alias: "controller.flowcell-window",

  config: {
    control: {
      "#": {
        boxready: "onWindowReady",
        beforeclose: "onWindowClose",
      },
      "#sequencing-kit-field": {
        change: "changeSequencer",
      },
      "#pools-flowcell-grid": {
        render: "initializePoolDragZone",
        itemcontextmenu: "showAdditionalInformationMenu",
      },
      "#flowcell-result-grid": {
        itemcontextmenu: "showUnloadLaneMenu",
      },
      "#sample-sheet-illuminav2-button": {
        click: "createSampleSheetIlluminav2Window",
      },
      "#save-button": {
        click: "save",
      },
    },
  },

  onWindowReady: function () {
    Ext.getStore("lanesStore").removeAll();
    Ext.getStore("poolsStore").reload();
  },

  onWindowClose: function (wnd) {
    Ext.getCmp("pools-flowcell-grid").dragZone.destroy();
  },

  changeSequencer: function (cb, newValue, oldValue) {
    var poolSizesStore = Ext.getStore("PoolSizes");
    var poolSize = poolSizesStore.findRecord(
      "id",
      newValue,
      0,
      false,
      true,
      true
    );

    var lanes = Ext.getCmp("lanes");
    var lanesStore = Ext.getStore("lanesStore");

    lanes.removeAll(true);
    lanesStore.removeAll();

    if (poolSize) {
      var numLanes = poolSize.get("multiplier");
      var laneTileWidth = numLanes === 1 ? 145 : 82;

      for (var i = 0; i < numLanes; i++) {
        lanes.add({
          cls: "lane",
          html: "Lane " + (i + 1),
          id: "lane" + (i + 1),
          width: laneTileWidth,
          listeners: {
            render: this.initializeLaneDropZone,
          },
        });
      }
    }

    // Get original Pool Loaded values
    if (oldValue) {
      Ext.getStore("poolsStore").reload();
    }
  },

  showAdditionalInformationMenu: function (grid, record, item, index, e) {
    e.stopEvent();
    Ext.create("Ext.menu.Menu", {
      plain: true,
      items: [
        {
          text: "Show Additional Information",
          margin: 5,
          handler: function () {
            Ext.create("MainHub.view.flowcell.PoolInfoWindow", {
              title: record.get("name"),
              pool: record.get("pk"),
            });
          },
        },
      ],
    }).showAt(e.getXY());
  },

  clickLane: function (e) {
    var laneId = this.id;
    var grid = Ext.getCmp("flowcell-result-grid");
    var lanesStore = Ext.getStore("lanesStore");

    if ($(this.dom).find(".lane-loaded").length === 1) {
      var record = lanesStore.findRecord("lane_id", laneId);
      // Highlight an active lane in the result grid
      grid.getSelectionModel().select(lanesStore.indexOf(record));
    } else {
      grid.getSelectionModel().deselectAll();
    }
  },

  initializePoolDragZone: function (v) {
    v.dragZone = Ext.create("Ext.dd.DragZone", v.getEl(), {
      onBeforeDrag: function (data, e) {
        var record = v.getStore().getAt(e.recordIndex);
        return !record.isDisabled();
      },

      getDragData: function (e) {
        var sourceEl = $(e.item).find("td div")[0];
        var d;

        if (sourceEl) {
          d = sourceEl.cloneNode(true);
          d.id = Ext.id();
          return (v.dragData = {
            sourceEl: sourceEl,
            repairXY: Ext.fly(sourceEl).getXY(),
            ddel: d,
            poolData: v.getStore().getAt(e.recordIndex).data,
          });
        }
      },

      getRepairXY: function () {
        return this.dragData.repairXY;
      },
    });
  },

  initializeLaneDropZone: function (v) {
    var lanesStore = Ext.getStore("lanesStore");
    var poolsStore = Ext.getStore("poolsStore");
    var sequencingKitId = Ext.getCmp("sequencing-kit-field").getValue();
    var sequencingKit = Ext.getStore("PoolSizes").findRecord(
      "id",
      sequencingKitId,
      0,
      false,
      true,
      true
    );

    // Initialize 'click' event
    v.el.on("click", this.up("window").getController().clickLane);

    function isLoaded(laneId) {
      return lanesStore.findRecord("lane_id", laneId) !== null;
    }

    function isSizeMatch(poolSize) {
      return sequencingKit.get("size") >= poolSize.get("size");
    }

    function isReadLengthOK(pool) {
      if (lanesStore.getCount() > 0) {
        var poolInResultId = lanesStore.getAt(0).get("pool_id");
        var poolInResultRecord = poolsStore.findRecord("pk", poolInResultId);

        if (poolInResultRecord.get("read_length") !== pool.get("read_length")) {
          return false;
        }
      }
      return true;
    }

    function isTargetingSelf(targetLane, pool) {
      var ids = [];
      lanesStore.each(function (record) {
        if (record.get("pool_id") === pool.get("pk")) {
          ids.push(record.get("lane_id"));
        }
      });
      return ids.indexOf(targetLane) !== -1;
    }

    v.dropZone = Ext.create("Ext.dd.DropZone", v.el, {
      getTargetFromEvent: function (e) {
        return e.getTarget();
      },

      onNodeOver: function (target, dd, e, data) {
        var pool = poolsStore.findRecord(
          "name",
          data.poolData.name,
          0,
          false,
          true,
          true
        );
        var poolSize = Ext.getStore("PoolSizes").findRecord(
          "id",
          pool.get("pool_size_id"),
          0,
          false,
          true,
          true
        );
        var laneId = $(target).attr("id").replace("-innerCt", "");
        var proto = Ext.dd.DropZone.prototype;

        if (
          !isLoaded(laneId) &&
          isReadLengthOK(pool) &&
          isSizeMatch(poolSize)
        ) {
          return proto.dropAllowed;
        } else {
          return proto.dropNotAllowed;
        }
      },

      onNodeDrop: function (target, dd, e, data) {
        var pool = poolsStore.findRecord(
          "name",
          data.poolData.name,
          0,
          false,
          true,
          true
        );
        var poolSize = Ext.getStore("PoolSizes").findRecord(
          "id",
          pool.get("pool_size_id"),
          0,
          false,
          true,
          true
        );
        var laneId = $(target).attr("id").replace("-innerCt", "");
        var laneName = $(target).text();
        var message;

        // If a target lane is not loaded
        if (!isLoaded(laneId)) {
          // Is the Read Length the same for all pools
          if (!isReadLengthOK(pool)) {
            new Noty({
              text: "Read Length must be the same for all pools on a flowcell.",
              type: "warning",
            }).show();
            return false;
          }

          if (!isSizeMatch(poolSize)) {
            message = Ext.String.format(
              "Pool with size {0} cannot be fit on a lane with capacity {1}.",
              poolSize.get("size"),
              sequencingKit.get("size")
            );
            new Noty({ text: message, type: "warning" }).show();
            return false;
          }

          // Load the pool on a lane
          lanesStore.add({
            pool_id: pool.get("pk"),
            pool_name: pool.get("name"),
            lane_id: laneId,
            lane_name: laneName,
          });

          pool.set("loaded", pool.get("loaded") + 1);

          // If the pool is fully loaded, don't allow to load it anymore
          if (pool.get("loaded") === pool.get("pool_size")) {
            pool.setDisabled(true);
          }

          // Disable the pool
          if (pool.get("loaded") === poolSize) {
            pool.setDisabled(true);
          }

          Ext.fly(target).addCls("lane-loaded");
          Ext.getCmp("pools-flowcell-grid").getView().refresh();

          return true;
        } else {
          // If a target lane is loaded
          // If a target lane and the loaded pool's lane are not the same
          if (!isTargetingSelf(laneId, pool)) {
            message = Ext.String.format(
              "{0} is already loaded. Please unload it and try again.",
              laneName
            );

            new Noty({ text: message, type: "warning" }).show();
          }
        }

        return false;
      },
    });
  },

  showUnloadLaneMenu: function (grid, record, item, index, e) {
    var me = this;
    e.stopEvent();
    Ext.create("Ext.menu.Menu", {
      plain: true,
      items: [
        {
          text: "Unload Lane",
          margin: 5,
          handler: function () {
            me.unloadLane(grid.getStore(), record);
          },
        },
      ],
    }).showAt(e.getXY());
  },

  unloadLane: function (lanesStore, record) {
    var poolsStore = Ext.getStore("poolsStore");
    var pool = poolsStore.findRecord(
      "pk",
      record.get("pool_id"),
      0,
      false,
      true,
      true
    );

    // Update (increase) Pool Loaded amount
    pool.set("loaded", pool.get("loaded") - 1);

    // If the pool is not fully loaded, allow to load it
    if (pool.get("loaded") !== pool.get("pool_size")) {
      pool.setDisabled(false);
    }

    Ext.fly(record.get("lane_id") + "-innerCt").removeCls("lane-loaded");
    lanesStore.remove(record);

    // Enable Pool for loading
    if (pool.get("pool_size") !== pool.get("loaded")) {
      pool.setDisabled(false);
    }
  },

  createSampleSheetIlluminav2Window: function (btn) {
    var form = btn.up("#flowcell-form");

    if (form.isValid()) {
      Ext.create("MainHub.view.flowcell.SampleSheetIlluminav2Window", {
        mode: "add",
      });
    } else {
      new Noty({
        text:
          "Please fill in all the required fields " +
          "before adding a sample sheet.",
        type: "warning",
      }).show();
    }
  },

  save: function (btn) {
    var me = this;
    var wnd = btn.up("window");
    var lanesStore = Ext.getStore("lanesStore");
    var form = Ext.getCmp("flowcell-form").getForm();
    var laneContainers = Ext.getCmp("lanes").items.items;

    if (!form.isValid()) {
      new Noty({
        text: "Please fill in all the required fields.",
        type: "warning",
      }).show();
      return;
    }

    if (lanesStore.getCount() !== laneContainers.length) {
      new Noty({
        text: "All lanes must be loaded.",
        type: "warning",
      }).show();
      return;
    }

    var data = form.getFieldValues();
    var lanes = lanesStore.data.items.map(function (lane) {
      return {
        name: lane.get("lane_name"),
        pool_id: lane.get("pool_id"),
      };
    });

    if (!form.getFieldValues()["sample_sheet"]) {
      Ext.Msg.show({
        title: "Missing sample sheet",
        message: Ext.String.format(
          "You are trying to save a flowcell without a sample " +
            "sheet.<br>Do you want to save it anyway?"
        ),
        buttons: Ext.Msg.YESNO,
        icon: Ext.Msg.QUESTION,
        fn: function (btn) {
          if (btn === "yes") {
            me._save(wnd, form, data, lanes);
          }
        },
      });
    } else {
      me._save(wnd, form, data, lanes);
    }
  },

  _save: function (wnd, form, data, lanes) {
    wnd.setLoading("Saving...");

    var sample_sheet = null;
    if (data.sample_sheet &&
      data.sample_sheet['sample_sheet_type'] === 'illuminav2'){
      sample_sheet = this._distillSampleSheetIlluminav2(data.sample_sheet);
    }

    form.submit({
      url: "api/flowcells/",
      method: "POST",
      params: {
        data: Ext.JSON.encode({
          flowcell_id: data.flowcell_id,
          pool_size: data.sequencing_kit,
          sample_sheet: sample_sheet,
          lanes: lanes,
        }),
      },

      success: function (f, action) {
        new Noty({ text: "Flowcell has been successfully loaded!" }).show();
        Ext.getStore("Flowcells").reload();
        wnd.close();
      },

      failure: function (f, action) {
        var error = "";
        try {
          var obj = Ext.JSON.decode(action.response.responseText);
          error += obj.message;
          if (obj.hasOwnProperty("errors")) {
            error += "<br/><br/>";
            for (var field in obj.errors) {
              if (obj.errors.hasOwnProperty(field)) {
                error += Ext.String.format("<strong>{0}</strong>", field);
                error += "<ul>";
                for (var i = 0; i < obj.errors[field].length; i++) {
                  error += Ext.String.format(
                    "<li>{0}</li>",
                    obj.errors[field][i]
                  );
                }
                error += "</ul>";
              }
            }
          }
        } catch (e) {
          error = action.response.statusText;
        }

        wnd.setLoading(false);
        new Noty({ text: error, type: "error" }).show();
        console.error(action);
      },
    });
  },

  _distillSampleSheetIlluminav2: function (formValues) {
    // Generate the value for the OverrideCycles parameter
    // from the four separate values for each read
    var OverrideCyclesVal = Object.keys(formValues)
      .filter(function (fieldName) {
        return fieldName.indexOf("OC") == 0;
      })
      .map(function (fieldName) {
        return formValues[fieldName];
      })
      .join(";");

    // If OverrideCyclesVal was set, add it to formValues
    if (OverrideCyclesVal !== ";;;") {
      formValues["SS-BCLConvert_Settings-OverrideCycles"] = OverrideCyclesVal;
    }

    // Convert form values into a structured object using their field names
    sampleSheet = Object.keys(formValues)
      .filter(function (fieldName) {
        return fieldName.indexOf("SS") == 0;
      })
      .reduce(function (newSampleSheet, fieldName) {
        var val = formValues[fieldName];
        if (val) {
          var [sectionTitle, parameterName] = fieldName.slice(3).split("-");
          if (sectionTitle in newSampleSheet) {
            newSampleSheet[sectionTitle][parameterName] = formValues[fieldName];
          } else {
            var newParameter = {};
            newParameter[parameterName] = formValues[fieldName];
            newSampleSheet[sectionTitle] = newParameter;
          }
        }

        return newSampleSheet;
      }, {});

    // Add back sample sheet type
    sampleSheet["sample_sheet_type"] = formValues["sample_sheet_type"];

    return sampleSheet;
  },
});

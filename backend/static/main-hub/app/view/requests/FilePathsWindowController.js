Ext.define("MainHub.view.requests.FilePathsWindowController", {
  extend: "Ext.app.ViewController",
  alias: "controller.requests-filePathsWindow",

  selectedOS: null,
  isEditing: false,
  isAdding: false,

  init: function () {
    this.control({
      "combobox[reference=osComboBox]": {
        change: function (combo, newValue, oldValue) {
          this.selectedOS = newValue;
          var wnd = this.getView();
          var dynamicContainer = wnd.down("#dynamic-container");
          var filePaths = wnd.record.data.filepaths;
          this.generateModifiedFilePaths(filePaths, dynamicContainer);
        }
      },
      "button[text=Add]": {
        click: this.onAddButtonClick
      }
    });

    this.getPaths(this.getView());
  },

  getPaths: function (wnd) {
    var requestNameTextarea = wnd.down("#request-name");
    var dynamicContainer = wnd.down("#dynamic-container");
    var dynamicContainer2 = wnd.down("#dynamic-container-2");

    requestNameTextarea.setText(wnd.record.data.name);
    this.generateModifiedFilePaths(wnd.record.data.filepaths, dynamicContainer);
    this.generateModifiedUserPaths(
      wnd.record.data.metapaths,
      dynamicContainer2
    );

    var os = this.detectOS(navigator.userAgent);
    var osComboBox = this.lookupReference("osComboBox");
    if (osComboBox) {
      osComboBox.setValue(os);
      this.selectedOS = os;
    }
  },

  createAddContainer: function (parentContainer) {
    var addContainer = parentContainer.insert(0, {
      xtype: "container",
      itemId: "add-container",
      padding: "0 5 15 0",
      style: {
        position: "sticky",
        top: 0,
        backgroundColor: "white",
        zIndex: 10
      },
      items: [
        {
          xtype: "textfield",
          itemId: "userPathInputKey",
          margin: "0 0 5 0",
          width: "100%",
          emptyText: "Name",
          listeners: {
            change: function () {
              var wnd = this.getView();
              var userPathKey = wnd.down("#userPathInputKey").getValue();
              var userPathValue = wnd.down("#userPathInputValue").getValue();
              var saveButton = wnd.down("#saveButton");

              saveButton.setDisabled(!userPathKey || !userPathValue);
            },
            scope: this
          }
        },
        {
          xtype: "textfield",
          itemId: "userPathInputValue",
          margin: "0 0 5 0",
          width: "100%",
          emptyText: "Path",
          listeners: {
            change: function () {
              var wnd = this.getView();
              var userPathKey = wnd.down("#userPathInputKey").getValue();
              var userPathValue = wnd.down("#userPathInputValue").getValue();
              var saveButton = wnd.down("#saveButton");

              saveButton.setDisabled(!userPathKey || !userPathValue);
            },
            scope: this
          }
        },
        {
          xtype: "container",
          layout: {
            type: "hbox",
            pack: "end"
          },
          margin: "5 0 0 0",
          items: [
            {
              xtype: "button",
              text: "Save",
              itemId: "saveButton",
              handler: this.onSaveButtonClick,
              scope: this,
              margin: "0 5 0 0",
              disabled: true
            },
            {
              xtype: "button",
              text: "Cancel",
              handler: this.onCancelButtonClick,
              scope: this
            }
          ]
        }
      ]
    });

    addContainer.show();
  },

  onAddButtonClick: function () {
    var wnd = this.getView();
    var dynamicContainer2 = wnd.down("#dynamic-container-2");

    var addContainer = dynamicContainer2.down("#add-container");

    this.isAdding = true;
    this.isEditing = false;

    if (!addContainer) {
      this.createAddContainer(dynamicContainer2);
    } else {
      addContainer.down("#userPathInputKey").setValue("");
      addContainer.down("#userPathInputValue").setValue("");
      addContainer.down("#userPathInputKey").setReadOnly(false);
      addContainer.show();
    }
  },

  onSaveButtonClick: function () {
    var wnd = this.getView();
    var userPathKey = wnd.down("#userPathInputKey").getValue();
    var userPathValue = wnd.down("#userPathInputValue").getValue();
    wnd.down("#userPathInputKey").setReadOnly(false);

    var metapathsObject = wnd.record.data.metapaths;
    var newInputData = {};

    if (this.isAdding) {
      if (metapathsObject.hasOwnProperty(userPathKey)) {
        new Noty({
          text: "A user path with the same name already exists.",
          type: "warning"
        }).show();
        return;
      }
      newInputData[userPathKey] = userPathValue;
      for (var key in metapathsObject) {
        if (key !== "nothing") newInputData[key] = metapathsObject[key];
      }
      this.saveUserPaths(newInputData);
    } else if (this.isEditing) {
      if (
        metapathsObject.hasOwnProperty(userPathKey) &&
        metapathsObject[userPathKey] !== userPathValue
      ) {
        for (var key in metapathsObject) {
          if (key === userPathKey) {
            newInputData[key] = userPathValue;
          } else {
            newInputData[key] = metapathsObject[key];
          }
        }
        this.saveUserPaths(newInputData);
      }
    }

    this.isAdding = false;
    this.isEditing = false;
  },

  onCancelButtonClick: function () {
    var wnd = this.getView();
    var addContainer = wnd.down("#dynamic-container-2").down("#add-container");

    if (addContainer) {
      addContainer.hide();
      addContainer.down("#userPathInputKey").setValue("");
      addContainer.down("#userPathInputValue").setValue("");
      addContainer.down("#userPathInputKey").setReadOnly(false);

      this.isAdding = false;
      this.isEditing = false;
    }
  },

  generateModifiedFilePaths: function (filePaths, container) {
    container.removeAll();
    for (var key in filePaths) {
      if (filePaths.hasOwnProperty(key)) {
        container.add({
          xtype: "container",
          items: [
            {
              xtype: "label",
              text: key,
              style: {
                fontWeight: "bold",
                padding: "4px 8px",
                width: "30%",
                display: "inline-block",
                wordWrap: "break-word",
                verticalAlign: "middle"
              }
            },
            {
              xtype: "label",
              text:
                key == "data" || key == "metadata"
                  ? this.onOSChange(filePaths[key])
                  : filePaths[key],
              style: {
                padding: "8px",
                display: "inline-block",
                width: "70%",
                borderLeft: "1px solid #d4d4d4",
                wordWrap: "break-word",
                verticalAlign: "middle",
                cursor: "copy"
              },
              listeners: {
                render: function (label) {
                  label.getEl().on("click", function () {
                    navigator.clipboard.writeText(label.text);
                    new Noty({
                      text: "File path has been copied to the clipboard.",
                      type: "success"
                    }).show();
                  });
                  label.getEl().on("mouseover", function () {
                    Ext.tip.QuickTipManager.register({
                      target: label.getEl(),
                      text: "Click to copy the file path.",
                      showDelay: 600
                    });
                  });
                  label.getEl().on("mouseout", function () {
                    Ext.tip.QuickTipManager.unregister(label.getEl());
                  });
                }
              }
            }
          ],
          style: {
            width: "100%",
            borderTop: "1px solid #d4d4d4",
            borderBottom: "1px solid #d4d4d4",
            marginBottom: "6px"
          }
        });
      }
    }
  },

  generateModifiedUserPaths: function (userPaths, container) {
    container.removeAll();

    if (
      !userPaths ||
      Object.keys(userPaths).length === 0 ||
      userPaths.hasOwnProperty("nothing")
    ) {
      container.add({
        xtype: "label",
        text: "No User Paths",
        style: {
          padding: "4px 8px",
          display: "inline-block",
          width: "100%",
          textAlign: "center"
        }
      });
    } else {
      for (let key in userPaths) {
        if (userPaths.hasOwnProperty(key)) {
          var recordContainer = Ext.create("Ext.container.Container", {
            xtype: "container",
            style: {
              width: "100%",
              borderTop: "1px solid #d4d4d4",
              borderBottom: "1px solid #d4d4d4",
              marginBottom: "6px",
              position: "relative"
            },
            items: [
              {
                xtype: "label",
                text: key,
                style: {
                  fontWeight: "bold",
                  padding: "8px",
                  width: "30%",
                  display: "inline-block",
                  wordWrap: "break-word",
                  verticalAlign: "middle"
                }
              },
              {
                xtype: "label",
                text:
                  !userPaths[key] || userPaths[key] === ""
                    ? "Empty"
                    : userPaths[key],
                style: {
                  padding: "8px",
                  display: "inline-block",
                  width: "56%",
                  borderLeft: "1px solid #d4d4d4",
                  wordWrap: "break-word",
                  verticalAlign: "middle",
                  cursor: "copy"
                },
                listeners: {
                  render: function (label) {
                    label.getEl().on("click", function () {
                      navigator.clipboard.writeText(label.text);
                      new Noty({
                        text: "User path has been copied to the clipboard.",
                        type: "success"
                      }).show();
                    });
                    label.getEl().on("mouseover", function () {
                      Ext.tip.QuickTipManager.register({
                        target: label.getEl(),
                        text: "Click to copy the user path.",
                        showDelay: 600
                      });
                    });
                    label.getEl().on("mouseout", function () {
                      Ext.tip.QuickTipManager.unregister(label.getEl());
                    });
                  }
                }
              },
              {
                xtype: "button",
                tooltip: "Edit",
                iconCls: "fa fa-pencil",
                style: {
                  position: "absolute",
                  top: "50%",
                  right: "4px",
                  height: "25px",
                  width: "25px",
                  transform: "translateY(-50%)",
                  display: "flex",
                  justifyContent: "center",
                  alignItems: "center",
                  padding: "0px",
                  fontSize: "14px"
                },
                handler: this.editUserPath.bind(this, key, userPaths[key]),
                scope: this
              },
              {
                xtype: "button",
                tooltip: "Delete",
                iconCls: "fa fa-trash",
                style: {
                  position: "absolute",
                  top: "50%",
                  right: "32px",
                  height: "25px",
                  width: "25px",
                  transform: "translateY(-50%)",
                  display: "flex",
                  justifyContent: "center",
                  alignItems: "center",
                  padding: "0px",
                  fontSize: "14px"
                },
                handler: this.deleteUserPath.bind(this, key)
              }
            ]
          });

          container.add(recordContainer);
        }
      }
    }
  },

  saveUserPaths: function (data) {
    var wnd = this.getView();
    Ext.Ajax.request({
      url: "api/requests/" + wnd.record.data.pk + "/put_metapaths/",
      method: "POST",
      jsonData: data,
      success: function (response) {
        var jsonResp = Ext.decode(response.responseText);
        if (jsonResp.success) {
          new Noty({
            text: "The user path has been saved successfully.",
            type: "success"
          }).show();
          wnd.record.data.metapaths = data;
          var dynamicContainer2 = wnd.down("#dynamic-container-2");
          this.generateModifiedUserPaths(data, dynamicContainer2);

          var addContainer = dynamicContainer2.down("#add-container");
          if (addContainer) {
            addContainer.hide();
          }
        } else {
          new Noty({
            text: "Failed to save the user path.",
            type: "error"
          }).show();
        }
      },
      failure: function (response) {
        new Noty({
          text: "An error occurred while saving the user path.",
          type: "error"
        }).show();
      },
      scope: this
    });
  },

  editUserPath: function (key, value) {
    var wnd = this.getView();
    var addContainer = wnd.down("#dynamic-container-2").down("#add-container");

    if (!addContainer) {
      this.createAddContainer(wnd.down("#dynamic-container-2"));
      addContainer = wnd.down("#dynamic-container-2").down("#add-container");
    } else {
      addContainer.show();
    }

    this.isAdding = false;
    this.isEditing = true;

    var userPathInputKey = addContainer.down("#userPathInputKey");
    var userPathInputValue = addContainer.down("#userPathInputValue");
    var saveButton = addContainer.down("#saveButton");

    userPathInputKey.setValue(key);
    userPathInputKey.setReadOnly(true);
    userPathInputValue.setValue(value);
    saveButton.setDisabled(false);
  },

  deleteUserPath: function (key) {
    Ext.Msg.confirm(
      "Confirmation",
      "Are you sure that you want to delete path '" + key + "'?",
      function (choice) {
        if (choice === "yes") {
          var wnd = this.getView();
          var record = wnd.record;
          var userPaths = Ext.apply({}, record.data.metapaths);

          if (userPaths.hasOwnProperty(key)) {
            delete userPaths[key];

            Ext.Ajax.request({
              url: "api/requests/" + record.data.pk + "/put_metapaths/",
              method: "POST",
              jsonData: userPaths,
              success: function (response) {
                var jsonResp = Ext.decode(response.responseText);
                if (jsonResp.success) {
                  new Noty({
                    text: "The user path has been deleted successfully.",
                    type: "success"
                  }).show();

                  wnd.record.data.metapaths = userPaths;
                  var dynamicContainer2 = wnd.down("#dynamic-container-2");
                  this.generateModifiedUserPaths(userPaths, dynamicContainer2);
                } else {
                  new Noty({
                    text: "Failed to delete the user path.",
                    type: "error"
                  }).show();
                }
              },
              failure: function (response) {
                new Noty({
                  text: "An error occurred while deleting the user path.",
                  type: "error"
                }).show();
              },
              scope: this
            });
          }
        }
      },
      this
    );
  },

  onOSChange: function (filePath) {
    var filePathRegex =
      /^\/[A-Za-z0-9_]+\/[A-Za-z0-9_]+\/[A-Za-z0-9_]+\/[A-Za-z0-9_\/.]+$/;
    if (!filePath) {
      return "Empty";
    }
    if (filePathRegex.test(filePath)) {
      var filePathSplit = filePath.split("/").filter(function (element) {
        return element !== "";
      });
      if (this.selectedOS == "Windows") {
        return (
          "\\\\" +
          filePathSplit[0] +
          "\\" +
          filePathSplit[1] +
          "-" +
          filePathSplit[2] +
          "\\" +
          filePathSplit.slice(3).join("\\")
        );
      } else if (this.selectedOS == "macOS") {
        return (
          "smb://" +
          filePathSplit[0] +
          "/" +
          filePathSplit[1] +
          "-" +
          filePathSplit[2] +
          "/" +
          filePathSplit.slice(3).join("/")
        );
      } else return filePath;
    } else {
      return filePath;
    }
  },

  detectOS: function (userAgent) {
    if (/Mac OS X/.test(userAgent)) {
      return "macOS";
    } else if (/Windows NT/.test(userAgent)) {
      return "Windows";
    } else {
      return "Linux";
    }
  }
});

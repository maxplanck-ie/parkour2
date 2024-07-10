Ext.define("MainHub.view.requests.FilepathsWindowController", {
  extend: "Ext.app.ViewController",
  alias: "controller.requests-filepathsWindow",

  selectedOS: null,
  userpathsArray: [],
  isEditing: false,
  isAdding: false,
  currentEditId: null,

  init: function () {
    this.control({
      "combobox[reference=osComboBox]": {
        change: function (combo, newValue, oldValue) {
          var wnd = this.getView();
          var dynamicContainer = wnd.down("#dynamic-container");
          var filepaths = wnd.record.data.filepaths;

          this.selectedOS = newValue;
          this.generateModifiedFilepaths(filepaths, dynamicContainer);
        }
      }
    });

    this.getPaths(this.getView());
  },

  getPaths: function (wnd) {
    var requestNameTextarea = wnd.down("#request-name");
    var dynamicContainer = wnd.down("#dynamic-container");
    var dynamicContainer2 = wnd.down("#dynamic-container-2");

    requestNameTextarea.setText(wnd.record.data.name);

    var filepaths = wnd.record.data.filepaths;
    var userpaths = wnd.record.data.metapaths;
    let updatedUserpathsArray = [];
    let id = 1;

    for (let key in userpaths) {
      if (userpaths.hasOwnProperty(key)) {
        let newObj = {
          pathId: id,
          pathName: key,
          pathValue: userpaths[key]
        };
        updatedUserpathsArray.push(newObj);
        id++;
      }
    }

    this.userpathsArray = updatedUserpathsArray;
    this.generateModifiedFilepaths(filepaths, dynamicContainer);
    this.generateModifiedUserpaths(updatedUserpathsArray, dynamicContainer2);

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
          itemId: "userpathInputKey",
          margin: "0 0 5 0",
          width: "100%",
          emptyText: "Name",
          listeners: {
            change: function () {
              var wnd = this.getView();
              var userpathKey = wnd.down("#userpathInputKey").getValue();
              var userpathValue = wnd.down("#userpathInputValue").getValue();
              var saveButton = wnd.down("#saveButton");

              saveButton.setDisabled(!userpathKey || !userpathValue);
            },
            scope: this
          }
        },
        {
          xtype: "textfield",
          itemId: "userpathInputValue",
          margin: "0 0 5 0",
          width: "100%",
          emptyText: "Path",
          listeners: {
            change: function () {
              var wnd = this.getView();
              var userpathKey = wnd.down("#userpathInputKey").getValue();
              var userpathValue = wnd.down("#userpathInputValue").getValue();
              var saveButton = wnd.down("#saveButton");

              saveButton.setDisabled(!userpathKey || !userpathValue);
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
    this.currentEditId = null;

    if (!addContainer) {
      this.createAddContainer(dynamicContainer2);
    } else {
      addContainer.down("#userpathInputKey").setValue("");
      addContainer.down("#userpathInputValue").setValue("");
      addContainer.show();
    }
  },

  onSaveButtonClick: function () {
    var wnd = this.getView();
    var userpathInputKey = wnd.down("#userpathInputKey").getValue();
    var userpathInputValue = wnd.down("#userpathInputValue").getValue();

    var newInputData = new Map();
    var userpathsArray = this.userpathsArray.slice();

    if (this.isAdding) {
      let userpaths = wnd.record.data.metapaths;
      if (userpaths.hasOwnProperty(userpathInputKey)) {
        new Noty({
          text: "A user path with the same name already exists.",
          type: "warning"
        }).show();
        return;
      }
      newInputData.set(userpathInputKey, userpathInputValue);
      for (let i = 0; i < userpathsArray.length; i++) {
        if (userpathsArray[i].pathValue !== null)
          newInputData.set(
            userpathsArray[i].pathName,
            userpathsArray[i].pathValue
          );
      }
    } else if (this.isEditing) {
      let currentEditId = this.currentEditId;
      for (let i = 0; i < userpathsArray.length; i++) {
        if (userpathsArray[i].pathId === currentEditId) {
          newInputData.set(userpathInputKey, userpathInputValue);
        } else {
          newInputData.set(
            userpathsArray[i].pathName,
            userpathsArray[i].pathValue
          );
        }
      }
    }

    this.userpathsArray = Array.from(newInputData).map((entry, index) => {
      return {
        pathId: index + 1,
        pathName: entry[0],
        pathValue: entry[1]
      };
    });

    this.saveUserpaths(Object.fromEntries(newInputData));

    this.isAdding = false;
    this.isEditing = false;
    this.currentEditId = null;
  },

  onCancelButtonClick: function () {
    var wnd = this.getView();
    var addContainer = wnd.down("#dynamic-container-2").down("#add-container");

    if (addContainer) {
      addContainer.hide();
      addContainer.down("#userpathInputKey").setValue("");
      addContainer.down("#userpathInputValue").setValue("");

      this.isAdding = false;
      this.isEditing = false;
      this.currentEditId = null;
    }
  },

  generateModifiedFilepaths: function (filepaths, container) {
    container.removeAll();

    for (let key in filepaths) {
      if (filepaths.hasOwnProperty(key)) {
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
                  ? this.onOSChange(filepaths[key])
                  : filepaths[key],
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

  generateModifiedUserpaths: function (userpathsArray, container) {
    container.removeAll();

    if (userpathsArray.filter((item) => item.pathValue !== null).length === 0) {
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
      userpathsArray.forEach((obj) => {
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
              text: obj.pathName,
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
                !obj.pathValue || obj.pathValue === ""
                  ? "Empty"
                  : obj.pathValue,
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
              handler: this.editUserpath.bind(this, obj.pathId),
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
              handler: this.deleteUserpath.bind(this, obj.pathId)
            }
          ]
        });

        container.add(recordContainer);
      });
    }
  },

  saveUserpaths: function (userpaths) {
    var wnd = this.getView();

    Ext.Ajax.request({
      url: "api/requests/" + wnd.record.data.pk + "/put_metapaths/",
      method: "POST",
      jsonData: userpaths,
      success: function (response) {
        var jsonResp = Ext.decode(response.responseText);
        var dynamicContainer2 = wnd.down("#dynamic-container-2");
        var addContainer = dynamicContainer2.down("#add-container");

        if (jsonResp.success) {
          new Noty({
            text: "The user path has been saved successfully.",
            type: "success"
          }).show();

          wnd.record.data.metapaths = userpaths;

          let updatedUserpathsArray = [];
          let id = 1;

          for (let key in userpaths) {
            if (userpaths.hasOwnProperty(key)) {
              let newObj = {
                pathId: id,
                pathName: key,
                pathValue: userpaths[key]
              };
              updatedUserpathsArray.push(newObj);
              id++;
            }
          }

          this.userpathsArray = updatedUserpathsArray;
          this.generateModifiedUserpaths(
            updatedUserpathsArray,
            dynamicContainer2
          );

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

  editUserpath: function (pathId) {
    var wnd = this.getView();
    var addContainer = wnd.down("#dynamic-container-2").down("#add-container");

    if (!addContainer) {
      this.createAddContainer(wnd.down("#dynamic-container-2"));
      addContainer = wnd.down("#dynamic-container-2").down("#add-container");
    } else {
      addContainer.show();
    }

    var userpathInputKey = addContainer.down("#userpathInputKey");
    var userpathInputValue = addContainer.down("#userpathInputValue");
    var saveButton = addContainer.down("#saveButton");

    this.isAdding = false;
    this.isEditing = true;
    this.currentEditId = pathId;

    var userpath = this.userpathsArray.find((obj) => obj.pathId === pathId);

    userpathInputKey.setValue(userpath.pathName);
    userpathInputValue.setValue(userpath.pathValue);
    saveButton.setDisabled(false);
  },

  deleteUserpath: function (pathId) {
    var userpathsArray = this.userpathsArray;
    var userpathIndex = userpathsArray.findIndex(
      (obj) => obj.pathId === pathId
    );
    var userpathKey = userpathsArray[userpathIndex].pathName;

    Ext.Msg.confirm(
      "Confirmation",
      "Are you sure that you want to delete path '" + userpathKey + "'?",
      function (choice) {
        if (choice === "yes") {
          var wnd = this.getView();
          var record = wnd.record;
          var userpaths = Ext.apply({}, record.data.metapaths);

          if (userpaths.hasOwnProperty(userpathKey)) {
            delete userpaths[userpathKey];

            Ext.Ajax.request({
              url: "api/requests/" + record.data.pk + "/put_metapaths/",
              method: "POST",
              jsonData: userpaths,
              success: function (response) {
                var jsonResp = Ext.decode(response.responseText);
                var dynamicContainer2 = wnd.down("#dynamic-container-2");

                if (jsonResp.success) {
                  new Noty({
                    text: "The user path has been deleted successfully.",
                    type: "success"
                  }).show();

                  wnd.record.data.metapaths = userpaths;

                  let updatedUserpathsArray = [];
                  let id = 1;

                  for (let key in userpaths) {
                    if (userpaths.hasOwnProperty(key)) {
                      let newObj = {
                        pathId: id,
                        pathName: key,
                        pathValue: userpaths[key]
                      };
                      updatedUserpathsArray.push(newObj);
                      id++;
                    }
                  }

                  this.userpathsArray = updatedUserpathsArray;
                  this.generateModifiedUserpaths(
                    updatedUserpathsArray,
                    dynamicContainer2
                  );
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

  onOSChange: function (filepath) {
    var filepathRegex =
      /^\/[A-Za-z0-9_]+\/[A-Za-z0-9_]+\/[A-Za-z0-9_]+\/[A-Za-z0-9_\/.]+$/;
    if (!filepath) {
      return "Empty";
    }
    if (filepathRegex.test(filepath)) {
      var filepathSplit = filepath.split("/").filter(function (element) {
        return element !== "";
      });
      if (this.selectedOS == "Windows") {
        return (
          "\\\\" +
          filepathSplit[0] +
          "\\" +
          filepathSplit[1] +
          "-" +
          filepathSplit[2] +
          "\\" +
          filepathSplit.slice(3).join("\\")
        );
      } else if (this.selectedOS == "macOS") {
        return (
          "smb://" +
          filepathSplit[0] +
          "/" +
          filepathSplit[1] +
          "-" +
          filepathSplit[2] +
          "/" +
          filepathSplit.slice(3).join("/")
        );
      } else return filepath;
    } else {
      return filepath;
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

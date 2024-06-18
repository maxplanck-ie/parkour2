Ext.define("MainHub.view.requests.FilePathsWindowController", {
  extend: "Ext.app.ViewController",
  alias: "controller.requests-filePathsWindow",

  selectedOS: null,

  init: function () {
    this.control({
      "combobox[reference=osComboBox]": {
        change: this.osComboBoxChange
      },
      "button[text=Add]": {
        click: this.onAddButtonClick
      },
      "button[text=Save]": {
        click: this.onSaveButtonClick
      },
      "button[text=Cancel]": {
        click: this.onCancelButtonClick
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

  onAddButtonClick: function () {
    var wnd = this.getView();
    var dynamicContainer2 = wnd.down("#dynamic-container-2");
    dynamicContainer2.removeAll();

    dynamicContainer2.add({
      xtype: "textfield",
      itemId: "userPathInputKey",
      margin: "10 0 5 0",
      width: "100%",
      emptyText: "User path's key"
    });

    dynamicContainer2.add({
      xtype: "textfield",
      itemId: "userPathInputValue",
      margin: "0 0 5 0",
      width: "100%",
      emptyText: "User path's value"
    });

    dynamicContainer2.add({
      xtype: "container",
      layout: {
        type: "hbox",
        pack: "end"
      },
      margin: "10 0 0 0",
      items: [
        {
          xtype: "button",
          text: "Save",
          handler: this.onSaveButtonClick,
          margin: "0 10 0 0"
        },
        {
          xtype: "button",
          text: "Cancel",
          handler: this.onCancelButtonClick
        }
      ]
    });
  },

  onSaveButtonClick: function () {
    var wnd = this.getView();
    var userPathKey = wnd.down("#userPathInputKey").getValue();
    var userPathValue = wnd.down("#userPathInputValue").getValue();

    var newInputData = {
      [userPathKey]: userPathValue
    };
    Ext.apply(newInputData, wnd.record.data.metapaths);

    Ext.Ajax.request({
      url: "api/requests/" + wnd.record.data.pk + "/put_metapaths/",
      method: "POST",
      jsonData: newInputData,
      success: function (response) {
        var jsonResp = Ext.decode(response.responseText);
        if (jsonResp.success) {
          new Noty({
            text: "The user path has been saved successfully.",
            type: "success"
          }).show();
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
      }
    });
  },

  onCancelButtonClick: function () {
    var wnd = this.getView();
  },

  osComboBoxChange: function (combo, newValue, oldValue) {
    this.selectedOS = newValue;
    var wnd = this.getView();
    var dynamicContainer = wnd.down("#dynamic-container");
    var filePaths = wnd.record.data.filepaths;
    this.generateModifiedFilePaths(filePaths, dynamicContainer);
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
                verticalAlign: "middle",
                lineHeight: "1.5"
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
                      text: "File path has been copied to the clipboard."
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

    if (!userPaths || Object.keys(userPaths).length === 0) {
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
      for (var key in userPaths) {
        if (userPaths.hasOwnProperty(key)) {
          container.add({
            xtype: "container",
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
                  verticalAlign: "middle",
                  lineHeight: "1.5"
                }
              },
              {
                xtype: "label",
                text: userPaths[key],
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
                        text: "User path has been copied to the clipboard."
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
    }
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

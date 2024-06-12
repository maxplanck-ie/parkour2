Ext.define("MainHub.view.requests.FilePathsWindowController", {
  extend: "Ext.app.ViewController",
  alias: "controller.requests-filePathsWindow",

  selectedOS: null,

  init: function () {
    this.control({
      "combobox[reference=osComboBox]": {
        change: this.osComboBoxChange
      }
    });
  },

  getFilePaths: function (wnd) {
    var requestNameTextarea = wnd.down("#request-name");
    var dynamicContainer = wnd.down("#dynamic-container");

    this.generateModifiedPaths(wnd.record.data.filepaths, dynamicContainer);

    requestNameTextarea.setText(wnd.record.data.name);

    var os = this.detectOS(navigator.userAgent);
    var osComboBox = this.lookupReference("osComboBox");
    if (osComboBox) {
      osComboBox.setValue(os);
      this.selectedOS = os;
    }
  },

  generateModifiedPaths: function (filePaths, container) {
    container.removeAll();

    for (var key in filePaths) {
      if (filePaths.hasOwnProperty(key)) {
        container.add({
          xtype: "container",
          items: [
            {
              xtype: "label",
              text: key,
              margin: "10 10 10 0",
              style: {
                fontWeight: "bold",
                padding: "0px 5px",
                borderRight: "1px solid #d4d4d4",
                width: "30%",
                display: "inline-block",
                wordWrap: "break-word"
              }
            },
            {
              xtype: "label",
              text:
                key == "data" || key == "metadata"
                  ? this.getModifiedFilePath(filePaths[key])
                  : filePaths[key],
              margin: "10 0 0 0",
              style: {
                padding: "0px 5px",
                display: "inline-block",
                width: "60%",
                wordWrap: "break-word",
                cursor: "copy"
              },
              listeners: {
                render: function (label) {
                  label.getEl().on("click", function () {
                    navigator.clipboard.writeText(label.text);
                    new Noty({ text: "File path copied successfully." }).show();
                  });
                  label.getEl().on("mouseover", function () {
                    Ext.tip.QuickTipManager.register({
                      target: label.getEl(),
                      text: "Click to copy",
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
            marginBottom: "5px"
          }
        });
      }
    }
  },

  osComboBoxChange: function (combo, newValue, oldValue) {
    this.selectedOS = newValue;
    var wnd = this.getView();
    var dynamicContainer = wnd.down("#dynamic-container");
    var filePaths = wnd.record.data.filepaths;
    this.generateModifiedPaths(filePaths, dynamicContainer);
  },

  getModifiedFilePath: function (filePath) {
    var filePathRegex =
      /^\/[A-Za-z0-9_]+\/[A-Za-z0-9_]+\/[A-Za-z0-9_]+\/[A-Za-z0-9_\/.]+$/;
    if (!filePath) {
      return "...";
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

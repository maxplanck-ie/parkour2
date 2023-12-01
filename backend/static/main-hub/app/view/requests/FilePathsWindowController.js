Ext.define("MainHub.view.requests.FilePathsWindowController", {
  extend: "Ext.app.ViewController",
  alias: "controller.requests-filePathsWindow",

  config: {
    control: {
      "#": {
        afterrender: "onAfterRender",
      },
    },
  },

  onAfterRender: function (wnd) {
    var requestNameTextarea = wnd.down("#request-name");
    var dynamicContainer = wnd.down("#dynamic-container");

    for (var key in wnd.record.data.filepaths) {
      if (wnd.record.data.filepaths.hasOwnProperty(key)) {
        dynamicContainer.add({
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
                wordWrap: "break-word",
              },
            },
            {
              xtype: "label",
              text: wnd.record.data.filepaths[key] || "...",
              margin: "10 0 0 0",
              style: {
                padding: "0px 5px",
                display: "inline-block",
                width: "60%",
                wordWrap: "break-word",
                cursor: "copy",
              },
              listeners: {
                render: function (label) {
                  label.getEl().on("click", function () {
                    navigator.clipboard.writeText(label.text);
                  });
                  label.getEl().on("mouseover", function () {
                    Ext.tip.QuickTipManager.register({
                      target: label.getEl(),
                      text: "Click to copy",
                      showDelay: 600,
                    });
                  });
                  label.getEl().on("mouseout", function () {
                    Ext.tip.QuickTipManager.unregister(label.getEl());
                  });
                },
              },
            },
          ],
          style: {
            width: "100%",
            borderTop: "1px solid #d4d4d4",
            borderBottom: "1px solid #d4d4d4",
            marginBottom: "5px",
          },
        });
      }
    }
    requestNameTextarea.setText(wnd.record.data.name);
  },
});

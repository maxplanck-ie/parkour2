Ext.define("MainHub.view.invoicing.UploadReportsWindow", {
  extend: "Ext.window.Window",

  title: "Upload Reports",
  height: 190,
  width: 500,

  modal: true,
  resizable: false,
  autoShow: true,
  layout: "fit",

  items: [
    {
      layout: {
        type: "vbox",
        align: "stretch"
      },
      items: [
        {
          xtype: "parkourmonthpicker",
          itemId: "upload-report-month-picker",
          fieldLabel: "Select Month",
          margin: "10px 10px 5px 10px",
          allowBlank: false
        },
        {
          xtype: "filefield",
          itemId: "file-field",
          fieldLabel: "Browse Report",
          labelWidth: 100,
          msgTarget: "side",
          buttonText: "Select",
          margin: "5px 10px 10px 10px",
          allowBlank: false
        }
      ]
    }
  ],

  dockedItems: [
    {
      xtype: "toolbar",
      dock: "bottom",
      items: [
        "->",
        {
          xtype: "button",
          itemId: "upload-button",
          text: "Upload",
          width: 80,
          handler: function () {
            var window = this.up("window");
            var fileField = window.down("#file-field");
            var monthPicker = window.down("#upload-report-month-picker");

            if (!fileField.getValue()) {
              new Noty({
                text: "Please select the report file.",
                type: "warning"
              }).show();
            }
            if (!monthPicker.getValue()) {
              new Noty({
                text: "Please select the month.",
                type: "warning"
              }).show();
            }
            if (!fileField.getValue() || !monthPicker.getValue()) {
              return;
            }

            var reportPayload = new FormData();
            reportPayload.append("report", fileField.fileInputEl.dom.files[0]);
            reportPayload.append(
              "month",
              Ext.Date.format(monthPicker.getValue(), "Y-m")
            );

            Ext.Ajax.request({
              url: "api/invoicing/upload/",
              method: "POST",
              rawData: reportPayload,
              headers: {
                "Content-Type": null
              },
              success: function (response) {
                window.close();
                new Noty({
                  text: "Report has been successfully uploaded.",
                  type: "success"
                }).show();
              },
              failure: function (response) {
                window.close();
                new Noty({
                  text: "Error while uploading the report.",
                  type: "error"
                }).show();
              }
            });
          }
        },
        {
          xtype: "button",
          itemId: "cancel-button",
          text: "Cancel",
          width: 80,
          handler: function () {
            var window = this.up("window");
            window.close();
          }
        }
      ]
    }
  ]
});

Ext.define("MainHub.view.invoicing.ViewUploadedReportsWindow", {
  extend: "Ext.window.Window",

  title: "View Uploaded Reports",
  height: 150,
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
          itemId: "view-report-month-picker",
          fieldLabel: "Select Month",
          margin: "10px",
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
          text: "View",
          width: 80,
          handler: function () {
            var window = this.up("window");
            var monthPicker = window.down("#view-report-month-picker");

            if (!monthPicker.getValue()) {
              new Noty({
                text: "Please select the month.",
                type: "warning"
              }).show();
              return;
            }

            Ext.Ajax.request({
              url: "/api/invoicing/billing_periods/",
              disableCaching: false,
              method: "GET",
              success: function (response) {
                var responseData = Ext.decode(response.responseText);
                var reportUrl = "";

                Ext.Array.each(responseData, function (item) {
                  if (
                    item.value[0] == monthPicker.getValue().getFullYear() &&
                    item.value[1] == monthPicker.getValue().getMonth() + 1
                  ) {
                    reportUrl = item.report_url;
                    return false;
                  }
                });

                if (reportUrl) {
                  var link = document.createElement("a");
                  link.href = reportUrl;
                  link.download = reportUrl.substr(
                    reportUrl.lastIndexOf("/") + 1
                  );
                  link.click();
                  new Noty({
                    text: "Report for the month is downloaded successfully.",
                    type: "success"
                  }).show();
                } else {
                  new Noty({
                    text: "No report found for the selected month.",
                    type: "warning"
                  }).show();
                }
              },
              failure: function (response) {
                new Noty({
                  text: "Error occurred while fetching report data.",
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

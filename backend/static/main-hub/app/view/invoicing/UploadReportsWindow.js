Ext.define("MainHub.view.invoicing.UploadReportsWindow", {
  extend: "Ext.window.Window",

  title: "Upload Reports",
  height: 595,
  width: 800,

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
          itemId: "start-month-picker",
          fieldLabel: "Month",
          margin: "0 15px 0 0"
        },
        {
          xtype: "filefield",
          name: "file",
          fieldLabel: "File",
          labelWidth: 100,
          msgTarget: "side",
          allowBlank: false,
          buttonText: "Select"
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
          iconCls: "fa fa-floppy-o fa-lg",
          handler: function () {
            var form = this.up("form").getForm();
            var uploadWindow = this.up("window"); // Get the reference to the upload window
            if (form.isValid()) {
              form.submit({
                url: "upload.php", // URL to submit the form data
                waitMsg: "Uploading your file...",
                success: function (fp, o) {
                  Ext.Msg.alert(
                    "Success",
                    'Your file "' + o.result.file + '" has been uploaded.'
                  );
                  billingPeriodCb.getStore().reload();
                  uploadWindow.close(); // Close the upload window upon success
                },
                failure: function (fp, o) {
                  Ext.Msg.alert(
                    "Failure",
                    'Your file "' + o.result.file + '" could not be uploaded.'
                  );
                }
              });
            } else {
              Ext.Msg.alert("Warning", "You did not select any file.");
            }
          }
        },
        {
          xtype: "button",
          itemId: "cancel-button",
          text: "Cancel",
          iconCls: "fa fa-floppy-o fa-lg"
        }
      ]
    }
  ]
});

// Ext.define("E", {
//   extend: "Ext.window.Window",
//   xtype: "fileuploadwindow",

//   // Define properties
//   config: {
//     month: null // Add a config property to store the selected month
//   },

//   onFileUpload: function () {
//     var uploadWindow = this;
//     var form = this.down("form").getForm();
//     var month = this.getMonth(); // Get the selected month from config

//     if (!form.isValid()) {
//       new Noty({
//         text: "You did not select any file.",
//         type: "warning"
//       }).show();
//       return;
//     }

//     form.submit({
//       url: btn.uploadUrl,
//       method: "POST",
//       waitMsg: "Uploading...",
//       params: {
//         month: month // Use the selected month here
//       },
//       success: function (f, action) {
//         new Noty({ text: "Report has been successfully uploaded." }).show();
//         billingPeriodCb.getStore().reload();
//         uploadWindow.close();
//       }
//     });
//   }
// });

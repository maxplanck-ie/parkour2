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
          itemId: "upload-month-picker",
          fieldLabel: "Month",
          margin: "0 15px 0 0"
        },
        {
          xtype: "filefield",
          name: "file",
          itemId: "file-field",
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
            var window = this.up("window");
            var fileField = window.down("#file-field");
            var monthPicker = this.up("window").down("#upload-month-picker");

            var form = Ext.create("Ext.form.Panel", {
              standardSubmit: false,
              hidden: true,
              items: [fileField]
            });

            var formData = new FormData();
            formData.append("report", fileField.fileInputEl.dom.files[0]);
            formData.append(
              "month",
              Ext.Date.format(monthPicker.getValue(), "m.Y")
            );

            Ext.Ajax.request({
              url: "api/invoicing/upload/",
              method: "POST",
              rawData: formData,
              headers: {
                "Content-Type": null
              },
              success: function (response) {
                Ext.toast({
                  html: "Report has been successfully uploaded.",
                  title: "Success",
                  align: "t",
                  closable: true,
                  slideInDuration: 400,
                  minWidth: 400
                });
                window.close();
              },
              failure: function (response) {
                Ext.toast({
                  html: "Failed to upload the report.",
                  title: "Error",
                  align: "t",
                  closable: true,
                  slideInDuration: 400,
                  minWidth: 400
                });
              }
            });
          }
        },
        {
          xtype: "button",
          itemId: "cancel-button",
          text: "Cancel",
          iconCls: "fa fa-floppy-o fa-lg",
          handler: function () {}
        }
      ]
    }
  ]
});

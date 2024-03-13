Ext.define("MainHub.view.invoicing.ViewUploadedReportsWindow", {
  extend: "Ext.window.Window",

  title: "View Uploaded Reports",
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
          iconCls: "fa fa-floppy-o fa-lg",
          handler: function () {}
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

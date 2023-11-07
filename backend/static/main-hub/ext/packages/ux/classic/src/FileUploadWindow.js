Ext.define('Ext.ux.FileUploadWindow', {
  extend: 'Ext.window.Window',
  alias: 'widget.fileuploadwindow',

  title: 'Upload file',
  width: 450,
  modal: true,
  autoShow: true,

  fileFieldName: 'file',

  initComponent: function () {
    var me = this;

    me.items = [{
      xtype: 'form',
      items: [{
        xtype: 'filefield',
        name: me.fileFieldName,
        fieldLabel: 'File',
        labelWidth: 50,
        buttonText: 'Select',
        allowBlank: false,
        width: 413,
        margin: 15,
        listeners: {
          change: function (fld, value) {
            fld.setRawValue(value.replace(/C:\\fakepath\\/g, ''));
          }
        }
      }]
    }];

    me.buttons = [
      {
        text: 'Upload',
        handler: function () {
          this.up('window').onFileUpload();
        }
      },
      {
        text: 'Cancel',
        handler: function () {
          this.up('window').close();
        }
      }
    ];

    this.callParent(arguments);
  }
});

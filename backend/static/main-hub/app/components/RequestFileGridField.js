Ext.define('MainHub.components.RequestFileGridField', {
  extend: 'Ext.form.FieldContainer',
  alias: 'widget.requestfilegridfield',

  requires: ['Ext.ux.MultiFileField'],

  store: '',
  uploadFileUrl: '',
  getFileUrl: '',

  initComponent: function () {
    var me = this;

    me.items = [{
      xtype: 'grid',
      cls: 'request-filegrid',
      height: 155,
      viewConfig: {
        loadMask: false,
        stripeRows: false
      },
      sortableColumns: false,
      enableColumnMove: false,
      enableColumnResize: false,
      enableColumnHide: false,
      columns: {
        items: [{
          text: 'Name',
          dataIndex: 'name',
          flex: 1,
          cls: 'request-file-header'
        },
        {
          text: 'Size',
          dataIndex: 'size',
          width: 100,
          cls: 'request-file-header',
          renderer: function (val) {
            var dim = '';
            var KB = 1000;
            var MB = 1000 * 1000;
            val = parseInt(val);

            if (val >= KB && val < MB) {
              val = (val / KB).toFixed(2);
              dim = ' KB';
            } else if (val >= MB) {
              val = (val / MB).toFixed(2);
              dim = ' MB';
            } else {
              val = val.toString();
              dim = ' bytes';
            }

            return val + dim;
          }
        },
        {
          width: 36,
          dataIndex: 'path',
          xtype: 'templatecolumn',
          cls: 'request-file-header',
          tpl: '<a href="{path}" download><img src="/static/main-hub/resources/images/download.png"></a>'
        },
        {
          xtype: 'actioncolumn',
          width: 36,
          align: 'center',
          cls: 'request-file-header',
          items: [{
            icon: '/static/main-hub/resources/images/delete.png',
            tooltip: 'Delete',
            handler: me.deleteFile
          }]
        }
        ]
      },
      store: me.store,

      dockedItems: [{
        xtype: 'toolbar',
        dock: 'bottom',
        padding: '4px 0 4px 8px',
        items: [
          {
            xtype: 'label',
            html: '<b>Hint:</b> Use this field to attach relevant file(s) to the request, ' +
                  'e.g. Bioanalyzer/Tapestation profiles, <i>etc</i>.',
            width: 235,
            style: "font-size:10px; line-height:normal;"
          },
          '->',
          {
            xtype: 'button',
            text: 'Add files',
            padding: 0,
            height: 28,
            width: 70,
            handler: function () {
              Ext.widget({
                xtype: 'window',
                title: 'Upload files',
                width: 450,
                autoShow: true,
                modal: true,
  
                items: [{
                  xtype: 'form',
                  items: [{
                    xtype: 'multifilefield',
                    name: 'files',
                    fieldLabel: 'Files',
                    labelWidth: 50,
                    buttonText: 'Select',
                    allowBlank: false,
                    width: 413,
                    margin: 15,
                    listeners: {
                      change: function (field) {
                        // Check that none of the files to be uploaded is bigger than 10 MB
                        var inputFiles = field.fileInputEl.dom.files;

                        Ext.each(inputFiles,
                          function (f, i) {

                            var size_limit = 10 * 1024 * 1024;
                    
                            if (f.size > size_limit) {
                              
                              // Create notification
                              new Noty({
                                text: 'One or more files is > 10 MB. A file cannot be > 10 Mb.',
                                type: 'error'
                              }).show();
                              
                              // Reset field to empty
                              field.setRawValue("");
                              return false;
                            }
                          })
                      }
                    }
                  }]
                }],
                bbar: [
                  {
                    xtype: 'label',
                    html: '<b>Hint:</b> Multiple file selection is possible, < 10 MB per file',
                    style: "font-size:10px; line-height:normal"
                  },
                  '->',
                  {
                    text: 'Upload',
                    handler: me.uploadFiles,
                    uploadFileUrl: me.uploadFileUrl,
                    getFileUrl: me.getFileUrl,
                    grid: me.down('grid')
                  }
                ]
              });
            }
          }
        ]
    }]
    }];

    me.callParent(arguments);
  },

  uploadFiles: function (btn) {
    var wnd = btn.up('window');
    var form = wnd.down('form').getForm();
    var uploadFileUrl = btn.uploadFileUrl;
    var grid = btn.grid;

    if (!form.isValid()) {
      new Noty({
        text: 'You did not select any files.',
        type: 'warning'
      }).show();
      return;
    }

    form.submit({
      url: uploadFileUrl,
      method: 'POST',
      waitMsg: 'Uploading...',
      params: Ext.JSON.encode(form.getFieldValues()),
      success: function (f, action) {
        var obj = Ext.JSON.decode(action.response.responseText);

        if (obj.success && obj.fileIds.length > 0) {
          Ext.Ajax.request({
            url: 'api/requests/get_files_after_upload/',
            method: 'GET',
            timeout: 1000000,
            scope: this,
            params: {
              'file_ids': Ext.JSON.encode(obj.fileIds)
            },
            success: function (response) {
              var obj = Ext.JSON.decode(response.responseText);
              if (obj.success) {
                grid.getStore().add(obj.data);
              } else {
                new Noty({ text: response.statusText, type: 'error' }).show();
                console.error(response);
              }
            }
          });
        } else {
          new Noty({ text: obj.message, type: 'error' }).show();
        }
        wnd.close();
      },
      failure: function (f, action) {
        var errorMsg = (action.failureType === 'server') ? 'Server error.' : 'Error.';
        new Noty({ text: errorMsg, type: 'error' }).show();
        console.error(action.response);
        wnd.close();
      }
    });
  },

  deleteFile: function (view, rowIndex, colIndex, item, e, record) {
    view.up().getStore().removeAt(rowIndex);
  },

  getValue: function () {
    return Ext.pluck(this.down('grid').getStore().data.items, 'id');
  }
});

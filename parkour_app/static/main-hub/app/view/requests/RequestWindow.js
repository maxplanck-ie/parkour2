Ext.define('MainHub.view.requests.RequestWindow', {
  extend: 'Ext.window.Window',
  requires: [
    'MainHub.view.requests.RequestWindowController',
    'MainHub.view.libraries.LibraryWindow',
    'MainHub.view.libraries.BatchAddWindow',
    'Ext.ux.FileGridField'
  ],
  controller: 'requests-requestwindow',

  height: 530,
  width: 850,
  modal: true,
  resizable: false,

  items: [{
    xtype: 'container',
    layout: {
      type: 'table',
      columns: 2
    },
    items: [
      {
        border: 0,
        padding: 15,
        width: 500,
        items: [
          {
            xtype: 'form',
            id: 'request-form',
            itemId: 'request-form',
            layout: 'anchor',
            border: 0,
            defaultType: 'textfield',
            defaults: {
              submitEmptyText: false,
              labelWidth: 80,
              anchor: '100%'
            },
            items: [
              {
                xtype: 'combobox',
                itemId: 'cost-unit-cb',
                name: 'cost_unit',
                queryMode: 'local',
                valueField: 'id',
                displayField: 'name',
                fieldLabel: 'Cost Unit',
                emptyText: 'Cost Unit',
                allowBlank: USER.is_staff,
                forceSelection: true,
                store: 'CostUnits'
              },
              {
                name: 'description',
                xtype: 'textarea',
                fieldLabel: 'Description',
                emptyText: 'Description',
                allowBlank: false,
                height: 125
              },
              {
                xtype: 'filegridfield',
                fieldLabel: 'Files',
                store: 'requestFilesStore',
                uploadFileUrl: 'api/requests/upload_files/'

              }
            ]
          },
          {
            id: 'uploadedDeepSeqRequest',
            border: 0,
            html: 'Signed Deep Sequencing Request ' +
                    '<sup><strong><span class="request-field-tooltip" tooltip-text="' +
                      '1. Save the request.<br/>' +
                      '2. Download the Deep Sequencing Request blank using the download button below.<br/>' +
                      '3. Print and sign it.<br/>' +
                      '4. Scan the blank and upload it back using the upload button below.<br/><br/>' +
                    '<strong>Note</strong>: if the blank is already uploaded, you cannot update it.' +
                  '">[?]</span></strong></sup>: <span id="uploaded-request-file">Not uploaded</span>'
          }
        ]
      },
      {
        xtype: 'grid',
        id: 'libraries-in-request-grid',
        itemId: 'libraries-in-request-grid',
        title: 'Libraries/Samples',
        width: 345,
        height: 432,
        padding: '12px 15px 15px 0',
        rowspan: 2,
        viewConfig: {
          stripeRows: false
        },
        sortableColumns: false,
        enableColumnMove: false,
        enableColumnResize: false,
        enableColumnHide: false,
        columns: {
          items: [{
            xtype: 'checkcolumn',
            itemId: 'check-column',
            dataIndex: 'selected',
            tdCls: 'no-dirty',
            width: 40
          },
          {
            text: 'Name',
            dataIndex: 'name',
            flex: 1
          },
          {
            text: '',
            dataIndex: 'record_type',
            width: 35,
            renderer: function (value, meta) {
              return meta.record.getRecordType().charAt(0);
            }
          },
          {
            text: 'Barcode',
            dataIndex: 'barcode',
            width: 95,
            renderer: function (value, meta, record) {
              return record.getBarcode();
            }
          }]
        },
        store: 'librariesInRequestStore',
        bbar: [
          '->',
          {
            itemId: 'batch-add-button',
            text: 'Add'
          }
        ]
      }
    ]
  }],
  bbar: [
    '->',
    {
      xtype: 'button',
      itemId: 'save-button',
      iconCls: 'fa fa-floppy-o fa-lg',
      text: 'Save'
    }
  ]
});

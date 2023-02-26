Ext.define('MainHub.view.requests.RequestWindow', {
  extend: 'Ext.window.Window',
  requires: [
    'MainHub.view.requests.RequestWindowController',
    'MainHub.view.libraries.LibraryWindow',
    'MainHub.view.libraries.BatchAddWindow',
    'Ext.ux.FileGridField'
  ],
  controller: 'requests-requestwindow',

  height: 570,
  width: 850,
  modal: true,
  resizable: true,

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
        width: 460,
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
                name: 'name',
                xtype: 'textfield',
                fieldLabel: '<span data-qtip="The name of the request/project, as provided by the Bioinformatics CF">Name</span>',
                emptyText: 'Project name, e.g. imb_2020_03_smith_rnaseq_[...]',
                allowBlank: false,
                regex: /^[A-Za-z0-9_]+$/,
                regexText: 'Only A-Z a-z 0-9 and _ are allowed',
              },
              ,
              {
                xtype: 'fieldcontainer',
                layout: 'hbox',
                width: 300,
                fieldLabel: 'PI',
                fieldWidth: 80,
                items: [
                  {
                    xtype: 'combobox',
                    itemId: 'pi-cb',
                    name: 'pi',
                    queryMode: 'local',
                    valueField: 'id',
                    displayField: 'name',
                    fieldLabel: '',
                    emptyText: 'PI',
                    padding: "0 10px 0 0",
                    width: 160,
                    allowBlank: USER.is_staff || USER.is_bioinformatician,
                    forceSelection: true,
                    store: 'PrincipalInvestigators',
                    listeners: {
                      change: {
                        // Update Cost Unit options based on PI selection
                        fn: function (cb) {
                          Ext.getStore('CostUnits').reload(
                            {
                              params: {
                                principal_investigator_id: cb.value ? cb.value : null
                              },
                            }
                          );
                        }
                      }
                    }
                  },
                  {
                    xtype: 'combobox',
                    itemId: 'cost-unit-cb',
                    name: 'cost_unit',
                    queryMode: 'local',
                    valueField: 'id',
                    displayField: 'name',
                    emptyText: 'Cost Unit', 
                    labelWidth: 60,
                    width: 175,
                    fieldLabel: 'Cost Unit',
                    allowBlank: USER.is_staff || USER.is_bioinformatician,
                    forceSelection: true,
                    store: 'CostUnits'
                  },
                ],
              },
              {
                name: 'description',
                xtype: 'textarea',
                fieldLabel: 'Description',
                emptyText: 'Description',
                height: 85
              },
              {
                xtype: 'fieldcontainer',
                layout: 'hbox',
                width: 300,
                fieldLabel: 'Pool',
                items: [
                  {
                    xtype: 'checkbox',
                    itemId: 'pooled-libraries',
                    name: 'pooled_libraries',
                    boxLabel: '<span data-qtip="Check if the libraries are already pooled">?</span>',
                    disabled: true,
                    readOnly: true
                  },
                  {
                    xtype: 'numberfield',
                    itemId: 'pooled-libraries-concentration',
                    name: 'pooled_libraries_concentration_user',
                    fieldLabel: '<span data-qtip="Pool concentration">ng/μl</span>',
                    // emptyText: 'Concentration',
                    labelWidth: 35,
                    width: 100,
                    padding: "0 0 0 10px",
                    disabled: true,
                    hideTrigger: true,
                    keyNavEnabled: false,
                    mouseWheelEnabled: false
                  },
                  {
                    xtype: 'numberfield',
                    itemId: 'pooled-libraries-volume',
                    name: 'pooled_libraries_volume_user',
                    fieldLabel: '<span data-qtip="Pool volume">μl</span>',
                    // emptyText: 'Concentration',
                    labelWidth: 20,
                    width: 80,
                    padding: "0 0 0 10px",
                    disabled: true,
                    hideTrigger: true,
                    keyNavEnabled: false,
                    mouseWheelEnabled: false
                  },
                  {
                    xtype: 'numberfield',
                    itemId: 'pooled-libraries-fragment-size',
                    name: 'pooled_libraries_fragment_size_user',
                    fieldLabel: '<span data-qtip="Avg. pool size in bp">bp</span>',
                    // emptyText: 'Mean Size',
                    disabled: true,
                    labelWidth: 20,
                    width: 107,
                    padding: "0 0 0 10px",
                    allowDecimals: false
                  },
                ],
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
            html: '<span id="approved-request-file">Not yet approved by PI</span>'
          }
        ]
      },
      {
        xtype: 'grid',
        id: 'libraries-in-request-grid',
        itemId: 'libraries-in-request-grid',
        title: 'Libraries/Samples',
        width: 375,
        height: 477,
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
        ],
        listeners: {
          // Open Batch Window by double record
          itemdblclick: function (dv, record, item, index, e) {

            var type = record.get('record_type') === 'Library' ? 'libraries' : 'samples';
            var id = record.get('pk');
            var url = Ext.String.format('api/{0}/', type);
        
            Ext.Ajax.request({
              url: url,
              method: 'GET',
              scope: this,
              params: {
                request_id: null,
                ids: Ext.JSON.encode([id])
              },
        
              success: function (response) {

                var obj = Ext.JSON.decode(response.responseText);
        
                if (obj.success) {
                  if (obj.data.length === 0) {
                    new Noty({ text: 'No data.', type: 'warning' }).show();
                    return;
                  }
        
                  Ext.create('MainHub.view.libraries.BatchAddWindow', {
                    mode: 'edit',
                    type: record.get('record_type'),
                    records: obj.data,
                  });
                } else {
                  new Noty({ text: obj.message, type: 'error' }).show();
                }
              },
        
              failure: function (response) {
                new Noty({ text: response.statusText, type: 'error' }).show();
                console.error(response);
              }
            });
          }
        }
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

Ext.define('MainHub.view.requests.Requests', {
  extend: 'Ext.container.Container',
  xtype: 'requests',

  requires: [
    'Ext.ux.form.SearchField',
    'MainHub.view.requests.RequestsController',
    'MainHub.view.requests.RequestWindow',
    'MainHub.view.requests.EmailWindow',
    'MainHub.view.libraries.LibraryWindow',
    'MainHub.view.metadataexporter.MetadataExporter'
  ],

  controller: 'requests',

  anchor: '100% -1',
  layout: 'fit',

  items: [{
    xtype: 'grid',
    id: 'requests-grid',
    itemId: 'requests-grid',
    height: Ext.Element.getViewportHeight() - 64,
    region: 'center',
    padding: 15,
    header: {
      title: 'Requests',
      items: [{
        xtype: 'fieldcontainer',
        defaultType: 'checkboxfield',
        layout: 'hbox',
        margin: '0 20 0 0',
        items: [
          {
            name: 'asBioinformatician',
            boxLabel: '<span data-qtip="Check, to filter requests for those where you are responsible for data analysis">As bioinformatician</span>',
            boxLabelAlign: 'before',
            checked: false,
            id: 'asBioinformatician',
            margin: '0 15 0 0',
            cls: 'grid-header-checkbox',
            hidden: !USER.is_bioinformatician,
            listeners: {
              change: function (checkbox, newValue, oldValue, eOpts) {
                if (newValue) {
                  Ext.getStore('requestsStore').getProxy().extraParams.asBioinformatician = 'True';
                  Ext.getStore('requestsStore').load()
                } else {
                  Ext.getStore('requestsStore').getProxy().extraParams.asBioinformatician = 'False';
                  Ext.getStore('requestsStore').load()
                }
              }
            }
          },
          {
            name: 'asHandler',
            boxLabel: '<span data-qtip="Check, to filter requests for those where you are responsible for processing">As handler</span>',
            boxLabelAlign: 'before',
            checked: false,
            id: 'asHandler',
            margin: '0 15 0 0',
            cls: 'grid-header-checkbox',
            hidden: !USER.is_staff,
            listeners: {
              change: function (checkbox, newValue, oldValue, eOpts) {
                if (newValue) {
                  Ext.getStore('requestsStore').getProxy().extraParams.asHandler = 'True';
                  Ext.getStore('requestsStore').load()
                } else {
                  Ext.getStore('requestsStore').getProxy().extraParams.asHandler = 'False';
                  Ext.getStore('requestsStore').load()
                }
              }
            }
          },
          {
            name: 'showAll',
            boxLabel: '<span data-qtip="Uncheck, to show only those requests that have not been yet sequenced">Show all</span>',
            boxLabelAlign: 'before',
            checked: true,
            id: 'showAll',

            margin: '0 15 0 0',
            cls: 'grid-header-checkbox',
            hidden: false,
            listeners: {
              change: function (checkbox, newValue, oldValue, eOpts) {

                if (newValue) {
                  Ext.getStore('requestsStore').getProxy().extraParams.showAll = 'True';
                  Ext.getStore('requestsStore').load()
                } else {
                  Ext.getStore('requestsStore').getProxy().extraParams.showAll = 'False';
                  Ext.getStore('requestsStore').load()
                }
              }
            }
          }]
      },

      {
        xtype: 'searchfield',
        store: 'requestsStore',
        emptyText: 'Search',
        margin: '0 10px 0 0',
        width: 250
      },

      {
        xtype: 'button',
        itemId: 'add-request-button',
        text: 'Add'
      }]
    },
    viewConfig: {
      emptyText: '<h1 style="text-align:center;margin:75px">No items</h1>',
      deferEmptyText: false,
      stripeRows: false
    },
    store: 'requestsStore',
    plugins: 'gridfilters',
    sortableColumns: false,
    enableColumnMove: false,

    columns: {
      items: [
        {
          text: 'ID',
          dataIndex: 'pk',
          hidden: true,
          flex: 1
        },
        {
          text: 'Name',
          dataIndex: 'name',
          flex: 1
        },
        {
          text: 'User',
          dataIndex: 'user_full_name',
          hidden: !(USER.is_staff || USER.member_of_bcf || USER.is_pi),
          flex: 1
        },
        {
          text: 'PI',
          dataIndex: 'pi_name',
          hidden: !(USER.is_staff || USER.member_of_bcf),
          flex: 1
        },
        {
          text: 'Cost Unit',
          dataIndex: 'cost_unit_name',
          hidden: !(USER.is_staff || USER.member_of_bcf),
          flex: 1
        },
        {
          text: 'Date',
          dataIndex: 'create_time',
          renderer: Ext.util.Format.dateRenderer('d.m.Y'),
          flex: 1
        },
        {
          text: 'Total Sequencing Depth (M)',
          dataIndex: 'total_sequencing_depth',
          flex: 1,
          hidden: (USER.is_staff || USER.member_of_bcf),
        },
        {
          text: 'Description',
          dataIndex: 'description',
          hidden: true,
          flex: 1,
          renderer: function (value, meta) {
            var val = Ext.util.Format.htmlEncode(value);
            meta.tdAttr = 'data-qtip="' + val + '" data-qwidth=300';
            return val;
          }
        },
        {
          text: 'Number of samples and libraries',
          dataIndex: 'number_of_samples',
          flex: 1
        },
        {
          text: 'Handler',
          dataIndex: 'handler_name',
          flex: 1,
          hidden: !(USER.is_staff || USER.member_of_bcf),
        }
      ]
    },
    listeners: {
      // Open Request Window by double clicking row
      itemdblclick: function (dv, record, item, index, e) {
        Ext.create('MainHub.view.requests.RequestWindow', {
          title: record.get('name'),
          mode: 'edit',
          record: record
        }).show();
      }
    },
    plugins: [{
      ptype: 'bufferedrenderer',
      trailingBufferZone: 100,
      leadingBufferZone: 100
    }, {
      ptype: 'rowexpander',
      expandOnDblClick: false,
      headerWidth: 28,
      rowBodyTpl: new Ext.XTemplate(
        '<strong>Attached files:</strong><br/>',
        '<tpl for="files">',
          '<span class="attached-file-link">',
            '<a href="{path}" download>{name}</a>',
          '</span><br/>',
        '</tpl>'
      )
    }]
  }]
});

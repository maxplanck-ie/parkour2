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

       name : 'showAll',
       boxLabel: 'Show all',
       boxLabelAlign: 'before',
       checked:true,
       id : 'showAll',

       margin: '0 15 0 0',
       cls: 'grid-header-checkbox',
       hidden: false,
       listeners:{
        change: function(checkbox, newValue, oldValue, eOpts) {

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
    sortableColumns: false,
    enableColumnMove: false,

    columns: {
      items: [
        {
          text: 'Name',
          dataIndex: 'name',
          flex: 1
        },
        {
          text: 'User',
          dataIndex: 'user_full_name',
          hidden: !USER.is_staff,
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
          flex: 1
        },
        {
          text: 'Description',
          dataIndex: 'description',
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
        }
      ]
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

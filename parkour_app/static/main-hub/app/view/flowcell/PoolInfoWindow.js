Ext.define('MainHub.view.flowcell.PoolInfoWindow', {
  extend: 'Ext.window.Window',
  requires: [
    'MainHub.view.flowcell.PoolInfoWindowController'
  ],

  controller: 'flowcell-poolinfowindow',

  title: 'Pool',
  modal: true,
  autoShow: true,

  width: 500,
  height: 600,
  layout: 'fit',

  items: [{
    xtype: 'grid',
    border: 0,
    viewConfig: {
      loadMask: false,
      stripeRows: false
    },
    sortableColumns: false,
    enableColumnMove: false,
    enableColumnHide: false,
    store: 'PoolInfo',

    columns: {
      defaults: {
        flex: 1
      },
      items: [
        {
          text: 'Library',
          dataIndex: 'name'
        },
        {
          text: 'Barcode',
          dataIndex: 'barcode',
          resizable: false,
          renderer: function (value, meta, record) {
            return record.getBarcode();
          }
        },
        {
          text: 'Library Protocol',
          dataIndex: 'protocol_name',
          renderer: function (value, meta) {
            meta.tdAttr = Ext.String.format('data-qtip="{0}"', value);
            return value;
          }
        }
      ]
    },

    features: [{
      ftype: 'grouping',
      groupHeaderTpl: '<strong>Request: {name}</strong>'
    }]
  }]
});

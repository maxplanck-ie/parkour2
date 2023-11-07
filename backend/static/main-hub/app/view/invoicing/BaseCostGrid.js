Ext.define('MainHub.view.invoicing.BaseCostGrid', {
  extend: 'Ext.grid.Panel',
  alias: 'widget.costgrid',

  viewConfig: {
    stripeRows: false
  },

  tools: [{
    type: 'gear',
    handler: function () {
      window.open(Ext.String.format('{0}/admin/invoicing/{1}/',
        window.location.origin, this.up('panel').configUrl
      ));
    }
  }],

  hideHeaders: true,
  sortableColumns: false,
  enableColumnMove: false,
  enableColumnHide: false,
  enableColumnResize: false,

  columns: [
    {
      text: 'Name',
      dataIndex: 'name',
      renderer: 'gridCellTooltipRenderer',
      flex: 1
    },
    {
      text: 'Price',
      dataIndex: 'price',
      renderer: Ext.util.Format.deMoney,
      editor: {
        xtype: 'numberfield',
        minValue: 0
      },
      width: 100
    }
  ],

  plugins: [
    {
      ptype: 'rowediting',
      clicksToEdit: 1
    }
  ]
});

Ext.define('MainHub.view.metadataexporter.MetadataBaseGrid', {
  extend: 'Ext.grid.Panel',
  alias: 'widget.metadatabasegrid',

  sortableColumns: false,
  enableColumnMove: false,
  enableColumnHide: false,

  viewConfig: {
    stripeRows: false
  },

  selModel: {
    type: 'spreadsheet',
    rowSelect: false
  },

  plugins: [
    {
      ptype: 'cellediting',
      clicksToEdit: 1
    },
    {
      ptype: 'clipboard'
    }
  ]
});

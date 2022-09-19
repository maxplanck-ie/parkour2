Ext.define('MainHub.components.BaseGrid', {
  extend: 'Ext.grid.Panel',
  alias: 'widget.basegrid',

  requires: [
    'MainHub.components.BaseGridController'
  ],

  controller: 'basegrid',

  height: Ext.Element.getViewportHeight() - 64,
  region: 'center',
  padding: 15,

  viewConfig: {
    stripeRows: false
    // loadMask: false,
    // markDirty: false
  },

  customConfig: {
    qualityCheckMenuOptions: []
  },

  selModel: {
    type: 'spreadsheet',
    rowSelect: false
  },

  sortableColumns: false,
  enableColumnMove: false,

  plugins: [
    {
      ptype: 'bufferedrenderer',
      trailingBufferZone: 100,
      leadingBufferZone: 100
    },
    {
      ptype: 'rowediting',
      clicksToEdit: 1
    },
    {
      ptype: 'clipboard'
    },
    {
      ptype: 'gridfilters'
    }
  ],

  dockedItems: [{
    xtype: 'toolbar',
    dock: 'bottom',
    items: [
      '->',
      {
        xtype: 'button',
        itemId: 'cancel-button',
        iconCls: 'fa fa-ban fa-lg',
        text: 'Cancel'
      },
      {
        xtype: 'button',
        itemId: 'save-button',
        iconCls: 'fa fa-floppy-o fa-lg',
        text: 'Save'
      }
    ]
  }]
});

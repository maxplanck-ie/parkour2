Ext.define('MainHub.view.flowcell.PoolInfoWindowController', {
  extend: 'Ext.app.ViewController',
  alias: 'controller.flowcell-poolinfowindow',

  config: {
    control: {
      '#': {
        boxready: 'loadData'
      }
    }
  },

  loadData: function (wnd) {
    wnd.down('grid').getStore().load({
      url: Ext.String.format('api/pools/{0}/', wnd.pool)
    });
  }
});

Ext.define('MainHub.view.usage.ChartBase', {
  extend: 'Ext.Panel',

  cls: 'shadow',

  height: 400,
  ui: 'light',
  layout: 'fit',

  // headerPosition: 'bottom',

  defaults: {
    width: '100%'
  },

  tools: [{
    type: 'print',
    handler: function () {
      var panel = this.up('panel');
      var polar = panel.down('polar');
      var cartesian = panel.down('cartesian');

      if (polar) {
        polar.download({
          filename: panel.title
        });
      }

      if (cartesian) {
        cartesian.download({
          filename: panel.title
        });
      }
    }
  }]
});

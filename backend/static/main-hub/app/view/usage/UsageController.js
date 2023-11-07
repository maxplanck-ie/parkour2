Ext.define('MainHub.view.usage.UsageController', {
  extend: 'Ext.app.ViewController',
  alias: 'controller.usage',

  config: {
    control: {
      '#': {
        activate: 'activate'
      },
      'daterangepicker': {
        select: 'setRange'
      },
      'usagerecords': {}
    }
  },

  activate: function (view) {
    var dateRange = view.down('daterangepicker');
    this.loadData(view, dateRange.getPickerValue());
  },

  setRange: function (drp, value) {
    this.loadData(drp.up('usage'), value);
  },

  loadData: function (view, dateRange) {
    var chartPanels = [
      'usagerecords',
      'usageorganizations',
      'usageprincipalinvestigators',
      'usagelibrarytypes'
    ];

    chartPanels.forEach(function (name) {
      var panel = view.down(name);
      var emptyText = panel.down('#empty-text');
      var polar = panel.down('polar');
      var cartesian = panel.down('cartesian');

      panel.setLoading();
      polar.getStore().load({
        params: {
          start: dateRange.startDateObj,
          end: dateRange.endDateObj
        },
        callback: function (data) {
          panel.setLoading(false);
          if (
            data && data.length > 0 &&
            Ext.Array.sum(Ext.Array.pluck(Ext.Array.pluck(data, 'data'), 'data')) > 0
          ) {
            emptyText.hide();
            polar.show();
            if (cartesian) {
              cartesian.show();
            }
          } else {
            emptyText.show();
            polar.hide();
            if (cartesian) {
              cartesian.hide();
            }
          }
        }
      });
    });
  }
});

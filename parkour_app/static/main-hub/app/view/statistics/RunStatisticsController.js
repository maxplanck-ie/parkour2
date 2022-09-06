Ext.define('MainHub.view.statistics.RunStatisticsController', {
  extend: 'MainHub.components.BaseGridController',
  alias: 'controller.run-statistics',

  config: {
    control: {
      '#': {
        activate: 'activateView'
      },
      'daterangepicker': {
        select: 'setRange'
      }
    }
  },

  activateView: function (view) {
    var dateRange = view.down('daterangepicker');
    dateRange.fireEvent('select', dateRange, dateRange.getPickerValue());
  },

  setRange: function (drp, value) {
    var grid = drp.up('grid');

    grid.getStore().reload({
      params: {
        start: value.startDateObj,
        end: value.endDateObj
      },
      callback: function () {
        grid.getView().features[0].collapseAll();
      }
    });
  }
});

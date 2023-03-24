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
      '#statusCb': {
        select: 'setStatus'
      },
      'usagerecords': {},
      '#download-report-button': {
        click: 'downloadReport'
      }
    },
  },

  activate: function (view) {
    var dateRange = view.down('daterangepicker');
    var status = view.down('#statusCb').getValue();
    this.loadData(view, dateRange.getPickerValue(), status);
  },

  setRange: function (drp, dateRange) {
    var view = drp.up('usage');
    var status = view.down('#statusCb').getValue();
    this.loadData(view, dateRange, status);
  },

  setStatus: function (cb) {
    var view = cb.up('usage');
    var dateRange = view.down('daterangepicker').getPickerValue();
    this.loadData(view, dateRange, cb.getValue());
  },

  loadData: function (view, dateRange, status) {
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
          end: dateRange.endDateObj,
          status: status
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
  },

  downloadReport: function (btn) {

    var view = btn.up('usage');
    
    var dateRange = view.down('daterangepicker').getPickerValue();
    var start = dateRange.startDateFmt ? dateRange.startDateFmt : '';
    var end = dateRange.endDateFmt ? dateRange.endDateFmt : '';

    var status = view.down('#statusCb').getValue();

    var form = Ext.create('Ext.form.Panel', { standardSubmit: true });
    form.submit({
      url: '/api/usage/report/',
      method: 'GET',
      params: {
        'start': start,
        'end': end,
        'status': status
      },
      failure: function () {
        new Noty({
          text: 'There was an error, the report could not be downloaded.',
          type: 'error'
        }).show();
      }
    });
  }
});

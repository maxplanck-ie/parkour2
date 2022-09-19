Ext.define('MainHub.view.statistics.SequencesController', {
  extend: 'MainHub.components.BaseGridController',
  alias: 'controller.sequences-statistics',

  config: {
    control: {
      '#': {
        activate: 'activateView'
      },
      '#sequences-grid': {
        groupcontextmenu: 'showGroupMenu'
      },
      'daterangepicker': {
        select: 'setRange'
      },
      '#download-report': {
        click: 'downloadReport'
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
  },

  downloadReport: function (btn) {
    var store = btn.up('grid').getStore();
    var selectedRecords = this._getSelectedRecords(store);

    if (selectedRecords.length === 0) {
      new Noty({
        text: 'You did not select any items.',
        type: 'warning'
      }).show();
      return;
    }

    var form = Ext.create('Ext.form.Panel', { standardSubmit: true });
    form.submit({
      url: 'api/sequences_statistics/download_report/',
      params: {
        barcodes: Ext.JSON.encode(Ext.Array.pluck(selectedRecords, 'barcode'))
      }
    });
  },

  _getSelectedRecords: function (store) {
    var records = [];

    store.each(function (item) {
      if (item.get('selected')) {
        records.push({
          barcode: item.get('barcode')
        });
      }
    });

    return records;
  }
});

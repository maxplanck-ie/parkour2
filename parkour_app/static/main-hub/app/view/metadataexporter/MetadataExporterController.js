Ext.define('MainHub.view.metadataexporter.MetadataExporterController', {
  extend: 'Ext.app.ViewController',
  alias: 'controller.metadataexporter-metadataexporter',

  config: {
    control: {
      '#': {
        boxready: 'boxready',
        beforeshow: 'setModelData'
      },
      '#galaxy-url-input, #galaxy-api-key-input': {
        keyup: 'saveToLocalStorage'
      },
      '#samples-grid': {
        headercontextmenu: 'showHeaderMenu'
      },
      '#refresh-galaxy-status-button': {
        click: 'refreshGalaxyStatus'
      },
      'enabasegrid': {
        itemcontextmenu: 'showContextMenu'
      },
      '#download-button': {
        click: 'handleButtonClick'
      },
      '#upload-button': {
        click: 'handleButtonClick'
      }
    }
  },

  setModelData: function (wnd) {
    wnd.down('form').getForm().setValues(wnd.request.data);
  },

  saveToLocalStorage: function (fld, e) {
    localStorage.setItem(fld.name, e.target.value);
  },

  boxready: function (wnd) {
    var requestId = wnd.request.get('pk');
    var galaxyURLField = wnd.down('form').down('#galaxy-url-input');
    var galaxyAPIKeyField = wnd.down('form').down('#galaxy-api-key-input');
    var refreshGalaxyStatusBtn = wnd.down('#refresh-galaxy-status-button');
    var galaxyURL;
    var galaxyAPIKey;

    // Set Galaxy URL and API Key
    galaxyURL = localStorage.getItem(galaxyURLField.name);
    galaxyAPIKey = localStorage.getItem(galaxyAPIKeyField.name);
    if (galaxyURL !== '') galaxyURLField.setValue(galaxyURL);
    if (galaxyAPIKey !== '') galaxyAPIKeyField.setValue(galaxyAPIKey);

    // Check Galaxy status
    if (galaxyURL && galaxyAPIKey) {
      refreshGalaxyStatusBtn.click();
    }

    // Load samples
    Ext.getStore('ENASamples').reload({
      url: Ext.String.format('api/metadata_exporter/{0}/', requestId)
    });
  },

  showHeaderMenu: function (ct, column, e) {
    var me = this;
    var store = Ext.getStore('ENASamples');
    var selectedSamples = this.getSelectedSamples(store);

    if (column.dataIndex !== 'selected') {
      return false;
    }

    var items = [
      {
        text: 'Select All',
        handler: function () {
          me.selectAll(true);
        }
      }, {
        text: 'Unselect All',
        handler: function () {
          me.selectAll(false);
        }
      }
    ];

    if (selectedSamples.length > 0) {
      items = items.concat([
        '-',
        {
          text: Ext.String.format('Delete Selected ({0})', selectedSamples.length),
          handler: function () {
            store.remove(selectedSamples);
          }
        }
      ]);
    }

    e.stopEvent();
    Ext.create('Ext.menu.Menu', {
      plain: true,
      defaults: {
        margin: 5
      },
      items: items
    }).showAt(e.getXY());
  },

  showContextMenu: function (gridView, record, itemEl, index, e) {
    var me = this;
    var dataIndex = MainHub.Utilities.getDataIndex(e, gridView);

    if (!dataIndex || dataIndex === 'selected' || dataIndex === 'library_name') {
      return false;
    }

    e.stopEvent();
    Ext.create('Ext.menu.Menu', {
      plain: true,
      defaults: {
        margin: 5
      },
      items: [
        {
          text: 'Apply to All',
          handler: function () {
            me.applyToAll(gridView, record, dataIndex);
          }
        },
        {
          text: 'Delete',
          handler: function () {
            record.store.remove(record);
          }
        }
      ]
    }).showAt(e.getXY());
  },

  refreshGalaxyStatus: function (btn) {
    var wnd = btn.up('window');
    var form = wnd.down('form').getForm();
    var data = form.getValues();
    var galaxyURL = data.galaxy_url;
    var galaxyAPIKey = data.galaxy_api_key;

    if (galaxyURL === '' || galaxyAPIKey === '') {
      new Noty({
        text: 'Galaxy URL or Galaxy API Key is missing.',
        type: 'warning'
      }).show();
      return false;
    }

    Ext.Ajax.request({
      url: 'api/metadata_exporter/get_galaxy_status/',
      timeout: 5000, // 5 seconds
      params: {
        galaxy_url: galaxyURL,
        galaxy_api_key: galaxyAPIKey
      },

      success: function (response) {
        var obj = Ext.decode(response.responseText);
        var status = obj.success ? 'online' : 'offline';
        var type = obj.success ? 'info' : 'error';

        new Noty({ text: 'Galaxy is ' + status, type: type }).show();
        wnd.getViewModel().setData({ galaxyStatus: status });
      },

      failure: function (response) {
        var error = response.statusText === 'communication failure'
          ? 'Timeout Exceeded.'
          : response.statusText;

        new Noty({ text: error, type: 'error' }).show();
      }
    });
  },

  selectAll: function (result) {
    var store = Ext.getStore('ENASamples');
    result = result || false;

    store.each(function (item) {
      item.set('selected', result);
    });
  },

  applyToAll: function (gridView, record, dataIndex) {
    var store = Ext.getStore('ENASamples');

    if (dataIndex) {
      store.each(function (item) {
        if (item !== record) {
          item.set(dataIndex, record.get(dataIndex));
        }
      });
    }

    this.validateAll();
  },

  handleButtonClick: function (btn) {
    var wnd = btn.up('window');
    var tabs = wnd.down('#tabs');
    var requestId = wnd.request.get('pk');
    var store = Ext.getStore('ENASamples');
    var form = wnd.down('form').getForm();
    var data = form.getValues();
    var galaxyURL = data.galaxy_url;
    var galaxyAPIKey = data.galaxy_api_key;
    var action = btn.itemId.split('-')[0];
    var params = {
      samples: Ext.JSON.encode(Ext.Array.pluck(store.data.items, 'data')),
      study_abstract: data.study_abstract,
      study_title: data.study_title,
      study_type: data.study_type
    };

    if (store.getCount() === 0) {
      new Noty({ text: 'No samples selected.', type: 'warning' }).show();
      return false;
    }

    // Form validation
    if (!form.isValid()) {
      tabs.setActiveItem(0);
      new Noty({ text: 'Check the form.', type: 'warning' }).show();
      return false;
    }

    // Sample data validation
    this.validateAll();

    var numInvalidRecords = store.data.items.reduce(function (n, item) {
      return n + (item.get('invalid') === true);
    }, 0);

    if (numInvalidRecords !== 0) {
      tabs.setActiveItem(1);
      new Noty({ text: 'Check the data.', type: 'warning' }).show();
      return;
    }

    if (action === 'download') {
      var downloadForm = Ext.create('Ext.form.Panel', { standardSubmit: true });
      downloadForm.submit({
        url: Ext.String.format('api/metadata_exporter/{0}/download/', requestId),
        params: params
      });
    } else {
      if (galaxyURL === '' || galaxyAPIKey === '') {
        new Noty({
          text: 'Galaxy URL or Galaxy API Key is missing.',
          type: 'warning'
        }).show();
        return false;
      }

      params.galaxy_url = galaxyURL;
      params.galaxy_api_key = galaxyAPIKey;

      wnd.setLoading('Uploading...');
      Ext.Ajax.request({
        url: Ext.String.format('api/metadata_exporter/{0}/upload/', requestId),
        params: params,

        success: function (response) {
          var obj = Ext.decode(response.responseText);
          var status = obj.success ? 'online' : 'offline';

          if (obj.success) {
            new Noty({
              text: 'Files have been successfully uploaded!'
            }).show();
          } else {
            new Noty({
              type: 'error',
              text: obj.message
            }).show();
          }
          wnd.getViewModel().setData({ galaxyStatus: status });
          wnd.setLoading(false);
        },

        failure: function (response) {
          console.log('server-side failure with status code ' + response.status);
          wnd.setLoading(false);
        }
      });
    }
  },

  validateAll: function () {
    var me = this;
    var grid = this.getView().down('#samples-grid');
    var store = grid.getStore();

    // Validate all records
    store.each(function (record) {
      me.validateRecord(record);
    });

    // Refresh the grid
    grid.getView().refresh();
  },

  validateRecord: function (record) {
    var grid = this.getView().down('#samples-grid');
    var store = grid.getStore();
    var validation = record.getValidation(true).data;
    var invalid = false;
    var errors = {};

    for (var dataIndex in validation) {
      if (validation.hasOwnProperty(dataIndex)) {
        if (validation[dataIndex] !== true) {
          invalid = true;
          errors[dataIndex] = validation[dataIndex];
        }
      }
    }

    store.suspendEvents();
    record.set({ invalid: invalid, errors: errors });
    store.resumeEvents();

    return errors;
  },

  errorRenderer: function (value, meta, record) {
    var dataIndex = meta.column.dataIndex;
    var errors = record.get('errors');

    if (Object.keys(errors).indexOf(dataIndex) !== -1) {
      meta.tdCls += ' invalid-record';
      meta.tdAttr = Ext.String.format('data-qtip="{0}"', errors[dataIndex]);
    }

    return value;
  },

  comboboxErrorRenderer: function (value, meta, record) {
    var dataIndex = meta.column.dataIndex;
    // var store = meta.column.getEditor().getStore();

    if (record && Object.keys(record.get('errors')).indexOf(dataIndex) !== -1) {
      meta.tdCls += ' invalid-record';
      meta.tdAttr = Ext.String.format('data-qtip="{0}"', record.get('errors')[dataIndex]);
    }

    return value;
  },

  getSelectedSamples: function (store) {
    return store.data.items.filter(function (item) {
      return item.get('selected');
    });
  }
});

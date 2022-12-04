Ext.define('MainHub.view.invoicing.InvoicingController', {
  extend: 'Ext.app.ViewController',
  alias: 'controller.invoicing',

  requires: [
    'Ext.ux.FileUploadWindow'
  ],

  config: {
    control: {
      '#': {
        activate: 'activateView'
      },
      '#billing-period-combobox': {
        select: 'selectBillingPeriod'
      },
      '#organization-combobox': {
        select: 'selectOrganization'
      },
      '#invoicing-grid': {
        resize: 'resize'
      },
      '#download-report': {
        click: 'downloadReport'
      },
      '#upload-report': {
        click: 'uploadReport'
      },
      '#fixed-costs-grid,#preparation-costs-grid,#sequencing-costs-grid': {
        edit: 'editPrice'
      }
    }
  },

  activateView: function (view) {
    view.down('#organization-combobox').getStore().reload();
    view.down('#billing-period-combobox').getStore().reload();

  },

  resize: function (el) {
    el.setHeight(Ext.Element.getViewportHeight() - 64);
  },

  selectBillingPeriod: function (cb, record) {
    var organizationId = cb.up().down('#organization-combobox').value;
    var uploadedReportBtn = cb.up().down('#view-uploaded-report-button');
    var reportUrl = record.report_urls().findRecord('organization_id', organizationId);
    var reportUrl = reportUrl ? reportUrl.get('url') : "";
    
    // Enable upload/download buttons
    var grid = cb.up('grid');
    grid.down('#download-report').enable();
    grid.down('#upload-report').enable();

    Ext.getStore('Invoicing').reload({
      params: {
        year: record.get('value')[0],
        month: record.get('value')[1],
        organization: organizationId
      }
    });

    if (reportUrl !== '') {
      uploadedReportBtn.reportUrl = reportUrl;
      uploadedReportBtn.show();
    } else {
      uploadedReportBtn.hide();
    }
  },

  selectOrganization: function (cb, record) {

    // Reload organization-specific cost stores
    Ext.getStore('FixedCosts').reload({
      params: {
        organization: cb.value
      },
    });
    Ext.getStore('LibraryPreparationCosts').reload({
      params: {
        organization: cb.value
      },
    });
    Ext.getStore('SequencingCosts').reload({
      params: {
        organization: cb.value
      },
    });

    var billingPeriodCb = cb.up().down('#billing-period-combobox');
    if (billingPeriodCb.value) {
      this.selectBillingPeriod(billingPeriodCb, billingPeriodCb.getSelection());
    } else {
      billingPeriodCb.enable();
    }
  },

  editPrice: function (editor, context) {
    var store = editor.grid.getStore();
    var proxy = store.getProxy();

    proxy.api.update = Ext.String.format('{0}{1}/',
      proxy.api.read, context.record.get('id')
    );

    store.sync({
      params: {
        organization: Ext.ComponentQuery.query('#organization-combobox')[0].getValue()
      },
      success: function (batch) {
        Ext.getCmp('invoicing-grid').getStore().reload();
        new Noty({ text: 'The changes have been saved.' }).show();
      }
    });
  },

  downloadReport: function (btn) {
    var billingPeriodCb = btn.up('grid').down('#billing-period-combobox');
    var value = billingPeriodCb.getValue();
    var form = Ext.create('Ext.form.Panel', { standardSubmit: true });

    form.submit({
      url: btn.downloadUrl,
      method: 'GET',
      params: {
        year: value[0],
        month: value[1],
        organization: btn.up('grid').down('#organization-combobox').getValue()
      }
    });
  },

  uploadReport: function (btn) {
    var billingPeriodCb = btn.up('grid').down('#billing-period-combobox');
    var value = billingPeriodCb.getValue();

    Ext.create('Ext.ux.FileUploadWindow', {
      fileFieldName: 'report',

      onFileUpload: function () {
        var uploadWindow = this;
        var form = this.down('form').getForm();

        if (!form.isValid()) {
          new Noty({
            text: 'You did not select any file.',
            type: 'warning'
          }).show();
          return;
        }

        form.submit({
          url: btn.uploadUrl,
          method: 'POST',
          waitMsg: 'Uploading...',
          params: {
            month: value[0] + '-' + value[1],
            organization: btn.up('grid').down('#organization-combobox').getValue()
          },
          success: function (f, action) {
            new Noty({ text: 'Report has been successfully uploaded.' }).show();
            billingPeriodCb.getStore().reload();
            uploadWindow.close();
          }
        });
      }
    });
  },

  gridCellTooltipRenderer: function (value, meta) {
    meta.tdAttr = Ext.String.format('data-qtip="{0}"', value);
    return value;
  },

  listRenderer: function (value, meta) {
    meta.tdAttr = Ext.String.format('data-qtip="{0}"', value.join('<br/>'));
    return value.join('; ');
  },

  sequencerRenderer: function (value, meta) {
    var items = value.map(function (item) {
      return Ext.String.format('{0}: {1}',
        item.flowcell_id, item.sequencer_name
      );
    });
    meta.tdAttr = Ext.String.format('data-qtip="{0}"', items.join('<br/>'));
    return _.uniq(Ext.Array.pluck(value, 'sequencer_name')).sort().join('; ');
  },

  percentageRenderer: function (value, meta) {
    var tpl = new Ext.XTemplate(
      '<ul>',
        '<tpl for=".">',
          '<li>{flowcell_id}',
            '<ul>',
              '<tpl for="pools">',
                '<li>{name}: {percentage}</li>',
              '</tpl>',
            '</ul>',
          '</li>',
        '</tpl>',
      '</ul>'
    );
    meta.tdAttr = Ext.String.format('data-qtip="{0}"', tpl.apply(value));

    return Ext.Array.pluck(value, 'pools').map(function (item) {
      return Ext.Array.pluck(item, 'percentage').join(', ');
    }).join('; ');
  },

  readLengthRenderer: function (value, meta) {
    var store = Ext.getStore('readLengthsInvoicingStore');
    var items = value.map(function (id) {
      var record = store.findRecord('id', id, 0, false, true, true);
      return record.get('name');
    });
    return items.join('; ');
  },

  libraryProtocolRenderer: function (value, meta) {
    var record = Ext.getStore('libraryprotocolinvoicingStore').findRecord(
      'id', value, 0, false, true, true);
    var name = record.get('name');
    meta.tdAttr = Ext.String.format('data-qtip="{0}"', name);
    return name;
  }
});

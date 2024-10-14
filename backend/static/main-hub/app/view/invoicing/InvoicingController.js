Ext.define("MainHub.view.invoicing.InvoicingController", {
  extend: "Ext.app.ViewController",
  alias: "controller.invoicing",

  requires: [
    "Ext.ux.FileUploadWindow",
    "MainHub.view.invoicing.UploadReportsWindow",
    "MainHub.view.invoicing.ViewUploadedReportsWindow"
  ],

  config: {
    control: {
      "#": {
        activate: "activateView"
      },
      parkourmonthpicker: {
        select: "selectMonth"
      },
      "#invoicing-grid": {
        resize: "resize"
      },
      "#download-report": {
        click: "downloadReport"
      },
      "#upload-reports": {
        click: "uploadReports"
      },
      "#view-uploaded-reports": {
        click: "viewUploadedReports"
      },
      "#fixed-costs-grid,#preparation-costs-grid,#sequencing-costs-grid": {
        edit: "editPrice"
      }
    }
  },

  activateView: function (view) {
    var startMonthPicker = view.down("#start-month-picker");
    var endMonthPicker = view.down("#end-month-picker");

    var currentDate = new Date();
    var defaultStartDate = Ext.Date.subtract(currentDate, Ext.Date.MONTH, 0);
    var defaultEndDate = currentDate;

    startMonthPicker.setValue(defaultStartDate);
    endMonthPicker.setValue(defaultEndDate);

    startMonthPicker.fireEvent("select", startMonthPicker);
    endMonthPicker.fireEvent("select", endMonthPicker);

    view.down("#fixed-costs-grid").getStore().reload();
    view.down("#preparation-costs-grid").getStore().reload();
    view.down("#sequencing-costs-grid").getStore().reload();
  },

  selectMonth: function (df, view) {
    var grid = df.up("grid");
    var startMonthPicker = grid.down("#start-month-picker");
    var endMonthPicker = grid.down("#end-month-picker");

    var start = Ext.Date.format(startMonthPicker.getValue(), "Y-m");
    var end = Ext.Date.format(endMonthPicker.getValue(), "Y-m");

    var store = grid.getStore();
    store.getProxy().setExtraParam("start", start);
    store.getProxy().setExtraParam("end", end);
    store.reload({});
  },

  resize: function (el) {
    el.setHeight(Ext.Element.getViewportHeight() - 64);
  },

  editPrice: function (editor, context) {
    var store = editor.grid.getStore();
    var proxy = store.getProxy();

    proxy.api.update = Ext.String.format(
      "{0}{1}/",
      proxy.api.read,
      context.record.get("id")
    );

    store.sync({
      success: function (batch) {
        Ext.getCmp("invoicing-grid").getStore().reload();
        new Noty({ text: "Changes have been saved successfully." }).show();
      }
    });
  },

  downloadReport: function (btn) {
    var grid = btn.up("grid");
    var startMonthPicker = grid.down("#start-month-picker");
    var endMonthPicker = grid.down("#end-month-picker");

    var start = Ext.Date.format(startMonthPicker.getValue(), "Y-m");
    var end = Ext.Date.format(endMonthPicker.getValue(), "Y-m");
    var form = Ext.create("Ext.form.Panel", { standardSubmit: true });

    form.submit({
      url: btn.downloadUrl,
      method: "GET",
      params: {
        start,
        end
      }
    });
  },

  uploadReports: function (btn) {
    Ext.create("MainHub.view.invoicing.UploadReportsWindow");
  },

  viewUploadedReports: function (btn) {
    Ext.create("MainHub.view.invoicing.ViewUploadedReportsWindow");
  },

  gridCellTooltipRenderer: function (value, meta) {
    if (value) {
      meta.tdAttr = 'data-qtip="' + value + '"';
    } else meta.tdAttr = "data-qtip=Empty";
    return value;
  },

  listRenderer: function (value, meta) {
    meta.tdAttr = Ext.String.format('data-qtip="{0}"', value.join("<br/>"));
    return value.join("; ");
  },

  sequencerRenderer: function (value, meta) {
    var items = value.map(function (item) {
      return Ext.String.format(
        "{0}: {1}",
        item.flowcell_id,
        item.sequencer_name
      );
    });
    meta.tdAttr = Ext.String.format('data-qtip="{0}"', items.join("<br/>"));
    return _.uniq(Ext.Array.pluck(value, "sequencer_name")).sort().join("; ");
  },

  percentageRenderer: function (value, meta) {
    var tpl = new Ext.XTemplate(
      "<ul>",
      '<tpl for=".">',
      "<li>{flowcell_id}",
      "<ul>",
      '<tpl for="pools">',
      "<li>{name}: {percentage}</li>",
      "</tpl>",
      "</ul>",
      "</li>",
      "</tpl>",
      "</ul>"
    );
    meta.tdAttr = Ext.String.format('data-qtip="{0}"', tpl.apply(value));

    return Ext.Array.pluck(value, "pools")
      .map(function (item) {
        return Ext.Array.pluck(item, "percentage").join(", ");
      })
      .join("; ");
  },

  readLengthRenderer: function (value, meta) {
    var store = Ext.getStore("readLengthsInvoicingStore");
    var items = value.map(function (id) {
      var record = store.findRecord("id", id, 0, false, true, true);
      return record.get("name");
    });
    return items.join("; ");
  },

  libraryProtocolRenderer: function (value, meta) {
    var record = Ext.getStore("libraryprotocolinvoicingStore").findRecord(
      "id",
      value,
      0,
      false,
      true,
      true
    );
    var name = record.get("name");
    meta.tdAttr = Ext.String.format('data-qtip="{0}"', name);
    return name;
  }
});

Ext.define("MainHub.view.flowcell.SampleSheetIlluminav2WindowController", {
  extend: "Ext.app.ViewController",
  alias: "controller.flowcell-samplesheet-illuminav2-window",

  config: {
    control: {
      "#": {
        boxready: "boxready",
      },
      "#ss-save-button": {
        click: "save",
      },
      "#ss-cancel-button": {
        click: "cancel",
      },
    },
  },

  boxready: function (wnd) {
    var flowcellForm = Ext.getCmp("flowcell-form").getForm();
    var sampleSheetValues = flowcellForm.getFieldValues()["sample_sheet"];
    if (sampleSheetValues) {
      var ssForm = wnd.down("#ss-options-form").getForm();
      ssForm.setValues(sampleSheetValues);
    }
  },

  save: function (btn) {
    var wnd = btn.up("window");
    var ssForm = wnd.down("#ss-options-form").getForm();
    if (!ssForm.isValid()) {
      new Noty({
        text:
          "The form is invalid. Check the fields with " +
          "errors and amend them accordingly.",
        type: "warning",
      }).show();
      return;
    }

    var flowcellForm = Ext.getCmp("flowcell-form");
    ssValues = ssForm.getFieldValues();
    ssValues["sample_sheet_type"] = "illuminav2";
    flowcellForm.getForm().setValues({ sample_sheet: ssValues });
    wnd.close();
  },

  cancel: function (btn) {
    var wnd = btn.up("window");
    var flowcellForm = Ext.getCmp("flowcell-form");
    flowcellForm.getForm().setValues({ sample_sheet: null });
    wnd.close();
  },
});

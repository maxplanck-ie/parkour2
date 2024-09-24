Ext.define("MainHub.view.requests.TokenWindowController", {
  extend: "Ext.app.ViewController",
  alias: "controller.requests-TokenWindow",
  requires: [],

  config: {
    control: {
      "#": {
        boxready: "boxready"
      },
      "#send-email-button": {
        click: "send"
      }
    }
  },

  boxready: function (wnd) {
    var subjectField = wnd.down("#subject-field");
    subjectField.setValue(wnd.record.get("name"));
  },

  send: function (btn) {
    var wnd = btn.up("window");
    var form = wnd.down("#email-form").getForm();

    if (!form.isValid()) {
      new Noty({
        text: "All fields must be filled in.",
        type: "warning"
      }).show();
      return;
    }

    btn.setDisabled(true);
    btn.setText("Sending...");

    form.submit({
      url: Ext.String.format(
        "api/requests/{0}/solicit_approval/",
        wnd.record.get("pk")
      ),
      params: form.getFieldValues(),
      success: function (f, action) {
        new Noty({ text: "Email sent, ask PI for your copy!" }).show();
        wnd.close();
      },
      failure: function (f, action) {
        var error = action.result
          ? action.result.error
          : action.response.statusText;
        new Noty({ text: error, type: "error" }).show();
        console.error(action);
        btn.setDisabled(false);
        btn.setText("Send");
      }
    });
  }
});

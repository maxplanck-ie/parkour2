Ext.define("MainHub.view.requests.EmailWindow", {
  extend: "Ext.window.Window",
  requires: ["MainHub.view.requests.EmailWindowController"],
  controller: "requests-emailwindow",

  height: 370,
  width: 450,
  modal: true,
  resizable: false,
  autoShow: true,
  layout: {
    type: "vbox",
    align: "stretch"
  },

  items: [
    {
      xtype: "form",
      itemId: "email-form",
      padding: 10,
      border: 0,
      defaults: {
        submitEmptyText: false,
        allowBlank: false,
        labelWidth: 100,
        anchor: "100%"
      },
      items: [
        {
          xtype: "textfield",
          itemId: "subject-field",
          name: "subject",
          fieldLabel: "Subject",
          emptyText: "Subject"
        },
        {
          xtype: "textarea",
          name: "message",
          fieldLabel: "Message",
          emptyText: "Message",
          height: 175
        },
        {
          xtype: "fieldcontainer",
          defaultType: "checkboxfield",
          name: "reject_request",
          itemId: "reject-field",
          items: [
            {
              boxLabel:
                "Reject request <sup><strong>" +
                '<span class="reject-request-tooltip" tooltip-text="' +
                "All failed libraries/samples will be automatically " +
                "included in the message. <br>" +
                "The status of ALL libraries/samples will be " +
                "changed to 'Pending submission' and the request will " +
                "be unapproved." +
                '">[!]</span></strong></sup>',
              name: "reject_request",
              inputValue: "true",
              checked: false
            }
          ]
        }
      ]
    }
  ],

  bbar: [
    "->",
    {
      xtype: "button",
      itemId: "send-email-button",
      iconCls: "fa fa-paper-plane fa-lg",
      text: "Send"
    }
  ]
});

Ext.define("MainHub.view.requests.FilepathsWindow", {
  extend: "Ext.window.Window",
  requires: ["MainHub.view.requests.FilepathsWindowController"],
  controller: "requests-filepathsWindow",

  height: 490,
  width: 900,
  modal: true,
  resizable: false,
  autoShow: true,
  layout: {
    type: "vbox",
    align: "stretch"
  },

  items: [
    {
      xtype: "container",
      itemId: "filepaths-container",
      padding: 10,
      border: 0,
      defaults: {
        labelWidth: 100
      },
      layout: {
        type: "vbox",
        align: "stretch"
      },
      items: [
        {
          xtype: "container",
          items: [
            {
              xtype: "label",
              text: "Request Name:",
              style: {
                fontWeight: "bold"
              },
              margin: "10"
            },
            {
              xtype: "label",
              itemId: "request-name",
              name: "request-name",
              margin: "10 0 10 0"
            }
          ],
          style: {
            border: "1px solid #d4d4d4"
          },
          margin: "0 0 10 0",
          padding: "5"
        },
        {
          xtype: "container",
          layout: {
            type: "hbox",
            align: "stretch"
          },
          flex: 1,
          items: [
            {
              xtype: "container",
              flex: 1,
              items: [
                {
                  xtype: "container",
                  items: [
                    {
                      xtype: "container",
                      layout: {
                        type: "hbox",
                        align: "middle"
                      },
                      padding: "0 0 0 10",
                      items: [
                        {
                          xtype: "label",
                          text: "Request File Paths:",
                          name: "file-paths-label",
                          style: {
                            fontWeight: "bold"
                          },
                          flex: 1
                        },
                        {
                          xtype: "combobox",
                          reference: "osComboBox",
                          store: ["Linux", "macOS", "Windows"],
                          queryMode: "local",
                          displayField: "name",
                          valueField: "name",
                          height: 32,
                          width: 150,
                          margin: "0 0 0 10"
                        }
                      ]
                    },
                    {
                      xtype: "container",
                      itemId: "dynamic-container",
                      margin: "15 0 0 15",
                      style: {
                        height: "270px",
                        overflowY: "scroll"
                      }
                    }
                  ],
                  style: {
                    border: "1px solid #d4d4d4"
                  },
                  margin: "0 10 0 0",
                  padding: "5"
                }
              ]
            },
            {
              xtype: "container",
              flex: 1,
              items: [
                {
                  xtype: "container",
                  layout: {
                    type: "hbox",
                    align: "middle"
                  },
                  padding: "0 0 0 10",
                  items: [
                    {
                      xtype: "label",
                      text: "Request User Paths:",
                      name: "user-paths-label",
                      style: {
                        fontWeight: "bold"
                      },
                      flex: 1
                    },
                    {
                      xtype: "button",
                      iconCls: "x-fa fa-plus",
                      text: "Add",
                      height: 32,
                      width: 70,
                      margin: "0 0 0 10",
                      style: {
                        borderColor: "#d4d4d4",
                        borderStyle: "solid",
                        borderWidth: "1px",
                        cursor: "pointer",
                        textAlign: "center",
                        lineHeight: "32px"
                      },
                      listeners: {
                        click: "onAddButtonClick"
                      }
                    }
                  ]
                },
                {
                  xtype: "container",
                  itemId: "dynamic-container-2",
                  margin: "15 0 0 15",
                  style: {
                    height: "270px",
                    overflowY: "scroll"
                  }
                }
              ],
              style: {
                border: "1px solid #d4d4d4"
              },
              padding: "5"
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
      itemId: "close-button",
      text: "Close",
      handler: function () {
        this.up("window").close();
      }
    }
  ],

  listeners: {
    afterrender: "getPaths"
  }
});

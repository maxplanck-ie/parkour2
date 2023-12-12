Ext.define("MainHub.view.requests.RequestsController", {
  extend: "Ext.app.ViewController",
  alias: "controller.requests",

  config: {
    control: {
      "#": {
        activate: "activateView",
      },
      "#requests-grid": {
        resize: "resize",
        itemcontextmenu: "showMenu",
      },
      "#add-request-button": {
        click: "addRequest",
      },
    },
  },

  activateView: function () {
    Ext.getStore("requestsStore").reload();
  },

  resize: function (el) {
    el.setHeight(Ext.Element.getViewportHeight() - 64);
  },

  addRequest: function (btn) {
    Ext.create("MainHub.view.requests.RequestWindow", {
      title: "New Request",
      mode: "add",
    }).show();
  },

  showMenu: function (grid, record, itemEl, index, e) {
    var me = this;
    var requestId = record.get("pk");
    var deepSeqReqPath = record.get("deep_seq_request_path");

    e.stopEvent();
    Ext.create("Ext.menu.Menu", {
      plain: true,
      defaults: {
        margin: 5,
      },
      items: [
        {
          text: "View",
          handler: function () {
            Ext.create("MainHub.view.requests.RequestWindow", {
              title: Ext.String.format(
                "{0} - {1}",
                record.get("pk"),
                record.get("name")
              ),
              mode: "edit",
              record: record,
            }).show();
          },
        },
        {
          text: "Delete",
          hidden: record.restrict_permissions,
          handler: function () {
            Ext.Msg.show({
              title: "Delete Request",
              message: Ext.String.format(
                'Are you sure you want to delete the request "{0}"?',
                record.get("name")
              ),
              buttons: Ext.Msg.YESNO,
              icon: Ext.Msg.QUESTION,
              fn: function (btn) {
                if (btn === "yes") {
                  me.deleteRequest(record);
                }
              },
            });
          },
        },
        "-",
        // {
        //   text: 'Download Request Form',
        //   tooltip: 'Download deep sequencing request form',
        //   disabled: !(deepSeqReqPath === ''),
        //   handler: function () {
        //     var url = Ext.String.format(
        //       'api/requests/{0}/download_deep_sequencing_request/', requestId
        //     );
        //     var downloadForm = Ext.create('Ext.form.Panel', { standardSubmit: true });
        //     downloadForm.submit({ url: url, method: 'GET' });
        //   }
        // },
        // {
        //   text: 'Upload Signed Request',
        //   tooltip: 'Upload signed request form to complete the submission',
        //   disabled: !(deepSeqReqPath === ''),
        //   handler: function () {
        //     me.uploadSignedRequest(requestId);
        //   }
        // },
        {
          text: "Request approval from PI",
          hidden: USER.is_pi || deepSeqReqPath !== "",
          disabled: !(deepSeqReqPath === ""),
          handler: function () {
            me.requestApproval(record, "False");
          },
        },
        {
          text: deepSeqReqPath === "" ? "Approve" : "Approved",
          hidden: !(USER.is_pi || USER.is_staff) && deepSeqReqPath === "",
          disabled: !(deepSeqReqPath === ""),
          handler: function () {
            Ext.Msg.show({
              title: "Approve request",
              message: "Are you sure you want to approve this request?",
              buttons: Ext.Msg.YESNO,
              icon: Ext.Msg.QUESTION,
              fn: function (btn) {
                if (btn === "yes") {
                  me.approve(record, "False");
                }
              },
            });
          },
        },
        {
          text: "Download Complete Report",
          handler: function () {
            var url = Ext.String.format(
              "api/requests/{0}/download_complete_report/",
              requestId
            );
            var downloadForm = Ext.create("Ext.form.Panel", {
              standardSubmit: true,
            });
            downloadForm.submit({ url: url, method: "GET" });
          },
        },
        "-",
        {
          text: "Metadata Exporter",
          disabled: !record.get("completed"),
          handler: function () {
            Ext.create("MainHub.view.metadataexporter.MetadataExporter", {
              request: record,
            });
          },
        },
        {
          text: "View File Paths",
          hidden: !USER.is_staff,
          handler: function () {
            Ext.create("MainHub.view.requests.FilePathsWindow", {
              title: "File Paths",
              record: record,
            });
          },
        },
        {
          text: "Compose Email",
          hidden: !USER.is_staff,
          handler: function () {
            Ext.create("MainHub.view.requests.EmailWindow", {
              title: "New Email",
              record: record,
            });
          },
        },
        {
          text: "Mark as complete",
          hidden: !(USER.is_staff || USER.member_of_bcf),
          handler: function () {
            Ext.Msg.show({
              title: "Mark request as complete",
              message: Ext.String.format(
                'Are you sure you want to mark request "{0} as complete?',
                record.get("name")
              ),
              buttons: Ext.Msg.YESNO,
              icon: Ext.Msg.QUESTION,
              fn: function (btn) {
                if (btn === "yes") {
                  me.markascomplete(record, "False");
                }
              },
            });
          },
        },
      ],
    }).showAt(e.getXY());
  },

  markascomplete: function (record, admin_override) {
    var me = this;
    Ext.Ajax.request({
      url: Ext.String.format(
        "api/requests/{0}/mark_as_complete/",
        record.get("pk")
      ),
      method: "POST",
      scope: me,

      params: {
        data: Ext.JSON.encode({
          override: admin_override,
        }),
      },
      success: function (response) {
        var obj = Ext.JSON.decode(response.responseText);

        if (obj.success) {
          Ext.getStore("requestsStore").reload();
          new Noty({ text: "Request has been marked as complete!" }).show();
        } else if (obj.noncomplete) {
          Ext.Msg.show({
            title: "Mark request as complete",
            message: Ext.String.format(
              "There are unsequenced libraries/samples related to this request. Do you want to mark it as complete anyway?"
            ),
            buttons: Ext.Msg.YESNO,
            icon: Ext.Msg.QUESTION,
            fn: function (btn) {
              if (btn === "yes") {
                me.markascomplete(record, "True");
              }
            },
          });
        } else {
          new Noty({ text: obj.message, type: "error" }).show();
        }
      },

      failure: function (response) {
        var responseText = response.responseText
          ? Ext.JSON.decode(response.responseText)
          : null;
        responseText = responseText.message
          ? responseText.message
          : "Unknown error.";
        responseText = response.statusText ? response.statusText : responseText;
        new Noty({ text: responseText, type: "error" }).show();
        console.error(response);
      },
    });
  },

  approve: function (record, admin_override) {
    var me = this;
    Ext.Ajax.request({
      url: Ext.String.format("api/requests/{0}/approve/", record.get("pk")),
      method: "GET",
      scope: me,
      params: {
        data: Ext.JSON.encode({
          override: admin_override,
        }),
      },
      success: function (response) {
        var obj = Ext.JSON.decode(response.responseText);

        if (obj.success) {
          Ext.getStore("requestsStore").reload();
          new Noty({ text: "Request has been approved" }).show();
        } else {
          var message = obj.error ? obj.error : "Unknown error.";
          new Noty({ text: message, type: "error" }).show();
        }
      },

      failure: function (response) {
        var responseText = response.responseText
          ? Ext.JSON.decode(response.responseText)
          : null;
        responseText = responseText.message
          ? responseText.message
          : "Unknown error.";
        responseText = response.statusText ? response.statusText : responseText;
        new Noty({ text: responseText, type: "error" }).show();
        console.error(response);
      },
    });
  },

  requestApproval: function (record, admin_override) {
    var me = this;
    Ext.Ajax.request({
      url: Ext.String.format(
        "api/requests/{0}/request_approval/",
        record.get("pk")
      ),
      method: "GET",
      scope: me,
      params: {
        data: Ext.JSON.encode({
          override: admin_override,
        }),
      },
      success: function (response) {
        var obj = Ext.JSON.decode(response.responseText);

        if (obj.success) {
          Ext.getStore("requestsStore").reload();
          new Noty({ text: "Approval has been successfully requested" }).show();
        } else {
          new Noty({ text: obj.message, type: "error" }).show();
        }
      },

      failure: function (response) {
        var responseText = response.responseText
          ? Ext.JSON.decode(response.responseText)
          : null;
        responseText = responseText.message
          ? responseText.message
          : "Unknown error.";
        responseText = response.statusText ? response.statusText : responseText;
        new Noty({ text: responseText, type: "error" }).show();
        console.error(response);
      },
    });
  },

  deleteRequest: function (record) {
    Ext.Ajax.request({
      url: Ext.String.format("api/requests/{0}/", record.get("pk")),
      method: "DELETE",
      scope: this,

      success: function (response) {
        var obj = Ext.JSON.decode(response.responseText);

        if (obj.success) {
          Ext.getStore("requestsStore").reload();
          new Noty({ text: "The request has been deleted!" }).show();
        } else {
          new Noty({ text: obj.message, type: "error" }).show();
        }
      },

      failure: function (response) {
        var obj = Ext.JSON.decode(response.responseText);
        new Noty({ text: obj.message, type: "error" }).show();
        console.error(response);
      },
    });
  },

  uploadSignedRequest: function (requestId) {
    var url = Ext.String.format(
      "api/requests/{0}/upload_deep_sequencing_request/",
      requestId
    );

    Ext.create("Ext.ux.FileUploadWindow", {
      onFileUpload: function () {
        var uploadWindow = this;
        var form = this.down("form").getForm();

        if (!form.isValid()) {
          new Noty({
            text: "You did not select any file.",
            type: "warning",
          }).show();
          return false;
        }

        form.submit({
          url: url,
          method: "POST",
          waitMsg: "Uploading...",

          success: function (f, action) {
            var obj = Ext.JSON.decode(action.response.responseText);
            if (obj.success) {
              new Noty({
                text: "Deep Sequencing Request has been successfully uploaded.",
              }).show();
              Ext.getStore("requestsStore").reload();
            } else {
              new Noty({ text: obj.message, type: "error" }).show();
            }
            uploadWindow.close();
          },

          failure: function (f, action) {
            var errorMsg;
            if (action.failureType === "server") {
              errorMsg = action.result.message
                ? action.result.message
                : "Server error.";
            } else {
              errorMsg = "Error.";
            }
            new Noty({ text: errorMsg, type: "error" }).show();
            console.error(action);
          },
        });
      },
    });
  },
});

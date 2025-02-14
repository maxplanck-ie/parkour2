Ext.define("MainHub.view.incominglibrariesvue.IncomingLibrariesVue", {
  extend: "Ext.container.Container",
  xtype: "incoming-libraries-vue",

  layout: "fit",

  initComponent: function () {
    this.callParent(arguments);

    this.addIframe();
  },

  listeners: {
    activate: function () {
      if (!this.down("#incomingLibrariesIframe")) {
        this.addIframe();
      } else {
        this.reloadIframe();
      }
    },

    deactivate: function () {
      this.removeIframe();
    },

    destroy: function () {
      this.removeIframe();
    }
  },

  addIframe: function () {
    this.add({
      xtype: "component",
      itemId: "incomingLibrariesIframe",
      html:
        '<iframe id="incomingLibrariesIframe" src="' +
        window.location.origin +
        '/vue/incoming_libraries_samples" width="100%" height="100%" frameborder="0"></iframe>'
    });
  },

  reloadIframe: function () {
    var iframe = document.getElementById("incomingLibrariesIframe");
    if (iframe) {
      iframe.contentWindow.location.href = iframe.src;
    }
  },

  removeIframe: function () {
    var iframeComponent = this.down("#incomingLibrariesIframe");
    if (iframeComponent) {
      this.remove(iframeComponent, true);
    }
  }
});

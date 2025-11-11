Ext.define("MainHub.view.librariesvue.LibrariesVue", {
  extend: "Ext.container.Container",
  xtype: "libraries-vue",

  layout: "fit",

  initComponent: function () {
    this.callParent(arguments);

    this.addIframe();
  },

  listeners: {
    activate: function () {
      if (!this.down("#librariesIframe")) {
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
      itemId: "librariesIframe",
      html:
        '<iframe id="librariesIframe" src="' +
        window.location.origin +
        '/vue/libraries_and_samples" width="100%" height="100%" frameborder="0"></iframe>'
    });
  },

  reloadIframe: function () {
    var iframe = document.getElementById("librariesIframe");
    if (iframe) {
      iframe.contentWindow.location.href = iframe.src;
    }
  },

  removeIframe: function () {
    var iframeComponent = this.down("#librariesIframe");
    if (iframeComponent) {
      this.remove(iframeComponent, true);
    }
  }
});

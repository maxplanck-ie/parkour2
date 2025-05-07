Ext.define("MainHub.view.poolingvue.PoolingVue", {
  extend: "Ext.container.Container",
  xtype: "pooling-vue",

  layout: "fit",

  initComponent: function () {
    this.callParent(arguments);

    this.addIframe();
  },

  listeners: {
    activate: function () {
      if (!this.down("#poolingIframe")) {
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
      itemId: "poolingIframe",
      html:
        '<iframe id="poolingIframe" src="' +
        window.location.origin +
        '/vue/pooling" width="100%" height="100%" frameborder="0"></iframe>'
    });
  },

  reloadIframe: function () {
    var iframe = document.getElementById("poolingIframe");
    if (iframe) {
      iframe.contentWindow.location.href = iframe.src;
    }
  },

  removeIframe: function () {
    var iframeComponent = this.down("#poolingIframe");
    if (iframeComponent) {
      this.remove(iframeComponent, true);
    }
  }
});

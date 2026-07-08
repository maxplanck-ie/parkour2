Ext.define("MainHub.view.indexgeneratorvue.IndexGeneratorVue", {
  extend: "Ext.container.Container",
  xtype: "index-generator-vue",

  layout: "fit",
  iframeDomId: "indexGeneratorIframe",

  initComponent: function () {
    this.callParent(arguments);

    this.addIframe();
  },

  listeners: {
    activate: function () {
      if (!this.down("#" + this.iframeDomId)) {
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
      itemId: this.iframeDomId,
      html:
        '<iframe id="' +
        this.iframeDomId +
        '" src="' +
        window.location.origin +
        '/vue/index_generator" width="100%" height="100%" frameborder="0"></iframe>'
    });
  },

  reloadIframe: function () {
    var iframe = document.getElementById(this.iframeDomId);
    if (iframe) {
      iframe.contentWindow.location.href = iframe.src;
    }
  },

  removeIframe: function () {
    var iframeComponent = this.down("#" + this.iframeDomId);
    if (iframeComponent) {
      this.remove(iframeComponent, true);
    }
  }
});

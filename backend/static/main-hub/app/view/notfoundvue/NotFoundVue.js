Ext.define("MainHub.view.notfoundvue.NotFoundVue", {
  extend: "Ext.container.Container",
  xtype: "not-found-vue",

  layout: "fit",
  iframeDomId: "notFoundIframe",

  initComponent: function () {
    this.callParent(arguments);
    this.addIframe();
  },

  listeners: {
    activate: function () {
      if (!this.down("#" + this.iframeDomId)) {
        this.addIframe();
      }
    },

    deactivate: function () {
      this.removeIframe();
    },

    destroy: function () {
      this.removeIframe();
    }
  },

  getIframeSrc: function () {
    var missingRoute = this.missingRoute || "";
    return (
      window.location.origin +
      "/vue/not-found?missingRoute=" +
      encodeURIComponent(missingRoute)
    );
  },

  addIframe: function () {
    this.add({
      xtype: "component",
      itemId: this.iframeDomId,
      html:
        '<iframe id="' +
        this.iframeDomId +
        '" src="' +
        this.getIframeSrc() +
        '" width="100%" height="100%" frameborder="0"></iframe>'
    });
  },

  removeIframe: function () {
    var iframeComponent = this.down("#" + this.iframeDomId);
    if (iframeComponent) {
      this.remove(iframeComponent, true);
    }
  }
});

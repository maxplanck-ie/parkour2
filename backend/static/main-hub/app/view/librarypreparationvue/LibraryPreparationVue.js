Ext.define("MainHub.view.librarypreparationvue.LibraryPreparationVue", {
  extend: "Ext.container.Container",
  xtype: "library-preparation-vue",

  layout: "fit",

  initComponent: function () {
    this.callParent(arguments);

    this.addIframe();
  },

  listeners: {
    activate: function () {
      if (!this.down("#libraryPreparationIframe")) {
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
      itemId: "libraryPreparationIframe",
      html:
        '<iframe id="libraryPreparationIframe" src="' +
        window.location.origin +
        '/vue/library_preparation" width="100%" height="100%" frameborder="0"></iframe>'
    });
  },

  reloadIframe: function () {
    var iframe = document.getElementById("libraryPreparationIframe");
    if (iframe) {
      iframe.contentWindow.location.href = iframe.src;
    }
  },

  removeIframe: function () {
    var iframeComponent = this.down("#libraryPreparationIframe");
    if (iframeComponent) {
      this.remove(iframeComponent, true);
    }
  }
});

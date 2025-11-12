Ext.define("MainHub.view.incominglibrariesvue.IncomingLibrariesVue", {
  extend: "Ext.container.Container",
  xtype: "incoming-libraries-vue",

  layout: "fit",
  iframeDomId: "incomingLibrariesIframe",

  initComponent: function () {
    this.callParent(arguments);

    this.setupParentClickRelay();
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
      this.teardownParentClickRelay();
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
        '/vue/incoming_libraries_samples" width="100%" height="100%" frameborder="0"></iframe>'
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
  },

  setupParentClickRelay: function () {
    if (this.parentPointerListener) {
      return;
    }

    var me = this;
    me.parentPointerEventName =
      window && window.PointerEvent ? "pointerdown" : "mousedown";
    me.parentPointerListener = Ext.bind(me.relayPointerEventToIframe, me);

    document.addEventListener(
      me.parentPointerEventName,
      me.parentPointerListener,
      true
    );
  },

  relayPointerEventToIframe: function (event) {
    if (!this.isVisible(true)) {
      return;
    }

    var iframe = document.getElementById(this.iframeDomId);
    if (!iframe || event.target === iframe || !iframe.contentWindow) {
      return;
    }

    iframe.contentWindow.postMessage(
      {
        source: "mainhub-ext",
        type: "parent-pointer-down"
      },
      window.location.origin
    );
  },

  teardownParentClickRelay: function () {
    if (!this.parentPointerListener) {
      return;
    }

    document.removeEventListener(
      this.parentPointerEventName,
      this.parentPointerListener,
      true
    );
    this.parentPointerListener = null;
  }
});

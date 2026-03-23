Ext.define("MainHub.view.main.MainContainerWrap", {
  extend: "Ext.container.Container",
  xtype: "maincontainerwrap",

  requires: [],

  scrollable: false,

  layout: {
    type: "fit"
  },

  beforeLayout: function () {
    // We setup some minHeights dynamically to ensure we stretch to fill the height
    // of the viewport minus the top toolbar

    var me = this,
      height = Ext.Element.getViewportHeight() - 68, // offset by topmost toolbar height
      // We use itemId/getComponent instead of "reference" because the initial
      // layout occurs too early for the reference to be resolved
      navTree = me.getComponent("navigationTreeList");

    me.minHeight = height;

    if (navTree) {
      navTree.setStyle({
        "min-height": height + "px"
      });
    }

    me.callParent(arguments);
  }
});

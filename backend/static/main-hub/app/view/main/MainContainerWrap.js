Ext.define("MainHub.view.main.MainContainerWrap", {
  extend: "Ext.container.Container",
  xtype: "maincontainerwrap",

  requires: [],

  scrollable: "y",

  layout: {
    type: "hbox",
    align: "stretchmax",
    animate: true,
    animatePolicy: {
      x: true,
      width: true
    }
  },

  beforeLayout: function () {
    var me = this,
      height = Ext.Element.getViewportHeight();

    me.minHeight = height;
    me.setHeight(height);
    me.callParent(arguments);
  }
});

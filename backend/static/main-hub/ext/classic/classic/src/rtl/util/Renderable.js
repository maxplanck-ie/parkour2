Ext.define("Ext.rtl.util.Renderable", {
  override: "Ext.util.Renderable",

  _rtlCls: Ext.baseCSSPrefix + "rtl",
  _ltrCls: Ext.baseCSSPrefix + "ltr",

  // this template should be exactly the same as frameTableTpl, except with the order
  // of right and left TD elements switched.
  rtlFrameTableTpl: [
    "<tpl if=\"hasTabGuard\">{% this.renderTabGuard(out, values, 'before'); %}</tpl>",
    '<table id="{fgid}Table" data-ref="frameTable" class="{frameCls} ',
    Ext.baseCSSPrefix + 'table-plain" cellpadding="0" role="presentation">',
    '<tpl if="top">',
    '<tr role="presentation">',
    '<tpl if="right"><td id="{fgid}TR" data-ref="frameTR" class="{frameCls}-tr {baseCls}-tr {baseCls}-{ui}-tr<tpl for="uiCls"> {parent.baseCls}-{parent.ui}-{.}-tr</tpl>{frameElCls}" role="presentation"></td></tpl>',
    '<td id="{fgid}TC" data-ref="frameTC" class="{frameCls}-tc {baseCls}-tc {baseCls}-{ui}-tc<tpl for="uiCls"> {parent.baseCls}-{parent.ui}-{.}-tc</tpl>{frameElCls}" role="presentation"></td>',
    '<tpl if="left"><td id="{fgid}TL" data-ref="frameTL" class="{frameCls}-tl {baseCls}-tl {baseCls}-{ui}-tl<tpl for="uiCls"> {parent.baseCls}-{parent.ui}-{.}-tl</tpl>{frameElCls}" role="presentation"></td></tpl>',
    "</tr>",
    "</tpl>",
    '<tr role="presentation">',
    '<tpl if="right"><td id="{fgid}MR" data-ref="frameMR" class="{frameCls}-mr {baseCls}-mr {baseCls}-{ui}-mr<tpl for="uiCls"> {parent.baseCls}-{parent.ui}-{.}-mr</tpl>{frameElCls}" role="presentation"></td></tpl>',
    '<td id="{fgid}Body" data-ref="frameBody" class="{frameBodyCls} {frameCls}-mc {baseCls}-mc {baseCls}-{ui}-mc<tpl for="uiCls"> {parent.baseCls}-{parent.ui}-{.}-mc</tpl>{frameElCls}" style="{mcStyle}" role="presentation">',
    "{%this.applyRenderTpl(out, values)%}",
    "</td>",
    '<tpl if="left"><td id="{fgid}ML" data-ref="frameML" class="{frameCls}-ml {baseCls}-ml {baseCls}-{ui}-ml<tpl for="uiCls"> {parent.baseCls}-{parent.ui}-{.}-ml</tpl>{frameElCls}" role="presentation"></td></tpl>',
    "</tr>",
    '<tpl if="bottom">',
    '<tr role="presentation">',
    '<tpl if="right"><td id="{fgid}BR" data-ref="frameBR" class="{frameCls}-br {baseCls}-br {baseCls}-{ui}-br<tpl for="uiCls"> {parent.baseCls}-{parent.ui}-{.}-br</tpl>{frameElCls}" role="presentation"></td></tpl>',
    '<td id="{fgid}BC" data-ref="frameBC" class="{frameCls}-bc {baseCls}-bc {baseCls}-{ui}-bc<tpl for="uiCls"> {parent.baseCls}-{parent.ui}-{.}-bc</tpl>{frameElCls}" role="presentation"></td>',
    '<tpl if="left"><td id="{fgid}BL" data-ref="frameBL" class="{frameCls}-bl {baseCls}-bl {baseCls}-{ui}-bl<tpl for="uiCls"> {parent.baseCls}-{parent.ui}-{.}-bl</tpl>{frameElCls}" role="presentation"></td></tpl>',
    "</tr>",
    "</tpl>",
    "</table>",
    "<tpl if=\"hasTabGuard\">{% this.renderTabGuard(out, values, 'after'); %}</tpl>"
  ],

  beforeRender: function () {
    var rtl = this.getInherited().rtl;
    if (rtl) {
      this.addCls(this._rtlCls);
    } else if (rtl === false) {
      this.addCls(this._ltrCls);
    }

    this.callParent();
  },

  initRenderData: function () {
    var me = this,
      renderData = me.callParent(),
      rtlCls = me._rtlCls;

    if (rtlCls && me.getInherited().rtl) {
      renderData.childElCls = " " + rtlCls;
    }

    return renderData;
  },

  privates: {
    getFrameTpl: function (table) {
      return table && this.getInherited().rtl
        ? this.lookupTpl("rtlFrameTableTpl")
        : this.callParent(arguments);
    },

    getFrameRenderData: function () {
      var me = this,
        data = me.callParent(),
        rtlCls = me._rtlCls;

      if (rtlCls && me.getInherited().rtl) {
        data.frameElCls = " " + rtlCls;
      }

      return data;
    }
  }
});

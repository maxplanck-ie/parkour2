Ext.define("MainHub.view.main.Main", {
  extend: "Ext.container.Viewport",

  requires: [
    "Ext.list.Tree",
    "Ext.tab.Panel",
    "MainHub.view.main.MainController",
    "MainHub.view.main.MainContainerWrap",
    "MainHub.view.librariesvue.LibrariesVue",
    "MainHub.view.incominglibrariesvue.IncomingLibrariesVue",
    "MainHub.view.indexgenerator.IndexGenerator",
    "MainHub.view.librarypreparationvue.LibraryPreparationVue",
    "MainHub.view.poolingvue.PoolingVue",
    "MainHub.view.flowcell.Flowcells",
    "MainHub.view.invoicing.Invoicing",
    "MainHub.view.usage.Usage",
    "MainHub.view.statistics.RunStatistics",
    "MainHub.view.statistics.Sequences"
  ],

  controller: "main",

  cls: "sencha-dash-viewport",
  itemd: "mainView",

  layout: {
    type: "vbox",
    align: "stretch"
  },

  listeners: {
    render: "onMainViewRender"
  },

  items: [
    {
      xtype: "toolbar",
      id: "headerBar",
      itemId: "headerBar",
      cls: "sencha-dash-dash-headerbar shadow bg-color-beige",
      height: 68,
      padding: 0,
      enableOverflow: true,
      overflowHandler: "scroller",
      items: [
        {
          xtype: "component",
          reference: "logo",
          cls: "main-logo",
          html: '<div class="logo"><img src="static/main-hub/resources/images/logo1.svg"><div id="header-title" class="title">Parkour LIMS</div></div>',
          style: "width: auto; height: 72px;"
        },
        {
          xtype: "toolbar",
          reference: "topNavToolbar",
          itemId: "topNavToolbar",
          cls: "header-nav-toolbar",
          flex: 1,
          layout: {
            type: "hbox",
            pack: "start"
          },
          defaults: {
            ui: "header"
          },
          items: []
        },
        {
          xtype: "container",
          cls: "header-user-actions",
          style: "margin-left: auto;",
          layout: {
            type: "hbox",
            align: "middle"
          },
          items: [
            {
              xtype: "tbtext",
              cls: "header-username color-bluish-grey",
              text: USER.name // from 'globals.html'
            },
            {
              xtype: "button",
              ui: "header",
              id: "adminSiteBtn",
              iconCls: "x-fa fa-cog color-bluish-grey",
              href: "admin",
              tooltip: "Site Administration"
            },
            {
              xtype: "button",
              ui: "header",
              iconCls: "x-fa fa-book color-bluish-grey",
              href: "https://github.com/maxplanck-ie/parkour2/wiki/Introduction",
              tooltip: "Documentation"
            },
            {
              xtype: "button",
              ui: "header",
              id: "dutiesBtn",
              iconCls: "x-fa fa-calendar color-bluish-grey",
              href: "vue/duties",
              tooltip: "Duties"
            },
            {
              xtype: "container",
              html: `
                <form id="logout-form" method="post" action="logout/" style="display:inline;">
                    <input type="hidden" name="csrfmiddlewaretoken" value="${CSRF_TOKEN}">
                    <button type="submit" style="background: none; padding: 0px; border: none; cursor: pointer">
                        <i style="font-size: 16px; font-style: normal !important; padding: 0px;" class="x-fa fa-sign-out color-bluish-grey"></i>
                    </button>
                </form>
              `,
              width: 30,
              height: 30,
              padding: 7,
              listeners: {
                render: function (component) {
                  Ext.create("Ext.tip.ToolTip", {
                    target: component.getEl(),
                    html: "Logout"
                  });
                }
              }
            }
          ]
        }
      ]
    },
    {
      xtype: "maincontainerwrap",
      id: "main-view-detail-wrap",
      reference: "mainContainerWrap",
      flex: 1,
      height: "100%",
      items: [
        {
          xtype: "container",
          flex: 1,
          height: "100%",
          reference: "mainCardPanel",
          cls: "sencha-dash-right-main-container",
          itemId: "contentPanel",
          layout: {
            type: "card",
            anchor: "100%"
          }
        }
      ]
    }
  ]
});

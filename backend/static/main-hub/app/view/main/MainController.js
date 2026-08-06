Ext.define("MainHub.view.main.MainController", {
  extend: "Ext.app.ViewController",
  alias: "controller.main",

  listen: {
    controller: {
      "#": {
        unmatchedroute: "onRouteChange"
      }
    }
  },

  routes: {
    ":node": "onRouteChange"
  },

  lastView: null,

  disabledRoutes: {
    requests: "libraries-vue",
    libraries: "libraries-vue",
    "incoming-libraries": "incoming-libraries-vue",
    "index-generator": "index-generator-vue",
    indexgenerator: "index-generator-vue",
    preparation: "library-preparation-vue",
    "library-preparation": "library-preparation-vue",
    pooling: "pooling-vue",
    flowcells: "flowcells-vue",
    "run-statistics": "run-statistics-vue",
    "sequences-statistics": "sequences-statistics-vue",
    invoicing: "invoicing-vue"
  },

  onMainViewRender: function () {
    var me = this;
    me.ensureTopNavStyles();
    me.bindHeaderLayoutFix();

    Ext.getStore("NavigationTree").on("load", function (store) {
      me.buildTopNavigation(store);
      if (!window.location.hash) {
        me.redirectTo("libraries-vue");
      }
    });

    if (!USER.is_staff) {
      Ext.getCmp("adminSiteBtn").hide();
      Ext.getCmp("dutiesBtn").hide();
    }
  },

  ensureTopNavStyles: function () {
    if (Ext.get("top-nav-styles")) {
      return;
    }

    Ext.util.CSS.createStyleSheet(
      [
        ".header-nav-toolbar {",
        "  padding: 6px 10px;",
        "  margin-left: 14px;",
        "  border-radius: 14px;",
        "  background: rgba(255, 255, 255, 0.9);",
        "  border: 1px solid #d8d8d8;",
        "  display: flex;",
        "  flex: 1 1 auto;",
        "  width: auto;",
        "  min-width: 0;",
        "  overflow: hidden;",
        "  gap: 8px;",
        "}",
        ".header-nav-toolbar .header-nav-button {",
        "  margin-left: 0;",
        "  border-radius: 12px;",
        "  background: rgba(255, 255, 255, 0.92);",
        "  border: 1px solid #d8d8d8;",
        "  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.5);",
        "  height: 30px;",
        "  padding: 0 9px;",
        "  height: 32px;",
        "  padding: 0 9px;",
        "}",
        ".header-nav-toolbar .header-nav-button .x-btn-inner {",
        "  color: #4d5b63;",
        "  font-weight: 600;",
        "  margin-left: 6px;",
        "}",
        ".header-nav-toolbar .header-nav-button .x-btn-icon-el {",
        "  color: #4d5b63;",
        "}",
        ".header-nav-toolbar .header-nav-button .x-btn-arrow-right,",
        ".header-nav-toolbar .header-nav-button .x-btn-arrow-bottom {",
        "  filter: brightness(0.2);",
        "}",
        ".header-nav-toolbar .header-nav-button:hover {",
        "  background: #eef3f3;",
        "  border-color: #bfc9c9;",
        "}",
        ".header-nav-toolbar .header-nav-button-active,",
        ".header-nav-toolbar .x-btn-pressed.header-nav-button {",
        "  background: #d9efed;",
        "  border-color: #0b7f78;",
        "}",
        ".header-nav-toolbar .header-nav-button-active .x-btn-icon-el,",
        ".header-nav-toolbar .x-btn-pressed.header-nav-button .x-btn-icon-el {",
        "  color: #0b7f78;",
        "}",
        ".main-logo {",
        "  width: 200px !important;",
        "  height: 68px;",
        "  padding: 0 20px 0 0;",
        "  margin-left: 10px;",
        "  margin-right: 6px;",
        "}"
        ,
        ".main-logo .logo {",
        "  display: flex;",
        "  align-items: center;",
        "  height: 68px;",
        "  line-height: 68px;",
        "  position: static;",
        "}",
        ".main-logo .logo img {",
        "  position: static;",
        "  margin: 0 14px 0 10px;",
        "}",
        ".main-logo .logo .title {",
        "  margin-left: 0;",
        "}"
        ,
        ".header-user-actions {",
        "  display: flex;",
        "  align-items: center;",
        "  padding: 5px 10px;",
        "  border: 1px solid #d8d8d8;",
        "  border-radius: 12px;",
        "  background: rgba(255, 255, 255, 0.92);",
        "  flex: 0 0 auto;",
        "}",
        ".header-user-actions .header-username {",
        "  margin-right: 6px;",
        "  max-width: 140px;",
        "  overflow: hidden;",
        "  text-overflow: ellipsis;",
        "  white-space: nowrap;",
        "}",
        ".header-user-actions .x-btn {",
        "  margin-left: 6px;",
        "}",
        "@media (max-width: 1919px) {",
        "  .header-nav-toolbar .header-nav-button .x-btn-inner {",
        "    display: none;",
        "  }",
        "  .header-nav-toolbar .header-nav-button {",
        "    padding: 0 6px;",
        "  }",
        "}"
      ].join("\n"),
      "top-nav-styles"
    );
  },

  bindHeaderLayoutFix: function () {
    var me = this,
      refs = me.getReferences(),
      headerBar = Ext.getCmp("headerBar"),
      logoCmp = refs && refs.logo;

    if (!headerBar || !logoCmp) {
      return;
    }

    var scheduleLayout = function () {
      Ext.defer(function () {
        if (!headerBar.destroyed) {
          headerBar.updateLayout();
        }
      }, 0);
    };

    var bindLogoLoad = function () {
      var imgEl = logoCmp.getEl() && logoCmp.getEl().down("img");
      if (imgEl) {
        imgEl.on("load", scheduleLayout, null, { single: true });
      }
    };

    if (logoCmp.rendered) {
      bindLogoLoad();
    } else {
      logoCmp.on("afterrender", bindLogoLoad, null, { single: true });
    }

    scheduleLayout();
  },

  buildTopNavigation: function (store) {
    var me = this,
      refs = me.getReferences(),
      toolbar = refs.topNavToolbar,
      root = store && store.getRoot();

    if (!toolbar || !root) {
      return;
    }

    toolbar.removeAll();

    root.eachChild(function (node) {
      if (node.get("hidden")) {
        return;
      }

      var menu = me.buildMenuForNode(node);
      var route = node.get("routeId") || node.get("viewType");

      toolbar.add({
        xtype: "button",
        ui: "header",
        cls: "header-nav-button",
        iconCls: node.get("iconCls"),
        text: node.get("text"),
        iconAlign: "left",
        tooltip: node.get("text"),
        navNodeId: node.getId(),
        navRouteId: route,
        menu: menu,
        handler: !menu
          ? function () {
            if (route) {
              me.redirectTo(route);
            }
          }
          : null
      });
    });

    Ext.defer(function () {
      toolbar.updateLayout();
      var headerBar = toolbar.up("toolbar");
      if (headerBar) {
        headerBar.updateLayout();
      }
    }, 0);
  },

  buildMenuForNode: function (node) {
    var me = this,
      items = [];

    node.eachChild(function (child) {
      if (child.get("hidden")) {
        return;
      }

      var childRoute = child.get("routeId") || child.get("viewType");
      var childMenu = me.buildMenuForNode(child);

      items.push({
        text: child.get("text"),
        iconCls: child.get("iconCls"),
        menu: childMenu,
        handler: !childMenu
          ? function () {
            if (childRoute) {
              me.redirectTo(childRoute);
            }
          }
          : null
      });
    });

    if (!items.length) {
      return null;
    }

    return Ext.create("Ext.menu.Menu", {
      items: items
    });
  },

  setCurrentView: function (hashTag) {
    hashTag = (hashTag || "").toLowerCase();

    var me = this,
      fallbackRoute = me.disabledRoutes[hashTag],
      refs,
      mainCard,
      mainLayout,
      store,
      node,
      view,
      lastView,
      existingItem,
      baseTitle = "Parkour LIMS",
      newView;

    if (fallbackRoute) {
      me.redirectTo(fallbackRoute);
      return;
    }

    refs = me.getReferences();
    mainCard = refs.mainCardPanel;
    mainLayout = mainCard.getLayout();
    store = Ext.getStore("NavigationTree");
    node =
      (store &&
        (store.findNode("routeId", hashTag) ||
          store.findNode("viewType", hashTag))) ||
      null;
    view = (node && node.get("viewType")) || "not-found-vue";
    lastView = me.lastView;
    existingItem = mainCard.child("component[routeId=" + hashTag + "]");

    // Set Page Title
    document.title = node
      ? baseTitle + " | " + node.data.text
      : baseTitle + " | 404";

    // Kill any previously routed window
    if (lastView && lastView.isWindow) {
      lastView.destroy();
    }

    lastView = mainLayout.getActiveItem();

    if (!existingItem) {
      newView = Ext.create({
        xtype: view,
        missingRoute: "#" + hashTag,
        routeId: hashTag, // for existingItem search later
        hideMode: "offsets"
      });
    }

    if (!newView || !newView.isWindow) {
      // !newView means we have an existing view, but if the newView isWindow
      // we don't add it to the card layout.
      if (existingItem) {
        // We don't have a newView, so activate the existing view.
        if (existingItem !== lastView) {
          mainLayout.setActiveItem(existingItem);
        }
        newView = existingItem;
      } else {
        // newView is set (did not exist already), so add it and make it the
        // activeItem.
        Ext.suspendLayouts();
        mainLayout.setActiveItem(mainCard.add(newView));
        Ext.resumeLayouts(true);
      }
    }

    me.updateTopNavSelection(node, store);

    if (newView.isFocusable(true)) {
      newView.focus();
    }

    me.lastView = newView;
  },

  onRouteChange: function (id) {
    var me = this,
      store = Ext.getStore("NavigationTree");

    // If a page is loaded for the first time
    store.on("load", function () {
      me.setCurrentView(id);
    });

    // If a page is changed
    if (store.getCount() > 0) {
      me.setCurrentView(id);
    }
  },
  updateTopNavSelection: function (node, store) {
    var me = this,
      refs = me.getReferences(),
      toolbar = refs.topNavToolbar;

    if (!toolbar) {
      return;
    }

    toolbar.items.each(function (item) {
      if (item && item.removeCls) {
        item.removeCls("header-nav-button-active");
      }
    });

    if (!node || !store) {
      return;
    }

    var topNode = node;
    while (topNode.parentNode && topNode.parentNode !== store.getRoot()) {
      topNode = topNode.parentNode;
    }

    toolbar.items.each(function (item) {
      if (item && item.navNodeId && item.navNodeId === topNode.getId()) {
        item.addCls("header-nav-button-active");
      }
    });
  }
});

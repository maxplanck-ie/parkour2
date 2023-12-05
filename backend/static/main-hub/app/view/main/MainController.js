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

  onMainViewRender: function () {
    var me = this;

    Ext.getStore("NavigationTree").on("load", function () {
      if (!window.location.hash) {
        me.redirectTo("requests");
      }
    });

    if (!USER.is_staff) {
      Ext.getCmp("adminSiteBtn").hide();
      Ext.getCmp("dutiesBtn").hide();
    }
  },

  setCurrentView: function (hashTag) {
    hashTag = (hashTag || "").toLowerCase();

    var me = this,
      refs = me.getReferences(),
      mainCard = refs.mainCardPanel,
      mainLayout = mainCard.getLayout(),
      lastView = me.lastView,
      existingItem = mainCard.child("component[routeId=" + hashTag + "]"),
      baseTitle = "Parkour LIMS",
      newView;

    // Set Page Title
    document.title = baseTitle + " | " + hashTag;

    // Kill any previously routed window
    if (lastView && lastView.isWindow) {
      lastView.destroy();
    }

    lastView = mainLayout.getActiveItem();

    if (!existingItem) {
      newView = Ext.create({
        xtype: hashTag || "page404",
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
  }
});

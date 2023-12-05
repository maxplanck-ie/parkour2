Ext.define("MainHub.view.main.Main", {
  extend: "Ext.container.Viewport",

  requires: [
    "Ext.list.Tree",
    "Ext.tab.Panel",
    "MainHub.view.main.MainController",
    "MainHub.view.main.MainContainerWrap",
    "MainHub.view.requests.Requests",
    "MainHub.view.libraries.Libraries",
    "MainHub.view.incominglibraries.IncomingLibraries",
    "MainHub.view.indexgenerator.IndexGenerator",
    "MainHub.view.librarypreparation.LibraryPreparation",
    "MainHub.view.pooling.Pooling",
    "MainHub.view.flowcell.Flowcells",
    "MainHub.view.invoicing.Invoicing",
    "MainHub.view.usage.Usage",
    "MainHub.view.statistics.RunStatistics",
    "MainHub.view.statistics.Sequences"
  ],

  controller: "main",

  cls: "sencha-dash-viewport",
  itemd: "viewport",

  layout: {
    type: "vbox",
    align: "stretch"
  },

  listeners: {
    render: "onMainViewRender"
  },

  items: [
    {
      xtype: "maincontainerwrap",
      id: "main-view-detail-wrap",
      reference: "mainContainerWrap",
      flex: 1,
      items: [
        {
          xtype: "container",
          flex: 1,
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

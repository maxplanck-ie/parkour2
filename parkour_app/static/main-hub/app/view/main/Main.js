Ext.define('MainHub.view.main.Main', {
    extend: 'Ext.container.Viewport',

    requires: [
        'Ext.list.Tree',
        'Ext.tab.Panel',
        'MainHub.view.main.MainController',
        'MainHub.view.main.MainContainerWrap',
        'MainHub.view.requests.Requests',
        'MainHub.view.libraries.Libraries',
        'MainHub.view.incominglibraries.IncomingLibraries',
        'MainHub.view.indexgenerator.IndexGenerator',
        'MainHub.view.librarypreparation.LibraryPreparation',
        'MainHub.view.pooling.Pooling',
        'MainHub.view.flowcell.Flowcells',
        'MainHub.view.invoicing.Invoicing',
        'MainHub.view.usage.Usage',
        'MainHub.view.statistics.RunStatistics',
        'MainHub.view.statistics.Sequences'
    ],

    controller: 'main',

    cls: 'sencha-dash-viewport',
    itemd: 'mainView',

    layout: {
        type: 'vbox',
        align: 'stretch'
    },

    listeners: {
        render: 'onMainViewRender'
    },

    items: [
        {
            xtype: 'toolbar',
            id: 'headerBar',
            itemId: 'headerBar',
            cls: 'sencha-dash-dash-headerbar shadow',
            height: 64,
            padding: 0,
            items: [
                {
                    xtype: 'component',
                    reference: 'logo',
                    cls: 'main-logo',
                    html: '<div class="logo"><img src="static/main-hub/resources/images/logo1.svg"><div class="title">Parkour LIMS</div></div>',
                    width: 300
                },
                {
                    margin: '0 0 0 8',
                    // ui: 'header',
                    iconCls: 'x-fa fa-navicon',
                    id: 'main-navigation-btn',
                    handler: 'onToggleNavigationSize'
                },
                '->',
                {
                    xtype: 'tbtext',
                    cls: 'top-user-name',
                    text: USER.name      // from 'globals.html'
                },
                {
                    xtype: 'button',
                    ui: 'header',
                    id: 'adminSiteBtn',
                    iconCls: 'x-fa fa-cog',
                    href: 'admin',
                    tooltip: 'Site administration'
                },
                {
                    xtype: 'button',
                    ui: 'header',
                    iconCls: 'x-fa fa-book',
                    href: 'https://parkour.readthedocs.io/',
                    tooltip: 'Documentation'
                },
                {
                    xtype: 'button',
                    ui: 'header',
                    iconCls: 'x-fa fa-sign-out',
                    href: 'logout',
                    hrefTarget:'_self',
                    tooltip: 'Logout'
                }
            ]
        },
        {
            xtype: 'maincontainerwrap',
            id: 'main-view-detail-wrap',
            reference: 'mainContainerWrap',
            flex: 1,
            items: [
                {
                    xtype: 'treelist',
                    reference: 'navigationTreeList',
                    itemId: 'navigationTreeList',
                    ui: 'navigation',
                    store: 'NavigationTree',
                    width: 300,
                    expanderFirst: false,
                    expanderOnly: false,
                    listeners: {
                        selectionchange: 'onNavigationTreeSelectionChange'
                    }
                },
                {
                    xtype: 'container',
                    flex: 1,
                    reference: 'mainCardPanel',
                    cls: 'sencha-dash-right-main-container',
                    itemId: 'contentPanel',
                    layout: {
                        type: 'card',
                        anchor: '100%'
                    }
                }
            ]
        }
    ]
});

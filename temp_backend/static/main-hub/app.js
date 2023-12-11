/*
 * This file is generated and updated by Sencha Cmd. You can edit this file as
 * needed for your application, but these edits will have to be merged by
 * Sencha Cmd when upgrading.
 */
Ext.application({
    name: 'MainHub',

    extend: 'MainHub.Application',

    appFolder: '/static/main-hub/app',

    requires: [
        'MainHub.overrides.list.RootTreeItem',
        'MainHub.overrides.grid.plugin.Clipboard',
        'MainHub.overrides.grid.plugin.RowExpander',
        'MainHub.overrides.grid.plugin.RowEditing',
        'MainHub.overrides.grid.selection.SpreadsheetModel',
        'MainHub.overrides.data.PageMap',
        'MainHub.overrides.Date',
        'MainHub.overrides.picker.Date',
        'MainHub.view.main.Main'
    ],

    // The name of the initial view to create. With the classic toolkit this class
    // will gain a "viewport" plugin if it does not extend Ext.Viewport. With the
    // modern toolkit, the main view will be added to the Viewport.
    //
    mainView: 'MainHub.view.main.Main'

    //-------------------------------------------------------------------------
    // Most customizations should be made to MainHub.Application. If you need to
    // customize this file, doing so below this section reduces the likelihood
    // of merge conflicts when upgrading to new versions of Sencha Cmd.
    //-------------------------------------------------------------------------
});

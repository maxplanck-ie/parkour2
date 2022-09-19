Ext.define('MainHub.store.flowcell.Sequencer', {
    extend: 'Ext.data.Store',
    storeId: 'sequencersStore',

    requires: [
        'MainHub.model.flowcell.Sequencer'
    ],

    model: 'MainHub.model.flowcell.Sequencer',

    proxy: {
        type: 'ajax',
        url: 'api/sequencers/',
        // timeout: 1000000,
        pageParam: false,   //to remove param "page"
        startParam: false,  //to remove param "start"
        limitParam: false,  //to remove param "limit"
        noCache: false,     //to remove param "_dc",
        reader: {
            type: 'json',
            rootProperty: 'data',
            successProperty: 'success'
        }
    },

    autoLoad: true
});

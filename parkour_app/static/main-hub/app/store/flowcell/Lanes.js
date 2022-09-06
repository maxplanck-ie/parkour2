Ext.define('MainHub.store.flowcell.Lanes', {
    extend: 'Ext.data.Store',
    storeId: 'lanesStore',

    requires: [
        'MainHub.model.flowcell.Lane'
    ],

    model: 'MainHub.model.flowcell.Lane',

    sorters: 'lane_name'
});

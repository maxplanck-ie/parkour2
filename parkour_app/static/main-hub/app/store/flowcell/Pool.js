Ext.define('MainHub.store.flowcell.Pool', {
    extend: 'Ext.data.Store',
    storeId: 'poolsStore',

    requires: [
        'MainHub.model.flowcell.Pool'
    ],

    model: 'MainHub.model.flowcell.Pool',

    proxy: {
        type: 'ajax',
        url: 'api/flowcells/pool_list/',
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

    listeners: {
        disable: function(record, state) {
            var gridView = Ext.getCmp('pools-flowcell-grid').getView();
            var rowIndex = this.indexOf(record);

            if (state) {
                gridView.addRowCls(rowIndex, 'pool-disabled');
            } else {
                gridView.removeRowCls(rowIndex, 'pool-disabled');
            }
        }
    }
});
